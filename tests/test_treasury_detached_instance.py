import unittest
from datetime import datetime
import sys
import os
import uuid
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db_manager import DBManager
from core.treasury_models import CashAccount, BankAccount
from core.accounting_models import Account, AccountType
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import DetachedInstanceError


class TestTreasuryDetachedInstance(unittest.TestCase):
    """
    اختبار للتأكد من عدم حدوث DetachedInstanceError عند الوصول للعلاقات بعد إغلاق الجلسة
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
    
    def _generate_unique_code(self):
        """إنشاء كود فريد"""
        return str(uuid.uuid4())[:8]
    
    def _create_test_account(self):
        """إنشاء حساب محاسبي للاختبار"""
        account = Account(
            code=self._generate_unique_code(),
            name=f'اختبار خزينة {uuid.uuid4().hex[:4]}',
            type=AccountType.ASSET.value,
            is_active=1
        )
        self.session.add(account)
        self.session.flush()
        return account
    
    def _create_test_cash_account(self, account, name=None):
        """إنشاء خزينة اختبار"""
        if name is None:
            name = f'خزينة {uuid.uuid4().hex[:4]}'
        
        cash_account = CashAccount(
            name=name,
            account_id=account.id,
            type='General',
            is_active=True,
            display_order=1
        )
        self.session.add(cash_account)
        self.session.flush()
        return cash_account
    
    def _create_test_bank_account(self, account, bank_name=None):
        """إنشاء حساب بنكي للاختبار"""
        if bank_name is None:
            bank_name = f'بنك {uuid.uuid4().hex[:4]}'
        
        bank_account = BankAccount(
            bank_name=bank_name,
            account_number=f'123456{uuid.uuid4().hex[:4]}',
            account_id=account.id,
            is_active=True,
            display_order=1
        )
        self.session.add(bank_account)
        self.session.flush()
        return bank_account

    def test_cash_account_without_joinedload_raises_error(self):
        """
        اختبار: الوصول للعلاقة بدون joinedload بعد إغلاق الجلسة يسبب خطأ
        """
        # إنشاء بيانات اختبار
        account = self._create_test_account()
        cash_account = self._create_test_cash_account(account)
        cash_id = cash_account.id
        self.session.commit()
        
        # استعلام بدون joinedload
        cash = self.session.query(CashAccount).filter(CashAccount.id == cash_id).first()
        self.assertIsNotNone(cash)
        
        # إغلاق الجلسة
        self.session.close()
        
        # محاولة الوصول للعلاقة بعد إغلاق الجلسة يجب أن يسبب خطأ
        with self.assertRaises(DetachedInstanceError):
            _ = cash.account.code
    
    def test_cash_account_with_joinedload_works_after_session_close(self):
        """
        اختبار: استخدام joinedload يسمح بالوصول للعلاقة بعد إغلاق الجلسة
        """
        # إنشاء بيانات اختبار
        account = self._create_test_account()
        cash_account = self._create_test_cash_account(account)
        cash_id = cash_account.id
        expected_code = account.code
        expected_name = account.name
        self.session.commit()
        
        # استعلام مع joinedload
        cash = self.session.query(CashAccount).options(
            joinedload(CashAccount.account)
        ).filter(CashAccount.id == cash_id).first()
        self.assertIsNotNone(cash)
        
        # إغلاق الجلسة
        self.session.close()
        
        # يجب أن يعمل الوصول للعلاقة بدون خطأ
        self.assertEqual(cash.account.code, expected_code)
        self.assertEqual(cash.account.name, expected_name)
    
    def test_bank_account_with_joinedload_works_after_session_close(self):
        """
        اختبار: استخدام joinedload لـ BankAccount يسمح بالوصول للعلاقة بعد إغلاق الجلسة
        """
        # إنشاء بيانات اختبار
        account = self._create_test_account()
        bank_account = self._create_test_bank_account(account)
        bank_id = bank_account.id
        expected_code = account.code
        expected_name = account.name
        self.session.commit()
        
        # استعلام مع joinedload
        bank = self.session.query(BankAccount).options(
            joinedload(BankAccount.account)
        ).filter(BankAccount.id == bank_id).first()
        self.assertIsNotNone(bank)
        
        # إغلاق الجلسة
        self.session.close()
        
        # يجب أن يعمل الوصول للعلاقة بدون خطأ
        self.assertEqual(bank.account.code, expected_code)
        self.assertEqual(bank.account.name, expected_name)
    
    def test_cash_accounts_list_with_joinedload_works_after_session_close(self):
        """
        اختبار: استعلام قائمة CashAccount مع joinedload يعمل بعد إغلاق الجلسة
        """
        # إنشاء عدة خزائن للاختبار
        accounts_data = []
        for i in range(2):
            account = self._create_test_account()
            cash_account = self._create_test_cash_account(account, f'خزينة {i}')
            accounts_data.append((cash_account, account))
        
        self.session.commit()
        
        # استعلام مع joinedload
        cash_accounts = self.session.query(CashAccount).options(
            joinedload(CashAccount.account)
        ).filter_by(is_active=True).order_by(CashAccount.display_order).all()
        
        self.assertGreaterEqual(len(cash_accounts), 2)
        
        # إغلاق الجلسة
        self.session.close()
        
        # يجب أن نتمكن من الوصول لجميع الخزائن والحسابات المرتبطة بها
        for cash in cash_accounts:
            self.assertIsNotNone(cash.account)
            self.assertIsNotNone(cash.account.code)
            self.assertIsNotNone(cash.account.name)
    
    def test_bank_accounts_list_with_joinedload_works_after_session_close(self):
        """
        اختبار: استعلام قائمة BankAccount مع joinedload يعمل بعد إغلاق الجلسة
        """
        # إنشاء عدة حسابات بنكية للاختبار
        for i in range(2):
            account = self._create_test_account()
            bank_account = self._create_test_bank_account(account, f'بنك {i}')
        
        self.session.commit()
        
        # استعلام مع joinedload
        bank_accounts = self.session.query(BankAccount).options(
            joinedload(BankAccount.account)
        ).order_by(BankAccount.display_order).all()
        
        self.assertGreaterEqual(len(bank_accounts), 2)
        
        # إغلاق الجلسة
        self.session.close()
        
        # يجب أن نتمكن من الوصول لجميع الحسابات البنكية والحسابات المرتبطة بها
        for bank in bank_accounts:
            self.assertIsNotNone(bank.account)
            self.assertIsNotNone(bank.account.code)
            self.assertIsNotNone(bank.account.name)
    
    def test_filtered_cash_accounts_with_joinedload(self):
        """
        اختبار: استعلام مع filter و joinedload يعمل بشكل صحيح
        """
        # إنشاء خزينة نشطة
        account1 = self._create_test_account()
        cash_active = self._create_test_cash_account(account1, 'خزينة نشطة')
        
        # إنشاء خزينة معطلة
        account2 = self._create_test_account()
        cash_inactive = CashAccount(
            name='خزينة معطلة',
            account_id=account2.id,
            type='General',
            is_active=False,
            display_order=2
        )
        self.session.add(cash_inactive)
        self.session.commit()
        
        # استعلام فقط الخزائن النشطة مع joinedload
        cash_accounts = self.session.query(CashAccount).options(
            joinedload(CashAccount.account)
        ).filter_by(is_active=True).all()
        
        # يجب أن يكون لدينا على الأقل الخزينة النشطة
        self.assertGreater(len(cash_accounts), 0)
        
        # إغلاق الجلسة
        self.session.close()
        
        # يجب أن نتمكن من الوصول للحساب المرتبط
        for cash in cash_accounts:
            self.assertIsNotNone(cash.account)
            self.assertIsNotNone(cash.account.code)


class TestTreasuryDashboardScenarios(unittest.TestCase):
    """
    اختبارات لسيناريوهات dashboard بالكامل
    """
    
    @classmethod
    def setUpClass(cls):
        cls.db_manager = DBManager()
    
    def setUp(self):
        self.session = self.db_manager.get_session()
    
    def tearDown(self):
        try:
            self.session.rollback()
        finally:
            self.session.close()
    
    def _generate_unique_code(self):
        """إنشاء كود فريد"""
        return str(uuid.uuid4())[:8]
    
    def test_dashboard_scenario_admin_cash_accounts(self):
        """
        اختبار سيناريو dashboard للمسؤول: الوصول لجميع الخزائن والحسابات
        """
        # إنشاء بيانات اختبار
        for i in range(3):
            account = Account(
                code=self._generate_unique_code(),
                name=f'حساب {i}',
                type=AccountType.ASSET.value,
                is_active=1
            )
            self.session.add(account)
            self.session.flush()
            
            cash = CashAccount(
                name=f'خزينة {i}',
                account_id=account.id,
                type='General',
                is_active=True,
                display_order=i
            )
            self.session.add(cash)
        
        self.session.commit()
        
        # محاكاة استعلام dashboard
        admin_cash_accounts = self.session.query(CashAccount).options(
            joinedload(CashAccount.account)
        ).filter_by(is_active=True).order_by(CashAccount.display_order).all()
        
        self.assertGreaterEqual(len(admin_cash_accounts), 3)
        
        # إغلاق الجلسة (كما يحدث في dashboard)
        self.session.close()
        
        # اختبار: يجب أن يتمكن الـ template من الوصول للبيانات
        for cash in admin_cash_accounts:
            self.assertIsNotNone(cash.name)
            self.assertIsNotNone(cash.account)
            self.assertIsNotNone(cash.account.code)
            self.assertIsNotNone(cash.account.name)
    
    def test_dashboard_scenario_bank_accounts(self):
        """
        اختبار سيناريو dashboard: الوصول لحسابات البنوك
        """
        # إنشاء بيانات اختبار
        for i in range(2):
            account = Account(
                code=self._generate_unique_code(),
                name=f'بنك {i}',
                type=AccountType.ASSET.value,
                is_active=1
            )
            self.session.add(account)
            self.session.flush()
            
            bank = BankAccount(
                bank_name=f'البنك {i}',
                account_number=f'123456{i}',
                account_id=account.id,
                is_active=True,
                display_order=i
            )
            self.session.add(bank)
        
        self.session.commit()
        
        # محاكاة استعلام dashboard
        bank_accounts = self.session.query(BankAccount).options(
            joinedload(BankAccount.account)
        ).order_by(BankAccount.display_order).all()
        
        self.assertGreaterEqual(len(bank_accounts), 2)
        
        # إغلاق الجلسة
        self.session.close()
        
        # اختبار: يجب أن يتمكن الـ template من الوصول للبيانات
        for bank in bank_accounts:
            self.assertIsNotNone(bank.bank_name)
            self.assertIsNotNone(bank.account)
            self.assertIsNotNone(bank.account.code)


if __name__ == '__main__':
    unittest.main()
