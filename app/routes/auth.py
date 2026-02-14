from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from core.auth_manager import AuthManager
from core.auth_models import User
from functools import wraps

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
auth_manager = AuthManager()

# Decorator for Login Required
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

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
    return render_template('auth/users.html', users=users)

@auth_bp.route('/users/add', methods=['GET', 'POST'])
@admin_required
def add_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        
        try:
            auth_manager.create_user(username, password, full_name)
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
            
            user.username = username
            user.full_name = full_name
            user.is_admin = is_admin
            user.is_active = is_active
            
            if new_password:
                user.set_password(new_password)
                
            db_session.commit()
            flash(f'تم تحديث بيانات {user.username} بنجاح', 'center')
            return redirect(url_for('auth.list_users'))
                
        return render_template('auth/edit_user.html', user=user)
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
