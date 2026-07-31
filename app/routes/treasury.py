from flask import Blueprint, render_template, request, flash, redirect, url_for, session as flask_session
from core.db_manager import DBManager
from core.treasury_models import CashAccount, BankAccount, CheckRecord, CashTransfer
from core.accounting_models import Account, JournalEntry, JournalItem, CostCenter
from core.database_models import Loan, Employee, Department
from core.auth_manager import AuthManager
from app.routes.auth import login_required
from sqlalchemy.orm import joinedload
from datetime import datetime

auth_manager = AuthManager()

treasury_bp = Blueprint('treasury', __name__)
db = DBManager()

@treasury_bp.route('/dashboard')
@login_required
def dashboard():
    db_session = db.get_session()
    user_id = flask_session.get('user_id')
    is_admin = flask_session.get('is_admin', False)
    
    try:
        user = auth_manager.get_user_by_id(user_id)
        # Filter cash accounts based on user access
        if is_admin:
            # Admins see all cash accounts
            cash_accounts = db_session.query(CashAccount).options(joinedload(CashAccount.account)).filter_by(is_active=True).order_by(CashAccount.display_order).all()
        else:
            # Regular users see only their assigned cash accounts via the relationship
            # Must refetch to ensure attached session and eager load 'account'
            accessible_ids = [c.id for c in user.accessible_cash_accounts]
            if accessible_ids:
                cash_accounts = db_session.query(CashAccount).options(joinedload(CashAccount.account))\
                    .filter(CashAccount.id.in_(accessible_ids), CashAccount.is_active == True)\
                    .order_by(CashAccount.display_order).all()
            else:
                cash_accounts = []
        
        # Separate accounts by type for better UI organization
        general_accounts = [c for c in cash_accounts if c.is_general()]
        subsidiary_accounts = [c for c in cash_accounts if c.is_subsidiary()]
        
        bank_accounts = db_session.query(BankAccount).options(joinedload(BankAccount.account)).order_by(BankAccount.display_order).all()
        # Count pending loans
        pending_loans_count = db_session.query(Loan).filter_by(status='Pending').count()
        # Fetching accounts for the 'Add' modals
        accounts = db_session.query(Account).filter_by(is_active=1).all()
        # Get users for assignment
        users = auth_manager.get_all_users()
        
        return render_template('treasury/dashboard.html', 
                               cash_accounts=cash_accounts,
                               general_accounts=general_accounts,
                               subsidiary_accounts=subsidiary_accounts,
                               bank_accounts=bank_accounts,
                               accounts=accounts,
                               users=users,
                               pending_loans_count=pending_loans_count,
                               is_admin=is_admin,
                               current_user_id=user_id)
    finally:
        db_session.close()

@treasury_bp.route('/loans/pending')
@login_required
def list_pending_loans():
    db_session = db.get_session()
    user_id = flask_session.get('user_id')
    is_admin = flask_session.get('is_admin', False)
    
    try:
        # Get Filter Parameters
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        department_ids = request.args.getlist('department_ids')
        
        query = db_session.query(Loan).join(Loan.employee).filter(Loan.status == 'Pending')
        
        if date_from:
            from core.utils.helpers import parse_date_compact
            parsed_date_from = parse_date_compact(date_from)
            if parsed_date_from:
                query = query.filter(Loan.date >= parsed_date_from)
            
        if date_to:
            from core.utils.helpers import parse_date_compact
            parsed_date_to = parse_date_compact(date_to)
            if parsed_date_to:
                query = query.filter(Loan.date <= parsed_date_to)
        if department_ids:
            # Convert string ids to integers if needed, though SQLAlchemy usually handles strings in in_() decently
            # for safety we map to int
            dep_ids = [int(x) for x in department_ids if x.isdigit()]
            if dep_ids:
                query = query.filter(Employee.department_id.in_(dep_ids))
            
        # Sorting Logic (hierarchical: employee code is always primary ASC)
        sort_by = request.args.get('sort', 'date')
        order = request.args.get('order', 'asc')

        if sort_by == 'department':
            query = query.join(Employee.department)
            secondary_order = Department.name.desc() if order == 'desc' else Department.name.asc()
        elif sort_by == 'amount':
            secondary_order = Loan.amount.desc() if order == 'desc' else Loan.amount.asc()
        elif sort_by == 'type':
            secondary_order = Loan.type.desc() if order == 'desc' else Loan.type.asc()
        elif sort_by == 'code':
            # Primary code ordering is fixed; keep date as secondary when code is selected.
            secondary_order = Loan.date.asc()
        else:
            # Default secondary sort by date (ASC)
            secondary_order = Loan.date.asc()

        query = query.order_by(Employee.code.asc(), secondary_order, Loan.id.asc())
            
        pending_loans = query.all()
        
        # Get Departments for filter
        departments = db_session.query(Department).order_by(Department.name).all()
        
        if is_admin:
            cash_accounts = db_session.query(CashAccount).options(joinedload(CashAccount.account)).filter_by(is_active=True).all()
        else:
            user = auth_manager.get_user_by_id(user_id)
            # Fix: Reload accounts in current session to avoid DetachedInstanceError
            accessible_ids = [c.id for c in user.accessible_cash_accounts]
            if accessible_ids:
                cash_accounts = db_session.query(CashAccount).options(joinedload(CashAccount.account))\
                    .filter(CashAccount.id.in_(accessible_ids), CashAccount.is_active == True).all()
            else:
                cash_accounts = []
        
        bank_accounts = db_session.query(BankAccount).options(joinedload(BankAccount.account)).all()
        cost_centers = db_session.query(CostCenter).all()
        return render_template('treasury/pending_loans.html', 
                                loans=pending_loans,
                                cash_accounts=cash_accounts,
                                bank_accounts=bank_accounts,
                                cost_centers=cost_centers,
                                departments=departments,
                                filters={'date_from': date_from, 'date_to': date_to, 'department_id': department_ids})
    finally:
        db_session.close()

