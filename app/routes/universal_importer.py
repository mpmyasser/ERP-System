from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
import os
from werkzeug.utils import secure_filename
from app.routes.auth import permission_required

importer_bp = Blueprint('importer', __name__)

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@importer_bp.route('/', methods=['GET'])
@permission_required('COA_IMPORT')
def index():
    """Dashboard for Universal Importers"""
    return render_template('importer/index.html')

@importer_bp.route('/coa', methods=['POST'])
@permission_required('COA_IMPORT')
def import_coa():
    """Import Chart of Accounts"""
    if 'file' not in request.files:
        flash('لم يتم تحديد ملف', 'danger')
        return redirect(url_for('importer.index'))
        
    file = request.files['file']
    if file.filename == '':
        flash('لم يتم تحديد ملف', 'danger')
        return redirect(url_for('importer.index'))
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Save to temp
        temp_path = os.path.join(current_app.root_path, '..', 'tmp')
        os.makedirs(temp_path, exist_ok=True)
        file_path = os.path.join(temp_path, filename)
        file.save(file_path)
        
        try:
            from app.utils.coa_importer import import_coa_from_excel
            db = current_app.db
            session = db.get_session()
            
            success, msg = import_coa_from_excel(session, file_path)
            
            if success:
                flash(msg, 'success')
            else:
                flash(msg, 'danger')
                
        except Exception as e:
            flash(f'حدث خطأ غير متوقع: {str(e)}', 'danger')
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
                
    else:
        flash('صيغة الملف غير مدعومة، يرجى رفع ملف Excel', 'warning')
        
    return redirect(url_for('importer.index'))

@importer_bp.route('/partners', methods=['POST'])
@permission_required('COA_IMPORT')
def import_partners():
    """Import Partners"""
    if 'file' not in request.files:
        flash('لم يتم تحديد ملف', 'danger')
        return redirect(url_for('importer.index'))
        
    file = request.files['file']
    if file.filename == '':
        flash('لم يتم تحديد ملف', 'danger')
        return redirect(url_for('importer.index'))
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        temp_path = os.path.join(current_app.root_path, '..', 'tmp')
        os.makedirs(temp_path, exist_ok=True)
        file_path = os.path.join(temp_path, filename)
        file.save(file_path)
        
        try:
            from app.utils.partner_importer import import_partners_from_excel
            db = current_app.db
            session = db.get_session()
            
            success, msg = import_partners_from_excel(session, file_path)
            
            if success:
                flash(msg, 'success')
            else:
                flash(msg, 'danger')
                
        except Exception as e:
            flash(f'حدث خطأ غير متوقع: {str(e)}', 'danger')
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
    else:
        flash('صيغة الملف غير مدعومة', 'warning')
        
    return redirect(url_for('importer.index'))

@importer_bp.route('/fabrics', methods=['POST'])
@permission_required('COA_IMPORT')
def import_fabrics():
    """Import Fabric Rolls"""
    if 'file' not in request.files:
        flash('لم يتم تحديد ملف', 'danger')
        return redirect(url_for('importer.index'))
        
    file = request.files['file']
    if file.filename == '':
        flash('لم يتم تحديد ملف', 'danger')
        return redirect(url_for('importer.index'))
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        temp_path = os.path.join(current_app.root_path, '..', 'tmp')
        os.makedirs(temp_path, exist_ok=True)
        file_path = os.path.join(temp_path, filename)
        file.save(file_path)
        
        try:
            from app.utils.fabric_importer import import_fabric_rolls_from_excel
            db = current_app.db
            session = db.get_session()
            
            success, msg = import_fabric_rolls_from_excel(session, file_path)
            
            if success:
                flash(msg, 'success')
            else:
                flash(msg, 'danger')
                
        except Exception as e:
            flash(f'حدث خطأ غير متوقع: {str(e)}', 'danger')
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
    else:
        flash('صيغة الملف غير مدعومة', 'warning')
        
    return redirect(url_for('importer.index'))
