
import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.join(os.getcwd(), 'core'))

from db_manager import DBManager
from services.payroll_processor import PayrollCalculator
from database_models import Employee, DailyRecord

db = DBManager()
session = db.get_session()

code = "114"
emp = session.query(Employee).filter_by(code=code).first()

if not emp:
    print(f"Employee {code} not found")
    sys.exit()

print(f"Employee: {emp.name} (Code: {emp.code})")
print(f"Basic Salary: {emp.basic_salary}")
print(f"Standard Start: {emp.standard_start_time}")
print(f"Standard End: {emp.standard_end_time}")
print(f"Overtime Allowed: {emp.overtime_allowed}")

calc = PayrollCalculator(db)
month = datetime.now().month
year = datetime.now().year

print(f"Generating Report for {month}/{year}")

# 1. Check Date Range
start, end = calc.get_salary_month_date_range(month, year)
print(f"Date Range: {start} to {end}")

# 2. Check Records
records = calc._get_monthly_records(emp.id, month, year)
print(f"Found {len(records)} daily records")

non_zero_found = False
for r in records:
    if r.late_minutes > 0 or r.overtime_hours > 0 or r.early_leave_minutes > 0:
        non_zero_found = True
        print(f"found DATA: Date: {r.date} | In: {r.check_in} | Out: {r.check_out}")
        print(f"   Stored Late Minutes: {r.late_minutes} -> Ded: {r.late_deduction_amount}")
        print(f"   Stored OT Hours: {r.overtime_hours} -> Pay: {r.overtime_pay_amount}")
        
if not non_zero_found:
    print("NO DATA FOUND: All records have 0 late/early/OT.")
    # Print sample to see why
    if records:
        r = records[-1] # Last record
        print(f"Sample (Last Rec): {r.date} | In: {r.check_in} | Out: {r.check_out}")
        print(f"   Value: {r.late_minutes}")

from policy.hr_policy import HRPolicy
print("-" * 20)
print(f"Policy Grace Period: {HRPolicy.LATE_GRACE_PERIOD_MINUTES}")
print(f"Policy OT Min Mins: {HRPolicy.OVERTIME_MIN_MINUTES}")
print("-" * 20)

# 3. Full Report
report = calc.get_detailed_payroll_report(emp.id, month, year)
print("-" * 20)
print("Report Summary:")
print(report['summary'])
print("-" * 20)
print("First 3 Daily Details:")
for d in report['daily_details'][:3]:
    print(d)
