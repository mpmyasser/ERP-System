from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, session as flask_session
from core.db_manager import DBManager
from core.accounting_models import Account, AccountType, JournalEntry, JournalItem, CostCenter
from app.routes.auth import login_required
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from datetime import datetime

accounting_bp = Blueprint('accounting', __name__)
db = DBManager()

@accounting_bp.route('/')
@login_required
def index():
    return render_template('accounting/dashboard.html')

@accounting_bp.route('/coa')
@login_required
def coa():
    """عرض شجرة الحسابات"""
    db_session = db.get_session()
    try:
        accounts = db_session.query(Account).order_by(Account.code).all()
        return render_template('accounting/coa.html', accounts=accounts)
    finally:
        db_session.close()

@accounting_bp.route('/coa/add', methods=['POST'])
@login_required
def add_account():
    code = request.form.get('code')
    name = request.form.get('name')
    type = request.form.get('type')
    parent_id = request.form.get('parent_id')
    display_order = request.form.get('display_order', 0)
    
    if not parent_id:
        parent_id = None
        
    db_session = db.get_session()
    try:
        # check duplicate
        if db_session.query(Account).filter_by(code=code).first():
            flash('كود الحساب موجود بالفعل', 'danger')
            return redirect(url_for('accounting.coa'))
            
        new_acc = Account(code=code, name=name, type=type, parent_id=parent_id, display_order=int(display_order) if display_order else 0)
        db_session.add(new_acc)
        db_session.commit()
        flash('تم إضافة الحساب بنجاح', 'center')
    except Exception as e:
        flash(f'خطأ: {e}', 'danger')
    finally:
        db_session.close()
        
    return redirect(url_for('accounting.coa'))

@accounting_bp.route('/coa/<int:id>/edit', methods=['POST'])
@login_required
def edit_account(id):
    name = request.form.get('name')
    display_order = request.form.get('display_order', 0)
    
    db_session = db.get_session()
    try:
        account = db_session.query(Account).get(id)
        if not account:
            flash('الحساب غير موجود', 'danger')
        else:
            account.name = name
            account.display_order = int(display_order) if display_order else 0
            db_session.commit()
            flash('تم تعديل الحساب بنجاح', 'center')
    except Exception as e:
        db_session.rollback()
        flash(f'خطأ: {e}', 'danger')
    finally:
        db_session.close()
    return redirect(url_for('accounting.coa'))

# --- قيود اليومية ---

@accounting_bp.route('/journals')
@login_required
def list_journals():
    db_session = db.get_session()
    try:
        entries = db_session.query(JournalEntry).order_by(JournalEntry.date.desc()).all()
        return render_template('accounting/journals_list.html', entries=entries)
    finally:
        db_session.close()

@accounting_bp.route('/journals/new', methods=['GET'])
@login_required
def new_journal():
    return render_template('accounting/journal_form.html', mode='create', entry=None)

@accounting_bp.route('/journals/<int:id>')
@login_required
def view_journal(id):
    db_session = db.get_session()
    try:
        entry = db_session.query(JournalEntry).options(joinedload(JournalEntry.items)).get(id)
        if not entry:
            flash('القيد غير موجود', 'danger')
            return redirect(url_for('accounting.list_journals'))
        
        # Calculate totals
        total_debit = sum(item.debit for item in entry.items)
        total_credit = sum(item.credit for item in entry.items)
        balance = total_debit - total_credit
        is_balanced = abs(balance) < 0.01
        
        return render_template('accounting/journal_view.html', 
                             entry=entry, 
                             total_debit=total_debit,
                             total_credit=total_credit,
                             balance=balance,
                             is_balanced=is_balanced)
    finally:
        db_session.close()

@accounting_bp.route('/journals/<int:id>/edit', methods=['GET'])
@login_required
def edit_journal(id):
    db_session = db.get_session()
    try:
        entry = db_session.query(JournalEntry).options(joinedload(JournalEntry.items)).get(id)
        if not entry:
            flash('القيد غير موجود', 'danger')
            return redirect(url_for('accounting.list_journals'))
        return render_template('accounting/journal_form.html', mode='edit', entry=entry)
    finally:
        db_session.close()

@accounting_bp.route('/api/accounts/search')
@login_required
def search_accounts():
    q = request.args.get('q', '')
    db_session = db.get_session()
    try:
        accounts = db_session.query(Account).filter(
            or_(Account.name.like(f'%{q}%'), Account.code.like(f'%{q}%'))
        ).limit(10).all()
        return jsonify([{'id': a.id, 'text': f'{a.code} - {a.name}'} for a in accounts])
    finally:
        db_session.close()

