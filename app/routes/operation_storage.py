"""
Manufacturing storage facade for the integrated app (/manufacturing).

The implementation and SQLite database live under app/manufacturing_storage/
and are independent from the standalone حركة التشغيل project folder.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from app.manufacturing_storage import operation_storage as _mod

# One-time bootstrap: if the integrated DB is missing but the legacy copy exists, seed it.
_INTEGRATED_DATA_DIR = Path(_mod.DB_PATH).parent
_LEGACY_DATA_DIR = (
    Path(__file__).resolve().parent.parent.parent / "حركة التشغيل" / "data"
)
if not Path(_mod.DB_PATH).exists() and (_LEGACY_DATA_DIR / "operation.db").exists():
    _INTEGRATED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(_LEGACY_DATA_DIR / "operation.db", _mod.DB_PATH)
    legacy_pwd = _LEGACY_DATA_DIR / "operation_admin_password.txt"
    integrated_pwd = _INTEGRATED_DATA_DIR / "operation_admin_password.txt"
    if legacy_pwd.exists() and not integrated_pwd.exists():
        shutil.copy2(legacy_pwd, integrated_pwd)

# ── Re-export every public symbol ─────────────────────────────────────────
DB_PATH = _mod.DB_PATH
get_connection = _mod.get_connection
initialize_database = _mod.initialize_database
get_setting = _mod.get_setting
set_setting = _mod.set_setting
lookup_product = _mod.lookup_product
get_recent_batches = _mod.get_recent_batches
get_recent_cut_items = _mod.get_recent_cut_items
mark_items_as_accounted = _mod.mark_items_as_accounted
get_accounting_statements = _mod.get_accounting_statements
get_accounting_statement_details = _mod.get_accounting_statement_details
reverse_accounting = _mod.reverse_accounting
get_dashboard_totals = _mod.get_dashboard_totals
purge_cut_data = _mod.purge_cut_data
purge_reference_items = _mod.purge_reference_items
purge_factory_prices = _mod.purge_factory_prices
update_cut_item_dispatch = _mod.update_cut_item_dispatch
bulk_dispatch_cut_items = getattr(_mod, "bulk_dispatch_cut_items", lambda *a, **k: 0)
reverse_cut_item_dispatch = getattr(_mod, "reverse_cut_item_dispatch", lambda *a, **k: None)
delete_cut_item = _mod.delete_cut_item
get_reference_items = _mod.get_reference_items
add_reference_items = _mod.add_reference_items
save_cut_batch = _mod.save_cut_batch
update_item_receipt = _mod.update_item_receipt
process_packing_and_merge = _mod.process_packing_and_merge
get_pending_packing_items = _mod.get_pending_packing_items
get_finished_stock = _mod.get_finished_stock
lookup_factory_price = _mod.lookup_factory_price
get_factory_balance = _mod.get_factory_balance
list_factories = _mod.list_factories
list_factories_with_items = _mod.list_factories_with_items
get_items_for_receiving = _mod.get_items_for_receiving
add_factory_payment = _mod.add_factory_payment
get_payment_receipt_data = _mod.get_payment_receipt_data


def list_factory_prices(limit=300, offset=0, search="", factory_name=""):
    """Extended wrapper supporting offset/search/factory_name filtering."""
    rows = _mod.list_factory_prices(limit=5000)
    if search:
        q = search.strip().lower()
        rows = [
            r
            for r in rows
            if q in str(r.get("factory_name", "")).lower()
            or q in str(r.get("factory_code", "")).lower()
            or q in str(r.get("product_name", "")).lower()
            or q in str(r.get("product_code", "")).lower()
        ]
    if factory_name:
        fn = factory_name.strip().lower()
        rows = [r for r in rows if fn in str(r.get("factory_name", "")).lower()]
    rows = rows[offset:]
    return rows[:limit] if limit else rows


delete_factory_price = _mod.delete_factory_price
add_factory_prices = _mod.add_factory_prices


def set_factory_price(
    factory_code,
    product_code,
    price_per_dozen,
    factory_name=None,
    product_name=None,
    product_size=None,
):
    if not factory_name:
        for f in list_factories():
            if f.get("code") == factory_code:
                factory_name = f.get("name")
                break
    if not product_name or not product_size:
        p = lookup_product(product_code)
        if p:
            product_name = product_name or p.get("name")
            product_size = product_size or p.get("size")

    return add_factory_prices(
        [
            {
                "factory_code": factory_code,
                "product_code": product_code,
                "price_per_dozen": price_per_dozen,
                "factory_name": factory_name or "",
                "product_name": product_name or "",
                "product_size": product_size or "",
            }
        ]
    )


add_factories = _mod.add_factories
delete_factory = _mod.delete_factory


def add_factory(code, name, phone=None, ftype=None, opening_balance=0.0):
    return add_factories(
        [
            {
                "code": code,
                "name": name,
                "phone": phone,
                "type": ftype,
                "opening_balance": opening_balance,
            }
        ]
    )


def import_factories_from_excel(file_storage):
    import pandas as pd

    df = pd.read_excel(file_storage)
    rows = []
    for _, row in df.iterrows():
        code = None
        name = None
        phone = None
        ftype = None
        for col in df.columns:
            col_lower = str(col).lower().strip()
            val = str(row[col]).strip() if pd.notna(row[col]) else None
            if not val:
                continue
            if "كود" in col_lower or "code" in col_lower:
                code = val
            elif "اسم" in col_lower or "name" in col_lower:
                name = val
            elif "تليفون" in col_lower or "phone" in col_lower or "هاتف" in col_lower:
                phone = val
            elif "نوع" in col_lower or "type" in col_lower:
                ftype = val
        if code and name:
            rows.append({"code": code, "name": name, "phone": phone, "type": ftype})
    if rows:
        return add_factories(rows)
    return 0


def get_reference_items(limit: int = 100, offset: int = 0, search: str = "") -> list[dict[str, Any]]:
    with get_connection() as connection:
        if search:
            like_query = f"%{search}%"
            rows = connection.execute(
                """
                SELECT code, name, size
                FROM operation_products
                WHERE code LIKE ? OR name LIKE ? OR size LIKE ?
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                """,
                (like_query, like_query, like_query, limit, offset),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT code, name, size
                FROM operation_products
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()
    return [dict(row) for row in rows]


def count_reference_items(search: str = "") -> int:
    with get_connection() as connection:
        if search:
            like_query = f"%{search}%"
            row = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM operation_products
                WHERE code LIKE ? OR name LIKE ? OR size LIKE ?
                """,
                (like_query, like_query, like_query),
            ).fetchone()
        else:
            row = connection.execute("SELECT COUNT(*) AS total FROM operation_products").fetchone()
    return int(row["total"]) if row else 0


def add_reference_item(code, name, size):
    return _mod.add_reference_items([{"code": code, "name": name, "size": size}])


delete_reference_item = _mod.delete_reference_item


def import_reference_from_excel(file_storage):
    rows, meta = _mod.parse_excel_rows(file_storage)
    if rows:
        return _mod.add_reference_items(rows)
    return 0


def import_prices_from_excel(file_storage):
    rows = _mod.parse_factory_price_rows(file_storage)
    if rows:
        return _mod.add_factory_prices(rows)
    return 0


get_product_packing_history = _mod.get_product_packing_history
get_packing_production_report = _mod.get_packing_production_report
get_cutting_production_report = _mod.get_cutting_production_report
get_message_detailed_report = _mod.get_message_detailed_report
list_factory_payments = _mod.list_factory_payments
delete_factory_payment = _mod.delete_factory_payment
update_factory_opening_balance = _mod.update_factory_opening_balance
get_factory_deficits_report = _mod.get_factory_deficits_report
delete_cut_batch = getattr(_mod, "delete_cut_batch", lambda *a, **k: None)
parse_excel_rows = _mod.parse_excel_rows
parse_factory_price_rows = _mod.parse_factory_price_rows

initialize_database()
