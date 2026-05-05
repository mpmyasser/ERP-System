import sys
import os

# Add the project root to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir))) # Adjusting to find project root
# Wait, let's just use the absolute path from the environment
project_root = r"e:\backoup\25-2-2026"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.db_manager import DBManager
from core.auth_models import SystemPermission

def list_permissions():
    db = DBManager()
    session = db.get_session()
    
    perms = session.query(SystemPermission).all()
    print("--- Current Permissions in Database ---")
    for p in perms:
        print(f"ID: {p.id} | Name: {p.name} | Description: {p.description}")
    
    session.close()

if __name__ == "__main__":
    list_permissions()
