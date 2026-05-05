from __future__ import annotations

import hmac
import os
import secrets
from collections import OrderedDict
from datetime import datetime
import unicodedata
import uuid

import pandas as pd
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for

from operation_storage import (
    DB_PATH,
    add_factories,
    add_factory_prices,
    add_reference_items,
    clean_text,
    delete_cut_item,
    delete_factory,
    delete_factory_price,
    delete_reference_item,
    get_dashboard_totals,
    get_recent_batches,
    get_recent_cut_items,
    get_reference_items,
    initialize_database,
    initialize_factories_table,
    list_factories,
    list_factory_prices,
    lookup_factory_price,
    lookup_product,
    parse_factory_price_rows,
    parse_excel_rows,
    purge_factory_prices,
    purge_cut_data,
    save_cut_batch,
    update_cut_item_dispatch,
    mark_items_as_accounted,
    add_factory_payment,
    list_factory_payments,
    delete_factory_payment,
    update_factory_opening_balance,
    get_payment_receipt_data,
    get_items_for_receiving,
    update_item_receipt,
    list_factories_with_items,
    get_accounting_statements,
    reverse_accounting,
    get_accounting_statement_details,
    get_setting,
    set_setting,
    reverse_cut_item_dispatch,
    get_factory_balance,
    get_factory_deficits_report,
    get_pending_packing_items,
    get_finished_stock,
    process_packing_and_merge,
    undo_item_receipt,
    get_packing_production_report,
    get_cutting_production_report,
    get_message_detailed_report,
    reverse_packing_by_note,
    get_product_packing_history,
)


PURGE_CONFIRM_PHRASE = "احذف جميع بيانات القص"
PRICE_PURGE_CONFIRM_PHRASE = "احذف جميع أسعار المصنعين"


def _get_admin_password_file_path():
    return DB_PATH.parent / "operation_admin_password.txt"


def _get_admin_password() -> str:
    env_password = os.environ.get("OPERATION_ADMIN_PASSWORD", "").strip()
    if env_password:
        return env_password

    password_file = _get_admin_password_file_path()
    if password_file.exists():
        stored_password = password_file.read_text(encoding="utf-8").strip()
        if stored_password:
            return stored_password

    generated_password = secrets.token_urlsafe(12)
    password_file.write_text(generated_password, encoding="utf-8")
    return generated_password


