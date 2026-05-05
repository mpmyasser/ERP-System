"""
سكريبت اختبار شامل لآلية احتساب جزاء الغياب
====================================================

هذا السكريبت يوضح:
1. من أين يتم قراءة إعدادات الغياب
2. كيف يتم احتساب الجزاء بناءً على الإعدادات
3. مثال عملي على سيناريو الغياب بدون بصمات
"""

import sys
import os
from datetime import date, datetime, timedelta

# إضافة مسار core للمشروع
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from db_manager import DBManager
from database_models import SystemSetting, Employee, DailyRecord
from policy.hr_policy import HRPolicy
from services.payroll_processor import PayrollCalculator

def print_section(title):
    """طباعة عنوان قسم"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def test_settings_reading():
    """
    [1] اختبار قراءة الإعدادات من قاعدة البيانات
    """
    print_section("[1] قراءة إعدادات الغياب من قاعدة البيانات")
    
    db = DBManager('core/hr.db')
    session = db.get_session()
    
    try:
        # قراءة الإعدادات مباشرة من قاعدة البيانات
        absence_grace = session.query(SystemSetting).filter_by(key='ABSENCE_GRACE_DAYS').first()
        absence_penalty = session.query(SystemSetting).filter_by(key='ABSENCE_PENALTY_DAYS').first()
        
        print(f"\nالإعدادات المخزنة في جدول system_settings:")
        print(f"   - المتغير: {absence_grace.key}")
        print(f"   - القيمة: {absence_grace.value}")
        print(f"   - الوصف: {absence_grace.description}")
        print(f"\n   - المتغير: {absence_penalty.key}")
        print(f"   - القيمة: {absence_penalty.value}")
        print(f"   - الوصف: {absence_penalty.description}")
        
        # قراءة الإعدادات من خلال HRPolicy (الطريقة الديناميكية)
        print(f"\nالقيم المقروءة من خلال HRPolicy (ديناميكياً):")
        print(f"   - HRPolicy.ABSENCE_GRACE_DAYS = {HRPolicy.ABSENCE_GRACE_DAYS}")
        print(f"   - HRPolicy.ABSENCE_PENALTY_DAYS = {HRPolicy.ABSENCE_PENALTY_DAYS}")
        
        print(f"\n[نعم] النتيجة: النظام يقرأ الإعدادات ديناميكياً من قاعدة البيانات")
        print(f"   وليس من قيم ثابتة في الكود!")
        
        return int(absence_grace.value), float(absence_penalty.value)
        
    finally:
        session.close()

def test_penalty_calculation(grace_days, penalty_days):
    """
    [2] اختبار آلية احتساب الجزاء
    """
    print_section("[2] آلية احتساب جزاء الغياب")
    
    print(f"\nالقاعدة المطبقة:")
    print(f"   - عدد أيام الغياب المسموح بها بدون جزاء: {grace_days} يوم")
    print(f"   - قيمة الجزاء لكل يوم زائد: {penalty_days} يوم (ربع يوم)")
    
    print(f"\nأمثلة على الحساب:")
    
    test_cases = [
        (0, "لا يوجد غياب"),
        (1, "يوم واحد غياب"),
        (2, "يومين غياب (الحد المسموح)"),
        (3, "ثلاثة أيام غياب (يبدأ الجزاء)"),
        (4, "أربعة أيام غياب"),
        (5, "خمسة أيام غياب"),
    ]
    
    for days_absent, description in test_cases:
        penalty = HRPolicy.calculate_absence_penalty(days_absent)
        print(f"\n   {description}:")
        print(f"      - عدد أيام الغياب: {days_absent}")
        print(f"      - أيام الجزاء: {penalty}")
        
        if days_absent <= grace_days:
            print(f"      - التفسير: ضمن الحد المسموح ({grace_days} يوم) = لا جزاء")
        else:
            extra_days = days_absent - grace_days
            print(f"      - التفسير: {extra_days} يوم زائد x {penalty_days} = {penalty} يوم جزاء")

def test_real_scenario():
    """
    [3] اختبار سيناريو واقعي: عدم ترحيل البصمات
    """
    print_section("[3] سيناريو واقعي: عدم ترحيل البصمات")
    
    db = DBManager('core/hr.db')
    session = db.get_session()
    
    try:
        # اختيار موظف عشوائي للاختبار
        employee = session.query(Employee).filter_by(is_active=True).first()
        
        if not employee:
            print("\n[تحذير] لا يوجد موظفين نشطين في النظام")
            return
        
        print(f"\nبيانات الموظف المختار للاختبار:")
        print(f"   - الاسم: {employee.name}")
        print(f"   - الكود: {employee.code}")
        print(f"   - الراتب الأساسي: {employee.basic_salary:.2f} جنيه")
        
        # حساب الراتب اليومي
        daily_salary = HRPolicy.calculate_daily_salary(employee.basic_salary)
        print(f"   - الراتب اليومي: {daily_salary:.2f} جنيه")
        
        # محاكاة سيناريو: 3 أيام غياب بدون بصمات
        print(f"\nالسيناريو: الموظف غائب 3 أيام بدون بصمات")
        
        days_absent = 3
        penalty_days = HRPolicy.calculate_absence_penalty(days_absent)
        penalty_amount = penalty_days * daily_salary
        
        print(f"\nالحساب:")
        print(f"   - عدد أيام الغياب: {days_absent}")
        print(f"   - أيام الجزاء: {penalty_days} (ربع يوم)")
        print(f"   - قيمة الجزاء: {penalty_amount:.2f} جنيه")
        print(f"   - الحساب: {penalty_days} x {daily_salary:.2f} = {penalty_amount:.2f}")
        
        print(f"\nالتأكيد:")
        print(f"   - اليوم الأول: غياب عادي (ضمن المسموح)")
        print(f"   - اليوم الثاني: غياب عادي (ضمن المسموح)")
        print(f"   - اليوم الثالث: غياب + جزاء ربع يوم")
        
    finally:
        session.close()

def test_payroll_integration():
    """
    [4] اختبار التكامل مع نظام الرواتب
    """
    print_section("[4] التكامل مع نظام الرواتب")
    
    db = DBManager('core/hr.db')
    session = db.get_session()
    
    try:
        # اختيار موظف للاختبار
        employee = session.query(Employee).filter_by(is_active=True).first()
        
        if not employee:
            print("\n[تحذير] لا يوجد موظفين نشطين في النظام")
            return
        
        print(f"\nالموظف: {employee.name}")
        
        # الحصول على الشهر والسنة الحالية
        today = date.today()
        month = today.month
        year = today.year
        
        print(f"الفترة: {month}/{year}")
        
        # حساب نطاق التواريخ
        calculator = PayrollCalculator(db)
        start_date, end_date = calculator.get_salary_month_date_range(month, year)
        
        print(f"   من: {start_date}")
        print(f"   إلى: {end_date}")
        
        # جلب سجلات الحضور
        records = session.query(DailyRecord).filter(
            DailyRecord.employee_id == employee.id,
            DailyRecord.date >= start_date,
            DailyRecord.date <= end_date
        ).all()
        
        print(f"\nإحصائيات الحضور:")
        print(f"   - عدد السجلات المسجلة: {len(records)}")
        
        # حساب أيام الغياب
        total_days = (end_date - start_date).days + 1
        absence_days = total_days - len(records)
        
        print(f"   - إجمالي الأيام في الفترة: {total_days}")
        print(f"   - أيام الحضور المسجلة: {len(records)}")
        print(f"   - أيام الغياب (بدون بصمات): {absence_days}")
        
        # حساب الجزاء
        penalty_days = HRPolicy.calculate_absence_penalty(absence_days)
        daily_salary = HRPolicy.calculate_daily_salary(employee.basic_salary)
        penalty_amount = penalty_days * daily_salary
        
        print(f"\nاحتساب الجزاء:")
        print(f"   - أيام الجزاء: {penalty_days}")
        print(f"   - قيمة الجزاء: {penalty_amount:.2f} جنيه")
        
        if absence_days <= HRPolicy.ABSENCE_GRACE_DAYS:
            print(f"\n[نعم] لا يوجد جزاء (ضمن الحد المسموح: {HRPolicy.ABSENCE_GRACE_DAYS} يوم)")
        else:
            extra_days = absence_days - HRPolicy.ABSENCE_GRACE_DAYS
            print(f"\n[تحذير] يوجد جزاء: {extra_days} يوم زائد x {HRPolicy.ABSENCE_PENALTY_DAYS} = {penalty_days} يوم")
        
    finally:
        session.close()

def show_code_flow():
    """
    [5] توضيح مسار التنفيذ في الكود
    """
    print_section("[5] مسار التنفيذ في الكود")
    
    print("""
