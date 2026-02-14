#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Check how many records were added and to which employees
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from db_manager import DBManager
from datetime import date

db = DBManager()
s = db.get_session()

from database_models import DailyRecord, Employee

target = date(2025, 12, 6)
records = s.query(DailyRecord).filter_by(date=target).all()

print("=" * 70)
print(f"📊 تقرير سجلات الحضور ليوم {target}")
print("=" * 70)

print(f"\nإجمالي السجلات: {len(records)}\n")

print("أول 5 موظفين:")
for i, rec in enumerate(records[:5]):
    emp = s.query(Employee).filter_by(id=rec.employee_id).first()
    print(f"  {i+1}. معرف={rec.employee_id}, الكود={emp.code if emp else '?'}, الاسم={emp.name if emp else 'UNKNOWN'}")

print("\nآخر 5 موظفين:")
for i, rec in enumerate(records[-5:], start=len(records)-4):
    emp = s.query(Employee).filter_by(id=rec.employee_id).first()
    print(f"  {i}. معرف={rec.employee_id}, الكود={emp.code if emp else '?'}, الاسم={emp.name if emp else 'UNKNOWN'}")

s.close()
