#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Remove incorrect attendance data for employee 101 on 2025-12-06
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from db_manager import DBManager
from datetime import date

db = DBManager()
s = db.get_session()

from database_models import AttendanceLog, DailyRecord, Employee

print("=" * 70)
print("🧹 حذف البيانات الخاطئة للموظف 101 ليوم 6/12/2025")
print("=" * 70)

target_date = date(2025, 12, 6)
emp_101 = s.query(Employee).filter_by(code='101').first()

if not emp_101:
    print("❌ الموظف 101 غير موجود")
    s.close()
    sys.exit(1)

print(f"\n📍 الموظف: {emp_101.name} (معرف={emp_101.id})")

# Count existing records
logs_before = s.query(AttendanceLog).filter_by(employee_code='101').count()
daily_before = s.query(DailyRecord).filter_by(employee_id=emp_101.id, date=target_date).count()

print(f"\nقبل الحذف:")
print(f"  - سجلات البصمة: {logs_before}")
print(f"  - سجلات الحضور: {daily_before}")

# Delete logs for 101 on 2025-12-06
deleted_logs = s.query(AttendanceLog).filter_by(employee_code='101').filter(
    AttendanceLog.timestamp >= f'{target_date} 00:00:00'
).delete()

# Delete daily records
deleted_daily = s.query(DailyRecord).filter_by(
    employee_id=emp_101.id,
    date=target_date
).delete()

s.commit()

print(f"\nتم الحذف:")
print(f"  - ✅ حذف {deleted_logs} سجل بصمة")
print(f"  - ✅ حذف {deleted_daily} سجل حضور يومي")

# Verify
logs_after = s.query(AttendanceLog).filter_by(employee_code='101').count()
daily_after = s.query(DailyRecord).filter_by(employee_id=emp_101.id, date=target_date).count()

print(f"\nبعد الحذف:")
print(f"  - سجلات البصمة: {logs_after}")
print(f"  - سجلات الحضور: {daily_after}")

print("\n" + "=" * 70)
print("✅ تم حذف البيانات الخاطئة بنجاح")
print("=" * 70)

s.close()
