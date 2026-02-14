import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'core'))

from db_manager import DBManager
from services.payroll_processor import PayrollCalculator
from database_models import Employee

def check_jan_payroll():
    db = DBManager()
    session = db.get_session()
    calc = PayrollCalculator(db)
    
    emp_code = '105'
    emp = session.query(Employee).filter_by(code=emp_code).first()
    
    if not emp:
        print(f"Employee {emp_code} not found")
        return

    print(f"--- Data for Employee {emp.name} (Code: {emp.code}) ---")
    print(f"Is Insured: {emp.is_insured}")
    print(f"Policy: {emp.insurance_policy}")
    print(f"Insurance Salary: {emp.insurance_salary}")
    print(f"Employee Share: {emp.insurance_employee_share}%")
    
    # Simulation for January 2026
    month = 1
    year = 2026
    
    report = calc.calculate_monthly_payroll(emp.id, month, year)
    
    print(f"\n--- Payroll Simulation result for {month}/{year} ---")
    print(f"Gross Salary: {report['Gross Salary']}")
    print(f"Insurance Deduction: {report['Insurance']}")
    print(f"Net Salary: {report['Net Salary']}")
    
    session.close()

if __name__ == "__main__":
    check_jan_payroll()
