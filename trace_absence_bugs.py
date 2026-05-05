"""
تتبع دقيق للأخطاء المنطقية في احتساب الغياب والجزاء
=====================================================

هذا السكريبت يفحص:
1. حساب عدد أيام الشهر (31 vs 26)
2. استبعاد الإجازات الأسبوعية من الغياب
3. استبعاد الأيام المستقبلية
4. استدعاء دالة الجزاء الفعلي
"""

import sys
import os
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from db_manager import DBManager
from database_models import Employee, DailyRecord, Leave, LeaveStatus, PublicHoliday
from policy.hr_policy import HRPolicy
from services.payroll_processor import PayrollCalculator

def trace_absence_calculation(employee_id: int, month: int, year: int):
    """تتبع دقيق لحساب الغياب والجزاء"""
    
    db = DBManager('core/hr.db')
    session = db.get_session()
    calculator = PayrollCalculator(db)
    
    try:
        employee = session.query(Employee).filter_by(id=employee_id).first()
        if not employee:
            print(f"[خطأ] الموظف {employee_id} غير موجود")
            return
        
        print("\n" + "="*80)
        print(f"تتبع حساب الغياب والجزاء للموظف: {employee.name} (كود: {employee.code})")
        print("="*80)
        
        # 1. حساب نطاق التاريخ
        start_date, end_date = calculator.get_salary_month_date_range(month, year)
        today = date.today()
        
        print(f"\n[1] نطاق الفترة:")
        print(f"    - تاريخ البداية: {start_date}")
        print(f"    - تاريخ النهاية: {end_date}")
        print(f"    - اليوم الحالي: {today}")
        
        # 2. حساب عدد الأيام
        total_calendar_days = (end_date - start_date).days + 1
        print(f"\n[2] عدد الأيام:")
        print(f"    - أيام التقويم الفعلية: {total_calendar_days}")
        print(f"    - أيام الشهر المعتمدة في الإعدادات: {HRPolicy.WORKING_DAYS_PER_MONTH}")
        print(f"    [تحذير] هناك فرق بين {total_calendar_days} و {HRPolicy.WORKING_DAYS_PER_MONTH}")
        
        # 3. جلب السجلات
        daily_records = session.query(DailyRecord).filter(
            DailyRecord.employee_id == employee_id,
            DailyRecord.date >= start_date,
            DailyRecord.date <= end_date
        ).order_by(DailyRecord.date).all()
        
        print(f"\n[3] سجلات الحضور:")
        print(f"    - عدد السجلات المسجلة: {len(daily_records)}")
        
        # 4. جلب الإجازات الأسبوعية والرسمية
        weekly_off_count = 0
        for d in range((end_date - start_date).days + 1):
            current_date = start_date + timedelta(days=d)
            weekday_mapping = {
                "الاثنين": "Monday",
                "الثلاثاء": "Tuesday",
                "الأربعاء": "Wednesday",
                "الخميس": "Thursday",
                "الجمعة": "Friday",
                "السبت": "Saturday",
                "الأحد": "Sunday"
            }
            target_weekday = weekday_mapping.get(HRPolicy.WEEKLY_HOLIDAY, "Friday")
            if current_date.strftime('%A') == target_weekday:
                weekly_off_count += 1
        
        print(f"\n[4] الإجازات الأسبوعية:")
        print(f"    - عدد الإجازات الأسبوعية: {weekly_off_count}")
        
        # 5. جلب الإجازات المعتمدة
        leaves = session.query(Leave).filter(
            Leave.employee_id == employee_id,
            Leave.start_date <= end_date,
            Leave.end_date >= start_date,
            Leave.status == LeaveStatus.APPROVED.value
        ).all()
        
        leave_days = 0
        for leave in leaves:
            d = leave.start_date
            while d <= leave.end_date:
                if start_date <= d <= end_date:
                    leave_days += 1
                d += timedelta(days=1)
        
        print(f"\n[5] الإجازات المعتمدة:")
        print(f"    - عدد أيام الإجازات: {leave_days}")
        for leave in leaves:
            print(f"      * {leave.leave_type}: من {leave.start_date} إلى {leave.end_date}")
        
        # 6. حساب الأيام المستقبلية
        future_days = 0
        for d in range((end_date - start_date).days + 1):
            current_date = start_date + timedelta(days=d)
            if current_date > today:
                future_days += 1
        
        print(f"\n[6] الأيام المستقبلية:")
        print(f"    - عدد الأيام المستقبلية: {future_days}")
        print(f"    [تحذير] هذه الأيام يجب استبعادها من حساب الغياب")
        
        # 7. حساب الأيام الفعلية المحسوبة
        actual_days_to_count = total_calendar_days - future_days
        print(f"\n[7] الأيام الفعلية المحسوبة:")
        print(f"    - الأيام المحسوبة فعلاً: {actual_days_to_count}")
        
        # 8. حساب الغياب الفعلي
        absence_days_raw = actual_days_to_count - len(daily_records)
        absence_days_corrected = absence_days_raw - weekly_off_count - leave_days
        
        print(f"\n[8] حساب الغياب:")
        print(f"    - الأيام الفعلية: {actual_days_to_count}")
        print(f"    - أيام الحضور المسجلة: {len(daily_records)}")
        print(f"    - الفرق الأولي: {absence_days_raw}")
        print(f"    - ناقص الإجازات الأسبوعية: -{weekly_off_count}")
        print(f"    - ناقص الإجازات المعتمدة: -{leave_days}")
        print(f"    - الغياب الفعلي: {absence_days_corrected}")
        
        # 9. حساب الجزاء
        grace_days = HRPolicy.ABSENCE_GRACE_DAYS
        penalty_days_value = HRPolicy.ABSENCE_PENALTY_DAYS
        
        print(f"\n[9] إعدادات الجزاء:")
        print(f"    - أيام الغياب المسموح بها: {grace_days}")
        print(f"    - قيمة الجزاء لكل يوم زائد: {penalty_days_value}")
        
        # حساب الجزاء
        if absence_days_corrected <= grace_days:
            penalty_days = 0.0
            print(f"\n[10] نتيجة الجزاء:")
            print(f"    - أيام الغياب: {absence_days_corrected}")
            print(f"    - الجزاء: 0 (ضمن المسموح)")
        else:
            extra_days = absence_days_corrected - grace_days
            penalty_days = extra_days * penalty_days_value
            print(f"\n[10] نتيجة الجزاء:")
            print(f"    - أيام الغياب: {absence_days_corrected}")
            print(f"    - أيام زائدة: {extra_days}")
            print(f"    - الجزاء: {penalty_days} يوم")
        
        # 11. حساب القيمة المالية
        daily_salary = HRPolicy.calculate_daily_salary(employee.basic_salary)
        penalty_amount = penalty_days * daily_salary
        
        print(f"\n[11] القيمة المالية:")
        print(f"    - الراتب الأساسي: {employee.basic_salary:.2f}")
        print(f"    - الراتب اليومي: {daily_salary:.2f}")
        print(f"    - قيمة الجزاء: {penalty_amount:.2f} جنيه")
        
        # 12. التحقق من استدعاء الدالة الفعلي
        print(f"\n[12] التحقق من استدعاء دالة الجزاء:")
        
        # محاكاة الحساب الفعلي
        attendance_data = calculator.calculate_attendance_deductions(
            daily_records, employee, employee.basic_salary
        )
        
        print(f"    - أيام الحضور المحسوبة: {attendance_data['attendance_days']}")
        print(f"    - أيام الغياب المحسوبة: {attendance_data['absence_days']}")
        print(f"    - أيام الجزاء المحسوبة: {attendance_data['absence_penalty_days']}")
        print(f"    - قيمة الجزاء المحسوبة: {attendance_data['absence_penalty_deduction']:.2f}")
        
        # 13. المقارنة
        print(f"\n[13] المقارنة والتحليل:")
        print(f"    - الغياب الفعلي (بعد الاستبعادات): {absence_days_corrected}")
        print(f"    - الغياب المحسوب في النظام: {attendance_data['absence_days']}")
        
        if absence_days_corrected != attendance_data['absence_days']:
            print(f"    [خطأ] عدم تطابق في حساب الغياب!")
            print(f"    السبب المحتمل:")
            if attendance_data['absence_days'] > absence_days_corrected:
                print(f"      - النظام يحسب الإجازات الأسبوعية كغياب")
                print(f"      - النظام يحسب الأيام المستقبلية كغياب")
            else:
                print(f"      - هناك فلتر يستبعد بعض الأيام")
        else:
            print(f"    [صحيح] الحساب متطابق")
        
        print(f"\n" + "="*80)
        
    finally:
        session.close()

def main():
    """الدالة الرئيسية"""
    
    # اختبار الموظف 236 (الذي يوجد مشكلة فيه)
    print("\n\n")
    print("*"*80)
    print("اختبار الموظف 236 (الموظف الذي يوجد مشكلة فيه)")
    print("*"*80)
    
    trace_absence_calculation(130, 2, 2026)
    
    # اختبار موظف آخر
    print("\n\n")
    print("*"*80)
    print("اختبار موظف آخر للمقارنة")
    print("*"*80)
    
    db = DBManager('core/hr.db')
    session = db.get_session()
    
    try:
        employee = session.query(Employee).filter_by(is_active=True).first()
        if employee:
            trace_absence_calculation(employee.id, 2, 2026)
    finally:
        session.close()

if __name__ == "__main__":
    main()
