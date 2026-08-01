import os
import tempfile
import unittest
from datetime import datetime
from uuid import uuid4

from flask import Flask

from app.routes.employees import employees_bp
from core.database_models import BulkSalaryUpdateRequest, Employee, SalaryHistory
from core.db_manager import DBManager


class BulkSalaryIdempotencyTestCase(unittest.TestCase):
    def setUp(self):
        self._database_fd, self._database_path = tempfile.mkstemp(suffix='.db')
        self.db_manager = DBManager(db_path=self._database_path)
        self.app = Flask(__name__)
        self.app.config.update(TESTING=True, SECRET_KEY='test-secret')
        self.app.db = self.db_manager
        self.app.register_blueprint(employees_bp, url_prefix='/employees')
        self.employee_id = self._create_employee()

    def tearDown(self):
        self.db_manager.engine.dispose()
        os.close(self._database_fd)
        os.remove(self._database_path)

    def _create_employee(self):
        session = self.db_manager.get_session()
        try:
            employee = Employee(
                code='EMP-001',
                name='موظف اختبار',
                category='EMPLOYEE',
                basic_salary=5000.0
            )
            session.add(employee)
            session.commit()
            return employee.id
        finally:
            session.close()

    def test_duplicate_salary_request_creates_one_salary_change(self):
        request_key = str(uuid4())
        request_payload = {
            'updates': [{'employee_id': self.employee_id, 'basic_salary': 5500.0}],
            'effective_date': datetime.now().strftime('%d/%m/%Y'),
            'idempotency_key': request_key
        }

        with self.app.test_client() as client:
            first_response = client.post('/employees/bulk_salaries/save', json=request_payload)
            duplicate_response = client.post('/employees/bulk_salaries/save', json=request_payload)

        self.assertTrue(first_response.get_json()['success'])
        self.assertTrue(duplicate_response.get_json()['success'])
        self.assertTrue(duplicate_response.get_json()['duplicate'])

        session = self.db_manager.get_session()
        try:
            self.assertEqual(session.query(BulkSalaryUpdateRequest).count(), 1)
            self.assertEqual(session.query(SalaryHistory).filter_by(employee_id=self.employee_id).count(), 2)
            self.assertEqual(session.query(Employee).filter_by(id=self.employee_id).one().basic_salary, 5500.0)
        finally:
            session.close()
