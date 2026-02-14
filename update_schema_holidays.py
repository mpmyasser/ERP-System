import sqlite3
import os

db_path = os.path.join('core', 'hr.db')

def update_db():
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Check if column exists
        c.execute("PRAGMA table_info(employees)")
        columns = [col[1] for col in c.fetchall()]
        
        if 'entitled_to_official_holidays' not in columns:
            print("Adding 'entitled_to_official_holidays' column...")
            c.execute("ALTER TABLE employees ADD COLUMN entitled_to_official_holidays BOOLEAN DEFAULT 1")
            conn.commit()
            print("Column added successfully.")
        else:
            print("Column already exists.")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    update_db()
