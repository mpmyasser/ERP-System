"""
Payroll Routes
==============
Payroll calculation and management
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'core'))

from db_manager import DBManager
from services.payroll_processor import PayrollCalculator

payroll_bp = Blueprint('payroll', __name__)

@payroll_bp.route('/')
def index():
    """Payroll main page"""
    db = current_app.db
    employees = db.get_all_employees(only_active=True)
    db.attach_effective_salaries(employees)
    total_basic_salary = sum(getattr(e, 'effective_salary', e.basic_salary or 0) for e in employees)
    
    return render_template('payroll/index.html', 
                         employees=employees,
                         total_basic_salary=total_basic_salary)

@payroll_bp.route('/calculate/<int:emp_id>', methods=['GET', 'POST'])
def calculate(emp_id):
    """Calculate payroll for employee with month/year selection"""
    db = current_app.db
    employee = db.get_employee_by_id(emp_id)
    
    if not employee:
        flash('الموظف غير موجود', 'danger')
        return redirect(url_for('payroll.index'))
    
    # Get month and year from request parameters (with defaults to current month/year)
    year = request.args.get('year', type=int, default=datetime.now().year)
    month = request.args.get('month', type=int, default=datetime.now().month)
    
    # Validate month
    if month < 1 or month > 12:
        month = datetime.now().month
    
    # Calculate payroll
    calculator = PayrollCalculator(db)
    payroll_data = calculator.calculate_employee_payroll(emp_id, year, month)
    
    return render_template('payroll/view.html',
                         employee=employee,
                         payroll=payroll_data,
                         year=year,
                         month=month)
