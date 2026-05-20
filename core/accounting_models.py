from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date, Enum, Text
from sqlalchemy.orm import relationship, backref
from core.database_models import Base
from datetime import datetime
import enum

class AccountType(enum.Enum):
    ASSET = "Asset"           # أصول
    LIABILITY = "Liability"   # خصوم
    EQUITY = "Equity"         # حقوق ملكية
    INCOME = "Income"         # إيرادات
    EXPENSE = "Expense"       # مصروفات
    TRADING = "Trading"       # متاجرة
    PRODUCTION = "Production" # تشغيل

class CostCenter(Base):
    """
    مراكز التكلفة (Cost Centers)
    """
    __tablename__ = 'cost_centers'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    display_order = Column(Integer, default=0)
    is_active = Column(Integer, default=1)
    
    def __repr__(self):
        return f"<CostCenter {self.code} - {self.name}>"

class Account(Base):
    """
    شجرة الحسابات (Tree Structure)
    """
    __tablename__ = 'accounts'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False) # e.g. '101'
    name = Column(String(100), nullable=False)             # e.g. 'NBE Bank'
    type = Column(String(20), nullable=False)              # Asset, Liability...
    parent_id = Column(Integer, ForeignKey('accounts.id'), nullable=True)
    
    # Hierarchy fields
    level = Column(Integer, default=1)           # المستوى (1, 2, 3...)
    path = Column(String(200), nullable=True)     # المسار البرمجي (1/101/10101)
    
    # Accounting details
    account_class = Column(String(50), nullable=True) # Balance Sheet / P&L
    balance_type = Column(String(20), default='Debit') # Debit / Credit
    
    # تفاصيل إضافية
    description = Column(String(200), nullable=True)
    display_order = Column(Integer, default=0)
    is_active = Column(Integer, default=1)
    
    # العلاقة الذاتية للأبناء
    # Adjacency List Relationship
    children = relationship('Account', 
                            backref=backref('parent', remote_side=[id]),
                            cascade="all, delete-orphan")
    
    # العلاقة مع قيود اليومية
    journal_items = relationship('JournalItem', back_populates='account')
    
    def __repr__(self):
        return f"<Account {self.code} - {self.name}>"

class JournalEntry(Base):
    """
    قيد اليومية (Header)
    """
    __tablename__ = 'journal_entries'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, default=datetime.now)
    reference = Column(String(100), nullable=True) # e.g. 'INV-2024-001'
    description = Column(Text, nullable=True)
    
    status = Column(String(20), default='Draft') # Draft, Posted, Cancelled
    
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    items = relationship('JournalItem', back_populates='entry', cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<JournalEntry {self.id} - {self.date}>"

class JournalItem(Base):
    """
    طرف القيد (Detail Line)
    """
    __tablename__ = 'journal_items'
    
    id = Column(Integer, primary_key=True)
    journal_entry_id = Column(Integer, ForeignKey('journal_entries.id'), nullable=False)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    
    debit = Column(Float, default=0.0)
    credit = Column(Float, default=0.0)
    
    description = Column(String(200), nullable=True)
    
    # مركز التكلفة (اختياري للربط مع الإنتاج)
    cost_center = Column(String(50), nullable=True) 
    
    entry = relationship('JournalEntry', back_populates='items')
    account = relationship('Account', back_populates='journal_items')
