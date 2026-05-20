from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime
from app.routes.auth import permission_required
import os
import uuid

# FACTORY_DIR needed for admin password file path only
FACTORY_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'حركة التشغيل'
)

# Import via local IDE-friendly wrapper (app/routes/operation_storage.py)
import app.routes.operation_storage as storage

import hmac
import unicodedata

PURGE_CONFIRM_PHRASE = "احذف جميع بيانات القص"

def _normalize_confirmation_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", (value or ""))
    return " ".join(normalized.split())

manufacturing_bp = Blueprint('manufacturing', __name__)

def _get_admin_password():
    # Check inside 'data' directory first (where operation_app stores it)
    path_data = os.path.join(FACTORY_DIR, 'data', 'operation_admin_password.txt')
    if os.path.exists(path_data):
        with open(path_data, 'r', encoding='utf-8') as f:
            return f.read().strip()
            
    # Fallback to direct factory dir
    path_direct = os.path.join(FACTORY_DIR, 'operation_admin_password.txt')
    if os.path.exists(path_direct):
        with open(path_direct, 'r', encoding='utf-8') as f:
            return f.read().strip()
            
    return "admin123"

@manufacturing_bp.route('/')
@permission_required('mfg_cutting_department')
def index():
    return render_template(
        "manufacturing/cuts_entry.html",
        current_time=datetime.now(),
        database_path=str(storage.DB_PATH),
        recent_batches=storage.get_recent_batches(limit=100),
        recent_cut_items=storage.get_recent_cut_items(limit=300, delivered=False),
        dashboard_totals=storage.get_dashboard_totals(pending_only=True),
        factories=storage.list_factories(),
        config={'PURGE_CONFIRM_PHRASE': PURGE_CONFIRM_PHRASE},
    )

@manufacturing_bp.route('/reference')
@permission_required('mfg_items_reference')
def reference_page():
    return render_template("manufacturing/reference.html", current_time=datetime.now())

@manufacturing_bp.route('/factories')
@permission_required('mfg_manufacturers')
def factories_page():
    return render_template("manufacturing/factories.html", current_time=datetime.now())

@manufacturing_bp.route('/pricing')
@permission_required('mfg_manufacturing_prices')
def pricing_page():
    return render_template(
        "manufacturing/pricing.html",
        current_time=datetime.now(),
        factories=storage.list_factories(),
        products=storage.get_reference_items(limit=500),
    )

@manufacturing_bp.route('/factory-payments')
@permission_required('mfg_payments')
def factory_payments_page():
    return render_template("manufacturing/factory_payments.html", current_time=datetime.now(), factories=storage.list_factories())

@manufacturing_bp.route('/manufacturer-accounts')
@permission_required('mfg_factory_accounts')
def manufacturer_accounts_page():
    view = request.args.get("view", "pending")
    grouped_statements = storage.get_accounting_statements(limit=500) if view == "history" else []
    cut_items = [] if view == "history" else storage.get_recent_cut_items(delivered=True, accounted=False)
    return render_template(
        "manufacturing/manufacturer_accounts.html",
        current_time=datetime.now(),
        manufacturer_cut_items=cut_items,
        grouped_statements=grouped_statements,
        factories=storage.list_factories(),
        current_view=view,
    )

@manufacturing_bp.route('/receiving')
@permission_required('mfg_receive_cuts')
def receiving_page():
    factory_code = request.args.get("factory_code", "")
    return render_template(
        "manufacturing/receiving.html",
        current_time=datetime.now(),
        factories=storage.list_factories_with_items(),
        items=storage.get_items_for_receiving(factory_code=factory_code) if factory_code else [],
        selected_factory=factory_code
    )

@manufacturing_bp.route('/warehouse')
@permission_required('mfg_packing_merging')
def warehouse_page():
    return render_template("manufacturing/warehouse.html", current_time=datetime.now(), pending_items=storage.get_pending_packing_items())

