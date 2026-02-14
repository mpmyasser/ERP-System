#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Manually add attendance logs for a specific date and create daily records
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from db_manager import DBManager
from database_models import Employee
from datetime import datetime, date, time
from collections import defaultdict

print("=" * 70)
print("🔧 إضافة سجلات البصمة يدويّاً")
print("=" * 70)

db = DBManager()
session = db.get_session()

# Get target date
target_date = date(2025, 12, 6)
print(f"\n📅 التاريخ المستهدف: {target_date}")

# Get all employees
employees = session.query(Employee).all()
print(f"📊 عدد الموظفين في النظام: {len(employees)}")

# Ask user for employee count
print("\n⚠️ سيتم إضافة سجلات بصمة لـ 83 موظف")
print("    - وقت الحضور: 08:00")
print("    - وقت الانصراف: 17:30")

response = input("\nهل تريد المتابعة؟ (نعم/لا): ").strip().lower()

if response not in ['نعم', 'yes', 'y']:
    print("تم الإلغاء")
    session.close()
    sys.exit(0)

# Add attendance logs for all employees
success_count = 0
skip_count = 0

print(f"\n⏳ جاري إضافة السجلات...")

for emp in employees[:83]:  # First 83 employees
    try:
        check_in_time = datetime.combine(target_date, time(8, 0, 0))
        check_out_time = datetime.combine(target_date, time(17, 30, 0))
        
        # Add IN log
        db.add_attendance_log(emp.code, check_in_time, 'IN')
        # Add OUT log
        db.add_attendance_log(emp.code, check_out_time, 'OUT')
        
        success_count += 1
    except Exception as e:
        print(f"❌ خطأ مع الموظف {emp.code}: {e}")
        skip_count += 1

print(f"\n✅ تم إضافة {success_count * 2} سجل بصمة ({success_count} موظف)")
if skip_count > 0:
    print(f"⚠️ تم تخطي {skip_count} موظف")

# Now process these logs into daily records
print(f"\n⏳ جاري معالجة السجلات إلى سجلات حضور يومي...")

from database_models import DailyRecord, AttendanceLog

# Get all logs for this date
logs = db.get_logs_by_date(target_date)
print(f"📊 السجلات المكتشفة: {len(logs)}")

if logs:
    # Group by employee code
    emp_logs = defaultdict(list)
    for log in logs:
        emp_logs[log.employee_code].append(log.timestamp)
    
    print(f"👥 عدد الموظفين: {len(emp_logs)}")
    
    # Create daily records
    processed = 0
    for emp_code, timestamps in emp_logs.items():
        # Find employee
        employee = session.query(Employee).filter_by(code=emp_code).first()
        if not employee:
            continue
        
        # Sort timestamps
        sorted_times = sorted(timestamps)
        check_in = sorted_times[0].time()
        check_out = sorted_times[-1].time() if len(sorted_times) > 1 else None
        
        # Check if record exists
        existing = session.query(DailyRecord).filter_by(
            employee_id=employee.id,
            date=target_date
        ).first()
        
        if existing:
            existing.check_in = check_in
            existing.check_out = check_out
            existing.status = "Present"
        else:
            daily_record = DailyRecord(
                employee_id=employee.id,
                date=target_date,
                check_in=check_in,
                check_out=check_out,
                status="Present",
                late_minutes=0,
                overtime_hours=0.0
            )
            session.add(daily_record)
        
        processed += 1
    
    try:
        session.commit()
        print(f"✅ تم إنشاء {processed} سجل حضور يومي")
    except Exception as e:
        session.rollback()
        print(f"❌ خطأ في الحفظ: {e}")

print("\n" + "=" * 70)
print("✅ تمت العملية بنجاح!")
print("=" * 70)
print("\n📌 يمكنك الآن:")
print("   1. الذهاب لصفحة الحضور اليومي")
print("   2. اختيار التاريخ 6/12/2025")
print("   3. ستظهر جميع سجلات الحضور")
print("=" * 70)

session.close()
        # 2. Process each date
        total_processed = 0
        for d in unique_dates:
            print(f"Processing date: {d}...", end=" ")
            count = db.process_attendance_for_date(d)
            print(f"Done. Created/Updated {count} records.")
            total_processed += count
            
        # 3. Verify DailyRecords count
        total_records = session.query(DailyRecord).count()
        print(f"\nTotal Daily Records in DB now: {total_records}")
        
        if total_records > 0:
            print("\n✅ SUCCESS: Data is definitely in the database now.")
            print(f"Please search for dates between {min(unique_dates)} and {max(unique_dates)}")
        else:
            print("\n❌ ERROR: Still no records in DailyRecord table.")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    force_process()
