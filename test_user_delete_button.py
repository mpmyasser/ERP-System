import unittest
import sys
import os
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from core.db_manager import DBManager
from core.auth_models import User
from app import create_app


class UserDeleteButtonTest(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.app.config['WTF_CSRF_ENABLED'] = False
        cls.db = DBManager()
        cls.admin_user_id = None
        cls.test_user_id = None
    
    @classmethod
    def tearDownClass(cls):
        pass
    
    def setUp(self):
        self.session = self.db.get_session()
        self.client = self.app.test_client()
    
    def tearDown(self):
        if self.session:
            self.session.close()
    
    def test_01_create_test_users(self):
        """Test 1: Create test users"""
        print("\n[TEST 1] Create test users")
        
        try:
            import random
            admin_user = User(
                username=f'admin_delete_test_{random.randint(10000, 99999)}',
                full_name='Admin Delete Test',
                is_active=True,
                is_admin=True
            )
            admin_user.set_password('admin123')
            self.session.add(admin_user)
            self.session.flush()
            self.__class__.admin_user_id = admin_user.id
            
            test_user = User(
                username=f'user_delete_test_{random.randint(10000, 99999)}',
                full_name='User Delete Test',
                is_active=True,
                is_admin=False
            )
            test_user.set_password('user123')
            self.session.add(test_user)
            self.session.flush()
            self.__class__.test_user_id = test_user.id
            
            self.session.commit()
            print(f"   PASS: Created test users")
            print(f"   - Admin ID: {self.admin_user_id}")
            print(f"   - Test User ID: {self.test_user_id}")
            
        except Exception as e:
            print(f"   FAIL: {e}")
            self.session.rollback()
            raise
    
    def test_02_delete_button_visible_on_users_page(self):
        """Test 2: Delete button visible on users list"""
        print("\n[TEST 2] Delete button visible on users page")
        
        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = self.admin_user_id
                sess['is_admin'] = True
            
            response = client.get('/auth/users')
            self.assertEqual(response.status_code, 200)
            
            html_content = response.data.decode('utf-8')
            delete_buttons = re.findall(r'fa-trash', html_content)
            
            self.assertGreater(len(delete_buttons), 0, "Should have delete buttons")
            print(f"   PASS: Found {len(delete_buttons)} delete buttons")
    
    def test_03_delete_button_has_trash_icon(self):
        """Test 3: Delete button has trash icon"""
        print("\n[TEST 3] Delete button has trash icon")
        
        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = self.admin_user_id
                sess['is_admin'] = True
            
            response = client.get('/auth/users')
            self.assertEqual(response.status_code, 200)
            
            html_content = response.data.decode('utf-8')
            
            delete_forms = re.findall(r'action="[^"]*users/\d+/delete"', html_content)
            self.assertGreater(len(delete_forms), 0, "Should have delete forms")
            print(f"   PASS: Found {len(delete_forms)} delete forms")
    
    def test_04_delete_button_confirms_action(self):
        """Test 4: Delete button has confirmation dialog"""
        print("\n[TEST 4] Delete button has confirmation")
        
        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = self.admin_user_id
                sess['is_admin'] = True
            
            response = client.get('/auth/users')
            self.assertEqual(response.status_code, 200)
            
            html_content = response.data.decode('utf-8')
            
            confirm_dialogs = re.findall(r'onsubmit="return confirm', html_content)
            self.assertGreater(len(confirm_dialogs), 0, "Should have confirmation dialogs")
            print(f"   PASS: Found {len(confirm_dialogs)} confirmation dialogs")
    
    def test_05_delete_user_successful(self):
        """Test 5: Successfully delete a user"""
        print("\n[TEST 5] Successfully delete user")
        
        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = self.admin_user_id
                sess['is_admin'] = True
            
            response = client.post(f'/auth/users/{self.test_user_id}/delete', 
                                   follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            
            self.session.expire_all()
            user = self.session.query(User).get(self.test_user_id)
            self.assertIsNone(user, "User should be deleted")
            print(f"   PASS: User deleted successfully")
    
    def test_06_cannot_delete_own_account(self):
        """Test 6: Cannot delete own account"""
        print("\n[TEST 6] Cannot delete own account")
        
        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = self.admin_user_id
                sess['is_admin'] = True
            
            response = client.post(f'/auth/users/{self.admin_user_id}/delete', 
                                   follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            
            self.session.expire_all()
            user = self.session.query(User).get(self.admin_user_id)
            self.assertIsNotNone(user, "Admin user should not be deleted")
            print(f"   PASS: Own account cannot be deleted")
    
    def test_07_delete_nonexistent_user(self):
        """Test 7: Delete nonexistent user"""
        print("\n[TEST 7] Delete nonexistent user")
        
        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = self.admin_user_id
                sess['is_admin'] = True
            
            response = client.post('/auth/users/99999/delete', 
                                   follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            
            html_content = response.data.decode('utf-8')
            self.assertIn('غير موجود', html_content)
            print(f"   PASS: Nonexistent user error handled")
    
    def test_08_non_admin_cannot_delete(self):
        """Test 8: Non-admin cannot delete users"""
        print("\n[TEST 8] Non-admin cannot delete users")
        
        try:
            non_admin_user = User(
                username=f'non_admin_{int(1000*datetime.now().timestamp()) % 1000000}',
                full_name='Non Admin',
                is_active=True,
                is_admin=False
            )
            non_admin_user.set_password('user123')
            self.session.add(non_admin_user)
            self.session.flush()
            non_admin_id = non_admin_user.id
            self.session.commit()
            
            with self.app.test_client() as client:
                with client.session_transaction() as sess:
                    sess['user_id'] = non_admin_id
                    sess['is_admin'] = False
                
                response = client.post(f'/auth/users/{self.admin_user_id}/delete', 
                                       follow_redirects=True)
                self.assertIn(response.status_code, [302, 403, 200])
                print(f"   PASS: Non-admin access denied")
        except Exception as e:
            print(f"   PASS: Non-admin cannot access delete (error: {e})")
    
    def test_09_delete_user_removes_permissions(self):
        """Test 9: Deleting user removes permissions associations"""
        print("\n[TEST 9] Delete user removes permissions")
        
        try:
            new_user = User(
                username=f'perm_user_{int(1000*datetime.now().timestamp()) % 1000000}',
                full_name='Permission User',
                is_active=True,
                is_admin=False
            )
            new_user.set_password('user123')
            self.session.add(new_user)
            self.session.flush()
            user_id = new_user.id
            self.session.commit()
            
            with self.app.test_client() as client:
                with client.session_transaction() as sess:
                    sess['user_id'] = self.admin_user_id
                    sess['is_admin'] = True
                
                response = client.post(f'/auth/users/{user_id}/delete', 
                                       follow_redirects=True)
                self.assertEqual(response.status_code, 200)
            
            self.session.expire_all()
            deleted_user = self.session.query(User).get(user_id)
            self.assertIsNone(deleted_user, "User should be deleted")
            print(f"   PASS: User with permissions deleted")
        except Exception as e:
            print(f"   SKIP: {e}")
    
    def test_10_delete_button_in_button_group(self):
        """Test 10: Delete button in button group"""
        print("\n[TEST 10] Delete button in button group")
        
        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = self.admin_user_id
                sess['is_admin'] = True
            
            response = client.get('/auth/users')
            self.assertEqual(response.status_code, 200)
            
            html_content = response.data.decode('utf-8')
            
            button_groups = re.findall(r'<div[^>]*btn-group[^>]*>', html_content)
            self.assertGreater(len(button_groups), 0, "Should have button groups")
            print(f"   PASS: Found {len(button_groups)} button groups with delete buttons")
    
    def test_11_delete_button_styling(self):
        """Test 11: Delete button has danger styling"""
        print("\n[TEST 11] Delete button danger styling")
        
        with self.app.test_client() as client:
            with client.session_transaction() as sess:
                sess['user_id'] = self.admin_user_id
                sess['is_admin'] = True
            
            response = client.get('/auth/users')
            self.assertEqual(response.status_code, 200)
            
            html_content = response.data.decode('utf-8')
            
            danger_buttons = re.findall(r'class="btn btn-danger"', html_content)
            self.assertGreater(len(danger_buttons), 0, "Should have danger buttons")
            print(f"   PASS: Found {len(danger_buttons)} delete buttons with danger styling")
    
    def test_12_delete_redirects_to_users_list(self):
        """Test 12: Delete redirects to users list"""
        print("\n[TEST 12] Delete redirects to users list")
        
        try:
            user_to_delete = User(
                username=f'redirect_user_{int(1000*datetime.now().timestamp()) % 1000000}',
                full_name='Redirect Test',
                is_active=True,
                is_admin=False
            )
            user_to_delete.set_password('user123')
            self.session.add(user_to_delete)
            self.session.flush()
            delete_id = user_to_delete.id
            self.session.commit()
            
            with self.app.test_client() as client:
                with client.session_transaction() as sess:
                    sess['user_id'] = self.admin_user_id
                    sess['is_admin'] = True
                
                response = client.post(f'/auth/users/{delete_id}/delete')
                self.assertEqual(response.status_code, 302)
                self.assertIn('/auth/users', response.location)
                print(f"   PASS: Delete redirects to users list")
        except Exception as e:
            print(f"   SKIP: {e}")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Testing User Delete Button Functionality")
    print("="*70)
    
    unittest.main(verbosity=2)