@manufacturing_bp.route('/finished-stock')
@permission_required('mfg_finished_goods_warehouse')
def finished_stock_page():
    return render_template("manufacturing/finished_stock.html", current_time=datetime.now(), stock=storage.get_finished_stock())

@manufacturing_bp.route('/print-payment/<int:payment_id>')
def print_payment_receipt(payment_id):
    try:
        receipt_data = storage.get_payment_receipt_data(payment_id)
        return render_template("manufacturing/payment_receipt.html", receipt=receipt_data)
    except Exception as e:
        return str(e), 404

@manufacturing_bp.route('/accounting-statement/<accounting_id>')
def print_accounting_statement(accounting_id):
    try:
        context = storage.get_accounting_statement_details(accounting_id)
        items = context["items"]
        total_qty = sum(float(i.get("quantity") or 0) for i in items)
        total_amount = sum((float(i.get("quantity") or 0) / 12.0) * float(i.get("manufacturing_price") or 0) for i in items)
        return render_template(
            "manufacturing/accounting_statement_receipt.html",
            accounting_id=accounting_id, factory_name=context["factory_name"],
            factory_code=context["factory_code"], accounted_date=context["accounted_date"],
            items=items, total_qty=total_qty, total_amount=total_amount,
            deduction=context["deduction"], previous_balance=context["previous_balance"],
            footer_note=storage.get_setting("statement_footer_note", ""),
            current_time=datetime.now().strftime("%d/%m/%Y %I:%M %p")
        )
    except Exception as e:
        return str(e), 500

# --- Reference API ---
@manufacturing_bp.route('/api/reference-list')
@permission_required('mfg_items_reference')
def api_reference_list():
    return jsonify({"items": storage.get_reference_items()})

@manufacturing_bp.route('/api/reference/add', methods=['POST'])
@permission_required('mfg_items_reference')
def api_reference_add():
    payload = request.get_json() or {}
    try:
        storage.add_reference_item(payload.get("code"), payload.get("name"), payload.get("size"))
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400

@manufacturing_bp.route('/api/reference/delete', methods=['POST'])
@permission_required('mfg_items_reference')
def api_reference_delete():
    payload = request.get_json() or {}
    try:
        storage.delete_reference_item(payload.get("code"))
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400

@manufacturing_bp.route('/api/reference/import', methods=['POST'])
@permission_required('mfg_items_reference')
def api_reference_import():
    if 'excel_file' not in request.files:
        return jsonify({"ok": False, "message": "No file"}), 400
    try:
        file = request.files['excel_file']
        result = storage.import_reference_from_excel(file)
        return jsonify({"ok": True, "inserted": result})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400

# --- Factories API ---
@manufacturing_bp.route('/api/factories/add', methods=['POST'])
@permission_required('mfg_manufacturers')
def api_factories_add():
    payload = request.get_json() or {}
    try:
        storage.add_factory(payload.get("code"), payload.get("name"), payload.get("phone"), payload.get("type"))
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400

@manufacturing_bp.route('/api/factories/delete', methods=['POST'])
@permission_required('mfg_manufacturers')
def api_factories_delete():
    payload = request.get_json() or {}
    try:
        storage.delete_factory(payload.get("code"))
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400

@manufacturing_bp.route('/api/factories/import', methods=['POST'])
@permission_required('mfg_manufacturers')
def api_factories_import():
    if 'excel_file' not in request.files:
        return jsonify({"ok": False, "message": "No file"}), 400
    try:
        file = request.files['excel_file']
        result = storage.import_factories_from_excel(file)
        return jsonify({"ok": True, "inserted": result})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400

# --- Pricing API ---
@manufacturing_bp.route('/api/prices/list')
@permission_required('mfg_manufacturing_prices')
def api_prices_list():
    limit = min(max(request.args.get("limit", 300, type=int) or 300, 1), 1000)
    offset = max(request.args.get("offset", 0, type=int) or 0, 0)
    search = request.args.get("q", "").strip()
    factory_name = request.args.get("factory", "").strip()
    rows = storage.list_factory_prices(
        limit=limit + 1,
        offset=offset,
        search=search,
        factory_name=factory_name,
    )
    return jsonify({
        "items": rows[:limit],
        "limit": limit,
        "offset": offset,
        "has_more": len(rows) > limit,
    })

