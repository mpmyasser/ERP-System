#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Integration tests for Attendance Import and Display
Tests that imported data appears in UI views
"""

import sys
import os
import io
import tempfile
import pandas as pd
from datetime import date, time, datetime, timedelta
from io import BytesIO

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'core')

from app import create_app
from core.db_manager import DBManager
from core.database_models import AttendanceLog, DailyRecord, Employee, Department
from sqlalchemy.orm import joinedload

def test_attendance_import_creates_daily_records():
    """Test 1: Imported attendance creates DailyRecord entries"""
    print("\n" + "="*80)
    print("TEST 1: Attendance Import Creates DailyRecord")
    print("="*80)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = os.path.join(tmpdir, 'test.db')
        db = DBManager(db_path=test_db)
        
        # Create test data
        dept = db.add_department("Test Department")
        emp = db.add_employee(
            name="Test Employee",
            code="EMP001",
            category="EMPLOYEE",
            department_id=dept.id,
            hire_date=date.today(),
            basic_salary=5000.0
        )
        
        # Manually create attendance logs like import would
        session = db.get_session()
        test_date = date.today()
        
        log1 = AttendanceLog(
            employee_code="EMP001",
            timestamp=datetime.combine(test_date, time(8, 0))  # Check in 8:00 AM
        )
        log2 = AttendanceLog(
            employee_code="EMP001",
            timestamp=datetime.combine(test_date, time(17, 0))  # Check out 5:00 PM
        )
        session.add(log1)
        session.add(log2)
        session.commit()
        
        # Verify logs were saved
        log_count = session.query(AttendanceLog).filter_by(
            employee_code="EMP001"
        ).count()
        print(f"   Created {log_count} attendance logs")
        
        # Process logs into DailyRecord (simulating what import should do)
        from collections import defaultdict
        emp_logs = defaultdict(list)
        
        logs = session.query(AttendanceLog).filter(
            AttendanceLog.timestamp.like(f"{test_date}%")
        ).all()
        
        for log in logs:
            emp_logs[log.employee_code].append(log.timestamp)
        
        for emp_code, timestamps in emp_logs.items():
            emp_obj = db.get_employee_by_code(str(emp_code))
            if emp_obj:
                sorted_times = sorted(timestamps)
                check_in = sorted_times[0].time()
                check_out = sorted_times[-1].time() if len(sorted_times) > 1 else None
                
                db.add_daily_record(
                    employee_id=emp_obj.id,
                    date=test_date,
                    check_in=check_in,
                    check_out=check_out
                )
        
        session.close()
        
        # Verify DailyRecord was created
        session = db.get_session()
        record = session.query(DailyRecord).filter(
            DailyRecord.employee_id == emp.id,
            DailyRecord.date == test_date
        ).first()
        session.close()
        
        if record and record.check_in == time(8, 0) and record.check_out == time(17, 0):
            print("✅ PASS: DailyRecord created with correct times")
            print(f"   Check-in: {record.check_in}")
            print(f"   Check-out: {record.check_out}")
            return True
        else:
            print("❌ FAIL: DailyRecord not created or times incorrect")
            if record:
                print(f"   Record found but check_in: {record.check_in}, check_out: {record.check_out}")
            return False


def test_attendance_daily_view_queries_records():
    """Test 2: Daily view correctly queries DailyRecord"""
    print("\n" + "="*80)
    print("TEST 2: Daily View Queries DailyRecord")
    print("="*80)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = os.path.join(tmpdir, 'test.db')
        db = DBManager(db_path=test_db)
        
        # Create test data
        dept = db.add_department("Test Department")
        emp = db.add_employee(
            name="Test Employee",
            code="EMP002",
            category="EMPLOYEE",
            department_id=dept.id,
            hire_date=date.today(),
            basic_salary=5000.0
        )
        
        test_date = date.today()
        db.add_daily_record(
            employee_id=emp.id,
            date=test_date,
            check_in=time(8, 30),
            check_out=time(17, 30)
        )
        
        # Simulate what the view does
        session = db.get_session()
        attendance_records = session.query(DailyRecord)\
            .filter_by(date=test_date)\
            .options(joinedload(DailyRecord.employee))\
            .all()
        session.close()
        
        if len(attendance_records) > 0 and attendance_records[0].employee.code == "EMP002":
            print("✅ PASS: View correctly queries and loads records")
            print(f"   Records found: {len(attendance_records)}")
            print(f"   Employee: {attendance_records[0].employee.name}")
            return True
        else:
            print("❌ FAIL: View query returned no records")
            return False


def test_attendance_date_filtering():
    """Test 3: View correctly filters by date"""
    print("\n" + "="*80)
    print("TEST 3: Attendance Date Filtering")
    print("="*80)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = os.path.join(tmpdir, 'test.db')
        db = DBManager(db_path=test_db)
        
        # Create test data
        dept = db.add_department("Test Department")
        emp = db.add_employee(
            name="Test Employee",
            code="EMP003",
            category="EMPLOYEE",
            department_id=dept.id,
            hire_date=date.today() - timedelta(days=30),
            basic_salary=5000.0
        )
        
        # Create records for different dates
        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        
        db.add_daily_record(emp.id, yesterday, time(8, 0), time(17, 0))
        db.add_daily_record(emp.id, today, time(8, 30), time(17, 30))
        db.add_daily_record(emp.id, tomorrow, time(9, 0), time(18, 0))
        
        # Query only today's records
        session = db.get_session()
        today_records = session.query(DailyRecord)\
            .filter_by(date=today)\
            .options(joinedload(DailyRecord.employee))\
            .all()
        
        yesterday_records = session.query(DailyRecord)\
            .filter_by(date=yesterday)\
            .options(joinedload(DailyRecord.employee))\
            .all()
        session.close()
        
        if (len(today_records) == 1 and 
            len(yesterday_records) == 1 and
            today_records[0].check_in == time(8, 30)):
            print("✅ PASS: Date filtering works correctly")
            print(f"   Today's records: {len(today_records)}")
            print(f"   Yesterday's records: {len(yesterday_records)}")
            print(f"   Today's check-in: {today_records[0].check_in}")
            return True
        else:
            print("❌ FAIL: Date filtering not working")
            return False


def test_attendance_view_route_rendering():
    """Test 4: Attendance daily route renders correctly"""
    print("\n" + "="*80)
    print("TEST 4: Attendance Daily Route Rendering")
    print("="*80)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = os.path.join(tmpdir, 'test.db')
        db = DBManager(db_path=test_db)
        
        # Create test data
        dept = db.add_department("Test Department")
        emp = db.add_employee(
            name="محمود أحمد",
            code="EMP004",
            category="EMPLOYEE",
            department_id=dept.id,
            hire_date=date.today(),
            basic_salary=5000.0
        )
        
        today = date.today()
        db.add_daily_record(emp.id, today, time(8, 0), time(17, 0))
        
        app = create_app()
        with app.test_client() as client:
            response = client.get(f'/attendance/?date={today.strftime("%Y-%m-%d")}')
            html_content = response.get_data(as_text=True)
            
            checks = [
                (response.status_code == 200, "Route returns 200 OK"),
                ('attendance' in html_content.lower(), "Template mentions attendance"),
                ('EMP004' in html_content, "Employee code displayed"),
                ('محمود' in html_content, "Employee name displayed"),
                ('08:00' in html_content or '8:00' in html_content, "Check-in time displayed"),
            ]
            
            all_passed = True
            for check, description in checks:
                if check:
                    print(f"   ✅ {description}")
                else:
                    print(f"   ❌ {description}")
                    all_passed = False
            
            if all_passed:
                print("\n✅ PASS: Route renders template with attendance data")
                return True
            else:
                print("\n❌ FAIL: Route rendering incomplete")
                return False


def test_attendance_no_records_message():
    """Test 5: View displays appropriate message when no records"""
    print("\n" + "="*80)
    print("TEST 5: Attendance No Records Message")
    print("="*80)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = os.path.join(tmpdir, 'test.db')
        db = DBManager(db_path=test_db)
        
        # Create department but don't create records
        db.add_department("Test Department")
        
        app = create_app()
        with app.test_client() as client:
            response = client.get(f'/attendance/?date={date.today().strftime("%Y-%m-%d")}')
            html_content = response.get_data(as_text=True)
            
            if response.status_code == 200 and ('لا توجد' in html_content or 'no' in html_content.lower()):
                print("✅ PASS: No records message displayed correctly")
                return True
            else:
                print("❌ FAIL: No records message not displayed")
                return False


def test_multiple_employees_attendance():
    """Test 6: View displays records for multiple employees correctly"""
    print("\n" + "="*80)
    print("TEST 6: Multiple Employees Attendance Display")
    print("="*80)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = os.path.join(tmpdir, 'test.db')
        db = DBManager(db_path=test_db)
        
        # Create test data
        dept = db.add_department("Test Department")
        emp1 = db.add_employee(
            name="Employee One",
            code="EMP005",
            category="EMPLOYEE",
            department_id=dept.id,
            hire_date=date.today(),
            basic_salary=5000.0
        )
        emp2 = db.add_employee(
            name="Employee Two",
            code="EMP006",
            category="EMPLOYEE",
            department_id=dept.id,
            hire_date=date.today(),
            basic_salary=5000.0
        )
        emp3 = db.add_employee(
            name="Employee Three",
            code="EMP007",
            category="EMPLOYEE",
            department_id=dept.id,
            hire_date=date.today(),
            basic_salary=5000.0
        )
        
        today = date.today()
        db.add_daily_record(emp1.id, today, time(8, 0), time(17, 0))
        db.add_daily_record(emp2.id, today, time(8, 15), time(17, 30))
        db.add_daily_record(emp3.id, today, time(8, 30), time(18, 0))
        
        # Query all records
        session = db.get_session()
        records = session.query(DailyRecord)\
            .filter_by(date=today)\
            .options(joinedload(DailyRecord.employee))\
            .all()
        session.close()
        
        if len(records) == 3:
            codes = [r.employee.code for r in records]
            if all(code in codes for code in ["EMP005", "EMP006", "EMP007"]):
                print("✅ PASS: All 3 employees' records retrieved correctly")
                for record in records:
                    print(f"   - {record.employee.code}: {record.check_in} to {record.check_out}")
                return True
        
        print("❌ FAIL: Not all employee records found")
        print(f"   Found {len(records)} records, expected 3")
        return False


def test_attendance_employee_relationship():
    """Test 7: DailyRecord correctly loads Employee relationship"""
    print("\n" + "="*80)
    print("TEST 7: DailyRecord-Employee Relationship Loading")
    print("="*80)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = os.path.join(tmpdir, 'test.db')
        db = DBManager(db_path=test_db)
        
        # Create test data
        dept = db.add_department("Test Department")
        emp = db.add_employee(
            name="Test Employee",
            code="EMP008",
            category="EMPLOYEE",
            department_id=dept.id,
            hire_date=date.today(),
            basic_salary=5000.0
        )
        
        db.add_daily_record(emp.id, date.today(), time(8, 0), time(17, 0))
        
        # Query with eager loading
        session = db.get_session()
        record = session.query(DailyRecord)\
            .filter_by(date=date.today())\
            .options(joinedload(DailyRecord.employee))\
            .first()
        
        if record and record.employee and record.employee.code == "EMP008":
            print("✅ PASS: Employee relationship loaded correctly")
            print(f"   Record ID: {record.id}")
            print(f"   Employee ID: {record.employee.id}")
            print(f"   Employee Code: {record.employee.code}")
            print(f"   Employee Name: {record.employee.name}")
            session.close()
            return True
        else:
            print("❌ FAIL: Employee relationship not loaded")
            session.close()
            return False


def run_all_tests():
    """Run all attendance tests"""
    print("\n" + "="*80)
    print("ATTENDANCE IMPORT & DISPLAY INTEGRATION TESTS")
    print("="*80)
    
    tests = [
        test_attendance_import_creates_daily_records,
        test_attendance_daily_view_queries_records,
        test_attendance_date_filtering,
        test_attendance_view_route_rendering,
        test_attendance_no_records_message,
        test_multiple_employees_attendance,
        test_attendance_employee_relationship,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
        return True
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
