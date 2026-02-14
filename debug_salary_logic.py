import sys
import os
sys.path.append(os.getcwd())

from core.db_manager import DBManager
from core.database_models import Employee, SalaryHistory
from datetime import datetime

db = DBManager()
session = db.get_session()

emp = session.query(Employee).filter(Employee.code == '102').first()
print(f"Employee: {emp.name} (Code: {emp.code})")

print("\n--- Salary History Records ---")
history = session.query(SalaryHistory).filter(SalaryHistory.employee_id == emp.id).order_by(SalaryHistory.effective_date.asc()).all()
for h in history:
    print(f"ID: {h.id} | Effective: {h.effective_date} | New Salary: {h.new_salary} | Reason: {h.reason}")

# اختبار منطق البحث لشهر 11
target_date = datetime(2025, 11, 25, 23, 59, 59)
print(f"\nSearching for effective salary as of: {target_date}")

h = session.query(SalaryHistory)\
    .filter(SalaryHistory.employee_id == emp.id,
            SalaryHistory.effective_date <= target_date)\
    .order_by(SalaryHistory.effective_date.desc())\
    .first()

if h:
    print(f"Found Record: ID {h.id}, Salary {h.new_salary}, Effective Date {h.effective_date}")
else:
    print("No record found, using basic_salary:", emp.basic_salary)
