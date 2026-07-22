"""
Permissions Routes
==================
Permissions management
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'core'))

from db_manager import DBManager
from app.forms import PermissionForm
from app.utils.form_helpers import employee_choices
from utils.helpers import parse_date_compact, format_date_ar

permissions_bp = Blueprint('permissions', __name__)

@permissions_bp.route('/')
def list():
    """List all permissions with filters"""
    db = current_app.db
    session = db.get_session()
    
    try:
        from database_models import Permission, Employee, Department
        from sqlalchemy.orm import joinedload
        
        # Get filters
        date_from_str = request.args.get('date_from')
        date_to_str = request.args.get('date_to')
        dept_ids = request.args.getlist('department_ids', type=int)
        dept_filter_mode = request.args.get('dept_filter_mode', 'include')
        
        query = session.query(Permission).join(Employee).options(
            joinedload(Permission.employee).joinedload(Employee.department)
        )
        
        # Date filtering
        if date_from_str:
            date_from = parse_date_compact(date_from_str)
            if date_from:
                query = query.filter(Permission.date >= date_from)
        if date_to_str:
            date_to = parse_date_compact(date_to_str)
            if date_to:
                query = query.filter(Permission.date <= date_to)
                
        # Department filtering
        if dept_ids:
            if dept_filter_mode == 'exclude':
                query = query.filter(Employee.department_id.notin_(dept_ids))
            else:
                query = query.filter(Employee.department_id.in_(dept_ids))
                
        permissions = query.order_by(Employee.code.asc(), Permission.date.asc(), Permission.id.asc()).all()
        departments = session.query(Department).all()
        
        # Calculate Statistics
        total_paid = sum(1 for p in permissions if p.is_paid)
        total_unpaid = sum(1 for p in permissions if not p.is_paid)
        total_material_value = sum(p.material_value for p in permissions)
        
        return render_template('permissions/list.html', 
                             permissions=permissions,
                             departments=departments,
                             selected_department_ids=dept_ids,
                             dept_filter_mode=dept_filter_mode,
                             date_from=date_from_str,
                             date_to=date_to_str,
                             total_paid=total_paid,
                             total_unpaid=total_unpaid,
                             total_material_value=total_material_value)
    finally:
        session.close()

@permissions_bp.route('/create', methods=['GET', 'POST'])
def create():
    """Create new permission"""
    form = PermissionForm()
    db = current_app.db
    
    form.employee_id.choices = employee_choices(db)
    
    if form.validate_on_submit():
        try:
            permission_date = form.date.data if form.date.data else None
            db.add_permission(
                employee_id=form.employee_id.data,
                date=permission_date,
                from_time=form.from_time.data,
                to_time=form.to_time.data,
                reason=form.reason.data,
                is_paid=form.is_paid.data
            )
            flash('تم إضافة التصريح بنجاح', 'center')
            return redirect(url_for('permissions.list'))
        except Exception as e:
            flash(f'حدث خطأ: {str(e)}', 'danger')
    
    today = datetime.now().date()
    if request.method == 'GET' and not form.date.data:
        form.date.data = today
    return render_template('permissions/form.html', form=form, mode='create', today=format_date_ar(today))

@permissions_bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    """Delete permission"""
    db = current_app.db
    
    try:
        db.delete_permission(id)
        flash('تم حذف التصريح بنجاح', 'center')
    except Exception as e:
        flash(f'حدث خطأ: {str(e)}', 'danger')
    
    return redirect(url_for('permissions.list'))

@permissions_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    """Edit permission"""
    db = current_app.db
    permission = db.get_permission_by_id(id)
    
    if not permission:
        flash('التصريح غير موجود', 'danger')
        return redirect(url_for('permissions.list'))
    
    form = PermissionForm(obj=permission)
    form.employee_id.choices = employee_choices(db, extra_ids=[permission.employee_id])
    
    if form.validate_on_submit():
        try:
            db.update_permission(
                permission_id=id,
                employee_id=form.employee_id.data,
                date=form.date.data,
                from_time=form.from_time.data,
                to_time=form.to_time.data,
                reason=form.reason.data,
                is_paid=form.is_paid.data
            )
            flash('تم تحديث التصريح بنجاح', 'center')
            return redirect(url_for('permissions.list'))
        except Exception as e:
            flash(f'حدث خطأ: {str(e)}', 'danger')
    
    if request.method == 'GET':
        form.employee_id.data = permission.employee_id
        form.date.data = permission.date
        form.from_time.data = permission.from_time
        form.to_time.data = permission.to_time
        form.reason.data = permission.reason
        form.is_paid.data = permission.is_paid
        
    return render_template('permissions/form.html', form=form, mode='edit', permission=permission)

@permissions_bp.route('/bulk', methods=['GET'])
def bulk():
    """Bulk entry for permissions"""
    db = current_app.db
    employees = [ e for e in db.get_all_employees() if e.is_active]
    today = format_date_ar(datetime.now().date())
    return render_template('permissions/bulk.html', employees=employees, today=today)

@permissions_bp.route('/check_duplicate')
def check_duplicate():
    """Check if employee already has a permission on a specific date"""
    db = current_app.db
    employee_id = request.args.get('employee_id', type=int)
    date_str = request.args.get('date')
    
    if not employee_id or not date_str:
        return {'exists': False}
        
    date_val = parse_date_compact(date_str)
    if not date_val:
        return {'exists': False}
        
    exists = db.check_permission_exists(employee_id, date_val)
    return {'exists': exists}

@permissions_bp.route('/bulk/save', methods=['POST'])
def bulk_save():
    """Save bulk permissions"""
    db = current_app.db
    session = db.get_session()
    
    try:
        from flask import jsonify
        from database_models import Permission
        from datetime import time as time_type
        
        data = request.get_json()
        entries = data.get('entries', [])
        
        if not entries:
            return jsonify({'success': False, 'error': 'لا يوجد بيانات'}), 400
        
        saved_count = 0
        for entry in entries:
            date_obj = parse_date_compact(entry.get('date'))
            if not date_obj:
                continue
            
            from_time_str = entry.get('from_time')
            to_time_str = entry.get('to_time')
            from_h, from_m = map(int, from_time_str.split(':'))
            to_h, to_m = map(int, to_time_str.split(':'))
            
            perm = Permission(
                employee_id=entry.get('employee_id'),
                date=date_obj,
                from_time=time_type(from_h, from_m),
                to_time=time_type(to_h, to_m),
                is_paid=entry.get('is_paid', False),
                reason=entry.get('reason', '')
            )
            session.add(perm)
            saved_count += 1
        
        session.commit()
        return jsonify({'success': True, 'saved': saved_count})
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        session.close()

@permissions_bp.route('/bulk_edit', methods=['GET'])
def bulk_edit():
    """Bulk edit permissions page"""
    db = current_app.db
    departments = db.get_departments()
    return render_template('permissions/bulk_edit.html', departments=departments)

@permissions_bp.route('/bulk_edit/load', methods=['GET'])
def bulk_edit_load():
    """Load permissions for bulk editing"""
    db = current_app.db
    session = db.get_session()
    
    try:
        from flask import jsonify
        from database_models import Permission, Employee
        
        date_from_str = request.args.get('date_from')
        date_to_str = request.args.get('date_to')
        department_id = request.args.get('department_id', type=int)
        
        query = session.query(Permission).join(Employee)
        
        if date_from_str:
            date_from = parse_date_compact(date_from_str)
            if date_from:
                query = query.filter(Permission.date >= date_from)
        
        if date_to_str:
            date_to = parse_date_compact(date_to_str)
            if date_to:
                query = query.filter(Permission.date <= date_to)
        
        if department_id:
            query = query.filter(Employee.department_id == department_id)
        
        permissions = query.order_by(Employee.code.asc(), Permission.date.asc(), Permission.id.asc()).all()
        
        permissions_data = []
        for perm in permissions:
            permissions_data.append({
                'id': perm.id,
                'employee_id': perm.employee_id,
                'employee_code': perm.employee.code if perm.employee else '',
                'employee_name': perm.employee.name if perm.employee else '',
                'date': format_date_ar(perm.date) if perm.date else '',
                'date_iso': perm.date.strftime('%Y-%m-%d') if perm.date else '',
                'from_time': perm.from_time.strftime('%H:%M') if perm.from_time else '',
                'to_time': perm.to_time.strftime('%H:%M') if perm.to_time else '',
                'reason': perm.reason or '',
                'is_paid': perm.is_paid
            })
        
        return jsonify({'success': True, 'permissions': permissions_data})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        session.close()

@permissions_bp.route('/bulk_edit/save', methods=['POST'])
def bulk_edit_save():
    """Save bulk edited permissions"""
    db = current_app.db
    session = db.get_session()
    
    try:
        from flask import jsonify
        from database_models import Permission
        from datetime import time as time_type
        
        data = request.get_json()
        permissions = data.get('permissions', [])
        
        updated = 0
        errors = []
        
        for item in permissions:
            try:
                perm_id = item.get('id')
                if not perm_id:
                    continue
                
                perm = session.query(Permission).filter(Permission.id == perm_id).first()
                if not perm:
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
                
                # Parse times
                from_time_str = item.get('from_time', '00:00')
                to_time_str = item.get('to_time', '00:00')
                from_h, from_m = map(int, from_time_str.split(':'))
                to_h, to_m = map(int, to_time_str.split(':'))
                
                perm.reason = item.get('reason', '')
                perm.is_paid = item.get('is_paid', False)
                perm.from_time = time_type(from_h, from_m)
                perm.to_time = time_type(to_h, to_m)
                if date_val:
                    perm.date = date_val
                
                session.add(perm)
                updated += 1
            except Exception as e:
                errors.append(f"Error for Permission ID {item.get('id')}: {str(e)}")
        
        session.commit()
        
        if errors:
            return jsonify({'success': False, 'message': '; '.join(errors[:5])})
        
        msg = f'تم تعديل {updated} تصريح بنجاح'
        flash(msg, 'center')
        return jsonify({'success': True, 'updated': updated, 'message': msg, 'center': True})
    except Exception as e:
        session.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        session.close()
