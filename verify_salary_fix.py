import sys
import os

# إضافة المجلد الرئيسي لمسار البحث
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'core'))

from core.db_manager import DBManager
from core.database_models import Employee, SalaryHistory
from core.services.payroll_processor import PayrollCalculator
from datetime import date

try:
    db = DBManager()
    session = db.get_session()
    
    emp = session.query(Employee).filter(Employee.code == '102').first()
    if not emp:
        print("Employee 102 not found")
        sys.exit(1)

    calculator = PayrollCalculator(db)
    
    # شهر 11 سنة 2025
    month, year = 11, 2025
    start_date, end_date = calculator.get_salary_month_date_range(month, year)
    
    # جلب الراتب الفعال
    effective_salary = calculator._get_effective_salary(emp, end_date)
    
    print(f"Employee: {emp.name} (Code: {emp.code})")
    print(f"Payroll Period: {start_date} to {end_date}")
    print(f"--- Result ---")
    print(f"Effective Salary for Nov 2025: {effective_salary}")
    
    if abs(effective_salary - 9500.0) < 0.01:
        print("\nVerification SUCCESS: The system correctly identifies the OLD salary (9500) for November 2025.")
    else:
        print(f"\nVerification FAILED: The system returned {effective_salary} instead of 9500.")

except Exception as e:
    import traceback
    print(f"Error during verification: {e}")
    traceback.print_exc()
