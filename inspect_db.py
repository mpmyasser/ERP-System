import sqlite3
import os

db_path = r'e:\backoup\25-2-2026\حركة التشغيل\data\operation.db'
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print('Tables in operation.db:')
    for table in tables:
        print('-', table[0])
        cursor.execute(f"PRAGMA table_info({table[0]})")
        cols = cursor.fetchall()
        print('  Columns:', [c[1] for c in cols])
