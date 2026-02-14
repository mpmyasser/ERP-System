import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'hr.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if days column already exists
    cursor.execute("PRAGMA table_info(penalties_and_bonuses)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'days' not in columns:
        print("Adding 'days' column to 'penalties_and_bonuses' table...")
        cursor.execute("ALTER TABLE penalties_and_bonuses ADD COLUMN days FLOAT")
        conn.commit()
        print("Done.")
    else:
        print("'days' column already exists.")

except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
