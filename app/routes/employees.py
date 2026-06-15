"""
Employee Routes
===============
Complete CRUD operations for employees
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file
from datetime import datetime
import sys
import os
from urllib.parse import urlencode

# Add core to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'core'))

from db_manager import DBManager
from database_models import EmployeeDocument, Employee
from app.forms import EmployeeForm, DocumentForm
from werkzeug.utils import secure_filename
from utils.helpers import parse_date_compact
import os
import pandas as pd
import io
from core.utils.excel_utils import apply_professional_style

employees_bp = Blueprint('employees', __name__)

# Helper function to get filter parameters from URL
def get_filter_params():
    """Extract filter parameters from request"""
    return {
        'search': request.args.get('search', ''),
        'department_ids': request.args.getlist('department_ids'),
        'dept_filter_mode': request.args.get('dept_filter_mode', 'include'),
        'status': request.args.get('status', ''),
        'job_title': request.args.get('job_title', ''),
        'date_from': request.args.get('date_from', ''),
        'date_to': request.args.get('date_to', '')
    }

# Helper function to build URL with filter parameters
def build_list_url(extra_params=None):
    """Build URL to employees list with current filter parameters"""
    filters = get_filter_params()
    if extra_params:
        filters.update(extra_params)

    # Build query string
    query_parts = []
    if filters.get('search'):
        query_parts.append(('search', filters['search']))
    for dept in filters.get('department_ids', []):
        query_parts.append(('department_ids', dept))
    if filters.get('dept_filter_mode'):
        query_parts.append(('dept_filter_mode', filters['dept_filter_mode']))
    if filters.get('status'):
        query_parts.append(('status', filters['status']))
    if filters.get('job_title'):
        query_parts.append(('job_title', filters['job_title']))
    if filters.get('date_from'):
        query_parts.append(('date_from', filters['date_from']))
    if filters.get('date_to'):
        query_parts.append(('date_to', filters['date_to']))

    if query_parts:
        return url_for('employees.list') + '?' + urlencode(query_parts)
    return url_for('employees.list')

@employees_bp.route('/')
def list():
    """List all employees with search and pagination"""
    db = current_app.db
    
    # Get parameters
    search = request.args.get('search', '')
    dept_filter_mode = request.args.get('dept_filter_mode', 'include')
    status_filter = request.args.get('status', '')
    job_title_filter = request.args.getlist('job_title')  # supports multiple selections
    date_from_str = request.args.get('date_from', '')
    date_to_str = request.args.get('date_to', '')
    dept_ids = request.args.getlist('department_ids')
    page = request.args.get('page', 1, type=int)
    
    # Parse dates
    from utils.helpers import parse_date_compact
    hire_date_from = parse_date_compact(date_from_str)
    hire_date_to = parse_date_compact(date_to_str)
    
    # Use optimized DB query with SQL-level filtering
    # We include all status if status_filter is empty, or specific status
    only_active = (status_filter == 'active')
    only_inactive = (status_filter == 'inactive')
    
    # We filter by dept in SQL if mode is 'include'
    sql_dept_ids = dept_ids if dept_filter_mode == 'include' else None
    
    # Initial optimized load (job_title=None, filtered in Python below for multi-select)
    employees = db.get_employees_optimized(
        only_active=only_active,
        department_ids=sql_dept_ids,
        job_title=None,
        search=search,
        load_full=False
    )
    
    # Post-process for complex filters not easily done in simple function above
    if only_inactive:
        employees = [e for e in employees if not e.is_active]
    
    if dept_ids and dept_filter_mode == 'exclude':
        dept_ids_int = [int(d) for d in dept_ids if d]
        employees = [e for e in employees if e.department_id not in dept_ids_int]

    # Filter by job titles (multiple)
    if job_title_filter and any(job_title_filter):
        employees = [e for e in employees if e.job_title in job_title_filter]

    # Date Range Filter (Still doing in Python but on smaller subset)
    if hire_date_from or hire_date_to:
        filtered = []
        for e in employees:
            if not e.hire_date: continue
            include = True
            if hire_date_from and e.hire_date < hire_date_from: include = False
            if hire_date_to and e.hire_date > hire_date_to: include = False
            if include: filtered.append(e)
        employees = filtered

    # 2. Get DEPARTMENTS
    departments = db.get_departments()
    
    # 4. Get Available Job Titles for filtering
    # For efficiency, we can get these from a small optimized query or use all titles
    job_titles = db.get_unique_job_titles()
    
    # Attach effective salary (based on SalaryHistory and today's date)
    db.attach_effective_salaries(employees)

    # Filters data
    # departments & job_titles are already calculated above
    # passed to template
    
    # Attach effective salary (based on SalaryHistory and today's date)
    db.attach_effective_salaries(employees)

    # Pass all employees to template for DataTables to handle
    employees_page = employees
    
    # Calculate pages (not needed for DataTables but keeping for template compatibility if used elsewhere)
    total_pages = 1
    total = len(employees)
    
    # Format dates for display (DD/MM/YYYY)
    from utils.helpers import format_date_ar
    hire_date_from_display = format_date_ar(hire_date_from) if hire_date_from else date_from_str
    hire_date_to_display = format_date_ar(hire_date_to) if hire_date_to else date_to_str

    return render_template('employees/list.html',
                          employees=employees_page,
                          search=search,
                          selected_departments=dept_ids,
                          dept_filter_mode=dept_filter_mode,
                          status_filter=status_filter,
                          selected_job_title=job_title_filter,  # list
                          hire_date_from=hire_date_from_display,
                          hire_date_to=hire_date_to_display,
                          departments=departments,
                          job_titles=job_titles,
                          page=page,
                          total_pages=total_pages,
                          total=total,
                          total_basic_salary=sum(getattr(e, 'effective_salary', e.basic_salary or 0) for e in employees),
                          total_incentives=sum(e.regularity_incentive or 0 for e in employees))

@employees_bp.route('/preview-filter')
def preview_filter():
    """Preview route for the new search filter design"""
    db = current_app.db
    
    # Get parameters
    search = request.args.get('search', '')
    dept_filter_mode = request.args.get('dept_filter_mode', 'include')
    status_filter = request.args.get('status', '')
    job_title_filter = request.args.getlist('job_title')
    date_from_str = request.args.get('date_from', '')
    date_to_str = request.args.get('date_to', '')
    dept_ids = request.args.getlist('department_ids')
    page = request.args.get('page', 1, type=int)
    
    # Parse dates
    from utils.helpers import parse_date_compact
    hire_date_from = parse_date_compact(date_from_str)
    hire_date_to = parse_date_compact(date_to_str)
    
    # Use optimized DB query with SQL-level filtering
    only_active = (status_filter == 'active')
    only_inactive = (status_filter == 'inactive')
    sql_dept_ids = dept_ids if dept_filter_mode == 'include' else None
    
    employees = db.get_employees_optimized(
        only_active=only_active,
        department_ids=sql_dept_ids,
        job_title=None, # Filtered in Python below to support multiple values
        search=search,
        load_full=False
    )
    
    # Post-process for complex filters not easily done in simple function above
    if only_inactive:
        employees = [e for e in employees if not e.is_active]
    
    if dept_ids and dept_filter_mode == 'exclude':
        dept_ids_int = [int(d) for d in dept_ids if d]
        employees = [e for e in employees if e.department_id not in dept_ids_int]

    # Filter by job titles (multiple)
    if job_title_filter and any(job_title_filter):
        employees = [e for e in employees if e.job_title in job_title_filter]

    # Date Range Filter
    if hire_date_from or hire_date_to:
        filtered = []
        for e in employees:
            if not e.hire_date: continue
            include = True
            if hire_date_from and e.hire_date < hire_date_from: include = False
            if hire_date_to and e.hire_date > hire_date_to: include = False
            if include: filtered.append(e)
        employees = filtered

    # Get DEPARTMENTS & Job Titles
    departments = db.get_departments()
    job_titles = db.get_unique_job_titles()
    
    db.attach_effective_salaries(employees)
    employees_page = employees
    
    total_pages = 1
    total = len(employees)
    
    from utils.helpers import format_date_ar
    hire_date_from_display = format_date_ar(hire_date_from) if hire_date_from else date_from_str
    hire_date_to_display = format_date_ar(hire_date_to) if hire_date_to else date_to_str

    return render_template('employees/preview_filter.html',
                          employees=employees_page,
                          search=search,
                          selected_departments=dept_ids,
                          dept_filter_mode=dept_filter_mode,
                          status_filter=status_filter,
                          selected_job_title=job_title_filter,
                          hire_date_from=hire_date_from_display,
                          hire_date_to=hire_date_to_display,
                          departments=departments,
                          job_titles=job_titles,
                          page=page,
                          total_pages=total_pages,
                          total=total,
                          total_basic_salary=sum(getattr(e, 'effective_salary', e.basic_salary or 0) for e in employees),
                          total_incentives=sum(e.regularity_incentive or 0 for e in employees))

@employees_bp.route('/check_code/<code>')
def check_code(code):
    """API to lookup employee by code (JSON)"""
    db = current_app.db
    emp = db.get_employee_by_code(code)
    
    if emp and emp.is_active:
        db.attach_effective_salaries([emp])
        return {
            'found': True,
            'id': emp.id,
            'name': emp.name,
            'basic_salary': emp.basic_salary,
            'effective_salary': getattr(emp, 'effective_salary', emp.basic_salary)
        }
    return {'found': False}

@employees_bp.route('/check_duplicate')
def check_duplicate():
    """Check if employee already exists by code or national_id"""
    db = current_app.db
    code = request.args.get('code')
    national_id = request.args.get('national_id')
    
    if not code and not national_id:
        return {'exists': False}
        
    return db.check_employee_exists(code, national_id)

@employees_bp.route('/create', methods=['GET', 'POST'])
def create():
    """Create new employee"""
    db = DBManager()
    form = EmployeeForm()
    
    # Populate department choices
    departments = db.get_departments()
    form.department_id.choices = [(0, 'اختر القسم...')] + [(d.id, d.name) for d in departments]
    
    # Pre-fill next available code on GET
    if request.method == 'GET' and not form.code.data:
        next_code = db.get_next_employee_code()
        if next_code:
            form.code.data = next_code

    if request.method == 'POST':
        try:
            # Validate only required fields (skip national_id and mobile_number validation)
            # Perform manual validation
            form.validate()
            
            # Check required fields manually
            has_required_errors = False
            if not form.name.data or not form.name.data.strip():
                form.name.errors = ['هذا الحقل مطلوب']
                has_required_errors = True
            if not form.code.data or not form.code.data.strip():
                form.code.errors = ['هذا الحقل مطلوب']
                has_required_errors = True
            if not form.hire_date.data:
                form.hire_date.errors = ['هذا الحقل مطلوب']
                has_required_errors = True
                
            if has_required_errors:
                return render_template('employees/form.html', form=form, mode='create')
            
            # Check for duplicates STRICTLY
            # We specifically check if code exists to give a specific error for code
            if db.check_employee_exists(form.code.data)['exists']:
                form.code.errors = ['هذا الكود مستخدم بالفعل لموظف آخر']
                has_required_errors = True
            
            # Check national ID duplicate separately if provided
            if form.national_id.data:
                # Use a custom query here or reuse check_employee_exists if it supports checking only national_id?
                # The existing method checks "code OR national_id".
                # Let's trust the method but if it returns true and code is unique (checked above), it must be national_id
                # However, to be precise, let's just use the errors list
                pass 

            if has_required_errors:
                 return render_template('employees/form.html', form=form, mode='create')

            # Show warnings for invalid optional fields OR block if strict
            warnings = []
            if form.national_id.data:
                nid = form.national_id.data.strip()
                if len(nid) != 14 or not nid.isdigit():
                    form.national_id.errors = ['الرقم القومي يجب أن يكون 14 رقم']
                    has_required_errors = True
            
            if form.mobile_number.data:
                mobile = form.mobile_number.data.strip()
                # User Requirement: Strictly 11 digits
                if not mobile.isdigit() or len(mobile) != 11:
                    form.mobile_number.errors = ['رقم الموبايل يجب أن يكون 11 رقم بالضبط']
                    has_required_errors = True
            
            if has_required_errors:
                 return render_template('employees/form.html', form=form, mode='create')
            
            # Parse dates from compact format or use date objects as-is
            from datetime import date as date_cls
            date_of_birth = None
            hire_date = None
            disruption_date = None
            insurance_start_date = None
            insurance_end_date = None
            
            if form.date_of_birth.data:
                date_of_birth = form.date_of_birth.data if isinstance(form.date_of_birth.data, date_cls) else parse_date_compact(form.date_of_birth.data)
            if form.hire_date.data:
                hire_date = form.hire_date.data if isinstance(form.hire_date.data, date_cls) else parse_date_compact(form.hire_date.data)
            if form.disruption_date.data:
                disruption_date = form.disruption_date.data if isinstance(form.disruption_date.data, date_cls) else parse_date_compact(form.disruption_date.data)
                
            # Insurance Logic & Validation
            is_insured = form.is_insured.data
            if is_insured:
                if form.insurance_start_date.data:
                    insurance_start_date = form.insurance_start_date.data if isinstance(form.insurance_start_date.data, date_cls) else parse_date_compact(form.insurance_start_date.data)
                if form.insurance_end_date.data:
                    insurance_end_date = form.insurance_end_date.data if isinstance(form.insurance_end_date.data, date_cls) else parse_date_compact(form.insurance_end_date.data)
                
                # Check End Date vs Start Date
                if insurance_end_date and insurance_start_date and insurance_end_date < insurance_start_date:
                    form.insurance_end_date.errors = ['تاريخ الخروج لا يمكن أن يكون قبل تاريخ البداية']
                    return render_template('employees/form.html', form=form, mode='create')
            else:
                # Force clear values if not insured
                insurance_start_date = None
                insurance_end_date = None
                
            # Create employee data dict
            employee_data = {
                'name': form.name.data,
                'code': form.code.data,
                'national_id': form.national_id.data if form.national_id.data and form.national_id.data.strip() else None,
                'date_of_birth': date_of_birth,
                'mobile_number': form.mobile_number.data,
                'address': form.address.data,
                'city': form.city.data,
                'governorate': form.governorate.data,
                'marital_status': form.marital_status.data,
                'military_status': form.military_status.data,
                'num_children': form.num_children.data or 0,
                'job_title': form.job_title.data,
                'department_id': form.department_id.data if form.department_id.data != 0 else None,
                'category': form.category.data,
                'hire_date': hire_date,
                'is_active': form.is_active.data,
                'basic_salary': form.basic_salary.data or 0,
                'incentive_allowance': form.incentive_allowance.data or 0.0,
                'regularity_incentive': form.regularity_incentive.data or 0.0,
                'entitled_to_official_holidays': form.entitled_to_official_holidays.data,
                'salary_type': form.salary_type.data,
                'daily_work_hours': form.daily_work_hours.data or 8.0,
                'standard_start_time': form.standard_start_time.data,
                'standard_end_time': form.standard_end_time.data,
                'overtime_allowed': form.overtime_allowed.data,
                'is_insured': is_insured,
                'insurance_policy': form.insurance_policy.data or 'employee_only' if is_insured else 'employee_only',
                'insurance_employee_share': form.insurance_employee_share.data or 11.0 if is_insured else 11.0,
                'insurance_company_share': form.insurance_company_share.data or 18.75 if is_insured else 18.75,
                'insurance_value_employee': form.insurance_value_employee.data or 0.0 if is_insured else 0.0,
                'insurance_value_company': form.insurance_value_company.data or 0.0 if is_insured else 0.0,
                'insurance_number': form.insurance_number.data if is_insured else None,
                'insurance_salary': form.insurance_salary.data or 0.0 if is_insured else 0.0,
                'insurance_start_date': insurance_start_date,
                'insurance_end_date': insurance_end_date,
                'transport_allowance': form.transport_allowance.data or 0.0,
                'disruption_date': disruption_date,
                'resignation_reason': form.resignation_reason.data
            }
            
            # Add employee
            new_emp = db.add_employee(**employee_data)
            
            # Show success message
            success_msg = f'✅ تم إضافة الموظف {form.name.data} بنجاح'
            if warnings:
                success_msg += '\n' + '\n'.join(warnings)
            
            flash(success_msg, 'center')
            return redirect(url_for('employees.view', id=new_emp.id))
            
        except Exception as e:
            flash(f'❌ حدث خطأ: {str(e)}', 'danger')
    
    return render_template('employees/form.html', form=form, mode='create')

@employees_bp.route('/<int:id>')
def view(id):
    """View employee details"""
    db = DBManager()
    employee = db.get_employee_by_id(id)
    
    if not employee:
        flash('الموظف غير موجود', 'danger')
        return redirect(url_for('employees.list'))
    
    # Get navigation (next/previous)
    next_emp = db.get_next_employee(id)
    prev_emp = db.get_previous_employee(id)
    
    # Get documents
    documents = db.get_employee_documents(id)
    document_form = DocumentForm()
    
    # Populate document types
    document_types = db.get_document_types()
    document_form.type_id.choices = [(dt.id, dt.name) for dt in document_types]
    
    # Get salary history
    salary_history = db.get_employee_salary_history(id)

    # Attach effective salary for display
    db.attach_effective_salaries([employee])
    
    return render_template('employees/view.html',
                         employee=employee,
                         next_emp=next_emp,
                         prev_emp=prev_emp,
                         documents=documents,
                         document_form=document_form,
                         salary_history=salary_history,
                         today=datetime.today().date())

@employees_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    """Edit employee"""
    db = DBManager()
    employee = db.get_employee_by_id(id)
    
    if not employee:
        flash('الموظف غير موجود', 'danger')
        return redirect(url_for('employees.list'))
    
    form = EmployeeForm(obj=employee)
    
    # Populate department choices
    departments = db.get_departments()
    form.department_id.choices = [(0, 'اختر القسم...')] + [(d.id, d.name) for d in departments]
    
    if request.method == 'POST':
        try:
            # Validate only required fields (skip national_id and mobile_number validation)
            form.validate()
            
            # Check required fields manually
            has_required_errors = False
            if not form.name.data or not form.name.data.strip():
                form.name.errors = ['هذا الحقل مطلوب']
                has_required_errors = True
            if not form.code.data or not form.code.data.strip():
                form.code.errors = ['هذا الحقل مطلوب']
                has_required_errors = True
            if not form.hire_date.data:
                form.hire_date.errors = ['هذا الحقل مطلوب']
                has_required_errors = True
                
            if has_required_errors:
                return render_template('employees/form.html', form=form, mode='edit', employee=employee)
            
            # Show warnings for invalid optional fields
            warnings = []
            if form.national_id.data:
                if len(form.national_id.data.strip()) != 14 or not form.national_id.data.strip().isdigit():
                    warnings.append('⚠️ الرقم القومي يجب أن يكون 14 رقم')
                    form.national_id.data = None  # Don't save invalid value
            
            if form.mobile_number.data:
                mobile = form.mobile_number.data.strip()
                if not mobile.isdigit() or len(mobile) < 10 or len(mobile) > 11:
                    warnings.append('⚠️ رقم الموبايل يجب أن يكون 10-11 رقم')
                    form.mobile_number.data = None  # Don't save invalid value
            
            # Parse dates from compact format or use date objects as-is
            from datetime import date as date_cls
            date_of_birth = None
            hire_date = None
            disruption_date = None
            if form.date_of_birth.data:
                date_of_birth = form.date_of_birth.data if isinstance(form.date_of_birth.data, date_cls) else parse_date_compact(form.date_of_birth.data)
            if form.hire_date.data:
                hire_date = form.hire_date.data if isinstance(form.hire_date.data, date_cls) else parse_date_compact(form.hire_date.data)
            if form.disruption_date.data:
                disruption_date = form.disruption_date.data if isinstance(form.disruption_date.data, date_cls) else parse_date_compact(form.disruption_date.data)
            
            # Update employee data
            employee_data = {
                'name': form.name.data,
                'code': form.code.data,
                'national_id': form.national_id.data if form.national_id.data and form.national_id.data.strip() else None,
                'date_of_birth': date_of_birth,
                'mobile_number': form.mobile_number.data,
                'address': form.address.data,
                'city': form.city.data,
                'governorate': form.governorate.data,
                'marital_status': form.marital_status.data,
                'military_status': form.military_status.data,
                'num_children': form.num_children.data or 0,
                'job_title': form.job_title.data,
                'department_id': form.department_id.data if form.department_id.data != 0 else None,
                'category': form.category.data,
                'hire_date': hire_date,
                'is_active': form.is_active.data,
                'basic_salary': form.basic_salary.data or 0,
                'incentive_allowance': form.incentive_allowance.data or 0.0,
                'regularity_incentive': form.regularity_incentive.data or 0.0,
                'entitled_to_official_holidays': form.entitled_to_official_holidays.data,
                'salary_type': form.salary_type.data,
                'daily_work_hours': form.daily_work_hours.data or 8.0,
                'standard_start_time': form.standard_start_time.data,
                'standard_end_time': form.standard_end_time.data,
                'overtime_allowed': form.overtime_allowed.data,
                'is_insured': form.is_insured.data,
                'insurance_policy': form.insurance_policy.data or 'employee_only',
                'insurance_employee_share': form.insurance_employee_share.data or 11.0,
                'insurance_company_share': form.insurance_company_share.data or 18.75,
                'insurance_value_employee': form.insurance_value_employee.data or 0.0,
                'insurance_value_company': form.insurance_value_company.data or 0.0,
                'insurance_number': form.insurance_number.data,
                'transport_allowance': form.transport_allowance.data or 0.0,
                'insurance_salary': form.insurance_salary.data or 0.0,
                'disruption_date': disruption_date,
                'resignation_reason': form.resignation_reason.data
            }
            
            # Filter out None values for required fields to prevent NOT NULL errors
            # (If validation failed above, these were set to None to trigger warnings but shouldn't overwrite DB)
            if employee_data.get('mobile_number') is None:
                employee_data.pop('mobile_number', None)
            if employee_data.get('national_id') is None:
                employee_data.pop('national_id', None)
            
            # Track salary change - handled by database listener in models.py
            # we just need to set the reason if we want a specific one
            old_salary = employee.basic_salary
            new_salary = employee_data.get('basic_salary', old_salary)
            
            if old_salary != new_salary:
                employee._change_reason = 'تعديل يدوي من صفحة البيانات'
            
            db.update_employee(id, **employee_data)
            
            # Show success message with warnings if any
            success_msg = f'✅ تم تحديث بيانات {form.name.data} بنجاح'
            if warnings:
                success_msg += '\n' + '\n'.join(warnings)
            
            flash(success_msg, 'center')
            return redirect(url_for('employees.view', id=id))
            
        except Exception as e:
            flash(f'❌ حدث خطأ: {str(e)}', 'danger')
    
    return render_template('employees/form.html', form=form, mode='edit', employee=employee)

@employees_bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    """Delete employee"""
    db = DBManager()
    employee = db.get_employee_by_id(id)
    
    if not employee:
        flash('الموظف غير موجود', 'danger')
        return redirect(url_for('employees.list'))
    
    try:
        employee_name = employee.name
        db.delete_employee(id)
        msg = f'تم حذف الموظف {employee_name} بنجاح'
        flash(msg, 'center')
        return {'success': True, 'message': msg, 'center': True}
    except Exception as e:
        flash(f'حدث خطأ أثناء الحذف: {str(e)}', 'danger')
        return {'success': False, 'error': str(e)}, 400

@employees_bp.route('/<int:id>/upload_document', methods=['POST'])
def upload_document(id):
    """Upload document for employee"""
    db = DBManager()
    form = DocumentForm()
    
    # Get filter parameters from POST (hidden inputs)
    filter_search = request.form.get('filter_search', '')
    filter_departments = request.form.getlist('filter_departments')
    filter_status = request.form.get('filter_status', '')
    filter_job_title = request.form.get('filter_job_title', '')
    
    # Re-populate choices before validation (required for dynamic selects)
    document_types = db.get_document_types()
    form.type_id.choices = [(dt.id, dt.name) for dt in document_types]
    
    if form.validate_on_submit():
        file = form.file.data
        if file:
            from werkzeug.utils import secure_filename
            filename = secure_filename(file.filename)
            # Create directory if not exists
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'documents', str(id))
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save file
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            
            # Save to DB (relative path for web)
            web_path = f'uploads/documents/{id}/{filename}'
            
            # Prepare data for new advanced document model
            doc_data = {
                'employee_id': id,
                'filename': filename,
                'file_path': web_path,
                'type_id': form.type_id.data,
                'expiry_date': form.expiry_date.data,
                'notes': form.notes.data
            }
            
            db.add_employee_document_advanced(**doc_data)
            
            flash('تم رفع المستند بنجاح', 'center')
        else:
            flash('لم يتم اختيار ملف', 'danger')
    else:
        # Show form errors
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    # Build URL with filter parameters
    query_parts = []
    if filter_search:
        query_parts.append(('search', filter_search))
    for dept in filter_departments:
        query_parts.append(('departments', dept))
    if filter_status:
        query_parts.append(('status', filter_status))
    if filter_job_title:
        query_parts.append(('job_title', filter_job_title))
    
    if query_parts:
        return redirect(url_for('employees.list') + '?' + urlencode(query_parts))
    return redirect(url_for('employees.list'))

@employees_bp.route('/<int:id>/delete_document/<int:doc_id>', methods=['POST'])
def delete_document(id, doc_id):
    """Delete employee document"""
    db = DBManager()
    
    # Get filter parameters from POST (hidden inputs)
    filter_search = request.form.get('filter_search', '')
    filter_departments = request.form.getlist('filter_departments')
    filter_status = request.form.get('filter_status', '')
    filter_job_title = request.form.get('filter_job_title', '')
    
    doc = db.delete_employee_document(doc_id)
    
    if doc:
        # Delete file from disk
        full_path = os.path.join(current_app.root_path, 'static', doc.file_path)
        if os.path.exists(full_path):
            try:
                os.remove(full_path)
            except:
                pass # Ignore if file not found
        flash('تم حذف المستند بنجاح', 'center')
        query_parts.append(('departments', dept))
    if filter_status:
        query_parts.append(('status', filter_status))
    if filter_job_title:
        query_parts.append(('job_title', filter_job_title))
    
    if query_parts:
        return redirect(url_for('employees.list') + '?' + urlencode(query_parts))
    return redirect(url_for('employees.list'))

@employees_bp.route('/import_excel', methods=['POST'])
def import_excel():
    """Import employees from Excel"""
    try:
        if 'file' not in request.files:
            flash('لم يتم اختيار ملف', 'danger')
            return redirect(build_list_url())
            
        file = request.files['file']
        if file.filename == '':
            flash('لم يتم اختيار ملف', 'danger')
            return redirect(build_list_url())
            
        if file and (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
            # Save file properly
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.root_path, '..', 'temp_import.xlsx')
            file.save(filepath)
            
            # Import
            from core.import_employees import import_employees
            import_employees(filepath)
            
            # Cleanup
            if os.path.exists(filepath):
                os.remove(filepath)
                
            flash('تم استيراد الموظفين بنجاح', 'center')
        else:
            flash('نوع الملف غير مدعوم. يرجى استخدام Excel (.xlsx)', 'danger')
            
    except Exception as e:
        flash(f'حدث خطأ أثناء الاستيراد: {str(e)}', 'danger')
        
    return redirect(build_list_url())

@employees_bp.route('/download_template')
def download_template():
    """Download Excel template for employee import"""
    import pandas as pd
    import io
    
    # Define columns
    columns = [
        'code', 'name', 'national_id', 'insurance_number', 'mobile_number', 
        'department', 'category', 'job_title', 'basic_salary', 'hire_date', 'address', 
        'city', 'governorate', 'marital_status', 'military_status', 'num_children', 'overtime_allowed',
        'standard_start_time', 'standard_end_time', 'regularity_incentive'
    ]
    
    # Create empty DataFrame
    df = pd.DataFrame(columns=columns)
    
    # Save to memory buffer
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Employees')
        
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name='employees_template.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@employees_bp.route('/export_excel')
def export_excel():
    """Export filtered employees to Excel with professional styling"""
    db = current_app.db

    # Get filters (mirroring list route)
    search = request.args.get('search', '')
    # Standardize names to match universal filter bar
    date_from_str = request.args.get('date_from', '')
    date_to_str = request.args.get('date_to', '')
    dept_ids = request.args.getlist('department_ids')
    dept_filter_mode = request.args.get('dept_filter_mode', 'include')
    status_filter = request.args.get('status', '')
    job_title_filter = request.args.get('job_title', '')
    
    hire_date_from = parse_date_compact(date_from_str)
    hire_date_to = parse_date_compact(date_to_str)
    
    # Use optimized DB query with SQL-level filtering
    only_active = (status_filter == 'active')
    only_inactive = (status_filter == 'inactive')
    
    # We filter by dept in SQL if mode is 'include'
    sql_dept_ids = dept_ids if dept_filter_mode == 'include' else None
    
    # Initial optimized load
    employees = db.get_employees_optimized(
        only_active=only_active,
        department_ids=sql_dept_ids,
        job_title=job_title_filter,
        search=search,
        load_full=True # Export usually needs full details
    )
    
    # Post-process for complex filters
    if only_inactive:
        employees = [e for e in employees if not e.is_active]
    
    if dept_ids and dept_filter_mode == 'exclude':
        dept_ids_int = [int(d) for d in dept_ids if d]
        employees = [e for e in employees if e.department_id not in dept_ids_int]
            
    # Apply Hire Date Filter
    if hire_date_from or hire_date_to:
        filtered = []
        for e in employees:
            if not e.hire_date: continue
            include = True
            if hire_date_from and e.hire_date < hire_date_from: include = False
            if hire_date_to and e.hire_date > hire_date_to: include = False
            if include: filtered.append(e)
        employees = filtered

    # 5. Apply Search Query
    employees = date_filtered_emps
    if search:
        search_lower = search.lower()
        employees = [e for e in employees if
                      (e.name and search_lower in e.name.lower()) or
                      (e.code and search_lower in e.code.lower())]
                     
    # Prepare data for Excel
    data = []
    for emp in employees:
        data.append({
            'الكود': emp.code,
            'الاسم': emp.name,
            'الوظيفة': emp.job_title or '',
            'القسم': emp.department.name if emp.department else '',
            'تاريخ التعيين': emp.hire_date,
            'الراتب الأساسي': float(emp.basic_salary or 0),
            'حافز الانتظام': float(emp.regularity_incentive or 0),
            'إضافي مسموح': 'نعم' if emp.overtime_allowed else 'لا',
            'الحالة': 'يعمل' if emp.is_active else 'لا يعمل',
            'رقم الموبايل': emp.mobile_number or '',
            'الرقم القومي': emp.national_id or '',
            'رقم التأمين': emp.insurance_number or ''
        })
        
    df = pd.DataFrame(data)
    
    # Create Excel file
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Employees')
        
        # Apply professional styling
        worksheet = writer.sheets['Employees']
        apply_professional_style(worksheet, df)
        
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'employees_list_{datetime.now().strftime("%Y%m%d")}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@employees_bp.route('/bulk')
def bulk_entry():
    """Bulk employee entry page"""
    db = current_app.db
    departments = db.get_departments()
    from utils.helpers import format_date_ar
    today = format_date_ar(datetime.now().date())
    
    # Get all distinct job titles for fallback/suggestion
    all_employees = db.get_all_employees()
    all_job_titles = sorted(set(e.job_title for e in all_employees if e.job_title))
    
    # Calculate next code
    next_code = "1001"
    try:
        # Find max code that is numeric
        codes = [int(e.code) for e in all_employees if e.code and e.code.isdigit()]
        if codes:
            next_code = str(max(codes) + 1)
    except Exception:
        pass

    return render_template('employees/bulk.html', 
                           departments=departments, 
                           today=today,
                           all_job_titles=all_job_titles,
                           next_code=next_code)

@employees_bp.route('/bulk_edit')
def bulk_edit():
    """Bulk employee edit page"""
    db = current_app.db
    departments = db.get_departments()
    all_employees = db.get_all_employees()
    all_job_titles = sorted(set(e.job_title for e in all_employees if e.job_title))

    return render_template(
        'employees/bulk_edit.html',
        departments=departments,
        all_job_titles=all_job_titles
    )

@employees_bp.route('/bulk_edit/load')
def bulk_edit_load():
    """Load employees for bulk editing"""
    db = current_app.db

    search = (request.args.get('search') or '').strip()
    department_id = (request.args.get('department_id') or '').strip()
    status = (request.args.get('status') or '').strip()
    job_title = (request.args.get('job_title') or '').strip()
    is_insured = (request.args.get('is_insured') or '').strip()

    session = db.get_session()
    try:
        query = session.query(Employee)
        if search:
            query = query.filter((Employee.name.like(f"%{search}%")) | (Employee.code.like(f"%{search}%")))
        if department_id:
            try:
                query = query.filter(Employee.department_id == int(department_id))
            except ValueError:
                pass
        if status == 'active':
            query = query.filter(Employee.is_active == True)
        elif status == 'inactive':
            query = query.filter(Employee.is_active == False)
        if job_title:
            query = query.filter(Employee.job_title == job_title)
        if is_insured == 'insured':
            query = query.filter(Employee.is_insured == True)
        elif is_insured == 'uninsured':
            query = query.filter(Employee.is_insured == False)

        # Order by employee code ascending by default (attempt numeric ordering when possible)
        try:
            from sqlalchemy import cast, Integer
            employees = query.order_by(cast(Employee.code, Integer).asc(), Employee.code.asc()).all()
        except Exception:
            employees = query.order_by(Employee.code.asc()).all()
    finally:
        session.close()

    from utils.helpers import format_date_ar

    def fmt_date(d):
        return format_date_ar(d) if d else ''

    def fmt_time(t):
        return t.strftime('%H:%M') if t else ''

    data = []
    for emp in employees:
        data.append({
            'id': emp.id,
            'code': emp.code,
            'name': emp.name,
            'national_id': emp.national_id or '',
            'date_of_birth': fmt_date(emp.date_of_birth),
            'governorate': emp.governorate or '',
            'city': emp.city or '',
            'address': emp.address or '',
            'mobile_number': emp.mobile_number or '',
            'department_id': emp.department_id or '',
            'job_title': emp.job_title or '',
            'category': emp.category or 'Employee',
            'hire_date': fmt_date(emp.hire_date),
            'standard_start_time': fmt_time(emp.standard_start_time),
            'standard_end_time': fmt_time(emp.standard_end_time),
            'daily_work_hours': float(emp.daily_work_hours or 0),
            'is_active': bool(emp.is_active),
            'basic_salary': float(emp.basic_salary or 0),
            'regularity_incentive': float(emp.regularity_incentive or 0),
            'incentive_allowance': float(emp.incentive_allowance or 0),
            'transport_allowance': float(emp.transport_allowance or 0),
            'overtime_allowed': bool(emp.overtime_allowed),
            'is_insured': bool(emp.is_insured),
            'insurance_policy': emp.insurance_policy or 'employee_only',
            'insurance_start_date': fmt_date(emp.insurance_start_date),
            'insurance_number': emp.insurance_number or '',
            'insurance_salary': float(emp.insurance_salary or 0),
            'insurance_employee_share': float(emp.insurance_employee_share or 11.0),
            'insurance_company_share': float(emp.insurance_company_share or 18.75)
        })

    return {'success': True, 'employees': data}

@employees_bp.route('/bulk_edit/save', methods=['POST'])
def bulk_edit_save():
    """Save bulk edited employees"""
    db = current_app.db
    data = request.get_json() or {}
    employees = data.get('employees', [])

    if not employees:
        return {'success': False, 'message': 'لا توجد بيانات للحفظ'}

    count = 0
    errors = []

    from utils.helpers import parse_date_compact
    from datetime import datetime

    for item in employees:
        try:
            emp_id = item.get('id')
            if not emp_id:
                continue

            name = str(item.get('name', '')).strip()
            code = str(item.get('code', '')).strip()
            if not name or not code:
                errors.append(f"بيانات ناقصة للموظف {name or 'غير معروف'}")
                continue

            # Parse dates
            hire_date = parse_date_compact(item.get('hire_date')) if item.get('hire_date') else None
            date_of_birth = parse_date_compact(item.get('date_of_birth')) if item.get('date_of_birth') else None
            insurance_start_date = parse_date_compact(item.get('insurance_start_date')) if item.get('insurance_start_date') else None

            # Parse times
            start_time = None
            if item.get('standard_start_time'):
                try:
                    start_time = datetime.strptime(item.get('standard_start_time'), '%H:%M').time()
                except ValueError:
                    start_time = None

            end_time = None
            if item.get('standard_end_time'):
                try:
                    end_time = datetime.strptime(item.get('standard_end_time'), '%H:%M').time()
                except ValueError:
                    end_time = None

            employee_data = {
                'name': name,
                'code': code,
                'national_id': item.get('national_id') or None,
                'date_of_birth': date_of_birth,
                'governorate': item.get('governorate') or None,
                'city': item.get('city') or None,
                'address': item.get('address') or None,
                'mobile_number': item.get('mobile_number') or None,
                'department_id': int(item['department_id']) if item.get('department_id') else None,
                'job_title': item.get('job_title') or None,
                'category': item.get('category') or 'Employee',
                'hire_date': hire_date,
                'standard_start_time': start_time,
                'standard_end_time': end_time,
                'daily_work_hours': float(item.get('daily_work_hours') or 0),
                'is_active': bool(item.get('is_active')),
                'basic_salary': float(item.get('basic_salary') or 0),
                'regularity_incentive': float(item.get('regularity_incentive') or 0),
                'incentive_allowance': float(item.get('incentive_allowance') or 0),
                'transport_allowance': float(item.get('transport_allowance') or 0),
                'overtime_allowed': bool(item.get('overtime_allowed')),
                'is_insured': bool(item.get('is_insured')),
                'insurance_policy': item.get('insurance_policy') or 'employee_only',
                'insurance_start_date': insurance_start_date,
                'insurance_number': item.get('insurance_number') or None,
                'insurance_salary': float(item.get('insurance_salary') or 0),
                'insurance_employee_share': float(item.get('insurance_employee_share') or 11.0),
                'insurance_company_share': float(item.get('insurance_company_share') or 18.75)
            }

            db.update_employee(emp_id, **employee_data)
            count += 1
        except Exception as e:
            errors.append(f"خطأ للموظف {item.get('name', '')}: {str(e)}")

    if errors:
        return {'success': False, 'message': 'تم حفظ البعض ولكن حدثت أخطاء:\n' + '\n'.join(errors[:10]), 'count': count}

    msg = f'تم تحديث {count} موظف بنجاح'
    flash(msg, 'center')
    return {'success': True, 'count': count, 'message': msg, 'center': True}

@employees_bp.route('/get_jobs/<int:dept_id>')
def get_department_jobs(dept_id):
    """Get job titles for a specific department"""
    db = current_app.db
    employees = db.get_all_employees()
    # Filter by department and get unique job titles
    jobs = sorted(set(e.job_title for e in employees if e.department_id == dept_id and e.job_title))
    return {'jobs': jobs}

@employees_bp.route('/bulk/save', methods=['POST'])
def bulk_save():
    """Save bulk employees"""
    db = current_app.db
    data = request.get_json()
    employees = data.get('employees', [])
    
    count = 0
    errors = []
    
    from utils.helpers import parse_date_compact
    from datetime import datetime
    
    for item in employees:
        try:
            # Basic validation (Strict)
            name = str(item.get('name', '')).strip()
            code = str(item.get('code', '')).strip()

            if not name or not code:
                # Skip empty rows silently or log?
                # If name is present but code missing, logical error, but if both missing, skip.
                if not name and not code:
                     continue
                errors.append(f"بيانات ناقصة للموظف {name or 'غير معروف'}")
                continue
                
            # Check code existence
            if db.check_employee_exists(code, item.get('national_id'))['exists']:
                errors.append(f"الكود {code} أو الرقم القومي مستخدم بالفعل")
                continue

            # Parse dates
            hire_date = parse_date_compact(item.get('hire_date')) if item.get('hire_date') else None
            date_of_birth = parse_date_compact(item.get('date_of_birth')) if item.get('date_of_birth') else None
            insurance_start_date = parse_date_compact(item.get('insurance_start_date')) if item.get('insurance_start_date') else None
            insurance_end_date = parse_date_compact(item.get('insurance_end_date')) if item.get('insurance_end_date') else None
            disruption_date = parse_date_compact(item.get('disruption_date')) if item.get('disruption_date') else None

            # Parse times
            start_time = None
            if item.get('standard_start_time'):
                try:
                    start_time = datetime.strptime(item.get('standard_start_time'), '%H:%M').time()
                except ValueError:
                    start_time = None

            end_time = None
            if item.get('standard_end_time'):
                try:
                    end_time = datetime.strptime(item.get('standard_end_time'), '%H:%M').time()
                except ValueError:
                    end_time = None

            # Prepare employee data
            # USE STRIPPED VALUES FROM VALIDATION
            employee_data = {
                'name': name,
                'code': code,
                'national_id': item.get('national_id'),
                'department_id': int(item['department_id']) if item.get('department_id') else None,
                'job_title': item.get('job_title'),
                'basic_salary': float(item.get('basic_salary', 0)),
                'hire_date': hire_date,
                
                # Extended fields
                'mobile_number': item.get('mobile_number'),
                'address': item.get('address'),
                'city': item.get('city'),
                'governorate': item.get('governorate'),
                'date_of_birth': date_of_birth,
                'marital_status': item.get('marital_status'),
                'military_status': item.get('military_status'),
                'num_children': int(item.get('num_children') or 0),
                
                'category': item.get('category') or 'Employee',
                'salary_type': item.get('salary_type', 'monthly'),
                'regularity_incentive': float(item.get('regularity_incentive', 0)),
                'incentive_allowance': float(item.get('incentive_allowance', 0)),
                'transport_allowance': float(item.get('transport_allowance', 0)),
                'is_active': item.get('is_active', True),
                
                # Work hours
                'standard_start_time': start_time,
                'standard_end_time': end_time,
                'daily_work_hours': float(item.get('daily_work_hours') or 8.0),
                'overtime_allowed': item.get('overtime_allowed', False),
                
                # Insurance
                'is_insured': item.get('is_insured', False),
                'insurance_policy': item.get('insurance_policy', 'employee_only'),
                'insurance_number': item.get('insurance_number'),
                'insurance_salary': float(item.get('insurance_salary', 0)),
                'insurance_employee_share': float(item.get('insurance_employee_share', 11.0)),
                'insurance_company_share': float(item.get('insurance_company_share', 18.75)),
                'insurance_value_employee': float(item.get('insurance_value_employee', 0)),
                'insurance_value_company': float(item.get('insurance_value_company', 0)),
                'insurance_start_date': insurance_start_date,
                'insurance_end_date': insurance_end_date,
                
                'disruption_date': disruption_date,
                'resignation_reason': item.get('resignation_reason')
            }
            
            # Clean up empty strings/None for optional fields
            # (Remove keys where value is None or empty string BUT keep 0/False)
            filtered_data = {}
            for k, v in employee_data.items():
                if v is None or v == '':
                    continue
                filtered_data[k] = v
            
            db.add_employee(**filtered_data)
            count += 1
            
        except Exception as e:
            errors.append(f"خطأ للموظف {item.get('name', '')}: {str(e)}")
            
    if errors:
        return {'success': False, 'message': 'تم حفظ البعض ولكن حدثت أخطاء:\n' + '\n'.join(errors[:10]), 'count': count}
        
    msg = f'تم إضافة {count} موظف بنجاح'
    flash(msg, 'center')
    return {'success': True, 'count': count, 'message': msg, 'center': True}

@employees_bp.route('/bulk_salaries')
def bulk_salaries():
    """Page for bulk updating employee salaries"""
    db = current_app.db
    departments = db.get_departments()
    
    # Optional filtering by department
    dept_ids = request.args.getlist('departments', type=int)
    
    employees = db.get_all_employees(only_active=True)
    if dept_ids:
        employees = [e for e in employees if e.department_id in dept_ids]

    # Attach effective salary for display
    db.attach_effective_salaries(employees)
        
    from datetime import datetime
    return render_template('employees/bulk_salaries.html', 
                         employees=employees, 
                         departments=departments,
                         selected_dept_ids=dept_ids,
                         now=datetime.now())

@employees_bp.route('/bulk_salaries/save', methods=['POST'])
def bulk_salaries_save():
    """Save bulk salary updates"""
    db = current_app.db
    data = request.get_json()
    updates = data.get('updates', [])
    effective_date_str = data.get('effective_date')
    effective_date_iso = data.get('effective_date_iso')
    
    effective_date = None
    if effective_date_str or effective_date_iso:
        def _normalize_digits(s):
            if not s:
                return s
            arabic_digits = '٠١٢٣٤٥٦٧٨٩'
            eastern_digits = '۰۱۲۳۴۵۶۷۸۹'
            out = []
            for ch in s:
                if ch in arabic_digits:
                    out.append(str(arabic_digits.index(ch)))
                elif ch in eastern_digits:
                    out.append(str(eastern_digits.index(ch)))
                else:
                    out.append(ch)
            return ''.join(out)

        if effective_date_str:
            effective_date_str = _normalize_digits(effective_date_str.strip())
        if effective_date_iso:
            effective_date_iso = _normalize_digits(effective_date_iso.strip())

        parsed = None
        for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
            try:
                parsed = datetime.strptime(effective_date_str, fmt)
                break
            except ValueError:
                continue
        if not parsed and effective_date_iso:
            try:
                parsed = datetime.strptime(effective_date_iso, '%Y-%m-%d')
            except ValueError:
                parsed = None
        if not parsed:
            return {'success': False, 'message': 'صيغة تاريخ التفعيل غير صحيحة. استخدم DD/MM/YYYY'}
        effective_date = parsed
            
    if not updates:
        return {'success': False, 'message': 'لا توجد بيانات لتحديثها'}
        
    try:
        db.bulk_update_salaries(updates, effective_date=effective_date)
        msg = f'تم تحديث رواتب {len(updates)} موظف بنجاح'
        flash(msg, 'center')
        return {'success': True, 'message': msg, 'center': True}
    except Exception as e:
        # Return error for AJAX caller
        return {'success': False, 'message': f'حدث خطأ: {str(e)}'}

def salary_history_delete(record_id):
    """Delete a specific salary history record"""
    db = current_app.db
    try:
        success, message = db.delete_salary_history_record(record_id)
        if success:
            return {'success': True, 'message': message}
        else:
            return {'success': False, 'message': message}
    except Exception as e:
        return {'success': False, 'message': f'حدث خطأ: {str(e)}'}

@employees_bp.route('/salary_history/rollback/<int:id>', methods=['POST'])
def salary_rollback(id):
    """Rollback last salary update (Legacy support - redirect to new logic if needed)"""
    db = current_app.db
    # جلب السجل الأحدث وحذفه باستخدام الدالة الجديدة لتوحيد المنطق
    session = db.get_session()
    from core.database_models import SalaryHistory
    last = session.query(SalaryHistory).filter_by(employee_id=id).order_by(SalaryHistory.effective_date.desc()).first()
    session.close()
    
    if last:
        return salary_history_delete(last.id)
    return {'success': False, 'message': 'لا يوجد سجل للتراجع عنه'}