@treasury_bp.route('/accounts/add_cash', methods=['POST'])
@login_required
def add_cash_account():
    name = request.form.get('name')
    acc_id = request.form.get('account_id')
    cash_type = request.form.get('type', 'General')
    user_id = request.form.get('user_id')
    display_order = request.form.get('display_order', 0)
    
    db_session = db.get_session()
    is_admin = flask_session.get('is_admin', False)
    
    try:
        # Non-admin users can only create cash accounts assigned to themselves
        if not is_admin:
            user_id = flask_session.get('user_id')
        
        new_c = CashAccount(
            name=name, 
            account_id=acc_id,
            type=cash_type,
            user_id=int(user_id) if user_id else None,
            display_order=int(display_order or 0)
        )
        db_session.add(new_c)
        db_session.commit()
        flash('تم إضافة الخزنة بنجاح', 'center')
    except Exception as e:
        flash(f'خطأ: {e}', 'danger')
    finally:
        db_session.close()
    return redirect(url_for('treasury.dashboard'))

@treasury_bp.route('/accounts/edit_cash/<int:id>', methods=['POST'])
@login_required
def edit_cash_account(id):
    name = request.form.get('name')
    acc_id = request.form.get('account_id')
    cash_type = request.form.get('type', 'General')
    user_id = request.form.get('user_id')
    display_order = request.form.get('display_order', 0)
    
    db_session = db.get_session()
    current_user_id = flask_session.get('user_id')
    is_admin = flask_session.get('is_admin', False)
    
    try:
        acc = db_session.query(CashAccount).options(joinedload(CashAccount.account)).filter(CashAccount.id == id).first()
        if not acc:
            flash('الخزنة غير موجودة', 'danger')
            return redirect(url_for('treasury.dashboard'))
        
        # Check permissions - non-admin can only edit their own cash accounts
        if not is_admin and acc.user_id != current_user_id:
            flash('ليس لديك صلاحية لتعديل هذه الخزنة', 'danger')
            return redirect(url_for('treasury.dashboard'))
        
        acc.name = name
        acc.account_id = acc_id
        acc.type = cash_type
        
        # Only admins can change user assignment
        if is_admin:
            acc.user_id = int(user_id) if user_id else None
        elif not acc.user_id:
            # If no user assigned, assign to current user
            acc.user_id = current_user_id
        
        acc.display_order = int(display_order or 0)
        db_session.commit()
        flash('تم تحديث الخزنة بنجاح', 'center')
    except Exception as e:
        db_session.rollback()
        flash(f'خطأ: {e}', 'danger')
    finally:
        db_session.close()
    return redirect(url_for('treasury.dashboard'))

@treasury_bp.route('/accounts/delete_cash/<int:id>', methods=['POST'])
@login_required
def delete_cash_account(id):
    db_session = db.get_session()
    try:
        acc = db_session.query(CashAccount).filter(CashAccount.id == id).first()
        if acc:
            db_session.delete(acc)
            db_session.commit()
            flash('تم حذف الخزنة بنجاح', 'center')
    except Exception as e:
        flash(f'خطأ: {e}', 'danger')
    finally:
        db_session.close()
    return redirect(url_for('treasury.dashboard'))

