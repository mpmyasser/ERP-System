from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from core.db_manager import DBManager
from core.commercial_models import Partner, Invoice, InvoiceItem
from core.accounting_models import Account, JournalEntry, JournalItem
from core.production_models import Warehouse, Product, InventoryTransaction
from app.routes.auth import login_required
from datetime import datetime

commercial_bp = Blueprint('commercial', __name__)
db = DBManager()

@commercial_bp.route('/opening-balances')
@login_required
def opening_balances():
    session = db.get_session()
    try:
        accounts = session.query(Account).filter_by(is_active=1).all()
        products = session.query(Product).all()
        warehouses = session.query(Warehouse).all()
        return render_template('commercial/opening_balances.html', 
                               accounts=accounts, 
                               products=products, 
                               warehouses=warehouses)
    finally:
        session.close()

@commercial_bp.route('/opening-balances/save-accounts', methods=['POST'])

@login_required
def save_opening_accounts():
    session = db.get_session()
    try:
        acc_ids = request.form.getlist('account_id[]')
        debits = request.form.getlist('debit[]')
        credits = request.form.getlist('credit[]')
        notes = request.form.getlist('note[]')
        
        # Create Opening Journal Entry
        entry = JournalEntry(
            date=datetime.now().date(),
            description="قيد أرصدة أول المدة - مالي",
            status='Posted'
        )
        session.add(entry)
        session.flush()
        
        for i in range(len(acc_ids)):
            if not acc_ids[i]: continue
            d = float(debits[i] or 0)
            c = float(credits[i] or 0)
            if d == 0 and c == 0: continue
            
            item = JournalItem(
                journal_entry_id=entry.id,
                account_id=acc_ids[i],
                debit=d,
                credit=c,
                description=notes[i] or "رصيد أول المدة"
            )
            session.add(item)
            
        session.commit()
        flash('تم حفظ أرصدة الحسابات المالية بنجاح', 'center')
    except Exception as e:
        session.rollback()
        flash(f'خطأ أثناء الحفظ: {e}', 'danger')
    finally:
        session.close()
    return redirect(url_for('commercial.opening_balances'))

@commercial_bp.route('/opening-balances/save-stock', methods=['POST'])
@login_required
def save_opening_stock():
    session = db.get_session()
    try:
        wh_ids = request.form.getlist('warehouse_id[]')
        prod_ids = request.form.getlist('product_id[]')
        qtys = request.form.getlist('qty[]')
        costs = request.form.getlist('cost[]')
        
        for i in range(len(wh_ids)):
            if not prod_ids[i]: continue
            q = float(qtys[i] or 0)
            c = float(costs[i] or 0)
            if q == 0: continue
            
            # Record inventory transaction
            trans = InventoryTransaction(
                product_id=prod_ids[i],
                warehouse_id=wh_ids[i],
                transaction_type='In',
                quantity=q,
                unit_cost=c,
                reference='Opening Balance',
                date=datetime.now().date()
            )
            session.add(trans)
            
        session.commit()
        flash('تم حفظ أرصدة المخازن بنجاح', 'center')
    except Exception as e:
        session.rollback()
        flash(f'خطأ أثناء الحفظ: {e}', 'danger')
    finally:
        session.close()
    return redirect(url_for('commercial.opening_balances'))

@commercial_bp.route('/partners/add', methods=['POST'])
@login_required
def add_partner():
    session = db.get_session()
    try:
        name = request.form.get('name')
        type = request.form.get('type')
        phone = request.form.get('phone')
        address = request.form.get('address')
        
        # In a real scenario, we might want to create a COA account for this partner automatically
        # For now, just save the partner
        new_partner = Partner(
            name=name,
            type=type,
            phone=phone,
            address=address,
            is_active=True
        )
        session.add(new_partner)
        session.commit()
        flash('تم إضافة الشريك بنجاح', 'center')
    except Exception as e:
        session.rollback()
        flash(f'خطأ: {e}', 'danger')
    finally:
        session.close()
    return redirect(url_for('commercial.list_partners'))

