import unittest
import sys
import os
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from core.db_manager import DBManager
from core.treasury_models import CashAccount, BankAccount
from core.accounting_models import Account
from core.database_models import Employee
from core.auth_models import User
from app import create_app


class CashAccountButtonsTest(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.app.config['WTF_CSRF_ENABLED'] = False
        cls.db = DBManager()
        cls.test_account_id = None
        cls.test_user_id = None
        cls.test_general_id = None
        cls.test_subsidiary_id = None
    
    @classmethod
    def tearDownClass(cls):
        pass
    
    def setUp(self):
        self.session = self.db.get_session()
        self.client = self.app.test_client()
    
    def tearDown(self):
        if self.session:
            self.session.close()
    
    def test_01_create_test_data(self):
        """Test 1: Create test data"""
        print("\n[TEST 1] Create test data")
        
        try:
            import random
            unique_id = random.randint(100000, 999999)
            acc = Account(
                code=f'9999-BTN-{unique_id}',
                name='Test - Cash Account Buttons',
                type='Cash',
                is_active=1
            )
            self.session.add(acc)
            self.session.flush()
            self.__class__.test_account_id = acc.id
            
            import random
            user = User(
                username=f'test_buttons_{random.randint(10000, 99999)}',
                full_name='Test Buttons',
                is_active=True,
                is_admin=True
            )
            user.set_password('test123')
            self.session.add(user)
            self.session.flush()
            self.__class__.test_user_id = user.id
            
            general = CashAccount(
                name='General Cash - Button Test',
                account_id=self.test_account_id,
                type='General',
                parent_cash_id=None,
                user_id=self.test_user_id,
                is_active=True,
                display_order=1
            )
            self.session.add(general)
            self.session.flush()
            self.__class__.test_general_id = general.id
            
            subsidiary = CashAccount(
                name='Subsidiary Cash - Button Test',
                account_id=self.test_account_id,
                type='Subsidiary',
                parent_cash_id=self.test_general_id,
                user_id=self.test_user_id,
                is_active=True,
                display_order=2
            )
            self.session.add(subsidiary)
            self.session.flush()
            self.__class__.test_subsidiary_id = subsidiary.id
            
            self.session.commit()
            print(f"   PASS: Test data created")
            print(f"   - General ID: {self.test_general_id}")
            print(f"   - Subsidiary ID: {self.test_subsidiary_id}")
            
        except Exception as e:
            print(f"   FAIL: {e}")
            self.session.rollback()
            raise
    
    def test_02_dashboard_has_buttons(self):
        """Test 2: Dashboard has cash account buttons"""
        print("\n[TEST 2] Dashboard has buttons")
        
        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = self.test_user_id
                sess['is_admin'] = True
            
            response = client.get('/treasury/dashboard')
            self.assertEqual(response.status_code, 200)
            
            html_content = response.data.decode('utf-8')
            buttons = re.findall(r'class="btn[^"]*"', html_content)
            
            self.assertGreater(len(buttons), 0, "Should have buttons")
            print(f"   PASS: Found {len(buttons)} buttons")
    
    def test_03_general_account_transfer_button(self):
        """Test 3: General account has transfer button"""
        print("\n[TEST 3] General account transfer button")
        
        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = self.test_user_id
                sess['is_admin'] = True
            
            response = client.get('/treasury/dashboard')
            self.assertEqual(response.status_code, 200)
            
            html_content = response.data.decode('utf-8')
            transfer_links = re.findall(r'href="([^"]*transfer[^"]*from_account=[^"]*)"', html_content)
            
            self.assertGreater(len(transfer_links), 0, "Should have transfer button")
            print(f"   PASS: Found {len(transfer_links)} transfer links")
    
    def test_04_subsidiary_receive_button(self):
        """Test 4: Subsidiary account has receive button"""
        print("\n[TEST 4] Subsidiary account receive button")
        
        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = self.test_user_id
                sess['is_admin'] = True
            
            response = client.get('/treasury/dashboard')
            self.assertEqual(response.status_code, 200)
            
            html_content = response.data.decode('utf-8')
            receive_links = re.findall(r'href="([^"]*transfers/receive[^"]*)"', html_content)
            
            self.assertGreater(len(receive_links), 0, "Should have receive button")
            print(f"   PASS: Found {len(receive_links)} receive links")
    
    def test_05_receipt_button_with_cash_id(self):
        """Test 5: Receipt button passes cash_id"""
        print("\n[TEST 5] Receipt button with cash_id")
        
        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = self.test_user_id
                sess['is_admin'] = True
            
            response = client.get('/treasury/dashboard')
            self.assertEqual(response.status_code, 200)
            
            html_content = response.data.decode('utf-8')
            receipt_links = re.findall(r'href="([^"]*vouchers/new/receipt[^"]*cash_id=[^"]*)"', html_content)
            
            self.assertGreater(len(receipt_links), 0, "Should have receipt button")
            print(f"   PASS: Found {len(receipt_links)} receipt links")
    
    def test_06_payment_button_with_cash_id(self):
        """Test 6: Payment button passes cash_id"""
        print("\n[TEST 6] Payment button with cash_id")
        
        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = self.test_user_id
                sess['is_admin'] = True
            
            response = client.get('/treasury/dashboard')
            self.assertEqual(response.status_code, 200)
            
            html_content = response.data.decode('utf-8')
            payment_links = re.findall(r'href="([^"]*vouchers/new/payment[^"]*cash_id=[^"]*)"', html_content)
            
            self.assertGreater(len(payment_links), 0, "Should have payment button")
            print(f"   PASS: Found {len(payment_links)} payment links")
    
    def test_07_edit_button(self):
        """Test 7: Edit button exists"""
        print("\n[TEST 7] Edit button exists")
        
        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = self.test_user_id
                sess['is_admin'] = True
            
            response = client.get('/treasury/dashboard')
            self.assertEqual(response.status_code, 200)
            
            html_content = response.data.decode('utf-8')
            edit_buttons = re.findall(r'data-bs-target="#editCashModal', html_content)
            
            self.assertGreater(len(edit_buttons), 0, "Should have edit buttons")
            print(f"   PASS: Found {len(edit_buttons)} edit buttons")
    
    def test_08_delete_button(self):
        """Test 8: Delete button exists"""
        print("\n[TEST 8] Delete button exists")
        
        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = self.test_user_id
                sess['is_admin'] = True
            
            response = client.get('/treasury/dashboard')
            self.assertEqual(response.status_code, 200)
            
            html_content = response.data.decode('utf-8')
            delete_buttons = re.findall(r'fa-trash', html_content)
            
            self.assertGreater(len(delete_buttons), 0, "Should have delete buttons")
            print(f"   PASS: Found {len(delete_buttons)} delete buttons")
    
    def test_09_voucher_preselects_cash(self):
        """Test 9: Voucher form pre-selects cash"""
        print("\n[TEST 9] Voucher form pre-selects cash")
        
        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = self.test_user_id
                sess['is_admin'] = True
            
            response = client.get(f'/treasury/vouchers/new/receipt?cash_id={self.test_general_id}')
            self.assertEqual(response.status_code, 200)
            
            html_content = response.data.decode('utf-8')
            selected_options = re.findall(r'selected', html_content)
            
            self.assertGreater(len(selected_options), 0, "Should pre-select cash")
            print(f"   PASS: Cash is pre-selected in voucher form")
    
    def test_10_transfer_preselects_account(self):
        """Test 10: Transfer form pre-selects account"""
        print("\n[TEST 10] Transfer form pre-selects account")
        
        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = self.test_user_id
                sess['is_admin'] = True
            
            response = client.get(f'/treasury/transfer?from_account={self.test_general_id}')
            self.assertEqual(response.status_code, 200)
            
            html_content = response.data.decode('utf-8')
            selected_options = re.findall(r'selected', html_content)
            
            self.assertGreater(len(selected_options), 0, "Should pre-select account")
            print(f"   PASS: Account is pre-selected in transfer form")
    
    def test_11_button_group_structure(self):
        """Test 11: Buttons grouped properly"""
        print("\n[TEST 11] Button group structure")
        
        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = self.test_user_id
                sess['is_admin'] = True
            
            response = client.get('/treasury/dashboard')
            self.assertEqual(response.status_code, 200)
            
            html_content = response.data.decode('utf-8')
            button_groups = re.findall(r'<div[^>]*btn-group[^>]*>', html_content)
            
            self.assertGreater(len(button_groups), 0, "Should have button groups")
            print(f"   PASS: Found {len(button_groups)} button groups")
    
    def test_12_icons_present(self):
        """Test 12: Button icons present"""
        print("\n[TEST 12] Button icons present")
        
        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = self.test_user_id
                sess['is_admin'] = True
            
            response = client.get('/treasury/dashboard')
            self.assertEqual(response.status_code, 200)
            
            html_content = response.data.decode('utf-8')
            
            icon_classes = [
                'fa-arrow-down',
                'fa-arrow-up',
                'fa-exchange-alt',
                'fa-edit',
                'fa-trash'
            ]
            
            found_icons = {}
            for icon_class in icon_classes:
                count = len(re.findall(icon_class, html_content))
                if count > 0:
                    found_icons[icon_class] = count
            
            self.assertGreater(len(found_icons), 0, "Should have icons")
            print(f"   PASS: Found {len(found_icons)} icon types")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Testing Cash Account Buttons")
    print("="*70)
    
    unittest.main(verbosity=2)
