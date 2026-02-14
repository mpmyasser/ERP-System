#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
اختبار نظام تسجيل السجل التاريخي للرواتب
Test Salary History Recording System
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from db_manager import DBManager
from datetime import datetime

def test_salary_history():
    """Test salary history functions"""
    db = DBManager()
    
    print("=" * 60)
    print("اختبار نظام السجل التاريخي للرواتب")
    print("=" * 60)
    
    try:
        # Get first employee
        employee = db.get_all_employees()[0] if db.get_all_employees() else None
        
        if not employee:
            print("❌ لا توجد موظفين في النظام")
            return
        
        print(f"\n✅ تم اختيار الموظف: {employee.code} - {employee.name}")
        print(f"   الراتب الحالي: {employee.basic_salary:,.2f}")
        
        # Test 1: Add salary history
        print("\n📝 اختبار 1: تسجيل تعديل على الراتب...")
        
        old_salary = employee.basic_salary
        new_salary = old_salary + 500
        
        history = db.add_salary_history(
            employee_id=employee.id,
            old_salary=old_salary,
            new_salary=new_salary,
            reason="زيادة سنوية",
            notes="تقييم إيجابي",
            modified_by="admin"
        )
        
        print(f"✅ تم تسجيل التعديل بنجاح")
        print(f"   من: {old_salary:,.2f} إلى {new_salary:,.2f}")
        print(f"   التغيير: {history.salary_change:+,.2f}")
        print(f"   السبب: {history.reason}")
        
        # Test 2: Get employee salary history
        print("\n📝 اختبار 2: الحصول على السجل التاريخي للموظف...")
        
        history_records = db.get_employee_salary_history(employee.id)
        print(f"✅ عدد التعديلات المسجلة: {len(history_records)}")
        
        if history_records:
            for i, record in enumerate(history_records[:3], 1):
                print(f"   {i}. {record.formatted_change_date} - {record.old_salary:,.2f} → {record.new_salary:,.2f} ({record.change_type})")
        
        # Test 3: Get full salary history report
        print("\n📝 اختبار 3: الحصول على تقرير السجل التاريخي الكامل...")
        
        all_history = db.get_salary_history_report()
        print(f"✅ إجمالي التعديلات في النظام: {len(all_history)}")
        
        # Statistics
        total_increases = sum(h.salary_change for h in all_history if h.salary_change > 0)
        total_decreases = sum(h.salary_change for h in all_history if h.salary_change < 0)
        
        print(f"   إجمالي الزيادات: {total_increases:+,.2f}")
        print(f"   إجمالي التخفيضات: {total_decreases:+,.2f}")
        print(f"   الفرق الإجمالي: {total_increases + total_decreases:+,.2f}")
        
        # Test 4: Get salary history with employee data
        print("\n📝 اختبار 4: الحصول على السجل مع بيانات الموظف...")
        
        detailed_history = db.get_salary_history_with_employee(employee.id)
        print(f"✅ عدد السجلات المفصلة: {len(detailed_history)}")
        
        print("\n" + "=" * 60)
        print("✅ جميع الاختبارات نجحت!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ حدث خطأ: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_salary_history()
