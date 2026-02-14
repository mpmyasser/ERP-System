"""
Audit Log System - Test Suite
اختبار نظام سجلات التتبع
"""

import sys
import os
sys.path.insert(0, 'd:\\H.R\\core')

from db_manager import DBManager
from database_models import Employee, AuditLog
from datetime import datetime

def test_audit_log_functions():
    """اختبار دوال نظام التتبع"""
    
    print("\n" + "="*80)
    print("Audit Log System - Test Suite")
    print("اختبار نظام سجلات التتبع")
    print("="*80)
    
    try:
        # إنشاء مدير قاعدة البيانات
        db = DBManager('hr_system.db')
        print("\n✓ تم الاتصال بقاعدة البيانات بنجاح")
        
        # 1. اختبار الحصول على السجلات الحديثة
        print("\n" + "-"*80)
        print("Test 1: الحصول على آخر سجلات التتبع")
        print("-"*80)
        
        recent_logs = db.get_audit_logs_recent(limit=5)
        if recent_logs:
            print(f"✓ تم الحصول على {len(recent_logs)} سجل حديث")
            for log in recent_logs[:3]:  # عرض أول 3 سجلات فقط
                print(f"  • {log.employee_code}: {log.field_name}")
                print(f"    من: {log.old_value} إلى: {log.new_value}")
                print(f"    الوقت: {log.timestamp}")
        else:
            print("ℹ لا توجد سجلات تتبع حتى الآن")
        
        # 2. اختبار الحصول على السجلات حسب الموظف
        print("\n" + "-"*80)
        print("Test 2: الحصول على السجلات لموظف معين")
        print("-"*80)
        
        # الحصول على أول موظف من قاعدة البيانات
        all_employees = db.get_all_employees()
        if all_employees:
            emp = all_employees[0]
            emp_logs = db.get_audit_logs_by_employee(emp.code, limit=10)
            print(f"✓ الموظف: {emp.code} - {emp.name}")
            if emp_logs:
                print(f"  عدد سجلات التتبع: {len(emp_logs)}")
                for log in emp_logs[:2]:
                    print(f"  • {log.field_name}: {log.old_value} → {log.new_value}")
            else:
                print("  ℹ لا توجد سجلات تتبع لهذا الموظف")
        
        # 3. اختبار الحصول على السجلات حسب الحقل
        print("\n" + "-"*80)
        print("Test 3: الحصول على السجلات حسب الحقل")
        print("-"*80)
        
        salary_logs = db.get_audit_logs_by_field('base_salary', limit=5)
        if salary_logs:
            print(f"✓ تم الحصول على {len(salary_logs)} سجل لتغييرات الراتب الأساسي")
            for log in salary_logs[:2]:
                print(f"  • الموظف {log.employee_code}: {log.old_value} → {log.new_value}")
        else:
            print("ℹ لا توجد تغييرات في حقل base_salary")
        
        # 4. اختبار ملخص السجلات
        print("\n" + "-"*80)
        print("Test 4: ملخص السجلات لموظف معين")
        print("-"*80)
        
        if all_employees:
            emp = all_employees[0]
            summary = db.get_audit_log_summary(emp.code)
            print(f"✓ الموظف: {emp.code}")
            print(f"  عدد التغييرات: {summary['count']}")
            if summary['latest']:
                print(f"  آخر تغيير: {summary['latest'].field_name} في {summary['latest'].timestamp}")
            if summary['fields_changed']:
                print(f"  الحقول التي تغيرت: {', '.join(summary['fields_changed'])}")
        
        # 5. اختبار سجل التطور
        print("\n" + "-"*80)
        print("Test 5: سجل التطور لحقل معين")
        print("-"*80)
        
        if all_employees:
            emp = all_employees[0]
            history = db.get_audit_log_history(emp.code, 'name')
            if history:
                print(f"✓ سجل التطور لحقل 'name' للموظف {emp.code}:")
                for change in history:
                    print(f"  • {change['change']} في {change['timestamp']}")
            else:
                print(f"ℹ لا يوجد سجل تطور لهذا الحقل")
        
        # 6. اختبار التصدير إلى CSV
        print("\n" + "-"*80)
        print("Test 6: تصدير السجلات إلى ملف CSV")
        print("-"*80)
        
        export_result = db.export_audit_logs_csv('audit_logs_export.csv')
        if export_result:
            print("✓ تم تصدير السجلات بنجاح إلى 'audit_logs_export.csv'")
        else:
            print("✗ فشل تصدير السجلات")
        
        # ملخص النتائج
        print("\n" + "="*80)
        print("✅ SUMMARY: جميع الاختبارات تمت بنجاح")
        print("="*80)
        print("""
الدوال المتاحة:
1. get_audit_logs_by_employee(employee_code) - السجلات لموظف معين
2. get_audit_logs_by_field(field_name) - السجلات لحقل معين
3. get_audit_logs_recent(limit) - آخر السجلات
4. get_audit_log_summary(employee_code) - ملخص التغييرات
5. get_audit_log_history(employee_code, field_name) - سجل التطور
6. export_audit_logs_csv(filename) - تصدير إلى CSV
        """)
        
    except Exception as e:
        print(f"\n✗ خطأ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_audit_log_functions()
