#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verify data for December 6, 2025
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from db_manager import DBManager
from datetime import date

db = DBManager()
session = db.get_session()

from database_models import AttendanceLog, DailyRecord

target_date = date(2025, 12, 6)

# Check logs
logs = db.get_logs_by_date(target_date)
daily = session.query(DailyRecord).filter_by(date=target_date).all()

print("Status for 2025-12-06:")
print(f"Logs: {len(logs)}")
print(f"Daily Records: {len(daily)}")

session.close()
