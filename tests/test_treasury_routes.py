import unittest
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from core.db_manager import DBManager
from core.treasury_models import CashAccount, BankAccount
from core.accounting_models import Account, AccountType
from core.auth_models import User
from core.auth_manager import AuthManager
from sqlalchemy.orm import joinedload
import tempfile
import os


class TreasuryRoutesTestCase(unittest.TestCase):
    """
    اختبار routes الخزينة للتأكد من عدم حدوث DetachedInstanceError
    """
    
    def setUp(self):
        """إنشاء تطبيق Flask للاختبار"""
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['SESSION_TYPE'] = 'filesystem'
        
        # إنشاء جلسة اختبار
        self.client = self.app.test_client()
        # قاعدة بيانات مؤقتة معزولة لكل اختبار (تمنع تسرّب البيانات بين الاختبارات
        # عبر تشارك ملف SQLite واحد، وهي المشكلة الجذرية لعدم استقرار هذه الاختبارات)
        self._temp_db_fd, self._temp_db_path = tempfile.mkstemp(suffix='.db')
        self.db_manager = DBManager(db_path=self._temp_db_path)
        self.session = self.db_manager.get_session()
    
    def tearDown(self):
        """تنظيف بعد الاختبار"""
        try:
            self.session.rollback()
        finally:
            self.session.close()
        self.db_manager.engine.dispose()
        os.close(self._temp_db_fd)
        try:
            os.remove(self._temp_db_path)
        except OSError:
            pass
    
    def _create_test_user(self):
        """إنشاء مستخدم اختبار"""
        user = User(
            username='testuser',
            password_hash='test',
            full_name='مستخدم اختبار',
            email='test@example.com'
        )
        self.session.add(user)
        self.session.flush()
        return user
    
    def _create_test_account(self, code='1001', name='حساب اختبار'):
        """إنشاء حساب محاسبي"""
        account = Account(
            code=code,
            name=name,
            type=AccountType.ASSET.value,
            is_active=1
        )
        self.session.add(account)
        self.session.flush()
        return account
    
    def _create_test_cash_account(self, account, name='خزينة اختبار', user_id=None):
        """إنشاء خزينة"""
        cash_account = CashAccount(
            name=name,
            account_id=account.id,
            type='General',
            is_active=True,
            display_order=1,
            user_id=user_id
        )
        self.session.add(cash_account)
        self.session.flush()
        return cash_account
    
    def _create_test_bank_account(self, account, bank_name='بنك اختبار'):
        """إنشاء حساب بنكي"""
        bank_account = BankAccount(
            bank_name=bank_name,
            account_number='123456',
            account_id=account.id,
            is_active=True,
            display_order=1
        )
        self.session.add(bank_account)
        self.session.flush()
        return bank_account

    def test_cash_account_accessed_after_session_close(self):
        """
        اختبار: التأكد من أن CashAccount يمكن الوصول إليه بعد إغلاق الجلسة
        """
        # إنشاء بيانات
        account = self._create_test_account()
        cash_account = self._create_test_cash_account(account)
        cash_id = cash_account.id
        self.session.commit()
        
        # محاكاة سيناريو route dashboard
        cash = self.session.query(CashAccount).options(
            joinedload(CashAccount.account)
        ).filter_by(is_active=True).filter(CashAccount.id == cash_id).first()
        
        self.assertIsNotNone(cash)
        
        # إغلاق الجلسة (كما يحدث في route)
        self.session.close()
        
        # اختبار الوصول للعلاقات
        try:
            account_code = cash.account.code
            account_name = cash.account.name
            self.assertEqual(account_code, '1001')
            self.assertEqual(account_name, 'حساب اختبار')
        except Exception as e:
            self.fail(f"Failed to access account relationship: {e}")
    
    def test_bank_account_accessed_after_session_close(self):
        """
        اختبار: التأكد من أن BankAccount يمكن الوصول إليه بعد إغلاق الجلسة
        """
        # إنشاء بيانات
        account = self._create_test_account()
        bank_account = self._create_test_bank_account(account)
        bank_id = bank_account.id
        self.session.commit()
        
        # محاكاة سيناريو route
        bank = self.session.query(BankAccount).options(
            joinedload(BankAccount.account)
        ).filter(BankAccount.id == bank_id).first()
        
        self.assertIsNotNone(bank)
        
        # إغلاق الجلسة
        self.session.close()
        
        # اختبار الوصول للعلاقات
        try:
            account_code = bank.account.code
            account_name = bank.account.name
            self.assertEqual(account_code, '1001')
            self.assertEqual(account_name, 'حساب اختبار')
        except Exception as e:
            self.fail(f"Failed to access account relationship: {e}")

    def test_multiple_cash_accounts_accessed_after_session_close(self):
        """
        اختبار: التأكد من أن قائمة CashAccount يمكن الوصول إليها بعد إغلاق الجلسة
        """
        # إنشاء عدة خزائن
        accounts = []
        cash_accounts = []
        
        for i in range(3):
            account = self._create_test_account(f'100{i}', f'حساب {i}')
            accounts.append(account)
            cash = self._create_test_cash_account(account, f'خزينة {i}')
            cash_accounts.append(cash)
        
        self.session.commit()
        
        # محاكاة سيناريو route dashboard
        fetched_cash_accounts = self.session.query(CashAccount).options(
            joinedload(CashAccount.account)
        ).filter_by(is_active=True).order_by(CashAccount.display_order).all()
        
        self.assertEqual(len(fetched_cash_accounts), 3)
        
        # إغلاق الجلسة
        self.session.close()
        
        # اختبار الوصول للعلاقات
        try:
            for i, cash in enumerate(fetched_cash_accounts):
                self.assertEqual(cash.account.code, f'100{i}')
                self.assertEqual(cash.account.name, f'حساب {i}')
        except Exception as e:
            self.fail(f"Failed to access account relationships: {e}")

    def test_filtered_cash_accounts_with_condition(self):
        """
        اختبار: التأكد من أن استعلام مع filter يعمل بشكل صحيح
        """
        # إنشاء خزينة نشطة وأخرى معطلة
        account1 = self._create_test_account('1001', 'نشطة')
        cash_active = self._create_test_cash_account(account1, 'خزينة نشطة')
        
        account2 = self._create_test_account('1002', 'معطلة')
        cash_inactive = CashAccount(
            name='خزينة معطلة',
            account_id=account2.id,
            type='General',
            is_active=False,
            display_order=2
        )
        self.session.add(cash_inactive)
        self.session.commit()
        
        # استعلام فقط النشطة
        fetched = self.session.query(CashAccount).options(
            joinedload(CashAccount.account)
        ).filter_by(is_active=True).all()
        
        self.assertEqual(len(fetched), 1)
        
        # إغلاق الجلسة
        self.session.close()
        
        # اختبار الوصول
        try:
            self.assertEqual(fetched[0].account.code, '1001')
            self.assertEqual(fetched[0].account.name, 'نشطة')
        except Exception as e:
            self.fail(f"Failed to access account relationship: {e}")

    def test_cash_account_get_by_id(self):
        """
        اختبار: الوصول لـ CashAccount باستخدام get() مع joinedload
        """
        account = self._create_test_account()
        cash = self._create_test_cash_account(account)
        cash_id = cash.id
        self.session.commit()
        
        # استعلام باستخدام filter().first() مع joinedload
        fetched = self.session.query(CashAccount).options(
            joinedload(CashAccount.account)
        ).filter(CashAccount.id == cash_id).first()
        
        self.assertIsNotNone(fetched)
        
        # إغلاق الجلسة
        self.session.close()
        
        # اختبار الوصول
        try:
            self.assertEqual(fetched.account.code, '1001')
        except Exception as e:
            self.fail(f"Failed to access account: {e}")

    def test_cash_account_sorted_after_session_close(self):
        """
        اختبار: التأكد من أن الخزائن المصنفة تعمل بعد إغلاق الجلسة
        """
        # إنشاء خزائن بترتيب مختلف
        account1 = self._create_test_account('1003', 'حساب 3')
        cash1 = self._create_test_cash_account(account1, 'خزينة 3')
        cash1.display_order = 3
        
        account2 = self._create_test_account('1002', 'حساب 2')
        cash2 = self._create_test_cash_account(account2, 'خزينة 2')
        cash2.display_order = 2
        
        account3 = self._create_test_account('1001', 'حساب 1')
        cash3 = self._create_test_cash_account(account3, 'خزينة 1')
        cash3.display_order = 1
        
        self.session.commit()
        
        # استعلام مع ترتيب
        fetched = self.session.query(CashAccount).options(
            joinedload(CashAccount.account)
        ).filter_by(is_active=True).order_by(CashAccount.display_order).all()
        
        self.assertEqual(len(fetched), 3)
        
        # إغلاق الجلسة
        self.session.close()
        
        # اختبار الترتيب والوصول
        try:
            self.assertEqual(fetched[0].display_order, 1)
            self.assertEqual(fetched[0].account.code, '1001')
            
            self.assertEqual(fetched[1].display_order, 2)
            self.assertEqual(fetched[1].account.code, '1002')
            
            self.assertEqual(fetched[2].display_order, 3)
            self.assertEqual(fetched[2].account.code, '1003')
        except Exception as e:
            self.fail(f"Failed to access sorted accounts: {e}")


