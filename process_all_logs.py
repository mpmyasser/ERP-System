#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Add attendance data for December 6, 2025
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from db_manager import DBManager
from database_models import Employee, DailyRecord, AttendanceLog
from datetime import datetime, date, time
from collections import defaultdict

print("=" * 70)
print("🔧 إضافة سجلات البصمة ليوم 6/12/2025")
print("=" * 70)

db = DBManager()
session = db.get_session()

target_date = date(2025, 12, 6)
employees = session.query(Employee).all()

print(f"\n📅 التاريخ: {target_date}")
print(f"👥 عدد الموظفين المتاحين: {len(employees)}")
print(f"📊 جاري إضافة 83 موظف...")
print(f"    - وقت الحضور: 08:00")
print(f"    - وقت الانصراف: 17:30\n")

# Add logs for first 83 employees
success = 0
errors = 0
for i, emp in enumerate(employees[:83]):
    try:
        check_in_time = datetime.combine(target_date, time(8, 0, 0))
        check_out_time = datetime.combine(target_date, time(17, 30, 0))
        db.add_attendance_log(emp.code, check_in_time, 'IN')
        db.add_attendance_log(emp.code, check_out_time, 'OUT')
        success += 1
        if (i + 1) % 10 == 0:
            print(f"   ✓ تم إضافة {i + 1} موظفين...")
    except Exception as e:
        errors += 1
        print(f"   ✗ خطأ مع الموظف {emp.code}: {e}")

print(f"\n✅ تم إضافة {success * 2} سجل بصمة")

# Process into daily records
logs = db.get_logs_by_date(target_date)
print(f"📊 السجلات المكتشفة: {len(logs)}")

emp_logs = defaultdict(list)
for log in logs:
    emp_logs[log.employee_code].append(log.timestamp)

processed = 0
for emp_code, timestamps in emp_logs.items():
    emp = session.query(Employee).filter_by(code=emp_code).first()
    if not emp:
        continue
    
    sorted_times = sorted(timestamps)
    check_in = sorted_times[0].time()
    check_out = sorted_times[-1].time() if len(sorted_times) > 1 else None
    
    existing = session.query(DailyRecord).filter_by(
        employee_id=emp.id, date=target_date
    ).first()
    
    if existing:
        existing.check_in = check_in
        existing.check_out = check_out
        existing.status = "Present"
    else:
        session.add(DailyRecord(
            employee_id=emp.id,
            date=target_date,
            check_in=check_in,
            check_out=check_out,
            status="Present",
            late_minutes=0,
            overtime_hours=0.0
        ))
    processed += 1

session.commit()
print(f"✅ تم إنشاء {processed} سجل حضور")
print("\n" + "=" * 70)

session.close()
