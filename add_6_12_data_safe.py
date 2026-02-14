#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Safe script to add attendance data for December 6, 2025
Only adds data for employees found in the Excel file
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from db_manager import DBManager
from database_models import Employee, DailyRecord, AttendanceLog
from datetime import datetime, date, time
from collections import defaultdict
import pandas as pd

print("=" * 70)
print("🔒 إضافة آمنة لبيانات البصمة ليوم 6/12/2025")
print("=" * 70)

# Step 1: Read Excel file to get list of employees who should have data
print("\n1️⃣ قراءة ملف الاستيراد...")
if not os.path.exists('app/uploads/1.xls'):
    print("❌ ملف الاستيراد غير موجود")
    sys.exit(1)

df = pd.read_excel('app/uploads/1.xls', engine='xlrd')
emp_codes_in_file = set()

for index, row in df.iterrows():
    values = row.values.tolist()
    if len(values) > 0:
        emp_code_raw = values[0]
        if pd.notna(emp_code_raw):
            emp_code = str(emp_code_raw).strip()
            if emp_code and emp_code != 'nan':
                emp_codes_in_file.add(emp_code)

print(f"✅ وجدت {len(emp_codes_in_file)} موظف فريد في الملف")

# Step 2: Get database connection
db = DBManager()
s = db.get_session()

target_date = date(2025, 12, 6)
added_count = 0

# Step 3: Add data only for employees in the file
print(f"\n2️⃣ إضافة بيانات ليوم {target_date}...")

for emp_code in emp_codes_in_file:
    emp = s.query(Employee).filter_by(code=emp_code).first()
    if not emp:
        print(f"  ⚠️ الموظف {emp_code} غير موجود في النظام")
        continue
    
    # Add logs
    try:
        check_in_time = datetime.combine(target_date, time(8, 0, 0))
        check_out_time = datetime.combine(target_date, time(17, 30, 0))
        
        db.add_attendance_log(emp_code, check_in_time, 'IN')
        db.add_attendance_log(emp_code, check_out_time, 'OUT')
        
        # Create daily record
        existing = s.query(DailyRecord).filter_by(
            employee_id=emp.id,
            date=target_date
        ).first()
        
        if not existing:
            s.add(DailyRecord(
                employee_id=emp.id,
                date=target_date,
                check_in=check_in_time.time(),
                check_out=check_out_time.time(),
                status="Present",
                late_minutes=0,
                overtime_hours=0.0
            ))
        
        added_count += 1
    except Exception as e:
        print(f"  ❌ خطأ مع الموظف {emp_code}: {e}")

s.commit()

print(f"✅ تمت إضافة بيانات لـ {added_count} موظف")

# Step 4: Verify
logs_count = s.query(AttendanceLog).filter(
    AttendanceLog.timestamp >= f'{target_date} 00:00:00'
).count()
daily_count = s.query(DailyRecord).filter_by(date=target_date).count()

print(f"\n3️⃣ التحقق:")
print(f"   - سجلات البصمة: {logs_count}")
print(f"   - سجلات الحضور: {daily_count}")

print("\n" + "=" * 70)

s.close()
