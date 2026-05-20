"""
Flask Application Factory
=========================
"""

from flask import Flask
from flask_wtf.csrf import CSRFProtect
from core.db_manager import DBManager

csrf = CSRFProtect()

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object('app.config.Config')
    
    # Initialize extensions
    csrf.init_app(app)
    
    # Initialize Database Manager
    app.db = DBManager()

    # Ensure required system permissions exist
    try:
        from core.auth_models import SystemPermission
        session = app.db.get_session()
        # System Permissions
        perm = session.query(SystemPermission).filter_by(name='bulk_salary_manage').first()
        if not perm:
            session.add(SystemPermission(
                name='bulk_salary_manage',
                description='إدارة تعديل المرتبات جماعياً (حفظ/تراجع)',
                category='HR'
            ))
            session.commit()
        
        session.commit()
        session.close()
    except Exception:
        # Avoid blocking app startup if permissions table isn't ready yet
        pass
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.employees import employees_bp
    from app.routes.departments import departments_bp
    from app.routes.attendance import attendance_bp
    from app.routes.loans import loans_bp
    from app.routes.penalties import penalties_bp
    from app.routes.permissions import permissions_bp
    from app.routes.payroll import payroll_bp
    from app.routes.reports import reports_bp
    from app.routes.bonuses import bonuses_bp
    from app.routes.leaves import leaves_bp
    from app.routes.settings import settings_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.accounting import accounting_bp
    from app.routes.treasury import treasury_bp
    from app.routes.interactive_api import interactive_api_bp
    from app.routes.universal_importer import importer_bp
    from app.routes.commercial import commercial_bp
    from app.routes.manufacturing import manufacturing_bp




    
    app.register_blueprint(main_bp)
    app.register_blueprint(employees_bp, url_prefix='/employees')
    app.register_blueprint(departments_bp, url_prefix='/departments')
    app.register_blueprint(attendance_bp, url_prefix='/attendance')
    app.register_blueprint(loans_bp, url_prefix='/loans')
    app.register_blueprint(penalties_bp, url_prefix='/penalties')
    app.register_blueprint(permissions_bp, url_prefix='/permissions')
    app.register_blueprint(payroll_bp, url_prefix='/payroll')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(bonuses_bp, url_prefix='/bonuses')
    app.register_blueprint(leaves_bp, url_prefix='/leaves')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(accounting_bp, url_prefix='/accounting')
    app.register_blueprint(treasury_bp, url_prefix='/treasury')
    app.register_blueprint(interactive_api_bp, url_prefix='/api/interactive')
    app.register_blueprint(importer_bp, url_prefix='/importer')
    app.register_blueprint(commercial_bp, url_prefix='/commercial')
    app.register_blueprint(manufacturing_bp, url_prefix='/manufacturing')





    
    @app.context_processor
    def utility_processor():
        from flask import session, g
        from core.auth_manager import AuthManager
        from datetime import date
        
        def has_perm(perm_name):
            if session.get('is_admin'):
                return True
            user_id = session.get('user_id')
            if not user_id:
                return False
            
            # Cache user in g to avoid multiple DB hits per request
            if 'current_user' not in g:
                auth = AuthManager()
                g.current_user = auth.get_user_by_id(user_id)
            
            return g.current_user.has_permission(perm_name) if g.current_user else False

        return {
            'date': date,
            'has_perm': has_perm
        }

    @app.before_request
    def require_login():
        from flask import request, session, redirect, url_for
        
        # Static files and login/logout are exceptions
        if request.endpoint in ['auth.login', 'static'] or not request.endpoint:
            return
            
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))

    return app