@treasury_bp.route('/accounts/add_bank', methods=['POST'])
@login_required
def add_bank_account():
    bank_name = request.form.get('bank_name')
    acc_num = request.form.get('account_number')
    acc_id = request.form.get('account_id')
    display_order = request.form.get('display_order', 0)
    
    db_session = db.get_session()
    try:
        new_b = BankAccount(bank_name=bank_name, account_number=acc_num, account_id=acc_id, display_order=int(display_order or 0))
        db_session.add(new_b)
        db_session.commit()
        flash('تم إضافة حساب البنك بنجاح', 'center')
    except Exception as e:
        flash(f'خطأ: {e}', 'danger')
    finally:
        db_session.close()
    return redirect(url_for('treasury.dashboard'))

@treasury_bp.route('/accounts/edit_bank/<int:id>', methods=['POST'])
@login_required
def edit_bank_account(id):
    bank_name = request.form.get('bank_name')
    acc_num = request.form.get('account_number')
    acc_id = request.form.get('account_id')
    display_order = request.form.get('display_order', 0)
    
    db_session = db.get_session()
    try:
        acc = db_session.query(BankAccount).filter(BankAccount.id == id).first()
        if acc:
            acc.bank_name = bank_name
            acc.account_number = acc_num
            acc.account_id = acc_id
            acc.display_order = int(display_order or 0)
            db_session.commit()
            flash('تم تحديث حساب البنك بنجاح', 'center')
    except Exception as e:
        flash(f'خطأ: {e}', 'danger')
    finally:
        db_session.close()
    return redirect(url_for('treasury.dashboard'))

@treasury_bp.route('/accounts/delete_bank/<int:id>', methods=['POST'])
@login_required
def delete_bank_account(id):
    db_session = db.get_session()
    try:
        acc = db_session.query(BankAccount).filter(BankAccount.id == id).first()
        if acc:
            db_session.delete(acc)
            db_session.commit()
            flash('تم حذف حساب البنك بنجاح', 'center')
    except Exception as e:
        flash(f'خطأ: {e}', 'danger')
    finally:
        db_session.close()
    return redirect(url_for('treasury.dashboard'))

@treasury_bp.route('/vouchers')
@login_required
def list_vouchers():
    db_session = db.get_session()
    try:
        # Fetch entries that look like vouchers (description starts with 'سند')
        entries = db_session.query(JournalEntry).filter(JournalEntry.description.like('سند %')).order_by(JournalEntry.date.desc()).all()
        
        vouchers_data = []
        for e in entries:
            # Simple heuristic: find the cash/bank account in items
            cash_account_names = [ca.name for ca in db_session.query(CashAccount).options(joinedload(CashAccount.account)).all()]
            bank_account_names = [ba.bank_name for ba in db_session.query(BankAccount).options(joinedload(BankAccount.account)).all()]
            main_item = next((i for i in e.items if i.account.name in cash_account_names or i.account.name in bank_account_names), e.items[0] if e.items else None)
            other_item = next((i for i in e.items if i != main_item), e.items[1] if len(e.items)>1 else None)
            
            vouchers_data.append({
                'id': e.id,
                'date': e.date,
                'description': e.description,
                'treasury_name': main_item.account.name if main_item else '?',
                'other_account_name': other_item.account.name if other_item else '?',
                'amount': main_item.debit if main_item and main_item.debit > 0 else (main_item.credit if main_item else 0),
                'status': e.status
            })
            
        return render_template('treasury/vouchers.html', vouchers=vouchers_data)
    finally:
        db_session.close()

