import pandas as pd
import sys
import os
from datetime import datetime
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# Add core to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_manager import DBManager
# Assuming AttendanceLog and other models are in database_models
# We need to check if AttendanceLog is importable. 
# Based on attendance.py usage: db.add_attendance_log uses logic inside DBManager or creates objects directly.
# attendance.py imports AttendanceLog in the verification step: query(AttendanceLog)
# Let's import basic models.
from database_models import AttendanceLog
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
    if not val_str or val_str.lower() == 'nan':
        return None
        
    # Try custom helper first
    parsed = parse_date_compact(val_str)
    if parsed:
        return parsed
        
    # Fallback to pandas
    try:
        return pd.to_datetime(val_str).date()
    except:
        try:
             # Try Parsing DD/MM/YYYY
             if '/' in val_str:
                 return pd.to_datetime(val_str, format='%d/%m/%Y').date()
             return pd.to_datetime(val_str).date()
        except:
             return None

def import_attendance_from_file(file_path):
    print(f"Reading file: {file_path}")
    
    try:
        # Try multiple engines/encodings if needed, but pandas usually handles it well.
        # attendance.py had complexity here, let's keep it simple first or mimic it?
        # Mimicking the retry logic is safer.
        try:
            df = pd.read_excel(file_path)
        except:
            try:
                df = pd.read_excel(file_path, engine='xlrd')
            except:
                df = pd.read_excel(file_path, engine='openpyxl')
                
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return {'success': 0, 'errors': [f"Failed to read file: {e}"]}

    # Normalize columns: lower, strip
    # BUT wait, the user said "Code is reference". 
    # We need to map columns Flexibly.
    # Expected columns: Code, Date, CheckIn, CheckOut
    # Let's clean column names
    original_cols = df.columns
    df.columns = [str(c).lower().strip() for c in df.columns]
    
    # Check for required columns
    # We need 'code' and 'date' at minimum
    # 'check_in' and 'check_out' can vary?
    # Common names: 'code', 'date', 'check_in', 'time_in', 'check_out', 'time_out', 'in', 'out'
    
    # Helper to find column
    def find_col(candidates):
        for c in candidates:
            if c in df.columns:
                return c
        return None

    col_code = find_col(['code', 'employee_code', 'id', 'كود', 'كود الموظف'])
    col_date = find_col(['date', 'day', 'تاريخ', 'التاريخ'])
    col_in = find_col(['check_in', 'in', 'time_in', 'start', 'حضور', 'دخول', 'وقت الحضور'])
    col_out = find_col(['check_out', 'out', 'time_out', 'end', 'inscan', 'outscan', 'انصراف', 'خروج', 'وقت الانصراف'])

    if not col_code or not col_date:
        return {'success': 0, 'errors': [f"Missing required columns. Found: {list(original_cols)}. Need: Code, Date"]}

    db = DBManager()
    session = db.get_session()
    
    stats = {'success': 0, 'errors': [], 'processed': 0}
    
    print("Starting import...")
    
    # 1. Batch Processing
    # Instead of calling db.add_attendance_log (which commits every time),
    # We will create objects and add to session, then commit ONCE.
    
    existing_count = 0 
    # Optional: Pre-fetch existing logs if we want to avoid duplicates? 
    # Or rely on DB constraints?
    # For now, let's just insert. SQLite is fast enough for insert-ignore if set up, 
    # but let's assume raw logs are append-only mostly.
    
    batch_size = 1000
    pending_commits = 0
    affected_dates = set()
    
    for index, row in df.iterrows():
        try:
            # Code: Ensure string, strip .0 if exists
            code_raw = row.get(col_code)
            if pd.isna(code_raw):
                continue
            
            code = str(code_raw).strip()
            if code.endswith('.0'):
                code = code[:-2] # Remove .0
            if not code:
                continue
                
            date_val = row.get(col_date)
            parsed_date = parse_excel_date(date_val)
            
            if not parsed_date:
                continue
                
            # Process Times
            def parse_time_val(val, date_obj):
                if not clean_value(val):
                    return None
                try:
                    # If val is datetime/timestamp
                    if isinstance(val, (datetime, pd.Timestamp)):
                        # Extract time component if it has one, or use it fully?
                        # If it's just time "08:30:00", pandas might make it 1900-01-01 08:30:00
                        return val 
                    
                    val_str = str(val).strip()
                    # Try simple concat first
                    ts = pd.to_datetime(f"{date_obj.strftime('%Y-%m-%d')} {val_str}")
                    return ts
                except:
                    return None

            check_in_ts = parse_time_val(row.get(col_in), parsed_date) if col_in else None
            check_out_ts = parse_time_val(row.get(col_out), parsed_date) if col_out else None
            
            if not check_in_ts and not check_out_ts:
                continue

            # Add objects directly to session
            if check_in_ts:
                full_ts_in = check_in_ts
                # Ensure it's full datetime
                if getattr(full_ts_in, 'date', None) and full_ts_in.date() != parsed_date:
                     # If time object or different date (1900 issue), fix it
                     t = full_ts_in.time()
                     full_ts_in = datetime.combine(parsed_date, t)
                elif not isinstance(full_ts_in, datetime):
                     continue # Should be datetime by now

                log_in = AttendanceLog(employee_code=code, timestamp=full_ts_in, type='IN')
                session.add(log_in)
                stats['success'] += 1
                pending_commits += 1
                affected_dates.add(parsed_date)
                
            if check_out_ts:
                full_ts_out = check_out_ts
                if getattr(full_ts_out, 'date', None) and full_ts_out.date() != parsed_date:
                     t = full_ts_out.time()
                     full_ts_out = datetime.combine(parsed_date, t)
                elif not isinstance(full_ts_out, datetime):
                     continue

                log_out = AttendanceLog(employee_code=code, timestamp=full_ts_out, type='OUT')
                session.add(log_out)
                stats['success'] += 1
                pending_commits += 1
                affected_dates.add(parsed_date)
            
            # Batch Commit
            if pending_commits >= batch_size:
                session.commit()
                pending_commits = 0
                
        except Exception as e:
            # stats['errors'].append(f"Row {index+2}: {str(e)}")
            # Don't fail the whole batch for one row error?
            # Rollback only if integrity error?
            # For bulk speed, we often ignore individual row errors or catch them.
            pass
            
    # Final Commit
    try:
        if pending_commits > 0:
            session.commit()
    except Exception as e:
        stats['errors'].append(f"Commit Error: {e}")
        session.rollback()

    session.close()
    stats['dates'] = list(affected_dates)
    return stats
