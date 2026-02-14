"""
Main Routes - Dashboard
=======================
"""

from flask import Blueprint, render_template, current_app
import sys
import os

# Add core to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'core'))

from db_manager import DBManager

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/dashboard')
def dashboard():
    """Dashboard page with statistics"""
    db = current_app.db
    
    # Get statistics
    employees = db.get_all_employees()
    departments = db.get_departments()
    
    stats = {
        'total_employees': len(employees),
        'active_employees': len([e for e in employees if e.is_active]),
        'total_departments': len(departments),
        'inactive_employees': len([e for e in employees if not e.is_active])
    }
    
    return render_template('dashboard.html', stats=stats)


@main_bp.route('/debug/resizer')
def resizer_test():
    """Simple page to test table_resizer.js functionality"""
    return render_template('debug/resizer_test.html')
