"""
Department Routes
=================
CRUD operations for departments
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
import sys
import os

# Add core to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'core'))

from db_manager import DBManager
import pandas as pd
import io
from flask import send_file
from core.utils.excel_utils import apply_professional_style
from datetime import datetime

departments_bp = Blueprint('departments', __name__)

@departments_bp.route('/')
def list():
    """List all departments"""
    db = current_app.db
    departments = db.get_departments()
    
    return render_template('departments/list.html', departments=departments)

@departments_bp.route('/create', methods=['GET', 'POST'])
def create():
    """Create new department"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        erp_code = request.form.get('erp_code', '')
        display_order = request.form.get('display_order', 0)
        
        if not name:
            flash('يرجى إدخال اسم القسم', 'danger')
            return render_template('departments/form.html', mode='create')
        
        try:
            db = current_app.db
            db.add_department(name=name, erp_cost_center_code=erp_code, display_order=int(display_order or 0))
            flash(f'تم إضافة القسم {name} بنجاح', 'center')
            return redirect(url_for('departments.list'))
        except Exception as e:
            flash(f'حدث خطأ: {str(e)}', 'danger')
    
    return render_template('departments/form.html', mode='create')

@departments_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    """Edit department"""
    db = current_app.db
    department = db.get_department_by_id(id)
    
    if not department:
        flash('القسم غير موجود', 'danger')
        return redirect(url_for('departments.list'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        erp_code = request.form.get('erp_code', '')
        display_order = request.form.get('display_order', 0)
        
        if not name:
            flash('يرجى إدخال اسم القسم', 'danger')
            return render_template('departments/form.html', mode='edit', department=department)
        
        try:
            db.update_department(id, name=name, erp_cost_center_code=erp_code, display_order=int(display_order or 0))
            flash(f'تم تحديث القسم {name} بنجاح', 'center')
            return redirect(url_for('departments.list'))
        except Exception as e:
            flash(f'حدث خطأ: {str(e)}', 'danger')
    
    return render_template('departments/form.html', mode='edit', department=department)

@departments_bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    """Delete department"""
    db = current_app.db
    department = db.get_department_by_id(id)
    
    if not department:
        flash('القسم غير موجود', 'danger')
        return redirect(url_for('departments.list'))
    
    try:
        dept_name = department.name
        db.delete_department(id)
        flash(f'تم حذف القسم {dept_name} بنجاح', 'center')
    except Exception as e:
        flash(f'حدث خطأ أثناء الحذف: {str(e)}', 'danger')
    
    return redirect(url_for('departments.list'))
    return redirect(url_for('departments.list'))

@departments_bp.route('/export_excel')
def export_excel():
    """Export departments list to Excel"""
    try:
        db = current_app.db
        departments = db.get_departments()
        
        excel_data = []
        for dept in departments:
            # Count active employees
            active_count = len([e for e in dept.employees if e.is_active])
            
            excel_data.append({
                'م': dept.id,
                'اسم القسم': dept.name,
                'كود مركز التكلفة (ERP)': dept.erp_cost_center_code or '',
                'عدد الموظفين': active_count
            })
            
        if not excel_data:
            flash("لا توجد أقسام لتصديرها", "warning")
            return redirect(url_for('departments.list'))

        # Create Excel
        df = pd.DataFrame(excel_data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Departments')
            apply_professional_style(writer.book.active, df)

        output.seek(0)
        filename = f"Departments_List_{datetime.now().strftime('%Y_%m_%d')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f"حدث خطأ أثناء تصدير ملف Excel: {str(e)}", "danger")
        return redirect(url_for('departments.list'))
