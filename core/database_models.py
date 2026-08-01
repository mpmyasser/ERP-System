from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Date, Time, DateTime, event, inspect
from sqlalchemy.orm import relationship, declarative_base, Session
from datetime import datetime, date
import enum

# Import new ERP Modules
# (Note: Circular imports might be tricky, so we rely on string references in relationships)
# Usually we import them at the end or handle Base properly.
# For simplicity in this structure, we assume they import Base from here.


Base = declarative_base()

class EmployeeCategory(enum.Enum):
    WORKER = "WORKER"
    EMPLOYEE = "EMPLOYEE"
    SUPERVISOR = "SUPERVISOR"
    DRIVER = "DRIVER"

class AttendanceType(enum.Enum):
    IN = "IN"
    OUT = "OUT"

class DailyStatus(enum.Enum):
    PRESENT = "Present"
    ABSENT = "Absent"
    VACATION = "Vacation"
    PERMISSION = "Permission"

class LoanType(enum.Enum):
    DAILY = "Daily"
    MONTHLY = "Monthly"
    EXTENDED = "Extended"

class PenaltyBonusType(enum.Enum):
    PENALTY = "Penalty"
    BONUS = "Bonus"

class MaritalStatus(enum.Enum):
    SINGLE = "أعزب"
    MARRIED = "متزوج"
    DIVORCED = "مطلق"
    WIDOWED = "أرمل"

class MilitaryStatus(enum.Enum):
    EXEMPT = "معفى"
    COMPLETED = "أدى الخدمة"
    POSTPONED = "مؤجل"
    NOT_HIS_TURN = "لم يصبه الدور"
    NOT_SUBJECT = "غير خاضع للتجنيد"

class WeeklyHoliday(enum.Enum):
    FRIDAY = "الجمعة"
    SATURDAY = "السبت"
    SUNDAY = "الأحد"
    MONDAY = "الإثنين"
    TUESDAY = "الثلاثاء"
    WEDNESDAY = "الأربعاء"
    THURSDAY = "الخميس"

class SalaryType(enum.Enum):
    FIXED = "ثابت"
    HOURLY = "بالساعة"
    HOSPITALITY = "ضيافة"

class Department(Base):
    __tablename__ = 'departments'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    erp_cost_center_code = Column(String, nullable=True)
    display_order = Column(Integer, default=0)
    
    employees = relationship("Employee", back_populates="department")

