import pandas as pd
import sys
import os
from datetime import datetime, date
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# Add core to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_manager import DBManager
from database_models import Employee, WeeklyHoliday, Department
from utils.helpers import parse_date_compact

def clean_value(val):
    """Clean Excel value, return None if empty/nan/null"""
    if pd.isna(val):
        return None
    val_str = str(val).strip()
    if not val_str or val_str.lower() == 'nan' or val_str.lower() == 'nat':
        return None
    return val_str

def parse_excel_date(val):
    """Parse date from Excel (Timestamp, string, etc)"""
    if pd.isna(val):
        return None
    
    # If already datetime/timestamp
    if isinstance(val, (datetime, pd.Timestamp)):
        return val.date()
    
    val_str = str(val).strip()
    if not val_str:
        return None
        
    # Try custom helper first
    parsed = parse_date_compact(val_str)
    if parsed:
        return parsed
        
    # Fallback to pandas
    try:
        return pd.to_datetime(val_str).date()
    except:
        return None

def import_employees(file_path):
    print(f"Reading file: {file_path}")
    
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    # Normalize columns: lower, strip
    df.columns = [str(c).lower().strip() for c in df.columns]
    
    # Check required key column
    if 'code' not in df.columns:
        print("Error: Missing required column 'code'")
        return

    db = DBManager()
    session = db.get_session()
    
    stats = {'updated': 0, 'inserted': 0, 'skipped': 0, 'errors': 0}
    
    # Pre-fetch departments for lookup
    dept_map = {d.name.strip(): d.id for d in session.query(Department).all()}
    print(f"Loaded {len(dept_map)} departments for lookup.")

    def get_dept_id(val):
        """Resolve department name to ID"""
        name = clean_value(val)
        if not name: return None
        return dept_map.get(name.strip())

    def parse_bool(val):
        """Parse boolean from various formats"""
        s = clean_value(val)
        if not s: return False
        return s.lower() in ['1', 'yes', 'true', 'on', 'نعم', 'صحيح']

    def parse_int(val):
        """Parse int safely"""
        try:
            v = clean_value(val)
            return int(float(v)) if v else 0
        except:
            return 0

    print("Starting import...")
    
    for index, row in df.iterrows():
        try:
            code = clean_value(row.get('code'))
            if not code:
                # Skip rows without code
                continue
                
            # Upsert Logic: Check if exists
            employee = session.query(Employee).filter_by(code=code).first()
            
            # --- Field Mapping & Extraction ---
            # Define mapping: (DB Field Name, Excel Column Name, TypeHelper)
            fields_map = [
                ('name', 'name', clean_value),
                ('national_id', 'national_id', clean_value),
                ('insurance_number', 'insurance_number', clean_value),
                ('mobile_number', 'mobile_number', clean_value),
                ('department_id', 'department', get_dept_id), # Map 'department' name to 'department_id'
                ('job_title', 'job_title', clean_value),
                ('basic_salary', 'basic_salary', float),
                ('hire_date', 'hire_date', parse_excel_date),
                ('address', 'address', clean_value),
                ('city', 'city', clean_value),
                ('governorate', 'governorate', clean_value),
                ('marital_status', 'marital_status', clean_value),
                ('military_status', 'military_status', clean_value),
                ('num_children', 'num_children', parse_int),
                ('overtime_allowed', 'overtime_allowed', parse_bool),
                ('standard_start_time', 'standard_start_time', lambda x: pd.to_datetime(str(x)).time() if clean_value(x) else None),
                ('standard_end_time', 'standard_end_time', lambda x: pd.to_datetime(str(x)).time() if clean_value(x) else None),
                ('regularity_incentive', 'regularity_incentive', float),
                 # Add other fields as needed
            ]
            
            # Extract values dict
            values = {}
            for db_field, excel_col, helper in fields_map:
                if excel_col in df.columns:
                    raw_val = row.get(excel_col)
                    cleaned = None
                    try:
                        if helper == float:
                            # Safe float conversion
                             v = clean_value(raw_val)
                             if v: cleaned = float(v)
                        elif helper:
                            cleaned = helper(raw_val)
                        else:
                            cleaned = raw_val
                    except:
                        cleaned = None
                    
                    values[db_field] = cleaned

            if employee:
                # === UPDATE ===
                # Update fields only if new value is NOT None
                updated_fields = []
                for field, val in values.items():
                    if val is not None:
                        # Check if changed (optional optimization)
                        current_val = getattr(employee, field)
                        if current_val != val:
                            setattr(employee, field, val)
                            updated_fields.append(field)
                
                if updated_fields:
                    stats['updated'] += 1
                    # print(f"Updated {code}: {updated_fields}")
                else:
                    stats['skipped'] += 1
            
            else:
                # === INSERT ===
                # Validate Required
                req_missing = []
                if not values.get('name'): req_missing.append('name')
                if not values.get('national_id'): req_missing.append('national_id')
                
                if req_missing:
                    print(f"Skipping new employee {code}: Missing required fields {req_missing}")
                    stats['errors'] += 1
                    continue
                
                # Set defaults for missing fields
                new_emp_data = {
                    'code': code,
                    'category': clean_value(row.get('category')) or 'EMPLOYEE',
                    'weekly_holiday': WeeklyHoliday.FRIDAY.value,
                    'is_active': True,
                    'num_children': 0,
                    'is_insured': True if values.get('insurance_number') else False,
                    'mobile_number': values.get('mobile_number') or '0000000000' # Default if missing
                }
                
                # Merge extracted values (they override defaults if present)
                # Note: values contains None for missing excel columns, we should filter those out 
                # to let DB defaults work? Or set explicit None?
                # SQLAlchemy defaults work if we don't pass argument.
                # So only pass if not None.
                for k, v in values.items():
                    if v is not None:
                        new_emp_data[k] = v
                
                new_emp = Employee(**new_emp_data)
                session.add(new_emp)
                stats['inserted'] += 1
                # print(f"Inserted {code}")

        except Exception as e:
            print(f"Error processing row {index+2} (Code: {code}): {e}")
            stats['errors'] += 1

    try:
        session.commit()
        print("\nImport Completed Successfully!")
        print(f"Stats: {stats}")
    except Exception as e:
        session.rollback()
        print(f"Critical Error during commit: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    import_employees(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Bulk Import.xlsx'))