@manufacturing_bp.route('/api/prices/add', methods=['POST'])
@permission_required('mfg_manufacturing_prices')
def api_prices_add():
    payload = request.get_json() or {}
    try:
        storage.set_factory_price(
            payload.get("factory_code"), payload.get("product_code"),
            payload.get("price_per_dozen"), payload.get("factory_name"),
            payload.get("product_name"), payload.get("product_size")
        )
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400

@manufacturing_bp.route('/api/prices/delete', methods=['POST'])
@permission_required('mfg_manufacturing_prices')
def api_prices_delete():
    payload = request.get_json() or {}
    try:
        storage.delete_factory_price(payload.get("factory_code"), payload.get("product_code"))
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400

@manufacturing_bp.route('/api/prices/import', methods=['POST'])
@permission_required('mfg_manufacturing_prices')
def api_prices_import():
    if 'excel_file' not in request.files:
        return jsonify({"ok": False, "message": "No file"}), 400
    try:
        file = request.files['excel_file']
        result = storage.import_prices_from_excel(file)
        return jsonify({"ok": True, "inserted": result})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 400

# --- API Endpoints ---
@manufacturing_bp.route('/save_cuts', methods=['POST'])
def save_cuts():
    # Support both JSON and Form data for backward compatibility
    if request.is_json:
        payload = request.get_json() or {}
        rows = payload.get("items", [])
        notes = payload.get("notes", "")
        source = payload.get("source", "manual")
        cut_date = payload.get("cut_date", "")
        message_no = payload.get("message_no", "")
    else:
        rows = _extract_rows_from_form(request.form)
        notes = request.form.get("notes", "")
        source = request.form.get("source", "manual")
        cut_date = request.form.get("cut_date", "")
        message_no = request.form.get("message_no", "")

    try:
        batch_codes = _save_cut_groups(
            rows,
            notes=notes,
            source=source,
            cut_date=cut_date,
            message_no=message_no,
        )
        
        if request.is_json:
            return jsonify({"ok": True, "batch_codes": batch_codes})
            
        if len(batch_codes) == 1:
            flash(f"تم حفظ بيان القص {batch_codes[0]} بنجاح.", "success")
        else:
            flash(f"تم حفظ {len(batch_codes)} رسائل قص بنجاح.", "success")
        return redirect(url_for("manufacturing.index"))
        
    except Exception as exc:
        if request.is_json:
            return jsonify({"ok": False, "message": str(exc)}), 500
        flash(str(exc), "error")
        return redirect(url_for("manufacturing.index"))

def _extract_rows_from_form(form_data) -> list[dict[str, str]]:
    codes = form_data.getlist("code[]")
    names = form_data.getlist("name[]")
    sizes = form_data.getlist("size[]")
    quantities = form_data.getlist("quantity[]")
    descriptions = form_data.getlist("description[]")
    manufacturing_prices = form_data.getlist("manufacturing_price[]")
    row_cut_dates = form_data.getlist("row_cut_date[]")
    row_message_numbers = form_data.getlist("row_message_no[]")
    factory_codes = form_data.getlist("factory_code[]")
    factory_names = form_data.getlist("factory_name[]")
    dispatch_dates = form_data.getlist("dispatch_date[]")
    received_dates = form_data.getlist("received_date[]")

    rows = []
    max_length = max(
        len(codes),
        len(names),
        len(sizes),
        len(quantities),
        len(descriptions),
        len(manufacturing_prices),
        len(row_cut_dates),
        len(row_message_numbers),
        len(factory_codes),
        len(factory_names),
        len(dispatch_dates),
        len(received_dates),
        0,
    )

    for index in range(max_length):
        rows.append(
            {
                "code": codes[index] if index < len(codes) else "",
                "name": names[index] if index < len(names) else "",
                "size": sizes[index] if index < len(sizes) else "",
                "quantity": quantities[index] if index < len(quantities) else "",
                "description": descriptions[index] if index < len(descriptions) else "",
                "manufacturing_price": manufacturing_prices[index] if index < len(manufacturing_prices) else "",
                "cut_date": row_cut_dates[index] if index < len(row_cut_dates) else "",
                "message_no": row_message_numbers[index] if index < len(row_message_numbers) else "",
                "factory_code": factory_codes[index] if index < len(factory_codes) else "",
                "factory_name": factory_names[index] if index < len(factory_names) else "",
                "dispatch_date": dispatch_dates[index] if index < len(dispatch_dates) else "",
                "received_date": received_dates[index] if index < len(received_dates) else "",
            }
        )

    return rows

