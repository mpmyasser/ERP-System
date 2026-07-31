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
_list_type = list


def _parse_leave_date(value):
    """Parse leave date from DD/MM/YYYY or YYYY-MM-DD formats."""
    if value is None:
        return None

    date_str = str(value).strip()
    if not date_str:
        return None

    parsed = parse_date_compact(date_str)
    if parsed:
        return parsed

    for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    raise ValueError(f"تنسيق تاريخ غير صالح: {date_str}")


def _recalculate_leave_balance_for_employee_year(session, employee_id: int, year: int) -> None:
    """
    Recalculate leave balance usage for one employee/year based on APPROVED leaves.
    This keeps balances consistent after bulk edits.
    """
    if not employee_id or not year:
        return

    service = LeaveService(session)
    balance = session.query(LeaveBalance).filter_by(
        employee_id=employee_id,
        year=year
    ).first()

    if not balance:
        balance = service.initialize_employee_balance(employee_id, year)

    balance.annual_used = 0.0
    balance.sick_used = 0.0
    balance.casual_used = 0.0
    balance.emergency_used = 0.0

    approved_leaves = session.query(Leave).filter(
        Leave.employee_id == employee_id,
        Leave.start_date >= date(year, 1, 1),
        Leave.start_date <= date(year, 12, 31),
        Leave.status == LeaveStatus.APPROVED.value
    ).all()

    for leave in approved_leaves:
        if leave.leave_type == LeaveTypeEnum.ANNUAL.value:
            balance.annual_used += float(leave.days_count or 0)
        elif leave.leave_type == LeaveTypeEnum.SICK.value:
            balance.sick_used += float(leave.days_count or 0)
        elif leave.leave_type == LeaveTypeEnum.CASUAL.value:
            balance.casual_used += float(leave.days_count or 0)
        elif leave.leave_type == LeaveTypeEnum.EMERGENCY.value:
            balance.emergency_used += float(leave.days_count or 0)

    session.flush()

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
    
    leaves = query.order_by(Employee.code.asc(), Leave.start_date.asc()).all()
    
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
    from database_models import Employee, Leave, LeaveTypeEnum, LeaveStatus
    from datetime import date
    if request.method == 'POST':
        session = None
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
                    
                    leave_type = entry.get('leave_type', LeaveTypeEnum.ANNUAL.value)
                    raw_is_paid = entry.get('is_paid', None)
                    if raw_is_paid is None:
                        is_paid = (leave_type != LeaveTypeEnum.UNPAID.value)
                    elif isinstance(raw_is_paid, str):
                        is_paid = raw_is_paid.strip().lower() in ('1', 'true', 'yes', 'on')
                    else:
                        is_paid = bool(raw_is_paid)
                    if leave_type == LeaveTypeEnum.UNPAID.value:
                        is_paid = False

                    # إنشاء الإجازة
                    leave = Leave(
                        employee_id=employee.id,
                        leave_type=leave_type,
                        start_date=datetime.strptime(entry['start_date'], '%d/%m/%Y').date(),
                        end_date=datetime.strptime(entry['end_date'], '%d/%m/%Y').date(),
                        days_count=float(entry.get('days_count', 1)),
                        is_paid=is_paid,
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
                if session:
                    session.rollback()
                return jsonify({'success': False, 'message': 'فشل الحفظ', 'errors': errors}), 400
                
        except Exception as e:
            if session:
                session.rollback()
            return jsonify({'success': False, 'message': f'خطأ: {str(e)}'}), 500
    
    # GET request
    employees = db.get_all_employees()
    today = date.today().strftime('%d/%m/%Y')
    
    return render_template('leaves/bulk.html',
                         employees=employees,
                         today=today,
                         leave_types=LeaveTypeEnum)


@leaves_bp.route('/bulk_edit', methods=['GET'])
def bulk_edit():
    """Bulk edit leaves page (UI pattern aligned with advances)."""
    db = current_app.db
    departments = db.get_departments()
    preselected_leave_id = request.args.get('leave_id', type=int)
    return render_template(
        'leaves/bulk_edit.html',
        departments=departments,
        leave_types=LeaveTypeEnum,
        leave_statuses=LeaveStatus,
        preselected_leave_id=preselected_leave_id
    )


@leaves_bp.route('/bulk_edit/load', methods=['GET'])
def bulk_edit_load():
    """Load leaves for bulk editing."""
    db = current_app.db
    session = db.get_session()

    try:
        date_from_str = request.args.get('date_from')
        date_to_str = request.args.get('date_to')
        department_id = request.args.get('department_id', type=int)
        code = (request.args.get('code') or '').strip()
        leave_id = request.args.get('leave_id', type=int)

        query = session.query(Leave).join(Employee).filter(Employee.is_active == True)

        if leave_id:
            query = query.filter(Leave.id == leave_id)

        if date_from_str:
            parsed_from = _parse_leave_date(date_from_str)
            query = query.filter(Leave.start_date >= parsed_from)

        if date_to_str:
            parsed_to = _parse_leave_date(date_to_str)
            query = query.filter(Leave.end_date <= parsed_to)

        if department_id:
            query = query.filter(Employee.department_id == department_id)

        if code:
            query = query.filter(Employee.code.ilike(f"%{code}%"))

        leaves = query.order_by(Employee.code.asc(), Leave.start_date.asc()).all()

        leaves_data = []
        for leave in leaves:
            leaves_data.append({
                'id': leave.id,
                'employee_id': leave.employee_id,
                'employee_code': leave.employee.code if leave.employee else '',
                'employee_name': leave.employee.name if leave.employee else '',
                'leave_type': leave.leave_type or '',
                'start_date': leave.start_date.strftime('%d/%m/%Y') if leave.start_date else '',
                'end_date': leave.end_date.strftime('%d/%m/%Y') if leave.end_date else '',
                'status': leave.status or '',
                'days_count': float(leave.days_count or 0),
                'department': leave.employee.department.name if leave.employee and leave.employee.department else ''
            })

        return jsonify({'success': True, 'leaves': leaves_data})
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        current_app.logger.exception('Leave bulk edit load failed')
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        session.close()

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
@leaves_bp.route('/<int:leave_id>/delete', methods=['POST'])
def delete(leave_id):
    """Delete leave record."""
    db = current_app.db
    session = db.get_session()
    is_ajax = request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    try:
        leave = session.query(Leave).filter_by(id=leave_id).first()
        if not leave:
            if is_ajax:
                return jsonify({'success': False, 'message': 'الإجازة غير موجودة'}), 404
            flash('الإجازة غير موجودة', 'danger')
            return redirect(url_for('leaves.list'))

        service = LeaveService(session)
        service.restore_balance_after_delete(leave)

        session.delete(leave)
        session.commit()

        if is_ajax:
            return jsonify({'success': True, 'message': 'تم حذف الإجازة بنجاح'})

        flash('تم حذف الإجازة بنجاح', 'center')
    except Exception as e:
        session.rollback()
        current_app.logger.exception("Leave delete failed for leave_id=%s", leave_id)
        if is_ajax:
            return jsonify({'success': False, 'message': f'فشل حذف الإجازة: {str(e)}'}), 500
        flash(f'خطأ: {str(e)}', 'danger')
    finally:
        session.close()

    return redirect(url_for('leaves.list'))


@leaves_bp.route('/<int:leave_id>/edit', methods=['GET'])
def edit_leave(leave_id):
    """Redirect single-record edit to bulk edit page pattern."""
    return redirect(url_for('leaves.bulk_edit', leave_id=leave_id))

@leaves_bp.route('/bulk_edit/save', methods=['POST'])
def bulk_edit_save():
    """Bulk update selected leaves row-by-row in one transaction."""
    db = current_app.db
    session = db.get_session()

    try:
        data = request.get_json(silent=True) or {}
        rows = data.get('rows', [])

        if not isinstance(rows, _list_type) or not rows:
            return jsonify({'success': False, 'message': 'يجب اختيار إجازة واحدة على الأقل'}), 400

        valid_leave_types = {lt.value for lt in LeaveTypeEnum}
        valid_statuses = {st.value for st in LeaveStatus}

        row_updates = {}
        leave_ids = []

        for index, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                return jsonify({'success': False, 'message': f'الصف {index}: تنسيق البيانات غير صالح'}), 400

            raw_id = row.get('id')
            if raw_id is None or not str(raw_id).strip().isdigit():
                return jsonify({'success': False, 'message': f'الصف {index}: معرف الإجازة غير صالح'}), 400

            leave_id = int(raw_id)
            if leave_id in row_updates:
                return jsonify({'success': False, 'message': f'تكرار نفس الإجازة في الطلب (ID: {leave_id})'}), 400

            leave_type = (row.get('type') or '').strip()
            start_raw = row.get('start')
            end_raw = row.get('end')
            status = (row.get('status') or '').strip()

            if not leave_type or leave_type not in valid_leave_types:
                return jsonify({'success': False, 'message': f'الصف {index}: نوع الإجازة غير صالح'}), 400

            if not status or status not in valid_statuses:
                return jsonify({'success': False, 'message': f'الصف {index}: حالة الإجازة غير صالحة'}), 400

            try:
                parsed_start = _parse_leave_date(start_raw)
                parsed_end = _parse_leave_date(end_raw)
            except ValueError as ve:
                return jsonify({'success': False, 'message': f'الصف {index}: {str(ve)}'}), 400

            if parsed_start is None or parsed_end is None:
                return jsonify({'success': False, 'message': f'الصف {index}: تاريخ البداية والنهاية مطلوبان وتنسيقهما يجب أن يكون صالحاً'}), 400

            if parsed_end < parsed_start:
                return jsonify({
                    'success': False,
                    'message': f'الصف {index}: تاريخ النهاية يجب أن يكون بعد تاريخ البداية'
                }), 400

            row_updates[leave_id] = {
                'leave_type': leave_type,
                'start_date': parsed_start,
                'end_date': parsed_end,
                'status': status
            }
            leave_ids.append(leave_id)

        leaves = session.query(Leave).filter(Leave.id.in_(leave_ids)).all()
        found_ids = {lv.id for lv in leaves}
        missing = sorted(set(leave_ids) - found_ids)
        if missing:
            return jsonify({'success': False, 'message': f'بعض الإجازات غير موجودة: {missing}'}), 404

        affected_balances = set()
        updated_count = 0

        for leave in leaves:
            old_year = leave.start_date.year if leave.start_date else None
            affected_balances.add((leave.employee_id, old_year))

            row_data = row_updates[leave.id]
            leave.leave_type = row_data['leave_type']
            leave.start_date = row_data['start_date']
            leave.end_date = row_data['end_date']
            leave.status = row_data['status']
            if leave.leave_type == LeaveTypeEnum.UNPAID.value:
                leave.is_paid = False
            leave.days_count = float((leave.end_date - leave.start_date).days + 1)

            new_year = leave.start_date.year if leave.start_date else None
            affected_balances.add((leave.employee_id, new_year))
            updated_count += 1

        for employee_id, year in affected_balances:
            if employee_id and year:
                _recalculate_leave_balance_for_employee_year(session, employee_id, year)

        session.commit()
        msg = f'تم تعديل {updated_count} إجازة بنجاح'
        flash(msg, 'center')
        return jsonify({'success': True, 'updated': updated_count, 'message': msg, 'center': True})
    except ValueError as e:
        session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        session.rollback()
        current_app.logger.exception('Leave bulk edit failed')
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        session.close()

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
    ).order_by(Leave.start_date.asc()).all()
    
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
                
            is_unpaid = request.form.get('is_unpaid_for_uninsured') == 'on'
            
            holiday = PublicHoliday(
                name=name,
                start_date=start_date,
                end_date=end_date,
                is_unpaid_for_uninsured=is_unpaid
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

        is_unpaid = request.form.get('is_unpaid_for_uninsured') == 'on'

        holiday.name = name
        holiday.start_date = start_date
        holiday.end_date = end_date
        holiday.is_unpaid_for_uninsured = is_unpaid
        
        session.commit()
        flash('تم تعديل العطلة بنجاح', 'center')
        
    except Exception as e:
        session.rollback()
        flash(f'حدث خطأ أثناء التعديل: {str(e)}', 'danger')
        
    return redirect(url_for('leaves.holidays'))