@commercial_bp.route('/partners')
@login_required
def list_partners():
    session = db.get_session()
    try:
        partners = session.query(Partner).all()
        return render_template('commercial/partners.html', partners=partners)
    finally:
        session.close()

@commercial_bp.route('/partners/import', methods=['GET', 'POST'])
@login_required
def import_partners():
    session = db.get_session()
    try:
        if request.method == 'POST':
            account_ids = request.form.getlist('account_ids[]')
            partner_types = request.form.getlist('partner_types[]')
            
            imported = 0
            skipped = 0
            
            for i, account_id in enumerate(account_ids):
                account_id = int(account_id)
                partner_type = partner_types[i] if i < len(partner_types) else 'Customer'
                
                # Check if partner already exists for this account
                existing = session.query(Partner).filter_by(account_id=account_id).first()
                if existing:
                    skipped += 1
                    continue
                
                account = session.query(Account).get(account_id)
                if not account:
                    continue
                
                # Create partner
                new_partner = Partner(
                    name=account.name,
                    type=partner_type,
                    account_id=account_id,
                    is_active=True
                )
                session.add(new_partner)
                imported += 1
            
            session.commit()
            if imported > 0:
                flash(f'تم استيراد {imported} شريك بنجاح', 'center')
            if skipped > 0:
                flash(f'تم تخطي {skipped} حساب (موجود بالفعل)', 'info')
            if imported == 0 and skipped == 0:
                flash('لم يتم استيراد أي حسابات', 'warning')
            
            return redirect(url_for('commercial.list_partners'))
        
        # GET - Show import form
        # Get accounts that are not yet linked to partners
        existing_partner_account_ids = [p.account_id for p in session.query(Partner).filter(Partner.account_id.isnot(None)).all()]
        
        # Get all active accounts (you might want to filter by type or name pattern)
        all_accounts = session.query(Account).filter_by(is_active=1).order_by(Account.code).all()
        
        # Filter accounts that could be customers/suppliers (typically under specific account codes)
        # Or show all accounts and let user choose
        accounts = [acc for acc in all_accounts if acc.id not in existing_partner_account_ids]
        
        return render_template('commercial/import_partners.html', accounts=accounts)
    except Exception as e:
        session.rollback()
        flash(f'خطأ أثناء الاستيراد: {e}', 'danger')
        return redirect(url_for('commercial.list_partners'))
    finally:
        session.close()

