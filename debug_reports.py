import sys
import os
from datetime import datetime, date, time
from sqlalchemy import create_engine, func, cast, Date
from sqlalchemy.orm import sessionmaker

# Add core directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from database_models import Base, AttendanceLog, DailyRecord, Employee
from db_manager import DBManager

def debug_attendance():
    print("--- Debugging Attendance Data ---")
    db = DBManager()
    session = db.get_session()
    
    try:
        # 1. Check Attendance Logs
        log_count = session.query(AttendanceLog).count()
        print(f"Total Attendance Logs: {log_count}")
        
        if log_count > 0:
            first_log = session.query(AttendanceLog).first()
            print(f"Sample Log: Emp={first_log.employee_code}, Time={first_log.timestamp} (Type: {type(first_log.timestamp)})")
            
            # Check distinct dates in logs
            dates = session.query(func.date(AttendanceLog.timestamp)).distinct().all()
            print(f"Distinct Dates in Logs: {dates}")
            
        # 2. Check Daily Records
        record_count = session.query(DailyRecord).count()
        print(f"Total Daily Records: {record_count}")
        
        if record_count > 0:
            first_record = session.query(DailyRecord).first()
            print(f"Sample Record: EmpID={first_record.employee_id}, Date={first_record.date}")

        # 3. Test Processing Logic (The suspected issue)
        if log_count > 0:
            # Pick a date from logs
            sample_log = session.query(AttendanceLog).order_by(AttendanceLog.timestamp.desc()).first()
            target_date = sample_log.timestamp.date()
            print(f"\nTesting processing for date: {target_date}")
            
            # Try the current logic (CAST)
            print("Testing CAST logic...")
            logs_cast = session.query(AttendanceLog).filter(
                cast(AttendanceLog.timestamp, Date) == target_date
            ).all()
            print(f"Logs found with CAST: {len(logs_cast)}")
            
            # Try the proposed fix (RANGE)
            print("Testing RANGE logic...")
            start_of_day = datetime.combine(target_date, time.min)
            end_of_day = datetime.combine(target_date, time.max)
            logs_range = session.query(AttendanceLog).filter(
                AttendanceLog.timestamp >= start_of_day,
                AttendanceLog.timestamp <= end_of_day
            ).all()
            print(f"Logs found with RANGE: {len(logs_range)}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    debug_attendance()
