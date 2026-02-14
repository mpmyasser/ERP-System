#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Integration tests for Bonus System - paid_with_salary field
Tests form rendering, submission, and database integration
"""

import sys
import os
import io
import tempfile
from datetime import date

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'core')

from app import create_app
from app.forms import BonusForm
from core.db_manager import DBManager
from core.database_models import Bonus, Employee, Department

def test_bonus_form_field_exists():
    """Test 1: Verify paid_with_salary field exists in BonusForm"""
    print("\n" + "="*80)
    print("TEST 1: Bonus Form Field Existence")
    print("="*80)
    
    app = create_app()
    with app.app_context():
        form = BonusForm()
        
        if 'paid_with_salary' in form._fields:
            field = form.paid_with_salary
            print("✅ PASS: paid_with_salary field exists")
            print(f"   Field type: {type(field).__name__}")
            print(f"   Label: {field.label.text}")
            print(f"   Default value: {field.default}")
            return True
        else:
            print("❌ FAIL: paid_with_salary field not found")
            print(f"   Available fields: {list(form._fields.keys())}")
            return False


def test_bonus_form_default_value():
    """Test 2: Verify default value is True (paid with salary)"""
    print("\n" + "="*80)
    print("TEST 2: Bonus Form Default Value")
    print("="*80)
    
    app = create_app()
    with app.app_context():
        form = BonusForm()
        
        if form.paid_with_salary.default == True:
            print("✅ PASS: Default value is True")
            print(f"   Default value: {form.paid_with_salary.default}")
            return True
        else:
            print("❌ FAIL: Default value is not True")
            print(f"   Actual value: {form.paid_with_salary.default}")
            return False


def test_bonus_form_submission_with_paid_with_salary_true():
    """Test 3: Submit form with paid_with_salary = True"""
    print("\n" + "="*80)
    print("TEST 3: Form Submission - paid_with_salary = True")
    print("="*80)
    
    # Create test database
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = os.path.join(tmpdir, 'test.db')
        db = DBManager(db_path=test_db)
        
        # Create test department and employee
        dept = db.add_department("Test Department")
        emp = db.add_employee(
            name="Test Employee",
            code="TST001",
            category="EMPLOYEE",
            department_id=dept.id,
            hire_date=date.today(),
            basic_salary=5000.0
        )
        
        app = create_app()
        with app.app_context():
            with app.test_request_context(method='POST', data={
                'employee_id': str(emp.id),
                'amount': '1000',
                'reason': 'Test bonus',
                'date_awarded': date.today().strftime('%d/%m/%Y'),
                'paid_with_salary': 'on'  # Checkbox is 'on' when checked
            }):
                form = BonusForm()
                
                if form.validate():
                    bonus = db.add_bonus(
                        employee_id=form.employee_id.data,
                        amount=form.amount.data,
                        reason=form.reason.data,
                        date_awarded=form.date_awarded.data,
                        paid_with_salary=form.paid_with_salary.data
                    )
                    
                    if bonus and bonus.paid_with_salary == True:
                        print("✅ PASS: Bonus saved with paid_with_salary = True")
                        print(f"   Bonus ID: {bonus.id}")
                        print(f"   Amount: {bonus.amount}")
                        print(f"   paid_with_salary: {bonus.paid_with_salary}")
                        return True
                    else:
                        print("❌ FAIL: Bonus not saved correctly")
                        return False
                else:
                    print("❌ FAIL: Form validation failed")
                    print(f"   Errors: {form.errors}")
                    return False


def test_bonus_form_submission_with_paid_with_salary_false():
    """Test 4: Submit form with paid_with_salary = False"""
    print("\n" + "="*80)
    print("TEST 4: Form Submission - paid_with_salary = False")
    print("="*80)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = os.path.join(tmpdir, 'test.db')
        db = DBManager(db_path=test_db)
        
        dept = db.add_department("Test Department")
        emp = db.add_employee(
            name="Test Employee",
            code="TST002",
            category="EMPLOYEE",
            department_id=dept.id,
            hire_date=date.today(),
            basic_salary=5000.0
        )
        
        app = create_app()
        with app.app_context():
            with app.test_request_context(method='POST', data={
                'employee_id': str(emp.id),
                'amount': '500',
                'reason': 'Immediate payment',
                'date_awarded': date.today().strftime('%d/%m/%Y'),
                # Note: NOT including paid_with_salary in data (unchecked checkbox)
            }):
                form = BonusForm()
                
                if form.validate():
                    bonus = db.add_bonus(
                        employee_id=form.employee_id.data,
                        amount=form.amount.data,
                        reason=form.reason.data,
                        date_awarded=form.date_awarded.data,
                        paid_with_salary=form.paid_with_salary.data
                    )
                    
                    if bonus and bonus.paid_with_salary == False:
                        print("✅ PASS: Bonus saved with paid_with_salary = False")
                        print(f"   Bonus ID: {bonus.id}")
                        print(f"   Amount: {bonus.amount}")
                        print(f"   paid_with_salary: {bonus.paid_with_salary}")
                        return True
                    else:
                        print("❌ FAIL: Bonus not saved with correct value")
                        print(f"   Expected: False, Got: {bonus.paid_with_salary if bonus else 'None'}")
                        return False
                else:
                    print("❌ FAIL: Form validation failed")
                    return False


def test_bonus_route_displays_form():
    """Test 5: Route displays form with toggle switch"""
    print("\n" + "="*80)
    print("TEST 5: Bonus Form Route - HTML Rendering")
    print("="*80)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = os.path.join(tmpdir, 'test.db')
        db = DBManager(db_path=test_db)
        
        dept = db.add_department("Test Department")
        db.add_employee(
            name="Test Employee",
            code="TST003",
            category="EMPLOYEE",
            department_id=dept.id,
            hire_date=date.today(),
            basic_salary=5000.0
        )
        
        app = create_app()
        with app.test_client() as client:
            response = client.get('/bonuses/create')
            html_content = response.get_data(as_text=True)
            
            # Check for toggle switch HTML
            checks = [
                ('paid_with_salary_switch' in html_content, "Toggle switch ID found"),
                ('form-check-input' in html_content, "Form-check-input class found"),
                ('صرف مع الراتب' in html_content or 'payment' in html_content.lower(), "Payment label found"),
                ('form-check form-switch' in html_content, "Form-switch class found"),
            ]
            
            all_passed = True
            for check, description in checks:
                if check:
                    print(f"   ✅ {description}")
                else:
                    print(f"   ❌ {description}")
                    all_passed = False
            
            if all_passed:
                print("\n✅ PASS: Form HTML contains toggle switch")
                return True
            else:
                print("\n❌ FAIL: Form HTML missing toggle switch elements")
                return False


def test_bonus_payroll_integration():
    """Test 6: Verify payroll processor uses paid_with_salary flag"""
    print("\n" + "="*80)
    print("TEST 6: Payroll Integration with paid_with_salary")
    print("="*80)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = os.path.join(tmpdir, 'test.db')
        db = DBManager(db_path=test_db)
        
        dept = db.add_department("Test Department")
        emp = db.add_employee(
            name="Test Employee",
            code="TST004",
            category="EMPLOYEE",
            department_id=dept.id,
            hire_date=date.today(),
            basic_salary=5000.0
        )
        
        # Add two bonuses: one with salary, one paid previously
        bonus1 = db.add_bonus(emp.id, 500.0, "With salary", date.today(), paid_with_salary=True)
        bonus2 = db.add_bonus(emp.id, 300.0, "Paid previously", date.today(), paid_with_salary=False)
        
        # Query bonuses with paid_with_salary = False (should get only bonus2)
        session = db.get_session()
        from core.database_models import Bonus as BonusModel
        paid_bonuses = session.query(BonusModel).filter(
            BonusModel.employee_id == emp.id,
            BonusModel.paid_with_salary == False
        ).all()
        session.close()
        
        if len(paid_bonuses) == 1 and paid_bonuses[0].amount == 300.0:
            print("✅ PASS: Payroll can correctly query paid_with_salary = False bonuses")
            print(f"   Found {len(paid_bonuses)} bonus(es) with paid_with_salary = False")
            print(f"   Bonus amount: {paid_bonuses[0].amount}")
            return True
        else:
            print("❌ FAIL: Payroll query returned unexpected results")
            print(f"   Found {len(paid_bonuses)} bonus(es), expected 1")
            return False


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*80)
    print("BONUS SYSTEM INTEGRATION TESTS")
    print("="*80)
    
    tests = [
        test_bonus_form_field_exists,
        test_bonus_form_default_value,
        test_bonus_form_submission_with_paid_with_salary_true,
        test_bonus_form_submission_with_paid_with_salary_false,
        test_bonus_route_displays_form,
        test_bonus_payroll_integration,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
        return True
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
