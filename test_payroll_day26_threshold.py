#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit Tests for Payroll Day 26 Threshold Logic
Tests the new calculation logic that determines salary calculation based on extraction date:
- Before day 26: (Actual Days × Daily Salary) + Additions - Deductions
- From day 26 onwards: Basic Salary + Additions - Deductions

Also tests:
- Calculation Type field tracking
- Actual Days field tracking
- Terminated employee handling
- Prorated employee handling
- Absence deduction logic for different employee types
"""

import sys
import os
import io
import unittest
import tempfile
from datetime import date, datetime, timedelta
from unittest.mock import patch

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from app import create_app
from core.db_manager import DBManager
from core.database_models import Employee, DailyRecord, Department
from core.services.payroll_processor import PayrollCalculator


class PayrollDay26ThresholdTestSetup(unittest.TestCase):
    """Base test setup for day 26 threshold tests"""
    
    def setUp(self):
        """Create test database and sample employee"""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.test_db = os.path.join(self.tmpdir.name, 'test.db')
        self.db = DBManager(db_path=self.test_db)
        
        dept = Department(id=1, name='Test Department')
        session = self.db.get_session()
        session.add(dept)
        session.commit()
        
        self.employee = Employee(
            id=1,
            code='EMP001',
            name='أحمد محمد',
            basic_salary=3000.0,
            category='EMPLOYEE',
            daily_work_hours=8.0,
            department_id=1,
            is_active=True,
            incentive_allowance=100.0,
            regularity_incentive=200.0,
            transport_allowance=50.0
        )
        session.add(self.employee)
        session.commit()
        session.close()
        
        self.calculator = PayrollCalculator(self.db)
    
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
    
    def _create_daily_records(self, employee_id, month, year, num_days=20, status='حاضر'):
        """Helper to create daily records for testing"""
        session = self.db.get_session()
        start_date, end_date = self.calculator.get_salary_month_date_range(month, year)
        
        for i in range(num_days):
            record_date = start_date + timedelta(days=i)
            if record_date <= end_date:
                record = DailyRecord(
                    employee_id=employee_id,
                    date=record_date,
                    check_in=None,
                    check_out=None,
                    late_minutes=0,
                    early_leave_minutes=0,
                    overtime_hours=0.0,
                    status=status,
                    manual_adjustment=0.0
                )
                session.add(record)
        session.commit()
        session.close()


class PayrollCalculationTypeTest(PayrollDay26ThresholdTestSetup):
    """Test Calculation Type field tracking"""
    
    def test_calculation_type_before_day26(self):
        """Test calculation type is 'أيام فعلية' before day 26"""
        self._create_daily_records(1, 1, 2025, num_days=20)
        
        with patch('core.services.payroll_processor.date') as mock_date_class:
            mock_date_class.today.return_value = date(2025, 1, 20)
            mock_date_class.side_effect = lambda *args, **kw: date(*args, **kw)
            result = self.calculator.calculate_monthly_payroll(1, 1, 2025)
        
        self.assertEqual(result['Calculation Type'], 'أيام فعلية')
    
    def test_calculation_type_on_day26(self):
        """Test calculation type is 'نهاية شهر' on day 26 onwards"""
        self._create_daily_records(1, 1, 2025, num_days=20)
        
        with patch('core.services.payroll_processor.date') as mock_date_class:
            mock_date_class.today.return_value = date(2025, 1, 26)
            mock_date_class.side_effect = lambda *args, **kw: date(*args, **kw)
            result = self.calculator.calculate_monthly_payroll(1, 1, 2025)
        
        self.assertEqual(result['Calculation Type'], 'نهاية شهر')
    
    def test_calculation_type_after_day26(self):
        """Test calculation type is 'نهاية شهر' after day 26"""
        self._create_daily_records(1, 1, 2025, num_days=20)
        
        with patch('core.services.payroll_processor.date') as mock_date_class:
            mock_date_class.today.return_value = date(2025, 1, 31)
            mock_date_class.side_effect = lambda *args, **kw: date(*args, **kw)
            result = self.calculator.calculate_monthly_payroll(1, 1, 2025)
        
        self.assertEqual(result['Calculation Type'], 'نهاية شهر')


class PayrollActualDaysFieldTest(PayrollDay26ThresholdTestSetup):
    """Test Actual Days field tracking"""
    
    def test_actual_days_field_present(self):
        """Test that Actual Days field is present in result"""
        self._create_daily_records(1, 1, 2025, num_days=15)
        result = self.calculator.calculate_monthly_payroll(1, 1, 2025)
        
        self.assertIn('Actual Days', result)
        self.assertEqual(result['Actual Days'], 15)
    
    def test_actual_days_equals_attendance_days(self):
        """Test that Actual Days equals Attendance Days"""
        self._create_daily_records(1, 1, 2025, num_days=18)
        result = self.calculator.calculate_monthly_payroll(1, 1, 2025)
        
        self.assertEqual(result['Actual Days'], result['Attendance Days'])


class PayrollGrossSalaryCalculationTest(PayrollDay26ThresholdTestSetup):
    """Test gross salary calculation based on day 26 threshold"""
    
    def test_gross_salary_before_day26_uses_actual_days(self):
        """Before day 26: gross = attendance_days × daily_salary"""
        self._create_daily_records(1, 1, 2025, num_days=20)
        
        with patch('core.services.payroll_processor.date') as mock_date_class:
            mock_date_class.today.return_value = date(2025, 1, 20)
            mock_date_class.side_effect = lambda *args, **kw: date(*args, **kw)
            result = self.calculator.calculate_monthly_payroll(1, 1, 2025)
        
        expected_gross = 20 * 100.0
        self.assertAlmostEqual(result['Gross Salary'], expected_gross, places=2)
    
    def test_gross_salary_on_day26_uses_basic_salary(self):
        """On/after day 26: gross = basic_salary"""
        self._create_daily_records(1, 1, 2025, num_days=20)
        
        with patch('core.services.payroll_processor.date') as mock_date_class:
            mock_date_class.today.return_value = date(2025, 1, 26)
            mock_date_class.side_effect = lambda *args, **kw: date(*args, **kw)
            result = self.calculator.calculate_monthly_payroll(1, 1, 2025)
        
        self.assertAlmostEqual(result['Gross Salary'], 3000.0, places=2)
    
    def test_gross_salary_different_attendance_days(self):
        """Verify calculation with different attendance day counts"""
        self._create_daily_records(1, 1, 2025, num_days=25)
        
        with patch('core.services.payroll_processor.date') as mock_date_class:
            mock_date_class.today.return_value = date(2025, 1, 20)
            mock_date_class.side_effect = lambda *args, **kw: date(*args, **kw)
            result = self.calculator.calculate_monthly_payroll(1, 1, 2025)
        
        expected_gross = 25 * 100.0
        self.assertAlmostEqual(result['Gross Salary'], expected_gross, places=2)


class PayrollTerminatedEmployeeTest(PayrollDay26ThresholdTestSetup):
    """Test terminated employee handling"""
    
    def test_terminated_employee_uses_actual_days(self):
        """Terminated employees always use actual days regardless of day 26"""
        session = self.db.get_session()
        emp = session.query(Employee).filter_by(id=1).first()
        emp.exit_date = date(2025, 1, 15)
        session.commit()
        session.close()
        
        self._create_daily_records(1, 1, 2025, num_days=12)
        
        with patch('core.services.payroll_processor.date') as mock_date_class:
            mock_date_class.today.return_value = date(2025, 1, 26)
            mock_date_class.side_effect = lambda *args, **kw: date(*args, **kw)
            result = self.calculator.calculate_monthly_payroll(1, 1, 2025)
        
        expected_gross = 12 * 100.0
        self.assertAlmostEqual(result['Gross Salary'], expected_gross, places=2)
    
    def test_terminated_employee_absence_deduction_not_applied(self):
        """Terminated employees should not have absence deductions"""
        session = self.db.get_session()
        emp = session.query(Employee).filter_by(id=1).first()
        emp.exit_date = date(2025, 1, 15)
        session.commit()
        session.close()
        
        self._create_daily_records(1, 1, 2025, num_days=12)
        
        with patch('core.services.payroll_processor.date') as mock_date_class:
            mock_date_class.today.return_value = date(2025, 1, 20)
            mock_date_class.side_effect = lambda *args, **kw: date(*args, **kw)
            result = self.calculator.calculate_monthly_payroll(1, 1, 2025)
        
        self.assertEqual(result['Absence Deduction'], 0.0)


class PayrollProratedEmployeeTest(PayrollDay26ThresholdTestSetup):
    """Test prorated (new hire or mid-month change) employee handling"""
    
    def test_prorated_employee_uses_actual_days(self):
        """Prorated employees always use actual days regardless of day 26"""
        session = self.db.get_session()
        emp = session.query(Employee).filter_by(id=1).first()
        emp.disruption_date = date(2025, 1, 15)
        session.commit()
        session.close()
        
        self._create_daily_records(1, 1, 2025, num_days=20)
        
        with patch('core.services.payroll_processor.date') as mock_date_class:
            mock_date_class.today.return_value = date(2025, 1, 26)
            mock_date_class.side_effect = lambda *args, **kw: date(*args, **kw)
            result = self.calculator.calculate_monthly_payroll(1, 1, 2025)
        
        self.assertTrue(result['Is Prorated'])
    
    def test_prorated_employee_absence_deduction_not_applied(self):
        """Prorated employees should not have absence deductions"""
        session = self.db.get_session()
        emp = session.query(Employee).filter_by(id=1).first()
        emp.disruption_date = date(2025, 1, 15)
        session.commit()
        session.close()
        
        self._create_daily_records(1, 1, 2025, num_days=10)
        
        with patch('core.services.payroll_processor.date') as mock_date_class:
            mock_date_class.today.return_value = date(2025, 1, 20)
            mock_date_class.side_effect = lambda *args, **kw: date(*args, **kw)
            result = self.calculator.calculate_monthly_payroll(1, 1, 2025)
        
        self.assertEqual(result['Absence Deduction'], 0.0)


class PayrollAbsenceDeductionTest(PayrollDay26ThresholdTestSetup):
    """Test absence deduction handling for different scenarios"""
    
    def test_absence_deduction_normal_employee_before_day26(self):
        """Normal employee before day 26 should have absence deduction"""
        session = self.db.get_session()
        start_date, end_date = self.calculator.get_salary_month_date_range(1, 2025)
        
        for i in range(20):
            record_date = start_date + timedelta(days=i)
            status = 'غائب' if i < 3 else 'حاضر'
            record = DailyRecord(
                employee_id=1,
                date=record_date,
                status=status,
                late_minutes=0,
                early_leave_minutes=0,
                overtime_hours=0.0
            )
            session.add(record)
        session.commit()
        session.close()
        
        with patch('core.services.payroll_processor.date') as mock_date_class:
            mock_date_class.today.return_value = date(2025, 1, 20)
            mock_date_class.side_effect = lambda *args, **kw: date(*args, **kw)
            result = self.calculator.calculate_monthly_payroll(1, 1, 2025)
        
        self.assertGreater(result['Absence Deduction'], 0.0)
    
    def test_absence_deduction_normal_employee_on_day26(self):
        """Normal employee on/after day 26 should have absence deduction"""
        session = self.db.get_session()
        start_date, end_date = self.calculator.get_salary_month_date_range(1, 2025)
        
        for i in range(20):
            record_date = start_date + timedelta(days=i)
            status = 'غائب' if i < 2 else 'حاضر'
            record = DailyRecord(
                employee_id=1,
                date=record_date,
                status=status,
                late_minutes=0,
                early_leave_minutes=0,
                overtime_hours=0.0
            )
            session.add(record)
        session.commit()
        session.close()
        
        with patch('core.services.payroll_processor.date') as mock_date_class:
            mock_date_class.today.return_value = date(2025, 1, 26)
            mock_date_class.side_effect = lambda *args, **kw: date(*args, **kw)
            result = self.calculator.calculate_monthly_payroll(1, 1, 2025)
        
        self.assertGreater(result['Absence Deduction'], 0.0)


class PayrollNetSalaryCalculationTest(PayrollDay26ThresholdTestSetup):
    """Test net salary calculation with new logic"""
    
    def test_net_salary_calculation_before_day26(self):
        """Net = (Actual Days × Daily Salary) + Additions - Deductions"""
        self._create_daily_records(1, 1, 2025, num_days=20)
        
        with patch('core.services.payroll_processor.date') as mock_date_class:
            mock_date_class.today.return_value = date(2025, 1, 20)
            mock_date_class.side_effect = lambda *args, **kw: date(*args, **kw)
            result = self.calculator.calculate_monthly_payroll(1, 1, 2025)
        
        expected = (20 * 100.0) + result['Total Additions'] - result['Total Deductions']
        self.assertAlmostEqual(result['Net Salary'], expected, places=2)
    
    def test_net_salary_calculation_on_day26(self):
        """Net = Basic Salary + Additions - Deductions"""
        self._create_daily_records(1, 1, 2025, num_days=20)
        
        with patch('core.services.payroll_processor.date') as mock_date_class:
            mock_date_class.today.return_value = date(2025, 1, 26)
            mock_date_class.side_effect = lambda *args, **kw: date(*args, **kw)
            result = self.calculator.calculate_monthly_payroll(1, 1, 2025)
        
        expected = 3000.0 + result['Total Additions'] - result['Total Deductions']
        self.assertAlmostEqual(result['Net Salary'], expected, places=2)


class PayrollMonthBoundaryTest(PayrollDay26ThresholdTestSetup):
    """Test payroll calculation at month boundaries"""
    
    def test_salary_month_date_range_regular_month(self):
        """Test date range for regular month (e.g., February)"""
        start, end = self.calculator.get_salary_month_date_range(2, 2025)
        
        self.assertEqual(start, date(2025, 1, 26))
        self.assertEqual(end, date(2025, 2, 25))
    
    def test_salary_month_date_range_january(self):
        """Test date range for January (wraps to previous year)"""
        start, end = self.calculator.get_salary_month_date_range(1, 2025)
        
        self.assertEqual(start, date(2024, 12, 26))
        self.assertEqual(end, date(2025, 1, 25))
    
    def test_salary_month_date_range_december(self):
        """Test date range for December"""
        start, end = self.calculator.get_salary_month_date_range(12, 2025)
        
        self.assertEqual(start, date(2025, 11, 26))
        self.assertEqual(end, date(2025, 12, 25))


class PayrollResultStructureTest(PayrollDay26ThresholdTestSetup):
    """Test that payroll result contains all required fields"""
    
    def test_result_contains_calculation_type(self):
        """Test result dictionary contains Calculation Type field"""
        self._create_daily_records(1, 1, 2025, num_days=20)
        result = self.calculator.calculate_monthly_payroll(1, 1, 2025)
        
        self.assertIn('Calculation Type', result)
        self.assertIn(result['Calculation Type'], ['نهاية شهر', 'أيام فعلية'])
    
    def test_result_contains_actual_days(self):
        """Test result dictionary contains Actual Days field"""
        self._create_daily_records(1, 1, 2025, num_days=20)
        result = self.calculator.calculate_monthly_payroll(1, 1, 2025)
        
        self.assertIn('Actual Days', result)
        self.assertIsInstance(result['Actual Days'], (int, float))
    
    def test_result_contains_required_fields(self):
        """Test result contains all payroll calculation fields"""
        self._create_daily_records(1, 1, 2025, num_days=20)
        result = self.calculator.calculate_monthly_payroll(1, 1, 2025)
        
        required_fields = [
            'Employee', 'Employee ID', 'Month', 'Year',
            'Basic Salary', 'Gross Salary', 'Net Salary',
            'Total Additions', 'Total Deductions',
            'Calculation Type', 'Actual Days', 'Is Prorated'
        ]
        
        for field in required_fields:
            self.assertIn(field, result, f"Missing required field: {field}")


class PayrollErrorHandlingTest(PayrollDay26ThresholdTestSetup):
    """Test error handling and edge cases"""
    
    def test_employee_not_found(self):
        """Test calculation with non-existent employee"""
        with self.assertRaises(ValueError):
            self.calculator.calculate_monthly_payroll(999, 1, 2025)
    
    def test_calculation_with_no_daily_records(self):
        """Test calculation when employee has no daily records"""
        result = self.calculator.calculate_monthly_payroll(1, 1, 2025)
        
        self.assertIn('Gross Salary', result)
        self.assertIn('Net Salary', result)


class PayrollAdditionsInclusionTest(PayrollDay26ThresholdTestSetup):
    """Test that additions are included regardless of calculation type"""
    
    def test_additions_included_before_day26(self):
        """Additions should be included in calculation before day 26"""
        self._create_daily_records(1, 1, 2025, num_days=20)
        
        with patch('core.services.payroll_processor.date') as mock_date_class:
            mock_date_class.today.return_value = date(2025, 1, 20)
            mock_date_class.side_effect = lambda *args, **kw: date(*args, **kw)
            result = self.calculator.calculate_monthly_payroll(1, 1, 2025)
        
        self.assertGreater(result['Total Additions'], 0.0)
    
    def test_additions_included_on_day26(self):
        """Additions should be included in calculation on/after day 26"""
        self._create_daily_records(1, 1, 2025, num_days=20)
        
        with patch('core.services.payroll_processor.date') as mock_date_class:
            mock_date_class.today.return_value = date(2025, 1, 26)
            mock_date_class.side_effect = lambda *args, **kw: date(*args, **kw)
            result = self.calculator.calculate_monthly_payroll(1, 1, 2025)
        
        self.assertGreater(result['Total Additions'], 0.0)


def run_tests():
    """Run all test cases"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    test_classes = [
        PayrollCalculationTypeTest,
        PayrollActualDaysFieldTest,
        PayrollGrossSalaryCalculationTest,
        PayrollTerminatedEmployeeTest,
        PayrollProratedEmployeeTest,
        PayrollAbsenceDeductionTest,
        PayrollNetSalaryCalculationTest,
        PayrollMonthBoundaryTest,
        PayrollResultStructureTest,
        PayrollErrorHandlingTest,
        PayrollAdditionsInclusionTest,
    ]
    
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
