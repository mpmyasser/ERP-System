
import sys
import os
sys.path.insert(0, os.path.abspath('d:/H.R'))
sys.path.insert(0, os.path.abspath('d:/H.R/core'))
from core.db_manager import DBManager

def test_search():
    db = DBManager()
    
    print("--- Searching for code '180' ---")
    loans = db.search_loans(code='180')
    print(f"Found {len(loans)} loans")
    for loan in loans:
        print(f"Loan ID: {loan.id}, Emp Code: {loan.employee.code}, Amount: {loan.amount}")
        
    print("\n--- Inspecting Emp 163 and 151 ---")
    # Check if we can find these employees to see if they have 180 in their data
    for code in ['163', '151']:
        emp = db.get_employee_by_code(code)
        if emp:
            loans = db.search_loans(code=code)
            print(f"Emp {code}: Found {len(loans)} loans")
            for loan in loans:
                 print(f"  Loan ID: {loan.id}, Amount: {loan.amount}, Date: {loan.date}")

if __name__ == "__main__":
    test_search()
