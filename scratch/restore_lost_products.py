import os
import sys
import sqlite3

op_db_path = r'e:\backoup\25-2-2026\حركة التشغيل\data\operation.db'

if not os.path.exists(op_db_path):
    print("Operation DB not found.")
    sys.exit(1)

products_to_add = [
    ("66", "عباية بناتي", "1"),
    ("67", "عباية بناتي صيفي", "S"),
    ("68", "عباية بناتي صيفي", "M"),
    ("69", "عباية بناتي صيفي", "L"),
    ("70", "عباية بناتي صيفي", "XL"),
    ("71", "عباية بناتي صيفي", "2XL"),
    ("72", "عباية بناتي صيفي", "3XL")
]

conn = sqlite3.connect(op_db_path)
cursor = conn.cursor()

inserted_count = 0
for code, name, size in products_to_add:
    # التحقق مما إذا كان الصنف موجوداً مسبقاً
    cursor.execute("SELECT COUNT(*) FROM operation_products WHERE code = ?", (code,))
    exists = cursor.fetchone()[0] > 0
    if not exists:
        cursor.execute(
            "INSERT INTO operation_products (code, name, size) VALUES (?, ?, ?)",
            (code, name, size)
        )
        print(f"Inserted: Code {code} - {name} - Size {size}")
        inserted_count += 1
    else:
        print(f"Code {code} already exists.")

conn.commit()
conn.close()

print(f"Finished restoring lost products. Added {inserted_count} products.")
