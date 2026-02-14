from core.db_manager import DBManager
from core.auth_models import User, SystemPermission
from database_models import Base # Ensure we use the correct Base
from sqlalchemy.orm import joinedload

class AuthManager:
    def __init__(self):
        self.db = DBManager()

    def get_user_by_username(self, username):
        session = self.db.get_session()
        try:
            return session.query(User).filter_by(username=username).first()
        finally:
            session.close()

    def get_user_by_id(self, user_id):
        session = self.db.get_session()
        try:
            # Eager load permissions and cash access to avoid detached instance errors later
            return session.query(User).options(
                joinedload(User.permissions),
                joinedload(User.accessible_cash_accounts)
            ).filter_by(id=user_id).first()
        finally:
            session.close()

    def create_user(self, username, password, full_name, is_admin=False):
        session = self.db.get_session()
        try:
            if session.query(User).filter_by(username=username).first():
                raise ValueError("اسم المستخدم موجود بالفعل")
                
            user = User(username=username, full_name=full_name, is_admin=is_admin)
            user.set_password(password)
            session.add(user)
            session.commit()
            return user
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
            
    def update_user_permissions(self, user_id, permission_ids):
        """
        Update the list of permissions for a user.
        permission_ids: list of int IDs
        """
        session = self.db.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                raise ValueError("User not found")
                
            # Get permission objects
            perms = session.query(SystemPermission).filter(SystemPermission.id.in_(permission_ids)).all()
            
            # Update relationship
            user.permissions = perms
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def update_user_cash_access(self, user_id, cash_account_ids):
        """
        Update the list of cash accounts a user can access.
        cash_account_ids: list of int IDs
        """
        session = self.db.get_session()
        try:
            from core.treasury_models import CashAccount
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                raise ValueError("User not found")
                
            # Get cash account objects
            accounts = session.query(CashAccount).filter(CashAccount.id.in_(cash_account_ids)).all()
            
            # Update relationship
            user.accessible_cash_accounts = accounts
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_all_users(self):
        session = self.db.get_session()
        try:
            return session.query(User).all()
        finally:
            session.close()

    def get_all_permissions(self):
        session = self.db.get_session()
        try:
            return session.query(SystemPermission).order_by(SystemPermission.category, SystemPermission.name).all()
        finally:
            session.close()

    def authenticate(self, username, password):
        session = self.db.get_session()
        try:
            user = session.query(User).filter_by(username=username).first()
            if user and user.check_password(password):
                if not user.is_active:
                    return None # User is banned
                return user
            return None
        finally:
            session.close()
