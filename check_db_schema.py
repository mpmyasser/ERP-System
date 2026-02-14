import sqlite3

conn = sqlite3.connect('core/hr.db')
cursor = conn.cursor()

# Check cash_accounts table structure
cursor.execute("PRAGMA table_info(cash_accounts)")
columns = cursor.fetchall()

print("=== cash_accounts جدول الأعمدة ===")
for col in columns:
    print(f"  - {col[1]} ({col[2]})")

conn.close()
