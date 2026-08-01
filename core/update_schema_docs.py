from sqlalchemy import create_engine
from database_models import EmployeeDocument
import os

# Connect to database
db_path = os.path.join(os.path.dirname(__file__), 'hr.db')
engine = create_engine(f'sqlite:///{db_path}')

# Create table
EmployeeDocument.__table__.create(engine)

print("Created employee_documents table.")
