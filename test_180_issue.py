#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test 180 specific issue"""

import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utils'))

from db_manager import DBManager
from database_models import Loan, Employee

# Initialize DB
db = DBManager()
session = db.get_session()

print("=" * 80)
print("التحقق من البيانات المخزنة للكود 180:")
print("=" * 80)

# Get employee 180
emp_180 = session.query(Employee).filter(Employee.code == '180').first()
if emp_180:
    print(f"✅ الموظف 180 موجود: {emp_180.name}")
    print(f"   الكود المخزن: '{emp_180.code}' (النوع: {type(emp_180.code).__name__}, الطول: {len(emp_180.code)})")
    
    # Get all loans for this employee
    loans_180 = session.query(Loan).filter(Loan.employee_id == emp_180.id).all()
    print(f"   عدد السلف: {len(loans_180)}")
    for loan in loans_180:
        print(f"     - المبلغ: {loan.amount}, التاريخ: {loan.date}")
else:
    print("❌ الموظف 180 غير موجود!")

print("\n" + "=" * 80)
print("البحث المباشر عن الكود '180' في جدول الموظفين:")
print("=" * 80)

# Direct SQL check
all_emp_codes = session.query(Employee.code).all()
print(f"إجمالي الموظفين: {len(all_emp_codes)}")

# Find codes that look similar to 180
similar_codes = []
for code_tuple in all_emp_codes:
    code = code_tuple[0]
    if '1' in code and '8' in code and '0' in code:
        similar_codes.append(code)

print(f"\nالأكواد التي تحتوي على 1 و 8 و 0:")
for code in sorted(set(similar_codes)):
    print(f"  - '{code}'")

print("\n" + "=" * 80)
print("نتيجة البحث عن الكود بالضبط '180':")
print("=" * 80)

result = db.search_loans(code='180')
print(f"عدد النتائج: {len(result)}")
for loan in result:
    print(f"  الكود: {loan.employee.code}, الاسم: {loan.employee.name}, المبلغ: {loan.amount}")

print("\n" + "=" * 80)
print("الأرقام الأخرى المتعلقة بـ 180:")
print("=" * 80)

# Check if there are loans with employee_id related to 180
print(f"معرّف الموظف 180: {emp_180.id if emp_180 else 'N/A'}")

# Search for loans that might be related
if emp_180:
    direct_check = session.query(Loan).filter(Loan.employee_id == emp_180.id).all()
    print(f"السلف المباشرة للموظف 180 (بـ ID): {len(direct_check)}")

session.close()
