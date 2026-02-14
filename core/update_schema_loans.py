
from sqlalchemy import create_engine, text
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hr.db')
print(f"Connecting to database at: {DB_PATH}")

engine = create_engine(f'sqlite:///{DB_PATH}')

def migrate():
    with engine.connect() as conn:
        try:
            # Check if column exists
            result = conn.execute(text("PRAGMA table_info(loans)"))
            columns = [row[1] for row in result.fetchall()]
            
            if 'date' not in columns:
                print("Adding 'date' column to 'loans' table...")
                conn.execute(text("ALTER TABLE loans ADD COLUMN date DATE"))
                
                # Update existing records to have today's date (or a default) logic handles default
                # But SQL adding column with nulls might need update if we want non-null. 
                # Model says nullable=True implied by default? No, it's Column(Date, default=...)
                # Sqlite adds it as NULL usually unless specified.
                # Let's update all null dates to today for consistency if needed, 
                # strictly speaking, we accept NULLs or update them.
                
                from datetime import date
                today = date.today()
                conn.execute(text(f"UPDATE loans SET date = '{today}' WHERE date IS NULL"))
                
                print("Migration successful: 'date' column added.")
                conn.commit()
            else:
                print("Column 'date' already exists in 'loans' table.")

            if 'excluded_months' not in columns:
                print("Adding 'excluded_months' column to 'loans' table...")
                conn.execute(text("ALTER TABLE loans ADD COLUMN excluded_months VARCHAR"))
                print("Migration successful: 'excluded_months' column added.")
                conn.commit()
            else:
                print("Column 'excluded_months' already exists in 'loans' table.")
                
        except Exception as e:
            print(f"Error during migration: {e}")
            conn.rollback()

if __name__ == "__main__":
    migrate()
