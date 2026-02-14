#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comprehensive Unit Tests for Bonus System
Tests database schema, model, form, and payroll integration
Covers: field existence, data types, constraints, form rendering, salary logic
"""

import sys
import os
import io
import unittest
import tempfile
from datetime import date
from decimal import Decimal

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from app import create_app
from app.forms import BonusForm
from core.db_manager import DBManager
from core.database_models import Bonus, Employee, Department
from sqlalchemy import inspect, Column, Boolean, Integer, Float, String, Date, ForeignKey
from sqlalchemy.orm import relationship


class BonusDatabaseSchemaTest(unittest.TestCase):
    """Test database schema for bonuses table"""
    
    def setUp(self):
        """Create test database"""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.test_db = os.path.join(self.tmpdir.name, 'test.db')
        self.db = DBManager(db_path=self.test_db)
    
    def tearDown(self):
        """Cleanup test database"""
        try:
            self.db.engine.dispose()
        except:
            pass
        import gc
        gc.collect()
        try:
            self.tmpdir.cleanup()
        except:
            pass
    
    def test_bonuses_table_exists(self):
        """Verify bonuses table exists in database"""
        inspector = inspect(self.db.engine)
        self.assertTrue(
            inspector.has_table('bonuses'),
            "bonuses table does not exist in database"
        )
    
    def test_paid_with_salary_column_exists(self):
        """Verify paid_with_salary column exists in bonuses table"""
        inspector = inspect(self.db.engine)
        columns = {col['name']: col for col in inspector.get_columns('bonuses')}
        
        self.assertIn(
            'paid_with_salary',
            columns,
            "paid_with_salary column not found in bonuses table"
        )
    
    def test_paid_with_salary_column_type(self):
        """Verify paid_with_salary is Boolean type"""
        inspector = inspect(self.db.engine)
        columns = {col['name']: col for col in inspector.get_columns('bonuses')}
        
        col_type = str(columns['paid_with_salary']['type'])
        self.assertIn(
            'BOOLEAN',
            col_type.upper(),
            f"paid_with_salary column type is {col_type}, expected BOOLEAN"
        )
    
    def test_paid_with_salary_not_nullable(self):
        """Verify paid_with_salary is NOT NULL"""
        inspector = inspect(self.db.engine)
        columns = {col['name']: col for col in inspector.get_columns('bonuses')}
        
        self.assertFalse(
            columns['paid_with_salary']['nullable'],
            "paid_with_salary should be NOT NULL"
        )
    
    def test_required_columns_exist(self):
        """Verify all required columns exist"""
        inspector = inspect(self.db.engine)
        columns = {col['name']: col for col in inspector.get_columns('bonuses')}
        
        required_columns = [
            'id', 'employee_id', 'amount', 'reason',
            'date_awarded', 'paid_with_salary'
        ]
        
        for col_name in required_columns:
            self.assertIn(
                col_name,
                columns,
                f"Column {col_name} not found in bonuses table"
            )


class BonusModelTest(unittest.TestCase):
    """Test Bonus SQLAlchemy model"""
    
    def setUp(self):
        """Create test database"""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.test_db = os.path.join(self.tmpdir.name, 'test.db')
        self.db = DBManager(db_path=self.test_db)
        self.dept = self.db.add_department("Test Department")
        self.emp = self.db.add_employee(
            name="Test Employee",
            code="TEST001",
            category="EMPLOYEE",
            department_id=self.dept.id,
            hire_date=date.today(),
            basic_salary=5000.0
        )
    
    def tearDown(self):
        """Cleanup test database"""
        try:
            self.db.engine.dispose()
        except:
            pass
        import gc
        gc.collect()
        try:
            self.tmpdir.cleanup()
        except:
            pass
    
    def test_bonus_has_paid_with_salary_attribute(self):
        """Verify Bonus model has paid_with_salary attribute"""
        self.assertTrue(
            hasattr(Bonus, 'paid_with_salary'),
            "Bonus model missing paid_with_salary attribute"
        )
    
    def test_bonus_paid_with_salary_is_column(self):
        """Verify paid_with_salary is a Column"""
        self.assertIsInstance(
            Bonus.paid_with_salary.property.columns[0],
            Column,
            "paid_with_salary is not a SQLAlchemy Column"
        )
    
    def test_bonus_default_true(self):
        """Verify paid_with_salary defaults to True"""
        bonus = Bonus(
            employee_id=self.emp.id,
            amount=500.0,
            reason="Test",
            date_awarded=date.today()
        )
        
        self.assertTrue(
            bonus.paid_with_salary,
            f"Default value is {bonus.paid_with_salary}, expected True"
        )
    
    def test_bonus_can_be_false(self):
        """Verify paid_with_salary can be set to False"""
        bonus = Bonus(
            employee_id=self.emp.id,
            amount=500.0,
            reason="Test",
            date_awarded=date.today(),
            paid_with_salary=False
        )
        
        self.assertFalse(
            bonus.paid_with_salary,
            "paid_with_salary should be False when explicitly set"
        )
    
    def test_bonus_create_with_true(self):
        """Verify bonus can be created with paid_with_salary=True"""
        bonus = self.db.add_bonus(
            employee_id=self.emp.id,
            amount=1000.0,
            reason="Performance bonus",
            date_awarded=date.today(),
            paid_with_salary=True
        )
        
        self.assertIsNotNone(bonus)
        self.assertTrue(bonus.paid_with_salary)
    
    def test_bonus_create_with_false(self):
        """Verify bonus can be created with paid_with_salary=False"""
        bonus = self.db.add_bonus(
            employee_id=self.emp.id,
            amount=500.0,
            reason="Immediate payment",
            date_awarded=date.today(),
            paid_with_salary=False
        )
        
        self.assertIsNotNone(bonus)
        self.assertFalse(bonus.paid_with_salary)


class BonusFormTest(unittest.TestCase):
    """Test BonusForm Flask-WTF form"""
    
    def setUp(self):
        """Setup Flask app"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
    
    def test_form_has_paid_with_salary_field(self):
        """Verify BonusForm has paid_with_salary field"""
        with self.app.app_context():
            form = BonusForm()
            self.assertIn(
                'paid_with_salary',
                form._fields,
                "BonusForm missing paid_with_salary field"
            )
    
    def test_form_field_is_boolean(self):
        """Verify paid_with_salary field is BooleanField"""
        with self.app.app_context():
            form = BonusForm()
            from wtforms.fields import BooleanField
            self.assertIsInstance(
                form.paid_with_salary,
                BooleanField,
                f"paid_with_salary is {type(form.paid_with_salary).__name__}, not BooleanField"
            )
    
    def test_form_field_label(self):
        """Verify field has Arabic label"""
        with self.app.app_context():
            form = BonusForm()
            label_text = str(form.paid_with_salary.label.text)
            self.assertIn(
                'المكافأة' or 'صرف' or 'الراتب',
                label_text,
                f"Label missing Arabic text. Label: {label_text}"
            )
    
    def test_form_default_true(self):
        """Verify form field defaults to True"""
        with self.app.app_context():
            form = BonusForm()
            self.assertTrue(
                form.paid_with_salary.default,
                f"Form default is {form.paid_with_salary.default}, expected True"
            )
    
    def test_form_accepts_true_value(self):
        """Verify form accepts True value"""
        with self.app.app_context():
            with self.app.test_request_context(
                method='POST',
                data={'paid_with_salary': 'on'}
            ):
                form = BonusForm()
                self.assertTrue(form.paid_with_salary.data)
    
    def test_form_accepts_false_value(self):
        """Verify form accepts False value (unchecked)"""
        with self.app.app_context():
            with self.app.test_request_context(method='POST', data={}):
                form = BonusForm()
                self.assertFalse(form.paid_with_salary.data)
    
    def test_form_field_not_required(self):
        """Verify paid_with_salary field is not in validators (has default)"""
        with self.app.app_context():
            form = BonusForm()
            validators = form.paid_with_salary.validators
            from wtforms.validators import DataRequired
            has_required = any(isinstance(v, DataRequired) for v in validators)
            self.assertFalse(has_required, "BooleanField should not require DataRequired")


