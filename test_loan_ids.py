#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check loan IDs for employee 180"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utils'))

from db_manager import DBManager
from database_models import Loan, Employee

db = DBManager()
session = db.get_session()

print("=" * 80)
print("فحص السلف للموظف 180:")
print("=" * 80)

emp_180 = session.query(Employee).filter(Employee.code == '180').first()
if emp_180:
    loans = session.query(Loan).filter(Loan.employee_id == emp_180.id).all()
    print(f"الموظف: {emp_180.name} (الكود: 180)")
    print(f"عدد السلف: {len(loans)}\n")
    
    for loan in loans:
        print(f"رقم السلفة (ID): {loan.id}")
        print(f"  الموظف: {loan.employee.name} (الكود: {loan.employee.code})")
        print(f"  المبلغ: {loan.amount}")
        print(f"  التاريخ: {loan.date}")
        print()

print("=" * 80)
print("فحص آخر 10 سلف في النظام:")
print("=" * 80)

last_loans = session.query(Loan).order_by(Loan.id.desc()).limit(10).all()
for loan in last_loans:
    print(f"ID: {loan.id:3d} | الكود: {loan.employee.code:3s} | الاسم: {loan.employee.name:30s} | المبلغ: {loan.amount:8.2f}")

print("\n" + "=" * 80)
print("فحص جميع السلف ذات الـ ID من 150 إلى 200:")
print("=" * 80)

loans_range = session.query(Loan).filter(Loan.id.between(150, 200)).order_by(Loan.id).all()
print(f"عدد السلف: {len(loans_range)}\n")
for loan in loans_range:
    print(f"ID: {loan.id:3d} | الكود: {loan.employee.code:3s} | الاسم: {loan.employee.name:30s} | المبلغ: {loan.amount:8.2f}")

session.close()
