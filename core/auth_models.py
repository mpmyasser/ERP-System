from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Table, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from core.database_models import Base
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# جدول الربط بين المستخدمين والصلاحيات (Many-to-Many)
user_permissions = Table('user_system_permissions', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('permission_id', Integer, ForeignKey('system_permissions.id'))
)

# جدول الربط بين المستخدمين والخزائن المسموح بالوصول إليها
user_cash_access = Table('user_cash_account_access', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('cash_account_id', Integer, ForeignKey('cash_accounts.id'))
)

class SystemPermission(Base):
    """
    جدول الصلاحيات المتاحة في النظام (Access Control).
    تم تغيير الاسم من Permission لتجنب التعارض مع جدول الأذونات (Permissions) الخاص بالموظفين.
    """
    __tablename__ = 'system_permissions'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False) # e.g. 'view_loans'
    description = Column(String(100), nullable=True)       # e.g. 'صلاحية عرض السلف'
    category = Column(String(50), nullable=True)           # e.g. 'Accounting', 'HR'

    def __repr__(self):
        return f"<SystemPermission {self.name}>"

class User(Base):
    """
    نموذج المستخدم للنظام.
    """
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False) # Superuser flag
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # العلاقة مع الصلاحيات
    permissions = relationship('SystemPermission', secondary=user_permissions, backref='users')
    
    # العلاقة مع الخزائن المسموح بالوصول إليها
    accessible_cash_accounts = relationship('CashAccount', secondary=user_cash_access, backref='authorized_users')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def has_permission(self, perm_name):
        """
        التحقق مما إذا كان المستخدم يملك صلاحية معينة.
        الأدمن يملك كل الصلاحيات دائماً.
        """
        if self.is_admin:
            return True
        return any(p.name == perm_name for p in self.permissions)

    def __repr__(self):
        return f"<User {self.username}>"


class UserTableSetting(Base):
    """
    Store per-user table widths and metadata so column widths persist across devices.
    page: the request path (e.g. /employees/bulk)
    table_key: logical key for a table on that page (index or data-table-key)
    widths: JSON encoded list of widths (e.g. ["100px","200px",null,...])
    """
    __tablename__ = 'user_table_settings'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    page = Column(String(255), nullable=False)
    table_key = Column(String(255), nullable=True)
    widths = Column(String, nullable=True)  # store JSON string
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<UserTableSetting user={self.user_id} page={self.page} table={self.table_key}>"

class UserPreference(Base):
    """
    Generic per-user key-value settings store.
    `value` stores JSON-encoded data to support dynamic setting types.
    """
    __tablename__ = 'user_preferences'
    __table_args__ = (UniqueConstraint('user_id', 'key', name='uq_user_preferences_user_key'),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    key = Column(String(255), nullable=False)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<UserPreference user={self.user_id} key={self.key}>"

