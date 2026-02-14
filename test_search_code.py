#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test search_code functionality"""

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

# Get all employees with loans
print("=" * 80)
print("جميع الموظفين الذين لديهم سلف:")
print("=" * 80)

employees_with_loans = session.query(Employee).join(Loan).distinct().limit(20).all()
for emp in employees_with_loans:
    loans_count = session.query(Loan).filter(Loan.employee_id == emp.id).count()
    print(f"الكود: '{emp.code}' (نوع: {type(emp.code).__name__}), الاسم: {emp.name}, عدد السلف: {loans_count}")

print("\n" + "=" * 80)
print("اختبار البحث عن كود '180':")
print("=" * 80)

# Search with exact match
result_180 = db.search_loans(code='180')
print(f"عدد النتائج: {len(result_180)}")
for loan in result_180[:10]:
    print(f"  الكود: '{loan.employee.code}', الاسم: {loan.employee.name}, المبلغ: {loan.amount}")

print("\n" + "=" * 80)
print("جميع الأكواد الموجودة:")
print("=" * 80)

all_codes = session.query(Employee.code).distinct().order_by(Employee.code).all()
print(f"عدد الأكواد المختلفة: {len(all_codes)}")
for code in all_codes[:30]:
    print(f"  '{code[0]}'", end=" ")
print("\n...")

print("\n" + "=" * 80)
print("جميع الأكواد المشابهة لـ 18:")
print("=" * 80)

similar = session.query(Employee.code).filter(Employee.code.contains('18')).distinct().all()
print(f"الأكواد التي تحتوي على '18': {[code[0] for code in similar]}")

print("\n" + "=" * 80)
print("عدد الموظفين بكل كود:")
print("=" * 80)

all_employees = session.query(Employee).limit(50).all()
code_counts = {}
for emp in all_employees:
    if emp.code not in code_counts:
        code_counts[emp.code] = 0
    code_counts[emp.code] += 1

for code, count in sorted(code_counts.items()):
    print(f"الكود: '{code}' - العدد: {count}")

session.close()
