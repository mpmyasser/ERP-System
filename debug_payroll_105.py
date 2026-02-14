import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'core'))

from db_manager import DBManager
from services.payroll_processor import PayrollCalculator
from database_models import Employee, DailyRecord

def debug_payroll_105():
    db = DBManager()
    session = db.get_session()
    calc = PayrollCalculator(db)
    
    emp = session.query(Employee).filter_by(code='105').first()
    if not emp:
        print("Employee 105 not found")
        return

    month = 1
    year = 2026
    
    print(f"Employee: {emp.name} (ID: {emp.id})")
    print(f"Basic Salary: {emp.basic_salary}")
    print(f"Insurance Salary: {emp.insurance_salary}")
    print(f"Is Insured: {emp.is_insured}")
    print(f"Insurance Policy: {emp.insurance_policy}")
    
    # Check Daily Records
    start_date, end_date = calc.get_salary_month_date_range(month, year)
    records = session.query(DailyRecord).filter(
        DailyRecord.employee_id == emp.id,
        DailyRecord.date >= start_date,
        DailyRecord.date <= end_date
    ).all()
    
    print(f"Found {len(records)} daily records between {start_date} and {end_date}")
    for r in records:
        print(f"  Date: {r.date}, Status: {r.status}, Attendance Days Incr: {'Yes' if r.status != 'Absent' else 'No'}")

    report = calc.get_detailed_payroll_report(emp.id, month, year)
    summary = report['summary']
    
    print("\n--- Summary Data from Calculator ---")
    print(f"Attendance Days: {summary['attendance_days']}")
    print(f"Gross Salary: {summary['gross_salary']}")
    print(f"Insurance Deduction: {summary['insurance']}")
    print(f"Net Salary: {summary['net_salary']}")
    
    session.close()

if __name__ == "__main__":
    debug_payroll_105()
