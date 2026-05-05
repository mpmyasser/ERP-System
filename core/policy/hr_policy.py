"""
سياسة الموارد البشرية للشركة (HR Policy)
======================================

هذا الملف يحتوي على جميع القوانين والسياسات المتعلقة بالحضور والغياب والرواتب.
تم تطوير هذا الكلاس ليعمل كـ "محرك ديناميكي" يقرأ القيم من قاعدة البيانات
تلقائياً دون الحاجة لتغيير الكود في كل مرة تتغير فيها السياسة.
"""

from datetime import time

class HRPolicyMeta(type):
    """
    ميتالكلاس يسمح بجعل الثوابت في HRPolicy تعمل كخصائص ديناميكية (Class Properties)
    تجلب القيم من قاعدة البيانات تلقائياً لضمان التوافق مع الكود القديم.
    """
    def _get_setting_meta(cls, key, default, data_type='int'):
        from flask import current_app
        try:
            db = current_app.db
            session = db.get_session()
            from database_models import SystemSetting
            setting = session.query(SystemSetting).filter_by(key=key).first()
            val = setting.value if setting else default
            session.close()
            
            if data_type == 'int': return int(val)
            if data_type == 'float': return float(val)
            return val
        except:
            return default

    @property
    def WORKING_DAYS_PER_MONTH(cls):
        return cls._get_setting_meta('WORKING_DAYS_PER_MONTH', 26)

    @property
    def LATE_GRACE_PERIOD_MINUTES(cls):
        return cls._get_setting_meta('LATE_GRACE_PERIOD_MINUTES', 10)

    @property
    def LATE_MULTIPLIER(cls):
        return cls._get_setting_meta('LATE_MULTIPLIER', 1, 'float')

    @property
    def EARLY_DEPARTURE_GRACE_PERIOD_MINUTES(cls):
        return cls._get_setting_meta('EARLY_DEPARTURE_GRACE_PERIOD_MINUTES', 0)

    @property
    def EARLY_DEPARTURE_MULTIPLIER(cls):
        return cls._get_setting_meta('EARLY_DEPARTURE_MULTIPLIER', 1, 'float')

    @property
    def ABSENCE_GRACE_DAYS(cls):
        return cls._get_setting_meta('ABSENCE_GRACE_DAYS', 2)

    @property
    def ABSENCE_PENALTY_DAYS(cls):
        return cls._get_setting_meta('ABSENCE_PENALTY_DAYS', 0.25, 'float')

    @property
    def OVERTIME_MIN_MINUTES(cls):
        return cls._get_setting_meta('OVERTIME_MIN_MINUTES', 60)

    @property
    def OVERTIME_RATE(cls):
        return cls._get_setting_meta('OVERTIME_RATE', 1.5, 'float')

    @property
    def OVERTIME_FIRST_HOUR_FIXED(cls):
        val = cls._get_setting_meta('OVERTIME_FIRST_HOUR_FIXED', 'True', 'str')
        return str(val).strip().lower() in ('true', '1', 'yes')

    @property
    def OVERTIME_ROUNDING_MODE(cls):
        return cls._get_setting_meta('OVERTIME_ROUNDING_MODE', 'HALF_HOUR', 'str')

    @property
    def OVERTIME_ROUND_THRESHOLD_MINUTES(cls):
        return cls._get_setting_meta('OVERTIME_ROUND_THRESHOLD_MINUTES', 30)

    @property
    def INCENTIVE_FULL_THRESHOLD(cls):
        return cls._get_setting_meta('INCENTIVE_FULL_THRESHOLD', 24)

    @property
    def INCENTIVE_HALF_THRESHOLD(cls):
        return cls._get_setting_meta('INCENTIVE_HALF_THRESHOLD', 15)

    @property
    def ROUNDING_BASE(cls):
        return cls._get_setting_meta('ROUNDING_BASE', 5)
    
    @property
    def PAYROLL_START_DAY(cls):
        return cls._get_setting_meta('PAYROLL_START_DAY', 26)
    
    @property
    def PAYROLL_END_DAY(cls):
        return cls._get_setting_meta('PAYROLL_END_DAY', 25)

    @property
    def PERMISSION_DEDUCTION_RATE(cls):
        return cls._get_setting_meta('PERMISSION_DEDUCTION_RATE', 1.0, 'float')

