import sqlite3
import os

db_path = r'e:\backoup\25-2-2026\حركة التشغيل\operation_database.db'
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(operation_cut_items)")
rows = cursor.fetchall()
for row in rows:
    print(f"{row['name']} ({row['type']})")
conn.close()
