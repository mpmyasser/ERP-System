# -*- coding: utf-8 -*-
"""
Leaves Routes
=============
إدارة الإجازات
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
import sys
import os
from datetime import datetime, date

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'core'))

from database_models import Employee, Leave, LeaveBalance, LeaveTypeEnum, LeaveStatus, PublicHoliday
from services.leave_service import LeaveService
from utils.helpers import parse_date_compact

leaves_bp = Blueprint('leaves', __name__)

@leaves_bp.route('/')
def list():
    """قائمة الإجازات"""
    db = current_app.db
    session = db.get_session()
    
    # فلاتر
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    department_ids = request.args.getlist('department_ids', type=int)
    leave_type = request.args.get('leave_type')
    
    # الاستعلام الأساسي
    query = session.query(Leave).join(Employee)
    
    # تطبيق الفلاتر
    if date_from:
        parsed_date_from = parse_date_compact(date_from)
        if parsed_date_from:
            query = query.filter(Leave.start_date >= parsed_date_from)
    if date_to:
        parsed_date_to = parse_date_compact(date_to)
        if parsed_date_to:
            query = query.filter(Leave.end_date <= parsed_date_to)
    if department_ids:
        query = query.filter(Employee.department_id.in_(department_ids))
    if leave_type:
        query = query.filter(Leave.leave_type == leave_type)
    
    leaves = query.order_by(Leave.start_date.desc()).all()
    
    # الأقسام للفلتر
    departments = db.get_departments()
    
    # الإحصائيات
    total_days = sum(leave.days_count for leave in leaves)
    employees_count = len(set(leave.employee_id for leave in leaves))
    
    return render_template('leaves/list.html',
                         leaves=leaves,
                         departments=departments,
                         department_ids=department_ids,
                         leave_type=leave_type,
                         date_from=date_from,
                         date_to=date_to,
                         total_days=total_days,
                         employees_count=employees_count,
                         leave_types=LeaveTypeEnum)

@leaves_bp.route('/check_duplicate')
def check_duplicate():
    """Check if employee already has a leave on a specific date"""
    db = current_app.db
    employee_id = request.args.get('employee_id', type=int)
    date_str = request.args.get('date')
    
    if not employee_id or not date_str:
        return {'exists': False}
        
    date_val = parse_date_compact(date_str)
    if not date_val:
        # Try DD/MM/YYYY
        try:
            date_val = datetime.strptime(date_str, '%d/%m/%Y').date()
        except:
            return {'exists': False}
        
    exists = db.check_leave_exists(employee_id, date_val)
    return {'exists': exists}

@leaves_bp.route('/bulk', methods=['GET', 'POST'])
def bulk():
    """Bulk entry of leaves"""
    db = current_app.db
    from database_models import Employee, Leave, LeaveTypeEnum, LeaveStatus, LeaveBalance
    from datetime import date
    from flask import jsonify

    if request.method == 'POST':
        try:
            data = request.get_json()
            entries = data.get('entries', [])
            
            if not entries:
                return jsonify({'success': False, 'message': 'لا توجد بيانات'}), 400
            
            session = db.get_session()
            service = LeaveService(session)
            
            created_count = 0
            errors = []
            
            for idx, entry in enumerate(entries):
                try:
                    # التحقق من البيانات
                    employee_code = entry.get('employee_code', '').strip()
                    if not employee_code:
                        errors.append(f"الصف {idx+1}: كود الموظف مطلوب")
                        continue
                    
                    # البحث عن الموظف
                    employee = session.query(Employee).filter_by(code=employee_code).first()
                    if not employee:
                        errors.append(f"الصف {idx+1}: الموظف {employee_code} غير موجود")
                        continue
                    
                    # إنشاء الإجازة
                    leave = Leave(
                        employee_id=employee.id,
                        leave_type=entry.get('leave_type', LeaveTypeEnum.ANNUAL.value),
                        start_date=datetime.strptime(entry['start_date'], '%d/%m/%Y').date(),
                        end_date=datetime.strptime(entry['end_date'], '%d/%m/%Y').date(),
                        days_count=float(entry.get('days_count', 1)),
                        is_paid=entry.get('is_paid', True),
                        status=LeaveStatus.APPROVED.value,
                        reason=entry.get('reason', ''),
                        approved_date=date.today()
                    )
                    
                    # حساب الأيام إذا لم تُدخل
                    if not entry.get('days_count'):
                        leave.days_count = (leave.end_date - leave.start_date).days + 1
                    
                    # حفظ الإجازة
                    session.add(leave)
                    
                    # تحديث الرصيد
                    service.update_balance_after_leave(employee.id, leave)
                    
                    created_count += 1
                    
                except Exception as e:
                    errors.append(f"الصف {idx+1}: {str(e)}")
                    continue
            
            if created_count > 0:
                session.commit()
                message = f"تم إضافة {created_count} إجازة بنجاح"
                if errors:
                    message += f" | {len(errors)} أخطاء"
                return jsonify({'success': True, 'message': message, 'errors': errors})
            else:
                session.rollback()
                return jsonify({'success': False, 'message': 'فشل الحفظ', 'errors': errors}), 400
                
        except Exception as e:
            session.rollback()
            return jsonify({'success': False, 'message': f'خطأ: {str(e)}'}), 500
    
    # GET request
    employees = db.get_all_employees()
    today = date.today().strftime('%d/%m/%Y')
    
    return render_template('leaves/bulk.html',
                         employees=employees,
                         today=today,
                         leave_types=LeaveTypeEnum)

@leaves_bp.route('/balances')
def balances():
    """عرض أرصدة الإجازات"""
    db = current_app.db
    session = db.get_session()
    
    year = request.args.get('year', type=int, default=date.today().year)
    department_id = request.args.get('department_id', type=int)
    
    # الاستعلام
    query = session.query(LeaveBalance).join(Employee).filter(LeaveBalance.year == year)
    
    if department_id:
        query = query.filter(Employee.department_id == department_id)
    
    balances = query.all()
    
    # الأقسام
    departments = db.get_departments()
    
    return render_template('leaves/balances.html',
                         balances=balances,
                         departments=departments,
                         year=year,
                         department_id=department_id)

@leaves_bp.route('/initialize_balances/<int:year>')
def initialize_balances(year):
    """تهيئة أرصدة الإجازات لجميع الموظفين"""
    db = current_app.db
    session = db.get_session()
    service = LeaveService(session)
    
    try:
        count = service.initialize_all_balances(year)
        session.commit()
        flash(f'تم تهيئة أرصدة {count} موظف للسنة {year}', 'center')
    except Exception as e:
        session.rollback()
        flash(f'خطأ: {str(e)}', 'danger')
    
    return redirect(url_for('leaves.balances', year=year))

@leaves_bp.route('/delete/<int:leave_id>', methods=['POST'])
def delete(leave_id):
    """حذف إجازة"""
    db = current_app.db
    session = db.get_session()
    
    try:
        leave = session.query(Leave).filter_by(id=leave_id).first()
        if not leave:
            flash('الإجازة غير موجودة', 'danger')
            return redirect(url_for('leaves.list'))
        
        # استرجاع الرصيد
        service = LeaveService(session)
        service.restore_balance_after_delete(leave)
        
        session.delete(leave)
        session.commit()
        flash('تم حذف الإجازة بنجاح', 'center')
    except Exception as e:
        session.rollback()
        flash(f'خطأ: {str(e)}', 'danger')
    
    return redirect(url_for('leaves.list'))

@leaves_bp.route('/employee/<int:emp_id>')
def employee_leaves(emp_id):
    """إجازات موظف معين"""
    db = current_app.db
    session = db.get_session()
    
    employee = session.query(Employee).filter_by(id=emp_id).first()
    if not employee:
        flash('الموظف غير موجود', 'danger')
        return redirect(url_for('leaves.list'))
    
    year = request.args.get('year', type=int, default=date.today().year)
    
    # الإجازات
    leaves = session.query(Leave).filter(
        Leave.employee_id == emp_id,
        Leave.start_date >= date(year, 1, 1),
        Leave.start_date <= date(year, 12, 31)
    ).order_by(Leave.start_date.desc()).all()
    
    # الرصيد
    balance = session.query(LeaveBalance).filter_by(
        employee_id=emp_id,
        year=year
    ).first()
    
    return render_template('leaves/employee.html',
                         employee=employee,
                         leaves=leaves,
                         balance=balance,
                         year=year,
                         leave_types=LeaveTypeEnum)
@leaves_bp.route('/holidays', methods=['GET', 'POST'])
def holidays():
    """إدارة العطلات الرسمية"""
    db = current_app.db
    session = db.get_session()
    
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            start_date_str = request.form.get('start_date')
            end_date_str = request.form.get('end_date')
            
            if not name or not start_date_str or not end_date_str:
                flash('جميع الحقول مطلوبة', 'danger')
                return redirect(url_for('leaves.holidays'))
                
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            if end_date < start_date:
                flash('تاريخ النهاية يجب أن يكون بعد تاريخ البداية', 'danger')
                return redirect(url_for('leaves.holidays'))
                
            holiday = PublicHoliday(
                name=name,
                start_date=start_date,
                end_date=end_date
            )
            session.add(holiday)
            session.commit()
            flash('تم إضافة العطلة بنجاح', 'center')
            
        except Exception as e:
            session.rollback()
            flash(f'حدث خطأ: {str(e)}', 'danger')
            
        return redirect(url_for('leaves.holidays'))
        
    # GET request - with filtering
    query = session.query(PublicHoliday)
    
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    search_name = request.args.get('search_name')
    
    if date_from:
        try:
            query = query.filter(PublicHoliday.start_date >= datetime.strptime(date_from, '%d/%m/%Y').date())
        except ValueError:
            pass # Invalid date format, ignore
            
    if date_to:
        try:
            query = query.filter(PublicHoliday.end_date <= datetime.strptime(date_to, '%d/%m/%Y').date())
        except ValueError:
            pass # Invalid date format, ignore
            
    if search_name:
        query = query.filter(PublicHoliday.name.ilike(f"%{search_name}%"))
        
    holidays = query.order_by(PublicHoliday.start_date.desc()).all()
    return render_template('leaves/holidays.html', holidays=holidays)

@leaves_bp.route('/holidays/delete/<int:id>', methods=['POST'])
def delete_holiday(id):
    """حذف عطلة رسمية"""
    db = current_app.db
    session = db.get_session()
    try:
        holiday = session.query(PublicHoliday).get(id)
        if holiday:
            session.delete(holiday)
            session.commit()
            flash('تم حذف العطلة بنجاح', 'center')
        else:
            flash('العطلة غير موجودة', 'warning')
    except Exception as e:
        session.rollback()
        flash(f'حدث خطأ أثناء الحذف: {str(e)}', 'danger')
        
    return redirect(url_for('leaves.holidays'))

@leaves_bp.route('/holidays/edit/<int:id>', methods=['POST'])
def edit_holiday(id):
    """تعديل عطلة رسمية"""
    db = current_app.db
    session = db.get_session()
    try:
        holiday = session.query(PublicHoliday).get(id)
        if not holiday:
            flash('العطلة غير موجودة', 'warning')
            return redirect(url_for('leaves.holidays'))

        name = request.form.get('name')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')

        if not name or not start_date_str or not end_date_str:
            flash('جميع الحقول مطلوبة', 'danger')
            return redirect(url_for('leaves.holidays'))
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
        if end_date < start_date:
            flash('تاريخ النهاية يجب أن يكون بعد تاريخ البداية', 'danger')
            return redirect(url_for('leaves.holidays'))

        holiday.name = name
        holiday.start_date = start_date
        holiday.end_date = end_date
        
        session.commit()
        flash('تم تعديل العطلة بنجاح', 'center')
        
    except Exception as e:
        session.rollback()
        flash(f'حدث خطأ أثناء التعديل: {str(e)}', 'danger')
        
    return redirect(url_for('leaves.holidays'))
