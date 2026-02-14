
import sys
import os
from datetime import datetime, date
sys.path.insert(0, os.path.join(os.getcwd(), 'core'))

from db_manager import DBManager
from services.attendance_service import AttendanceService
from database_models import Employee, DailyRecord

db = DBManager()
session = db.get_session()
service = AttendanceService(session)

code = "114"
emp = session.query(Employee).filter_by(code=code).first()

if not emp:
    print("Employee 114 not found")
    sys.exit()

print(f"=== Config for {emp.name} ===")
print(f"Standard Start: {emp.standard_start_time}")
print(f"Standard End: {emp.standard_end_time}")
print(f"Overtime Allowed: {emp.overtime_allowed}")
print(f"Grace Period: {getattr(emp, 'late_grace_period', 'Default')}")

# Pick a test date
test_date = date(2025, 11, 26)
record = session.query(DailyRecord).filter_by(employee_id=emp.id, date=test_date).first()

if not record:
    print(f"No record found for {test_date}")
    sys.exit()

print(f"\n=== Before Reprocess ({test_date}) ===")
print(f"In: {record.check_in} | Out: {record.check_out}")
print(f"Late Mins: {record.late_minutes}")
print(f"OT Hours: {record.overtime_hours}")
print(f"Late Ded: {record.late_deduction_amount}")

# Force Reprocess
print("\n>>> Reprocessing...")
# We need to pass Check In/Out explicitly or it might use None if we don't fetch from logs?
# process_attendance_record uses args passed to it.
# Wait, process_attendance_for_date (in db_manager/routes) logic usually fetches logs then calls process_record.
# Here we just want to re-run calculation logic on EXISTING times if possible, or we retrieve logs.
# Let's verify what logs exist first.
from database_models import AttendanceLog
logs = session.query(AttendanceLog).filter(
    AttendanceLog.employee_code == code,
    AttendanceLog.timestamp >= datetime.combine(test_date, datetime.min.time()),
    AttendanceLog.timestamp <= datetime.combine(test_date, datetime.max.time())
).all()

print(f"Found {len(logs)} logs for this day.")
if logs:
    times = sorted([l.timestamp.time() for l in logs])
    cin = times[0]
    cout = times[-1] if len(times) > 1 else None
    print(f"Derived In: {cin}, Out: {cout}")
    
    # CALL SERVICE
    service.process_attendance_record(emp.id, test_date, cin, cout)
    session.commit()
    
    # Reload record
    session.refresh(record)
    print(f"\n=== After Reprocess ({test_date}) ===")
    print(f"Late Mins: {record.late_minutes}")
    print(f"OT Hours: {record.overtime_hours}")
    print(f"Late Ded: {record.late_deduction_amount}")
    print(f"OT Pay: {record.overtime_pay_amount}")
else:
    print("No raw logs found to reprocess from!")