def _normalize_confirmation_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or ""))
    return " ".join(normalized.split())


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "operation-dev-secret")
    app.config["PURGE_CONFIRM_PHRASE"] = PURGE_CONFIRM_PHRASE
    app.config["PRICE_PURGE_CONFIRM_PHRASE"] = PRICE_PURGE_CONFIRM_PHRASE
    _get_admin_password()

    initialize_database()
    initialize_factories_table()

    @app.get("/")
    def index():
        return render_template(
            "cuts_entry.html",
            current_time=datetime.now(),
            database_path=str(DB_PATH),
            recent_batches=get_recent_batches(),
            recent_cut_items=get_recent_cut_items(delivered=False),
            dashboard_totals=get_dashboard_totals(pending_only=True),
            factories=list_factories(),
        )

    @app.get("/reference")
    def reference_page():
        return render_template(
            "reference.html",
            current_time=datetime.now(),
            database_path=str(DB_PATH),
        )

    @app.get("/factories")
    def factories_page():
        return render_template(
            "factories.html",
            current_time=datetime.now(),
            database_path=str(DB_PATH),
        )

    @app.get("/pricing")
    def pricing_page():
        return render_template(
            "pricing.html",
            current_time=datetime.now(),
            database_path=str(DB_PATH),
            factories=list_factories(),
            products=get_reference_items(limit=500),
        )

    @app.get("/factory-payments")
    def factory_payments_page():
        return render_template(
            "factory_payments.html",
            current_time=datetime.now(),
            database_path=str(DB_PATH),
            factories=list_factories(),
        )

    @app.get("/print-payment/<int:payment_id>")
    def print_payment_receipt(payment_id):
        try:
            receipt_data = get_payment_receipt_data(payment_id)
            return render_template("payment_receipt.html", receipt=receipt_data)
        except Exception as e:
            return f"<h3 style='direction: rtl; text-align: center; margin-top: 50px; color: red;'>خطأ: {str(e)}</h3>", 404

    @app.get("/accounting-statement/<accounting_id>")
    def print_accounting_statement(accounting_id):
        pwd = request.args.get("pwd", "")
        if pwd != _get_admin_password():
            return f"<h3 style='direction: rtl; text-align: center; margin-top: 50px; color: red;'>خطأ: صلاحية مرفوضة. يرجى إدخال كلمة مرور الإدارة.</h3>", 403
            
        try:
            context = get_accounting_statement_details(accounting_id)
            if not context["items"]:
                return f"<h3 style='direction: rtl; text-align: center; margin-top: 50px; color: red;'>التسوية غير موجودة أو فارغة.</h3>", 404
            
            items = context["items"]
            total_qty = sum(float(i.get("quantity") or 0) for i in items)
            total_amount = sum((float(i.get("quantity") or 0) / 12.0) * float(i.get("manufacturing_price") or 0) for i in items)
            
            # balance_after = context["previous_balance"] - context["deduction"]
            # net_to_pay = total_amount - context["deduction"]
            
            return render_template(
                "accounting_statement_receipt.html",
                accounting_id=accounting_id,
                factory_name=context["factory_name"],
                factory_code=context["factory_code"],
                accounted_date=context["accounted_date"],
                items=items,
                total_qty=total_qty,
                total_amount=total_amount,
                deduction=context["deduction"],
                previous_balance=context["previous_balance"],
                footer_note=get_setting("statement_footer_note", ""),
                current_time=datetime.now().strftime("%d/%m/%Y %I:%M %p")
            )
        except Exception as e:
            return f"<h3 style='direction: rtl; text-align: center; margin-top: 50px; color: red;'>خطأ: {str(e)}</h3>", 500

    @app.get("/manufacturer-accounts")
    def manufacturer_accounts_page():
        view = request.args.get("view", "pending")
        
        grouped_statements = []
        cut_items = []
        if view == "history":
            grouped_statements = get_accounting_statements(limit=500)
        else:
            cut_items = get_recent_cut_items(delivered=True, accounted=False)
            
        return render_template(
            "manufacturer_accounts.html",
            current_time=datetime.now(),
            database_path=str(DB_PATH),
            manufacturer_cut_items=cut_items,
            grouped_statements=grouped_statements,
            factories=list_factories(),
            current_view=view,
        )

    @app.get("/receiving")
    def receiving_page():
        factory_code = request.args.get("factory_code", "")
        # نجلب المصانع التي عندها عهدة فقط لتسهيل الاختيار في الفلتر
        active_factories = list_factories_with_items()
        
        items = []
        if factory_code:
            items = get_items_for_receiving(factory_code=factory_code)
            
        return render_template(
            "receiving.html",
            current_time=datetime.now(),
            database_path=str(DB_PATH),
            factories=active_factories,
            items=items,
            selected_factory=factory_code
        )

    @app.post("/api/cut-items/receive")
    def cut_items_receive():
        payload = request.get_json() or {}
        item_id = payload.get("item_id")
        grade = float(payload.get("grade") or 0)
        repairs = float(payload.get("repairs") or 0)
        added = float(payload.get("added") or 0)
        remainders = float(payload.get("remainders") or 0)
        good_pieces = float(payload.get("good_pieces") or 0)
        good_dozens_entry = float(payload.get("good_dozens_entry") or 0)
        good_pieces_entry = float(payload.get("good_pieces_entry") or 0)
        received_actual_date = payload.get("received_actual_date") or datetime.now().strftime("%d/%m/%Y")
        packing_department = payload.get("packing_department") or ""

        if not item_id:
            return jsonify({"ok": False, "message": "رقم القصة مطلوب."}), 400

        try:
            result = update_item_receipt(
                item_id=item_id,
                grade=grade,
                repairs=repairs,
                added=added,
                remainders=remainders,
                good_pieces=good_pieces,
                good_dozens_entry=good_dozens_entry,
                good_pieces_entry=good_pieces_entry,
                received_actual_date=received_actual_date,
                packing_department=packing_department
            )
            return jsonify({"ok": True, "item": result, "message": "تم تسجيل الاستلام بنجاح."})
        except Exception as exc:
            return jsonify({"ok": False, "message": str(exc)}), 500

    @app.post("/api/cut-items/undo-receive")
    def cut_items_undo_receive():
        payload = request.get_json() or {}
        item_id = payload.get("item_id")
        if not item_id:
            return jsonify({"ok": False, "message": "رقم القصة مطلوب."}), 400
        
        try:
            success = undo_item_receipt(item_id)
            if success:
                return jsonify({"ok": True, "message": "تم التراجع عن الاستلام بنجاح، عادت القصة لصفحة الاستلام."})
            else:
                return jsonify({"ok": False, "message": "فشل التراجع، ربما تم تعبئة الصنف بالفعل."})
        except Exception as exc:
            return jsonify({"ok": False, "message": str(exc)}), 500

    @app.get("/warehouse")
    def warehouse_page():
        return render_template(
            "warehouse.html",
            current_time=datetime.now(),
            database_path=str(DB_PATH),
            pending_items=get_pending_packing_items()
        )

    @app.get("/finished-stock")
    def finished_stock_page():
        return render_template(
            "finished_stock.html",
            current_time=datetime.now(),
            database_path=str(DB_PATH),
            stock=get_finished_stock()
        )

    @app.get("/api/warehouse/pending")
    def api_warehouse_pending():
        return jsonify(get_pending_packing_items())

    @app.post("/api/warehouse/pack")
    def api_warehouse_pack():
        payload = request.get_json() or {}
        item_ids = payload.get("item_ids", [])
        delivery_note_no = payload.get("delivery_note_no", "").strip()
        
        if not item_ids:
            return jsonify({"ok": False, "message": "لم يتم اختيار أي أصناف."}), 400
            
        if not delivery_note_no:
            return jsonify({"ok": False, "message": "يجب إدخال رقم إذن التسليم للمخازن."}), 400
        
        try:
            result = process_packing_and_merge(item_ids, delivery_note_no)
            return jsonify({"ok": True, "result": result, "message": f"تمت التعبئة بنجاح: معالجة {result['processed']} سجل بـ رقم إذن {delivery_note_no}."})
        except Exception as exc:
            return jsonify({"ok": False, "message": str(exc)}), 500
 
    @app.post("/api/warehouse/reverse-pack")
    def api_warehouse_reverse_pack():
        payload = request.get_json() or {}
        delivery_note_no = payload.get("delivery_note_no", "").strip()
        
        if not delivery_note_no:
            return jsonify({"ok": False, "message": "رقم إذن التسليم مطلوب."}), 400
            
        try:
            result = reverse_packing_by_note(delivery_note_no)
            return jsonify({"ok": True, "message": f"تم التراجع عن إذن التسليم {delivery_note_no} بنجاح وإعادة {result['reversed_items']} صنف للمستودع."})
        except Exception as exc:
            return jsonify({"ok": False, "message": str(exc)}), 500

    @app.post("/api/warehouse/delete-item")
    def delete_warehouse_item():
        try:
            data = request.get_json()
            item_id = data.get("item_id")
            if not item_id:
                return jsonify({"ok": False, "message": "معرف الصنف مطلوب."}), 400
            
            if delete_cut_item(item_id):
                return jsonify({"ok": True, "message": "تم حذف الصنف بنجاح."})
            else:
                return jsonify({"ok": False, "message": "فشل حذف الصنف أو الصنف غير موجود."}), 404
        except Exception as e:
            return jsonify({"ok": False, "message": str(e)}), 500
            
    @app.get("/api/finished-stock/details")
    def finished_stock_details():
        product_code = request.args.get("code", "")
        product_size = request.args.get("size", "")
        if not product_code or not product_size:
            return jsonify({"error": "الكود والمقاس مطلوبان."}), 400
            
        try:
            history = get_product_packing_history(product_code, product_size)
            return jsonify(history)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.post("/api/cut-items/mark-accounted")
    def cut_items_mark_accounted():
        payload = request.get_json() or {}
        item_ids = payload.get("item_ids", [])
        accounted_date = payload.get("accounted_date") or datetime.now().strftime("%d/%m/%Y")
        deduction_amount = float(payload.get("deduction_amount") or 0)
        factory_code = payload.get("factory_code")
        
        if not item_ids:
            return jsonify({"ok": False, "message": "اختر قصات للمحاسبة أولاً."}), 400
            
        try:
            # Generate a unique accounting ID
            today_str = datetime.now().strftime("%Y%m%d")
            accounting_id = f"ACC-{today_str}-{uuid.uuid4().hex[:6].upper()}"

            count = mark_items_as_accounted(item_ids, accounted_date, accounting_id=accounting_id)

            # If there's a deduction from advances, record it in the ledger
            if deduction_amount > 0 and factory_code:
                add_factory_payment(
                    factory_code=factory_code,
                    amount=-deduction_amount, # Negative because it's a deduction
                    date=accounted_date,
                    description=f"خصم تسوية لعدد {len(item_ids)} قصات (رقم التسوية: {accounting_id})",
                    entry_type="خصم تسوية",
                    accounting_id=accounting_id
                )

            return jsonify({"ok": True, "count": count, "accounting_id": accounting_id, "message": f"تمت محاسبة {count} سجلات بنجاح."})
        except Exception as exc:
            return jsonify({"ok": False, "message": str(exc)}), 500

    @app.get("/reports/factory-deficits")
    def factory_deficits_report_page():
        factory_code = request.args.get("factory_code", "")
        deficits = get_factory_deficits_report(factory_code=factory_code)
        
        return render_template(
            "factory_deficits_report.html",
            deficits=deficits,
            factories=list_factories(),
            selected_factory=factory_code,
            current_time=datetime.now()
        )

    @app.post("/api/cut-items/reverse-accounting")
    def cut_items_reverse_accounting():
        payload = request.get_json() or {}
        accounting_id = payload.get("accounting_id")
        password = payload.get("password")
        
        if not accounting_id:
            return jsonify({"ok": False, "message": "رقم التسوية مطلوب."}), 400
            
        if password != _get_admin_password():
            return jsonify({"ok": False, "message": "كلمة مرور الإدارة غير صحيحة، لا يمكن فك التسوية."}), 403
            
        try:
            result = reverse_accounting(accounting_id)
            return jsonify({"ok": True, "message": result["message"], "items_affected": result["items_affected"]})
        except Exception as exc:
            return jsonify({"ok": False, "message": str(exc)}), 500

    @app.get("/reports/production/packing")
    def production_packing_report():
        from_month = request.args.get("from_month", type=int)
        to_month = request.args.get("to_month", type=int)
        year = request.args.get("year", datetime.now().year, type=int)
        department = request.args.get("department", "الكل")
        product = request.args.get("product", "الكل")
        factory = request.args.get("factory", "الكل")

        # التوافق مع الرابط القديم
        old_month = request.args.get("month", type=int)
        if old_month and not from_month:
            from_month = old_month
            to_month = old_month

        # جلب البيانات لكل الأصناف لتكوين قائمة الفلتر الديناميكية
        all_potential_data = get_packing_production_report(
            from_month=from_month,
            to_month=to_month,
            year=year,
            department=department,
            product_code='الكل',
            factory_name=factory
        )
        
        # استخراج الأصناف الفريدة الموجودة في هذه البيانات فقط
        report_products = []
        seen_codes = set()
        for item in all_potential_data:
            code = item.get('product_code')
            if code and code not in seen_codes:
                report_products.append({
                    'code': code,
                    'name': item.get('product_name', ''),
                    'size': item.get('product_size', '')
                })
                seen_codes.add(code)
        
        # ترتيب الأصناف أبجدياً حسب الاسم
        report_products.sort(key=lambda x: x['name'])

        # الفلترة الفعلية للبيانات المعروضة في الجدول إذا اختار المستخدم صنفاً معيناً
        if product == 'الكل':
            report_data = all_potential_data
        else:
            report_data = [i for i in all_potential_data if i['product_code'] == product]
        
        return render_template(
            "production_packing_report.html",
            report_data=report_data,
            selected_from_month=from_month,
            selected_to_month=to_month,
            selected_year=year,
            selected_department=department,
            selected_product=product,
            selected_factory=factory,
            factories=list_factories(),
            products=report_products,  # نمرر القائمة المفلترة الجديدة
            current_time=datetime.now()
        )

    @app.get("/reports/message")
    def message_detailed_report_page():
        message_no = request.args.get("message_no", "").strip()
        if not message_no:
            return render_template("message_report_search.html", current_time=datetime.now())
            
        try:
            report_data = get_message_detailed_report(message_no)
            return render_template(
                "message_report_details.html",
                data=report_data,
                current_time=datetime.now()
            )
        except Exception as exc:
            flash(str(exc), "error")
            return redirect(url_for("message_detailed_report_page"))

    @app.get("/reports/production/cutting")
    def production_cutting_report():
        month = request.args.get("month", datetime.now().month, type=int)
        year = request.args.get("year", datetime.now().year, type=int)
        report_data = get_cutting_production_report(month, year)
        return render_template(
            "production_cutting_report.html",
            report_data=report_data,
            selected_month=month,
            selected_year=year,
            current_time=datetime.now()
        )

    @app.get("/api/factories/balance")
    def factories_balance():
        code = request.args.get("code", "")
        return jsonify(get_factory_balance(code))

    @app.get("/api/settings")
    def get_settings_route():
        key = request.args.get("key")
        if not key:
            return jsonify({"ok": False, "message": "المفتاح مطلوب."}), 400
        return jsonify({"ok": True, "value": get_setting(key, "")})

    @app.post("/api/settings")
    def set_settings_route():
        payload = request.get_json() or {}
        key = payload.get("key")
        value = payload.get("value")
        if not key:
            return jsonify({"ok": False, "message": "المفتاح مطلوب."}), 400
        set_setting(key, value)
        return jsonify({"ok": True, "message": "تم حفظ الإعداد بنجاح."})

    @app.get("/api/factories/payments/list")
    def factories_payments_list():
        code = request.args.get("code", "")
        return jsonify({"items": list_factory_payments(code)})

    @app.post("/api/factories/opening-balance/update")
    def factories_opening_balance_update():
        payload = request.get_json() or {}
        try:
            factory_code = payload.get("factory_code")
            amount = float(payload.get("amount") or 0)
            if not factory_code:
                return jsonify({"ok": False, "message": "كود المصنع مطلوب."}), 400
            success = update_factory_opening_balance(factory_code, amount)
            if success:
                return jsonify({"ok": True, "message": "تم تحديث الرصيد الافتتاحي."})
            else:
                return jsonify({"ok": False, "message": "لم يتم العثور على المصنع."}), 404
        except Exception as exc:
            return jsonify({"ok": False, "message": str(exc)}), 500

    @app.post("/api/factories/payments/add")
    def factories_payments_add():
        payload = request.get_json() or {}
        try:
            payment_id = add_factory_payment(
                factory_code=payload.get("factory_code"),
                amount=float(payload.get("amount") or 0),
                date=payload.get("date") or datetime.now().strftime("%d/%m/%Y"),
                description=payload.get("description", ""),
                entry_type=payload.get("entry_type") or "سلفة نقدية"
            )
            return jsonify({"ok": True, "id": payment_id})
        except Exception as exc:
            return jsonify({"ok": False, "message": str(exc)}), 500

    @app.post("/api/factories/payments/delete")
    def factories_payments_delete():
        payload = request.get_json() or {}
        try:
            delete_factory_payment(payload.get("id"))
            return jsonify({"ok": True})
        except Exception as exc:
            return jsonify({"ok": False, "message": str(exc)}), 500

    @app.get("/accounting-statement/<accounting_id>")
    def accounting_statement_report(accounting_id):
        from operation_storage import get_connection
        with get_connection() as conn:
            # 1. Get transaction info (deduction)
            payment = conn.execute(
                "SELECT * FROM operation_factory_payments WHERE accounting_id = ?",
                (accounting_id,)
            ).fetchone()
            
            # 2. Get items involved
            items = conn.execute(
                """
                SELECT i.*, p.name as product_name, p.size as product_size
                FROM operation_cut_items i
                JOIN operation_products p ON p.id = i.product_id
                WHERE i.accounting_id = ?
                """,
                (accounting_id,)
            ).fetchall()
            
            if not items:
                return "عذراً، لم يتم العثور على بيانات لهذه التسوية.", 404
            
            factory_code = items[0]["factory_code"]
            factory_name = items[0]["factory_name"]
            accounted_date = items[0]["accounted_date"]
            
            # 3. Get balances
            balance_info = get_factory_balance(factory_code)
            
            # Logic for balance representation:
            # We want current balance (after deduction) and the deduction itself.
            deduction = abs(payment["amount"]) if payment else 0
            
        return render_template(
            "statement_report.html",
            accounting_id=accounting_id,
            factory_name=factory_name,
            factory_code=factory_code,
            accounted_date=accounted_date,
            items=items,
            payment=payment,
            deduction=deduction,
            balance_info=balance_info,
            current_time=datetime.now()
        )

    @app.get("/api/factories/list")
    def factories_list():
        return jsonify({"items": list_factories()})

    @app.post("/api/factories/add")
    def factories_add():
        payload = request.get_json() or {}
        row = {
            "code": payload.get("code"),
            "name": payload.get("name"),
            "type": payload.get("type") or "خارجي",
            "phone": payload.get("phone"),
            "opening_balance": payload.get("opening_balance") or 0,
        }
        if not row["code"] or not row["name"]:
            return jsonify({"ok": False, "message": "املأ الكود والاسم."}), 400
        inserted = add_factories([row])
        return jsonify({"ok": True, "inserted": inserted})

    @app.post("/api/factories/import")
    def factories_import():
        excel_file = request.files.get("excel_file")
        if not excel_file or not excel_file.filename:
            return jsonify({"ok": False, "message": "اختر ملف Excel أولًا."}), 400
        try:
            data_frame = pd.read_excel(excel_file)
            if data_frame.empty:
                raise ValueError("الملف لا يحتوي على بيانات.")
            rows = []
            for _, row in data_frame.iterrows():
                rows.append(
                    {
                        "code": str(
                            row.get("code")
                            or row.get("كود")
                            or row.get("الكود")
                            or ""
                        ).strip(),
                        "name": str(
                            row.get("name")
                            or row.get("اسم")
                            or row.get("الاسم")
                            or ""
                        ).strip(),
                        "type": str(
                            row.get("type")
                            or row.get("النوع")
                            or "خارجي"
                        ).strip(),
                        "phone": str(
                            row.get("phone")
                            or row.get("هاتف")
                            or row.get("تليفون")
                            or row.get("رقم التليفون")
                            or row.get("mobile")
                            or row.get("tel")
                            or row.get("phone_no")
                            or row.get("phone number")
                            or ""
                        ).strip(),
                    }
                )
            rows = [item for item in rows if item["code"] and item["name"]]
            inserted = add_factories(rows)
        except ValueError as exc:
            return jsonify({"ok": False, "message": str(exc)}), 400
        return jsonify({"ok": True, "inserted": inserted})

    @app.post("/api/factories/delete")
    def factories_delete():
        payload = request.get_json(silent=True) or {}
        try:
            deleted = delete_factory(payload.get("code", ""))
        except ValueError as exc:
            return jsonify({"ok": False, "message": str(exc)}), 400
        return jsonify({"ok": True, "factory": deleted})

    @app.get("/api/prices/list")
    def prices_list():
        return jsonify({"items": list_factory_prices()})

    @app.get("/api/prices/lookup")
    def prices_lookup():
        item = lookup_factory_price(
            request.args.get("factory_code", ""),
            request.args.get("product_code", ""),
        )
        return jsonify({"found": bool(item), "item": item})

    @app.post("/api/prices/add")
    def prices_add():
        payload = request.get_json(silent=True) or {}
        row = {
            "factory_code": payload.get("factory_code"),
            "factory_name": payload.get("factory_name"),
            "product_code": payload.get("product_code"),
            "product_name": payload.get("product_name"),
            "product_size": payload.get("product_size"),
            "price_per_dozen": payload.get("price_per_dozen"),
        }
        if (
            not row["factory_code"]
            or not row["product_code"]
            or not clean_text(row["product_size"])
            or clean_text(row["price_per_dozen"]) == ""
        ):
            return jsonify({"ok": False, "message": "املأ المصنع والصنف والمقاس والسعر."}), 400
        inserted = add_factory_prices([row])
        return jsonify({"ok": True, "inserted": inserted})

    @app.post("/api/prices/import")
    def prices_import():
        excel_file = request.files.get("excel_file")
        if not excel_file or not excel_file.filename:
            return jsonify({"ok": False, "message": "اختر ملف Excel أولًا."}), 400

        try:
            rows = parse_factory_price_rows(excel_file)
            inserted = add_factory_prices(rows)
        except ValueError as exc:
            return jsonify({"ok": False, "message": str(exc)}), 400

        return jsonify({"ok": True, "inserted": inserted})

    @app.post("/api/prices/delete")
    def prices_delete():
        payload = request.get_json(silent=True) or {}
        try:
            deleted = delete_factory_price(
                payload.get("factory_code", ""),
                payload.get("product_code", ""),
            )
        except ValueError as exc:
            return jsonify({"ok": False, "message": str(exc)}), 400
        return jsonify({"ok": True, "item": deleted})

    @app.post("/api/admin/purge-prices")
    def admin_purge_prices():
        payload = request.get_json(silent=True) or {}
        admin_password = str(payload.get("admin_password") or "").strip()
        confirmation = _normalize_confirmation_text(payload.get("confirmation") or "")

        if not admin_password:
            return jsonify({"ok": False, "message": "اكتب كلمة سر الأدمن أولًا."}), 400
        if confirmation != _normalize_confirmation_text(PRICE_PURGE_CONFIRM_PHRASE):
            return jsonify(
                {
                    "ok": False,
                    "message": f"اكتب جملة التأكيد كما هي: {PRICE_PURGE_CONFIRM_PHRASE}",
                }
            ), 400
        if not hmac.compare_digest(admin_password, _get_admin_password()):
            return jsonify({"ok": False, "message": "كلمة سر الأدمن غير صحيحة."}), 403

        deleted = purge_factory_prices()
        return jsonify(
            {
                "ok": True,
                "deleted": deleted,
                "message": f"تم حذف {deleted['deleted_prices']} سعر من مرجع أسعار المصنعين نهائيًا.",
            }
        )

    @app.get("/api/products/lookup")
    def product_lookup():
        code = request.args.get("code", "")
        product = lookup_product(code)
        return jsonify({"found": bool(product), "product": product})

    @app.post("/api/cut-items/update")
    def update_cut_item():
        payload = request.get_json(silent=True) or {}
        try:
            updated_item = update_cut_item_dispatch(
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
        return jsonify({"ok": True, "item": updated_item})


    @app.post("/api/cut-items/reverse-dispatch")
    def reverse_cut_item_dispatch_route():
        payload = request.get_json(silent=True) or {}
        item_id = payload.get("id")
        if not item_id:
            return jsonify({"ok": False, "message": "رقم السطر مطلوب."}), 400
        try:
            result = reverse_cut_item_dispatch(item_id)
            return jsonify({"ok": True, "message": "تم التراجع عن التسليم بنجاح.", "item": result})
        except Exception as exc:
            return jsonify({"ok": False, "message": str(exc)}), 500

    @app.post("/api/cut-items/delete")
    def remove_cut_item():
        payload = request.get_json(silent=True) or {}
        try:
            deleted_item = delete_cut_item(payload.get("id"))
        except ValueError as exc:
            return jsonify({"ok": False, "message": str(exc)}), 400
        return jsonify({"ok": True, "item": deleted_item})

    @app.post("/api/import-excel")
    def import_excel():
        excel_file = request.files.get("excel_file")
        if not excel_file or not excel_file.filename:
            return jsonify({"ok": False, "message": "اختر ملف Excel أولًا."}), 400

        try:
            rows, meta = parse_excel_rows(excel_file)
        except ValueError as exc:
            return jsonify({"ok": False, "message": str(exc)}), 400

        return jsonify(
            {
                "ok": True,
                "rows": rows,
                "meta": meta,
                "summary": {
                    "count": len(rows),
                    "quantity": sum(float(row.get("quantity") or 0) for row in rows),
                },
            }
        )

    @app.get("/api/reference-list")
    def reference_list():
        reference_items = get_reference_items()
        return jsonify({"items": reference_items})

    @app.post("/api/reference/import")
    def reference_import():
        excel_file = request.files.get("excel_file")
        if not excel_file or not excel_file.filename:
            return jsonify({"ok": False, "message": "اختر ملف Excel أولًا."}), 400

        try:
            rows, _ = parse_excel_rows(excel_file)
        except ValueError as exc:
            return jsonify({"ok": False, "message": str(exc)}), 400

        inserted = add_reference_items(rows)
        return jsonify({"ok": True, "inserted": inserted})

    @app.post("/api/reference/add")
    def reference_add():
        payload = request.get_json() or {}
        row = {
            "code": payload.get("code"),
            "name": payload.get("name"),
            "size": payload.get("size"),
        }
        if not row["code"] or not row["name"] or not row["size"]:
            return jsonify({"ok": False, "message": "املأ الكود والاسم والمقاس."}), 400
        inserted = add_reference_items([row])
        return jsonify({"ok": True, "inserted": inserted})

    @app.post("/api/reference/delete")
    def reference_delete():
        payload = request.get_json(silent=True) or {}
        try:
            deleted = delete_reference_item(payload.get("code", ""))
        except ValueError as exc:
            return jsonify({"ok": False, "message": str(exc)}), 400
        return jsonify({"ok": True, "item": deleted})

    @app.post("/cuts/save")
    def save_cuts():
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
        except ValueError as exc:
            flash(str(exc), "error")
            return redirect(url_for("index"))

        if len(batch_codes) == 1:
            flash(f"تم حفظ بيان القص {batch_codes[0]} بنجاح.", "success")
        else:
            flash(f"تم حفظ {len(batch_codes)} رسائل قص بنجاح.", "success")
        return redirect(url_for("index"))

    @app.post("/api/admin/purge-cuts")
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

        deleted = purge_cut_data()
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

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "database": str(DB_PATH)})

    return app


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


