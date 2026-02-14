#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Check if documents exist"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from db_manager import DBManager

db = DBManager()
session = db.get_session()

# Count all documents
from database_models import EmployeeDocument
total_docs = session.query(EmployeeDocument).count()
print(f"إجمالي المستندات في النظام: {total_docs}")

# Get first employee
from database_models import Employee
first_emp = session.query(Employee).first()
if first_emp:
    print(f"\nالموظف الأول: {first_emp.name} (ID: {first_emp.id})")
    docs = db.get_employee_documents(first_emp.id)
    print(f"عدد مستندات هذا الموظف: {len(docs)}")

session.close()
