import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from db_manager import DBManager
from datetime import date

db = DBManager()
session = db.get_session()

from database_models import AttendanceLog, DailyRecord

# Check logs for the imported dates
print("=" * 50)
print("التحقق من سجلات البصمة المستوردة")
print("=" * 50)

# Check logs between 4/12/2025 and 6/12/2025
from datetime import datetime
target_dates = [
    date(2025, 12, 4),
    date(2025, 12, 5),
    date(2025, 12, 6),
]

total_new_logs = 0
for target_date in target_dates:
    # Use the range-based query like the fixed get_logs_by_date
    from datetime import time
    start_of_day = datetime.combine(target_date, time.min)
    end_of_day = datetime.combine(target_date, time.max)
    
    logs = session.query(AttendanceLog).filter(
        AttendanceLog.timestamp >= start_of_day,
        AttendanceLog.timestamp <= end_of_day
    ).all()
    
    print(f"\nالتاريخ: {target_date}")
    print(f"  عدد سجلات البصمة: {len(logs)}")
    total_new_logs += len(logs)
    
    if logs:
        # Show sample employees
        employees = list(set([log.employee_code for log in logs]))
        print(f"  عدد الموظفين: {len(employees)}")
        print(f"  عينة من الموظفين: {employees[:5]}")

print(f"\n{'=' * 50}")
print(f"إجمالي سجلات البصمة الجديدة: {total_new_logs}")

# Check daily records
print(f"\n{'=' * 50}")
print("التحقق من سجلات الحضور اليومي")
print("=" * 50)

total_daily_records = 0
for target_date in target_dates:
    daily_records = session.query(DailyRecord).filter_by(date=target_date).all()
    print(f"\nالتاريخ: {target_date}")
    print(f"  عدد سجلات الحضور: {len(daily_records)}")
    total_daily_records += len(daily_records)

print(f"\n{'=' * 50}")
print(f"إجمالي سجلات الحضور: {total_daily_records}")
print("=" * 50)

session.close()