def _save_cut_groups(
    rows: list[dict[str, str]],
    notes: str = "",
    source: str = "manual",
    cut_date: str = "",
    message_no: str = "",
) -> list[str]:
    has_row_groups = any(
        str(row.get("cut_date") or "").strip() or str(row.get("message_no") or "").strip()
        for row in rows
    )
    if source != "excel" or not has_row_groups:
        return [
            save_cut_batch(
                rows,
                notes=notes,
                source=source,
                cut_date=cut_date,
                message_no=message_no,
            )
        ]

    grouped_rows: OrderedDict[tuple[str, str], list[dict[str, str]]] = OrderedDict()
    default_cut_date = str(cut_date or "").strip()
    default_message_no = str(message_no or "").strip()

    for row in rows:
        group_cut_date = str(row.get("cut_date") or default_cut_date).strip()
        group_message_no = str(row.get("message_no") or default_message_no).strip()
        group_key = (group_cut_date, group_message_no)
        grouped_rows.setdefault(group_key, []).append(row)

    batch_codes: list[str] = []
    for (group_cut_date, group_message_no), group_items in grouped_rows.items():
        batch_codes.append(
            save_cut_batch(
                group_items,
                notes=notes,
                source=source,
                cut_date=group_cut_date,
                message_no=group_message_no,
            )
        )
    return batch_codes
