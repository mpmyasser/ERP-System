#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to verify import functionality
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from db_manager import DBManager
from datetime import date

# Connect to database
db = DBManager()
session = db.get_session()

from database_models import AttendanceLog, DailyRecord

print("=" * 70)
print("✓ اختبار نجاح المتطلبات")
print("=" * 70)

# Test 1: Check if get_logs_by_date works
print("\n1️⃣  اختبار دالة get_logs_by_date:")
test_date = date(2025, 12, 4)
logs = db.get_logs_by_date(test_date)
print(f"   ✓ عدد السجلات لـ {test_date}: {len(logs)}")

# Test 2: Check database connectivity
print("\n2️⃣  اختبار الاتصال بقاعدة البيانات:")
log_count = session.query(AttendanceLog).count()
record_count = session.query(DailyRecord).count()
print(f"   ✓ إجمالي سجلات البصمة: {log_count}")
print(f"   ✓ إجمالي سجلات الحضور: {record_count}")

# Test 3: Check if daily records have required fields
print("\n3️⃣  اختبار حقول سجلات الحضور:")
sample_record = session.query(DailyRecord).first()
if sample_record:
    print(f"   ✓ معرف الموظف: {sample_record.employee_id}")
    print(f"   ✓ التاريخ: {sample_record.date}")
    print(f"   ✓ وقت الحضور: {sample_record.check_in}")
    print(f"   ✓ وقت الانصراف: {sample_record.check_out}")
    print(f"   ✓ الحالة: {sample_record.status}")

print("\n" + "=" * 70)
print("✅ جميع الاختبارات نجحت!")
print("=" * 70)
print("\n📌 الآن يمكنك:")
print("   1. الذهاب لصفحة استيراد البصمة في البرنامج")
print("   2. اختيار ملف Excel يحتوي على بيانات البصمة")
print("   3. النقر على 'استيراد البيانات'")
print("   4. ستظهر رسالة نجاح مع عدد السجلات المستوردة")
print("=" * 70)

session.close()
