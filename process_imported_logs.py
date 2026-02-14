#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Process imported attendance logs into daily records
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from db_manager import DBManager
from database_models import AttendanceLog, DailyRecord, Employee
from datetime import date, datetime, time
from collections import defaultdict

# Connect to database
db = DBManager()
session = db.get_session()

# Define the dates to process
dates_to_process = [
    date(2025, 12, 4),
    date(2025, 12, 5),
    date(2025, 12, 6),
]

print("معالجة سجلات البصمة المستوردة...")
print("=" * 60)

total_processed = 0

for target_date in dates_to_process:
    print(f"\nمعالجة التاريخ: {target_date}")
    
    # Get logs for this date using the fixed method
    logs = db.get_logs_by_date(target_date)
    print(f"  عدد السجلات المستوردة: {len(logs)}")
    
    if not logs:
        print(f"  لا توجد سجلات لمعالجتها")
        continue
    
    # Group logs by employee
    emp_logs = defaultdict(list)
    for log in logs:
        emp_logs[log.employee_code].append(log.timestamp)
    
    print(f"  عدد الموظفين: {len(emp_logs)}")
    
    # Process each employee
    processed_for_date = 0
    skipped = 0
    
    for emp_code, timestamps in emp_logs.items():
        if not timestamps:
            continue
        
        # Find employee by code
        employee = session.query(Employee).filter_by(code=emp_code).first()
        if not employee:
            skipped += 1
            continue
        
        emp_id = employee.id
        
        # Sort timestamps
        sorted_times = sorted(timestamps)
        check_in = sorted_times[0].time()
        check_out = sorted_times[-1].time() if len(sorted_times) > 1 else None
        
        # Check if record exists
        existing = session.query(DailyRecord).filter_by(
            employee_id=emp_id,
            date=target_date
        ).first()
        
        if existing:
            # Update existing record
            existing.check_in = check_in
            existing.check_out = check_out
            existing.late_minutes = 0
            existing.overtime_hours = 0.0
            existing.status = "Present"  # Update status for imported records
        else:
            # Create new record
            daily_record = DailyRecord(
                employee_id=emp_id,
                date=target_date,
                check_in=check_in,
                check_out=check_out,
                late_minutes=0,
                overtime_hours=0.0,
                status="Present"  # Default status for imported records
            )
            session.add(daily_record)
        
        processed_for_date += 1
    
    # Commit changes for this date
    try:
        session.commit()
        print(f"  ✓ تمت معالجة {processed_for_date} موظف")
        if skipped > 0:
            print(f"  ⚠ تم تخطي {skipped} موظف (غير موجود في النظام)")
        total_processed += processed_for_date
    except Exception as e:
        session.rollback()
        print(f"  ✗ خطأ في المعالجة: {str(e)}")

print("\n" + "=" * 60)
print(f"✓ تمت معالجة {total_processed} سجل حضور يومي بنجاح")
print("=" * 60)

session.close()