from collections import OrderedDict
def _save_cut_groups(
    rows: list[dict[str, str]],
    notes: str = "",
    source: str = "manual",
    cut_date: str = "",
    message_no: str = "",
) -> list[str]:
    has_row_groups = any(
        (row.get("cut_date") or "").strip() or (row.get("message_no") or "").strip()
        for row in rows
    )
    if source != "excel" or not has_row_groups:
        return [
            storage.save_cut_batch(
                rows,
                notes=notes,
                source=source,
                cut_date=cut_date,
                message_no=message_no,
            )
        ]

    grouped_rows: OrderedDict[tuple[str, str], list[dict[str, str]]] = OrderedDict()
    default_cut_date = (cut_date or "").strip()
    default_message_no = (message_no or "").strip()

    for row in rows:
        group_cut_date = (row.get("cut_date") or default_cut_date).strip()
        group_message_no = (row.get("message_no") or default_message_no).strip()
        group_key = (group_cut_date, group_message_no)
        grouped_rows.setdefault(group_key, []).append(row)

    batch_codes: list[str] = []
    for (group_cut_date, group_message_no), group_items in grouped_rows.items():
        batch_codes.append(
            storage.save_cut_batch(
                group_items,
                notes=notes,
                source=source,
                cut_date=group_cut_date,
                message_no=group_message_no,
            )
        )
    return batch_codes

@manufacturing_bp.route('/api/products/lookup')
def api_products_lookup():
    code = request.args.get("code", "")
    product = storage.lookup_product(code)
    return jsonify({"found": bool(product), "product": product})

@manufacturing_bp.route('/api/import-excel', methods=['POST'])
def api_import_excel():
    excel_file = request.files.get("excel_file")
    if not excel_file or not excel_file.filename:
        return jsonify({"ok": False, "message": "اختر ملف Excel أولًا."}), 400

    try:
        rows, meta = storage.parse_excel_rows(excel_file)
        
        if not rows:
            return jsonify({"ok": False, "message": "الملف فارغ أو لا يحتوي على بيانات صالحة."}), 400
            
        batch_codes = _save_cut_groups(
            rows=rows,
            notes="مستورد من Excel",
            source="excel",
            cut_date=meta.get("cut_date") or "",
            message_no=meta.get("message_no") or "",
        )

        return jsonify({
            "ok": True,
            "message": f"تم استيراد {len(rows)} سطر بنجاح وإضافتها للسجل العام.",
            "batch_codes": batch_codes,
            "summary": {
                "count": len(rows),
                "quantity": sum(float(row.get("quantity") or 0) for row in rows),
            },
        })
    except Exception as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400

@manufacturing_bp.route('/api/cut-items/update', methods=['POST'])
def api_cut_items_update():
    payload = request.get_json(silent=True) or {}
    try:
        updated_item = storage.update_cut_item_dispatch(
            item_id=payload.get("id"),
            cut_date=payload.get("cut_date"),
            message_no=payload.get("message_no"),
            code=payload.get("code"),
            name=payload.get("name"),
            size=payload.get("size"),
            quantity=payload.get("quantity"),
            factory_code=payload.get("factory_code"),
            factory_name=payload.get("factory_name"),
            manufacturing_price=payload.get("manufacturing_price"),
            dispatch_date=payload.get("dispatch_date"),
            description=payload.get("description"),
        )
    except ValueError as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400
    except Exception as exc:
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "message": "حدث خطأ غير متوقع: " + str(exc)}), 500
    return jsonify({"ok": True, "item": updated_item})