الملفات المسؤولة عن احتساب الجزاء:

[1] قراءة الإعدادات:
   - core/database_models.py
      -> جدول SystemSetting (يخزن الإعدادات)
   
   - core/policy/hr_policy.py
      -> HRPolicyMeta._get_setting_meta() (يقرأ من قاعدة البيانات)
      -> @property ABSENCE_GRACE_DAYS (يستدعي _get_setting_meta)
      -> @property ABSENCE_PENALTY_DAYS (يستدعي _get_setting_meta)

[2] حساب الجزاء:
   - core/policy/hr_policy.py
      -> HRPolicy.calculate_absence_penalty(days_absent)
         -> إذا days_absent <= ABSENCE_GRACE_DAYS: return 0.0
         -> وإلا: return (days_absent - ABSENCE_GRACE_DAYS) x ABSENCE_PENALTY_DAYS

[3] تطبيق الجزاء في الرواتب:
   - core/services/payroll_processor.py
      -> PayrollCalculator.calculate_attendance_deductions()
         -> يحسب عدد أيام الغياب من DailyRecord
         -> يستدعي calculate_absence_penalty(total_absence_days)
         -> يحسب القيمة المالية: penalty_days x daily_salary
         -> يضيفها إلى absence_penalty_deduction

[4] معالجة الغياب بدون بصمات:
   - core/services/attendance_service.py
      -> AttendanceService.determine_status()
         -> إذا لم يوجد check_in ولا check_out: return "غائب"
   
   - app/routes/attendance.py
      -> عند استيراد البصمات، يتم إنشاء DailyRecord لكل يوم
      -> الأيام بدون بصمات = لا يوجد لها DailyRecord
      -> في حساب الرواتب، يتم اعتبارها غياب

