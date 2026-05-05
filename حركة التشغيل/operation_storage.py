from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, List, Dict

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = (BASE_DIR / "data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = (DATA_DIR / "operation.db").resolve()


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS operation_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                size TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS operation_cut_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_code TEXT NOT NULL UNIQUE,
                source TEXT NOT NULL DEFAULT 'manual',
                status TEXT NOT NULL DEFAULT 'داخل القص',
                cut_date TEXT,
                message_no TEXT,
                factory_code TEXT,
                factory_name TEXT,
                received_date TEXT,
                total_items INTEGER NOT NULL DEFAULT 0,
                total_quantity REAL NOT NULL DEFAULT 0,
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS operation_cut_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id INTEGER NOT NULL,
                product_id INTEGER,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                size TEXT NOT NULL,
                quantity REAL NOT NULL DEFAULT 0,
                description TEXT,
                factory_code TEXT,
                factory_name TEXT,
                manufacturing_price REAL NOT NULL DEFAULT 0,
                received_date TEXT,
                dispatch_date TEXT,
                status TEXT NOT NULL DEFAULT 'داخل القص',
                is_accounted INTEGER NOT NULL DEFAULT 0,
                accounted_date TEXT,
                accounting_id TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(batch_id) REFERENCES operation_cut_batches(id) ON DELETE CASCADE,
                FOREIGN KEY(product_id) REFERENCES operation_products(id)
            );

            CREATE TABLE IF NOT EXISTS operation_factory_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                factory_code TEXT NOT NULL,
                factory_name TEXT NOT NULL,
                product_code TEXT NOT NULL,
                product_name TEXT NOT NULL,
                product_size TEXT,
                price_per_dozen REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(factory_code, product_code)
            );

            CREATE INDEX IF NOT EXISTS idx_operation_cut_items_batch
            ON operation_cut_items(batch_id);

            CREATE INDEX IF NOT EXISTS idx_operation_factory_prices_lookup
            ON operation_factory_prices(factory_code, product_code);

            CREATE TABLE IF NOT EXISTS operation_factory_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                factory_code TEXT NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                entry_type TEXT NOT NULL DEFAULT 'سلفة نقدية',
                accounting_id TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_operation_factory_payments_lookup
            ON operation_factory_payments(factory_code);

            CREATE TABLE IF NOT EXISTS operation_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );

            CREATE TABLE IF NOT EXISTS operation_finished_stock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_code TEXT NOT NULL,
                product_name TEXT NOT NULL,
                product_size TEXT NOT NULL,
                quantity REAL NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(product_code, product_size)
            );
            """
        )
        _ensure_batch_columns(connection)
        _ensure_item_columns(connection)
        _ensure_factory_price_columns(connection)
        _ensure_stock_columns(connection)
        _ensure_factory_payments_columns(connection)
        _repair_text_encodings(
            connection,
            [
                ("operation_cut_batches", "status"),
                ("operation_cut_batches", "factory_name"),
                ("operation_cut_items", "status"),
                ("operation_cut_items", "factory_name"),
                ("operation_cut_items", "name"),
                ("operation_products", "name"),
                ("operation_factory_prices", "factory_name"),
                ("operation_factory_prices", "product_name"),
                ("operation_factory_prices", "product_size"),
            ],
        )
        _normalize_date_columns(
            connection,
            [
                ("operation_cut_batches", "cut_date"),
                ("operation_cut_batches", "received_date"),
                ("operation_cut_items", "received_date"),
                ("operation_cut_items", "dispatch_date"),
            ],
        )



def get_setting(key: str, default: Any = None) -> Any:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT value FROM operation_settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default


def set_setting(key: str, value: Any) -> None:
    with get_connection() as connection:
        connection.execute(
            "INSERT OR REPLACE INTO operation_settings (key, value) VALUES (?, ?)",
            (key, str(value)),
        )
        connection.commit()


def lookup_product(code: str) -> dict[str, Any] | None:
    normalized_code = clean_text(code)
    if not normalized_code:
        return None

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, code, name, size
            FROM operation_products
            WHERE code = ?
            """,
            (normalized_code,),
        ).fetchone()

    return dict(row) if row else None


def get_recent_batches(limit: int = 1000) -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT batch_code, source, status, cut_date, message_no,
                   factory_code, factory_name, received_date,
                   total_items, total_quantity, created_at
            FROM operation_cut_batches
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        batches = [dict(row) for row in rows]
        for batch in batches:
            batch["cut_date"] = normalize_date_text(batch.get("cut_date"))
            batch["received_date"] = normalize_date_text(batch.get("received_date"))
        return batches


def get_recent_cut_items(
    limit: int = 1000, delivered: bool | None = None, accounted: bool | None = None
) -> list[dict[str, Any]]:
    query = """
        SELECT
            i.id,
            b.batch_code,
            b.cut_date,
            b.message_no,
            i.code,
            i.name,
            i.size,
            i.quantity,
            i.description,
            i.factory_code,
            i.factory_name,
            i.manufacturing_price,
            COALESCE(i.dispatch_date, i.received_date) AS dispatch_date,
            i.status,
            i.is_accounted,
            i.accounted_date,
            i.accounting_id,
            i.is_received,
            i.received_grade,
            i.received_repairs,
            i.received_added,
            i.received_remainders,
            COALESCE(i.received_good, 0) AS received_good,
            COALESCE(i.received_good_dozens, 0) AS received_good_dozens,
            COALESCE(i.received_good_pieces, 0) AS received_good_pieces,
            i.received_actual_date,
            i.created_at,
            fp.price_per_dozen AS current_reference_price,
            fp.updated_at AS price_updated_at
        FROM operation_cut_items i
        JOIN operation_cut_batches b ON b.id = i.batch_id
        LEFT JOIN operation_factory_prices fp ON (UPPER(fp.factory_code) = UPPER(i.factory_code) AND UPPER(fp.product_code) = UPPER(i.code))
    """
    params: list[Any] = []
    where_clauses: list[str] = []

    if delivered is True:
        where_clauses.append(
            "COALESCE(NULLIF(TRIM(i.status), ''), 'داخل القص') != 'داخل القص'"
        )
    elif delivered is False:
        where_clauses.append(
            "COALESCE(NULLIF(TRIM(i.status), ''), 'داخل القص') = 'داخل القص'"
        )

    if accounted is True:
        where_clauses.append("i.is_accounted = 1")
    elif accounted is False:
        where_clauses.append("i.is_accounted = 0")

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += """
        ORDER BY i.id DESC
        LIMIT ?
    """
    params.append(limit)

    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
    items = [dict(row) for row in rows]
    for item in items:
        item["cut_date"] = normalize_date_text(item.get("cut_date"))
        item["dispatch_date"] = normalize_date_text(item.get("dispatch_date"))
    return items


def mark_items_as_accounted(item_ids: list[int], accounted_date: str, accounting_id: str | None = None) -> int:
    if not item_ids:
        return 0
    with get_connection() as connection:
        placeholders = ",".join(["?"] * len(item_ids))
        cursor = connection.execute(
            f"""
            UPDATE operation_cut_items
            SET is_accounted = 1, accounted_date = ?, accounting_id = ?
            WHERE id IN ({placeholders})
            """,
            [accounted_date, accounting_id] + item_ids,
        )
        connection.commit()
        return cursor.rowcount


def get_accounting_statements(limit: int = 1000) -> list[dict[str, Any]]:
    query = """
        SELECT
            i.accounting_id,
            MAX(i.accounted_date) AS accounted_date,
            MAX(i.factory_code) AS factory_code,
            MAX(i.factory_name) AS factory_name,
            COUNT(*) AS total_items,
            SUM(i.quantity) AS total_quantity,
            SUM(i.quantity * i.manufacturing_price) AS total_amount
        FROM operation_cut_items i
        WHERE i.is_accounted = 1 AND i.accounting_id IS NOT NULL
        GROUP BY i.accounting_id
        ORDER BY accounted_date DESC, i.accounting_id DESC
        LIMIT ?
    """
    with get_connection() as connection:
        rows = connection.execute(query, (limit,)).fetchall()
    return [dict(row) for row in rows]


def get_accounting_statement_details(accounting_id: str) -> dict[str, Any]:
    query_items = """
        SELECT
            i.id,
            b.batch_code,
            b.cut_date,
            b.message_no,
            i.code,
            i.name,
            i.size,
            i.quantity,
            i.manufacturing_price,
            i.status,
            i.accounted_date,
            i.factory_name,
            i.factory_code,
            i.description,
            COALESCE(i.received_good_dozens, 0) AS received_good_dozens,
            COALESCE(i.received_good_pieces, 0) AS received_good_pieces
        FROM operation_cut_items i
        JOIN operation_cut_batches b ON b.id = i.batch_id
        WHERE i.accounting_id = ?
        ORDER BY i.id ASC
    """
    with get_connection() as connection:
        rows = connection.execute(query_items, (accounting_id,)).fetchall()
        items = [dict(row) for row in rows]
        
        if not items:
            return {"items": [], "deduction": 0, "previous_balance": 0, "factory_name": "", "factory_code": ""}
            
        factory_code = items[0]["factory_code"]
        factory_name = items[0]["factory_name"]
        
        # Get the deduction payment associated with this accounting
        payment = connection.execute(
            "SELECT id, amount FROM operation_factory_payments WHERE accounting_id = ? LIMIT 1",
            (accounting_id,)
        ).fetchone()
        
        deduction_amount = 0
        previous_balance = 0
        
        if payment:
            payment_id = payment["id"]
            deduction_amount = -float(payment["amount"] or 0) # Convert back to positive for UI
            
            # Get opening balance
            factory = connection.execute(
                "SELECT opening_balance FROM operation_factories WHERE code = ?",
                (factory_code,)
            ).fetchone()
            opening_balance = float(factory["opening_balance"] or 0) if factory else 0
            
            # Get sum of payments before this one
            prev_sum = connection.execute(
                "SELECT SUM(amount) as s FROM operation_factory_payments WHERE factory_code = ? AND id < ?",
                (factory_code, payment_id)
            ).fetchone()
            previous_payments_sum = float(prev_sum["s"] or 0)
            
            previous_balance = opening_balance + previous_payments_sum
            
        return {
            "items": items,
            "deduction": deduction_amount,
            "previous_balance": previous_balance,
            "factory_name": factory_name,
            "factory_code": factory_code,
            "accounted_date": items[0]["accounted_date"]
        }