@treasury_bp.route('/vouchers/new/<type>', methods=['GET', 'POST'])
@login_required
def new_voucher(type):
    db_session = db.get_session()
    cash_id = request.args.get('cash_id')
    
    if request.method == 'POST':
        date_str = request.form.get('date')
        treasury_src = request.form.get('treasury_acc_id') # e.g., 'cash_1'
        other_acc_id = request.form.get('other_account_id')
        amount = float(request.form.get('amount', 0))
        description = request.form.get('description')
        
        # Determine actual account IDs
        src_type, src_id = treasury_src.split('_')
        main_acc_id = None
        if src_type == 'cash':
            cash_acc = db_session.query(CashAccount).filter(CashAccount.id == src_id).first()
            if cash_acc:
                main_acc_id = cash_acc.account_id
        else:
            bank_acc = db_session.query(BankAccount).filter(BankAccount.id == src_id).first()
            if bank_acc:
                main_acc_id = bank_acc.account_id
            
        try:
            # Create Journal Entry
            entry = JournalEntry(
                date=datetime.strptime(date_str, '%Y-%m-%d').date(),
                description=f"سند {('قبض' if type == 'receipt' else 'صرف')} - {description}",
                status='Posted',
                created_by=flask_session.get('user_id')
            )
            db_session.add(entry)
            db_session.flush()
            
            # Create Items
            main_debit = amount if type == 'receipt' else 0
            main_credit = 0 if type == 'receipt' else amount
            
            other_debit = main_credit
            other_credit = main_debit
            
            # Line 1: Main (Cash/Bank)
            db_session.add(JournalItem(journal_entry_id=entry.id, account_id=main_acc_id, debit=main_debit, credit=main_credit, description=description))
            # Line 2: Other
            db_session.add(JournalItem(journal_entry_id=entry.id, account_id=other_acc_id, debit=other_debit, credit=other_credit, description=description))
            
            db_session.commit()
            flash('تم حفظ السند بنجاح وترحيله للحسابات', 'center')
            return redirect(url_for('treasury.list_vouchers'))
        except Exception as e:
            flash(f'خطأ: {e}', 'danger')
            db_session.rollback()

    user_id = flask_session.get('user_id')
    is_admin = flask_session.get('is_admin', False)
    
    try:
        # Filter cash accounts based on user
        if is_admin:
            cash_accounts = db_session.query(CashAccount).options(joinedload(CashAccount.account)).filter_by(is_active=True).all()
        else:
            cash_accounts = db_session.query(CashAccount).options(joinedload(CashAccount.account)).filter_by(user_id=user_id, is_active=True).all()
        
        selected_cash = None
        if cash_id:
            selected_cash = db_session.query(CashAccount).options(joinedload(CashAccount.account)).filter_by(id=cash_id).first()
        
        bank_accounts = db_session.query(BankAccount).options(joinedload(BankAccount.account)).all()
        accounts = db_session.query(Account).filter_by(is_active=1).all()
        return render_template('treasury/voucher_form.html', 
                               type=type, 
                               cash_accounts=cash_accounts, 
                               bank_accounts=bank_accounts, 
                               accounts=accounts,
                               selected_cash=selected_cash)
    finally:
        db_session.close()

@treasury_bp.route('/transfer', methods=['GET', 'POST'])
@login_required
def cash_transfer():
    db_session = db.get_session()
    from_account = request.args.get('from_account')
    
    if request.method == 'POST':
        date_str = request.form.get('date')
        from_cash_id = request.form.get('from_cash_id')
        to_cash_id = request.form.get('to_cash_id')
        amount = float(request.form.get('amount', 0))
        description = request.form.get('description', '')
        
        if not from_cash_id or not to_cash_id:
            flash('يرجى تحديد الخزينة المصدر والخزينة المستلمة', 'danger')
            return redirect(url_for('treasury.cash_transfer'))
        
        if from_cash_id == to_cash_id:
            flash('لا يمكن التحويل من الخزينة لنفسها', 'danger')
            return redirect(url_for('treasury.cash_transfer'))
        
        user_id = flask_session.get('user_id')
        is_admin = flask_session.get('is_admin', False)
        
        try:
            from_cash = db_session.query(CashAccount).filter(CashAccount.id == from_cash_id).first()
            to_cash = db_session.query(CashAccount).filter(CashAccount.id == to_cash_id).first()
            
            if not from_cash or not to_cash:
                flash('الخزينة غير موجودة', 'danger')
                return redirect(url_for('treasury.cash_transfer'))
            
            # Validate transfer direction: Only General → Subsidiary allowed
            if not is_admin:
                if from_cash.is_subsidiary():
                    flash('لا يمكن التحويل من خزينة فرعية. التحويلات تتم من الخزائن العمومية فقط', 'danger')
                    return redirect(url_for('treasury.cash_transfer'))
                
                if to_cash.is_general():
                    flash('لا يمكن التحويل إلى خزينة عمومية. التحويلات تتم من الخزائن العمومية إلى الفرعية فقط', 'danger')
                    return redirect(url_for('treasury.cash_transfer'))
                
                if from_cash.parent_cash_id != to_cash.parent_cash_id and to_cash.parent_cash_id != from_cash.id:
                    flash('يمكن التحويل فقط من الخزينة العمومية إلى خزائنها الفرعية المباشرة', 'danger')
                    return redirect(url_for('treasury.cash_transfer'))
            
            # Check permissions - non-admin can only transfer from their assigned cash accounts
            if not is_admin and from_cash.user_id != user_id:
                flash('ليس لديك صلاحية للتحويل من هذه الخزينة', 'danger')
                return redirect(url_for('treasury.cash_transfer'))
            
            from_account_id = from_cash.account_id
            to_account_id = to_cash.account_id
            
            # Create Journal Entry for transfer
            transfer_desc = f"تحويل من {from_cash.name} إلى {to_cash.name}"
            if description:
                transfer_desc += f" - {description}"
            
            entry = JournalEntry(
                date=datetime.strptime(date_str, '%Y-%m-%d').date(),
                description=f"سند تحويل - {transfer_desc}",
                status='Posted',
                created_by=flask_session.get('user_id')
            )
            db_session.add(entry)
            db_session.flush()
            
            # Line 1: From Cash Account - Credit (Money out)
            db_session.add(JournalItem(
                journal_entry_id=entry.id,
                account_id=from_account_id,
                debit=0,
                credit=amount,
                description=transfer_desc
            ))
            
            # Line 2: To Cash Account - Debit (Money in)
            db_session.add(JournalItem(
                journal_entry_id=entry.id,
                account_id=to_account_id,
                debit=amount,
                credit=0,
                description=transfer_desc
            ))
            
            # Create CashTransfer record
            transfer = CashTransfer(
                from_cash_id=int(from_cash_id),
                to_cash_id=int(to_cash_id),
                amount=amount,
                transfer_date=datetime.strptime(date_str, '%Y-%m-%d').date(),
                description=description,
                status='Pending',
                journal_entry_id=entry.id
            )
            db_session.add(transfer)
            
            db_session.commit()
            flash(f'تم حفظ تحويل {amount} من {from_cash.name} إلى {to_cash.name} بنجاح - في انتظار الاستلام', 'center')
            return redirect(url_for('treasury.dashboard'))
        except Exception as e:
            db_session.rollback()
            flash(f'خطأ: {e}', 'danger')
    
    user_id = flask_session.get('user_id')
    is_admin = flask_session.get('is_admin', False)
    
    try:
        # Filter cash accounts based on user
        if is_admin:
            # Admins can transfer from/to any cash account
            cash_accounts = db_session.query(CashAccount).options(joinedload(CashAccount.account)).filter_by(is_active=True).order_by(CashAccount.display_order).all()
        else:
            # Regular users can only transfer from their assigned cash accounts
            cash_accounts = db_session.query(CashAccount).options(joinedload(CashAccount.account)).filter_by(user_id=user_id, is_active=True).order_by(CashAccount.display_order).all()
        
        selected_account = None
        if from_account:
            selected_account = db_session.query(CashAccount).options(joinedload(CashAccount.account)).filter(CashAccount.id == from_account).first()
        
        return render_template('treasury/cash_transfer.html', 
                               cash_accounts=cash_accounts, 
                               selected_account=selected_account,
                               today=datetime.now().strftime('%Y-%m-%d'))
    finally:
        db_session.close()

