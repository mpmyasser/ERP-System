import sys
import os
sys.path.append(os.getcwd())

from core.db_manager import DBManager
from core.database_models import Employee, SalaryHistory
from datetime import datetime

db = DBManager()
session = db.get_session()

emp = session.query(Employee).filter(Employee.code == '102').first()
if emp:
    print(f"Employee: {emp.name} (Code: {emp.code})")
    print(f"Basic Salary Field: {emp.basic_salary}")
    print(f"Salary Updated At: {emp.salary_updated_at}")

    print("\n--- Salary History Records (Latest 5) ---")
    history = session.query(SalaryHistory).filter(SalaryHistory.employee_id == emp.id).order_by(SalaryHistory.change_date.desc()).limit(5).all()
    for h in history:
        print(f"ID: {h.id} | Effective: {h.effective_date} | New Salary: {h.new_salary} | Change Date: {h.change_date} | Reason: {h.reason}")
else:
    print("Employee 102 not found")