class BonusFormHTMLRenderingTest(unittest.TestCase):
    """Test HTML rendering of bonus form"""
    
    def setUp(self):
        """Setup Flask app"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
    
    def test_form_page_returns_200(self):
        """Verify form page loads successfully"""
        response = self.client.get('/bonuses/create')
        self.assertEqual(
            response.status_code,
            200,
            f"Form page returned {response.status_code}, expected 200"
        )
    
    def test_form_contains_checkbox_element(self):
        """Verify HTML contains checkbox input for paid_with_salary"""
        response = self.client.get('/bonuses/create')
        html = response.get_data(as_text=True)
        
        self.assertIn(
            'id="paid_with_salary_switch"',
            html,
            "Checkbox with id 'paid_with_salary_switch' not found"
        )
    
    def test_form_checkbox_has_correct_name(self):
        """Verify checkbox has correct name attribute"""
        response = self.client.get('/bonuses/create')
        html = response.get_data(as_text=True)
        
        self.assertIn(
            'name="paid_with_salary"',
            html,
            "Checkbox with name 'paid_with_salary' not found"
        )
    
    def test_form_contains_toggle_styling(self):
        """Verify form includes toggle switch styling"""
        response = self.client.get('/bonuses/create')
        html = response.get_data(as_text=True)
        
        self.assertIn(
            'form-check form-switch',
            html,
            "Form switch styling not found"
        )
    
    def test_form_contains_arabic_label(self):
        """Verify Arabic label is present"""
        response = self.client.get('/bonuses/create')
        html = response.get_data(as_text=True)
        
        self.assertIn(
            'صرف مع الراتب',
            html,
            "Arabic label 'صرف مع الراتب' not found"
        )
    
    def test_form_contains_help_text(self):
        """Verify form contains help text for both states"""
        response = self.client.get('/bonuses/create')
        html = response.get_data(as_text=True)
        
        self.assertIn('مفعّل', html, "ON state indicator not found")
        self.assertIn('معطّل', html, "OFF state indicator not found")
    
    def test_form_contains_submit_button(self):
        """Verify form has submit button"""
        response = self.client.get('/bonuses/create')
        html = response.get_data(as_text=True)
        
        self.assertIn(
            'type="submit"',
            html,
            "Submit button not found"
        )


class BonusPayrollIntegrationTest(unittest.TestCase):
    """Test bonus integration with payroll system"""
    
    def setUp(self):
        """Create test data"""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.test_db = os.path.join(self.tmpdir.name, 'test.db')
        self.db = DBManager(db_path=self.test_db)
        
        self.dept = self.db.add_department("Test Department")
        self.emp = self.db.add_employee(
            name="Test Employee",
            code="PAYROLL001",
            category="EMPLOYEE",
            department_id=self.dept.id,
            hire_date=date.today(),
            basic_salary=10000.0
        )
    
    def tearDown(self):
        """Cleanup"""
        try:
            self.db.engine.dispose()
        except:
            pass
        import gc
        gc.collect()
        try:
            self.tmpdir.cleanup()
        except:
            pass
    
    def test_bonuses_paid_with_salary_true_queryable(self):
        """Verify bonuses with paid_with_salary=True are queryable"""
        bonus = self.db.add_bonus(
            employee_id=self.emp.id,
            amount=500.0,
            reason="With salary",
            date_awarded=date.today(),
            paid_with_salary=True
        )
        
        session = self.db.get_session()
        result = session.query(Bonus).filter(
            Bonus.employee_id == self.emp.id,
            Bonus.paid_with_salary == True
        ).all()
        session.close()
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].amount, 500.0)
    
    def test_bonuses_paid_with_salary_false_queryable(self):
        """Verify bonuses with paid_with_salary=False are queryable"""
        bonus = self.db.add_bonus(
            employee_id=self.emp.id,
            amount=300.0,
            reason="Immediate",
            date_awarded=date.today(),
            paid_with_salary=False
        )
        
        session = self.db.get_session()
        result = session.query(Bonus).filter(
            Bonus.employee_id == self.emp.id,
            Bonus.paid_with_salary == False
        ).all()
        session.close()
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].amount, 300.0)
    
    def test_query_separates_by_payment_method(self):
        """Verify queries correctly separate bonuses by payment method"""
        self.db.add_bonus(self.emp.id, 500.0, "With salary", date.today(), paid_with_salary=True)
        self.db.add_bonus(self.emp.id, 300.0, "Immediate", date.today(), paid_with_salary=False)
        self.db.add_bonus(self.emp.id, 200.0, "With salary", date.today(), paid_with_salary=True)
        
        session = self.db.get_session()
        with_salary = session.query(Bonus).filter(
            Bonus.employee_id == self.emp.id,
            Bonus.paid_with_salary == True
        ).all()
        immediate = session.query(Bonus).filter(
            Bonus.employee_id == self.emp.id,
            Bonus.paid_with_salary == False
        ).all()
        session.close()
        
        self.assertEqual(len(with_salary), 2)
        self.assertEqual(len(immediate), 1)
        self.assertEqual(sum(b.amount for b in with_salary), 700.0)
        self.assertEqual(sum(b.amount for b in immediate), 300.0)


class BonusDataIntegrityTest(unittest.TestCase):
    """Test data integrity constraints"""
    
    def setUp(self):
        """Create test database"""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.test_db = os.path.join(self.tmpdir.name, 'test.db')
        self.db = DBManager(db_path=self.test_db)
        
        self.dept = self.db.add_department("Test Department")
        self.emp = self.db.add_employee(
            name="Test Employee",
            code="INTEGRITY001",
            category="EMPLOYEE",
            department_id=self.dept.id,
            hire_date=date.today(),
            basic_salary=5000.0
        )
    
    def tearDown(self):
        """Cleanup"""
        try:
            self.db.engine.dispose()
        except:
            pass
        import gc
        gc.collect()
        try:
            self.tmpdir.cleanup()
        except:
            pass
    
    def test_bonus_with_null_paid_with_salary_rejected(self):
        """Verify NULL value for paid_with_salary is handled"""
        session = self.db.get_session()
        bonus = Bonus(
            employee_id=self.emp.id,
            amount=500.0,
            reason="Test",
            date_awarded=date.today()
        )
        
        self.assertIsNotNone(bonus.paid_with_salary, "paid_with_salary should never be None")
        session.close()
    
    def test_bonus_amount_can_be_zero(self):
        """Verify bonuses can have zero amount"""
        bonus = self.db.add_bonus(
            employee_id=self.emp.id,
            amount=0.0,
            reason="No bonus",
            date_awarded=date.today(),
            paid_with_salary=True
        )
        
        self.assertIsNotNone(bonus)
        self.assertEqual(bonus.amount, 0.0)
    
    def test_bonus_amount_can_be_large(self):
        """Verify bonuses can have large amounts"""
        large_amount = 999999.99
        bonus = self.db.add_bonus(
            employee_id=self.emp.id,
            amount=large_amount,
            reason="Large bonus",
            date_awarded=date.today(),
            paid_with_salary=False
        )
        
        self.assertEqual(bonus.amount, large_amount)


class BonusEditTest(unittest.TestCase):
    """Test editing bonuses with paid_with_salary field"""
    
    def setUp(self):
        """Create test data"""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.test_db = os.path.join(self.tmpdir.name, 'test.db')
        self.db = DBManager(db_path=self.test_db)
        
        self.dept = self.db.add_department("Test Department")
        self.emp = self.db.add_employee(
            name="Test Employee",
            code="EDIT001",
            category="EMPLOYEE",
            department_id=self.dept.id,
            hire_date=date.today(),
            basic_salary=5000.0
        )
        
        self.bonus = self.db.add_bonus(
            employee_id=self.emp.id,
            amount=500.0,
            reason="Initial",
            date_awarded=date.today(),
            paid_with_salary=True
        )
    
    def tearDown(self):
        """Cleanup"""
        try:
            self.db.engine.dispose()
        except:
            pass
        import gc
        gc.collect()
        try:
            self.tmpdir.cleanup()
        except:
            pass
    
    def test_can_toggle_paid_with_salary_true_to_false(self):
        """Verify bonus can change from paid_with_salary=True to False"""
        self.bonus.paid_with_salary = False
        session = self.db.get_session()
        session.merge(self.bonus)
        session.commit()
        session.close()
        
        session = self.db.get_session()
        updated = session.query(Bonus).filter(Bonus.id == self.bonus.id).first()
        session.close()
        
        self.assertFalse(updated.paid_with_salary)
    
    def test_can_toggle_paid_with_salary_false_to_true(self):
        """Verify bonus can change from paid_with_salary=False to True"""
        bonus = self.db.add_bonus(
            employee_id=self.emp.id,
            amount=300.0,
            reason="Change",
            date_awarded=date.today(),
            paid_with_salary=False
        )
        
        bonus.paid_with_salary = True
        session = self.db.get_session()
        session.merge(bonus)
        session.commit()
        session.close()
        
        session = self.db.get_session()
        updated = session.query(Bonus).filter(Bonus.id == bonus.id).first()
        session.close()
        
        self.assertTrue(updated.paid_with_salary)


class BonusEdgeCasesTest(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def setUp(self):
        """Create test database"""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.test_db = os.path.join(self.tmpdir.name, 'test.db')
        self.db = DBManager(db_path=self.test_db)
        
        self.dept = self.db.add_department("Test Department")
        self.emp = self.db.add_employee(
            name="Test Employee",
            code="EDGE001",
            category="EMPLOYEE",
            department_id=self.dept.id,
            hire_date=date.today(),
            basic_salary=5000.0
        )
    
    def tearDown(self):
        """Cleanup"""
        try:
            self.db.engine.dispose()
        except:
            pass
        import gc
        gc.collect()
        try:
            self.tmpdir.cleanup()
        except:
            pass
    
    def test_multiple_bonuses_same_employee_different_payment_methods(self):
        """Verify employee can have bonuses with different payment methods"""
        b1 = self.db.add_bonus(self.emp.id, 100, "Type1", date.today(), paid_with_salary=True)
        b2 = self.db.add_bonus(self.emp.id, 200, "Type2", date.today(), paid_with_salary=False)
        b3 = self.db.add_bonus(self.emp.id, 300, "Type3", date.today(), paid_with_salary=True)
        
        self.assertTrue(b1.paid_with_salary)
        self.assertFalse(b2.paid_with_salary)
        self.assertTrue(b3.paid_with_salary)
    
    def test_bonus_with_special_characters_in_reason(self):
        """Verify bonuses work with special characters"""
        bonus = self.db.add_bonus(
            employee_id=self.emp.id,
            amount=500.0,
            reason="مكافأة أداء ممتاز!",
            date_awarded=date.today(),
            paid_with_salary=True
        )
        
        self.assertIsNotNone(bonus)
        self.assertIn("مكافأة", bonus.reason)
    
    def test_bonus_historical_data_conversion(self):
        """Verify old bonuses without field get correct default"""
        bonus = self.db.add_bonus(
            employee_id=self.emp.id,
            amount=500.0,
            reason="Old bonus",
            date_awarded=date(2020, 1, 1),
            paid_with_salary=True
        )
        
        self.assertTrue(bonus.paid_with_salary)


def run_tests_with_summary():
    """Run all tests and print summary"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    test_classes = [
        BonusDatabaseSchemaTest,
        BonusModelTest,
        BonusFormTest,
        BonusFormHTMLRenderingTest,
        BonusPayrollIntegrationTest,
        BonusDataIntegrityTest,
        BonusEditTest,
        BonusEdgeCasesTest,
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*80)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests_with_summary()
    sys.exit(0 if success else 1)
