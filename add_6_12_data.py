#!/usr/bin/env python3
"""Add data manually using Python code"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
from db_manager import DBManager
from database_models import Employee, DailyRecord, AttendanceLog
from datetime import datetime, date, time
from collections import defaultdict

db = DBManager()
s = db.get_session()
target = date(2025, 12, 6)
emps = s.query(Employee).all()

for e in emps[:83]:
    try:
        in_t = datetime.combine(target, time(8, 0))
        out_t = datetime.combine(target, time(17, 30))
        db.add_attendance_log(e.code, in_t, 'IN')
        db.add_attendance_log(e.code, out_t, 'OUT')
    except: pass

logs = db.get_logs_by_date(target)
print(f"Logs: {len(logs)}")

emp_logs = defaultdict(list)
for log in logs:
    emp_logs[log.employee_code].append(log.timestamp)

cnt = 0
for code, times in emp_logs.items():
    e = s.query(Employee).filter_by(code=code).first()
    if not e: continue
    sorted_t = sorted(times)
    in_t = sorted_t[0].time()
    out_t = sorted_t[-1].time() if len(sorted_t) > 1 else None
    ex = s.query(DailyRecord).filter_by(employee_id=e.id, date=target).first()
    if ex:
        ex.check_in, ex.check_out, ex.status = in_t, out_t, "Present"
    else:
        s.add(DailyRecord(employee_id=e.id, date=target, check_in=in_t, check_out=out_t, status="Present", late_minutes=0, overtime_hours=0.0))
    cnt += 1

s.commit()
print(f"Daily Records: {cnt}")
s.close()
