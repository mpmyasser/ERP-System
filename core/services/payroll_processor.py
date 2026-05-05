"""
Payroll Processor Service
=========================
Professional payroll calculation service based on company HR policy.

This module handles all payroll-related calculations including:
- Monthly salary calculation
- Attendance deductions (lateness, absence)
- Overtime calculations
- Incentive calculations
- Loans deductions
- Permissions deductions
- Administrative penalties

All calculations are based on the official HR policy (policy/hr_policy.py)
"""

from datetime import datetime, date, timedelta
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from policy.hr_policy import HRPolicy
from database_models import Employee, DailyRecord, Loan, PenaltyBonus, Bonus, Permission, PublicHoliday, Leave, LeaveStatus, LeaveTypeEnum


class PayrollCalculator:
    """
    Professional payroll calculator based on company HR policy
    """
    
    def __init__(self, db):
        """
        Initialize the payroll calculator
        
        Args:
            db: DBManager instance
        """
        self.db = db
        self.session = db.get_session()
        
    @staticmethod
    def get_salary_month_date_range(month: int, year: int):
        """
        Get the date range for a salary month.
        Dynamic range based on HRPolicy settings.
        """
        start_day = HRPolicy.PAYROLL_START_DAY
        end_day = HRPolicy.PAYROLL_END_DAY
        
        if month == 1:
            start_date = date(year - 1, 12, start_day)
            end_date = date(year, 1, end_day)
        else:
            start_date = date(year, month - 1, start_day)
            end_date = date(year, month, end_day)
        return start_date, end_date
    
    def _get_effective_salary(self, employee: Employee, target_date: date) -> float:
        """
        البحث عن الراتب الذي كان فعالاً في تاريخ معين بناءً على سجل التاريخ.
        إذا لم يوجد سجل، يتم استخدام الراتب الحالي للموظف.
        """
        from datetime import datetime, time
        # تحويل target_date إلى datetime في نهاية اليوم لضمان شمولية التعديلات في نفس اليوم
        target_dt = datetime.combine(target_date, time.max)

        from core.database_models import SalaryHistory
        # البحث عن أحدث سجل تاريخي فعال (تاريخ التفعيل <= التاريخ المستهدف)
        history = self.session.query(SalaryHistory)\
            .filter(SalaryHistory.employee_id == employee.id,
                    SalaryHistory.effective_date <= target_dt)\
            .order_by(SalaryHistory.effective_date.desc())\
            .first()
        
        if history:
            return history.new_salary

        # إذا لم يوجد أي سجل فعال قبل التاريخ المطلوب، استخدم أقدم سجل كراتب سابق
        earliest = self.session.query(SalaryHistory)\
            .filter(SalaryHistory.employee_id == employee.id)\
            .order_by(SalaryHistory.effective_date.asc())\
            .first()

        if earliest:
            return earliest.old_salary

        # إذا لم يوجد أي سجل تاريخي، نستخدم الراتب الحالي
        return employee.basic_salary
    
    
    def calculate_employee_payroll(self, emp_id: int, year: int, month: int) -> Dict:
        """
        حساب مرتب موظف واحد لشهر محدد.
        يتضمن:
        - جلب بيانات الموظف
        - الحضور والانصراف
        - السلف
        - الجزاءات
        - حساب إجمالي المستحقات
        - حساب الاستقطاعات
        - حساب صافي المرتب
        
        Args:
            emp_id: معرف الموظف
            year: السنة
            month: الشهر (1-12)
            
        Returns:
            dict: بيانات الراتب الشهري الكاملة
        """
        return self.calculate_monthly_payroll(emp_id, month, year)
    
    
    def calculate_monthly_payroll(self, employee_id: int, month: int, year: int) -> Dict:
        """
        حساب الراتب الشهري الكامل للموظف
        """
        employee = self.session.query(Employee).filter_by(id=employee_id).first()
        if not employee:
            raise ValueError(f"لم يتم العثور على الموظف {employee_id}")
        
        daily_records = self._get_monthly_records(employee_id, month, year)
        start_date, end_date = self.get_salary_month_date_range(month, year)
        
        effective_basic_salary = self._get_effective_salary(employee, end_date)

        configured_work_days = int(HRPolicy.WORKING_DAYS_PER_MONTH or 26)
        if configured_work_days <= 0:
            configured_work_days = 26

        daily_salary = (effective_basic_salary / configured_work_days) if configured_work_days > 0 else 0.0
        attendance_data = self.calculate_attendance_deductions(daily_records, employee, effective_basic_salary, start_date, end_date)
        paid_leave_days = self._get_paid_leave_days(employee_id, start_date, end_date, daily_records)
        unpaid_leave_days = self._get_unpaid_leave_days(employee_id, start_date, end_date, daily_records)
        absence_days_for_salary = max(0, int(attendance_data.get('absence_days', 0) or 0))
        today = date.today()

        is_hospitality = (employee.salary_type == 'ضيافة')
        
        if today < start_date:
            payable_days = 0
            unpaid_missing_days = 0
        elif is_hospitality:
            # CRITICAL: Hospitality employees get full salary regardless of attendance.
            # Only Loans and Insurance are allowed as deductions for this category.
            payable_days = configured_work_days
            unpaid_missing_days = 0
        elif today <= end_date:
            # Open payroll period (current month): dynamic based on actual signed attendance + paid leaves + excused holidays.
            payable_days = min(configured_work_days, attendance_data['attendance_days'] + paid_leave_days + attendance_data.get('excused_holiday_days', 0))
            elapsed_work_days = min(configured_work_days, self._count_working_days_in_range(start_date, today))
            unpaid_missing_days = max(0, elapsed_work_days - payable_days)
        else:
            # Closed payroll period: configured days minus absence and unpaid leave.
            payable_days = max(0, configured_work_days - absence_days_for_salary - unpaid_leave_days)
            payable_days = min(configured_work_days, payable_days)
            unpaid_missing_days = min(configured_work_days, absence_days_for_salary + unpaid_leave_days)
        overtime_value = self.calculate_overtime(daily_records, employee, effective_basic_salary)
        incentive_value = self.calculate_incentive(attendance_data['incentive_attendance_days'], employee.incentive_allowance)
        loans_deduction = self.calculate_loans_deduction(employee_id, month, year)
        permissions_deduction = self.calculate_permissions_deduction(daily_records, employee, effective_basic_salary)
        admin_penalties = self._get_administrative_penalties(employee_id, month, year)
        
        # الراتب الإجمالي = أجر اليوم × (الحضور الفعلي + الإجازات المدفوعة)
        gross_salary = payable_days * daily_salary
        
        # حافز الانتظام
        regularity_incentive_value = 0.0
        if employee.salary_type == 'ضيافة' or attendance_data['incentive_attendance_days'] >= HRPolicy.INCENTIVE_FULL_THRESHOLD:
            regularity_incentive_value = getattr(employee, 'regularity_incentive', 0.0) or 0.0
        
        # المكافآت
        bonuses_with_salary = 0.0
        try:
            bonuses_true = self.session.query(Bonus).filter(
                Bonus.employee_id == employee_id,
                Bonus.paid_with_salary == True,
                Bonus.date_awarded >= start_date,
                Bonus.date_awarded <= end_date
            ).all()
            bonuses_with_salary += sum(b.amount for b in bonuses_true) if bonuses_true else 0.0
            
            legacy_bonuses = self.session.query(PenaltyBonus).filter(
                PenaltyBonus.employee_id == employee_id,
                PenaltyBonus.type == "Bonus",
                PenaltyBonus.date >= start_date,
                PenaltyBonus.date <= end_date
            ).all()
            bonuses_with_salary += sum(b.amount for b in legacy_bonuses) if legacy_bonuses else 0.0
        except: pass
        
        bonuses_paid_during_month = 0.0
        try:
            bonuses_false = self.session.query(Bonus).filter(
                Bonus.employee_id == employee_id,
                Bonus.paid_with_salary == False,
                Bonus.date_awarded >= start_date,
                Bonus.date_awarded <= end_date
            ).all()
            bonuses_paid_during_month = sum(b.amount for b in bonuses_false) if bonuses_false else 0.0
        except: pass
        
        # إجمالي المستحقات
        total_additions = overtime_value + incentive_value + employee.transport_allowance + regularity_incentive_value + bonuses_with_salary
        
        # التأمين
        insurance_data = employee.calculate_insurance_values()
        insurance_deduction = insurance_data['employee_deduction']
        
        # إجمالي الاستقطاعات
        if is_hospitality:
            # CRITICAL: Hospitality only pays for Loans and Insurance (as per company policy).
            total_deductions = loans_deduction + insurance_deduction
        else:
            total_deductions = (
                attendance_data['lateness_deduction'] +
                attendance_data.get('early_deduction', 0.0) +
                attendance_data['absence_penalty_deduction'] +
                loans_deduction +
                permissions_deduction +
                admin_penalties +
                insurance_deduction
            )
        
        # الراتب الصافي
        net_salary = gross_salary + total_additions - total_deductions
        rounding_base = HRPolicy.ROUNDING_BASE
        if rounding_base > 0:
            net_salary = round(float(net_salary) / rounding_base) * rounding_base
        
        return {
            'Employee': employee.name,
            'Employee ID': employee_id,
            'Month': month,
            'Year': year,
            'Basic Salary': effective_basic_salary,
            'Gross Salary': gross_salary,
            'Daily Salary': daily_salary,
            'Paid Leave Days': paid_leave_days,
            'Unpaid Leave Days': unpaid_leave_days,
            'Payable Days': payable_days,
            'Unpaid Missing Days': unpaid_missing_days,
            'Incentive': incentive_value,
            'Regularity Incentive': regularity_incentive_value,
            'Bonuses': bonuses_with_salary, # 🆕 إجمالي المكافآت المستحقة
            'Bonuses Paid During Month': bonuses_paid_during_month, # 🆕 ما تم صرفه خلال الشهر
            'OT Value': overtime_value,
            'Transport Allowance': employee.transport_allowance,
            'Total Additions': total_additions,
            'Attendance Days': payable_days,
            'Actual Days': payable_days,  # للتوافق مع التقارير الأخرى
            'Present Attendance Days': attendance_data['attendance_days'],
            'Absence Days': unpaid_missing_days,
            'Penalty Absence Days': attendance_data['absence_days'],
            'Lateness Deduction': attendance_data['lateness_deduction'],
            'Early Deduction': attendance_data['early_deduction'],
            'Absence Deduction': 0.0,
            'Absence Penalty Deduction': attendance_data['absence_penalty_deduction'],
            'Permissions Deduction': permissions_deduction,
            'Loan Deduction': loans_deduction,
            'Admin Penalties': admin_penalties,
            'Insurance': insurance_deduction,
            'Insurance_Company_Cost': insurance_data['company_cost'],
            'Insurance_Total': insurance_data['total_insurance'],
            'Insurance_Policy': employee.insurance_policy,
            'Total Deductions': total_deductions,
            'Net Salary': net_salary,
            'Calculation Type': "حساب أيام فعلية"
        }
    
    
    def calculate_attendance_deductions(self, daily_records: List[DailyRecord], employee: Employee, basic_salary_override: float = None, start_date: date = None, end_date: date = None) -> Dict:
        """
        حساب خصومات الحضور (التأخير، الغياب، الجزاءات)
        
        Args:
            daily_records: سجلات الحضور اليومية
            employee: بيانات الموظف
            basic_salary_override: الراتب الأساسي (يستخدم في حالة الأثر الرجعي)
            start_date: تاريخ بداية الفترة
            end_date: تاريخ نهاية الفترة
            
        Returns:
            dict: تفاصيل خصومات الحضور
        """
        basic_salary = basic_salary_override if basic_salary_override is not None else employee.basic_salary

        if not basic_salary or basic_salary <= 0:
            return {
                'attendance_days': 0,
                'absence_days': 0,
                'late_minutes': 0,
                'lateness_deduction': 0.0,
                'early_minutes': 0,
                'early_deduction': 0.0,
                'absence_deduction': 0.0,
                'absence_penalty_days': 0,
                'absence_penalty_deduction': 0.0,
                'overtime_hours': 0.0,
                'permissions_hours': 0.0,
            }
        
        daily_hours = employee.daily_work_hours if employee.daily_work_hours else 8.0
        hourly_salary = HRPolicy.calculate_hourly_salary(basic_salary, daily_hours)
        daily_salary = HRPolicy.calculate_daily_salary(basic_salary)
        
        total_late_minutes = 0
        total_lateness_deduction = 0.0
        total_early_minutes = 0
        total_early_deduction = 0.0
        total_absence_days = 0
        total_overtime_hours = 0.0
        total_permissions_hours = 0.0
        attendance_days = len({r.date for r in daily_records})
        
        for record in daily_records:
            if record.late_minutes and record.late_minutes > 0:
                total_late_minutes += record.late_minutes
                deduction = self.calculate_lateness_penalty(record.late_minutes, hourly_salary)
                total_lateness_deduction += deduction
            
            if record.early_leave_minutes and record.early_leave_minutes > 0:
                total_early_minutes += record.early_leave_minutes
                deduction = HRPolicy.calculate_early_departure_deduction(record.early_leave_minutes, hourly_salary)
                total_early_deduction += deduction
            
            if record.overtime_hours and record.overtime_hours > 0:
                total_overtime_hours += record.overtime_hours
            
            if record.manual_adjustment and record.manual_adjustment < 0:
                hours = abs(record.manual_adjustment)
                total_permissions_hours += hours
        
        # حساب الغياب الفعلي
        if start_date and end_date:
            today = date.today()
            actual_end_date = min(end_date, today)
            total_calendar_days = (actual_end_date - start_date).days + 1
            
            # استبعد الإجازات الأسبوعية
            weekly_off_count = 0
            for d in range(total_calendar_days):
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
            
            # استبعد الإجازات المعتمدة
            leaves = self.session.query(Leave).filter(
                Leave.employee_id == employee.id,
                Leave.start_date <= actual_end_date,
                Leave.end_date >= start_date,
                Leave.status == LeaveStatus.APPROVED.value
            ).all()
            
            leave_days = 0
            for leave in leaves:
                d = leave.start_date
                while d <= leave.end_date:
                    if start_date <= d <= actual_end_date:
                        leave_days += 1
                    d += timedelta(days=1)
            
            # حساب العطلات الرسمية وتأثيرها (Public Holidays)
            # تم إضافة هذا الجزء لتنفيذ طلب الإجازات الخاصة (مثل ليلة العيد)
            public_holidays = self.session.query(PublicHoliday).filter(
                PublicHoliday.start_date <= actual_end_date,
                PublicHoliday.end_date >= start_date
            ).all()
            
            target_weekday = weekday_mapping.get(HRPolicy.WEEKLY_HOLIDAY, "Friday")
            excused_holiday_days = 0  # أيام عطلة سيتم استثناؤها من الغياب (فتصبح مدفوعة)
            unpaid_holiday_days = 0   # أيام عطلة غير مدفوعة (لغير المؤمنين) ولكن لا تسبب جزاء
            incentive_virtual_presence = 0 # أيام ستضاف للحضور لمقاصد حافز الانتظام فقط
            
            attended_dates = {r.date for r in daily_records}
            
            for h in public_holidays:
                d = h.start_date
                while d <= h.end_date:
                    if start_date <= d <= actual_end_date:
                        # استبعد إذا كان اليوم هو يوم الإجازة الأسبوعية أصلاً
                        if d.strftime('%A') != target_weekday:
                            is_special = getattr(h, 'is_unpaid_for_uninsured', False)
                            
                            # لضمان عدم التأثير على الحافز (للمؤمن وغير المؤمن)
                            if is_special and d not in attended_dates:
                                incentive_virtual_presence += 1
                            
                            # المنطق المالي والجزائي
                            if d not in attended_dates:
                                if is_special and employee.is_insured:
                                    # إجازة خاصة + مؤمن عليه -> مدفوعة (استثنها من الغياب الكلي)
                                    excused_holiday_days += 1
                                else:
                                    # إجازة (عادية أو خاصة غير مدفوعة) -> تضاف للغياب المالي لكن تُطرح من الجزاء
                                    unpaid_holiday_days += 1
                                
                    d += timedelta(days=1)

            # الغياب المالي = الأيام الفعلية - الحضور - الإجازات الأسبوعية - الإجازات المعتمدة - العطلات المدفوعة
            total_absence_days = total_calendar_days - attendance_days - weekly_off_count - leave_days - excused_holiday_days
            total_absence_days = max(0, total_absence_days)
            
            # أيام الجزاء الإداري = إجمالي الغياب - أيام العطلات التي لم تُدفع (لأن العطلة لا جزاء عليها)
            penalty_eligible_days = max(0, total_absence_days - unpaid_holiday_days)
        else:
            total_absence_days = 0
            penalty_eligible_days = 0
            incentive_virtual_presence = 0
            excused_holiday_days = 0
        
        absence_deduction = total_absence_days * daily_salary
        absence_penalty_days = self.calculate_absence_penalty(penalty_eligible_days)
        absence_penalty_deduction = absence_penalty_days * daily_salary
        
        return {
            'attendance_days': attendance_days,
            'incentive_attendance_days': attendance_days + incentive_virtual_presence,
            'excused_holiday_days': excused_holiday_days,
            'absence_days': total_absence_days,
            'late_minutes': total_late_minutes,
            'lateness_deduction': total_lateness_deduction,
            'early_minutes': total_early_minutes,
            'early_deduction': total_early_deduction,
            'absence_deduction': absence_deduction,
            'absence_penalty_days': absence_penalty_days,
            'absence_penalty_deduction': absence_penalty_deduction,
            'overtime_hours': total_overtime_hours,
            'permissions_hours': total_permissions_hours,
        }
    
    
    def calculate_lateness_penalty(self, late_minutes: int, hourly_salary: float) -> float:
        """
        حساب خصم التأخير
        
        قواعد:
        - أول 15 دقيقة: خصم عادي
        - 15-60 دقيقة: كل دقيقة = دقيقتين خصم
        
        Args:
            late_minutes: عدد دقائق التأخير
            hourly_salary: راتب الساعة
            
        Returns:
            float: قيمة الخصم
        """
        return HRPolicy.calculate_late_deduction(late_minutes, hourly_salary)
    
    
    def calculate_absence_penalty(self, days_absent: int) -> float:
        """
        حساب جزاء الغياب (ربع يوم لكل يوم بعد اليومين الأول)
        
        Args:
            days_absent: عدد أيام الغياب
            
        Returns:
            float: عدد أيام الجزاء
        """
        return HRPolicy.calculate_absence_penalty(days_absent)
    
    
    def calculate_overtime(self, daily_records: List[DailyRecord], employee: Employee, basic_salary_override: float = None) -> float:
        """
        حساب قيمة الإضافي
        
        قواعد:
        - ساعة إضافي = راتب الساعة × 1.5
        - يجب إكمال 30 دقيقة على الأقل
        
        Args:
            daily_records: سجلات الحضور
            employee: بيانات الموظف
            
        Returns:
            float: قيمة الإضافي
        """
        if not employee.overtime_allowed:
            return 0.0
        
        total_overtime_hours = 0.0
        for record in daily_records:
            if record.overtime_hours and record.overtime_hours > 0:
                total_overtime_hours += record.overtime_hours
        
        # Check minimum 30 minutes
        if total_overtime_hours < (HRPolicy.OVERTIME_MIN_MINUTES / 60.0):
            return 0.0
        
        daily_hours = employee.daily_work_hours if employee.daily_work_hours else 8.0
        basic_salary = basic_salary_override if basic_salary_override is not None else employee.basic_salary
        hourly_salary = HRPolicy.calculate_hourly_salary(basic_salary, daily_hours)
        
        return HRPolicy.calculate_overtime_pay(total_overtime_hours, hourly_salary)
    
    
    def calculate_incentive(self, attendance_days: int, full_incentive_amount: float) -> float:
        """
        حساب الحافز
        
        قواعد:
        - 24 يوم فأكثر: حافز كامل
        - 15 يوم فأكثر: نصف حافز
        - أقل من 15 يوم: لا يوجد حافز
        
        Args:
            attendance_days: عدد أيام الحضور
            full_incentive_amount: قيمة الحافز الكامل
            
        Returns:
            float: قيمة الحافز المستحقة
        """
        if not full_incentive_amount:
            return 0.0
        
        return HRPolicy.calculate_incentive_amount(attendance_days, full_incentive_amount)
    
    
    def calculate_loans_deduction(self, employee_id: int, month: int, year: int) -> float:
        """
        حساب قسط السلف الشهري
        
        Args:
            employee_id: معرف الموظف
            month: الشهر
            year: السنة
            
        Returns:
            float: قيمة القسط المستحق
        """
        # Get active loans
        active_loans = self.session.query(Loan).filter_by(
            employee_id=employee_id,
            is_paid_off=False
        ).all()
        
        total_installment = 0.0
        # --- تحديد التاريخ المرجعي لهذا الشهر (يوم 25) ---
        # نستخدم يوم 25 لنعرف الرصيد "قبل" أو "خلال" معالجة هذا الشهر
        from datetime import date as dt_date
        calculation_date = dt_date(year, month, 25)

        for loan in active_loans:
            # إذا كانت السلفة بدأت بعد تاريخ الحساب الحالي، فتجاهلها
            if loan.date > calculation_date:
                continue

            # الرصيد المتبقي في نهاية هذا الشهر (قبل خصم قسط هذا الشهر)
            remaining_at_end_of_month = loan.get_remaining_balance(calculation_date)
            
            # --- منطق استثناء الأشهر ---
            if loan.excluded_months:
                excluded_months_list = []
                for tok in loan.excluded_months.split(','):
                    t = tok.strip()
                    if not t:
                        continue
                    try:
                        excluded_months_list.append(int(t))
                    except ValueError:
                        try:
                            f = float(t)
                            if f.is_integer():
                                excluded_months_list.append(int(f))
                        except ValueError:
                            continue
                if month in excluded_months_list:
                    continue

            # --- الحساب العادي للقسط ---
            if remaining_at_end_of_month > 0 and loan.installments_count > 0:
                base_installment = loan.amount / loan.installments_count
                
                # التأكد من أن القسط لا يتجاوز الرصيد المتبقي
                installment_to_deduct = min(base_installment, remaining_at_end_of_month)
                total_installment += installment_to_deduct
        
        return total_installment
    
    
    def calculate_permissions_deduction(self, daily_records: List[DailyRecord], employee: Employee, basic_salary_override: float = None) -> float:
        """
        حساب خصم التصاريح
        """
        # We need the date range from the daily_records to query permissions
        if not daily_records:
            return 0.0
            
        start_date = min(r.date for r in daily_records)
        end_date = max(r.date for r in daily_records)
        
        permissions = self.session.query(Permission).filter(
            Permission.employee_id == employee.id,
            Permission.date >= start_date,
            Permission.date <= end_date,
            Permission.is_paid == False # Only unpaid permissions are deducted
        ).all()
        
        total_permissions_hours = 0.0
        for p in permissions:
            # Calculate duration in hours
            p_start = p.from_time.hour * 60 + p.from_time.minute
            p_end = p.to_time.hour * 60 + p.to_time.minute
            duration_minutes = max(0, p_end - p_start)
            total_permissions_hours += (duration_minutes / 60.0)
            
        if total_permissions_hours == 0:
            return 0.0
            
        daily_hours = employee.daily_work_hours if employee.daily_work_hours else 8.0
        basic_salary = basic_salary_override if basic_salary_override is not None else employee.basic_salary
        hourly_salary = HRPolicy.calculate_hourly_salary(basic_salary, daily_hours)
        
        return total_permissions_hours * hourly_salary * HRPolicy.PERMISSION_DEDUCTION_RATE
    
    
    def _get_monthly_records(self, employee_id: int, month: int, year: int) -> List[DailyRecord]:
        """Get all daily records for an employee in a specific salary month"""
        start_date, end_date = self.get_salary_month_date_range(month, year)
        work_statuses = ['Present', 'Late', 'حاضر', 'عمل']
        
        records = self.session.query(DailyRecord).filter(
            DailyRecord.employee_id == employee_id,
            DailyRecord.date >= start_date,
            DailyRecord.date <= end_date
        ).filter(
            or_(
                DailyRecord.check_in.isnot(None),
                DailyRecord.check_out.isnot(None),
                DailyRecord.status.in_(work_statuses)
            )
        ).order_by(DailyRecord.date.asc(), DailyRecord.id.desc()).all()

        # Deduplicate by date to avoid overcounting when duplicate rows exist.
        def _score(rec: DailyRecord) -> int:
            return int(rec.check_in is not None) + int(rec.check_out is not None)

        best_by_date = {}
        for rec in records:
            current = best_by_date.get(rec.date)
            if current is None:
                best_by_date[rec.date] = rec
                continue

            if _score(rec) > _score(current):
                best_by_date[rec.date] = rec
            elif _score(rec) == _score(current) and rec.id > current.id:
                best_by_date[rec.date] = rec

        return [best_by_date[d] for d in sorted(best_by_date.keys())]

    def _get_paid_leave_days(self, employee_id: int, start_date: date, end_date: date, daily_records: List[DailyRecord]) -> int:
        """Count approved paid leave days in range, excluding overlap with attendance/weekends/official holidays."""
        leaves = self.session.query(Leave).filter(
            Leave.employee_id == employee_id,
            Leave.start_date <= end_date,
            Leave.end_date >= start_date,
            Leave.status == LeaveStatus.APPROVED.value,
            Leave.is_paid == True,
            Leave.leave_type != LeaveTypeEnum.UNPAID.value
        ).all()

        attendance_dates = {r.date for r in daily_records}
        weekday_mapping = {
            "الاثنين": "Monday",
            "الثلاثاء": "Tuesday",
            "الأربعاء": "Wednesday",
            "الخميس": "Thursday",
            "الجمعة": "Friday",
            "السبت": "Saturday",
            "الأحد": "Sunday"
        }
        weekly_off_day = weekday_mapping.get(HRPolicy.WEEKLY_HOLIDAY, "Friday")

        holiday_rows = self.session.query(PublicHoliday).filter(
            PublicHoliday.start_date <= end_date,
            PublicHoliday.end_date >= start_date
        ).all()
        official_holiday_dates = set()
        for holiday in holiday_rows:
            d = holiday.start_date
            while d <= holiday.end_date:
                if start_date <= d <= end_date:
                    official_holiday_dates.add(d)
                d += timedelta(days=1)

        leave_dates = set()
        for leave in leaves:
            if leave.leave_type == LeaveTypeEnum.UNPAID.value:
                continue
            d = leave.start_date
            while d <= leave.end_date:
                if not (start_date <= d <= end_date):
                    d += timedelta(days=1)
                    continue

                if d in attendance_dates:
                    d += timedelta(days=1)
                    continue

                if d in official_holiday_dates:
                    d += timedelta(days=1)
                    continue

                if d.strftime('%A') == weekly_off_day:
                    d += timedelta(days=1)
                    continue

                if start_date <= d <= end_date:
                    leave_dates.add(d)
                d += timedelta(days=1)

        return len(leave_dates)

    def _get_unpaid_leave_days(self, employee_id: int, start_date: date, end_date: date, daily_records: List[DailyRecord]) -> int:
        """Count approved unpaid leave days in range, excluding overlap with attendance/weekends/official holidays."""
        leaves = self.session.query(Leave).filter(
            Leave.employee_id == employee_id,
            Leave.start_date <= end_date,
            Leave.end_date >= start_date,
            Leave.status == LeaveStatus.APPROVED.value,
            or_(
                Leave.is_paid == False,
                Leave.leave_type == LeaveTypeEnum.UNPAID.value
            )
        ).all()

        attendance_dates = {r.date for r in daily_records}
        weekday_mapping = {
            "الاثنين": "Monday",
            "الثلاثاء": "Tuesday",
            "الأربعاء": "Wednesday",
            "الخميس": "Thursday",
            "الجمعة": "Friday",
            "السبت": "Saturday",
            "الأحد": "Sunday"
        }
        weekly_off_day = weekday_mapping.get(HRPolicy.WEEKLY_HOLIDAY, "Friday")

        holiday_rows = self.session.query(PublicHoliday).filter(
            PublicHoliday.start_date <= end_date,
            PublicHoliday.end_date >= start_date
        ).all()
        official_holiday_dates = set()
        for holiday in holiday_rows:
            d = holiday.start_date
            while d <= holiday.end_date:
                if start_date <= d <= end_date:
                    official_holiday_dates.add(d)
                d += timedelta(days=1)

        leave_dates = set()
        for leave in leaves:
            d = leave.start_date
            while d <= leave.end_date:
                if not (start_date <= d <= end_date):
                    d += timedelta(days=1)
                    continue

                if d in attendance_dates:
                    d += timedelta(days=1)
                    continue

                if d in official_holiday_dates:
                    d += timedelta(days=1)
                    continue

                if d.strftime('%A') == weekly_off_day:
                    d += timedelta(days=1)
                    continue

                leave_dates.add(d)
                d += timedelta(days=1)

        return len(leave_dates)

    def _count_working_days_in_range(self, start_date: date, end_date: date) -> int:
        """Count working days in range excluding weekly off and official holidays."""
        if end_date < start_date:
            return 0

        weekday_mapping = {
            "الاثنين": "Monday",
            "الثلاثاء": "Tuesday",
            "الأربعاء": "Wednesday",
            "الخميس": "Thursday",
            "الجمعة": "Friday",
            "السبت": "Saturday",
            "الأحد": "Sunday"
        }
        weekly_off_day = weekday_mapping.get(HRPolicy.WEEKLY_HOLIDAY, "Friday")

        holiday_rows = self.session.query(PublicHoliday).filter(
            PublicHoliday.start_date <= end_date,
            PublicHoliday.end_date >= start_date
        ).all()
        official_holiday_dates = set()
        for holiday in holiday_rows:
            d = holiday.start_date
            while d <= holiday.end_date:
                if start_date <= d <= end_date:
                    official_holiday_dates.add(d)
                d += timedelta(days=1)

        total = 0
        d = start_date
        while d <= end_date:
            if d.strftime('%A') != weekly_off_day and d not in official_holiday_dates:
                total += 1
            d += timedelta(days=1)

        return total
    
    
    def _get_administrative_penalties(self, employee_id: int, month: int, year: int) -> float:
        """Get administrative penalties for the month"""
        start_date, end_date = self.get_salary_month_date_range(month, year)
        
        penalties = self.session.query(PenaltyBonus).filter(
            PenaltyBonus.employee_id == employee_id,
            PenaltyBonus.type == "Penalty",
            PenaltyBonus.date >= start_date,
            PenaltyBonus.date <= end_date
        ).all()
        
        total = sum(p.amount for p in penalties if p.amount)
        return total
    
    
    def get_detailed_payroll_report(self, employee_id: int, month: int, year: int) -> Dict:
        """
        Get detailed payroll report for an employee
        """
        # Get employee with department eagerly loaded
        from sqlalchemy.orm import joinedload
        employee = self.session.query(Employee).options(joinedload(Employee.department)).filter_by(id=employee_id).first()
        if not employee:
            raise ValueError(f"لم يتم العثور على الموظف {employee_id}")
        
        # 1. Get Summary Stats from the core calculator to ensure 100% consistency
        summary_data = self.calculate_monthly_payroll(employee_id, month, year)
        
        # 2. Daily Details
        daily_records = self._get_monthly_records(employee_id, month, year)
        start_date, end_date = self.get_salary_month_date_range(month, year)
        
        # Create a dictionary of records keyed by date
        records_map = {r.date: r for r in daily_records}
        
        # Pre-fetch permissions for the month to map them
        permissions_query = self.session.query(Permission).filter(
            Permission.employee_id == employee_id,
            Permission.date >= start_date,
            Permission.date <= end_date
        ).all()
        
        from collections import defaultdict
        perms_by_date = defaultdict(list)
        for p in permissions_query:
            perms_by_date[p.date].append(p)
            
        # Fetch Public Holidays
        holidays_query = self.session.query(PublicHoliday).filter(
            PublicHoliday.start_date <= end_date,
            PublicHoliday.end_date >= start_date
        ).all()
        
        holiday_dates = {}
        for h in holidays_query:
            d = h.start_date
            while d <= h.end_date:
                if start_date <= d <= end_date:
                    holiday_dates[d] = h.name
                d += timedelta(days=1)
        
        # Fetch Leaves for the month
        leaves_query = self.session.query(Leave).filter(
            Leave.employee_id == employee_id,
            Leave.start_date <= end_date,
            Leave.end_date >= start_date,
            Leave.status == LeaveStatus.APPROVED.value
        ).all()
        
        leave_dates = {}
        for leave in leaves_query:
            d = leave.start_date
            while d <= leave.end_date:
                if start_date <= d <= end_date:
                    leave_dates[d] = leave.leave_type
                d += timedelta(days=1)
            
        daily_hours = employee.daily_work_hours if employee.daily_work_hours else 8.0
        hourly_salary = HRPolicy.calculate_hourly_salary(employee.basic_salary, daily_hours)
        
        daily_details = []
        # from datetime import timedelta - REMOVED
        
        current_date = start_date
        while current_date <= end_date:
            record = records_map.get(current_date)
            
            day_perms = perms_by_date.get(current_date, [])
            perm_hours = 0.0
            perm_deduction = 0.0
            
            for p in day_perms:
                 p_start = p.from_time.hour * 60 + p.from_time.minute
                 p_end = p.to_time.hour * 60 + p.to_time.minute
                 dur = max(0, (p_end - p_start) / 60.0)
                 perm_hours += dur
                 
                 if not p.is_paid:
                     deduct = dur * hourly_salary * HRPolicy.PERMISSION_DEDUCTION_RATE
                     perm_deduction += deduct

            # Check for holiday
            is_holiday = False
            holiday_name = ""
            
            # Map WEEKLY_HOLIDAY name to day name
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
                is_holiday = True
                holiday_name = "إجازة أسبوعية"
            
            # Check for Public Holiday
            # الشرط الجديد: يجب أن تكون العطلة موجودة AND الموظف يستحق العطلات الرسمية
            if current_date in holiday_dates and getattr(employee, 'entitled_to_official_holidays', True):
                is_holiday = True
                holiday_name = holiday_dates[current_date]


            
            # Check for Leave
            is_leave = False
            leave_type = ""
            if current_date in leave_dates:
                is_leave = True
                leave_type = leave_dates[current_date]
            
            if record:
                daily_details.append({
                    'date': current_date,
                    'check_in': record.check_in,
                    'check_out': record.check_out,
                    'status': record.status,
                    'late_minutes': record.late_minutes or 0,
                    'late_deduction': record.late_deduction_amount,
                    'early_minutes': record.early_leave_minutes or 0,
                    'early_deduction': record.early_deduction_amount,
                    'overtime_hours': record.overtime_hours or 0.0,
                    'overtime_value': record.overtime_pay_amount,
                    'permission_hours': perm_hours,
                    'permission_deduction': perm_deduction,
                    'is_holiday': is_holiday,
                    'holiday_name': holiday_name,
                    'is_leave': is_leave,
                    'leave_type': leave_type
                })
            else:
                # No record entry, just show the day
                status_text = ""
                if is_leave:
                    status_text = leave_type
                elif is_holiday:
                    status_text = holiday_name
                else:
                    status_text = "غائب"
                
                daily_details.append({
                    'date': current_date,
                    'check_in': None,
                    'check_out': None,
                    'status': status_text,
                    'late_minutes': 0,
                    'late_deduction': 0.0,
                    'early_minutes': 0,
                    'early_deduction': 0.0,
                    'overtime_hours': 0.0,
                    'overtime_value': 0.0,
                    'permission_hours': perm_hours,
                    'permission_deduction': perm_deduction,
                    'is_holiday': is_holiday,
                    'holiday_name': holiday_name,
                    'is_leave': is_leave,
                    'leave_type': leave_type
                })
            
            current_date += timedelta(days=1)
            
        # 3. Loans Details
        loans_details = []
        active_loans = self.session.query(Loan).filter_by(employee_id=employee_id).all()
        for loan in active_loans:
             installment = 0.0
             # Use calculation date to see what WAS the balance during this cycle
             from datetime import date as dt_date
             calculation_date = dt_date(year, month, 25)
             rem_balance = loan.get_remaining_balance(calculation_date)
             # Note: logic for showing installment should match calculate_loans_deduction
             # but here we just show what's recorded
             if not loan.is_paid_off and rem_balance > 0:
                 if loan.excluded_months:
                     excluded = []
                     for tok in loan.excluded_months.split(','):
                         t = tok.strip()
                         if not t:
                             continue
                         try:
                             excluded.append(int(t))
                         except ValueError:
                             try:
                                 f = float(t)
                                 if f.is_integer():
                                     excluded.append(int(f))
                             except ValueError:
                                 continue
                     if month not in excluded:
                         installment = min(loan.amount / loan.installments_count, rem_balance)
                 else:
                     installment = min(loan.amount / loan.installments_count, rem_balance)
             
             if loan.date <= end_date and ((start_date <= loan.date <= end_date) or (installment > 0) or (rem_balance > 0)):
                  loans_details.append({
                      'id': loan.id,
                      'type': loan.type,
                      'amount': loan.amount,
                      'date': loan.date,
                      'installment': installment,
                      'remaining': rem_balance,
                      'end_date': loan.end_date
                  })

        # 4. Penalties Details
        penalties_details = []
        raw_penalties = self.session.query(PenaltyBonus).filter(
            PenaltyBonus.employee_id == employee_id,
            PenaltyBonus.type == "Penalty",
            PenaltyBonus.date >= start_date,
            PenaltyBonus.date <= end_date
        ).all()
        
        for p in raw_penalties:
              penalties_details.append({
                  'id': p.id,
                  'date': p.date,
                  'reason': p.reason,
                  'amount': p.amount
              })

        # Final consistent structure
        return {
            'employee_id': employee_id,
            'employee_name': employee.name,
            'employee_code': employee.code,
            'job_title': employee.job_title,
            'department_name': employee.department.name if employee.department else 'غير محدد',
            'basic_salary': summary_data['Basic Salary'],
            'month': month,
            'year': year,
            'daily_details': daily_details,
            'loans_details': loans_details,
            'penalties_details': penalties_details,
            'summary': {
                'gross_salary': summary_data['Gross Salary'],
                'incentive': summary_data['Incentive'],
                'regularity_incentive': summary_data['Regularity Incentive'],
                'bonuses': summary_data['Bonuses'],
                'transport': summary_data['Transport Allowance'],
                'overtime_value': summary_data['OT Value'],
                'total_additions': summary_data['Total Additions'],
                'late_deduction': summary_data['Lateness Deduction'],
                'early_deduction': summary_data['Early Deduction'],
                'absence_deduction': summary_data['Absence Deduction'],
                'daily_salary': summary_data.get('Daily Salary', 0),
                'absence_penalty': summary_data['Absence Penalty Deduction'],
                'permissions_deduction': summary_data['Permissions Deduction'],
                'loans_deduction': summary_data['Loan Deduction'],
                'admin_penalties': summary_data['Admin Penalties'],
                'insurance': summary_data['Insurance'],
                'total_deductions': summary_data['Total Deductions'],
                'net_salary': summary_data['Net Salary'],
                'attendance_days': summary_data['Attendance Days'],
                'absence_days': summary_data['Absence_Days'] if 'Absence_Days' in summary_data else summary_data.get('Absence Days', 0)
            }
        }
