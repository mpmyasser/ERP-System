from core.db_manager import DBManager
from core.database_models import Employee, SalaryHistory, AuditLog
import sys

try:
    db = DBManager()
    session = db.get_session()
    emp = session.query(Employee).filter(Employee.code == '102').first()
    
    if not emp:
        print("Employee 102 not found")
        sys.exit(1)
        
    print(f"Employee: {emp.name}")
    print(f"Hire Date: {emp.hire_date}")
    print(f"Current basic_salary field: {emp.basic_salary}")
    
    print("\n--- Salary History Table ---")
    history = session.query(SalaryHistory).filter(SalaryHistory.employee_id == emp.id).order_by(SalaryHistory.effective_date).all()
    for h in history:
        print(f"Effective: {h.effective_date} | Salary: {h.new_salary} | Reason: {h.reason}")
        
    print("\n--- Audit Logs (Field Changes) ---")
    logs = session.query(AuditLog).filter(AuditLog.employee_code == '102', AuditLog.field_name == 'basic_salary').order_by(AuditLog.timestamp).all()
    for l in logs:
        print(f"Changed At: {l.timestamp} | From: {l.old_value} | To: {l.new_value}")

except Exception as e:
    print(f"Error: {e}")