@manufacturing_bp.route('/api/admin/purge-cuts', methods=['POST'])
def admin_purge_cuts():
    payload = request.get_json(silent=True) or {}
    admin_password = str(payload.get("admin_password") or "").strip()
    confirmation = _normalize_confirmation_text(payload.get("confirmation") or "")

    if not admin_password:
        return jsonify({"ok": False, "message": "اكتب كلمة سر الأدمن أولًا."}), 400
    if confirmation != _normalize_confirmation_text(PURGE_CONFIRM_PHRASE):
        return jsonify(
            {
                "ok": False,
                "message": f"اكتب جملة التأكيد كما هي: {PURGE_CONFIRM_PHRASE}",
            }
        ), 400
    if not hmac.compare_digest(admin_password, _get_admin_password()):
        return jsonify({"ok": False, "message": "كلمة سر الأدمن غير صحيحة."}), 403

    deleted = storage.purge_cut_data()
    return jsonify(
        {
            "ok": True,
            "deleted": deleted,
            "message": (
                f"تم حذف {deleted['deleted_items']} صنف و"
                f" {deleted['deleted_batches']} بيان قص نهائيًا."
            ),
        }
    )

@manufacturing_bp.route('/api/cut-items/dispatch', methods=['POST'])
def api_dispatch_item():
    payload = request.get_json() or {}
    try:
        storage.update_cut_item_dispatch(
            item_id=payload.get("item_id"),
            factory_code=payload.get("factory_code"),
            factory_name=payload.get("factory_name"),
            dispatch_date=payload.get("dispatch_date"),
            manufacturing_price=payload.get("manufacturing_price"),
            message_no=payload.get("message_no"),
            code=payload.get("code"),
            name=payload.get("name"),
            size=payload.get("size"),
            quantity=payload.get("quantity"),
            cut_date=payload.get("cut_date"),
            description=payload.get("description")
        )
        return jsonify({"ok": True})
    except Exception as exc:
        return jsonify({"ok": False, "message": str(exc)}), 500

@manufacturing_bp.route('/api/cut-items/receive', methods=['POST'])
def cut_items_receive():
    payload = request.get_json() or {}
    try:
        result = storage.update_item_receipt(
            item_id=payload.get("item_id"), grade=float(payload.get("grade") or 0),
            repairs=float(payload.get("repairs") or 0), added=float(payload.get("added") or 0),
            remainders=float(payload.get("remainders") or 0), good_pieces=float(payload.get("good_pieces") or 0),
            good_dozens_entry=float(payload.get("good_dozens_entry") or 0),
            good_pieces_entry=float(payload.get("good_pieces_entry") or 0),
            received_actual_date=payload.get("received_actual_date") or datetime.now().strftime("%d/%m/%Y"),
            packing_department=payload.get("packing_department") or ""
        )
        return jsonify({"ok": True, "item": result})
    except Exception as exc:
        return jsonify({"ok": False, "message": str(exc)}), 500

@manufacturing_bp.route('/api/warehouse/pack', methods=['POST'])
def api_warehouse_pack():
    payload = request.get_json() or {}
    try:
        result = storage.process_packing_and_merge(payload.get("item_ids", []), payload.get("delivery_note_no", "").strip())
        return jsonify({"ok": True, "result": result})
    except Exception as exc:
        return jsonify({"ok": False, "message": str(exc)}), 500



@manufacturing_bp.route('/api/prices/lookup')
def api_prices_lookup():
    item = storage.lookup_factory_price(request.args.get("factory_code", ""), request.args.get("product_code", ""))
    return jsonify({"found": bool(item), "item": item})

@manufacturing_bp.route('/api/finished-stock/details')
def api_finished_stock_details():
    product_code = request.args.get("code", "")
    product_size = request.args.get("size", "")
    if not product_code or not product_size:
        return jsonify({"error": "Code and size are required"}), 400
    try:
        history = storage.get_product_packing_history(product_code, product_size)
        return jsonify(history)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@manufacturing_bp.route('/api/factories/balance')