@accounting_bp.route('/journals/save', methods=['POST'])
@login_required
def save_journal():
    data = request.json
    if not data:
        return jsonify({'success': False, 'message': 'لا توجد بيانات'}), 400
        
    date_str = data.get('date')
    ref = data.get('reference')
    desc = data.get('description')
    items = data.get('items', [])
    
    if not items:
        return jsonify({'success': False, 'message': 'يجب إضافة سطر واحد على الأقل في القيد'}), 400
        
    # التحقق من توازن القيد
    total_debit = sum(float(i.get('debit', 0) or 0) for i in items)
    total_credit = sum(float(i.get('credit', 0) or 0) for i in items)
    
    if abs(total_debit - total_credit) > 0.001:
        return jsonify({'success': False, 'message': f'القيد غير متوازن! الفرق: {total_debit - total_credit}'}), 400

    db_session = db.get_session()
    try:
        entry_id = data.get('id')
        if entry_id:
            entry = db_session.query(JournalEntry).get(entry_id)
            if not entry:
                return jsonify({'success': False, 'message': 'القيد غير موجود'}), 404
            # Update existing entry
            entry.date = datetime.strptime(date_str, '%Y-%m-%d').date()
            entry.reference = ref
            entry.description = desc
            
            # Remove old items
            db_session.query(JournalItem).filter_by(journal_entry_id=entry.id).delete()
        else:
            # Create Journal Entry
            entry = JournalEntry(
                date=datetime.strptime(date_str, '%Y-%m-%d').date(),
                reference=ref,
                description=desc,
                created_by=flask_session.get('user_id'),
                status='Posted'
            )
            db_session.add(entry)
            db_session.flush()
        
        for item in items:
            j_item = JournalItem(
                journal_entry_id=entry.id,
                account_id=item.get('account_id'),
                debit=float(item.get('debit', 0) or 0),
                credit=float(item.get('credit', 0) or 0),
                description=item.get('description')
            )
            db_session.add(j_item)
            
        db_session.commit()
        return jsonify({'success': True, 'message': 'تم حفظ القيد بنجاح'})
    except Exception as e:
        db_session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        db_session.close()

@accounting_bp.route('/journals/<int:entry_id>/delete', methods=['POST'])
@login_required
def delete_journal(entry_id):
    db_session = db.get_session()
    try:
        entry = db_session.query(JournalEntry).filter_by(id=entry_id).first()
        if entry:
            db_session.delete(entry)
            db_session.commit()
            flash('تم حذف القيد بنجاح', 'center')
        else:
            flash('القيد غير موجود', 'danger')
    except Exception as e:
        db_session.rollback()
        flash(f'خطأ أثناء الحذف: {e}', 'danger')
    finally:
        db_session.close()
    return redirect(url_for('accounting.list_journals'))

# --- مراكز التكلفة ---

@accounting_bp.route('/cost_centers')
@login_required
def list_cost_centers():
    db_session = db.get_session()
    try:
        centers = db_session.query(CostCenter).order_by(CostCenter.code).all()
        return render_template('accounting/cost_centers.html', centers=centers)
    finally:
        db_session.close()

@accounting_bp.route('/cost_centers/add', methods=['POST'])
@login_required
def add_cost_center():
    code = request.form.get('code')
    name = request.form.get('name')
    display_order = request.form.get('display_order', 0)
    
    db_session = db.get_session()
    try:
        if db_session.query(CostCenter).filter_by(code=code).first():
            flash('كود مركز التكلفة موجود بالفعل', 'danger')
        else:
            new_center = CostCenter(code=code, name=name, display_order=int(display_order) if display_order else 0)
            db_session.add(new_center)
            db_session.commit()
            flash('تم إضافة مركز التكلفة بنجاح', 'center')
    except Exception as e:
        flash(f'خطأ: {e}', 'danger')
    finally:
        db_session.close()
    return redirect(url_for('accounting.list_cost_centers'))

@accounting_bp.route('/cost_centers/<int:id>/edit', methods=['POST'])
@login_required
def edit_cost_center(id):
    name = request.form.get('name')
    display_order = request.form.get('display_order', 0)
    
    db_session = db.get_session()
    try:
        center = db_session.query(CostCenter).get(id)
        if not center:
            flash('مركز التكلفة غير موجود', 'danger')
        else:
            center.name = name
            center.display_order = int(display_order) if display_order else 0
            db_session.commit()
            flash('تم تعديل مركز التكلفة بنجاح', 'center')
    except Exception as e:
        db_session.rollback()
        flash(f'خطأ: {e}', 'danger')
    finally:
        db_session.close()
    return redirect(url_for('accounting.list_cost_centers'))

@accounting_bp.route('/cost_centers/<int:id>/delete', methods=['POST'])
@login_required
def delete_cost_center(id):
    db_session = db.get_session()
    try:
        center = db_session.query(CostCenter).get(id)
        if center:
            db_session.delete(center)
            db_session.commit()
            flash('تم حذف مركز التكلفة بنجاح', 'center')
    except Exception as e:
        db_session.rollback()
        flash(f'خطأ: {e}', 'danger')
    finally:
        db_session.close()
    return redirect(url_for('accounting.list_cost_centers'))
