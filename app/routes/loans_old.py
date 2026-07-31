"""
Loans Routes
============
Loans management
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'core'))

from app.forms import LoanForm
import pandas as pd
import io
from flask import send_file
from core.utils.excel_utils import apply_professional_style

loans_bp = Blueprint('loans', __name__)

@loans_bp.route('/')
def list():
    """List all loans with filters"""
    db = current_app.db
    
    # Filters
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    # Use getlist for multiple selections
    department_ids = request.args.getlist('department_ids', type=int) 
    # Fallback to single department_id if getlist is empty (backward compatibility/direct link)
    if not department_ids and request.args.get('department_id'):
         department_ids = [request.args.get('department_id', type=int)]
         
    dept_filter_mode = request.args.get('dept_filter_mode', 'include')
    search_code = request.args.get('search_code', '').strip()
    
    # If searching by code, ignore department filter to find the employee regardless of department
    if search_code:
        department_ids = []
    
    # Get loans
    loans = db.search_loans(
        date_from=date_from, 
        date_to=date_to, 
        department_ids=department_ids, 
        dept_filter_mode=dept_filter_mode, 
        code=search_code
    )
    
    # Calculate statistics
    total_loans_amount = sum(loan.amount for loan in loans)
    beneficiaries_count = len(set(loan.employee_id for loan in loans))
    
    # Group loans by department
    grouped_loans = {}
    for loan in loans:
        dept_name = loan.employee.department.name if loan.employee and loan.employee.department else 'بدون قسم'
        if dept_name not in grouped_loans:
            grouped_loans[dept_name] = {
                'loans': [],
                'total_amount': 0,
                'beneficiaries': set()
            }
        grouped_loans[dept_name]['loans'].append(loan)
        grouped_loans[dept_name]['total_amount'] += loan.amount
        grouped_loans[dept_name]['beneficiaries'].add(loan.employee_id)
    
    # Convert sets to counts for template
    for dept in grouped_loans:
        grouped_loans[dept]['beneficiaries_count'] = len(grouped_loans[dept]['beneficiaries'])

    # Get departments for filter
    departments = db.get_departments()
    
    # Sort grouped_loans by department order (same as dropdown)
    from collections import OrderedDict
    dept_order = {dept.name: idx for idx, dept in enumerate(departments)}
    sorted_grouped_loans = OrderedDict(
        sorted(grouped_loans.items(), key=lambda x: dept_order.get(x[0], 999))
    )
    
    return render_template('loans/list.html', 
                         loans=loans,
                         grouped_loans=sorted_grouped_loans,
                         departments=departments,
                         date_from=date_from,
                         date_to=date_to,
                         department_ids=department_ids,
                         dept_filter_mode=dept_filter_mode,
                         search_code=search_code,
                         total_loans_amount=total_loans_amount,
                         beneficiaries_count=beneficiaries_count)

@loans_bp.route('/create', methods=['GET', 'POST'])
def create():
    """Create new loan"""
    form = LoanForm()
    db = current_app.db
    
    form.employee_id.choices = [(e.id, f"{e.name} ({e.code})") for e in db.get_all_employees() if e.is_active]
    
    if form.validate_on_submit():
        try:
            db.add_loan(
                employee_id=form.employee_id.data,
                amount=form.amount.data,
                loan_type=form.loan_type.data,
                number_of_installments=form.number_of_installments.data,
                date_issued=(form.date.data if form.date.data else datetime.now().date()),
                excluded_months=form.excluded_months.data
            )
            flash('تم إضافة السلفة بنجاح', 'center')
            return redirect(url_for('loans.list'))
        except Exception as e:
            flash(f'حدث خطأ: {str(e)}', 'danger')
    
    today = datetime.now().date()
    from utils.helpers import format_date_ar
    if request.method == 'GET' and not form.date.data:
        form.date.data = today
    return render_template('loans/form.html', form=form, mode='create', today=format_date_ar(today))

@loans_bp.route('/<int:id>')
def view(id):
    """View loan details"""
    db = current_app.db
    loan = db.get_loan_by_id(id)
    
    if not loan:
        flash('السلفة غير موجودة', 'danger')
        return redirect(url_for('loans.list'))
    
    return render_template('loans/view.html', loan=loan)

@loans_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    """Edit loan"""
    db = current_app.db
    loan = db.get_loan_by_id(id)
    
    if not loan:
        flash('السلفة غير موجودة', 'danger')
        return redirect(url_for('loans.list'))
    
    form = LoanForm(obj=loan)
    form.employee_id.choices = [(e.id, f"{e.name} ({e.code})") for e in db.get_all_employees() if e.is_active]
    
    if form.validate_on_submit():
        try:
            db.update_loan(
                loan_id=id,
                employee_id=form.employee_id.data,
                amount=form.amount.data,
                type=form.loan_type.data,
                installments_count=form.number_of_installments.data,
                date=(form.date.data if form.date.data else loan.date),
                excluded_months=form.excluded_months.data
            )
            flash('تم تحديث السلفة بنجاح', 'center')
            return redirect(url_for('loans.view', id=id))
        except Exception as e:
            flash(f'حدث خطأ: {str(e)}', 'danger')
    
    # Pre-populate form with loan data
    if request.method == 'GET':
        form.employee_id.data = loan.employee_id
        form.amount.data = loan.amount
        form.loan_type.data = loan.type
        form.number_of_installments.data = loan.installments_count
        form.date.data = loan.date
        form.excluded_months.data = loan.excluded_months
    
    from utils.helpers import format_date_ar
    today = format_date_ar(loan.date if loan.date else datetime.now().date())
    return render_template('loans/form.html', form=form, mode='edit', loan=loan, today=today)

@loans_bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    """Delete loan"""
    db = current_app.db
    
    try:
        db.delete_loan(id)
        flash('تم حذف السلفة بنجاح', 'center')
    except Exception as e:
        flash(f'حدث خطأ: {str(e)}', 'danger')
    
    return redirect(url_for('loans.list'))
    return redirect(url_for('loans.list'))

@loans_bp.route('/bulk')
def bulk_entry():
    """Bulk loan entry page"""
    from utils.helpers import format_date_ar
    today = format_date_ar(datetime.now().date())
    return render_template('loans/bulk.html', today=today)

@loans_bp.route('/check_duplicate')
def check_duplicate():
    """Check if employee already has a loan on a specific date"""
    db = current_app.db
    employee_id = request.args.get('employee_id', type=int)
    date_str = request.args.get('date')
    
    if not employee_id or not date_str:
        return {'exists': False}
        
    from utils.helpers import parse_date_compact
    date_val = parse_date_compact(date_str)
    
    if not date_val:
        return {'exists': False}
        
    exists = db.check_loan_exists(employee_id, date_val)
    return {'exists': exists}

@loans_bp.route('/bulk/save', methods=['POST'])
def bulk_save():
    """Save bulk loans"""
    db = current_app.db
    data = request.get_json()
    loans = data.get('loans', [])
    
    count = 0
    errors = []
    
    from utils.helpers import parse_date_compact
    
    for item in loans:
        try:
            # Parse date
            date_val = parse_date_compact(item.get('date'))
            if not date_val:
                date_val = datetime.now().date()
                
            # Check for duplicate
            if db.check_loan_exists(int(item['employee_id']), date_val):
                # Skip or add error? User wants to prevent duplicate.
                # Let's add to errors to notify which ones were skipped
                errors.append(f"الموظف {item.get('employee_id')} لديه سلفة بالفعل بتاريخ {date_val}")
                continue

            db.add_loan(
                employee_id=int(item['employee_id']),
                amount=float(item['amount']),
                loan_type=item['loan_type'],
                number_of_installments=int(item['number_of_installments']),
                date_issued=date_val,
                excluded_months=item.get('excluded_months') # Optional if we add it to grid later
            )
            count += 1
        except Exception as e:
            errors.append(f"Error for Emp {item.get('employee_id')}: {str(e)}")
            
    if errors:
        return {'success': False, 'message': ', '.join(errors)}
        
    flash(f'تم إضافة {count} سلفة بنجاح', 'center')
    return {'success': True}

@loans_bp.route('/bulk_edit')
def bulk_edit():
    """Bulk edit loans page"""
    db = current_app.db
    departments = db.get_departments()
    return render_template('loans/bulk_edit.html', departments=departments)

@loans_bp.route('/bulk_edit/load')
def bulk_edit_load():
    """Load loans for bulk editing"""
    db = current_app.db
    
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    department_id = request.args.get('department_id', type=int)
    
    try:
        # Get loans with filters
        loans = db.search_loans(
            date_from=date_from,
            date_to=date_to,
            department_ids=[department_id] if department_id else None
        )
        
        # Format loans for frontend
        loans_data = []
        for loan in loans:
            from utils.helpers import format_date_ar
            loans_data.append({
                'id': loan.id,
                'employee_id': loan.employee_id,
                'employee_code': loan.employee.code if loan.employee else '',
                'employee_name': loan.employee.name if loan.employee else '',
                'amount': float(loan.amount),
                'type': loan.type,
                'installments_count': loan.installments_count,
                'date': format_date_ar(loan.date) if loan.date else '',
                'date_iso': loan.date.strftime('%Y-%m-%d') if loan.date else '',  # For HTML date input
                'excluded_months': loan.excluded_months or ''
            })
        
        return {'success': True, 'loans': loans_data}
    except Exception as e:
        return {'success': False, 'message': str(e)}

@loans_bp.route('/bulk_edit/save', methods=['POST'])
def bulk_edit_save():
    """Save bulk edited loans"""
    db = current_app.db
    data = request.get_json()
    loans = data.get('loans', [])
    
    updated = 0
    errors = []
    
    from utils.helpers import parse_date_compact
    
    for item in loans:
        try:
            loan_id = item.get('id')
            if not loan_id:
                continue
                
            # Parse date - can be ISO or DD/MM/YYYY
            date_str = item.get('date')
            date_val = None
            if date_str:
                from utils.helpers import parse_date_compact
                date_val = parse_date_compact(date_str)
                if not date_val:
                    try:
                        # Fallback for ISO
                        from datetime import datetime
                        date_val = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except:
                        pass
            
            # Update loan
            update_data = {
                'loan_id': loan_id,
                'amount': float(item['amount']),
                'type': item['type'],
                'installments_count': int(item['installments_count']),
                'date': date_val,
                'excluded_months': item.get('excluded_months') if item.get('excluded_months') else None
            }
            
            # Use provided remaining balance if it exists and looks valid, otherwise don't reset it
            if 'remaining_balance' in item and item['remaining_balance'] is not None:
                try:
                    update_data['remaining_balance'] = float(item['remaining_balance'])
                except:
                    pass
            
            db.update_loan(**update_data)
            updated += 1
        except Exception as e:
            errors.append(f"Error for Loan ID {item.get('id')}: {str(e)}")
    
    if errors:
        return {'success': False, 'message': '; '.join(errors[:5])}  # Show first 5 errors
    
    return {'success': True, 'updated': updated}
    return {'success': True, 'updated': updated}

@loans_bp.route('/export_excel')
def export_excel():
    """Export loans list to Excel"""
    try:
        db = current_app.db
        
        # Get Filters (Duplicate logic from list route)
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        department_ids = request.args.getlist('department_ids', type=int) 
        if not department_ids and request.args.get('department_id'):
             department_ids = [request.args.get('department_id', type=int)]
             
        search_code = request.args.get('search_code', '').strip()
        if search_code:
            department_ids = []
        
        # Get data
        loans = db.search_loans(
            date_from=date_from, 
            date_to=date_to, 
            department_ids=department_ids, 
            code=search_code
        )
        
        excel_data = []
        from utils.helpers import format_date_ar
        
        for loan in loans:
            dept_name = loan.employee.department.name if loan.employee and loan.employee.department else 'بدون قسم'
            
            excel_data.append({
                'م': loan.id,
                'كود الموظف': loan.employee.code if loan.employee else '',
                'اسم الموظف': loan.employee.name if loan.employee else '',
                'القسم': dept_name,
                'قيمة السلفة': float(loan.amount),
                'نوع السلفة': loan.type,
                'عدد الأقساط': loan.installments_count,
                'قيمة القسط': float(loan.amount / loan.installments_count) if loan.installments_count > 0 else 0.0,
                'تاريخ الصرف': format_date_ar(loan.date),
                'الأشهر المستبعدة': loan.excluded_months or ''
            })
            
        if not excel_data:
            flash("لا توجد سلف لتصديرها (حسب الفلاتر المختارة)", "warning")
            return redirect(url_for('loans.list'))

        # Create Excel
        df = pd.DataFrame(excel_data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Loans List')
            apply_professional_style(writer.book.active, df)

        output.seek(0)
        filename = f"Loans_List_{datetime.now().strftime('%Y_%m_%d')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f"حدث خطأ أثناء تصدير ملف Excel: {str(e)}", "danger")
        return redirect(url_for('loans.list'))