@treasury_bp.route('/transfers/receive')
@login_required
def receive_transfers():
    """صفحة استلام التحويلات للخزينة الفرعية"""
    db_session = db.get_session()
    user_id = flask_session.get('user_id')
    is_admin = flask_session.get('is_admin', False)
    
    try:
        # Get user's cash accounts
        if is_admin:
            # Admins see all pending transfers
            pending_transfers = db_session.query(CashTransfer).options(
                joinedload(CashTransfer.from_cash),
                joinedload(CashTransfer.to_cash)
            ).filter_by(status='Pending').order_by(CashTransfer.transfer_date.desc()).all()
        else:
            # Regular users see only transfers to their assigned subsidiary cash accounts
            user_subsidiary_ids = [
                c.id for c in db_session.query(CashAccount).filter_by(user_id=user_id, is_active=True).all() 
                if c.is_subsidiary()
            ]
            pending_transfers = db_session.query(CashTransfer).options(
                joinedload(CashTransfer.from_cash),
                joinedload(CashTransfer.to_cash)
            ).filter(
                CashTransfer.status == 'Pending',
                CashTransfer.to_cash_id.in_(user_subsidiary_ids)
            ).order_by(CashTransfer.transfer_date.desc()).all()
        
        # Group transfers by source account
        transfers_by_source = {}
        for transfer in pending_transfers:
            source_name = transfer.from_cash.name
            if source_name not in transfers_by_source:
                transfers_by_source[source_name] = {
                    'from_account': transfer.from_cash,
                    'transfers': [],
                    'total_amount': 0
                }
            transfers_by_source[source_name]['transfers'].append(transfer)
            transfers_by_source[source_name]['total_amount'] += transfer.amount
        
        # Calculate statistics
        total_pending_amount = sum(t.amount for t in pending_transfers)
        received_count = len([t for t in pending_transfers if t.status == 'Received'])
        
        return render_template('treasury/receive_transfers.html', 
                             transfers=pending_transfers,
                             transfers_by_source=transfers_by_source,
                             total_pending_amount=total_pending_amount,
                             pending_count=len(pending_transfers),
                             received_count=received_count)
    finally:
        db_session.close()

