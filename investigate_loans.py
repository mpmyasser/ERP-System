import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from db_manager import DBManager
from datetime import datetime, timedelta

db = DBManager()
session = db.get_session()

from core.database_models import Loan
from sqlalchemy import func

# 1. Count total Loan records
total_count = session.query(func.count(Loan.id)).scalar()
print(f"Total Loan records: {total_count}")

# 2. Get max loan ID
max_id = session.query(func.max(Loan.id)).scalar()
print(f"Max loan ID: {max_id}")

# 3. Get count of loans created in last 1 hour
one_hour_ago = datetime.now() - timedelta(hours=1)
recent_count = session.query(func.count(Loan.id)).filter(Loan.date >= one_hour_ago).scalar()
print(f"Loans in last 1 hour: {recent_count}")

# 4. Check repeated amounts
repeated_amounts = session.query(
    Loan.amount, 
    func.count(Loan.amount).label('count')
).group_by(Loan.amount).having(func.count(Loan.amount) > 100).order_by(func.count(Loan.amount).desc()).limit(5).all()

print("\nTop 5 repeated amounts (>100 occurrences):")
for amount, count in repeated_amounts:
    print(f"  Amount: {amount} - Count: {count}")

session.close()
