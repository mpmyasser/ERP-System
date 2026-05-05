import sys
import os
# Add root to path
root = os.getcwd()
sys.path.insert(0, root)
# Add core to path
sys.path.insert(0, os.path.join(root, 'core'))

from core.db_manager import DBManager
from core.database_models import Employee

db = DBManager()
print("Testing with load_full=False...")
# Simulating the list() route call
employees = db.get_employees_optimized(load_full=False)
if employees:
    e = employees[0]
    print(f"Employee: {e.name}")
    try:
        # This will likely trigger a lazy load IF the session is still open, 
        # but db.get_employees_optimized CLOSES the session in 'finally'.
        print(f"Daily Work Hours: {getattr(e, 'daily_work_hours', 'NOT ACCESSIBLE')}")
    except Exception as err:
        print(f"Error accessing daily_work_hours: {err}")
else:
    print("No employees found.")