@commercial_bp.route('/invoices/<type>/new', methods=['GET', 'POST'])
@login_required
def new_invoice(type):
    session = db.get_session()
    if request.method == 'POST':
        try:
            invoice_number = request.form.get('invoice_number')
            date_str = request.form.get('date')
            partner_id = request.form.get('partner_id')
            warehouse_id = request.form.get('warehouse_id')
            notes = request.form.get('notes')
            
            prod_ids = request.form.getlist('product_id[]')
            qtys = request.form.getlist('quantity[]')
            prices = request.form.getlist('unit_price[]')
            
            # 1. Create Invoice object
            inv = Invoice(
                type=type,
                invoice_number=invoice_number,
                date=datetime.strptime(date_str, '%Y-%m-%d').date(),
                partner_id=partner_id,
                warehouse_id=warehouse_id,
                status='Posted',
                notes=notes
            )
            session.add(inv)
            session.flush()
            
            total_before_tax = 0
            for i in range(len(prod_ids)):
                if not prod_ids[i]: continue
                q = float(qtys[i] or 0)
                p = float(prices[i] or 0)
                line_total = q * p
                total_before_tax += line_total
                
                item = InvoiceItem(
                    invoice_id=inv.id,
                    product_id=prod_ids[i],
                    quantity=q,
                    unit_price=p,
                    total=line_total
                )
                session.add(item)
                
                # 2. Update Stock (Inventory Transaction)
                trans_type = 'In' if type == 'Purchase' else 'Out'
                stock_trans = InventoryTransaction(
                    product_id=prod_ids[i],
                    warehouse_id=warehouse_id,
                    transaction_type=trans_type,
                    quantity=q,
                    unit_cost=p, # For purchase it's cost, for sales it's tracking revenue side
                    reference=f"Invoice {invoice_number}",
                    date=inv.date
                )
                session.add(stock_trans)
                
            tax_amount = total_before_tax * 0.14
            net_amount = total_before_tax + tax_amount
            
            inv.total_amount = total_before_tax
            inv.tax_amount = tax_amount
            inv.net_amount = net_amount
            
            # 3. Automated Journal Entry
            partner = session.query(Partner).get(partner_id)
            # Find relevant accounts (In a real ERP, these are defined in settings)
            # For now, let's assume default accounts for Sales and Purchases
            sales_acc = session.query(Account).filter(Account.name.like('%مبيعات%')).first()
            purchase_acc = session.query(Account).filter(Account.name.like('%مشتريات%')).first()
            vat_acc = session.query(Account).filter(Account.name.like('%قيمة مضافة%')).first()
            
            # Partner account
            partner_acc_id = partner.account_id
            if not partner_acc_id:
                # Fallback to general AR/AP if specific partner account is missing
                fallback_name = 'مدينون' if type == 'Sales' else 'دائنون'
                fallback_acc = session.query(Account).filter(Account.name.like(f'%{fallback_name}%')).first()
                partner_acc_id = fallback_acc.id if fallback_acc else 1 # Default to 1 if everything fails
            
            entry = JournalEntry(
                date=inv.date,
                description=f"فاتورة {('مشتريات' if type == 'Purchase' else 'مبيعات')} رقم {invoice_number}",
                status='Posted'
            )
            session.add(entry)
            session.flush()
            
            if type == 'Sales':
                # Sales Entry:
                # Debit: Partner (Net)
                # Credit: Sales (Total before tax)
                # Credit: VAT (Tax)
                session.add(JournalItem(journal_entry_id=entry.id, account_id=partner_acc_id, debit=net_amount, credit=0, description=notes))
                session.add(JournalItem(journal_entry_id=entry.id, account_id=sales_acc.id if sales_acc else 1, debit=0, credit=total_before_tax, description=notes))
                session.add(JournalItem(journal_entry_id=entry.id, account_id=vat_acc.id if vat_acc else 1, debit=0, credit=tax_amount, description=notes))
            else:
                # Purchase Entry:
                # Debit: Purchase/Inventory (Total before tax)
                # Debit: VAT (Tax)
                # Credit: Partner (Net)
                session.add(JournalItem(journal_entry_id=entry.id, account_id=purchase_acc.id if purchase_acc else 1, debit=total_before_tax, credit=0, description=notes))
                session.add(JournalItem(journal_entry_id=entry.id, account_id=vat_acc.id if vat_acc else 1, debit=tax_amount, credit=0, description=notes))
                session.add(JournalItem(journal_entry_id=entry.id, account_id=partner_acc_id, debit=0, credit=net_amount, description=notes))
            
            inv.journal_entry_id = entry.id
            session.commit()
            flash('تم حفظ الفاتورة وترحيلها للمحاسبة والمخازن بنجاح', 'center')
            return redirect(url_for('commercial.list_invoices', type=type))
            
        except Exception as e:
            session.rollback()
            flash(f'خطأ أثناء حفظ الفاتورة: {e}', 'danger')
            
    try:
        partners = session.query(Partner).filter_by(type=type if type != 'Both' else Partner.type).all()
        warehouses = session.query(Warehouse).all()
        # Product model needs to be converted to dict for frontend
        products_raw = session.query(Product).all()
        products = []
        for p in products_raw:
            products.append({
                'id': p.id,
                'name': p.name,
                'sell_price': 0, # Add price logic if available in model later
                'cost_price': 0
            })
            
        return render_template('commercial/invoice_form.html', 
                               type=type, 
                               partners=partners, 
                               warehouses=warehouses, 
                               products=products,
                               today=datetime.now().strftime('%Y-%m-%d'))
    finally:
        session.close()

@commercial_bp.route('/invoices/<type>')

@login_required
def list_invoices(type):
    session = db.get_session()
    try:
        invoices = session.query(Invoice).filter_by(type=type).all()
        return render_template('commercial/invoices_list.html', invoices=invoices, type=type)
    finally:
        session.close()
