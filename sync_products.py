import sys
import sqlite3
import os
sys.path.insert(0, r'e:\backoup\25-2-2026')
from core.db_manager import DBManager
from sqlalchemy import text
from core.commercial_models import Product

db = DBManager()
op_db_path = r'e:\backoup\25-2-2026\حركة التشغيل\data\operation.db'

print("Syncing products from Operation DB to Commercial DB...")

if not os.path.exists(op_db_path):
    print("Operation DB not found.")
    sys.exit(1)

op_conn = sqlite3.connect(op_db_path)
op_cursor = op_conn.cursor()

# Get all products from operation
op_cursor.execute("SELECT code, name, size FROM operation_products")
op_products = op_cursor.fetchall()

# Get finished stock from operation to update stock quantities
op_cursor.execute("SELECT product_code, quantity FROM operation_finished_stock")
op_stock = {row[0]: row[1] for row in op_cursor.fetchall()}

with db.get_session() as session:
    for code, name, size in op_products:
        # Check if product exists in commercial DB
        product = session.query(Product).filter_by(code=code).first()
        full_name = f"{name} - {size}" if size else name
        stock = op_stock.get(code, 0.0)
        
        if product:
            # Update existing
            product.name = full_name
            product.current_stock = stock
        else:
            # Create new
            new_product = Product(
                code=code,
                name=full_name,
                category='منتج تام',
                unit='Piece',
                current_stock=stock,
                is_active=True
            )
            session.add(new_product)
            
    session.commit()
    print(f"Synced {len(op_products)} products.")

op_conn.close()
print("Sync complete.")
