"""
Attendance Routes
=================
Attendance management and import
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
import sys
import os
from datetime import datetime, date
from calendar import monthrange
from werkzeug.utils import secure_filename
from utils.helpers import parse_date_compact
from sqlalchemy.orm import joinedload

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'core'))

from database_models import DailyRecord, Employee
from app.forms import AttendanceImportForm

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')

attendance_bp = Blueprint('attendance', __name__)


def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _daily_redirect_query_from_form(form):
    month = _to_int(form.get('month'))
    year = _to_int(form.get('year'))
    page = _to_int(form.get('page'))
    dept = (form.get('dept') or '').strip()
    date_from = (form.get('date_from') or '').strip()
    date_to = (form.get('date_to') or '').strip()

    params = {}
    if month and 1 <= month <= 12:
        params['month'] = month
    if year and 1900 <= year <= 2100:
        params['year'] = year
    if page and page > 1:
        params['page'] = page
    if dept:
        params['dept'] = dept
    if date_from:
        params['date_from'] = date_from
    if date_to:
        params['date_to'] = date_to
    return params


def _redirect_daily_with_context():
    return redirect(url_for('attendance.daily', **_daily_redirect_query_from_form(request.form)))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@attendance_bp.route('/')
def daily():
    """Daily attendance view"""
    db = current_app.db
    session = db.get_session()
    
    try:
        # Handle Date Range
        d_from = request.args.get('date_from')
        d_to = request.args.get('date_to')
        current_page = request.args.get('page', type=int) or 1
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)
        if current_page < 1:
            current_page = 1
        
        # Fallback to single 'date' param for backward compatibility
        d_legacy = request.args.get('date')
        
        if d_from:
            start_date = parse_date_compact(d_from)
        elif month and year and 1 <= month <= 12:
            start_date = date(year, month, 1)
        elif d_legacy:
            start_date = parse_date_compact(d_legacy)
        else:
            start_date = date.today()
        
        if not start_date:
            start_date = date.today()
            
        if d_to:
            end_date = parse_date_compact(d_to)
        elif month and year and 1 <= month <= 12:
            end_date = date(year, month, monthrange(year, month)[1])
        else:
            end_date = start_date
        
        if not end_date:
            end_date = start_date
            
        if end_date < start_date:
            end_date = start_date
        
        # Get filters
        dept_ids = request.args.getlist('department_ids', type=int)
        if not dept_ids:
            dept_csv = (request.args.get('dept') or '').strip()
            if dept_csv:
                dept_ids = [int(x) for x in dept_csv.split(',') if x.strip().isdigit()]
        dept_filter_mode = request.args.get('dept_filter_mode', 'include')
        search = (request.args.get('search') or '').strip()
        selected_dept_csv = ",".join(str(d) for d in dept_ids)
        
        # Query with explicit eager loading
        query = session.query(DailyRecord)\
            .join(Employee)\
            .filter(DailyRecord.date >= start_date)\
            .filter(DailyRecord.date <= end_date)\
            .order_by(Employee.code.asc(), DailyRecord.date.asc())\
            .options(joinedload(DailyRecord.employee))
        
        # Apply Department Filter
        if dept_ids:
            if dept_filter_mode == 'exclude':
                query = query.filter(Employee.department_id.notin_(dept_ids))
            else:
                query = query.filter(Employee.department_id.in_(dept_ids))

        # Apply search filter if provided (match code or name)
        if search:
            from sqlalchemy import or_
            query = query.filter(or_(Employee.code.ilike(f"%{search}%"), Employee.name.ilike(f"%{search}%")))
                
        attendance_records = query.all()
        
        all_employees = session.query(Employee)\
            .options(joinedload(Employee.department))\
            .all()
        
        # Get departments for filter
        from database_models import Department
        all_departments = session.query(Department).all()
        
        # Query permissions for this date range
        from database_models import Permission
        permissions = session.query(Permission).filter(Permission.date >= start_date, Permission.date <= end_date).all()
        permissions_map = {p.employee_id: p for p in permissions} 
        
        from datetime import timedelta
        
        # Render template while session is still open
        result = render_template('attendance/daily.html', 
                               records=attendance_records,
                               employees=all_employees,
                               departments=all_departments,
                               selected_department_ids=dept_ids,
                               dept_filter_mode=dept_filter_mode,
                               permissions_map=permissions_map,
                               date=start_date, # For compatibility
                               start_date=start_date,
                               end_date=end_date,
                               date_from_value=d_from or start_date.strftime('%d/%m/%Y'),
                               date_to_value=d_to or end_date.strftime('%d/%m/%Y'),
                               current_page_value=current_page,
                               month=start_date.month,
                               year=start_date.year,
                               selected_dept_csv=selected_dept_csv,
                               timedelta=timedelta)
        return result
    finally:
        session.close()

@attendance_bp.route('/import', methods=['GET', 'POST'])
def import_attendance():
    """Import attendance from file"""
    form = AttendanceImportForm()
    
    if form.validate_on_submit():
        file = form.file.data
        
        if not allowed_file(file.filename):
            flash('نوع الملف غير مدعوم. استخدم ملفات Excel فقط (.xls, .xlsx)', 'danger')
            return redirect(url_for('attendance.import_attendance'))
        
        try:
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            # Read Excel file with proper encoding handling
            # Now using generic core import
            from core.import_attendance import import_attendance_from_file
            
            # The core function handles reading, cleaning, and DB operations
            result = import_attendance_from_file(filepath)
            
            # Clean up uploaded file
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception as e:
                    pass  # Ignore cleanup errors
            
            success_count = result.get('success', 0)
            errors = result.get('errors', [])
            affected_dates = result.get('dates', [])
            
            if success_count > 0:
                flash(f'تم استيراد {success_count} سجل بصمة بنجاح!', 'center')
                
                # Auto-process logic (Process affected dates)
                try:
                    if affected_dates:
                        db = current_app.db # Get db instance
                        count_processed = 0
                        for d in affected_dates:
                            # d is datetime.date object from the script
                            db.process_attendance_for_date(d, source='system')
                            count_processed += 1
                        
                        flash(f'تمت معالجة الحضور لـ {count_processed} يوم/أيام تلقائيًا.', 'info')
                except Exception as e:
                    print(f"Error triggering processing: {e}")
                    flash(f'حدث خطأ أثناء معالجة البيانات: {e}', 'warning')
                    
            if errors:
                flash(f'تم العثور على {len(errors)} أخطاء. عرض أول 5:', 'warning')
                for err in errors[:5]:
                    flash(str(err), 'danger')
            elif success_count == 0:
                 flash('لم يتم استيراد أي سجلات. تأكد من صحة أسماء الأعمدة (Code, Date, In, Out)', 'warning')
                 
            return redirect(url_for('attendance.import_attendance'))
            
        except Exception as e:
            flash(f'خطأ غير متوقع: {str(e)}', 'danger')
            return redirect(url_for('attendance.import_attendance'))
    
    return render_template('attendance/import.html', form=form)

@attendance_bp.route('/employee/<int:emp_id>')
def employee_attendance(emp_id):
    """View employee attendance history"""
    db = current_app.db
    employee = db.get_employee_by_id(emp_id)
    
    if not employee:
        flash('الموظف غير موجود', 'danger')
        return redirect(url_for('attendance.daily'))
    
    # Get attendance records
    records = db.get_employee_attendance(emp_id)
    
    return render_template('attendance/view.html',
                         employee=employee,
                         records=records)

@attendance_bp.route('/clear', methods=['POST'])
def clear_attendance():
    """Clear all attendance records for a specific date or all time"""
    db = current_app.db
    date_str = request.form.get('date')
    
    try:
        if date_str:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            db.clear_attendance_records(target_date)
            flash(f'تم حذف سجلات الحضور ليوم {date_str}', 'success')
            
        return _redirect_daily_with_context()
    except Exception as e:
        flash(f'حدث خطأ أثناء الحذف: {str(e)}', 'danger')
        return _redirect_daily_with_context()

@attendance_bp.route('/reprocess', methods=['POST'])
def reprocess_attendance():
    """Reprocess raw logs into daily records"""
    db = current_app.db
    date_str = request.form.get('date')

    if not date_str:
        flash('التاريخ مطلوب لإعادة المعالجة', 'danger')
        return _redirect_daily_with_context()

    session = db.get_session()
    try:
        from core.services.attendance_service import AttendanceService
        from collections import defaultdict

        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        service = AttendanceService(session)

        logs = db.get_logs_by_date(target_date)

        emp_logs = defaultdict(list)
        for log in logs:
            emp_logs[log.employee_code].append(log.timestamp)

        processing_count = 0
        for emp_code, timestamps in emp_logs.items():
            if not timestamps:
                continue

            sorted_times = sorted(timestamps)
            check_in = sorted_times[0].time()
            check_out = sorted_times[-1].time() if len(sorted_times) > 1 else None

            emp = session.query(Employee).filter_by(code=str(emp_code)).first()
            if not emp:
                continue

            _, updated = service.upsert_daily_record(
                employee_id=emp.id,
                attendance_date=target_date,
                check_in=check_in,
                check_out=check_out,
                source='reprocess',
                commit=False,
            )
            if updated:
                processing_count += 1

        session.commit()
        flash(f'تمت إعادة معالجة {processing_count} سجل موظف بنجاح', 'success')
        return _redirect_daily_with_context()

    except Exception as e:
        session.rollback()
        flash(f'خطأ في المعالجة: {str(e)}', 'danger')
        return _redirect_daily_with_context()
    finally:
        session.close()

@attendance_bp.route('/add_manual', methods=['POST'])
def add_manual_log():
    """Add a manual attendance record"""
    db = current_app.db

    employee_id = request.form.get('employee_id')
    date_str = request.form.get('date')
    check_in_str = request.form.get('check_in')
    check_out_str = request.form.get('check_out')

    if not all([employee_id, date_str]):
        flash('يجب تحديد الموظف والتاريخ', 'danger')
        return _redirect_daily_with_context()

    session = db.get_session()
    try:
        from core.services.attendance_service import AttendanceService

        service = AttendanceService(session)
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        check_in = None
        if check_in_str:
            check_in = datetime.strptime(check_in_str, '%H:%M').time()

        check_out = None
        if check_out_str:
            check_out = datetime.strptime(check_out_str, '%H:%M').time()

        service.process_attendance_record(
            int(employee_id),
            target_date,
            check_in,
            check_out,
            source='manual',
            commit=False,
        )
        session.commit()

        flash('تم إضافة سجل الحضور بنجاح', 'success')
        return _redirect_daily_with_context()

    except Exception as e:
        session.rollback()
        flash(f'خطأ في الإضافة: {str(e)}', 'danger')
        return _redirect_daily_with_context()
    finally:
        session.close()

@attendance_bp.route('/update_manual', methods=['POST'])
def update_manual_log():
    """Update an existing attendance record"""
    db = current_app.db

    record_id = request.form.get('record_id')
    check_in_str = request.form.get('check_in')
    check_out_str = request.form.get('check_out')

    if not record_id:
         flash('معرف السجل مفقود', 'danger')
         return _redirect_daily_with_context()

    session = db.get_session()
    try:
        from core.services.attendance_service import AttendanceService

        check_in = None
        if check_in_str:
            try:
                 check_in = datetime.strptime(check_in_str, '%H:%M').time()
            except ValueError:
                 check_in = datetime.strptime(check_in_str, '%H:%M:%S').time()

        check_out = None
        if check_out_str:
             try:
                 check_out = datetime.strptime(check_out_str, '%H:%M').time()
             except ValueError:
                 check_out = datetime.strptime(check_out_str, '%H:%M:%S').time()

        service = AttendanceService(session)
        updated_record = service.process_attendance_record_by_id(
            record_id=int(record_id),
            check_in=check_in,
            check_out=check_out,
            source='manual',
            commit=False,
        )
        session.commit()

        if updated_record is None:
            flash('تم حذف سجل الحضور بنجاح', 'success')
        else:
            flash('تم تحديث السجل بنجاح', 'success')
        return _redirect_daily_with_context()

    except Exception as e:
        session.rollback()
        flash(f'خطأ في التحديث: {str(e)}', 'danger')
        return _redirect_daily_with_context()
    finally:
        session.close()

@attendance_bp.route('/bulk')
def bulk_entry():
    """Bulk attendance entry page"""
    from utils.helpers import format_date_ar
    today = format_date_ar(datetime.now().date())
    return render_template('attendance/bulk.html', today=today)

@attendance_bp.route('/check_duplicate')
def check_duplicate():
    """Check if employee already has attendance on a specific date"""
    db = current_app.db
    employee_id = request.args.get('employee_id', type=int)
    date_str = request.args.get('date')
    
    if not employee_id or not date_str:
        return {'exists': False}
        
    date_val = parse_date_compact(date_str)
    if not date_val:
        return {'exists': False}
        
    exists = db.check_attendance_exists(employee_id, date_val)
    return {'exists': exists}

@attendance_bp.route('/bulk/save', methods=['POST'])
def bulk_save():
    """Save bulk attendance records"""
    db = current_app.db
    data = request.get_json()
    records = data.get('records', [])
    
    count = 0
    errors = []
    
    from core.services.attendance_service import AttendanceService
    session = db.get_session()
    service = AttendanceService(session)
    
    try:
        for item in records:
            try:
                # Parse date
                date_str = item.get('date')
                record_date = parse_date_compact(date_str)
                if not record_date:
                    record_date = datetime.now().date()
                
                # Parse times
                check_in = None
                if item.get('check_in'):
                    check_in = datetime.strptime(item['check_in'], '%H:%M').time()
                    
                check_out = None
                if item.get('check_out'):
                    check_out = datetime.strptime(item['check_out'], '%H:%M').time()
                
                # Process attendance record
                service.process_attendance_record(
                    int(item['employee_id']),
                    record_date,
                    check_in,
                    check_out,
                    source='manual',
                    commit=False
                )
                count += 1
            except Exception as e:
                errors.append(f"ط®ط·ط£ ظ„ظ„ظ…ظˆط¸ظپ {item.get('employee_id')}: {str(e)}")
        
        session.commit()
    except Exception as e:
        session.rollback()
        return {'success': False, 'message': str(e)}
    finally:
        session.close()
        
    if errors:
        return {'success': False, 'message': ', '.join(errors[:5])}
        
    msg = f'طھظ… ط¥ط¶ط§ظپط© {count} ط³ط¬ظ„ ط­ط¶ظˆط± ط¨ظ†ط¬ط§ط­'
    flash(msg, 'center')
    return {'success': True, 'message': msg, 'center': True}

@attendance_bp.route('/bulk/delete/<int:record_id>', methods=['POST'])
def bulk_delete(record_id):
    """Delete an attendance record"""
    db = current_app.db
    session = db.get_session()

    try:
        record = session.query(DailyRecord).get(record_id)
        if record:
            session.delete(record)
            session.commit()
            flash('تم حذف سجل الحضور بنجاح', 'success')
            return {'success': True}
        else:
            flash('السجل غير موجود', 'danger')
            return {'success': False, 'message': 'السجل غير موجود'}
    except Exception as e:
        session.rollback()
        flash(f'حدث خطأ أثناء الحذف: {str(e)}', 'danger')
        return {'success': False, 'message': str(e)}
    finally:
        session.close()
