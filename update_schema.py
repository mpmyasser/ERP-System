import sqlite3
import os
from sqlalchemy import create_engine, text

DB_PATH = "hr_system.db"
# Use absolute path for reliability
ABS_DB_PATH = f"sqlite:///{os.path.abspath(DB_PATH)}"

def add_column_if_not_exists(cursor, table, column, type_def):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type_def}")
        print(f"Added column {column} to {table}")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"Column {column} already exists in {table}")
        else:
            print(f"Error adding {column}: {e}")

def migrate():
    if not os.path.exists(DB_PATH):
        print("Database not found, skipping migration (will be created by DBManager).")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Personal
    add_column_if_not_exists(cursor, "employees", "hire_date", "DATE")
    add_column_if_not_exists(cursor, "employees", "address", "VARCHAR")
    add_column_if_not_exists(cursor, "employees", "city", "VARCHAR")
    add_column_if_not_exists(cursor, "employees", "governorate", "VARCHAR")
    add_column_if_not_exists(cursor, "employees", "marital_status", "VARCHAR")
    add_column_if_not_exists(cursor, "employees", "mobile_number", "VARCHAR")
    add_column_if_not_exists(cursor, "employees", "date_of_birth", "DATE")
    add_column_if_not_exists(cursor, "employees", "national_id", "VARCHAR")
    add_column_if_not_exists(cursor, "employees", "num_children", "INTEGER DEFAULT 0")
    add_column_if_not_exists(cursor, "employees", "age_youngest_child", "INTEGER DEFAULT 0")
    add_column_if_not_exists(cursor, "employees", "military_status", "VARCHAR")
    add_column_if_not_exists(cursor, "employees", "has_relatives", "BOOLEAN DEFAULT 0")
    add_column_if_not_exists(cursor, "employees", "relationship_degree", "VARCHAR")
    add_column_if_not_exists(cursor, "employees", "weekly_holiday", "VARCHAR")
    
    # Work Status
    add_column_if_not_exists(cursor, "employees", "is_active", "BOOLEAN DEFAULT 1")
    add_column_if_not_exists(cursor, "employees", "exit_date", "DATE")
    add_column_if_not_exists(cursor, "employees", "resignation_reason", "TEXT")
    add_column_if_not_exists(cursor, "employees", "disruption_date", "DATE")
    add_column_if_not_exists(cursor, "employees", "entitlement_date", "DATE")
    
    # Financial
    add_column_if_not_exists(cursor, "employees", "incentive_allowance", "FLOAT DEFAULT 0")
    add_column_if_not_exists(cursor, "employees", "regularity_incentive", "FLOAT DEFAULT 0")
    add_column_if_not_exists(cursor, "employees", "transport_allowance", "FLOAT DEFAULT 0")
    add_column_if_not_exists(cursor, "employees", "insurance_salary", "FLOAT DEFAULT 0")
    add_column_if_not_exists(cursor, "employees", "salary_type", "VARCHAR")
    
    add_column_if_not_exists(cursor, "employees", "erp_account_code", "VARCHAR")
    
    # Documents
    add_column_if_not_exists(cursor, "employees", "documents_received", "TEXT")
    
    # Education
    add_column_if_not_exists(cursor, "employees", "college", "VARCHAR")
    add_column_if_not_exists(cursor, "employees", "major", "VARCHAR")
    add_column_if_not_exists(cursor, "employees", "graduation_year", "INTEGER")
    add_column_if_not_exists(cursor, "employees", "grade", "VARCHAR")
    add_column_if_not_exists(cursor, "employees", "qualification", "VARCHAR")

    conn.commit()
    conn.close()
    print("Migration completed.")

if __name__ == "__main__":
    migrate()
