import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
from db_manager import DBManager
from datetime import date

db = DBManager()
s = db.get_session()
from database_models import DailyRecord, Employee

target = date(2025, 12, 6)
records = s.query(DailyRecord).filter_by(date=target).all()

print(f"Total records for {target}: {len(records)}")

if records:
    for i, rec in enumerate(records[:5]):
        emp = s.query(Employee).filter_by(id=rec.employee_id).first()
        print(f"  {i+1}. EmpID={rec.employee_id}, Name={emp.name if emp else 'NOT FOUND'}, In={rec.check_in}, Out={rec.check_out}")

s.close()
