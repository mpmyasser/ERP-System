import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from db_manager import DBManager
from datetime import datetime, time, date

db = DBManager()
session = db.get_session()

from database_models import AttendanceLog

# Get all distinct dates in the database
from sqlalchemy import func

distinct_dates = session.query(
    func.date(AttendanceLog.timestamp)
).distinct().order_by(func.date(AttendanceLog.timestamp)).all()

print("جميع التواريخ الموجودة في قاعدة البيانات:")
print("=" * 60)

for date_tuple in distinct_dates:
    if date_tuple[0]:
        date_obj = date_tuple[0]
        
        # Ensure it's a date object
        if isinstance(date_obj, str):
            from datetime import datetime as dt
            date_obj = dt.strptime(date_obj, '%Y-%m-%d').date()
        
        # Count logs for this date
        start_of_day = datetime.combine(date_obj, time.min)
        end_of_day = datetime.combine(date_obj, time.max)
        
        count = session.query(AttendanceLog).filter(
            AttendanceLog.timestamp >= start_of_day,
            AttendanceLog.timestamp <= end_of_day
        ).count()
        
        print(f"{date_obj}: {count} سجل بصمة")

session.close()
