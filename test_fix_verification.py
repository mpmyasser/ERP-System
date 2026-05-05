"""
اختبار الإصلاح: التحقق من حساب الغياب والجزاء الصحيح
"""

import sys
import os
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from db_manager import DBManager
from database_models import Employee
from services.payroll_processor import PayrollCalculator

def test_absence_calculation():
    """اختبار حساب الغياب بعد الإصلاح"""
    
    db = DBManager('core/hr.db')
    calculator = PayrollCalculator(db)
    
    print("\n" + "="*80)
    print("اختبار الإصلاح: حساب الغياب والجزاء")
    print("="*80)
    
    # اختبار الموظف 236
    employee_id = 130
    month = 2
    year = 2026
    
    try:
        payroll = calculator.calculate_monthly_payroll(employee_id, month, year)
        
        print(f"\nالموظف: {payroll['Employee']}")
        print(f"الفترة: {month}/{year}")
        print(f"\nالنتائج:")
        print(f"  - أيام الحضور: {payroll['Attendance Days']}")
        print(f"  - أيام الغياب: {payroll['Absence Days']}")
        print(f"  - أيام الجزاء: {payroll.get('Absence Penalty Days', 'N/A')}")
        print(f"  - قيمة الجزاء: {payroll['Absence Penalty Deduction']:.2f} جنيه")
        print(f"  - الراتب الأساسي: {payroll['Basic Salary']:.2f}")
        print(f"  - الراتب الإجمالي: {payroll['Gross Salary']:.2f}")
        print(f"  - الاستقطاعات: {payroll['Total Deductions']:.2f}")
        print(f"  - الراتب الصافي: {payroll['Net Salary']:.2f}")
        
        # التحقق من النتائج
        print(f"\nالتحقق:")
        if payroll['Absence Days'] > 0:
            print(f"  [صحيح] تم احتساب الغياب: {payroll['Absence Days']} أيام")
        else:
            print(f"  [خطأ] الغياب = 0 (لم يتم الإصلاح)")
        
        if payroll['Absence Penalty Deduction'] > 0:
            print(f"  [صحيح] تم احتساب الجزاء: {payroll['Absence Penalty Deduction']:.2f} جنيه")
        else:
            print(f"  [تحذير] الجزاء = 0 (قد يكون ضمن المسموح)")
        
    except Exception as e:
        print(f"[خطأ] {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)

if __name__ == "__main__":
    test_absence_calculation()