@treasury_bp.route('/transfers/<int:transfer_id>/receive', methods=['POST'])
@login_required
def confirm_receive_transfer(transfer_id):
    """تأكيد استلام التحويل"""
    db_session = db.get_session()
    user_id = flask_session.get('user_id')
    is_admin = flask_session.get('is_admin', False)
    
    try:
        transfer = db_session.query(CashTransfer).options(
            joinedload(CashTransfer.to_cash),
            joinedload(CashTransfer.from_cash)
        ).get(transfer_id)
        
        if not transfer:
            flash('التحويل غير موجود', 'danger')
            return redirect(url_for('treasury.receive_transfers'))
        
        # Validate transfer is TO a subsidiary account
        if not transfer.to_cash.is_subsidiary():
            flash('هذا التحويل ليس موجهاً لخزينة فرعية', 'danger')
            return redirect(url_for('treasury.receive_transfers'))
        
        # Check permissions - user can only receive transfers to their assigned subsidiary cash accounts
        if not is_admin:
            if transfer.to_cash.user_id != user_id:
                flash('ليس لديك صلاحية لاستلام هذا التحويل', 'danger')
                return redirect(url_for('treasury.receive_transfers'))
        
        if transfer.status != 'Pending':
            flash('تم استلام هذا التحويل مسبقاً', 'warning')
            return redirect(url_for('treasury.receive_transfers'))
        
        transfer.status = 'Received'
        transfer.received_date = datetime.now().date()
        transfer.received_by = user_id
        
        db_session.commit()
        
        flash(f'✅ تم استلام التحويل من {transfer.from_cash.name} إلى {transfer.to_cash.name} بقيمة {transfer.amount} بنجاح', 'center')
        return redirect(url_for('treasury.receive_transfers'))
    except Exception as e:
        db_session.rollback()
        flash(f'❌ خطأ: {e}', 'danger')
        return redirect(url_for('treasury.receive_transfers'))
    finally:
        db_session.close()

@treasury_bp.route('/transfers/report')
@login_required
def transfers_report():
    """تقرير حركة التحويلات"""
    db_session = db.get_session()
    user_id = flask_session.get('user_id')
    is_admin = flask_session.get('is_admin', False)
    
    try:
        # Get filter parameters
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        cash_id = request.args.get('cash_id')
        status = request.args.get('status', 'all')
        direction = request.args.get('direction', 'all')
        
        query = db_session.query(CashTransfer).options(
            joinedload(CashTransfer.from_cash),
            joinedload(CashTransfer.to_cash)
        )
        
        if from_date:
            query = query.filter(CashTransfer.transfer_date >= datetime.strptime(from_date, '%Y-%m-%d').date())
        if to_date:
            query = query.filter(CashTransfer.transfer_date <= datetime.strptime(to_date, '%Y-%m-%d').date())
        if cash_id:
            query = query.filter((CashTransfer.from_cash_id == cash_id) | (CashTransfer.to_cash_id == cash_id))
        if status != 'all':
            query = query.filter_by(status=status)
        
        transfers = query.order_by(CashTransfer.transfer_date.desc()).all()
        
        # Filter based on direction and user role
        if not is_admin:
            if direction == 'from':
                # Show transfers FROM user's general accounts
                user_general_ids = [c.id for c in db_session.query(CashAccount).options(joinedload(CashAccount.account)).filter_by(user_id=user_id, is_active=True).all() if c.is_general()]
                transfers = [t for t in transfers if t.from_cash_id in user_general_ids]
            elif direction == 'to':
                # Show transfers TO user's subsidiary accounts
                user_subsidiary_ids = [c.id for c in db_session.query(CashAccount).options(joinedload(CashAccount.account)).filter_by(user_id=user_id, is_active=True).all() if c.is_subsidiary()]
                transfers = [t for t in transfers if t.to_cash_id in user_subsidiary_ids]
            else:
                # Show all transfers related to user's accounts
                user_ids = [c.id for c in db_session.query(CashAccount).options(joinedload(CashAccount.account)).filter_by(user_id=user_id, is_active=True).all()]
                transfers = [t for t in transfers if t.from_cash_id in user_ids or t.to_cash_id in user_ids]
        
        cash_accounts = db_session.query(CashAccount).options(joinedload(CashAccount.account)).filter_by(is_active=True).order_by(CashAccount.display_order).all()
        
        # Calculate totals
        total_amount = sum(t.amount for t in transfers)
        pending_count = len([t for t in transfers if t.status == 'Pending'])
        received_count = len([t for t in transfers if t.status == 'Received'])
        
        return render_template('treasury/transfers_report.html',
                             transfers=transfers,
                             cash_accounts=cash_accounts,
                             total_amount=total_amount,
                             pending_count=pending_count,
                             received_count=received_count,
                             from_date=from_date or '',
                             to_date=to_date or '',
                             selected_cash_id=cash_id or '',
                             selected_status=status)
    finally:
        db_session.close()

