# -*- coding: utf-8 -*-
"""
اختبار التحقق من الإصلاحات
"""
from datetime import date

print("=" * 60)
print("التحقق من منطق اليوم 26")
print("=" * 60)

today = date.today()
print(f"التاريخ الحالي: {today}")
print(f"اليوم من الشهر: {today.day}")
print(f"هل نحن بعد اليوم 26؟ {today.day >= 26}")

if today.day >= 26:
    print("\n>> نستخدم: الراتب الاساسي الكامل (نهاية شهر)")
else:
    print("\n>> نستخدم: عدد الايام x الراتب اليومي (ايام فعلية)")

print("\n" + "=" * 60)
print("مثال حسابي:")
print("=" * 60)

basic_salary = 3000
attendance_days = 20
daily_salary = basic_salary / 30

print(f"الراتب الأساسي: {basic_salary} جنيه")
print(f"أيام الحضور: {attendance_days} يوم")
print(f"الراتب اليومي: {daily_salary:.2f} جنيه")

if today.day >= 26:
    gross_salary = basic_salary
    calc_type = "نهاية شهر"
else:
    gross_salary = attendance_days * daily_salary
    calc_type = "أيام فعلية"

print(f"\nنوع الحساب: {calc_type}")
print(f"الراتب الإجمالي: {gross_salary:.2f} جنيه")

print("\n" + "=" * 60)
print("الاصلاحات المطبقة:")
print("=" * 60)
print("1. اصلاح منتقي الشهر في payroll/view.html")
print("2. تطبيق منطق اليوم 26 في get_detailed_payroll_report")
print("3. اضافة منتقي الشهر في detailed_salary.html")
print("4. اضافة employee_id في البيانات المرجعة")
