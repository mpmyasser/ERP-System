"""
Bonuses Routes
==============
Management of employee bonuses with tracking for salary deductions
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'core'))

from db_manager import DBManager
from app.forms import BonusForm
from utils.helpers import parse_date_compact, format_date_ar

bonuses_bp = Blueprint('bonuses', __name__)

@bonuses_bp.route('/')
def list():
    """List all bonuses with filters"""
    db = current_app.db
    session = db.get_session()
    
    try:
        from database_models import Bonus, Employee, Department
        from sqlalchemy.orm import joinedload
        
        # Get filters
        date_from_str = request.args.get('date_from')
        date_to_str = request.args.get('date_to')
        dept_ids = request.args.getlist('department_ids', type=int)
        dept_filter_mode = request.args.get('dept_filter_mode', 'include')
        
        query = session.query(Bonus).join(Employee).options(
            joinedload(Bonus.employee).joinedload(Employee.department)
        ).filter(Employee.is_active == True)
        
        # Date filtering
        if date_from_str:
            date_from = parse_date_compact(date_from_str)
            if date_from:
                query = query.filter(Bonus.date_awarded >= date_from)
        if date_to_str:
            date_to = parse_date_compact(date_to_str)
            if date_to:
                query = query.filter(Bonus.date_awarded <= date_to)
                
        # Department filtering
        if dept_ids:
            if dept_filter_mode == 'exclude':
                query = query.filter(Employee.department_id.notin_(dept_ids))
            else:
                query = query.filter(Employee.department_id.in_(dept_ids))
                
        bonuses = query.order_by(Employee.code.asc(), Bonus.date_awarded.asc()).all()
        departments = session.query(Department).all()
        
        # Calculate Statistics
        total_bonuses_amount = sum(b.amount for b in bonuses)
        
        return render_template('bonuses/list.html', 
                             bonuses=bonuses,
                             departments=departments,
                             selected_department_ids=dept_ids,
                             dept_filter_mode=dept_filter_mode,
                             date_from=date_from_str,
                             date_to=date_to_str,
                             total_bonuses_amount=total_bonuses_amount)
    finally:
        session.close()
def create():
    """Create new bonus"""
    form = BonusForm()
    db = current_app.db
    
    form.employee_id.choices = [(e.id, f"{e.name} ({e.code})") for e in db.get_all_employees() if e.is_active]
    
    if form.validate_on_submit():
        try:
            bonus_date = form.date_awarded.data if form.date_awarded.data else None
            db.add_bonus(
                employee_id=form.employee_id.data,
                amount=form.amount.data,
                reason=form.reason.data,
                date_awarded=bonus_date,
                paid_with_salary=form.paid_with_salary.data
            )
            flash('تم إضافة المكافأة بنجاح', 'center')
            return redirect(url_for('bonuses.list'))
        except Exception as e:
            flash(f'حدث خطأ: {str(e)}', 'danger')
    
    today = datetime.now().date()
    if request.method == 'GET' and not form.date_awarded.data:
        form.date_awarded.data = today
    return render_template('bonuses/form.html', form=form, mode='create', today=format_date_ar(today))

@bonuses_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    """Edit bonus"""
    db = current_app.db
    bonus = db.get_bonus_by_id(id)
    
    if not bonus:
        flash('المكافأة غير موجودة', 'danger')
        return redirect(url_for('bonuses.list'))
    
    form = BonusForm()
    form.employee_id.choices = [(e.id, f"{e.name} ({e.code})") for e in db.get_all_employees()]
    
    if form.validate_on_submit():
        try:
            bonus_date = form.date_awarded.data if form.date_awarded.data else None
            db.update_bonus(
                id,
                employee_id=form.employee_id.data,
                amount=form.amount.data,
                reason=form.reason.data,
                date_awarded=bonus_date,
                paid_with_salary=form.paid_with_salary.data
            )
            flash('تم تحديث المكافأة بنجاح', 'center')
            return redirect(url_for('bonuses.list'))
        except Exception as e:
            flash(f'حدث خطأ: {str(e)}', 'danger')
    
    elif request.method == 'GET':
        form.employee_id.data = bonus.employee_id
        form.amount.data = bonus.amount
        form.reason.data = bonus.reason
        form.date_awarded.data = bonus.date_awarded
        form.paid_with_salary.data = bonus.paid_with_salary
    
    today = format_date_ar(bonus.date_awarded) if bonus.date_awarded else datetime.now().date()
    return render_template('bonuses/form.html', form=form, mode='edit', bonus=bonus, today=today)

@bonuses_bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    """Delete bonus"""
    db = current_app.db
    
    try:
        db.delete_bonus(id)
        flash('تم حذف المكافأة بنجاح', 'center')
    except Exception as e:
        flash(f'حدث خطأ: {str(e)}', 'danger')
    
    return redirect(url_for('bonuses.list'))

@bonuses_bp.route('/employee/<int:employee_id>')
def employee_bonuses(employee_id):
    """List bonuses for a specific employee"""
    db = current_app.db
    employee = db.get_employee_by_id(employee_id)
    
    if not employee:
        flash('الموظف غير موجود', 'danger')
        return redirect(url_for('bonuses.list'))
    
    bonuses = db.get_employee_bonuses(employee_id)
    
    return render_template('bonuses/employee_list.html', employee=employee, bonuses=bonuses)

@bonuses_bp.route('/bulk', methods=['GET'])
def bulk():
    """Bulk entry page for bonuses"""
    db = current_app.db
    employees = [e for e in db.get_all_employees() if e.is_active]
    today = format_date_ar(datetime.now().date())
    return render_template('bonuses/bulk.html', employees=employees, today=today)

@bonuses_bp.route('/check_duplicate')
def check_duplicate():
    """Check if employee already has a bonus on a specific date"""
    db = current_app.db
    employee_id = request.args.get('employee_id', type=int)
    date_str = request.args.get('date')
    
    if not employee_id or not date_str:
        return {'exists': False}
        
    date_val = parse_date_compact(date_str)
    if not date_val:
        return {'exists': False}
        
    exists = db.check_bonus_exists(employee_id, date_val)
    return {'exists': exists}

@bonuses_bp.route('/bulk/save', methods=['POST'])
def bulk_save():
    """Save bulk bonuses"""
    db = current_app.db
    session = db.get_session()
    
    try:
        from flask import jsonify
        from database_models import Bonus
        from utils.helpers import parse_date_compact
        
        data = request.get_json()
        entries = data.get('entries', [])
        
        if not entries:
            return jsonify({'success': False, 'error': 'لا يوجد بيانات'}), 400
        
        saved_count = 0
        for entry in entries:
            date_awarded = parse_date_compact(entry.get('date_awarded'))
            if not date_awarded:
                continue
            
            bonus = Bonus(
                employee_id=entry.get('employee_id'),
                date_awarded=date_awarded,
                amount=entry.get('amount'),
                reason=entry.get('reason', ''),
                paid_with_salary=entry.get('paid_with_salary', True)
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

@bonuses_bp.route('/bulk_edit', methods=['GET'])
def bulk_edit():
    """Bulk edit bonuses page"""
    db = current_app.db
    departments = db.get_departments()
    return render_template('bonuses/bulk_edit.html', departments=departments)

@bonuses_bp.route('/bulk_edit/load', methods=['GET'])
def bulk_edit_load():
    """Load bonuses for bulk editing"""
    db = current_app.db
    session = db.get_session()
    
    try:
        from flask import jsonify
        from database_models import Bonus, Employee
        
        date_from_str = request.args.get('date_from')
        date_to_str = request.args.get('date_to')
        department_id = request.args.get('department_id', type=int)
        
        query = session.query(Bonus).join(Employee).filter(Employee.is_active == True)
        
        if date_from_str:
            date_from = parse_date_compact(date_from_str)
            if date_from:
                query = query.filter(Bonus.date_awarded >= date_from)
        
        if date_to_str:
            date_to = parse_date_compact(date_to_str)
            if date_to:
                query = query.filter(Bonus.date_awarded <= date_to)
        
        if department_id:
            query = query.filter(Employee.department_id == department_id)
        
        bonuses = query.order_by(Employee.code.asc(), Bonus.date_awarded.asc()).all()
        
        bonuses_data = []
        for bonus in bonuses:
            bonuses_data.append({
                'id': bonus.id,
                'employee_id': bonus.employee_id,
                'employee_code': bonus.employee.code if bonus.employee else '',
                'employee_name': bonus.employee.name if bonus.employee else '',
                'amount': float(bonus.amount),
                'date': format_date_ar(bonus.date_awarded) if bonus.date_awarded else '',
                'date_iso': bonus.date_awarded.strftime('%Y-%m-%d') if bonus.date_awarded else '',
                'reason': bonus.reason or '',
                'paid_with_salary': bonus.paid_with_salary
            })
        
        return jsonify({'success': True, 'bonuses': bonuses_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        session.close()

@bonuses_bp.route('/bulk_edit/save', methods=['POST'])
def bulk_edit_save():
    """Save bulk edited bonuses"""
    db = current_app.db
    session = db.get_session()
    
    try:
        from flask import jsonify
        from database_models import Bonus
        
        data = request.get_json()
        bonuses = data.get('bonuses', [])
        
        updated = 0
        errors = []
        
        for item in bonuses:
            try:
                bonus_id = item.get('id')
                if not bonus_id:
                    continue
                
                bonus = session.query(Bonus).filter(Bonus.id == bonus_id).first()
                if not bonus:
                    continue
                
                date_str = item.get('date')
                date_val = None
                if date_str:
                    date_val = parse_date_compact(date_str)
                    if not date_val:
                        try:
                            date_val = datetime.strptime(date_str, '%Y-%m-%d').date()
                        except (ValueError, TypeError):
                            pass
                
                bonus.amount = float(item['amount'])
                bonus.reason = item.get('reason', '')
                bonus.paid_with_salary = item.get('paid_with_salary', True)
                if date_val:
                    bonus.date_awarded = date_val
                
                session.add(bonus)
                updated += 1
            except Exception as e:
                errors.append(f"Error for Bonus ID {item.get('id')}: {str(e)}")
        
        session.commit()
        
        if errors:
            return jsonify({'success': False, 'message': '; '.join(errors[:5])})
        
        return jsonify({'success': True, 'updated': updated})
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        session.close()
