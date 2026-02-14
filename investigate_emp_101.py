#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Investigate employee 101 fingerprints
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from db_manager import DBManager
from datetime import date
import pandas as pd

db = DBManager()
s = db.get_session()

from database_models import AttendanceLog, DailyRecord, Employee

print("=" * 70)
print("🔍 التحقيق: الموظف رقم 101")
print("=" * 70)

# Check if employee 101 exists
emp_101 = s.query(Employee).filter_by(code='101').first()
print(f"\n1️⃣ الموظف 101 موجود؟ {emp_101 is not None}")
if emp_101:
    print(f"   الاسم: {emp_101.name}")
    print(f"   معرف قاعدة البيانات: {emp_101.id}")

# Check all logs for employee code 101
print(f"\n2️⃣ البحث عن جميع البصمات برقم 101...")
all_logs_101 = s.query(AttendanceLog).filter_by(employee_code='101').all()
print(f"   إجمالي البصمات: {len(all_logs_101)}")

if all_logs_101:
    # Group by date
    logs_by_date = {}
    for log in all_logs_101:
        log_date = log.timestamp.date()
        if log_date not in logs_by_date:
            logs_by_date[log_date] = []
        logs_by_date[log_date].append(log)
    
    print(f"\n   التواريخ التي توجد بصمات فيها:")
    for d in sorted(logs_by_date.keys()):
        count = len(logs_by_date[d])
        print(f"      {d}: {count} بصمة")

# Check daily records for employee ID (if exists)
print(f"\n3️⃣ البحث عن سجلات الحضور اليومي...")
if emp_101:
    daily_recs = s.query(DailyRecord).filter_by(employee_id=emp_101.id).all()
    print(f"   إجمالي السجلات اليومية: {len(daily_recs)}")
    
    if daily_recs:
        print(f"\n   التواريخ المسجلة:")
        for rec in daily_recs:
            print(f"      {rec.date}: الحضور={rec.check_in}, الانصراف={rec.check_out}")

# Check Excel file for employee 101
print(f"\n4️⃣ البحث في ملف الاستيراد...")
if os.path.exists('app/uploads/1.xls'):
    df = pd.read_excel('app/uploads/1.xls', engine='xlrd')
    
    found_in_file = False
    for index, row in df.iterrows():
        values = row.values.tolist()
        if len(values) > 0:
            emp_code = str(values[0]).strip()
            if '101' in emp_code or emp_code == '101':
                found_in_file = True
                print(f"   ✓ وجدت الموظف 101 في السطر {index + 2}")
                print(f"     البيانات: {values}")
    
    if not found_in_file:
        print(f"   ✗ لم يتم العثور على الموظف 101 في ملف الاستيراد")
else:
    print(f"   ⚠️ ملف الاستيراد غير موجود")

print("\n" + "=" * 70)

s.close()