class HRPolicy(metaclass=HRPolicyMeta):
    """
    كلاس محرك السياسات المتقدم.
    استخدام metaclass يضمن أن HRPolicy.WORKING_DAYS_PER_MONTH سيجلب القيمة من DB
    وليس من ثابت جامد.
    """
    
    # ثوابت الاستقرار
    WEEKLY_HOLIDAY = "الأحد"
    DEFAULT_START_TIME = time(8, 0)
    DEFAULT_END_TIME = time(16, 0)
    DEFAULT_WORK_HOURS = 8.0
    
    @staticmethod
    def calculate_daily_salary(monthly_salary):
        return monthly_salary / HRPolicy.WORKING_DAYS_PER_MONTH
    
    @staticmethod
    def calculate_hourly_salary(monthly_salary, daily_hours=8.0):
        daily_salary = HRPolicy.calculate_daily_salary(monthly_salary)
        return daily_salary / daily_hours
    
    @staticmethod
    def calculate_late_deduction(late_minutes, hourly_salary):
        if late_minutes <= HRPolicy.LATE_GRACE_PERIOD_MINUTES:
            return 0.0
        extra_minutes = late_minutes - HRPolicy.LATE_GRACE_PERIOD_MINUTES
        return (extra_minutes * HRPolicy.LATE_MULTIPLIER / 60.0) * hourly_salary
    
    @staticmethod
    def calculate_early_departure_deduction(early_minutes, hourly_salary):
        if early_minutes <= HRPolicy.EARLY_DEPARTURE_GRACE_PERIOD_MINUTES:
            return 0.0
        extra_minutes = early_minutes - HRPolicy.EARLY_DEPARTURE_GRACE_PERIOD_MINUTES
        return (extra_minutes * HRPolicy.EARLY_DEPARTURE_MULTIPLIER / 60.0) * hourly_salary
    
    @staticmethod
    def calculate_absence_penalty(days_absent):
        if days_absent <= HRPolicy.ABSENCE_GRACE_DAYS:
            return 0.0
        extra_days = days_absent - HRPolicy.ABSENCE_GRACE_DAYS
        return extra_days * HRPolicy.ABSENCE_PENALTY_DAYS
    
    @staticmethod
    def calculate_incentive_amount(attendance_days, full_incentive_amount):
        if attendance_days >= HRPolicy.INCENTIVE_FULL_THRESHOLD:
            return full_incentive_amount
        elif attendance_days >= HRPolicy.INCENTIVE_HALF_THRESHOLD:
            return full_incentive_amount * 0.5
        else:
            return 0.0
    
    @staticmethod
    def calculate_overtime_hours_rounded(overtime_hours):
        """
        تحويل ساعات الإضافي الخام إلى ساعات مقرَّبة وفق الإعدادات.

        المنطق:
        1. بوابة الاستحقاق: أقل من OVERTIME_MIN_MINUTES → 0
        2. إذا OVERTIME_FIRST_HOUR_FIXED = True:
           - أولى 60 دقيقة = 1 ساعة كاملة
           - يُطبَّق التقريب على المتبقي فقط
        3. إذا OVERTIME_FIRST_HOUR_FIXED = False:
           - يُطبَّق التقريب على كل 60 دقيقة
        """
        total_minutes = overtime_hours * 60.0

        # Gatekeeper
        if total_minutes < HRPolicy.OVERTIME_MIN_MINUTES:
            return 0.0

        threshold = HRPolicy.OVERTIME_ROUND_THRESHOLD_MINUTES
        mode = HRPolicy.OVERTIME_ROUNDING_MODE

        def _round_remainder(remaining_minutes):
            """تقريب الدقائق المتبقية بعد آخر ساعة كاملة."""
            if mode == 'HALF_HOUR':
                if remaining_minutes < threshold:
                    return 0.0
                elif remaining_minutes == threshold:
                    return 0.5
                else:  # > threshold
                    return 1.0
            else:
                # وضع افتراضي: دقيقة بدقيقة
                return remaining_minutes / 60.0

        if HRPolicy.OVERTIME_FIRST_HOUR_FIXED:
            # أول 60 دقيقة = 1 ساعة ثابتة
            remaining = total_minutes - 60.0
            calculated = 1.0 + _round_remainder(remaining)
        else:
            # تقريب على كامل الوقت
            full_hours = int(total_minutes // 60)
            remaining = total_minutes % 60
            calculated = full_hours + _round_remainder(remaining)

        return calculated

    @staticmethod
    def calculate_overtime_pay(overtime_hours, hourly_salary):
        calculated = HRPolicy.calculate_overtime_hours_rounded(overtime_hours)
        if calculated == 0.0:
            return 0.0
        return calculated * hourly_salary * HRPolicy.OVERTIME_RATE

class LoanType:
    MONTHLY = "شهرية"
    EXTENDED = "ممتدة"
    EMERGENCY = "طارئة"

class AttendanceStatus:
    PRESENT = "حاضر"
    ABSENT = "غائب"
    LATE = "متأخر"
    PERMISSION = "تصريح"
    HOLIDAY = "عطلة"