@treasury_bp.route('/checks')
@login_required
def list_checks():
    db_session = db.get_session()
    try:
        checks = db_session.query(CheckRecord).order_by(CheckRecord.due_date.asc()).all()
        return render_template('treasury/checks.html', checks=checks)
    finally:
        db_session.close()
@treasury_bp.route('/vouchers/<int:entry_id>/delete', methods=['POST'])
@login_required
def delete_voucher(entry_id):
    db_session = db.get_session()
    try:
        entry = db_session.query(JournalEntry).filter_by(id=entry_id).first()
        if entry:
            db_session.delete(entry)
            db_session.commit()
            flash('تم حذف السند بنجاح', 'center')
        else:
            flash('السند غير موجود', 'danger')
    except Exception as e:
        db_session.rollback()
        flash(f'خطأ أثناء الحذف: {e}', 'danger')
    finally:
        db_session.close()
    return redirect(url_for('treasury.list_vouchers'))

@treasury_bp.route('/vouchers/<int:entry_id>/print')
@login_required
def print_voucher(entry_id):
    db_session = db.get_session()
    try:
        e = db_session.query(JournalEntry).filter_by(id=entry_id).first()
        if not e:
            flash('السند غير موجود', 'danger')
            return redirect(url_for('treasury.list_vouchers'))
        
        # Determine main and other accounts
        from core.treasury_models import CashAccount, BankAccount
        cash_acc_names = [ca.name for ca in db_session.query(CashAccount).options(joinedload(CashAccount.account)).all()]
        bank_acc_names = [ba.bank_name for ba in db_session.query(BankAccount).options(joinedload(BankAccount.account)).all()]
        
        main_item = next((i for i in e.items if i.account.name in cash_acc_names or i.account.name in bank_acc_names), e.items[0] if e.items else None)
        other_item = next((i for i in e.items if i != main_item), e.items[1] if len(e.items)>1 else None)
        
        voucher = {
            'id': e.id,
            'date': e.date,
            'description': e.description,
            'amount': main_item.debit if main_item and main_item.debit > 0 else (main_item.credit if main_item else 0),
            'main_account': main_item.account.name if main_item else '?',
            'other_account': other_item.account.name if other_item else '?',
            'type': 'قبض' if 'قبض' in e.description else 'صرف',
            'created_by': e.created_by
        }
        
        return render_template('treasury/voucher_print.html', voucher=voucher)
    finally:
        db_session.close()

@treasury_bp.route('/loans/<int:loan_id>/disburse', methods=['POST'])
@login_required
def disburse_loan(loan_id):
    db_session = db.get_session()
    try:
        loan = db_session.query(Loan).get(loan_id)
        if not loan or loan.status != 'Pending':
            flash('السلفة غير موجودة أو تم التعامل معها مسبقاً', 'danger')
            return redirect(url_for('treasury.list_pending_loans'))
            
        treasury_src = request.form.get('treasury_acc_id')
        cost_center_id = request.form.get('cost_center_id')
        
        # Get Cost Center Name if selected
        cc_obj = None
        if cost_center_id:
            cc_obj = db_session.query(CostCenter).get(cost_center_id)
        
        cost_center_name = cc_obj.name if cc_obj else ''
        
        # Determine actual account ID
        src_type, src_id = treasury_src.split('_')
        main_acc_id = None
        if src_type == 'cash':
            cash_acc = db_session.query(CashAccount).filter(CashAccount.id == src_id).first()
            if cash_acc:
                main_acc_id = cash_acc.account_id
        else:
            bank_acc = db_session.query(BankAccount).filter(BankAccount.id == src_id).first()
            if bank_acc:
                main_acc_id = bank_acc.account_id
            
        # Create Journal Entry (Voucher)
        description = f"صرف سلفة للموظف {loan.employee.name} ({loan.employee.code})"
        if cost_center_name:
            description += f" - مركز تكلفة: {cost_center_name}"
            
        entry = JournalEntry(
            date=datetime.now().date(),
            description=f"سند صرف سلفة - {description}",
            status='Posted',
            created_by=flask_session.get('user_id')
        )
        db_session.add(entry)
        db_session.flush()
        
        # Line 1: Main (Cash/Bank) - Credit (Money out)
        db_session.add(JournalItem(
            journal_entry_id=entry.id, 
            account_id=main_acc_id, 
            debit=0, 
            credit=loan.amount, 
            description=description,
            cost_center=cost_center_name
        ))
        
        # Line 2: Loan/Employee Account - Debit (Asset/Debt increases)
        loans_account = db_session.query(Account).filter(Account.name.like('%سلف%')).first()
        loans_acc_id = loans_account.id if loans_account else main_acc_id 
        
        db_session.add(JournalItem(
            journal_entry_id=entry.id, 
            account_id=loans_acc_id, 
            debit=loan.amount, 
            credit=0, 
            description=description,
            cost_center=cost_center_name
        ))
        
        # Update Loan details
        loan.status = 'Approved'
        loan.cost_center = cost_center_name
        loan.disbursed_at = datetime.now()
        loan.disbursed_by = flask_session.get('user_id')
        
        db_session.commit()
        flash(f'تم صرف السلفة بنجاح للموظف {loan.employee.name} وتوليد سند الصرف رقم #{entry.id}', 'center')
    except Exception as e:
        db_session.rollback()
        flash(f'خطأ أثناء الصرف: {e}', 'danger')
    finally:
        db_session.close()
    return redirect(url_for('treasury.list_pending_loans'))

