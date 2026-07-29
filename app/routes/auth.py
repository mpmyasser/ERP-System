from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import time
import json
import os
import urllib.request
from core.auth_manager import AuthManager
from core.auth_models import User, UserPreference
from functools import wraps

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
auth_manager = AuthManager()

def _get_user_pref(session_db, user_id, key):
    return session_db.query(UserPreference).filter_by(user_id=user_id, key=key).first()

def _get_user_pref_value(session_db, user_id, key):
    pref = _get_user_pref(session_db, user_id, key)
    return pref.value if pref else None

def _set_user_pref(session_db, user_id, key, value):
    pref = _get_user_pref(session_db, user_id, key)
    if pref:
        pref.value = value
    else:
        session_db.add(UserPreference(user_id=user_id, key=key, value=value))

def _mask_phone(phone):
    digits = ''.join(ch for ch in (phone or '') if ch.isdigit())
    if not digits:
        return ''
    if len(digits) <= 4:
        return digits
    return ('*' * (len(digits) - 4)) + digits[-4:]

def _send_whatsapp_code(phone, code):
    api_url = os.environ.get('WHATSAPP_API_URL')
    api_token = os.environ.get('WHATSAPP_API_TOKEN')
    if not api_url or not api_token:
        return False
    payload = json.dumps({
        'to': phone,
        'message': f'رمز التحقق الخاص بك هو: {code}'
    }).encode('utf-8')
    try:
        req = urllib.request.Request(
            api_url,
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_token}'
            }
        )
        with urllib.request.urlopen(req, timeout=10):
            return True
    except Exception:
        return False

# Decorator for Login Required
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def safe_referrer(fallback_endpoint, **fallback_kwargs):
    """
    يُعيد request.referrer فقط إذا كان يُشير لنفس نطاق التطبيق (لمنع Open Redirect
    عبر تزوير Referer header)، وإلا يُعيد url_for(fallback_endpoint) كبديل آمن.
    """
    from urllib.parse import urlparse
    referrer = request.referrer
    if referrer:
        ref_host = urlparse(referrer).netloc
        req_host = urlparse(request.host_url).netloc
        if ref_host == req_host:
            return referrer
    return url_for(fallback_endpoint, **fallback_kwargs)