def api_factories_balance():
    return jsonify(storage.get_factory_balance(request.args.get("code", "")))

@manufacturing_bp.route('/api/factories/list')
def api_factories_list():
    return jsonify({"items": storage.list_factories()})

@manufacturing_bp.route('/api/settings', methods=['GET', 'POST'])
def handle_settings():
    if request.method == 'POST':
        payload = request.get_json() or {}
        storage.set_setting(payload.get("key"), payload.get("value"))
        return jsonify({"ok": True})
    return jsonify({"ok": True, "value": storage.get_setting(request.args.get("key"), "")})

@manufacturing_bp.route('/api/cut-items/mark-accounted', methods=['POST'])
@permission_required('mfg_factory_accounts')
def cut_items_mark_accounted():
    payload = request.get_json() or {}
    try:
        today_str = datetime.now().strftime("%Y%m%d")
        accounting_id = f"ACC-{today_str}-{uuid.uuid4().hex[:6].upper()}"
        
        item_ids = payload.get("item_ids", [])
        item_prices = payload.get("item_prices", {})
        
        item_ids = [int(i) for i in item_ids]
        item_prices = {int(k): float(v) for k, v in item_prices.items()}
        
        count = storage.mark_items_as_accounted(
            item_ids, 
            payload.get("accounted_date"), 
            accounting_id=accounting_id,
            item_prices=item_prices
        )
        
        deduction = float(payload.get("deduction_amount") or 0)
        if deduction > 0 and payload.get("factory_code"):
            storage.add_factory_payment(
                factory_code=payload.get("factory_code"), amount=-deduction,
                date=payload.get("accounted_date"), entry_type="خصم تسوية", accounting_id=accounting_id,
                description=f"خصم تسوية (رقم التسوية: {accounting_id})"
            )
        return jsonify({"ok": True, "count": count, "accounting_id": accounting_id})
    except Exception as exc:
        return jsonify({"ok": False, "message": str(exc)}), 500

@manufacturing_bp.route('/api/factories/payments/add', methods=['POST'])
@permission_required('mfg_payments')
def factories_payments_add():
    payload = request.get_json() or {}
    try:
        payment_id = storage.add_factory_payment(
            factory_code=payload.get("factory_code"),
            amount=float(payload.get("amount") or 0),
            date=payload.get("date") or datetime.now().strftime("%d/%m/%Y"),
            description=payload.get("description", ""),
            entry_type=payload.get("entry_type") or "سلفة نقدية"
        )
        return jsonify({"ok": True, "id": payment_id})
    except Exception as exc:
        return jsonify({"ok": False, "message": str(exc)}), 500

@manufacturing_bp.route('/api/factories/payments/list')
def factories_payments_list():
    code = request.args.get("code", "")
    return jsonify({"items": storage.list_factory_payments(code)})

@manufacturing_bp.route('/api/factories/payments/delete', methods=['POST'])
@permission_required('mfg_payments')
def factories_payments_delete():
    payload = request.get_json() or {}
    try:
        storage.delete_factory_payment(payload.get("id"))
        return jsonify({"ok": True})
    except Exception as exc:
        return jsonify({"ok": False, "message": str(exc)}), 500

@manufacturing_bp.route('/api/factories/opening-balance/update', methods=['POST'])
def factories_opening_balance_update():
    payload = request.get_json() or {}
    try:
        storage.update_factory_opening_balance(payload.get("factory_code"), float(payload.get("amount") or 0))
        return jsonify({"ok": True})
    except Exception as exc:
        return jsonify({"ok": False, "message": str(exc)}), 500

