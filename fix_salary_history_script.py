from core.db_manager import DBManager
from core.database_models import Employee, SalaryHistory, AuditLog
from datetime import datetime
import sys

def repair_missing_history():
    db = DBManager()
    session = db.get_session()
    
    employees = session.query(Employee).all()
    added_count = 0
    records_added = []

    print(f"Starting repair for {len(employees)} employees...")

    for emp in employees:
        # 1. Check if employee already has any history
        existing_history_count = session.query(SalaryHistory).filter(SalaryHistory.employee_id == emp.id).count()
        
        if existing_history_count == 0:
            # No history found - we need to add the initial record
            
            # 2. Try to find the ORIGINAL salary from AuditLogs
            first_audit = session.query(AuditLog).filter(
                AuditLog.employee_code == emp.code,
                AuditLog.field_name == 'basic_salary'
            ).order_by(AuditLog.timestamp.asc()).first()
            
            initial_salary = 0.0
            if first_audit and first_audit.old_value:
                try:
                    initial_salary = float(first_audit.old_value)
                except:
                    initial_salary = emp.basic_salary
            else:
                initial_salary = emp.basic_salary
            
            # 3. Create the initial history record
            # Use hire_date if available, otherwise a default old date
            effective_date = emp.hire_date if emp.hire_date else datetime(2020, 1, 1).date()
            
            # Combine date with min time for DateTime field
            effective_datetime = datetime.combine(effective_date, datetime.min.time())
            
            new_history = SalaryHistory(
                employee_id=emp.id,
                old_salary=0.0,
                new_salary=initial_salary,
                salary_change=initial_salary,
                change_date=datetime.now(),
                effective_date=effective_datetime,
                reason="رصيد افتتاحى - تاريخ التعيين (سكريبت إصلاح)"
            )
            
            session.add(new_history)
            added_count += 1
            records_added.append(f"{emp.code} - {emp.name} (Salary: {initial_salary})")

    if added_count > 0:
        session.commit()
        print(f"Successfully added {added_count} initial records.")
    else:
        print("No missing records found.")
    
    return added_count, records_added

if __name__ == "__main__":
    count, names = repair_missing_history()
    print("\n--- Detailed Report ---")
    for name in names:
        print(f"Added: {name}")
    print(f"\nTotal Records Added: {count}")
