import sys
import os
sys.path.insert(0, r'e:\backoup\25-2-2026')
from core.db_manager import DBManager
from sqlalchemy import text

db = DBManager()
with db.engine.connect() as conn:
    print("Clearing commercial tables...")
    conn.execute(text("DELETE FROM invoice_items"))
    conn.execute(text("DELETE FROM invoices"))
    conn.execute(text("DELETE FROM inventory_transactions"))
    conn.execute(text("DELETE FROM products"))
    conn.execute(text("DELETE FROM partners"))
    conn.commit()
    print("Commercial tables cleared successfully.")