class Employee(Base):
    __tablename__ = 'employees'
    
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    job_title = Column(String, nullable=True)
    department_id = Column(Integer, ForeignKey('departments.id'))
    
    category = Column(String, nullable=False)
    
    basic_salary = Column(Float, default=0.0)
    daily_work_hours = Column(Float, default=8.0)
    standard_start_time = Column(Time, nullable=True)
    standard_end_time = Column(Time, nullable=True)
    
    # ============ نظام التأمينات المرن ============
    is_insured = Column(Boolean, default=False)
    insurance_number = Column(String, nullable=True)
    
    # الحصة التأمينية – نمط (أ): employee_only (قانونية) | both_from_employee (استقطاع عامل) | company_pays_all (استقطاع شركة)
    insurance_policy = Column(String(50), default='employee_only')
    
    # النسب المئوية
    insurance_employee_share = Column(Float, default=11.0)  # حصة العامل %
    insurance_company_share = Column(Float, default=18.75)  # حصة الشركة %
    
    # Insurance Dates
    insurance_start_date = Column(Date, nullable=True)
    insurance_end_date = Column(Date, nullable=True)
    
    # الحقول القديمة (للتوافق - سيتم حسابها تلقائياً)
    insurance_value_employee = Column(Float, default=0.0)
    insurance_value_company = Column(Float, default=0.0)
    
    overtime_allowed = Column(Boolean, default=False)
    has_attendance_bonus = Column(Boolean, default=False)
    
    erp_account_code = Column(String, nullable=True)
    
    # New Fields - Personal
    hire_date = Column(Date, nullable=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    governorate = Column(String, nullable=True)
    marital_status = Column(String, nullable=True)
    mobile_number = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    national_id = Column(String, unique=True, nullable=True)
    num_children = Column(Integer, default=0)
    age_youngest_child = Column(Integer, default=0)
    military_status = Column(String, nullable=True)
    has_relatives = Column(Boolean, default=False)
    relationship_degree = Column(String, nullable=True)
    weekly_holiday = Column(String, default=WeeklyHoliday.FRIDAY.value)
    
    # New Fields - Work Status
    is_active = Column(Boolean, default=True)
    exit_date = Column(Date, nullable=True)
    resignation_reason = Column(String, nullable=True)
    disruption_date = Column(Date, nullable=True)
    entitlement_date = Column(Date, nullable=True)
    entitled_to_official_holidays = Column(Boolean, default=True) # هل يستحق العطلات الرسمية مدفوعة الأجر؟
    
    # New Fields - Financial
    incentive_allowance = Column(Float, default=0.0)
    regularity_incentive = Column(Float, default=0.0)  # حافز الانتظام (يصرف إذا حضر 24 يوم أو أكثر)
    transport_allowance = Column(Float, default=0.0)
    insurance_salary = Column(Float, default=0.0)
    salary_type = Column(String, default=SalaryType.FIXED.value)
    salary_updated_at = Column(DateTime, nullable=True)
    
    # New Fields - Documents (JSON string)
    documents_received = Column(String, nullable=True)
    
    # New Fields - Education
    college = Column(String, nullable=True)
    major = Column(String, nullable=True)
    graduation_year = Column(Integer, nullable=True)
    grade = Column(String, nullable=True)
    qualification = Column(String, nullable=True)
    
    def calculate_insurance_values(self):
        """
        حساب قيم التأمين بناءً على السياسة المختارة
        
        Returns:
            dict: {
                'employee_deduction': المبلغ الذي يُخصم من راتب الموظف,
                'company_cost': المبلغ الذي تتحمله الشركة,
                'total_insurance': إجمالي التأمين
            }
        """
        if not self.is_insured:
            return {
                'employee_deduction': 0.0,
                'company_cost': 0.0,
                'total_insurance': 0.0
            }
        
        # تحديد قاعدة الحساب: الشريحة التأمينية (أو الراتب الأساسي كاحتياطي)
        calculation_base = self.insurance_salary if (self.insurance_salary and self.insurance_salary > 0) else (self.basic_salary or 0)
        
        # حساب القيم الأساسية بناءً على الشريحة التأمينية
        employee_value = calculation_base * (self.insurance_employee_share / 100)
        company_value = calculation_base * (self.insurance_company_share / 100)
        
        # تطبيق السياسة المختارة
        if self.insurance_policy == 'employee_only':
            # قانونية: خصم حصة العامل فقط (الشركة تدفع حصتها)
            return {
                'employee_deduction': employee_value,
                'company_cost': company_value,
                'total_insurance': employee_value + company_value
            }
        elif self.insurance_policy == 'both_from_employee':
            # استقطاع عامل: خصم الحصتين من العامل
            return {
                'employee_deduction': employee_value + company_value,
                'company_cost': 0.0,
                'total_insurance': employee_value + company_value
            }
        elif self.insurance_policy == 'company_pays_all':
            # استقطاع شركة: الشركة تتحمل الحصتين
            return {
                'employee_deduction': 0.0,
                'company_cost': employee_value + company_value,
                'total_insurance': employee_value + company_value
            }
        else:
            # افتراضي: employee_only
            return {
                'employee_deduction': employee_value,
                'company_cost': company_value,
                'total_insurance': employee_value + company_value
            }
    
    department = relationship("Department", back_populates="employees")
    attendance_logs = relationship("AttendanceLog", back_populates="employee")
    daily_records = relationship("DailyRecord", back_populates="employee")
    loans = relationship("Loan", back_populates="employee")
    penalties_bonuses = relationship("PenaltyBonus", back_populates="employee")
    permissions = relationship("Permission", back_populates="employee")
    documents = relationship("EmployeeDocument", back_populates="employee")
    bonuses = relationship('Bonus', back_populates='employee')
    leave_balances = relationship("LeaveBalance", back_populates="employee")
    leaves = relationship("Leave", back_populates="employee")
    salary_history = relationship("SalaryHistory", back_populates="employee", cascade="all, delete-orphan")

class AttendanceLog(Base):
    __tablename__ = 'attendance_logs'
    
    id = Column(Integer, primary_key=True)
    employee_code = Column(String, ForeignKey('employees.code'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    type = Column(String, nullable=False)
    
    employee = relationship("Employee", back_populates="attendance_logs", foreign_keys=[employee_code], primaryjoin="Employee.code == AttendanceLog.employee_code")

class DailyRecord(Base):
    __tablename__ = 'daily_records'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    date = Column(Date, nullable=False)
    
    check_in = Column(Time, nullable=True)
    check_out = Column(Time, nullable=True)
    
    late_minutes = Column(Integer, default=0)
    early_leave_minutes = Column(Integer, default=0)
    overtime_hours = Column(Float, default=0.0)
    
    status = Column(String, default=DailyStatus.ABSENT)
    
    calculated_penalty_amount = Column(Float, default=0.0)
    manual_adjustment = Column(Float, default=0.0)
    is_manual_override = Column(Boolean, default=False)
    
    employee = relationship("Employee", back_populates="daily_records")
    
    @property
    def hourly_salary(self):
        if self.employee and self.employee.basic_salary:
            from policy.hr_policy import HRPolicy
            # Use employee's actual daily work hours (e.g., 10 or 8) for correct calculation
            daily_hours = self.employee.daily_work_hours if self.employee.daily_work_hours else 8.0
            return HRPolicy.calculate_hourly_salary(self.employee.basic_salary, daily_hours)
        return 0.0

    @property
    def late_deduction_amount(self):
        """Calculate late deduction value dynamically"""
        if self.late_minutes > 0 and self.hourly_salary > 0:
            from policy.hr_policy import HRPolicy
            return HRPolicy.calculate_late_deduction(self.late_minutes, self.hourly_salary)
        return 0.0

    @property
    def early_deduction_amount(self):
        """Calculate early leave deduction value dynamically"""
        if self.early_leave_minutes > 0 and self.hourly_salary > 0:
             from policy.hr_policy import HRPolicy
             return HRPolicy.calculate_early_departure_deduction(self.early_leave_minutes, self.hourly_salary)
        return 0.0

    @property
    def overtime_pay_amount(self):
        """Calculate overtime pay value dynamically"""
        if self.overtime_hours > 0 and self.hourly_salary > 0:
            from policy.hr_policy import HRPolicy
            return HRPolicy.calculate_overtime_pay(self.overtime_hours, self.hourly_salary)
        return 0.0

class Loan(Base):
    __tablename__ = 'loans'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(String, nullable=False)
    installments_count = Column(Integer, default=1)
    remaining_balance = Column(Float, nullable=False)
    is_paid_off = Column(Boolean, default=False)
    date = Column(Date, default=datetime.now().date)
    excluded_months = Column(String, nullable=True)
    
    # New Fields for Approval Workflow
    status = Column(String(20), default='Approved') # Pending, Approved, Cancelled
    cost_center = Column(String(50), nullable=True)
    disbursed_at = Column(DateTime, nullable=True)
    disbursed_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    employee = relationship("Employee", back_populates="loans")

    @property
    def installment_value(self):
        if self.installments_count > 0:
            return self.amount / self.installments_count
        return 0.0

    @property
    def monthly_installment(self):
        """Alias for installment_value used in reports"""
        return self.installment_value

    def get_remaining_balance(self, as_of=None):
        """
        Calculates the remaining balance automatically based on a given date (default today)
        and payroll cycle (26th to 25th).
        """
        if self.is_paid_off:
            return 0.0
        
        if not self.date or self.amount <= 0:
            return self.amount or 0.0

        excluded = []
        if self.excluded_months:
            for m in self.excluded_months.split(','):
                token = m.strip()
                if not token:
                    continue
                try:
                    excluded.append(int(token))
                except ValueError:
                    try:
                        f = float(token)
                        if f.is_integer():
                            excluded.append(int(f))
                        else:
                            # ignore non-integer tokens like '2.4'
                            continue
                    except ValueError:
                        continue
        
        if as_of is None:
            # Simple global default if used as property
            as_of = datetime.now().date()
        
        installments_deducted = 0
        # Logic fix: The first 'deadline' for deduction should be the 25th of the month 
        # in which the loan started, UNLESS the loan started after the 25th.
        # If started after the 25th, the first deadline is the 25th of the NEXT month.
        
        # Safety break after 120 cycles (10 years)
        current_check_date = self.date
        for _ in range(120):
            if installments_deducted >= self.installments_count:
                break
            
            # Update current month/year from current_check_date to ensure the loop progresses
            c_month = current_check_date.month
            c_year = current_check_date.year
            
            # The 'deadline' for this installment is the 25th of its month
            deadline = date(c_year, c_month, 25)
            
            # If the calculated deadline for this month is actually before the loan started (e.g. loan on 28th)
            # then we shouldn't consider this month for deduction.
            if deadline < self.date:
                # Move to next month without counting an installment
                nm = c_month + 1
                ny = c_year
                if nm > 12:
                    nm = 1
                    ny += 1
                c_month = nm
                c_year = ny
                continue

            # If our 'as_of' date is past the 25th, then it's officially 'gone' from balance.
            if as_of > deadline:
                if c_month not in excluded:
                    installments_deducted += 1
            else:
                # We haven't reached the deadline for this or future installments as of our target date
                break
                
            # Move to next month
            nm = c_month + 1
            ny = c_year
            if nm > 12:
                nm = 1
                ny += 1
            import calendar
            last_day = calendar.monthrange(ny, nm)[1]
            current_check_date = date(ny, nm, min(self.date.day, last_day))

        calc_remaining = self.amount - (installments_deducted * self.installment_value)
        return max(0.0, calc_remaining)

    @property
    def auto_remaining_balance(self):
        """Dynamic balance lookup for UI"""
        return self.get_remaining_balance()

    @property
    def auto_is_paid_off(self):
        """Checks if the loan is fully paid based on time logic."""
        return self.auto_remaining_balance <= 0

    @property
    def installments_remaining(self):
        """Calculate number of remaining installments using auto logic"""
        if self.installment_value > 0:
            return round(self.auto_remaining_balance / self.installment_value)
        return 0

    @property
    def end_date(self):
        """Calculate expected end date considering excluded months"""
        if not self.date or self.installments_count <= 0:
            return None
            
        excluded = []
        if self.excluded_months:
            for m in self.excluded_months.split(','):
                token = m.strip()
                if not token:
                    continue
                try:
                    excluded.append(int(token))
                except ValueError:
                    try:
                        f = float(token)
                        if f.is_integer():
                            excluded.append(int(f))
                        else:
                            continue
                    except ValueError:
                        continue
        
        # Start logic
        current_check_date = self.date
        installments_paid = 0
        
        # Loop until all installments are accounted for
        for _ in range(120):
            if installments_paid >= self.installments_count:
                break
                
            c_month = current_check_date.month
            c_year = current_check_date.year
            
            # The 'deadline' for this installment is the 25th of its month
            deadline = date(c_year, c_month, 25)
            
            # If the calculated deadline for this month is actually before the loan started (e.g. loan on 28th)
            # then we shouldn't consider this month for deduction.
            if deadline < self.date:
                # Move to next month
                nm = c_month + 1
                ny = c_year
                if nm > 12:
                    nm = 1
                    ny += 1
                current_check_date = date(ny, nm, min(self.date.day, 28))
                continue

            if c_month not in excluded:
                installments_paid += 1
            
            if installments_paid < self.installments_count:
                # Move to next month for next iteration
                nm = c_month + 1
                ny = c_year
                if nm > 12:
                    nm = 1
                    ny += 1
                current_check_date = date(ny, nm, min(self.date.day, 28))
            else:
                # This IS the final month
                return date(c_year, c_month, 25)
                
        return date(current_check_date.year, current_check_date.month, 25)

class PenaltyBonus(Base):
    __tablename__ = 'penalties_and_bonuses'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    date = Column(Date, default=datetime.now().date)
    type = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    days = Column(Float, nullable=True) # حقل أيام الخصم (ربع يوم، نصف، إلخ)
    reason = Column(String, nullable=True)
    
    employee = relationship("Employee", back_populates="penalties_bonuses")

    @property
    def daily_rate(self):
        """قيمة اليوم الواحد للموظف حالياً"""
        if self.employee and self.employee.basic_salary:
            from policy.hr_policy import HRPolicy
            return HRPolicy.calculate_daily_salary(self.employee.basic_salary)
        return 0.0

    @property
    def day_value(self):
        """القيمة المالية لعدد الأيام المسجلة"""
        if self.days and self.daily_rate > 0:
            return self.days * self.daily_rate
        return 0.0

class Permission(Base):
    __tablename__ = 'permissions'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    date = Column(Date, nullable=False)
    from_time = Column(Time, nullable=False)
    to_time = Column(Time, nullable=False)
    reason = Column(String, nullable=True)
    is_paid = Column(Boolean, default=False)
    
    
    employee = relationship("Employee", back_populates="permissions")

    @property
    def material_value(self):
        """
        حساب القيمة المادية لمدة التصريح
        القيمة = مدة التصريح بالساعات × معدل أجر الساعة
        """
        if self.from_time and self.to_time and self.employee and self.employee.basic_salary:
            # 1. حساب المدة بالساعات
            start_minutes = self.from_time.hour * 60 + self.from_time.minute
            end_minutes = self.to_time.hour * 60 + self.to_time.minute
            duration_minutes = max(0, end_minutes - start_minutes)
            duration_hours = duration_minutes / 60.0
            
            if duration_hours <= 0:
                return 0.0

            # 2. حساب معدل أجر الساعة
            from core.policy.hr_policy import HRPolicy
            daily_salary = self.employee.basic_salary / float(HRPolicy.WORKING_DAYS_PER_MONTH)
            
            # ساعات العمل اليومية (الافتراضي 8)
            work_hours = self.employee.daily_work_hours if self.employee.daily_work_hours else 8.0
            
            hourly_rate = daily_salary / work_hours
            
            return duration_hours * hourly_rate
        return 0.0

class LeaveTypeEnum(enum.Enum):
    """أنواع الإجازات"""
    ANNUAL = "سنوية"
    SICK = "مرضية"
    CASUAL = "عارضة"
    UNPAID = "بدون راتب"
    EMERGENCY = "طارئة"
    MATERNITY = "وضع"
    BEREAVEMENT = "وفاة"

class LeaveStatus(enum.Enum):
    """حالة طلب الإجازة"""
    PENDING = "قيد الانتظار"
    APPROVED = "موافق عليها"
    REJECTED = "مرفوضة"
    CANCELLED = "ملغاة"

class LeaveBalance(Base):
    """رصيد الإجازات للموظف"""
    __tablename__ = 'leave_balances'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    year = Column(Integer, nullable=False)
    
    # رصيد كل نوع (بالأيام)
    annual_balance = Column(Float, default=21.0)
    annual_used = Column(Float, default=0.0)
    
    sick_balance = Column(Float, default=30.0)
    sick_used = Column(Float, default=0.0)
    
    casual_balance = Column(Float, default=7.0)
    casual_used = Column(Float, default=0.0)
    
    emergency_balance = Column(Float, default=3.0)
    emergency_used = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    employee = relationship("Employee", back_populates="leave_balances")
    
    @property
    def annual_remaining(self):
        return max(0, self.annual_balance - self.annual_used)
    
    @property
    def sick_remaining(self):
        return max(0, self.sick_balance - self.sick_used)
    
    @property
    def casual_remaining(self):
        return max(0, self.casual_balance - self.casual_used)
    
    @property
    def emergency_remaining(self):
        return max(0, self.emergency_balance - self.emergency_used)

class Leave(Base):
    """سجل الإجازات"""
    __tablename__ = 'leaves'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    
    leave_type = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days_count = Column(Float, nullable=False)
    
    is_paid = Column(Boolean, default=True)
    status = Column(String, default=LeaveStatus.APPROVED.value)
    
    reason = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    
    requested_date = Column(Date, default=datetime.now().date)
    approved_date = Column(Date, nullable=True)
    approved_by = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    employee = relationship("Employee", back_populates="leaves")
    
    @property
    def duration_days(self):
        """حساب المدة بالأيام"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0

class DocumentType(Base):
    """انواع المستندات المتاحة للرفع"""
    __tablename__ = 'document_types'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    needs_expiry = Column(Boolean, default=False) # هل هذا النوع يحتاج لتاريخ انتهاء؟
    # Indicates whether this document type is required for all employees
    is_required = Column(Boolean, default=True)

    def __repr__(self):
        return f"<DocumentType {self.name}>"

class PublicHoliday(Base):
    """العطلات الرسمية والمواسيم"""
    __tablename__ = 'public_holidays'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_unpaid_for_uninsured = Column(Boolean, default=False) # هل تُخصم من غير المؤمن عليهم؟
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<PublicHoliday {self.name} ({self.start_date} - {self.end_date})>"

class EmployeeDocument(Base):
    __tablename__ = 'employee_documents'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    type_id = Column(Integer, ForeignKey('document_types.id'), nullable=True)
    
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.now)
    
    # حقل نصي قديم للتوافق، سيتم استبداله بـ type_id لاحقاً
    document_type = Column(String, nullable=True) 
    
    expiry_date = Column(Date, nullable=True)
    notes = Column(String, nullable=True)
    
    employee = relationship("Employee", back_populates="documents")
    type_info = relationship("DocumentType")

# --- الإضافة المطلوبة تبدأ هنا ---

# 1. تعريف نموذج سجل التعديلات (AuditLog)
class AuditLog(Base):
    """
    نموذج لتخزين سجل التعديلات التي تتم على بيانات الموظفين.
    يتم تسجيل كل تغيير كصف مستقل في هذا الجدول.
    """
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    employee_code = Column(String(50), nullable=False, index=True)
    field_name = Column(String(100), nullable=False)
    old_value = Column(String(255))
    new_value = Column(String(255))
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<AuditLog {self.timestamp} - {self.employee_code} - {self.field_name}>"

# 2. مستمع أحداث لتتبع التغييرات على نموذج الموظف تلقائيًا
@event.listens_for(Session, 'before_flush')
def track_employee_changes(session, flush_context, instances):
    """
    هذه الدالة تستمع لأي تغييرات قبل حفظها في قاعدة البيانات.
    - للموظفين الجدد: تسجل الراتب الافتتاحي في سجل الرواتب.
    - للتعديلات: تسجل التغيير في AuditLog وسجل الرواتب.
    """
    from core.database_models import SalaryHistory

    # أولاً: معالجة الموظفين الجدد (سجل الراتب الافتتاحي)
    for instance in session.new:
        if isinstance(instance, Employee):
            # إضافة سجل الراتب الافتتاحي عند التعيين
            initial_salary = instance.basic_salary or 0.0
            
            # تحديد تاريخ التفعيل (تاريخ التعيين أو اليوم)
            effective_date = instance.hire_date if instance.hire_date else date.today()
            effective_datetime = datetime.combine(effective_date, datetime.min.time())
            
            history_entry = SalaryHistory(
                employee=instance,
                old_salary=0.0,
                new_salary=initial_salary,
                salary_change=initial_salary,
                change_date=datetime.now(),
                effective_date=effective_datetime,
                reason="راتب تعيين (افتتاحي)"
            )
            session.add(history_entry)

    # ثانياً: معالجة التعديلات على الموظفين الحاليين
    for instance in session.dirty:
        if not isinstance(instance, Employee):
            continue
            
        if getattr(instance, '_skip_audit', False):
            continue

        state = inspect(instance)
        
        for attr in state.attrs:
            history = attr.history
            
            if history.has_changes():
                old_value = history.deleted[0] if history.deleted else None
                new_value = history.added[0] if history.added else None

                if old_value != new_value:
                    # تسجيل في AuditLog
                    log_entry = AuditLog(
                        employee_code=instance.code,
                        field_name=attr.key,
                        old_value=str(old_value) if old_value is not None else None,
                        new_value=str(new_value) if new_value is not None else None,
                    )
                    session.add(log_entry)

                    # معالجة خاصة للراتب الأساسي
                    if attr.key == 'basic_salary':
                        instance.salary_updated_at = datetime.now()
                        
                        old_val = float(old_value) if old_value is not None else 0.0
                        new_val = float(new_value) if new_value is not None else 0.0
                        
                        # تحديد تاريخ التفعيل من الخاصية المؤقتة _effective_date إن وجدت
                        eff_date = getattr(instance, '_effective_date', datetime.now())
                        if isinstance(eff_date, (date, datetime)) and not isinstance(eff_date, datetime):
                            eff_date = datetime.combine(eff_date, datetime.min.time())
                        
                        history_entry = SalaryHistory(
                            employee=instance,
                            old_salary=old_val,
                            new_salary=new_val,
                            salary_change=new_val - old_val,
                            change_date=datetime.now(),
                            effective_date=eff_date,
                            reason=getattr(instance, '_change_reason', "تعديل يدوي")
                        )
                        session.add(history_entry)

# --- الإضافة المطلوبة تنتهي هنا ---

class SystemSetting(Base):
    """
    نموذج لتخزين إعدادات النظام بشكل ديناميكي
    """
    __tablename__ = 'system_settings'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    category = Column(String(50), nullable=True)  # e.g. 'Attendance', 'Overtime', 'Financial'
    data_type = Column(String(20), default='string')  # e.g. 'int', 'float', 'string', 'bool'
    
    def __repr__(self):
        return f"<SystemSetting {self.key}: {self.value}>"

class Bonus(Base):
    """
    نموذج لتسجيل المكافآت الممنوحة للموظفين.
    """
    __tablename__ = 'bonuses'

    id = Column(Integer, primary_key=True)
    
    # ربط المكافأة بالموظف
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    
    # مبلغ المكافأة
    amount = Column(Float, nullable=False, default=0.0)
    
    # سبب منح المكافأة
    reason = Column(String(500), nullable=True)
    
    # تاريخ منح المكافأة
    date_awarded = Column(Date, default=date.today, nullable=False)
    
    # يحدد ما إذا كانت المكافأة ستُصرف مع راتب نهاية الشهر
    paid_with_salary = Column(Boolean, default=True, nullable=False)
    
    # تعريف العلاقة مع نموذج الموظف
    employee = relationship('Employee', back_populates='bonuses')
    
    def __repr__(self):
        return f"<Bonus {self.id} for Employee {self.employee_id} - Amount: {self.amount}>"


class SalaryHistory(Base):
    """
    نموذج لتسجيل السجل التاريخي لتعديلات رواتب الموظفين
    يحفظ كل تعديل على الراتب مع التاريخ والقيمة القديمة والجديدة والسبب
    """
    __tablename__ = 'salary_history'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    
    # الراتب القديم والجديد
    old_salary = Column(Float, nullable=False)
    new_salary = Column(Float, nullable=False)
    
    # الفرق (التعديل)
    salary_change = Column(Float, nullable=False)
    
    # تاريخ التعديل (وقت العملية)
    change_date = Column(DateTime, default=datetime.now, nullable=False)
    
    # تاريخ التفعيل (التاريخ الذي يبدأ فيه استحقاق الراتب الجديد)
    effective_date = Column(DateTime, default=datetime.now, nullable=False)
    
    # سبب التعديل (ترقية، تخفيض، تصحيح، إلخ)
    reason = Column(String(255), nullable=True)
    
    # معلومات إضافية
    notes = Column(String(500), nullable=True)
    
    # من قام بالتعديل (اسم المستخدم)
    modified_by = Column(String(100), nullable=True)
    
    # العلاقة مع الموظف
    employee = relationship('Employee', back_populates='salary_history')
    
    def __repr__(self):
        return f"<SalaryHistory {self.id} - Employee: {self.employee_id} - Change: {self.salary_change} - Date: {self.change_date}>"
    
    @property
    def formatted_change_date(self):
        """تنسيق التاريخ بالعربية"""
        if self.change_date:
            return self.change_date.strftime('%d/%m/%Y %H:%M')
        return '-'

    @property
    def formatted_effective_date(self):
        """تنسيق تاريخ التفعيل بالعربية"""
        if self.effective_date:
            return self.effective_date.strftime('%d/%m/%Y')
        return '-'
    
    @property
    def change_type(self):
        """نوع التعديل (زيادة أو تخفيض)"""
        if self.salary_change > 0:
            return 'زيادة'
        elif self.salary_change < 0:
            return 'تخفيض'
        else:
            return 'بدون تغيير'


class BulkSalaryUpdateRequest(Base):
    """مفتاح طلب الحفظ الجماعي لمنع تسجيل التعديل أكثر من مرة."""
    __tablename__ = 'bulk_salary_update_requests'

    id = Column(Integer, primary_key=True)
    idempotency_key = Column(String(36), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