class TreasuryDataIntegrityTests(unittest.TestCase):
    """
    اختبارات التحقق من تكامل البيانات
    """
    
    def setUp(self):
        self._temp_db_fd, self._temp_db_path = tempfile.mkstemp(suffix='.db')
        self.db_manager = DBManager(db_path=self._temp_db_path)
        self.session = self.db_manager.get_session()
    
    def tearDown(self):
        try:
            self.session.rollback()
        finally:
            self.session.close()
        self.db_manager.engine.dispose()
        os.close(self._temp_db_fd)
        try:
            os.remove(self._temp_db_path)
        except OSError:
            pass
    
    def test_cash_account_code_accessibility(self):
        """
        اختبار: التأكد من إمكانية الوصول إلى code من خلال العلاقة
        """
        account = Account(
            code='TEST001',
            name='حساب اختبار',
            type=AccountType.ASSET.value,
            is_active=1
        )
        self.session.add(account)
        self.session.flush()
        
        cash = CashAccount(
            name='خزينة اختبار',
            account_id=account.id,
            type='General',
            is_active=True
        )
        self.session.add(cash)
        self.session.commit()
        
        # استعلام مع joinedload
        fetched = self.session.query(CashAccount).options(
            joinedload(CashAccount.account)
        ).filter_by(id=cash.id).first()
        
        # إغلاق الجلسة
        self.session.close()
        
        # التحقق من البيانات
        self.assertEqual(fetched.account.code, 'TEST001')
        self.assertEqual(fetched.account.name, 'حساب اختبار')
    
    def test_bank_account_code_accessibility(self):
        """
        اختبار: التأكد من إمكانية الوصول إلى code من خلال العلاقة للبنوك
        """
        account = Account(
            code='BANK001',
            name='بنك اختبار',
            type=AccountType.ASSET.value,
            is_active=1
        )
        self.session.add(account)
        self.session.flush()
        
        bank = BankAccount(
            bank_name='البنك الأهلي',
            account_number='123456789',
            account_id=account.id,
            is_active=True
        )
        self.session.add(bank)
        self.session.commit()
        
        # استعلام مع joinedload
        fetched = self.session.query(BankAccount).options(
            joinedload(BankAccount.account)
        ).filter_by(id=bank.id).first()
        
        # إغلاق الجلسة
        self.session.close()
        
        # التحقق من البيانات
        self.assertEqual(fetched.account.code, 'BANK001')
        self.assertEqual(fetched.account.name, 'بنك اختبار')


if __name__ == '__main__':
    unittest.main()
