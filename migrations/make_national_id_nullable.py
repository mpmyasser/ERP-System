"""
Migration Script: Make national_id nullable
This script updates the employees table to allow NULL values in the national_id column.
"""

import sqlite3
import os
import sys

# Add core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

def migrate_national_id():
    """Make national_id column nullable in employees table"""
    
    db_path = os.path.join(os.path.dirname(__file__), '..', 'core', 'hr.db')
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return False
    
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # SQLite doesn't support ALTER COLUMN directly
        # We need to recreate the table
        
        print("Step 1: Creating backup of employees table...")
        cursor.execute("""
            CREATE TABLE employees_backup AS 
            SELECT * FROM employees
        """)
        
        print("Step 2: Dropping original employees table...")
        cursor.execute("DROP TABLE employees")
        
        print("Step 3: Creating new employees table with nullable national_id...")
        cursor.execute("""
            CREATE TABLE employees (
                id INTEGER PRIMARY KEY,
                code VARCHAR UNIQUE NOT NULL,
                name VARCHAR NOT NULL,
                job_title VARCHAR,
                department_id INTEGER,
                category VARCHAR NOT NULL,
                basic_salary FLOAT DEFAULT 0.0,
                daily_work_hours FLOAT DEFAULT 8.0,
                standard_start_time TIME,
                standard_end_time TIME,
                is_insured BOOLEAN DEFAULT 0,
                insurance_value_employee FLOAT DEFAULT 0.0,
                insurance_value_company FLOAT DEFAULT 0.0,
                insurance_number VARCHAR,
                overtime_allowed BOOLEAN DEFAULT 0,
                has_attendance_bonus BOOLEAN DEFAULT 0,
                erp_account_code VARCHAR,
                hire_date DATE,
                address VARCHAR,
                city VARCHAR,
                governorate VARCHAR,
                marital_status VARCHAR,
                mobile_number VARCHAR,
                date_of_birth DATE,
                national_id VARCHAR UNIQUE,
                num_children INTEGER DEFAULT 0,
                age_youngest_child INTEGER DEFAULT 0,
                military_status VARCHAR,
                has_relatives BOOLEAN DEFAULT 0,
                relationship_degree VARCHAR,
                weekly_holiday VARCHAR DEFAULT 'الجمعة',
                is_active BOOLEAN DEFAULT 1,
                exit_date DATE,
                resignation_reason VARCHAR,
                disruption_date DATE,
                entitlement_date DATE,
                incentive_allowance FLOAT DEFAULT 0.0,
                regularity_incentive FLOAT DEFAULT 0.0,
                transport_allowance FLOAT DEFAULT 0.0,
                insurance_salary FLOAT DEFAULT 0.0,
                salary_type VARCHAR DEFAULT 'ثابت',
                documents_received VARCHAR,
                college VARCHAR,
                major VARCHAR,
                graduation_year INTEGER,
                grade VARCHAR,
                qualification VARCHAR,
                FOREIGN KEY (department_id) REFERENCES departments(id)
            )
        """)
        
        print("Step 4: Restoring data from backup (converting empty strings to NULL)...")
        cursor.execute("""
            INSERT INTO employees 
            SELECT 
                id, code, name, job_title, department_id, category, basic_salary,
                daily_work_hours, standard_start_time, standard_end_time, is_insured,
                insurance_value_employee, insurance_value_company, insurance_number,
                overtime_allowed, has_attendance_bonus, erp_account_code, hire_date,
                address, city, governorate, marital_status,
                NULLIF(mobile_number, ''),
                date_of_birth,
                NULLIF(national_id, ''),
                num_children, age_youngest_child, military_status, has_relatives,
                relationship_degree, weekly_holiday, is_active, exit_date,
                resignation_reason, disruption_date, entitlement_date,
                incentive_allowance, regularity_incentive, transport_allowance,
                insurance_salary, salary_type, documents_received, college, major,
                graduation_year, grade, qualification
            FROM employees_backup
        """)
        
        print("Step 5: Dropping backup table...")
        cursor.execute("DROP TABLE employees_backup")
        
        conn.commit()
        print("[SUCCESS] Migration completed successfully!")
        print("   - national_id is now nullable")
        print("   - mobile_number is now nullable")
        print("   - All existing data has been preserved")
        return True
        
    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        conn.rollback()
        
        # Try to restore from backup if it exists
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='employees_backup'")
            if cursor.fetchone():
                print("Attempting to restore from backup...")
                cursor.execute("DROP TABLE IF EXISTS employees")
                cursor.execute("ALTER TABLE employees_backup RENAME TO employees")
                conn.commit()
                print("Backup restored successfully")
        except:
            pass
        
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Migration: Make national_id nullable")
    print("=" * 60)
    success = migrate_national_id()
    sys.exit(0 if success else 1)
