from app import create_app
from core.database_models import Loan, Employee
from datetime import datetime

app = create_app()
with app.app_context():
    session = app.db.get_session()
    try:
        # Simulate Filter: Department 8 and Date > 2026-01-01
        print("--- Testing Filter: Department 8 ---")
        dep_ids = [8]
        query = session.query(Loan).join(Loan.employee).filter(Loan.status == 'Pending')
        query = query.filter(Employee.department_id.in_(dep_ids))
        results = query.all()
        print(f"Found {len(results)} loans for Dept 8.")
        
        # Simulate Filter: Date Range 01/01/2026 - 31/01/2026
        print("--- Testing Filter: Date Range Jan 2026 ---")
        d_from = datetime.strptime('01/01/2026', '%d/%m/%Y').date()
        d_to = datetime.strptime('31/01/2026', '%d/%m/%Y').date()
        
        query = session.query(Loan).join(Loan.employee).filter(Loan.status == 'Pending')
        query = query.filter(Loan.date >= d_from)
        query = query.filter(Loan.date <= d_to)
        results = query.all()
        print(f"Found {len(results)} loans in Jan 2026.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()