@manufacturing_bp.route('/api/cut-items/delete', methods=['POST'])
def delete_cut_item():
    payload = request.get_json(silent=True) or {}
    item_id = payload.get("id")
    if not item_id:
        return jsonify({"ok": False, "message": "رقم الصنف مطلوب"}), 400
    try:
        deleted = storage.delete_cut_item(item_id)
        if not deleted:
            return jsonify({"ok": False, "message": "الصنف غير موجود أو تم حذفه بالفعل."}), 404
        return jsonify({"ok": True})
    except Exception as exc:
        return jsonify({"ok": False, "message": str(exc)}), 500

@manufacturing_bp.route('/api/cut-items/reverse-accounting', methods=['POST'])
@permission_required('mfg_factory_accounts')
def cut_items_reverse_accounting():
    payload = request.get_json(silent=True) or {}
    accounting_id = payload.get("accounting_id")
    if not accounting_id:
        return jsonify({"ok": False, "message": "رقم التسوية مطلوب"}), 400
    try:
        storage.reverse_accounting(accounting_id)
        return jsonify({"ok": True})
    except Exception as exc:
        return jsonify({"ok": False, "message": str(exc)}), 500

@manufacturing_bp.route('/api/cut-items/reverse-dispatch', methods=['POST'])
def api_reverse_dispatch():
    payload = request.get_json(silent=True) or {}
    item_id = payload.get("id")
    if not item_id:
        return jsonify({"ok": False, "message": "رقم الصنف مطلوب"}), 400
    try:
        storage.reverse_cut_item_dispatch(item_id)
        return jsonify({"ok": True})
    except Exception as exc:
        return jsonify({"ok": False, "message": str(exc)}), 500

@manufacturing_bp.route('/reports/factory-deficits')
@permission_required('mfg_deficit_report')
def factory_deficits_report_page():
    factory_code = request.args.get("factory_code", "")
    deficits = storage.get_factory_deficits_report(factory_code=factory_code)
    return render_template(
        "manufacturing/factory_deficits_report.html",
        deficits=deficits,
        factories=storage.list_factories(),
        selected_factory=factory_code,
        current_time=datetime.now()
    )

@manufacturing_bp.route('/reports/production/packing')
@permission_required('mfg_packing_production')
def production_packing_report():
    year = request.args.get("year", datetime.now().year, type=int)
    from_month = request.args.get("from_month", "", type=str)
    to_month = request.args.get("to_month", "", type=str)
    department = request.args.get("department", "الكل")
    factory = request.args.get("factory", "الكل")
    product = request.args.get("product", "الكل")
    
    report_data = storage.get_packing_production_report(
        year=year,
        from_month=int(from_month) if from_month else None,
        to_month=int(to_month) if to_month else None,
        department=department if department != "الكل" else None,
        factory_name=factory if factory != "الكل" else None,
        product_code=product if product != "الكل" else None
    )
    
    return render_template(
        "manufacturing/production_packing_report.html",
        report_data=report_data,
        factories=storage.list_factories(),
        products=storage.get_reference_items(),
        selected_year=year,
        selected_from_month=from_month,
        selected_to_month=to_month,
        selected_department=department,
        selected_factory=factory,
        selected_product=product
    )

@manufacturing_bp.route('/reports/production/cutting')
@permission_required('mfg_cutting_production')
def production_cutting_report():
    month = request.args.get("month", datetime.now().month, type=int)
    year = request.args.get("year", datetime.now().year, type=int)
    report_data = storage.get_cutting_production_report(month, year)
    return render_template(
        "manufacturing/production_cutting_report.html",
        report_data=report_data,
        selected_month=month,
        selected_year=year,
        current_time=datetime.now()
    )

@manufacturing_bp.route('/reports/message')
@permission_required('mfg_message_detailed_report')
def message_detailed_report_page():
    from flask import flash
    message_no = request.args.get("message_no", "").strip()
    if not message_no:
        return render_template("manufacturing/message_report_search.html", current_time=datetime.now())
        
    try:
        report_data = storage.get_message_detailed_report(message_no)
        return render_template(
            "manufacturing/message_report_details.html",
            data=report_data,
            current_time=datetime.now()
        )
    except Exception as exc:
        flash(str(exc), "error")
        return redirect(url_for("manufacturing.message_detailed_report_page"))