def reverse_accounting(accounting_id: str) -> dict[str, Any]:
    if not accounting_id:
        raise ValueError("رقم التسوية مطلوب.")
        
    with get_connection() as connection:
        # First check if there is a deduction from this accounting id in payments
        connection.execute(
            """
            DELETE FROM operation_factory_payments 
            WHERE accounting_id = ?
            """,
            (accounting_id,)
        )
        
        # Then reverse the items
        cursor = connection.execute(
            """
            UPDATE operation_cut_items
            SET 
                is_accounted = 0,
                accounted_date = NULL,
                accounting_id = NULL
            WHERE accounting_id = ?
            """,
            (accounting_id,)
        )
        items_affected = cursor.rowcount
        
        connection.commit()
        
    return {
        "accounting_id": accounting_id,
        "items_affected": items_affected,
        "message": "تم إلغاء التسوية بنجاح واسترجاع القصات."
    }


def get_dashboard_totals(pending_only: bool = False) -> dict[str, Any]:
    where_clause = ""
    if pending_only:
        where_clause = """
            WHERE COALESCE(NULLIF(TRIM(status), ''), 'داخل القص') = 'داخل القص'
        """

    with get_connection() as connection:
        items_row = connection.execute(
            f"""
            SELECT COUNT(*) AS total_items
            FROM operation_cut_items
            {where_clause}
            """
        ).fetchone()
        quantity_row = connection.execute(
            f"""
            SELECT COALESCE(SUM(quantity), 0) AS total_quantity
            FROM operation_cut_items
            {where_clause}
            """
        ).fetchone()
        
        messages_row = connection.execute(
            f"""
            SELECT COUNT(DISTINCT message_no) AS total_messages
            FROM operation_cut_batches
            WHERE id IN (
                SELECT DISTINCT batch_id 
                FROM operation_cut_items 
                {where_clause}
            ) AND message_no IS NOT NULL AND message_no != ''
            """
        ).fetchone()

    return {
        "total_items": int(items_row["total_items"] or 0) if items_row else 0,
        "total_quantity": float(quantity_row["total_quantity"] or 0) if quantity_row else 0.0,
        "total_messages": int(messages_row["total_messages"] or 0) if messages_row else 0,
    }


def purge_cut_data() -> dict[str, Any]:
    with get_connection() as connection:
        counts_row = connection.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM operation_cut_batches) AS total_batches,
                (SELECT COUNT(*) FROM operation_cut_items) AS total_items,
                (SELECT COALESCE(SUM(quantity), 0) FROM operation_cut_items) AS total_quantity
            """
        ).fetchone()

        connection.execute("DELETE FROM operation_cut_items")
        connection.execute("DELETE FROM operation_cut_batches")
        connection.execute(
            """
            DELETE FROM sqlite_sequence
            WHERE name IN ('operation_cut_items', 'operation_cut_batches')
            """
        )
        connection.commit()

    return {
        "deleted_batches": int(counts_row["total_batches"] or 0) if counts_row else 0,
        "deleted_items": int(counts_row["total_items"] or 0) if counts_row else 0,
        "deleted_quantity": float(counts_row["total_quantity"] or 0) if counts_row else 0.0,
    }


def update_cut_item_dispatch(
    item_id: int,
    cut_date: str = "",
    message_no: str = "",
    code: str = "",
    name: str = "",
    size: str = "",
    quantity: Any = "",
    factory_code: str = "",
    factory_name: str = "",
    manufacturing_price: Any = "",
    dispatch_date: str = "",
    description: str = "",
) -> dict[str, Any]:
    try:
        normalized_id = int(item_id)
    except (TypeError, ValueError) as exc:
        raise ValueError("رقم السطر غير صحيح.") from exc

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                i.id,
                i.batch_id,
                i.code,
                i.name,
                i.size,
                i.quantity,
                i.description,
                i.factory_code,
                i.factory_name,
                i.manufacturing_price,
                COALESCE(i.dispatch_date, i.received_date) AS dispatch_date,
                b.message_no,
                b.cut_date
            FROM operation_cut_items i
            JOIN operation_cut_batches b ON b.id = i.batch_id
            WHERE i.id = ?
            """,
            (normalized_id,),
        ).fetchone()
        if not row:
            raise ValueError("السطر المطلوب غير موجود.")

        if cut_date is None:
            normalized_cut_date = normalize_date_text(row["cut_date"])
        else:
            cut_date_text = clean_text(cut_date)
            normalized_cut_date = normalize_date_text(row["cut_date"] if cut_date_text == "" else cut_date_text)

        normalized_message_no = clean_text(message_no) if message_no is not None else clean_text(row["message_no"])
        normalized_code = clean_text(code) if code is not None else clean_text(row["code"])
        normalized_name = clean_text(name) if name is not None else clean_text(row["name"])
        normalized_size = clean_text(size) if size is not None else clean_text(row["size"])

        if quantity is None:
            normalized_quantity = _parse_quantity(row["quantity"])
        else:
            quantity_text = clean_text(quantity)
            normalized_quantity = _parse_quantity(row["quantity"] if quantity_text == "" else quantity_text)

        normalized_description = clean_text(description) if description is not None else clean_text(row["description"])
        normalized_factory_code = clean_text(factory_code) if factory_code is not None else clean_text(row["factory_code"])
        normalized_factory_name = clean_text(factory_name) if factory_name is not None else clean_text(row["factory_name"])
        normalized_manufacturing_price = _resolve_manufacturing_price(
            connection,
            code=normalized_code,
            factory_code=normalized_factory_code,
            raw_price=row["manufacturing_price"] if manufacturing_price is None else manufacturing_price,
            preserve_existing=True,
        )
        if dispatch_date is None:
            normalized_dispatch_date = normalize_date_text(row["dispatch_date"])
        else:
            dispatch_text = clean_text(dispatch_date)
            normalized_dispatch_date = normalize_date_text(row["dispatch_date"] if dispatch_text == "" else dispatch_text)

        if not normalized_code:
            raise ValueError("الكود مطلوب.")
        if not normalized_name:
            raise ValueError("الاسم مطلوب.")
        if not normalized_size:
            raise ValueError("المقاس مطلوب.")

        normalized_code = normalized_code.upper()
        product_id = _upsert_product(connection, normalized_code, normalized_name, normalized_size)

        status_value = (
            "تم الإرسال"
            if normalized_factory_code and normalized_factory_name and normalized_dispatch_date
            else "داخل القص"
        )

        connection.execute(
            """
            UPDATE operation_cut_items
            SET
                product_id = ?,
                code = ?,
                name = ?,
                size = ?,
                quantity = ?,
                description = ?,
                factory_code = ?,
                factory_name = ?,
                manufacturing_price = ?,
                dispatch_date = ?,
                received_date = ?,
                status = ?
            WHERE id = ?
            """,
            (
                product_id,
                normalized_code,
                normalized_name,
                normalized_size,
                normalized_quantity,
                normalized_description,
                normalized_factory_code,
                normalized_factory_name,
                normalized_manufacturing_price,
                normalized_dispatch_date,
                normalized_dispatch_date,
                status_value,
                normalized_id,
            ),
        )

        connection.execute(
            """
            UPDATE operation_cut_batches
            SET cut_date = ?, message_no = ?
            WHERE id = ?
            """,
            (normalized_cut_date, normalized_message_no, int(row["batch_id"])),
        )
        _refresh_batch_totals(connection, int(row["batch_id"]))
        _refresh_batch_status(connection, int(row["batch_id"]))
        connection.commit()

    return {
        "id": normalized_id,
        "cut_date": normalized_cut_date,
        "message_no": normalized_message_no,
        "code": normalized_code,
        "name": normalized_name,
        "size": normalized_size,
        "quantity": normalized_quantity,
        "factory_code": normalized_factory_code,
        "factory_name": normalized_factory_name,
        "manufacturing_price": normalized_manufacturing_price,
        "dispatch_date": normalized_dispatch_date,
        "description": normalized_description,
        "status": status_value,
    }


def reverse_cut_item_dispatch(item_id: int) -> dict[str, Any]:
    """يعيد القصة إلى حالة 'داخل القص' ويمسح بيانات المصنع والتسليم."""
    try:
        normalized_id = int(item_id)
    except (TypeError, ValueError) as exc:
        raise ValueError("رقم السطر غير صحيح.") from exc

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, batch_id, is_accounted
            FROM operation_cut_items
            WHERE id = ?
            """,
            (normalized_id,),
        ).fetchone()
        if not row:
            raise ValueError("القصة المطلوبة غير موجودة.")

        if row["is_accounted"]:
            raise ValueError("لا يمكن التراجع عن تسليم قصة تم محاسبتها فعلياً. يرجى فك التسوية أولاً.")

        batch_id = int(row["batch_id"])

        connection.execute(
            """
            UPDATE operation_cut_items
            SET
                status = 'داخل القص',
                factory_code = NULL,
                factory_name = NULL,
                manufacturing_price = 0,
                dispatch_date = NULL,
                received_date = NULL,
                is_received = 0,
                received_grade = NULL,
                received_repairs = NULL,
                received_added = NULL,
                received_remainders = NULL,
                received_actual_date = NULL
            WHERE id = ?
            """,
            (normalized_id,),
        )

        _refresh_batch_status(connection, batch_id)
        connection.commit()

    return {"id": normalized_id, "status": "داخل القص"}


def delete_cut_item(item_id: int) -> dict[str, Any]:
    try:
        normalized_id = int(item_id)
    except (TypeError, ValueError) as exc:
        raise ValueError("رقم السطر غير صحيح.") from exc

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, batch_id
            FROM operation_cut_items
            WHERE id = ?
            """,
            (normalized_id,),
        ).fetchone()
        if not row:
            raise ValueError("السطر المطلوب غير موجود.")

        batch_id = int(row["batch_id"])
        connection.execute(
            """
            DELETE FROM operation_cut_items
            WHERE id = ?
            """,
            (normalized_id,),
        )

        totals = connection.execute(
            """
            SELECT COUNT(*) AS total_items, COALESCE(SUM(quantity), 0) AS total_quantity
            FROM operation_cut_items
            WHERE batch_id = ?
            """,
            (batch_id,),
        ).fetchone()

        if not totals or int(totals["total_items"] or 0) == 0:
            connection.execute(
                """
                DELETE FROM operation_cut_batches
                WHERE id = ?
                """,
                (batch_id,),
            )
        else:
            connection.execute(
                """
                UPDATE operation_cut_batches
                SET
                    total_items = ?,
                    total_quantity = ?
                WHERE id = ?
                """,
                (
                    int(totals["total_items"] or 0),
                    float(totals["total_quantity"] or 0),
                    batch_id,
                ),
            )
            _refresh_batch_status(connection, batch_id)

        connection.commit()

    return {"id": normalized_id}


