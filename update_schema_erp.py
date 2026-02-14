import sys
import os

# Add core to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
core_dir = os.path.join(current_dir, 'core')
if core_dir not in sys.path:
    sys.path.insert(0, core_dir)

from db_manager import DBManager
from database_models import Base
from auth_models import User, SystemPermission, user_permissions
from accounting_models import Account, JournalEntry, JournalItem
from production_models import Warehouse, Product, InventoryTransaction, ProductionOrder, ProductionQC
from treasury_models import CashAccount, BankAccount, CheckRecord
from commercial_models import Partner, Invoice, InvoiceItem



def update_db():
    print("Updating database schema for Full ERP...")
    try:
        db = DBManager()
        engine = db.engine
        
        # Create all new tables
        Base.metadata.create_all(engine)
        print("Tables created successfully.")
        
        # Initialize basic permissions
        session = db.get_session()
        if session.query(SystemPermission).count() == 0:
            print("Initializing basic permissions...")
            perms = [
                SystemPermission(name='view_dashboard', description='View Dashboard', category='General'),
                SystemPermission(name='manage_users', description='Manage Users', category='Admin'),
                SystemPermission(name='manage_roles', description='Manage Roles & Permissions', category='Admin'),
                
                # HR
                SystemPermission(name='view_hr', description='View HR Module', category='HR'),
                SystemPermission(name='manage_employees', description='Manage Employees', category='HR'),
                SystemPermission(name='view_loans', description='View Loans Only', category='HR'),
                
                # Accounting
                SystemPermission(name='view_accounting', description='View Accounting Module', category='Accounting'),
                SystemPermission(name='manage_journals', description='Create/Edit Journals', category='Accounting'),
                SystemPermission(name='view_reports', description='View Financial Reports', category='Accounting'),
                
                # Inventory & Production
                SystemPermission(name='view_inventory', description='View Inventory', category='Inventory'),
                SystemPermission(name='manage_stock', description='Stock Movements', category='Inventory'),
                SystemPermission(name='view_production', description='View Production', category='Production'),
                SystemPermission(name='manage_cuts', description='Manage Cuts', category='Production'),
                SystemPermission(name='qc_check', description='Perform QC', category='Production'),
            ]
            session.add_all(perms)
            session.commit()
            print("Permissions initialized.")
        else:
            print("Permissions already exist. Skipping initialization.")
        
        # Check if Admin user exists
        if session.query(User).filter_by(username='admin').first() is None:
            print("Creating default admin user...")
            admin = User(username='admin', full_name='System Administrator', is_admin=True)
            admin.set_password('admin123') # Default password, should be changed
            session.add(admin)
            session.commit()
            print("Default admin created (user: admin, pass: admin123).")
            
        session.close()
        
    except Exception as e:
        print(f"Error during update: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    update_db()