@treasury_bp.route('/loans/disburse_bulk', methods=['POST'])
@login_required
def disburse_loans_bulk():
    """Bulk disbursement of loans"""
    db_session = db.get_session()
    try:
        loan_ids_str = request.form.get('loan_ids', '')
        if not loan_ids_str:
            flash('لم يتم تحديد أي سلف للصرف', 'warning')
            return redirect(url_for('treasury.list_pending_loans'))
            
        loan_ids = [int(id) for id in loan_ids_str.split(',')]
        
        treasury_src = request.form.get('treasury_acc_id')
        cost_center_id = request.form.get('cost_center_id')
        
        # Get Cost Center Name if selected
        cc_obj = None
        cost_center_name = ''
        if cost_center_id:
            cc_obj = db_session.query(CostCenter).get(cost_center_id)
            cost_center_name = cc_obj.name if cc_obj else ''
            
        # Determine actual account ID
        src_type, src_id = treasury_src.split('_')
        main_acc_id = None
        if src_type == 'cash':
            cash_acc = db_session.query(CashAccount).filter(CashAccount.id == src_id).first()
            if cash_acc:
                main_acc_id = cash_acc.account_id
        else:
            bank_acc = db_session.query(BankAccount).filter(BankAccount.id == src_id).first()
            if bank_acc:
                main_acc_id = bank_acc.account_id
                
        if not main_acc_id:
             flash('خطأ في تحديد حساب الخزينة/البنك', 'danger')
             return redirect(url_for('treasury.list_pending_loans'))

        loans_account = db_session.query(Account).filter(Account.name.like('%سلف%')).first()
        loans_acc_id = loans_account.id if loans_account else main_acc_id 
        
        success_count = 0
        total_amount = 0
        
        for loan_id in loan_ids:
            loan = db_session.query(Loan).get(loan_id)
            if not loan or loan.status != 'Pending':
                continue
                
            # Create Journal Entry (Voucher)
            description = f"صرف سلفة للموظف {loan.employee.name} ({loan.employee.code})"
            if cost_center_name:
                description += f" - مركز تكلفة: {cost_center_name}"
                
            entry = JournalEntry(
                date=datetime.now().date(),
                description=f"سند صرف سلفة - {description}",
                status='Posted',
                created_by=flask_session.get('user_id')
            )
            db_session.add(entry)
            db_session.flush() # To get entry.id
            
            # Line 1: Main (Cash/Bank) - Credit (Money out)
            db_session.add(JournalItem(
                journal_entry_id=entry.id, 
                account_id=main_acc_id, 
                debit=0, 
                credit=loan.amount, 
                description=description,
                cost_center=cost_center_name
            ))
            
            # Line 2: Loan/Employee Account - Debit (Asset/Debt increases)
            db_session.add(JournalItem(
                journal_entry_id=entry.id, 
                account_id=loans_acc_id, 
                debit=loan.amount, 
                credit=0, 
                description=description,
                cost_center=cost_center_name
            ))
            
            loan.status = 'Approved'
            loan.cost_center = cost_center_name
            loan.disbursed_at = datetime.now()
            loan.disbursed_by = flask_session.get('user_id')
            
            success_count += 1
            total_amount += loan.amount
            
        db_session.commit()
        if success_count > 0:
            flash(f'تم اعتماد وصرف {success_count} سلفة بإجمالي {total_amount:,.2f} بنجاح', 'center')
        else:
            flash('لم يتم صرف أي سلفة (ربما تم صرفها مسبقاً)', 'warning')
            
    except Exception as e:
        db_session.rollback()
        flash(f'خطأ أثناء الصرف الجماعي: {e}', 'danger')
    finally:
        db_session.close()
    return redirect(url_for('treasury.list_pending_loans'))
