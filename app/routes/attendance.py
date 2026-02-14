"""
Attendance Routes
=================
Attendance management and import
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
import sys
import os
from datetime import datetime, date
import pandas as pd
from werkzeug.utils import secure_filename
from utils.helpers import parse_date_compact
from sqlalchemy.orm import joinedload

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'core'))

from db_manager import DBManager
from database_models import DailyRecord, Employee, AttendanceLog
from app.forms import AttendanceImportForm

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')

attendance_bp = Blueprint('attendance', __name__)

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
        
        # Fallback to single 'date' param for backward compatibility
        d_legacy = request.args.get('date')
        
        if d_from:
            start_date = parse_date_compact(d_from)
        elif d_legacy:
            start_date = parse_date_compact(d_legacy)
        else:
            start_date = date.today()
            
        if d_to:
            end_date = parse_date_compact(d_to)
        else:
            end_date = start_date
            
        if end_date < start_date:
            end_date = start_date
        
        # Get filters
        dept_ids = request.args.getlist('department_ids', type=int)
        dept_filter_mode = request.args.get('dept_filter_mode', 'include')
        search = (request.args.get('search') or '').strip()
        
        # Query with explicit eager loading
        query = session.query(DailyRecord)\
            .join(Employee)\
            .filter(DailyRecord.date >= start_date)\
            .filter(DailyRecord.date <= end_date)\
            .order_by(DailyRecord.date.desc(), Employee.code)\
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
            flash('❌ نوع الملف غير مدعوم. استخدم ملفات Excel فقط (.xls, .xlsx)', 'danger')
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
                flash(f'✅ تم استيراد {success_count} سجل بصمة بنجاح!', 'center')
                
                # Auto-process logic (Process affected dates)
                try:
                    if affected_dates:
                        db = current_app.db # Get db instance
                        count_processed = 0
                        for d in affected_dates:
                            # d is datetime.date object from the script
                            db.process_attendance_for_date(d)
                            count_processed += 1
                        
                        flash(f'✅ تمت معالجة الحضور لـ {count_processed} يوم/أيام تلقائياً.', 'info')
                except Exception as e:
                    print(f"Error triggering processing: {e}")
                    flash(f'⚠️ حدث خطأ أثناء معالجة البيانات: {e}', 'warning')
                    
            if errors:
                flash(f'⚠️ تم العثور على {len(errors)} أخطاء. عرض أول 5:', 'warning')
                for err in errors[:5]:
                    flash(str(err), 'danger')
            elif success_count == 0:
                 flash('⚠️ لم يتم استيراد أي سجلات. تأكد من صحة أسماء الأعمدة (Code, Date, In, Out)', 'warning')
                 
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
            flash(f'تم حذف سجلات الحضور ليوم {date_str}', 'center')
            
        return redirect(url_for('attendance.daily'))
    except Exception as e:
        flash(f'حدث خطأ أثناء الحذف: {str(e)}', 'danger')
        return redirect(url_for('attendance.daily'))

@attendance_bp.route('/reprocess', methods=['POST'])
def reprocess_attendance():
    """Reprocess raw logs into daily records"""
    db = current_app.db
    date_str = request.form.get('date')
    
    if not date_str:
        flash('التاريخ مطلوب لإعادة المعالجة', 'danger')
        return redirect(url_for('attendance.daily'))
        
    try:
        from core.services.attendance_service import AttendanceService
        
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        service = AttendanceService(db.get_session())
        
        # 1. Clear existing daily records for this date (optional, but safe)
        # db.clear_attendance_records(target_date)
        
        # 2. Get all logs for this date
        logs = db.get_logs_by_date(target_date)
        
        # 3. Group by employee
        from collections import defaultdict
        emp_logs = defaultdict(list)
        for log in logs:
            # logs only have employee_code
            emp_logs[log.employee_code].append(log.timestamp)
            
        processing_count = 0
        for emp_code, timestamps in emp_logs.items():
            if not timestamps:
                continue
                
            sorted_times = sorted(timestamps)
            
            # Simple Logic: First is IN, Last is OUT
            check_in = sorted_times[0].time()
            check_out = sorted_times[-1].time() if len(sorted_times) > 1 else None
            
            # If only 1 record, it's just check-in? Or invalid?
            # Assuming Check-in. Check-out is None.
            
            # We need employee_id. If log stored Code, we need to resolve it.
            # Assuming db.get_logs_by_date returns objects with access to employee_id
            
            # Resolve Employee ID from Code
            emp_id = None
            emp = db.get_employee_by_code(str(emp_code))
            if emp:
                emp_id = emp.id
            
            if emp_id:
                service.process_attendance_record(emp_id, target_date, check_in, check_out)
                processing_count += 1
                
        flash(f'تم إعادة معالجة {processing_count} سجل موظف بنجاح', 'center')
        return redirect(url_for('attendance.daily'))
        
    except Exception as e:
        flash(f'خطأ في المعالجة: {str(e)}', 'danger')
        return redirect(url_for('attendance.daily'))

@attendance_bp.route('/add_manual', methods=['POST'])
def add_manual_log():
    """Add a manual attendance record"""
    db = current_app.db
    
    # Form data
    employee_id = request.form.get('employee_id')
    date_str = request.form.get('date')
    check_in_str = request.form.get('check_in')
    check_out_str = request.form.get('check_out')
    
    if not all([employee_id, date_str]):
        flash('يجب تحديد الموظف والتاريخ', 'danger')
        return redirect(url_for('attendance.daily'))
        
    try:
        from core.services.attendance_service import AttendanceService
        service = AttendanceService(db.get_session())
        
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        check_in = None
        if check_in_str:
            check_in = datetime.strptime(check_in_str, '%H:%M').time()
            
        check_out = None
        if check_out_str:
            check_out = datetime.strptime(check_out_str, '%H:%M').time()
            
        # Process directly
        service.process_attendance_record(int(employee_id), target_date, check_in, check_out)
        
        flash('تم إضافة سجل الحضور بنجاح', 'center')
        return redirect(url_for('attendance.daily'))
        
    except Exception as e:
        flash(f'خطأ في الإضافة: {str(e)}', 'danger')
        return redirect(url_for('attendance.daily'))

@attendance_bp.route('/update_manual', methods=['POST'])
def update_manual_log():
    """Update an existing attendance record"""
    db = current_app.db
    
    record_id = request.form.get('record_id')
    check_in_str = request.form.get('check_in')
    check_out_str = request.form.get('check_out')
    
    if not record_id:
         flash('معرف السجل مفقود', 'danger')
         return redirect(url_for('attendance.daily'))
         
    try:
        check_in = None
        if check_in_str:
            try:
                 check_in = datetime.strptime(check_in_str, '%H:%M').time()
            except ValueError:
                 # Try with Seconds if present
                 check_in = datetime.strptime(check_in_str, '%H:%M:%S').time()

        check_out = None
        if check_out_str:
             try:
                 check_out = datetime.strptime(check_out_str, '%H:%M').time()
             except ValueError:
                 check_out = datetime.strptime(check_out_str, '%H:%M:%S').time()

        # Update via Service to ensure recalcs?
        # Or simple DB update? Service is safer for logic.
        # But we need Employee ID and Date.
        # Let's fetch record first to get metadata if we want to use Service.
        # Or just use DBManager simple update if we don't care about late minutes updates yet.
        # Ideally: Recalculate.
        
        # Simpler approach: update raw times in DB.
        db.update_daily_record(int(record_id), check_in, check_out)
        
        flash('تم تحديث السجل بنجاح', 'center')
        return redirect(url_for('attendance.daily'))
        
    except Exception as e:
        flash(f'خطأ في التحديث: {str(e)}', 'danger')
        return redirect(url_for('attendance.daily'))

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
                    check_out
                )
                count += 1
            except Exception as e:
                errors.append(f"خطأ للموظف {item.get('employee_id')}: {str(e)}")
        
        session.commit()
    except Exception as e:
        session.rollback()
        return {'success': False, 'message': str(e)}
    finally:
        session.close()
        
    if errors:
        return {'success': False, 'message': ', '.join(errors[:5])}
        
    msg = f'تم إضافة {count} سجل حضور بنجاح'
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
            return {'success': True}
        else:
            return {'success': False, 'message': 'السجل غير موجود'}
    except Exception as e:
        session.rollback()
        return {'success': False, 'message': str(e)}
    finally:
        session.close()

