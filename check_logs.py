import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from db_manager import DBManager

db = DBManager()
session = db.get_session()

from database_models import AttendanceLog

count = session.query(AttendanceLog).count()
print(f'إجمالي السجلات: {count}')

# Check logs after our import test
logs = session.query(AttendanceLog).order_by(AttendanceLog.timestamp.desc()).limit(5).all()
print("\nآخر 5 سجلات:")
for log in logs:
    print(f"  - الموظف: {log.employee_code}, الوقت: {log.timestamp}, النوع: {log.type}")

session.close()
