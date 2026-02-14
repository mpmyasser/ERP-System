#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
حساب صافي الراتب للموظف 114 - شهر ديسمبر 2024
مع الأخذ في الاعتبار:
- عدد الأيام الفعلية
- السلف
- الخصومات والتصاريح
- الإضافي (overtime)
- الحد الأقصى 26 يوم للشهر
"""

import sys
import os
from datetime import datetime, date
from calendar import monthrange

sys.path.insert(0, os.path.join(os.getcwd(), 'core'))

from db_manager import DBManager
from services.payroll_processor import PayrollCalculator
from database_models import Employee, DailyRecord
from utils.hr_policy import HRPolicy

db = DBManager()
session = db.get_session()

# Get employee 114
emp = session.query(Employee).filter_by(code="114").first()

if not emp:
    print("❌ الموظف 114 غير موجود")
    sys.exit(1)

print("=" * 80)
print(f"حساب الراتب - الموظف: {emp.name} (الكود: {emp.code})")
print("=" * 80)
print(f"الراتب الأساسي: {emp.basic_salary} ج.م")
print(f"ساعات العمل اليومية: {emp.daily_work_hours}")
print()

# Get current month/year
month = datetime.now().month
year = datetime.now().year

calc = PayrollCalculator(db)
start_date, end_date = calc.get_salary_month_date_range(month, year)

print(f"الفترة: من {start_date.strftime('%d/%m/%Y')} إلى {end_date.strftime('%d/%m/%Y')}")
print()

# Get daily records
daily_records = calc._get_monthly_records(emp.id, month, year)

print(f"عدد السجلات اليومية: {len(daily_records)}")
print()

# Calculate components
attendance_data = calc.calculate_attendance_deductions(daily_records, emp)
overtime_value = calc.calculate_overtime(daily_records, emp)
incentive_value = calc.calculate_incentive(attendance_data['attendance_days'], emp.incentive_allowance)
loans_deduction = calc.calculate_loans_deduction(emp.id, month, year)
permissions_deduction = calc.calculate_permissions_deduction(daily_records, emp)
admin_penalties = calc._get_administrative_penalties(emp.id, month, year)

print("📊 تفاصيل الحساب:")
print("-" * 80)

# Get days info
attendance_days = attendance_data['attendance_days']
absence_days = attendance_data['absence_days']
total_days = attendance_days + absence_days

print(f"أيام الحضور الفعلية: {attendance_days}")
print(f"أيام الغياب: {absence_days}")
print(f"إجمالي الأيام المسجلة: {total_days}")
print()

# Calculate daily salary
daily_salary = HRPolicy.calculate_daily_salary(emp.basic_salary)
print(f"الراتب اليومي: {daily_salary:.2f} ج.م")
print()

# Gross salary calculation
gross_salary = emp.basic_salary
print(f"الراتب الأساسي (الإجمالي الأولي): {gross_salary:.2f} ج.م")
print()

# Additions
print("✅ الإضافات:")
print(f"  - الحافز الدورى: {incentive_value:.2f} ج.م")
print(f"  - بدل النقل: {emp.transport_allowance:.2f} ج.م")
print(f"  - الوقت الإضافي: {overtime_value:.2f} ج.م")
total_additions = incentive_value + emp.transport_allowance + overtime_value
print(f"  📌 إجمالي الإضافات: {total_additions:.2f} ج.م")
print()

# Deductions
print("❌ الخصومات:")
late_deduction = attendance_data['lateness_deduction']
early_deduction = attendance_data.get('early_deduction', 0.0)
absence_penalty = attendance_data['absence_penalty_deduction']

print(f"  - خصم التأخير: {late_deduction:.2f} ج.م")
print(f"  - خصم المبكر: {early_deduction:.2f} ج.م")
print(f"  - خصم الغياب: {absence_penalty:.2f} ج.م")
print(f"  - خصم التصاريح: {permissions_deduction:.2f} ج.م")
print(f"  - خصم السلف: {loans_deduction:.2f} ج.م")
print(f"  - جزاءات إدارية: {admin_penalties:.2f} ج.م")
if emp.is_insured:
    insurance_deduction = emp.insurance_value_employee
    print(f"  - التأمين: {insurance_deduction:.2f} ج.م")
else:
    insurance_deduction = 0.0
    print(f"  - التأمين: 0.00 ج.م (غير مؤمن)")

total_deductions = (late_deduction + early_deduction + absence_penalty + 
                    permissions_deduction + loans_deduction + admin_penalties + insurance_deduction)
print(f"  📌 إجمالي الخصومات: {total_deductions:.2f} ج.م")
print()

# Net salary
net_salary = gross_salary + total_additions - total_deductions
print("=" * 80)
print(f"🎯 صافي الراتب = {gross_salary:.2f} + {total_additions:.2f} - {total_deductions:.2f}")
print(f"🎯 صافي الراتب = {net_salary:.2f} ج.م")
print("=" * 80)
print()

# Details breakdown
print("📋 التفاصيل الكاملة:")
print("-" * 80)
print(f"الراتب الأساسي:          {gross_salary:>15.2f} ج.م")
print(f"إضافات:                 {total_additions:>15.2f} ج.م")
print(f"  ├─ حافز دوري:          {incentive_value:>14.2f} ج.م")
print(f"  ├─ بدل نقل:            {emp.transport_allowance:>14.2f} ج.م")
print(f"  └─ وقت إضافي:          {overtime_value:>14.2f} ج.م")
print(f"                         " + "-" * 20)
print(f"الإجمالي قبل الخصم:      {gross_salary + total_additions:>15.2f} ج.م")
print(f"                         " + "-" * 20)
print(f"الخصومات:               {total_deductions:>15.2f} ج.م")
print(f"  ├─ تأخير:              {late_deduction:>14.2f} ج.م")
print(f"  ├─ مبكر:               {early_deduction:>14.2f} ج.م")
print(f"  ├─ غياب:               {absence_penalty:>14.2f} ج.م")
print(f"  ├─ تصريح:              {permissions_deduction:>14.2f} ج.م")
print(f"  ├─ سلفة:               {loans_deduction:>14.2f} ج.م")
print(f"  ├─ جزاءات:             {admin_penalties:>14.2f} ج.م")
print(f"  └─ تأمين:              {insurance_deduction:>14.2f} ج.م")
print(f"                         " + "=" * 20)
print(f"💰 صافي الراتب:          {net_salary:>15.2f} ج.م")
print("=" * 80)

# Provide the data for approval
print()
print("📌 APPROVAL DATA:")
print(f"Employee: {emp.name}")
print(f"Code: {emp.code}")
print(f"Month: {month}/{year}")
print(f"Gross Salary: {gross_salary:.2f}")
print(f"Additions: {total_additions:.2f}")
print(f"Deductions: {total_deductions:.2f}")
print(f"NET_SALARY: {net_salary:.2f}")
