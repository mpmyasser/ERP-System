"""
Employee Forms - WTForms
========================
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SelectField, BooleanField, IntegerField, FloatField, TextAreaField, TimeField
from wtforms.fields import DateField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, ValidationError
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'core'))
from utils.helpers import parse_date_compact


def validate_date_format_custom(form, field):
    """
    Validator that uses our custom parse_date_compact function.
    WTForms DateField returns a date object if successful, or None.
    The raw string is in `field.raw_data`.
    """
    if not field.data and field.raw_data:
        # DateField failed to parse, let's try our custom parser on the raw input
        if field.raw_data[0]:
            parsed_date = parse_date_compact(field.raw_data[0])
            if parsed_date:
                # If our parser succeeds, we can consider it valid and patch the data
                field.data = parsed_date
            else:
                raise ValidationError('صيغة التاريخ غير صحيحة. استخدم DD/MM/YYYY أو أدخلها كـ DDMMYYYY')


def validate_not_future(form, field):
    """
    Validator to prevent future dates strictly.
    """
    if field.data:
        from datetime import date
        if field.data > date.today():
            raise ValidationError('غير مسموح باختيار تاريخ مستقبلي (لاحق لتاريخ اليوم)')


def validate_loan_date_within_month(form, field):
    """
    Validator for loan dates - allows future dates only up to end of current month.
    """
    if field.data:
        from datetime import date
        import calendar
        
        today = date.today()
        
        # Check if date is in the past (allowed for loans)
        if field.data <= today:
            return  # Allow past dates
        
        # For future dates, ensure they don't exceed end of current month
        last_day_of_month = calendar.monthrange(today.year, today.month)[1]
        end_of_month = date(today.year, today.month, last_day_of_month)
        
        if field.data > end_of_month:
            raise ValidationError('يجب أن تكون تاريخ السلفة في نهاية هذا الشهر على الأقصى (لا يمكن تجاوز آخر يوم في الشهر الحالي)')

class EmployeeForm(FlaskForm):
    """Employee form for create/update"""
    
    # Personal Data
    name = StringField('اسم الموظف', validators=[DataRequired(), Length(max=200)])
    code = StringField('كود الموظف', validators=[DataRequired(), Length(max=50)])
    national_id = StringField('الرقم القومي', validators=[Optional(), Length(min=14, max=14)])
    # Render date fields as text using DD/MM/YYYY to match user preference
    date_of_birth = DateField('تاريخ الميلاد', format='%d/%m/%Y', validators=[Optional(), validate_date_format_custom, validate_not_future], render_kw={"placeholder": "DD/MM/YYYY", "type": "text", "class": "date-string form-control"})
    mobile_number = StringField('رقم الموبايل', validators=[Optional(), Length(min=10, max=11)])
    address = StringField('العنوان', validators=[Optional()])
    city = StringField('المدينة', validators=[Optional()])
    governorate = StringField('المحافظة', validators=[Optional()])
    marital_status = SelectField('الحالة الاجتماعية', choices=[
        ('', 'اختر...'),
        ('أعزب', 'أعزب'),
        ('متزوج', 'متزوج'),
        ('مطلق', 'مطلق'),
        ('أرمل', 'أرمل')
    ])
    military_status = SelectField('الموقف من التجنيد', choices=[
        ('', 'اختر...'),
        ('معفى', 'معفى'),
        ('أدى الخدمة', 'أدى الخدمة'),
        ('مؤجل', 'مؤجل'),
        ('لم يصبه الدور', 'لم يصبه الدور'),
        ('غير خاضع للتجنيد', 'غير خاضع للتجنيد')
    ])
    num_children = IntegerField('عدد الأولاد', validators=[Optional(), NumberRange(min=0)], default=0)
    
    # Work Data
    job_title = StringField('الوظيفة', validators=[Optional()])
    department_id = SelectField('القسم', coerce=int, validators=[Optional()])
    category = SelectField('الفئة', choices=[
        ('WORKER', 'عامل'),
        ('EMPLOYEE', 'موظف'),
        ('SUPERVISOR', 'مشرف'),
        ('DRIVER', 'سائق')
    ])
    hire_date = DateField('تاريخ التعيين', format='%d/%m/%Y', validators=[Optional(), validate_date_format_custom, validate_not_future], render_kw={"placeholder": "DD/MM/YYYY", "type": "text", "class": "date-string form-control"})
    is_active = BooleanField('يعمل', default=True)
    disruption_date = DateField('تاريخ الانقطاع', format='%d/%m/%Y', validators=[Optional(), validate_date_format_custom, validate_not_future], render_kw={"placeholder": "DD/MM/YYYY", "type": "text", "class": "date-string form-control"})
    resignation_reason = StringField('سبب إنهاء الخدمة', validators=[Optional()])
    
    # Financial Data
    basic_salary = FloatField('الراتب الأساسي', validators=[Optional(), NumberRange(min=0)], default=0)
    transport_allowance = FloatField('بدل انتقال', validators=[Optional(), NumberRange(min=0)], default=0)
    incentive_allowance = FloatField('الحوافز', validators=[Optional(), NumberRange(min=0)], default=0)
    regularity_incentive = FloatField('حافز الانتظام', validators=[Optional(), NumberRange(min=0)], default=0)
    entitled_to_official_holidays = BooleanField('يستحق العطلات الرسمية مدفوعة الأجر', default=True)
    is_insured = BooleanField('مؤمن عليه', default=False)
    
    # New Insurance Fields
    insurance_start_date = DateField('تاريخ بداية التأمين', format='%d/%m/%Y', validators=[Optional(), validate_date_format_custom, validate_not_future], render_kw={"placeholder": "DD/MM/YYYY", "type": "text", "class": "date-string form-control"})
    insurance_end_date = DateField('تاريخ الخروج من التأمين', format='%d/%m/%Y', validators=[Optional(), validate_date_format_custom, validate_not_future], render_kw={"placeholder": "DD/MM/YYYY", "type": "text", "class": "date-string form-control"})
    
    insurance_value_employee = FloatField('حصة الموظف المحسوبة', validators=[Optional(), NumberRange(min=0)], default=0)
    insurance_value_company = FloatField('حصة الشركة المحسوبة', validators=[Optional(), NumberRange(min=0)], default=0)
    insurance_policy = SelectField('الحصة التأمينية – نمط (أ)', choices=[
        ('employee_only', 'قانونية'),
        ('both_from_employee', 'استقطاع عامل'),
        ('company_pays_all', 'استقطاع شركة')
    ], default='employee_only')
    insurance_employee_share = FloatField('حصة العامل (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=11.0)
    insurance_company_share = FloatField('حصة الشركة (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=18.75)
    insurance_number = StringField('الرقم التأميني', validators=[Optional()])
    insurance_salary = FloatField('الشريحة التأمينية', validators=[Optional(), NumberRange(min=0)], default=0)
    salary_type = SelectField('نوع المرتب', choices=[
        ('ثابت', 'ثابت'),
        ('بالساعة', 'بالساعة'),
        ('ضيافة', 'ضيافة')
    ])
    
    # Work Schedule
    daily_work_hours = FloatField('ساعات العمل', validators=[Optional()], default=8.0)
    standard_start_time = TimeField('ميعاد الحضور الرسمي', validators=[Optional()])
    standard_end_time = TimeField('ميعاد الانصراف الرسمي', validators=[Optional()])
    overtime_allowed = BooleanField('يسمح بالإضافي', default=False)


class PermissionForm(FlaskForm):
    """Permission form"""
    employee_id = SelectField('الموظف', coerce=int, validators=[DataRequired()])
    date = DateField('التاريخ', format='%d/%m/%Y', validators=[DataRequired(), validate_date_format_custom, validate_not_future], render_kw={"placeholder": "DD/MM/YYYY", "type": "text", "class": "date-string form-control"})
    from_time = TimeField('من الساعة', validators=[DataRequired()])
    to_time = TimeField('إلى الساعة', validators=[DataRequired()])
    reason = TextAreaField('السبب', validators=[Optional()])
    is_paid = BooleanField('تصريح مدفوع')


class PenaltyForm(FlaskForm):
    """Penalty/Bonus form"""
    employee_id = SelectField('الموظف', coerce=int, validators=[DataRequired()])
    date = DateField('التاريخ', format='%d/%m/%Y', validators=[DataRequired(), validate_date_format_custom, validate_not_future], render_kw={"placeholder": "DD/MM/YYYY", "type": "text", "class": "date-string form-control"})
    penalty_type = SelectField('النوع', choices=[
        ('Penalty', 'خصم (جزاء)'),
        ('Bonus', 'مكافأة')
    ], validators=[DataRequired()])
    amount = FloatField('المبلغ', validators=[Optional(), NumberRange(min=0)])
    days = FloatField('أيام الخصم (اختياري)', validators=[Optional()])
    reason = TextAreaField('السبب', validators=[DataRequired()])


def validate_excluded_months_format(form, field):
    """Validate excluded_months - must be comma-separated integers (1-12) or empty."""
    if not field.data:
        return
    tokens = [t.strip() for t in field.data.split(',') if t.strip()]
    for tok in tokens:
        # allow integer strings or float strings that represent whole numbers (e.g. '5.0')
        try:
            if '.' in tok:
                f = float(tok)
                if not f.is_integer():
                    raise ValidationError('قيمة الأشهر يجب أن تكون أعدادًا صحيحة (1-12) مفصولة بفواصل')
                val = int(f)
            else:
                val = int(tok)
        except ValueError:
            raise ValidationError('قيمة الأشهر يجب أن تكون أعدادًا صحيحة (1-12) مفصولة بفواصل')
        if val < 1 or val > 12:
            raise ValidationError('الأشهر يجب أن تكون بين 1 و 12')

class LoanForm(FlaskForm):
    """Loan form"""
    employee_id = SelectField('الموظف', coerce=int, validators=[DataRequired()])
    loan_type = SelectField('نوع السلفة', choices=[
        ('permanent', 'مستديمة'),
        ('temporary', 'مؤقتة')
    ], validators=[DataRequired()])
    amount = FloatField('المبلغ', validators=[DataRequired(), NumberRange(min=0)])
    number_of_installments = IntegerField('عدد الأقساط', validators=[DataRequired(), NumberRange(min=1)])
    date = DateField('تاريخ السلفة', format='%d/%m/%Y', validators=[Optional(), validate_date_format_custom, validate_loan_date_within_month], render_kw={"placeholder": "DD/MM/YYYY", "type": "text", "class": "date-string form-control allow-month-end"})
    excluded_months = StringField('أشهر الاستثناء من الخصم', validators=[Optional(), validate_excluded_months_format])


class AttendanceImportForm(FlaskForm):
    """Import attendance from Excel"""
    file = FileField('اختر ملف Excel', validators=[
        DataRequired(),
        FileAllowed(['xlsx', 'xls'], 'ملفات Excel فقط')
    ])


class DocumentForm(FlaskForm):
    """Document upload form"""
    file = FileField('المستند (صورة أو PDF)', validators=[
        DataRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'ملفات صور أو PDF فقط')
    ])
    type_id = SelectField('نوع المستند', coerce=int, validators=[DataRequired()])
    # Exclude validate_not_future from expiry_date (User Request)
    expiry_date = DateField('تاريخ انتهاء الصلاحية', format='%d/%m/%Y', validators=[Optional(), validate_date_format_custom], render_kw={"placeholder": "DD/MM/YYYY", "type": "text", "class": "date-string form-control form-control-sm allow-future"})
    notes = TextAreaField('ملاحظات', validators=[Optional()])


class BonusForm(FlaskForm):
    """
    نموذج لإضافة مكافأة جديدة للموظف
    """
    employee_id = SelectField('الموظف', coerce=int, validators=[DataRequired()])
    amount = FloatField('المبلغ', validators=[DataRequired(), NumberRange(min=0)])
    reason = TextAreaField('السبب', validators=[DataRequired()])
    date_awarded = DateField('تاريخ المكافأة', format='%d/%m/%Y', validators=[DataRequired(), validate_date_format_custom, validate_not_future], render_kw={"placeholder": "DD/MM/YYYY", "type": "text", "class": "date-string form-control"})
    paid_with_salary = BooleanField('هل تُصرف هذه المكافأة مع راتب نهاية الشهر؟', default=True)


