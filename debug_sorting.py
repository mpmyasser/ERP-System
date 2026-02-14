from app import create_app
from core.database_models import Loan, Employee, Department

app = create_app()
with app.app_context():
    session = app.db.get_session()
    try:
        # Test Sort by Amount DESC
        print("--- Testing Sort: Amount DESC ---")
        query = session.query(Loan).join(Loan.employee).filter(Loan.status == 'Pending')
        query = query.order_by(Loan.amount.desc())
        results = query.limit(5).all()
        for l in results:
            print(f"Loan ID: {l.id}, Amount: {l.amount}")

        # Test Sort by Code ASC
        print("\n--- Testing Sort: Code ASC ---")
        query = session.query(Loan).join(Loan.employee).filter(Loan.status == 'Pending')
        query = query.order_by(Employee.code.asc())
        results = query.limit(5).all()
        for l in results:
            print(f"Loan ID: {l.id}, Code: {l.employee.code}")
            
        # Test Sort by Department Name
        print("\n--- Testing Sort: Department Name ---")
        query = session.query(Loan).join(Loan.employee).join(Employee.department).filter(Loan.status == 'Pending')
        query = query.order_by(Department.name.asc())
        results = query.limit(5).all()
        for l in results:
             print(f"Loan ID: {l.id}, Dept: {l.employee.department.name}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        session.close()