# Decorator for Admin Only
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        if not session.get('is_admin'):
            flash('غير مصرح لك بدخول هذه الصفحة', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Decorator for Permission Required
def permission_required(perm_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('auth.login'))
            
            if session.get('is_admin'):
                return f(*args, **kwargs)
            
            # Use auth_manager to check permission
            user_id = session.get('user_id')
            user = auth_manager.get_user_by_id(user_id)
            if not user or not user.has_permission(perm_name):
                flash('ليس لديك الصلاحية الكافية للقيام بهذا الإجراء', 'danger')
                return redirect(url_for('main.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = auth_manager.authenticate(username, password)
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            session['full_name'] = user.full_name
            session['is_admin'] = user.is_admin
            # Store permissions in session for quick UI checks (optional but good for perf)
            # Or rely on a context processor to load them
            
            flash(f'مرحباً {user.full_name}', 'center')
            return redirect(url_for('main.dashboard'))
        else:
            flash('اسم المستخدم أو كلمة المرور غير صحيحة', 'danger')
            
    return render_template('auth/login.html')

@auth_bp.route('/forgot', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        national_id_input = (request.form.get('national_id') or '').strip()
        if not username:
            flash('يرجى إدخال اسم المستخدم', 'warning')
            return render_template('auth/forgot_password.html')

        user = auth_manager.get_user_by_username(username)
        if not user:
            flash('اسم المستخدم غير موجود', 'warning')
            return render_template('auth/forgot_password.html')

        from database_models import Employee
        db_session = auth_manager.db.get_session()
        try:
            mobile_pref = _get_user_pref_value(db_session, user.id, 'mobile_number')
            national_pref = _get_user_pref_value(db_session, user.id, 'national_id')
            employee = db_session.query(Employee).filter(Employee.code == username).first()
            if not employee and user.full_name:
                employee = db_session.query(Employee).filter(Employee.name == user.full_name).first()
            if not employee:
                employee = db_session.query(Employee).filter(Employee.name == username).first()
            mobile_number = mobile_pref or (employee.mobile_number if employee else None)
            national_id = national_pref or (employee.national_id if employee else None)
        finally:
            db_session.close()

        if mobile_number:
            code = f"{secrets.randbelow(1000000):06d}"
            sent = _send_whatsapp_code(mobile_number, code)
            if not sent:
                flash('تعذر إرسال كود التحقق عبر واتساب. يرجى مراجعة الإعدادات.', 'warning')
                return render_template('auth/forgot_password.html')

            session['reset_user_id'] = user.id
            session['reset_otp_hash'] = generate_password_hash(code)
            session['reset_otp_expires'] = int(time.time()) + 600
            session['reset_phone_masked'] = _mask_phone(mobile_number)
            session['reset_using_national_id'] = False
            session['reset_otp_attempts'] = 0

            flash('تم إرسال كود التحقق إلى واتساب الموظف', 'info')
            return redirect(url_for('auth.reset_password'))

        if not national_id:
            flash('لا يوجد رقم واتساب أو رقم قومي مسجل لهذا المستخدم', 'warning')
            return render_template('auth/forgot_password.html')

        if not national_id_input:
            flash('أدخل الرقم القومي لإثبات الهوية', 'warning')
            return render_template('auth/forgot_password.html')

        if national_id_input != national_id:
            flash('الرقم القومي غير مطابق', 'warning')
            return render_template('auth/forgot_password.html')

        session['reset_user_id'] = user.id
        session['reset_otp_expires'] = int(time.time()) + 600
        session['reset_phone_masked'] = ''
        session['reset_using_national_id'] = True

        flash('تم التحقق من الهوية بالرقم القومي', 'info')
        return redirect(url_for('auth.reset_password'))

    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset', methods=['GET', 'POST'])
def reset_password():
    if not session.get('reset_user_id'):
        flash('ابدأ باستعادة كلمة المرور أولاً', 'info')
        return redirect(url_for('auth.forgot_password'))

    masked_phone = session.get('reset_phone_masked', '')
    using_national_id = bool(session.get('reset_using_national_id'))

    if request.method == 'POST':
        otp = (request.form.get('otp') or '').strip()
        new_password = (request.form.get('new_password') or '').strip()
        confirm_password = (request.form.get('confirm_password') or '').strip()

        if not new_password or not confirm_password:
            flash('يرجى تعبئة جميع الحقول', 'warning')
            return render_template('auth/reset_password.html', masked_phone=masked_phone, using_national_id=using_national_id)

        if new_password != confirm_password:
            flash('كلمة المرور وتأكيدها غير متطابقين', 'warning')
            return render_template('auth/reset_password.html', masked_phone=masked_phone, using_national_id=using_national_id)

        expires_at = session.get('reset_otp_expires')
        if not expires_at or int(time.time()) > int(expires_at):
            flash('انتهت صلاحية كود التحقق، أعد المحاولة', 'warning')
            return redirect(url_for('auth.forgot_password'))

        otp_hash = session.get('reset_otp_hash')
        if not using_national_id:
            attempts = session.get('reset_otp_attempts', 0)
            if attempts >= 5:
                session.pop('reset_user_id', None)
                session.pop('reset_otp_hash', None)
                session.pop('reset_otp_expires', None)
                session.pop('reset_phone_masked', None)
                session.pop('reset_using_national_id', None)
                session.pop('reset_otp_attempts', None)
                flash('تم تجاوز الحد المسموح من المحاولات، يرجى إعادة المحاولة من البداية', 'warning')
                return redirect(url_for('auth.forgot_password'))

            if not otp_hash or not otp or not check_password_hash(otp_hash, otp):
                session['reset_otp_attempts'] = attempts + 1
                flash('كود التحقق غير صحيح', 'warning')
                return render_template('auth/reset_password.html', masked_phone=masked_phone, using_national_id=using_national_id)

        db_session = auth_manager.db.get_session()
        try:
            user = db_session.query(User).filter_by(id=session.get('reset_user_id')).first()
            if not user:
                flash('المستخدم غير موجود', 'warning')
                return redirect(url_for('auth.forgot_password'))
            user.set_password(new_password)
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            flash(f'حدث خطأ أثناء التحديث: {e}', 'danger')
            return render_template('auth/reset_password.html', masked_phone=masked_phone, using_national_id=using_national_id)
        finally:
            db_session.close()

        session.pop('reset_user_id', None)
        session.pop('reset_otp_hash', None)
        session.pop('reset_otp_expires', None)
        session.pop('reset_phone_masked', None)
        session.pop('reset_using_national_id', None)
        session.pop('reset_otp_attempts', None)

        flash('تم تغيير كلمة المرور بنجاح', 'center')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', masked_phone=masked_phone, using_national_id=using_national_id)

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('تم تسجيل الخروج بنجاح', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session.get('user_id')
    user = auth_manager.get_user_by_id(user_id)
    
    if request.method == 'POST':
        username = request.form.get('username')
        full_name = request.form.get('full_name')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        db_session = auth_manager.db.get_session()
        try:
            # Re-fetch user in local session
            db_user = db_session.query(User).filter_by(id=user_id).first()
            
            # Check if username changed and is available
            if username != db_user.username:
                existing = db_session.query(User).filter_by(username=username).first()
                if existing:
                    flash('اسم المستخدم هذا موجود بالفعل، اختر اسماً آخر', 'danger')
                    return redirect(url_for('auth.profile'))
                db_user.username = username
                session['username'] = username
            
            db_user.full_name = full_name
            session['full_name'] = full_name
            
            if new_password:
                if new_password != confirm_password:
                    flash('كلمة المرور وتأكيدها غير متطابقين', 'danger')
                    return redirect(url_for('auth.profile'))
                db_user.set_password(new_password)
                
            db_session.commit()
            flash('تم تحديث الملف الشخصي بنجاح', 'center')
        except Exception as e:
            db_session.rollback()
            flash(f'خطأ أثناء التحديث: {e}', 'danger')
        finally:
            db_session.close()
            
        return redirect(url_for('auth.profile'))
        
    return render_template('auth/profile.html', user=user)

@auth_bp.route('/users')

@admin_required
def list_users():
    users = auth_manager.get_all_users()
    db_session = auth_manager.db.get_session()
    try:
        user_ids = [u.id for u in users]
        prefs = {}
        if user_ids:
            rows = db_session.query(UserPreference)\
                .filter(UserPreference.user_id.in_(user_ids))\
                .filter(UserPreference.key.in_(['mobile_number', 'national_id']))\
                .all()
            for row in rows:
                prefs.setdefault(row.user_id, {})[row.key] = row.value
    finally:
        db_session.close()
    return render_template('auth/users.html', users=users, user_prefs=prefs)

@auth_bp.route('/users/add', methods=['GET', 'POST'])
@admin_required
def add_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        
        try:
            user = auth_manager.create_user(username, password, full_name)
            mobile_number = (request.form.get('mobile_number') or '').strip()
            national_id = (request.form.get('national_id') or '').strip()
            db_session = auth_manager.db.get_session()
            try:
                if mobile_number:
                    _set_user_pref(db_session, user.id, 'mobile_number', mobile_number)
                if national_id:
                    _set_user_pref(db_session, user.id, 'national_id', national_id)
                db_session.commit()
            finally:
                db_session.close()
            flash('تم إضافة المستخدم بنجاح. يرجى تحديد الصلاحيات الآن.', 'center')
            return redirect(url_for('auth.list_users'))
        except Exception as e:
            flash(f'خطأ: {e}', 'danger')
            
    return render_template('auth/add_user.html')

@auth_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    db_session = auth_manager.db.get_session()
    try:
        user = db_session.query(User).get(user_id)
        
        if not user:
            flash('المستخدم غير موجود', 'danger')
            return redirect(url_for('auth.list_users'))
            
        if request.method == 'POST':
            username = request.form.get('username')
            full_name = request.form.get('full_name')
            new_password = request.form.get('password')
            is_admin = request.form.get('is_admin') == 'on'
            is_active = request.form.get('is_active') == 'on'
            mobile_number = (request.form.get('mobile_number') or '').strip()
            national_id = (request.form.get('national_id') or '').strip()
            
            user.username = username
            user.full_name = full_name
            user.is_admin = is_admin
            user.is_active = is_active
            
            if new_password:
                user.set_password(new_password)
            _set_user_pref(db_session, user.id, 'mobile_number', mobile_number or None)
            _set_user_pref(db_session, user.id, 'national_id', national_id or None)
                 
            db_session.commit()
            flash(f'تم تحديث بيانات {user.username} بنجاح', 'center')
            return redirect(url_for('auth.list_users'))
                
        mobile_pref = _get_user_pref_value(db_session, user.id, 'mobile_number')
        national_pref = _get_user_pref_value(db_session, user.id, 'national_id')
        return render_template('auth/edit_user.html', user=user, mobile_number=mobile_pref, national_id=national_pref)
    except Exception as e:
        db_session.rollback()
        flash(f'خطأ: {e}', 'danger')
        return redirect(url_for('auth.list_users'))
    finally:
        db_session.close()

@auth_bp.route('/users/<int:user_id>/permissions', methods=['GET', 'POST'])
@admin_required
def manage_permissions(user_id):
    user = auth_manager.get_user_by_id(user_id)
    all_permissions = auth_manager.get_all_permissions()
    
    db_session = auth_manager.db.get_session()
    from core.treasury_models import CashAccount
    all_cash_accounts = db_session.query(CashAccount).filter_by(is_active=True).all()
    db_session.close()
    
    if request.method == 'POST':
        # Get list of checks
        selected_perms = request.form.getlist('permissions')
        # Convert to ints
        try:
            perm_ids = [int(p) for p in selected_perms]
            auth_manager.update_user_permissions(user_id, perm_ids)
            
            # Update cash access
            selected_cash = request.form.getlist('cash_accounts')
            cash_ids = [int(c) for c in selected_cash]
            auth_manager.update_user_cash_access(user_id, cash_ids)
            
            flash('تم تحديث الصلاحيات والوصول بنجاح', 'center')
            return redirect(url_for('auth.list_users'))
        except Exception as e:
            flash(f'خطأ في الحفظ: {e}', 'danger')
            
    # Group permissions by category for better UI
    perms_by_cat = {}
    for p in all_permissions:
        if p.category not in perms_by_cat:
            perms_by_cat[p.category] = []
        perms_by_cat[p.category].append(p)
        
    return render_template('auth/permissions.html', 
                           user=user, 
                           perms_by_cat=perms_by_cat,
                           all_cash_accounts=all_cash_accounts)

@auth_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    db_session = auth_manager.db.get_session()
    current_user_id = session.get('user_id')
    
    try:
        if user_id == current_user_id:
            flash('لا يمكنك حذف حسابك الخاص', 'danger')
            return redirect(url_for('auth.list_users'))
        
        user = db_session.query(User).get(user_id)
        
        if not user:
            flash('المستخدم غير موجود', 'danger')
            return redirect(url_for('auth.list_users'))
        
        username = user.username
        db_session.delete(user)
        db_session.commit()
        flash(f'تم حذف المستخدم {username} بنجاح', 'center')
        
    except Exception as e:
        db_session.rollback()
        flash(f'خطأ أثناء حذف المستخدم: {e}', 'danger')
    finally:
        db_session.close()
    
    return redirect(url_for('auth.list_users'))