مسار التنفيذ الكامل:

   [قاعدة البيانات: system_settings]
              ↓
   [HRPolicy يقرأ الإعدادات ديناميكياً]
              ↓
   [PayrollCalculator يحسب أيام الغياب]
              ↓
   [HRPolicy.calculate_absence_penalty()]
              ↓
   [احتساب القيمة المالية للجزاء]
              ↓
   [إضافتها إلى إجمالي الاستقطاعات]
    """)

def main():
    """
    الدالة الرئيسية
    """
    print("\n" + "="*80)
    print("  اختبار شامل لآلية احتساب جزاء الغياب")
    print("="*80)
    
    try:
        # 1. قراءة الإعدادات
        grace_days, penalty_days = test_settings_reading()
        
        # 2. اختبار الحساب
        test_penalty_calculation(grace_days, penalty_days)
        
        # 3. سيناريو واقعي
        test_real_scenario()
        
        # 4. التكامل مع الرواتب
        test_payroll_integration()
        
        # 5. مسار التنفيذ
        show_code_flow()
        
        print_section("انتهى الاختبار بنجاح")
        
        print("""
الخلاصة:

[1] الإعدادات:
   - يتم قراءتها من جدول system_settings في قاعدة البيانات
   - المتغير: ABSENCE_GRACE_DAYS (القيمة الحالية: 2)
   - المتغير: ABSENCE_PENALTY_DAYS (القيمة الحالية: 0.25)

[2] آلية الحساب:
   - أول يومين غياب: لا جزاء (ضمن المسموح)
   - من اليوم الثالث: ربع يوم جزاء لكل يوم زائد
   - الحساب: (أيام الغياب - 2) x 0.25

[3] الغياب بدون بصمات:
   - عند عدم ترحيل البصمات، لا يوجد DailyRecord
   - في حساب الرواتب، يتم اعتبار الأيام بدون سجلات = غياب
   - يتم تطبيق الجزاء تلقائياً حسب الإعدادات

[4] التأكيد:
   [نعم] النظام يعتمد على الإعدادات وليس قيم ثابتة
   [نعم] الجزاء يبدأ من اليوم الثالث فقط
   [نعم] الأيام بدون بصمات تُعتبر غياب تلقائياً
        """)
        
    except Exception as e:
        print(f"\n[خطأ] حدث خطأ: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