def get_reference_items(limit: int = 100) -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT code, name, size
            FROM operation_products
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def add_reference_items(rows: List[Dict[str, Any]]) -> int:
    with get_connection() as connection:
        inserted = 0
        for row in rows:
            if not row.get("code") or not row.get("name") or not row.get("size"):
                continue
            _upsert_product(
                connection,
                row["code"],
                row["name"],
                row["size"],
            )
            inserted += 1
        connection.commit()
    return inserted


def delete_reference_item(code: str) -> dict[str, Any]:
    normalized_code = clean_text(code).upper()
    if not normalized_code:
        raise ValueError("كود الصنف مطلوب.")

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT code
            FROM operation_products
            WHERE UPPER(code) = ?
            """,
            (normalized_code,),
        ).fetchone()
        if not row:
            raise ValueError("الصنف المطلوب غير موجود.")

        connection.execute(
            """
            DELETE FROM operation_products
            WHERE UPPER(code) = ?
            """,
            (normalized_code,),
        )
        connection.commit()

    return {"code": normalized_code}


def list_factory_prices(limit: int = 5000) -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT factory_code, factory_name, product_code, product_name, product_size, price_per_dozen
            FROM operation_factory_prices
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def add_factory_prices(rows: List[Dict[str, Any]]) -> int:
    with get_connection() as connection:
        inserted = 0
        for row in rows:
            factory_code = clean_text(row.get("factory_code")).upper()
            product_code = clean_text(row.get("product_code")).upper()
            factory_name = clean_text(row.get("factory_name"))
            product_name = clean_text(row.get("product_name"))
            product_size = clean_text(row.get("product_size"))
            price_value = _parse_price(row.get("price_per_dozen"))
            if not factory_code or not product_code or not factory_name or not product_name or not product_size:
                continue
            connection.execute(
                """
                INSERT INTO operation_factory_prices (
                    factory_code, factory_name, product_code, product_name, product_size, price_per_dozen
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(factory_code, product_code)
                DO UPDATE SET
                    factory_name = excluded.factory_name,
                    product_name = excluded.product_name,
                    product_size = excluded.product_size,
                    price_per_dozen = excluded.price_per_dozen,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (factory_code, factory_name, product_code, product_name, product_size, price_value),
            )
            inserted += 1
        connection.commit()
    return inserted


def delete_factory_price(factory_code: str, product_code: str) -> dict[str, Any]:
    normalized_factory_code = clean_text(factory_code).upper()
    normalized_product_code = clean_text(product_code).upper()
    if not normalized_factory_code or not normalized_product_code:
        raise ValueError("كود المصنع وكود الصنف مطلوبان.")

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id
            FROM operation_factory_prices
            WHERE UPPER(factory_code) = ? AND UPPER(product_code) = ?
            """,
            (normalized_factory_code, normalized_product_code),
        ).fetchone()
        if not row:
            raise ValueError("سعر التصنيع المطلوب غير موجود.")

        connection.execute(
            """
            DELETE FROM operation_factory_prices
            WHERE UPPER(factory_code) = ? AND UPPER(product_code) = ?
            """,
            (normalized_factory_code, normalized_product_code),
        )
        connection.commit()

    return {"factory_code": normalized_factory_code, "product_code": normalized_product_code}


def lookup_factory_price(factory_code: str, product_code: str) -> dict[str, Any] | None:
    normalized_factory_code = clean_text(factory_code).upper()
    normalized_product_code = clean_text(product_code).upper()
    if not normalized_factory_code or not normalized_product_code:
        return None

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT factory_code, factory_name, product_code, product_name, product_size, price_per_dozen, updated_at
            FROM operation_factory_prices
            WHERE UPPER(factory_code) = ? AND UPPER(product_code) = ?
            """,
            (normalized_factory_code, normalized_product_code),
        ).fetchone()

    return dict(row) if row else None


def purge_factory_prices() -> dict[str, Any]:
    with get_connection() as connection:
        counts_row = connection.execute(
            """
            SELECT COUNT(*) AS total_prices
            FROM operation_factory_prices
            """
        ).fetchone()

        connection.execute("DELETE FROM operation_factory_prices")
        connection.execute(
            """
            DELETE FROM sqlite_sequence
            WHERE name = 'operation_factory_prices'
            """
        )
        connection.commit()

    return {
        "deleted_prices": int(counts_row["total_prices"] or 0) if counts_row else 0,
    }


def save_cut_batch(
    raw_rows: list[dict[str, Any]],
    notes: str = "",
    source: str = "manual",
    cut_date: str = "",
    message_no: str = "",
) -> str:
    with get_connection() as connection:
        rows = _normalize_rows(raw_rows, connection)
        if not rows:
            raise ValueError("لا يوجد أي سطر صالح للحفظ.")

        batch_code = _generate_batch_code(connection)
        total_quantity = sum(row["quantity"] for row in rows)

        status_value = "تم الإرسال" if all(r.get("dispatched") for r in rows) else "داخل القص"

        cursor = connection.execute(
            """
            INSERT INTO operation_cut_batches (
                batch_code,
                source,
                status,
                cut_date,
                message_no,
                total_items,
                total_quantity,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                batch_code,
                source,
                status_value,
                normalize_date_text(cut_date),
                clean_text(message_no),
                len(rows),
                total_quantity,
                clean_text(notes),
            ),
        )
        batch_id = cursor.lastrowid

        for row in rows:
            product_id = _upsert_product(connection, row["code"], row["name"], row["size"])
            connection.execute(
                """
                INSERT INTO operation_cut_items (
                    batch_id,
                    product_id,
                    code,
                    name,
                    size,
                    quantity,
                    description,
                    factory_code,
                    factory_name,
                    manufacturing_price,
                    received_date,
                    dispatch_date,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    batch_id,
                    product_id,
                    row["code"],
                    row["name"],
                    row["size"],
                    row["quantity"],
                    row.get("description"),
                    row.get("factory_code"),
                    row.get("factory_name"),
                    row.get("manufacturing_price", 0),
                    row.get("received_date"),
                    row.get("dispatch_date"),
                    "تم الإرسال" if row.get("dispatched") else "داخل القص",
                ),
            )

        connection.commit()
        return batch_code


