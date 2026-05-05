import sys
import os

# Add the project root to sys.path
project_root = r"e:\backoup\25-2-2026"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.db_manager import DBManager
from core.auth_models import SystemPermission

def cleanup_permissions():
    db = DBManager()
    session = db.get_session()
    
    # Target the wrong permission
    wrong_perm = session.query(SystemPermission).filter_by(name='view_interactive_daily_report').first()
    
    if wrong_perm:
        print(f"Deleting permission: {wrong_perm.name} ({wrong_perm.description})")
        session.delete(wrong_perm)
        session.commit()
        print("Done.")
    else:
        print("Permission not found or already deleted.")
    
    session.close()

if __name__ == "__main__":
    cleanup_permissions()
