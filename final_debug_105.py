import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'core'))

from db_manager import DBManager
from services.payroll_processor import PayrollCalculator
from database_models import Employee, DailyRecord

def final_debug():
    db = DBManager()
    session = db.get_session()
    calc = PayrollCalculator(db)
    
    # 1. Fetch employee 105
    emp = session.query(Employee).filter_by(code='105').first()
    if not emp:
        print("M105_NOT_FOUND")
        return

    print(f"DEBUG_START")
    print(f"EMP_ID: {emp.id}")
    print(f"EMP_NAME: {emp.name}")
    print(f"IS_INSURED: {emp.is_insured}")
    print(f"INS_POLICY: {emp.insurance_policy}")
    print(f"INS_SALARY: {emp.insurance_salary}")
    print(f"EMP_SHARE: {emp.insurance_employee_share}")
    print(f"COMP_SHARE: {emp.insurance_company_share}")

    # 2. Check for Jan 2026 Simulation
    report = calc.calculate_monthly_payroll(emp.id, 1, 2026)
    print(f"CALC_INSURANCE: {report['Insurance']}")
    print(f"CALC_GROSS: {report['Gross Salary']}")
    print(f"CALC_NET: {report['Net Salary']}")
    
    # 3. Check for any other employee with same code?
    all_105s = session.query(Employee).filter_by(code='105').all()
    print(f"TOTAL_105_RECORDS: {len(all_105s)}")

    session.close()

if __name__ == "__main__":
    final_debug()
