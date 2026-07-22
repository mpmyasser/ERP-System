"""
Penalties Routes
================
Penalties management
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'core'))

from db_manager import DBManager
from app.forms import PenaltyForm
from app.utils.form_helpers import employee_choices
from utils.helpers import parse_date_compact, format_date_ar

penalties_bp = Blueprint('penalties', __name__)

@penalties_bp.route('/')
def list():
    """List all penalties with filters"""
    db = current_app.db
    session = db.get_session()
    
    try:
        from database_models import PenaltyBonus, Employee, Department
        from sqlalchemy.orm import joinedload
        
        # Get filters
        date_from_str = request.args.get('date_from')
        date_to_str = request.args.get('date_to')
        dept_ids = request.args.getlist('department_ids', type=int)
        dept_filter_mode = request.args.get('dept_filter_mode', 'include')
        
        query = session.query(PenaltyBonus).join(Employee).options(
            joinedload(PenaltyBonus.employee).joinedload(Employee.department)
        )
        
        # Always exclude inactive employees from reports/lists
        query = query.filter(Employee.is_active == True)
        
        # Date filtering
        if date_from_str:
            date_from = parse_date_compact(date_from_str)
            if date_from:
                query = query.filter(PenaltyBonus.date >= date_from)
        if date_to_str:
            date_to = parse_date_compact(date_to_str)
            if date_to:
                query = query.filter(PenaltyBonus.date <= date_to)
                
        # Department filtering
        if dept_ids:
            if dept_filter_mode == 'exclude':
                query = query.filter(Employee.department_id.notin_(dept_ids))
            else:
                query = query.filter(Employee.department_id.in_(dept_ids))
                
        penalties = query.order_by(Employee.code.asc(), PenaltyBonus.date.asc()).all()
        departments = session.query(Department).all()
        
        # Calculate Statistics
        total_penalty_amount = 0
        total_penalty_days_value = 0
        
        for p in penalties:
            if p.type == 'Penalty':
                if p.days:
                    # If day_value is property it works, if not we might need to compute
                    # Assuming model has day_value property that uses relationship calculate_hourly_salary or similar
                    # If p.day_value is 0 but days > 0, it means it wasn't calculated dynamically in query
                    # Let's rely on model property if exists
                     total_penalty_days_value += p.day_value
                else:
                    total_penalty_amount += p.amount

        total_penalties = total_penalty_amount + total_penalty_days_value
        
        total_penalty_days = sum(p.days for p in penalties if p.type == 'Penalty' and p.days)
        total_bonuses = sum(p.amount for p in penalties if p.type == 'Bonus')

        return render_template('penalties/list.html', 
                             penalties=penalties,
                             departments=departments,
                             selected_department_ids=dept_ids,
                             dept_filter_mode=dept_filter_mode,
                             date_from=date_from_str,
                             date_to=date_to_str,
                             total_penalties=total_penalties,
                             total_penalty_days=total_penalty_days,
                             total_bonuses=total_bonuses)
    finally:
        session.close()

@penalties_bp.route('/create', methods=['GET', 'POST'])
def create():
    """Create new penalty"""
    form = PenaltyForm()
    db = current_app.db
    
    form.employee_id.choices = employee_choices(db)
    
    if form.validate_on_submit():
        try:
            # `form.date.data` is a datetime.date if validator passed; use it directly
            penalty_date = form.date.data if form.date.data else None
            db.add_penalty(
                employee_id=form.employee_id.data,
                penalty_type=form.penalty_type.data,
                amount=form.amount.data,
                reason=form.reason.data,
                date=penalty_date
            )
            flash('تم إضافة الجزاء بنجاح', 'center')
            return redirect(url_for('penalties.list'))
        except Exception as e:
            flash(f'حدث خطأ: {str(e)}', 'danger')
    
    today = datetime.now().date()
    # If rendering form initially, set default date data to today so WTForms shows it
    if request.method == 'GET' and not form.date.data:
        form.date.data = today
    return render_template('penalties/form.html', form=form, mode='create', today=format_date_ar(today))

@penalties_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    """Edit existing penalty"""
    db = current_app.db
    form = PenaltyForm()
    
    # Get employees for dropdown
    form.employee_id.choices = employee_choices(db, active_only=False)
    
    session = db.get_session()
    from database_models import PenaltyBonus
    penalty = session.query(PenaltyBonus).get(id)
    
    if not penalty:
        flash('الجزاء غير موجود', 'danger')
        return redirect(url_for('penalties.list'))
        
    if request.method == 'GET':
        # Populate form
        form.employee_id.data = penalty.employee_id
        form.penalty_type.data = penalty.type
        form.amount.data = penalty.amount
        form.date.data = penalty.date
        form.reason.data = penalty.reason
        
        if penalty.days:
             form.days.data = penalty.days
        
    if form.validate_on_submit():
        try:
            penalty.employee_id = form.employee_id.data
            penalty.type = form.penalty_type.data
            penalty.amount = form.amount.data
            penalty.days = form.days.data
            penalty.date = form.date.data
            penalty.reason = form.reason.data
            
            session.commit()
            flash('تم تعديل الجزاء بنجاح', 'center')
            return redirect(url_for('penalties.list'))
        except Exception as e:
            session.rollback()
            flash(f'حدث خطأ: {str(e)}', 'danger')
            
    return render_template('penalties/form.html', form=form, mode='edit', penalty=penalty)

@penalties_bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    """Delete penalty"""
    db = current_app.db
    
    try:
        db.delete_penalty(id)
        flash('تم حذف الجزاء بنجاح', 'center')
    except Exception as e:
        flash(f'حدث خطأ: {str(e)}', 'danger')
    
    return redirect(url_for('penalties.list'))

@penalties_bp.route('/bulk', methods=['GET'])
def bulk():
    """Bulk entry page for penalties and bonuses"""
    db = current_app.db
    employees = [e for e in db.get_all_employees() if e.is_active]
    
    from utils.helpers import format_date_ar
    from datetime import datetime
    today = format_date_ar(datetime.now().date())
    
    return render_template('penalties/bulk.html', 
                         employees=employees,
                         today=today)

@penalties_bp.route('/check_duplicate')
def check_duplicate():
    """Check if employee already has a penalty/bonus on a specific date"""
    db = current_app.db
    employee_id = request.args.get('employee_id', type=int)
    date_str = request.args.get('date')
    entry_type = request.args.get('type', 'Penalty')
    
    if not employee_id or not date_str:
        return {'exists': False}
        
    date_val = parse_date_compact(date_str)
    if not date_val:
        return {'exists': False}
        
    exists = db.check_penalty_bonus_exists(employee_id, date_val, entry_type)
    return {'exists': exists}

@penalties_bp.route('/bulk/save', methods=['POST'])
def bulk_save():
    """Save bulk entries for penalties and bonuses"""
    db = current_app.db
    session = db.get_session()
    
    try:
        from flask import jsonify
        from database_models import PenaltyBonus, Bonus
        from utils.helpers import parse_date_compact
        
        data = request.get_json()
        entries = data.get('entries', [])
        
        if not entries:
            return jsonify({'success': False, 'error': 'لا يوجد بيانات'}), 400
        
        saved_count = 0
        
        for entry in entries:
            employee_id = entry.get('employee_id')
            entry_type = entry.get('type')  # 'Penalty' or 'Bonus'
            date_str = entry.get('date')
            amount = entry.get('amount')
            paid_with_salary = entry.get('paid_with_salary', True)
            reason = entry.get('reason', '')
            
            # Parse date
            entry_date = parse_date_compact(date_str)
            if not entry_date:
                continue
            
            # Save to appropriate table based on type
            if entry_type == 'Penalty':
                # Save to PenaltyBonus table
                penalty = PenaltyBonus(
                    employee_id=employee_id,
                    type='Penalty',
                    date=entry_date,
                    amount=amount,
                    days=entry.get('days'),
                    reason=reason
                )
                session.add(penalty)
            
            elif entry_type == 'Bonus':
                # Save to Bonus table (new structure)
                bonus = Bonus(
                    employee_id=employee_id,
                    date_awarded=entry_date,
                    amount=amount,
                    reason=reason,
                    paid_with_salary=paid_with_salary
                )
                session.add(bonus)
            
            saved_count += 1
        
        session.commit()
        return jsonify({'success': True, 'saved': saved_count})
        
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@penalties_bp.route('/bulk_edit', methods=['GET'])
def bulk_edit():
    """Bulk edit penalties page"""
    db = current_app.db
    departments = db.get_departments()
    return render_template('penalties/bulk_edit.html', departments=departments)

@penalties_bp.route('/bulk_edit/load', methods=['GET'])
def bulk_edit_load():
    """Load penalties for bulk editing"""
    db = current_app.db
    session = db.get_session()
    
    try:
        from flask import jsonify
        from database_models import PenaltyBonus, Employee
        
        date_from_str = request.args.get('date_from')
        date_to_str = request.args.get('date_to')
        department_id = request.args.get('department_id', type=int)
        code = request.args.get('code')
        
        query = session.query(PenaltyBonus).join(Employee).filter(PenaltyBonus.type == 'Penalty', Employee.is_active == True)
        
        if date_from_str:
            date_from = parse_date_compact(date_from_str)
            if date_from:
                query = query.filter(PenaltyBonus.date >= date_from)
        
        if date_to_str:
            date_to = parse_date_compact(date_to_str)
            if date_to:
                query = query.filter(PenaltyBonus.date <= date_to)
        
        if department_id:
            query = query.filter(Employee.department_id == department_id)
            
        if code:
             query = query.filter(Employee.code.ilike(f"%{code}%"))
        
        penalties = query.order_by(Employee.code.asc(), PenaltyBonus.date.asc()).all()
        
        penalties_data = []
        for penalty in penalties:
            penalties_data.append({
                'id': penalty.id,
                'employee_id': penalty.employee_id,
                'employee_code': penalty.employee.code if penalty.employee else '',
                'employee_name': penalty.employee.name if penalty.employee else '',
                'amount': float(penalty.amount),
                'days': float(penalty.days) if penalty.days else 0,
                'date': format_date_ar(penalty.date) if penalty.date else '',
                'date_iso': penalty.date.strftime('%Y-%m-%d') if penalty.date else '',
                'reason': penalty.reason or ''
            })
        
        return jsonify({'success': True, 'penalties': penalties_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        session.close()

@penalties_bp.route('/bulk_edit/save', methods=['POST'])
def bulk_edit_save():
    """Save bulk edited penalties"""
    db = current_app.db
    session = db.get_session()
    
    try:
        from flask import jsonify
        from database_models import PenaltyBonus
        
        data = request.get_json()
        penalties = data.get('penalties', [])
        
        updated = 0
        errors = []
        
        for item in penalties:
            try:
                penalty_id = item.get('id')
                if not penalty_id:
                    continue
                
                penalty = session.query(PenaltyBonus).filter(PenaltyBonus.id == penalty_id).first()
                if not penalty:
                    continue
                
                date_str = item.get('date')
                date_val = None
                if date_str:
                    date_val = parse_date_compact(date_str)
                    if not date_val:
                        try:
                            date_val = datetime.strptime(date_str, '%Y-%m-%d').date()
                        except:
                            pass
                
                penalty.amount = float(item.get('amount', 0))
                penalty.days = float(item.get('days', 0))
                penalty.reason = item.get('reason', '')
                if date_val:
                    penalty.date = date_val
                
                session.add(penalty)
                updated += 1
            except Exception as e:
                errors.append(f"Error for Penalty ID {item.get('id')}: {str(e)}")
        
        session.commit()
        
        if errors:
            return jsonify({'success': False, 'message': '; '.join(errors[:5])})
        
        msg = f'تم تعديل {updated} جزاء بنجاح'
        flash(msg, 'center')
        return jsonify({'success': True, 'updated': updated, 'message': msg, 'center': True})
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        session.close()