def parse_excel_rows(file_storage: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    data_frame = pd.read_excel(file_storage)
    if data_frame.empty:
        raise ValueError("الملف لا يحتوي على أي بيانات.")

    columns = {normalize_column_name(column): column for column in data_frame.columns}

    code_column = _find_column(columns, ["code", "itemcode", "الكود", "كود", "كودالصنف", "رمز"])
    name_column = _find_column(columns, ["name", "itemname", "productname", "الاسم", "اسم", "اسمالصنف", "الصنف"])
    size_column = _find_column(columns, ["size", "المقاس", "مقاس", "القطعه", "القطعة", "قطعه"], required=False)
    quantity_column = _find_column(columns, ["quantity", "qty", "الكمية", "كمية"])
    description_column = _find_column(
        columns,
        ["description", "desc", "الوصف", "وصف", "البيان", "بيان"],
        required=False,
    )
    color_column = _find_column(columns, ["color", "colour", "اللون"], required=False)
    cut_date_column = _find_column(columns, ["cutdate", "تاريخالقص", "تاريخ القص"], required=False)
    message_column = _find_column(columns, ["messageno", "message_no", "رقمالرسالة", "رقم الرسالة"], required=False)

    rows: list[dict[str, Any]] = []
    meta: dict[str, Any] = {}
    for _, row in data_frame.iterrows():
        code = excel_cell_to_text(row.get(code_column))
        name = excel_cell_to_text(row.get(name_column))
        size = excel_cell_to_text(row.get(size_column)) if size_column else ""
        quantity = excel_cell_to_text(row.get(quantity_column)) if quantity_column else ""
        description = excel_cell_to_text(row.get(description_column)) if description_column else ""
        color = excel_cell_to_text(row.get(color_column)) if color_column else ""
        cut_date = normalize_date_text(row.get(cut_date_column)) if cut_date_column else ""
        message_no = excel_cell_to_text(row.get(message_column)) if message_column else ""

        if not any([code, name, size, quantity, color]):
            continue

        rows.append({
            "code": code,
            "name": name,
            "size": size or color,
            "quantity": quantity,
            "description": description,
            "color": color,
            "cut_date": cut_date,
            "message_no": message_no,
        })

        if not meta.get("cut_date") and cut_date:
            meta["cut_date"] = cut_date
        if not meta.get("message_no") and message_no:
            meta["message_no"] = message_no

    if not rows:
        raise ValueError("لم أجد صفوفًا قابلة للاستيراد داخل الملف.")

    return rows, meta


def parse_factory_price_rows(file_storage: Any) -> list[dict[str, Any]]:
    data_frame = pd.read_excel(file_storage)
    if data_frame.empty:
        raise ValueError("الملف لا يحتوي على أي بيانات.")

    raw_columns = list(data_frame.columns)
    normalized_columns = [
        "".join(str(column).strip().lower().replace("_", "").replace("-", "").replace(".", "").split())
        for column in raw_columns
    ]

    def find_column_index(candidates: list[str], excluded: set[int] | None = None) -> int | None:
        excluded = excluded or set()
        normalized_candidates = {
            "".join(candidate.strip().lower().replace("_", "").replace("-", "").replace(".", "").split())
            for candidate in candidates
        }
        for index, value in enumerate(normalized_columns):
            if index in excluded:
                continue
            if value in normalized_candidates:
                return index
        return None

    factory_code_index = find_column_index(["factorycode", "factory_code", "كودالمصنع", "كود المصنع"])
    factory_name_index = find_column_index(["factoryname", "factory_name", "اسمالمصنع", "اسم المصنع"])
    product_code_index = find_column_index(
        ["productcode", "itemcode", "product_code", "كودالصنف", "كود الصنف"],
        {factory_code_index} if factory_code_index is not None else None,
    )
    product_name_index = find_column_index(["productname", "itemname", "product_name", "اسمالصنف", "اسم الصنف"])
    product_size_index = find_column_index(["productsize", "size", "المقاس", "مقاس"])
    price_index = find_column_index(["priceperdozen", "price_per_dozen", "dozenprice", "سعرالدستة", "سعر الدستة"])

    if None in {factory_code_index, factory_name_index, product_code_index, product_name_index, product_size_index, price_index}:
        if len(raw_columns) >= 6:
            factory_code_index = 0
            factory_name_index = 1
            product_code_index = 2
            product_name_index = 3
            product_size_index = 4
            price_index = 5
        else:
            raise ValueError(
                "ملف أسعار التصنيع يجب أن يحتوي على: كود المصنع، اسم المصنع، كود الصنف، اسم الصنف، المقاس، سعر الدستة."
            )

    rows: list[dict[str, Any]] = []
    for _, row in data_frame.iterrows():
        factory_code = excel_cell_to_text(row.iloc[factory_code_index]).upper()
        factory_name = excel_cell_to_text(row.iloc[factory_name_index])
        product_code = excel_cell_to_text(row.iloc[product_code_index]).upper()
        product_name = excel_cell_to_text(row.iloc[product_name_index])
        product_size = excel_cell_to_text(row.iloc[product_size_index]) if product_size_index is not None else ""
        price_per_dozen = excel_cell_to_text(row.iloc[price_index])

        if not any([factory_code, factory_name, product_code, product_name, product_size, price_per_dozen]):
            continue

        rows.append(
            {
                "factory_code": factory_code,
                "factory_name": factory_name,
                "product_code": product_code,
                "product_name": product_name,
                "product_size": product_size,
                "price_per_dozen": price_per_dozen,
            }
        )

    if not rows:
        raise ValueError("لم أجد صفوفًا قابلة للاستيراد داخل الملف.")

    return rows


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def excel_cell_to_text(value: Any) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    if pd.isna(value):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def normalize_date_text(value: Any) -> str:
    if value is None:
        return ""

    if pd.isna(value):
        return ""

    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")

    text = clean_text(value)
    if not text:
        return ""
    if text.lower() == "nat":
        return ""

    normalized_text = text
    if "T" in normalized_text:
        normalized_text = normalized_text.split("T", 1)[0]
    if " " in normalized_text and ":" in normalized_text:
        normalized_text = normalized_text.split(" ", 1)[0]
    normalized_text = normalized_text.replace("-", "/").replace(".", "/")

    formats = [
        "%d/%m/%Y",
        "%d/%m/%y",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%m/%d/%y",
    ]
    for fmt in formats:
        try:
            parsed = datetime.strptime(normalized_text, fmt)
            return parsed.strftime("%d/%m/%Y")
        except ValueError:
            continue

    try:
        parsed = pd.to_datetime(text, errors="coerce", dayfirst=True)
        if not pd.isna(parsed):
            return parsed.to_pydatetime().strftime("%d/%m/%Y")
    except Exception:
        pass

    return text


def normalize_column_name(value: Any) -> str:
    return "".join(str(value).strip().lower().replace("_", "").replace("-", "").split())


def _find_column(
    columns: dict[str, str],
    candidates: list[str],
    required: bool = True,
) -> str | None:
    for candidate in candidates:
        found = columns.get(normalize_column_name(candidate))
        if found:
            return found

    if required:
        raise ValueError("ملف Excel يجب أن يحتوي على أعمدة الكود والاسم والمقاس/القطعة والكمية.")
    return None


def _normalize_rows(
    raw_rows: list[dict[str, Any]],
    connection: sqlite3.Connection,
) -> list[dict[str, Any]]:
    normalized_rows: list[dict[str, Any]] = []

    for index, raw_row in enumerate(raw_rows, start=1):
        code = clean_text(raw_row.get("code"))
        name = clean_text(raw_row.get("name"))
        size = clean_text(raw_row.get("size"))
        quantity = _parse_quantity(raw_row.get("quantity"))
        description = clean_text(raw_row.get("description"))
        factory_code = clean_text(raw_row.get("factory_code"))
        factory_name = clean_text(raw_row.get("factory_name"))
        manufacturing_price = _resolve_manufacturing_price(
            connection,
            code=code,
            factory_code=factory_code,
            raw_price=raw_row.get("manufacturing_price"),
        )
        dispatch_date = normalize_date_text(raw_row.get("dispatch_date")) or normalize_date_text(raw_row.get("received_date"))

        if not any([code, name, size, raw_row.get("quantity")]):
            continue

        if not code:
            raise ValueError(f"السطر رقم {index} يحتاج إلى كود.")

        stored_product = connection.execute(
            """
            SELECT name, size
            FROM operation_products
            WHERE code = ?
            """,
            (code,),
        ).fetchone()

        if stored_product:
            if not name:
                name = stored_product["name"]
            if not size:
                size = stored_product["size"]

        if not name:
            raise ValueError(f"السطر رقم {index} يحتاج إلى اسم الصنف.")
        if not size:
            raise ValueError(f"السطر رقم {index} يحتاج إلى المقاس.")

        normalized_rows.append(
            {
                "code": code,
                "name": name,
                "size": size,
                "quantity": quantity,
                "description": description,
                "factory_code": factory_code,
                "factory_name": factory_name,
                "manufacturing_price": manufacturing_price,
                "received_date": dispatch_date,
                "dispatch_date": dispatch_date,
                "dispatched": bool(factory_code and factory_name and dispatch_date),
            }
        )

    return normalized_rows


def _parse_quantity(value: Any) -> float:
    text = clean_text(value)
    if not text:
        return 0.0
    try:
        quantity = float(text)
    except ValueError as exc:
        raise ValueError(f"قيمة الكمية غير صحيحة: {text}") from exc

    if quantity < 0:
        raise ValueError("الكمية لا يمكن أن تكون أقل من صفر.")
    return quantity


def _parse_price(value: Any) -> float:
    text = clean_text(value)
    if not text:
        return 0.0
    try:
        price = float(text)
    except ValueError as exc:
        raise ValueError(f"قيمة السعر غير صحيحة: {text}") from exc

    if price < 0:
        raise ValueError("السعر لا يمكن أن يكون أقل من صفر.")
    return price


def _resolve_manufacturing_price(
    connection: sqlite3.Connection,
    code: str,
    factory_code: str,
    raw_price: Any,
    preserve_existing: bool = False,
) -> float:
    if preserve_existing:
        price_text = clean_text(raw_price)
        if price_text != "":
            return _parse_price(raw_price)
    else:
        if clean_text(raw_price):
            return _parse_price(raw_price)

    normalized_code = clean_text(code).upper()
    normalized_factory_code = clean_text(factory_code).upper()
    if not normalized_code or not normalized_factory_code:
        return _parse_price(raw_price) if clean_text(raw_price) else 0.0

    row = connection.execute(
        """
        SELECT price_per_dozen
        FROM operation_factory_prices
        WHERE UPPER(factory_code) = ? AND UPPER(product_code) = ?
        """,
        (normalized_factory_code, normalized_code),
    ).fetchone()
    if row:
        return float(row["price_per_dozen"] or 0)

    return _parse_price(raw_price) if clean_text(raw_price) else 0.0


def _upsert_product(
    connection: sqlite3.Connection,
    code: str,
    name: str,
    size: str,
) -> int:
    connection.execute(
        """
        INSERT INTO operation_products (code, name, size)
        VALUES (?, ?, ?)
        ON CONFLICT(code)
        DO UPDATE SET
            name = excluded.name,
            size = excluded.size,
            updated_at = CURRENT_TIMESTAMP
        """,
        (code, name, size),
    )

    row = connection.execute(
        """
        SELECT id
        FROM operation_products
        WHERE code = ?
        """,
        (code,),
    ).fetchone()
    return int(row["id"])


def _generate_batch_code(connection: sqlite3.Connection) -> str:
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"CUT-{today}-"
    row = connection.execute(
        """
        SELECT batch_code
        FROM operation_cut_batches
        WHERE batch_code LIKE ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (f"{prefix}%",),
    ).fetchone()

    if row:
        current_sequence = int(str(row["batch_code"]).rsplit("-", 1)[-1])
    else:
        current_sequence = 0

    return f"{prefix}{current_sequence + 1:03d}"


def _refresh_batch_totals(connection: sqlite3.Connection, batch_id: int) -> tuple[int, float]:
    totals_row = connection.execute(
        """
        SELECT COUNT(*) AS total_items, COALESCE(SUM(quantity), 0) AS total_quantity
        FROM operation_cut_items
        WHERE batch_id = ?
        """,
        (batch_id,),
    ).fetchone()

    total_items = int(totals_row["total_items"] or 0) if totals_row else 0
    total_quantity = float(totals_row["total_quantity"] or 0) if totals_row else 0.0

    connection.execute(
        """
        UPDATE operation_cut_batches
        SET
            total_items = ?,
            total_quantity = ?
        WHERE id = ?
        """,
        (total_items, total_quantity, batch_id),
    )
    return total_items, total_quantity


def _refresh_batch_status(connection: sqlite3.Connection, batch_id: int) -> None:
    pending_row = connection.execute(
        """
        SELECT
            SUM(
                CASE
                    WHEN TRIM(COALESCE(factory_code, '')) != ''
                     AND TRIM(COALESCE(factory_name, '')) != ''
                     AND TRIM(COALESCE(dispatch_date, received_date, '')) != ''
                    THEN 0
                    ELSE 1
                END
            ) AS pending_rows
        FROM operation_cut_items
        WHERE batch_id = ?
        """,
        (batch_id,),
    ).fetchone()

    pending_rows = int(pending_row["pending_rows"] or 0) if pending_row else 0
    status_value = "تم الإرسال" if pending_rows == 0 else "داخل القص"

    summary_row = connection.execute(
        """
        SELECT
            CASE
                WHEN COUNT(DISTINCT NULLIF(TRIM(factory_name), '')) = 1
                    THEN MAX(NULLIF(TRIM(factory_name), ''))
                WHEN COUNT(DISTINCT NULLIF(TRIM(factory_name), '')) > 1
                    THEN 'متعدد المصانع'
                ELSE NULL
            END AS factory_name_value,
            CASE
                WHEN COUNT(DISTINCT NULLIF(TRIM(factory_code), '')) = 1
                    THEN MAX(NULLIF(TRIM(factory_code), ''))
                ELSE NULL
            END AS factory_code_value,
            CASE
                WHEN COUNT(DISTINCT NULLIF(TRIM(COALESCE(dispatch_date, received_date)), '')) = 1
                    THEN MAX(NULLIF(TRIM(COALESCE(dispatch_date, received_date)), ''))
                ELSE NULL
            END AS dispatch_date_value
        FROM operation_cut_items
        WHERE batch_id = ?
        """,
        (batch_id,),
    ).fetchone()

    connection.execute(
        """
        UPDATE operation_cut_batches
        SET
            status = ?,
            factory_code = ?,
            factory_name = ?,
            received_date = ?
        WHERE id = ?
        """,
        (
            status_value,
            summary_row["factory_code_value"] if summary_row else None,
            summary_row["factory_name_value"] if summary_row else None,
            summary_row["dispatch_date_value"] if summary_row else None,
            batch_id,
        ),
    )


def _ensure_batch_columns(connection: sqlite3.Connection) -> None:
    info = connection.execute("PRAGMA table_info(operation_cut_batches)").fetchall()
    existing = {col["name"] for col in info} if info and isinstance(info[0], sqlite3.Row) else {c[1] for c in info}

    def add_column(name: str, ddl: str) -> None:
        if name not in existing:
            connection.execute(f"ALTER TABLE operation_cut_batches ADD COLUMN {name} {ddl}")

    add_column("cut_date", "TEXT")
    add_column("message_no", "TEXT")
    add_column("factory_code", "TEXT")
    add_column("factory_name", "TEXT")
    add_column("received_date", "TEXT")


def _ensure_item_columns(connection: sqlite3.Connection) -> None:
    info = connection.execute("PRAGMA table_info(operation_cut_items)").fetchall()
    existing = {col["name"] for col in info} if info and isinstance(info[0], sqlite3.Row) else {c[1] for c in info}

    def add_column(name: str, ddl: str) -> None:
        if name not in existing:
            connection.execute(f"ALTER TABLE operation_cut_items ADD COLUMN {name} {ddl}")

    add_column("description", "TEXT")
    add_column("factory_code", "TEXT")
    add_column("factory_name", "TEXT")
    add_column("manufacturing_price", "REAL NOT NULL DEFAULT 0")
    add_column("received_date", "TEXT")
    add_column("dispatch_date", "TEXT")
    add_column("is_accounted", "INTEGER NOT NULL DEFAULT 0")
    add_column("accounted_date", "TEXT")
    add_column("accounting_id", "TEXT")
    add_column("is_received", "INTEGER NOT NULL DEFAULT 0")
    add_column("received_grade", "REAL")
    add_column("received_repairs", "REAL")
    add_column("received_added", "REAL")
    add_column("received_remainders", "REAL")
    add_column("received_good", "REAL")
    add_column("received_good_dozens", "REAL DEFAULT 0")
    add_column("received_good_pieces", "REAL DEFAULT 0")
    add_column("received_actual_date", "TEXT")
    add_column("is_packed", "INTEGER NOT NULL DEFAULT 0")
    add_column("delivery_note_no", "TEXT")
    add_column("packing_department", "TEXT")

    # إصلاح البيانات القديمة للمستلم
    connection.execute("""
        UPDATE operation_cut_items 
        SET received_good_pieces = received_good 
        WHERE is_received = 1 AND (received_good > 0 OR received_good IS NOT NULL)
          AND (received_good_dozens IS NULL OR received_good_dozens = 0)
          AND (received_good_pieces IS NULL OR received_good_pieces = 0)
    """)


def _ensure_factory_price_columns(connection: sqlite3.Connection) -> None:
    info = connection.execute("PRAGMA table_info(operation_factory_prices)").fetchall()
    existing = {col["name"] for col in info} if info and isinstance(info[0], sqlite3.Row) else {c[1] for c in info}

    def add_column(name: str, ddl: str) -> None:
        if name not in existing:
            connection.execute(f"ALTER TABLE operation_factory_prices ADD COLUMN {name} {ddl}")

    add_column("factory_name", "TEXT")
    add_column("product_name", "TEXT")
    add_column("product_size", "TEXT")
    add_column("price_per_dozen", "REAL NOT NULL DEFAULT 0")
    add_column("updated_at", "TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP")


def _ensure_stock_columns(connection: sqlite3.Connection) -> None:
    info = connection.execute("PRAGMA table_info(operation_finished_stock)").fetchall()
    existing = {col["name"] for col in info} if info and isinstance(info[0], sqlite3.Row) else {c[1] for c in info}

    def add_column(name: str, ddl: str) -> None:
        if name not in existing:
            connection.execute(f"ALTER TABLE operation_finished_stock ADD COLUMN {name} {ddl}")

    add_column("dozens_qty", "REAL DEFAULT 0")
    add_column("pieces_qty", "REAL DEFAULT 0")

    # إصلاح رصيد المخزن القديم
    connection.execute("""
        UPDATE operation_finished_stock 
        SET pieces_qty = quantity 
        WHERE (quantity > 0 OR quantity IS NOT NULL)
          AND (dozens_qty IS NULL OR dozens_qty = 0)
          AND (pieces_qty IS NULL OR pieces_qty = 0)
    """)
 
 
def _ensure_factory_payments_columns(connection: sqlite3.Connection) -> None:
    info = connection.execute("PRAGMA table_info(operation_factory_payments)").fetchall()
    existing = {col["name"] for col in info} if info and isinstance(info[0], sqlite3.Row) else {c[1] for c in info}
 
    def add_column(name: str, ddl: str) -> None:
        if name not in existing:
            connection.execute(f"ALTER TABLE operation_factory_payments ADD COLUMN {name} {ddl}")
 
    add_column("accounting_id", "TEXT")


def _repair_text_encodings(
    connection: sqlite3.Connection,
    targets: list[tuple[str, str]],
) -> None:
    for table_name, column_name in targets:
        try:
            rows = connection.execute(
                f"""
                SELECT id, {column_name}
                FROM {table_name}
                WHERE {column_name} IS NOT NULL AND {column_name} != ''
                """
            ).fetchall()
        except sqlite3.OperationalError:
            continue

        for row in rows:
            original_value = row[column_name]
            fixed_value = _decode_mojibake_text(original_value)
            if fixed_value != original_value:
                connection.execute(
                    f"UPDATE {table_name} SET {column_name} = ? WHERE id = ?",
                    (fixed_value, row["id"]),
                )


def _normalize_date_columns(
    connection: sqlite3.Connection,
    targets: list[tuple[str, str]],
) -> None:
    for table_name, column_name in targets:
        try:
            rows = connection.execute(
                f"""
                SELECT id, {column_name}
                FROM {table_name}
                WHERE {column_name} IS NOT NULL AND TRIM({column_name}) != ''
                """
            ).fetchall()
        except sqlite3.OperationalError:
            continue

        for row in rows:
            original_value = row[column_name]
            normalized_value = normalize_date_text(original_value)
            if normalized_value != original_value:
                connection.execute(
                    f"UPDATE {table_name} SET {column_name} = ? WHERE id = ?",
                    (normalized_value, row["id"]),
                )


def _decode_mojibake_text(value: str) -> str:
    if not isinstance(value, str):
        return value
    if not _looks_like_mojibake(value):
        return value

    try:
        decoded = value.encode("cp1256").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value

    if _mojibake_score(decoded) < _mojibake_score(value):
        return decoded
    return value


def _looks_like_mojibake(value: str) -> bool:
    has_arabic = any("\u0600" <= ch <= "\u06FF" for ch in value)
    has_noisy_chars = any(0x00A0 <= ord(ch) <= 0x00FF for ch in value) or any(
        0x2018 <= ord(ch) <= 0x203A for ch in value
    ) or any(ch in "âÃØÙ" for ch in value)
    return has_arabic and has_noisy_chars


def _mojibake_score(value: str) -> int:
    return sum(
        1
        for ch in value
        if (0x00A0 <= ord(ch) <= 0x00FF)
        or (0x2018 <= ord(ch) <= 0x203A)
        or ch in "âÃØÙ"
    )


def initialize_factories_table() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS operation_factories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'خارجي',
                phone TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        _ensure_factories_columns(connection)
        _repair_text_encodings(
            connection,
            [
                ("operation_factories", "name"),
                ("operation_factories", "type"),
            ],
        )
        connection.commit()


def add_factories(rows: List[Dict[str, Any]]) -> int:
    with get_connection() as connection:
        inserted = 0
        for row in rows:
            code = clean_text(row.get("code"))
            name = clean_text(row.get("name"))
            ftype = clean_text(row.get("type") or "خارجي")
            phone = clean_text(row.get("phone"))
            opening_balance = float(row.get("opening_balance") or 0)
            if not code or not name:
                continue
            connection.execute(
                """
                INSERT INTO operation_factories (code, name, type, phone, opening_balance)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(code) DO UPDATE SET
                    name = excluded.name,
                    type = excluded.type,
                    phone = excluded.phone,
                    opening_balance = excluded.opening_balance
                """,
                (code, name, ftype, phone, opening_balance),
            )
            inserted += 1
        connection.commit()
        return inserted


def add_factory_payment(
    factory_code: str,
    amount: float,
    date: str,
    description: str,
    entry_type: str = "سلفة نقدية",
    accounting_id: str = None,
) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO operation_factory_payments (factory_code, amount, date, description, entry_type, accounting_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (factory_code, amount, date, description, entry_type, accounting_id),
        )
        connection.commit()
        return cursor.lastrowid


def list_factory_payments(factory_code: str, limit: int = 1000) -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, factory_code, amount, date, description, entry_type, created_at
            FROM operation_factory_payments
            WHERE factory_code = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (factory_code, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def delete_factory_payment(payment_id: int) -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM operation_factory_payments WHERE id = ?", (payment_id,)
        )
        connection.commit()
        return cursor.rowcount


def get_payment_receipt_data(payment_id: int) -> dict[str, Any]:
    with get_connection() as connection:
        payment = connection.execute(
            "SELECT * FROM operation_factory_payments WHERE id = ?",
            (payment_id,)
        ).fetchone()
        
        if not payment:
            raise ValueError("الحركة المالية غير موجودة")
            
        factory = connection.execute(
            "SELECT name, opening_balance FROM operation_factories WHERE code = ?",
            (payment["factory_code"],)
        ).fetchone()
        
        if not factory:
            raise ValueError("المصنع غير موجود")
            
        prev_payments = connection.execute(
            "SELECT SUM(amount) as sum_amount FROM operation_factory_payments WHERE factory_code = ? AND id < ?",
            (payment["factory_code"], payment_id)
        ).fetchone()
        
        prev_sum = float(prev_payments["sum_amount"] or 0)
        opening = float(factory["opening_balance"] or 0)
        previous_balance = opening + prev_sum
        amount = float(payment["amount"] or 0)
        current_balance = previous_balance + amount
        
        return {
            "payment_id": payment_id,
            "date": payment["date"],
            "description": payment["description"] or payment["entry_type"],
            "entry_type": payment["entry_type"],
            "amount": amount,
            "factory_code": payment["factory_code"],
            "factory_name": factory["name"],
            "previous_balance": previous_balance,
            "current_balance": current_balance,
        }


def get_factory_balance(factory_code: str) -> dict[str, Any]:
    with get_connection() as connection:
        factory = connection.execute(
            "SELECT name, opening_balance FROM operation_factories WHERE code = ?",
            (factory_code,),
        ).fetchone()
        if not factory:
            return {"factory_code": factory_code, "found": False}

        payments_sum = connection.execute(
            "SELECT SUM(amount) as total FROM operation_factory_payments WHERE factory_code = ?",
            (factory_code,),
        ).fetchone()

        total_payments = float(payments_sum["total"] or 0)
        current_balance = float(factory["opening_balance"] or 0) + total_payments

        return {
            "factory_code": factory_code,
            "factory_name": factory["name"],
            "opening_balance": factory["opening_balance"],
            "total_payments_movements": total_payments,
            "current_balance": current_balance,
            "found": True,
        }


def update_factory_opening_balance(factory_code: str, amount: float) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            "UPDATE operation_factories SET opening_balance = ? WHERE code = ?",
            (amount, factory_code),
        )
        connection.commit()
        return cursor.rowcount > 0


def list_factories(limit: int = 300) -> List[Dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT code, name, type, phone
            FROM operation_factories
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def list_factories_with_items() -> List[Dict[str, Any]]:
    """يجلب المصانع التي عندها قصات لم تُستلم بعد."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT
                TRIM(i.factory_code) AS code,
                TRIM(i.factory_name) AS name,
                COUNT(*) AS item_count
            FROM operation_cut_items i
            WHERE
                TRIM(COALESCE(i.factory_code, '')) != ''
                AND TRIM(COALESCE(i.factory_name, '')) != ''
                AND COALESCE(i.is_received, 0) = 0
                AND COALESCE(NULLIF(TRIM(i.status), ''), 'داخل القص') != 'داخل القص'
            GROUP BY TRIM(i.factory_code), TRIM(i.factory_name)
            ORDER BY name
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_items_for_receiving(
    factory_code: str | None = None, limit: int = 2000
) -> list[dict[str, Any]]:
    """يجلب القصات المُرسلة للمصانع والتي لم يتم استلامها بعد."""
    query = """
        SELECT
            i.id,
            b.batch_code,
            b.cut_date,
            b.message_no,
            i.code,
            i.name,
            i.size,
            i.quantity,
            i.description,
            i.factory_code,
            i.factory_name,
            i.manufacturing_price,
            COALESCE(i.dispatch_date, i.received_date) AS dispatch_date,
            i.status,
            i.is_accounted,
            i.is_received,
            i.received_grade,
            i.received_repairs,
            i.received_added,
            i.received_remainders,
            i.received_actual_date,
            COALESCE(i.received_good_dozens, 0) AS received_good_dozens,
            COALESCE(i.received_good_pieces, 0) AS received_good_pieces
        FROM operation_cut_items i
        JOIN operation_cut_batches b ON b.id = i.batch_id
        WHERE
            COALESCE(i.is_received, 0) = 0
            AND COALESCE(NULLIF(TRIM(i.status), ''), 'داخل القص') != 'داخل القص'
    """
    params: list[Any] = []
    if factory_code:
        normalized = clean_text(factory_code).upper()
        query += " AND UPPER(TRIM(i.factory_code)) = ?"
        params.append(normalized)

    query += " ORDER BY i.factory_name, b.cut_date, i.id DESC LIMIT ?"
    params.append(limit)

    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
    items = [dict(row) for row in rows]
    for item in items:
        item["cut_date"] = normalize_date_text(item.get("cut_date"))
        item["dispatch_date"] = normalize_date_text(item.get("dispatch_date"))
        item["received_actual_date"] = normalize_date_text(item.get("received_actual_date"))
    return items


def get_pending_packing_items(limit: int = 1000) -> list[dict[str, Any]]:
    """يجلب الأصناف التي تم استلامها ولم يتم تعبئتها بعد (بانتظار الدمج والتعبئة)."""
    query = """
        SELECT
            i.id, b.batch_code, b.message_no, b.cut_date, i.code, i.name, i.size, i.quantity,
            i.factory_name,
            COALESCE(i.received_good, 0) AS received_good,
            COALESCE(i.received_good_dozens, 0) AS received_good_dozens,
            COALESCE(i.received_good_pieces, 0) AS received_good_pieces,
            i.received_actual_date, i.is_packed
        FROM operation_cut_items i
        JOIN operation_cut_batches b ON b.id = i.batch_id
        WHERE i.is_received = 1 AND COALESCE(i.is_packed, 0) = 0
        ORDER BY b.cut_date DESC, i.code ASC
        LIMIT ?
    """
    with get_connection() as connection:
        rows = connection.execute(query, (limit,)).fetchall()
    return [dict(row) for row in rows]


def get_finished_stock(limit: int = 2000) -> list[dict[str, Any]]:
    """يجلب رصيد مخزن المنتج التام الحالي."""
    query = """
        SELECT id, product_code, product_name, product_size, quantity, quantity AS total_pieces,
               COALESCE(dozens_qty, 0) AS dozens_qty, COALESCE(pieces_qty, 0) AS pieces_qty, updated_at 
        FROM operation_finished_stock 
        ORDER BY product_code ASC, product_size ASC 
        LIMIT ?
    """
    with get_connection() as connection:
        rows = connection.execute(query, (limit,)).fetchall()
    return [dict(row) for row in rows]


def get_factory_deficits_report(factory_code: str = None) -> list[dict[str, Any]]:
    """جلب القصات التي تم استلامها وبها عجز (المتبقي بالسالب حسب طلب المستخدم)."""
    with get_connection() as connection:
        query = """
            SELECT 
                i.id, i.code, i.name, i.size, i.quantity as original_qty,
                i.received_grade, i.received_repairs, i.received_added, i.received_remainders,
                i.received_good, i.received_good_dozens, i.received_good_pieces,
                i.received_actual_date,
                i.factory_name, i.factory_code,
                b.message_no
            FROM operation_cut_items i
            JOIN operation_cut_batches b ON i.batch_id = b.id
            WHERE i.is_received = 1
        """
        params = []
        if factory_code:
            query += " AND i.factory_code = ?"
            params.append(factory_code)
        
        rows = connection.execute(query, params).fetchall()
        
        results = []
        for row in rows:
            item = dict(row)
            # حساب المتبقي (الفعلي - الهدف)
            # الهدف هو ما كان يجب استلامه نظرياً
            target_pieces = (item["original_qty"] or 0) * 12
            available_to_receive = target_pieces - (item["received_grade"] or 0) - (item["received_repairs"] or 0) - (item["received_remainders"] or 0) + (item["received_added"] or 0)
            
            # المتبقي حسب طلب المستخدم الجديد: Received - Available
            # إذا كان Received < Available يكون سالباً (عجز)
            remaining = (item["received_good"] or 0) - available_to_receive
            
            if remaining < 0:
                item["deficit_pieces"] = abs(remaining)
                results.append(item)
                
        return results
def get_message_detailed_report(message_no: str) -> dict[str, Any]:
    """يجلب تقريرًا شاملاً عن كافة حركات الأصناف المرتبطة برقم رسالة معين عبر كافة بيانات القص."""
    if not message_no:
        raise ValueError("رقم الرسالة مطلوب.")

    with get_connection() as connection:
        # 1. جلب كافة الأصناف التي تحمل هذا رقم الرسالة عبر الربط مع جدول البيانات الأساسية
        items = connection.execute(
            """
            SELECT i.*, p.name as product_name, p.size as product_size, b.message_no, b.cut_date as batch_cut_date
            FROM operation_cut_items i
            JOIN operation_cut_batches b ON b.id = i.batch_id
            LEFT JOIN operation_products p ON p.id = i.product_id
            WHERE b.message_no = ?
            ORDER BY b.cut_date DESC, i.id ASC
            """,
            (message_no,)
        ).fetchall()

        if not items:
            raise ValueError(f"لم يتم العثور على أي بيانات للرسالة رقم: {message_no}")

        items_list = [dict(it) for it in items]
        
        # محاولة جلب بيانات عامة للرسالة من أول صنف متاح
        # نستخدم بيانات أول صنف كبيانات عامة للرسالة (تاريخ القص، المصنع)
        first_item = items_list[0]
        batch_info = {
            "message_no": message_no,
            "cut_date": normalize_date_text(first_item.get("batch_cut_date")),
            "factory_name": first_item.get("factory_name", "-"),
            "batch_code": first_item.get("batch_code", "-"),
            "notes": first_item.get("description", "") # نستخدم الوصف كملحوظات إذا لم يوجد بيان
        }

        # 2. حساب إجماليات للتقرير
        total_planned = sum(float(it["quantity"] or 0) for it in items_list)
        total_received = sum(float(it["received_good"] or 0) for it in items_list)
        total_grade = sum(float(it["received_grade"] or 0) for it in items_list)
        total_repairs = sum(float(it["received_repairs"] or 0) for it in items_list)
        
        # حساب التكلفة: (الكمية / 12) * السعر (لأن السعر للدستة)
        total_cost = sum((float(it["received_good"] or 0) / 12.0) * float(it["manufacturing_price"] or 0) for it in items_list)

        summary = {
            "total_planned_qty": total_planned,
            "total_received_good": total_received,
            "total_grade": total_grade,
            "total_repairs": total_repairs,
            "total_added": sum(float(it["received_added"] or 0) for it in items_list),
            "total_remainders": sum(float(it["received_remainders"] or 0) for it in items_list),
            "total_cost": total_cost,
            "items_count": len(items_list),
            "accounted_count": sum(1 for it in items_list if it["is_accounted"]),
            "packed_count": sum(1 for it in items_list if it["is_packed"])
        }

        return {
            "batch": batch_info,
            "report_items": items_list,
            "summary": summary
        }


def process_packing_and_merge(item_ids: list[int], delivery_note_no: str) -> dict[str, Any]:
    """
    ينفذ منطق الدمج والترحيل للأصناف المختارة:
    1. دمج A و B لنفس الصنف.
    2. اعتماد الكمية الأقل كمنتج تام.
    3. ترحيل فائض B للأكواد البديلة بناءً على المقاس.
    """
    if not item_ids:
        return {"processed": 0, "messages": ["لا توجد أصناف مختارة."]}

    with get_connection() as connection:
        # 1. جلب البيانات الكاملة للأصناف المختارة
        placeholders = ",".join(["?"] * len(item_ids))
        rows = connection.execute(
            f"SELECT * FROM operation_cut_items WHERE id IN ({placeholders})", item_ids
        ).fetchall()
        items = [dict(row) for row in rows]

        # 2. تجميع الأصناف للبحث عن أزواج A/B
        # سنقوم بتجميعها بناءً على الكود (بدون حرف A/B) والمقاس
        groups: dict[str, list[dict]] = {}
        for item in items:
            code = item["code"].strip().upper()
            size = item["size"].strip().upper()
            # استخراج الكود الأساسي (مثلاً 51 من 51A)
            base_code = code
            if code.endswith("A") or code.endswith("B"):
                base_code = code[:-1]
            
            group_key = f"{base_code}|{size}"
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(item)

        results = []
        processed_ids = []

        for group_key, group_items in groups.items():
            base_code, size = group_key.split("|")
            
            item_a = next((it for it in group_items if it["code"].upper().endswith("A")), None)
            item_b = next((it for it in group_items if it["code"].upper().endswith("B")), None)
            
            if item_a and item_b:
                # منطق الدمج (A + B)
                qty_a = item_a["received_good"] or 0
                qty_b = item_b["received_good"] or 0
                
                final_qty = min(qty_a, qty_b)
                surplus_b = max(0, qty_b - qty_a)
                
                # حساب الوحدات للمنتج التام
                # إذا كان كلاهما مدخل بالدستة، تظل النتيجة بالدستة
                # وإلا يتم تحويلها لقطع لضمان الدقة
                final_dozens = 0
                final_pieces = 0
                
                # نتحقق إذا كان كلاهما دستة صافية
                a_is_doz = (item_a.get("received_good_dozens") or 0) > 0 and (item_a.get("received_good_pieces") or 0) == 0
                b_is_doz = (item_b.get("received_good_dozens") or 0) > 0 and (item_b.get("received_good_pieces") or 0) == 0
                
                if a_is_doz and b_is_doz:
                    final_dozens = final_qty / 12
                else:
                    final_pieces = final_qty

                # إضافة المنتج التام (الكود بدون حرف)
                results.append({
                    "code": base_code,
                    "name": item_a["name"].replace("A", "").replace("B", "").strip(),
                    "size": size,
                    "qty": final_qty,
                    "dozens": final_dozens,
                    "pieces": final_pieces
                })
                
                # ترحيل فائض B إن وجد
                if surplus_b > 0:
                    migrated_code = _get_migrated_code(base_code, size)
                    if migrated_code:
                        results.append({
                            "code": migrated_code,
                            "name": f"ترحيل فائض {base_code}B",
                            "size": size,
                            "qty": surplus_b,
                            "dozens": 0,
                            "pieces": surplus_b
                        })
                    else:
                        results.append({
                            "code": f"{base_code}B",
                            "name": f"فائض {item_b['name']}",
                            "size": size,
                            "qty": surplus_b,
                            "dozens": 0,
                            "pieces": surplus_b
                        })
                
                processed_ids.extend([item_a["id"], item_b["id"]])

            else:
                # أصناف منفردة (ليست زوج A/B أو أحد الطرفين مفقود في الاختيار)
                for it in group_items:
                    results.append({
                        "code": it["code"],
                        "name": it["name"],
                        "size": it["size"],
                        "qty": it["received_good"] or 0,
                        "dozens": it.get("received_good_dozens") or 0,
                        "pieces": it.get("received_good_pieces") or 0
                    })
                    processed_ids.append(it["id"])

        # 3. تحديث المخزن التام
        for res in results:
            if res["qty"] <= 0: continue
            
            # محاولة التحديث أو الإدخال (Upsert)
            connection.execute("""
                INSERT INTO operation_finished_stock (product_code, product_name, product_size, quantity, dozens_qty, pieces_qty)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(product_code, product_size) 
                DO UPDATE SET 
                    quantity = quantity + excluded.quantity,
                    dozens_qty = dozens_qty + excluded.dozens_qty,
                    pieces_qty = pieces_qty + excluded.pieces_qty,
                    updated_at = CURRENT_TIMESTAMP
            """, (res["code"], res["name"], res["size"], res["qty"], res.get("dozens", 0), res.get("pieces", 0)))

        # 4. تمييز الأصناف كمغلفة/تامة وربطها برقم إذن التسليم
        if processed_ids:
            p_placeholders = ",".join(["?"] * len(processed_ids))
            connection.execute(
                f"UPDATE operation_cut_items SET is_packed = 1, delivery_note_no = ? WHERE id IN ({p_placeholders})",
                [delivery_note_no] + processed_ids
            )
        connection.commit()
        return {"processed": len(processed_ids), "entries": len(results)}

def reverse_packing_by_note(delivery_note_no: str) -> dict[str, Any]:
    """التراجع عن عملية تعبئة بالكامل بناءً على رقم إذن التسليم."""
    if not delivery_note_no:
        raise ValueError("رقم إذن التسليم مطلوب.")

    with get_connection() as connection:
        # 1. جلب القصات المرتبطة بهذا الإذن
        rows = connection.execute(
            "SELECT * FROM operation_cut_items WHERE delivery_note_no = ?", (delivery_note_no,)
        ).fetchall()
        items = [dict(row) for row in rows]
        
        if not items:
            raise ValueError(f"لم يتم العثور على أي قصات مرتبطة بإذن التسليم رقم: {delivery_note_no}")

        # 2. إعادة حساب التأثير الذي حدث على المخزن (نفس منطق التعبئة ولكن بالعكس)
        groups: dict[str, list[dict]] = {}
        for item in items:
            code = item["code"].strip().upper()
            size = item["size"].strip().upper()
            base_code = code[:-1] if (code.endswith("A") or code.endswith("B")) else code
            group_key = f"{base_code}|{size}"
            groups.setdefault(group_key, []).append(item)

        to_subtract = []
        for group_key, group_items in groups.items():
            base_code, size = group_key.split("|")
            item_a = next((it for it in group_items if it["code"].upper().endswith("A")), None)
            item_b = next((it for it in group_items if it["code"].upper().endswith("B")), None)
            
            if item_a and item_b:
                qty_a = item_a["received_good"] or 0
                qty_b = item_b["received_good"] or 0
                final_qty = min(qty_a, qty_b)
                surplus_b = max(0, qty_b - qty_a)
                
                # خصم المنتج التام
                to_subtract.append({"code": base_code, "size": size, "qty": final_qty})
                
                # خصم الفائض المرحل
                if surplus_b > 0:
                    migrated = _get_migrated_code(base_code, size)
                    if migrated:
                        to_subtract.append({"code": migrated, "size": size, "qty": surplus_b})
                    else:
                        to_subtract.append({"code": f"{base_code}B", "size": size, "qty": surplus_b})
            else:
                for it in group_items:
                    to_subtract.append({"code": it["code"], "size": it["size"], "qty": it["received_good"] or 0})

        # 3. تنفيذ الخصم من المخزن
        for sub in to_subtract:
            connection.execute("""
                UPDATE operation_finished_stock 
                SET quantity = MAX(0, quantity - ?),
                    dozens_qty = MAX(0, dozens_qty - ?),
                    pieces_qty = MAX(0, pieces_qty - ?),
                    updated_at = CURRENT_TIMESTAMP
                WHERE product_code = ? AND product_size = ?
            """, (sub["qty"], sub["qty"]/12, sub["qty"] % 12, sub["code"], sub["size"]))

        # 4. إعادة القصات لوضع "بانتظار التعبئة"
        connection.execute(
            "UPDATE operation_cut_items SET is_packed = 0, delivery_note_no = NULL WHERE delivery_note_no = ?",
            (delivery_note_no,)
        )
        connection.commit()
        return {"reversed_items": len(items), "delivery_note": delivery_note_no}

def _get_migrated_code(base_code: str, size: str) -> str | None:
    """تطبيق قواعد الترحيل المعتمدة في الخطة."""
    base = base_code.strip().upper()
    sz = size.strip().upper()
    
    # المجموعة الأولى: من 34 حتى 39
    group1 = [str(i) for i in range(34, 40)]
    if base in group1:
        mapping = {"S": "27", "M": "28", "L": "29", "XL": "30", "2XL": "31", "3XL": "32"}
        return mapping.get(sz)
    
    # المجموعة الثانية: من 1 حتى 5
    group2 = [str(i) for i in range(1, 6)]
    if base in group2:
        mapping = {"S": "13", "M": "14", "L": "15", "XL": "16", "2XL": "17"}
        return mapping.get(sz)
        
    return None


def update_item_receipt(
    item_id: int,
    grade: float = 0,
    repairs: float = 0,
    added: float = 0,
    remainders: float = 0,
    good_pieces: float = 0,
    good_dozens_entry: float = 0,
    good_pieces_entry: float = 0,
    received_actual_date: str = "",
    packing_department: str = "",
) -> dict[str, Any]:
    """يحدّث بيانات الاستلام ويغيّر حالة القصة إلى 'تم الاستلام'."""
    try:
        normalized_id = int(item_id)
    except (TypeError, ValueError) as exc:
        raise ValueError("رقم السطر غير صحيح.") from exc

    normalized_date = normalize_date_text(received_actual_date) if received_actual_date else ""

    with get_connection() as connection:
        row = connection.execute(
            "SELECT id, status FROM operation_cut_items WHERE id = ?",
            (normalized_id,),
        ).fetchone()
        if not row:
            raise ValueError("القصة المطلوبة غير موجودة.")

        connection.execute(
            """
            UPDATE operation_cut_items
            SET
                is_received      = 1,
                status           = 'تم الاستلام',
                received_grade     = ?,
                received_repairs   = ?,
                received_added     = ?,
                received_remainders = ?,
                received_good      = ?,
                received_good_dozens = ?,
                received_good_pieces = ?,
                received_actual_date = ?,
                packing_department   = ?
            WHERE id = ?
            """,
            (grade, repairs, added, remainders, good_pieces, good_dozens_entry, good_pieces_entry, normalized_date, packing_department, normalized_id),
        )
        connection.commit()

    return {
        "id": normalized_id,
        "is_received": 1,
        "received_grade": grade,
        "received_repairs": repairs,
        "received_added": added,
        "received_remainders": remainders,
        "received_actual_date": normalized_date,
    }


def undo_item_receipt(item_id: int) -> bool:
    """إلغاء استلام القصة وإعادتها لحالة 'بانتظار الاستلام'."""
    try:
        normalized_id = int(item_id)
    except (TypeError, ValueError):
        return False

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE operation_cut_items
            SET
                is_received      = 0,
                status           = 'بانتظار الاستلام',
                received_grade     = 0,
                received_repairs   = 0,
                received_added     = 0,
                received_remainders = 0,
                received_good      = 0,
                received_good_dozens = 0,
                received_good_pieces = 0,
                received_actual_date = NULL,
                packing_department   = NULL
            WHERE id = ? AND COALESCE(is_packed, 0) = 0
            """,
            (normalized_id,),
        )
        connection.commit()
        return cursor.rowcount > 0


def delete_factory(code: str) -> dict[str, Any]:
    normalized_code = clean_text(code).upper()
    if not normalized_code:
        raise ValueError("كود المصنع مطلوب.")

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT code
            FROM operation_factories
            WHERE UPPER(code) = ?
            """,
            (normalized_code,),
        ).fetchone()
        if not row:
            raise ValueError("المصنع المطلوب غير موجود.")

        connection.execute(
            """
            DELETE FROM operation_factories
            WHERE UPPER(code) = ?
            """,
            (normalized_code,),
        )
        connection.commit()

    return {"code": normalized_code}


def _ensure_factories_columns(connection: sqlite3.Connection) -> None:
    info = connection.execute("PRAGMA table_info(operation_factories)").fetchall()
    existing = {col["name"] for col in info} if info and isinstance(info[0], sqlite3.Row) else {c[1] for c in info}

    def add_column(name: str, ddl: str) -> None:
        if name not in existing:
            connection.execute(f"ALTER TABLE operation_factories ADD COLUMN {name} {ddl}")

    add_column("phone", "TEXT")
    add_column("opening_balance", "REAL NOT NULL DEFAULT 0")


def get_packing_production_report(
    from_month: int = None, 
    to_month: int = None, 
    year: int = None,
    department: str = None,
    product_code: str = None,
    factory_name: str = None
) -> list[dict[str, Any]]:
    """يستخرج تقرير إنتاج أقسام التعبئة بناءً على فلاتر متعددة ونطاق شهور."""
    if not year: 
        year = datetime.now().year
        
    query = """
        SELECT 
            i.received_actual_date as date,
            i.name as product_name,
            i.code as product_code,
            i.size as product_size,
            i.received_good_dozens as dozens,
            i.received_good_pieces as pieces,
            i.packing_department as department,
            b.message_no,
            i.factory_name
        FROM operation_cut_items i
        JOIN operation_cut_batches b ON b.id = i.batch_id
        WHERE i.is_received = 1 
          AND i.packing_department IS NOT NULL
          AND i.received_actual_date IS NOT NULL
    """
    params = []
    
    # Filter by Year (using string matching on the end of the date DD/MM/YYYY)
    query += " AND substr(i.received_actual_date, 7, 4) = ?"
    params.append(str(year))
    
    # Filter by Month Range
    if from_month and to_month:
        query += " AND CAST(substr(i.received_actual_date, 4, 2) AS INTEGER) BETWEEN ? AND ?"
        params.append(int(from_month))
        params.append(int(to_month))
        
    # Optional Filters
    if department and department != 'الكل':
        query += " AND i.packing_department = ?"
        params.append(department)
        
    if product_code and product_code != 'الكل':
        query += " AND i.code = ?"
        params.append(product_code)
        
    if factory_name and factory_name != 'الكل':
        query += " AND i.factory_name = ?"
        params.append(factory_name)
        
    query += " ORDER BY substr(i.received_actual_date, 7, 4) DESC, substr(i.received_actual_date, 4, 2) DESC, substr(i.received_actual_date, 1, 2) DESC, i.packing_department ASC"
    
    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

def get_cutting_production_report(month: int = None, year: int = None) -> list[dict[str, Any]]:
    """يستخرج تقرير إنتاج قسم القص والفرش لشهر وسنة معينة."""
    if not month: month = datetime.now().month
    if not year: year = datetime.now().year
    
    # البحث في تاريخ القص بصيغة dd/mm/yyyy
    search_pattern = f'%/{month:02d}/{year}%'
    
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT 
                b.cut_date,
                b.message_no,
                i.code,
                i.description,
                i.name,
                i.size,
                i.quantity
            FROM operation_cut_items i
            JOIN operation_cut_batches b ON b.id = i.batch_id
            WHERE b.cut_date LIKE ?
            ORDER BY b.cut_date ASC, b.message_no ASC, i.code ASC
        """, (search_pattern,)).fetchall()
        
        data = [dict(row) for row in rows]
        # تطبيع التواريخ للعرض
        from operation_storage import normalize_date_text
        for item in data:
            item['cut_date'] = normalize_date_text(item.get('cut_date'))
            
        return data


def get_product_packing_history(product_code: str, product_size: str) -> list[dict[str, Any]]:
    """جلب تاريخ التعبئة لصنف معين (تفاصيل الوارد للمخزن)."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT i.delivery_note_no, i.packing_department, i.factory_name, 
                   b.message_no, i.received_good, i.received_actual_date,
                   i.received_good_dozens, i.received_good_pieces
            FROM operation_cut_items i
            JOIN operation_cut_batches b ON b.id = i.batch_id
            WHERE i.is_packed = 1 
              AND (UPPER(i.code) = UPPER(?) OR 
                   UPPER(i.code) = UPPER(?) || 'A' OR 
                   UPPER(i.code) = UPPER(?) || 'B')
              AND UPPER(i.size) = UPPER(?)
            ORDER BY i.received_actual_date DESC, i.id DESC
            """,
            (product_code, product_code, product_code, product_size)
        ).fetchall()
        
        return [dict(row) for row in rows]


def delete_cut_item(item_id: int) -> bool:
    """حذف صنف (قصة) محدد من قاعدة البيانات وتحديث إجماليات البيان المرتبط به."""
    try:
        normalized_id = int(item_id)
    except (TypeError, ValueError):
        return False

    with get_connection() as connection:
        # جلب id البيان قبل الحذف لتحديث إجمالياته لاحقاً
        row = connection.execute(
            "SELECT batch_id FROM operation_cut_items WHERE id = ?", (normalized_id,)
        ).fetchone()
        
        if not row:
            return False
            
        batch_id = row["batch_id"]

        # الحذف الفعلي
        cursor = connection.execute(
            "DELETE FROM operation_cut_items WHERE id = ?", (normalized_id,)
        )
        
        if cursor.rowcount > 0:
            # تحديث الإجماليات والحالة للبيان المرتبط
            _refresh_batch_totals(connection, batch_id)
            _refresh_batch_status(connection, batch_id)
            connection.commit()
            return True
            
        return False




