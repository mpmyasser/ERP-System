
import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'core'))
from db_manager import DBManager
from database_models import Employee

db = DBManager()
session = db.get_session()
emp = session.query(Employee).filter_by(code="114").first()
print(f"Code: {emp.code}")
print(f"Name: {emp.name}")
print(f"Start: {emp.standard_start_time}")
print(f"End: {emp.standard_end_time}")
print(f"OT Allowed: {emp.overtime_allowed}")
