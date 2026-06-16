import unittest
from datetime import datetime, date
import sys
import os
import uuid
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db_manager import DBManager
from core.treasury_models import CashAccount, BankAccount, CashTransfer
from core.accounting_models import Account, AccountType
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import DetachedInstanceError


class TestTreasuryRouteQueries(unittest.TestCase):
    """
    اختبار الاستعلامات المستخدمة في routes/treasury.py للتحقق من eager loading الصحيح
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
        return str(uuid.uuid4())[:8]
    
    def _create_test_account(self, name_suffix=''):
        account = Account(
            code=self._generate_unique_code(),
            name=f'حساب {name_suffix or uuid.uuid4().hex[:4]}',
            type=AccountType.ASSET.value,
            is_active=1
        )
        self.session.add(account)
        self.session.flush()
        return account
    
    def test_dashboard_cash_accounts_query_pattern(self):
        """
        اختبار: نمط استعلام dashboard للخزائن النشطة
        محاكاة: db_session.query(CashAccount).options(joinedload(CashAccount.account))
                    .filter_by(is_active=True).order_by(CashAccount.display_order).all()
        """
        # إنشاء بيانات
        for i in range(3):
            account = self._create_test_account(f'داشبورد {i}')
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
        cash_accounts = self.session.query(CashAccount).options(
            joinedload(CashAccount.account)
        ).filter_by(is_active=True).order_by(CashAccount.display_order).all()
        
        self.assertGreaterEqual(len(cash_accounts), 3)
        
        # إغلاق الجلسة (كما في treasury.py)
        self.session.close()
        
        # التحقق من أن template يمكنه الوصول للبيانات: c.account.code - c.account.name
        for c in cash_accounts:
            # هذا يجب أن ينجح مع eager loading
            try:
                code = c.account.code
                name = c.account.name
                self.assertIsNotNone(code)
                self.assertIsNotNone(name)
            except DetachedInstanceError:
                self.fail(f"DetachedInstanceError raised when accessing c.account on {c.name}")
    
    def test_dashboard_bank_accounts_query_pattern(self):
        """
        اختبار: نمط استعلام dashboard للحسابات البنكية
        محاكاة: db_session.query(BankAccount).options(joinedload(BankAccount.account))
                    .order_by(BankAccount.display_order).all()
        """
        # إنشاء بيانات
        for i in range(2):
            account = self._create_test_account(f'بنك {i}')
            bank = BankAccount(
                bank_name=f'البنك {i}',
                account_number=f'ACC{i}',
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
        
        # التحقق من الوصول
        for ba in bank_accounts:
            try:
                code = ba.account.code
                name = ba.account.name
                self.assertIsNotNone(code)
                self.assertIsNotNone(name)
            except DetachedInstanceError:
                self.fail(f"DetachedInstanceError raised when accessing account on {ba.bank_name}")
    
    def test_list_pending_loans_query_pattern(self):
        """
        اختبار: نمط استعلام list_pending_loans
        محاكاة: db_session.query(CashAccount).options(joinedload(CashAccount.account))
                    .filter_by(is_active=True).all()
        """
        # إنشاء خزائن
        for i in range(2):
            account = self._create_test_account(f'خزينة قروض {i}')
            cash = CashAccount(
                name=f'خزينة {i}',
                account_id=account.id,
                type='General',
                is_active=True,
                display_order=i
            )
            self.session.add(cash)
        
        self.session.commit()
        
        # محاكاة استعلام list_pending_loans
        cash_accounts = self.session.query(CashAccount).options(
            joinedload(CashAccount.account)
        ).filter_by(is_active=True).all()
        
        self.assertGreaterEqual(len(cash_accounts), 2)
        
        # إغلاق الجلسة
        self.session.close()
        
        # التحقق من الوصول
        for ca in cash_accounts:
            try:
                self.assertIsNotNone(ca.account.code)
            except DetachedInstanceError:
                self.fail(f"DetachedInstanceError raised for {ca.name}")
    
    def test_new_voucher_form_query_pattern(self):
        """
        اختبار: نمط استعلام new_voucher للخزائن والحسابات البنكية
        """
        # إنشاء خزائن
        for i in range(2):
            account = self._create_test_account(f'سند {i}')
            cash = CashAccount(
                name=f'خزينة {i}',
                account_id=account.id,
                type='General',
                user_id=123,
                is_active=True,
                display_order=i
            )
            self.session.add(cash)
        
        # إنشاء حسابات بنكية
        for i in range(2):
            account = self._create_test_account(f'سند بنك {i}')
            bank = BankAccount(
                bank_name=f'البنك {i}',
                account_number=f'ACC{i}',
                account_id=account.id,
                is_active=True,
                display_order=i
            )
            self.session.add(bank)
        
        self.session.commit()
        
        # محاكاة استعلام النموذج
        cash_accounts = self.session.query(CashAccount).options(
            joinedload(CashAccount.account)
        ).filter_by(user_id=123, is_active=True).all()
        
        bank_accounts = self.session.query(BankAccount).options(
            joinedload(BankAccount.account)
        ).all()
        
        # إغلاق الجلسة
        self.session.close()
        
        # التحقق من الوصول
        for ca in cash_accounts:
            try:
                self.assertIsNotNone(ca.account.code)
            except DetachedInstanceError:
                self.fail(f"DetachedInstanceError for cash account")
        
        for ba in bank_accounts:
            try:
                self.assertIsNotNone(ba.account.code)
            except DetachedInstanceError:
                self.fail(f"DetachedInstanceError for bank account")
    
    def test_cash_transfer_query_with_filter(self):
        """
        اختبار: نمط استعلام cash_transfer مع filter
        محاكاة: db_session.query(CashAccount).filter(CashAccount.id == cash_id).first()
        ملاحظة: في الكود الحالي، لا يتم استخدام account بعد إغلاق الجلسة مباشرة في POST handler
        لكن يجب التحقق من أن البيانات آمنة
        """
        # إنشاء خزائن
        account1 = self._create_test_account('من1')
        from_cash = CashAccount(
            name='من',
            account_id=account1.id,
            type='General',
            is_active=True,
            display_order=1
        )
        self.session.add(from_cash)
        self.session.flush()
        
        account2 = self._create_test_account('إلى1')
        to_cash = CashAccount(
            name='إلى',
            account_id=account2.id,
            type='Subsidiary',
            parent_cash_id=from_cash.id,
            is_active=True,
            display_order=2
        )
        self.session.add(to_cash)
        self.session.commit()
        
        # محاكاة استعلام cash_transfer
        queried_from = self.session.query(CashAccount).filter(
            CashAccount.id == from_cash.id
        ).first()
        
        queried_to = self.session.query(CashAccount).filter(
            CashAccount.id == to_cash.id
        ).first()
        
        # الوصول قبل إغلاق الجلسة (كما في POST handler)
        from_id = queried_from.account_id
        from_name = queried_from.name
        to_id = queried_to.account_id
        to_name = queried_to.name
        
        # إغلاق الجلسة
        self.session.close()
        
        # يجب أن تظل البيانات الأساسية موجودة
        self.assertIsNotNone(from_id)
        self.assertIsNotNone(from_name)
        self.assertIsNotNone(to_id)
        self.assertIsNotNone(to_name)
    
    def test_receive_transfers_pending_transfers_query(self):
        """
        اختبار: نمط استعلام receive_transfers للتحويلات المعلقة
        محاكاة: db_session.query(CashTransfer).options(
                    joinedload(CashTransfer.from_cash),
                    joinedload(CashTransfer.to_cash)
                ).filter_by(status='Pending').order_by(CashTransfer.transfer_date.desc()).all()
        """
        # إنشاء خزائن وتحويلات
        general_account = self._create_test_account('عمومي')
        general_cash = CashAccount(
            name='عمومية',
            account_id=general_account.id,
            type='General',
            is_active=True,
            display_order=1
        )
        self.session.add(general_cash)
        self.session.flush()
        
        sub_account = self._create_test_account('فرعي')
        sub_cash = CashAccount(
            name='فرعية',
            account_id=sub_account.id,
            type='Subsidiary',
            parent_cash_id=general_cash.id,
            is_active=True,
            display_order=2
        )
        self.session.add(sub_cash)
        self.session.flush()
        
        # إنشاء تحويلات
        for i in range(2):
            transfer = CashTransfer(
                from_cash_id=general_cash.id,
                to_cash_id=sub_cash.id,
                amount=1000.0 * (i + 1),
                transfer_date=date.today(),
                description=f'تحويل {i}',
                status='Pending'
            )
            self.session.add(transfer)
        
        self.session.commit()
        
        # محاكاة استعلام receive_transfers
        pending_transfers = self.session.query(CashTransfer).options(
            joinedload(CashTransfer.from_cash),
            joinedload(CashTransfer.to_cash)
        ).filter_by(status='Pending').order_by(CashTransfer.transfer_date.desc()).all()
        
        self.assertGreaterEqual(len(pending_transfers), 2)
        
        # حفظ البيانات قبل الإغلاق (كما يفعل receive_transfers بتجميع البيانات)
        transfer_list = [
            {
                'from_name': t.from_cash.name,
                'to_name': t.to_cash.name,
                'amount': t.amount
            }
            for t in pending_transfers
        ]
        
        # إغلاق الجلسة
        self.session.close()
        
        # التحقق من الوصول للبيانات المجمعة
        for i, t in enumerate(pending_transfers):
            try:
                # محاكاة template access
                source_name = t.from_cash.name
                dest_name = t.to_cash.name
                self.assertEqual(source_name, transfer_list[i]['from_name'])
                self.assertEqual(dest_name, transfer_list[i]['to_name'])
            except DetachedInstanceError:
                self.fail(f"DetachedInstanceError in transfer {i}")


class TestQueryRegressions(unittest.TestCase):
    """
    اختبار السيناريوهات التي كانت تسبب DetachedInstanceError قبل الإصلاح
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
        return str(uuid.uuid4())[:8]
    
    def _create_test_account(self, name_suffix=''):
        account = Account(
            code=self._generate_unique_code(),
            name=f'حساب {name_suffix or uuid.uuid4().hex[:4]}',
            type=AccountType.ASSET.value,
            is_active=1
        )
        self.session.add(account)
        self.session.flush()
        return account
    
    def test_regression_dashboard_cash_account_code_access(self):
        """
        اختبار Regression: الوصول إلى c.account.code في dashboard.html (المشكلة الأصلية)
        كان يسبب: DetachedInstanceError at app/templates/treasury/dashboard.html line 104
        """
        # إنشاء بيانات
        account = self._create_test_account('regression')
        cash = CashAccount(
            name='اختبار انحدار',
            account_id=account.id,
            type='General',
            is_active=True,
            display_order=1
        )
        self.session.add(cash)
        self.session.commit()
        
        # محاكاة dashboard query (بدون joinedload - هذا كان يسبب الخطأ)
        cash_without_eager = self.session.query(CashAccount).filter_by(is_active=True).first()
        
        # محاكاة dashboard query (مع joinedload - الحل)
        cash_with_eager = self.session.query(CashAccount).options(
            joinedload(CashAccount.account)
        ).filter_by(is_active=True).first()
        
        # إغلاق الجلسة (كما في treasury.py finally block)
        self.session.close()
        
        # بدون joinedload يجب أن يرفع خطأ
        with self.assertRaises(DetachedInstanceError):
            _ = cash_without_eager.account.code
        
        # مع joinedload يجب أن يعمل
        try:
            code = cash_with_eager.account.code
            name = cash_with_eager.account.name
            self.assertIsNotNone(code)
            self.assertIsNotNone(name)
        except DetachedInstanceError:
            self.fail("joinedload should prevent DetachedInstanceError")
    
    def test_regression_multiple_relationship_levels(self):
        """
        اختبار Regression: الوصول إلى relationship داخل relationship (nested eager loading)
        """
        # إنشاء hierarchical data
        general_account = self._create_test_account('general')
        general_cash = CashAccount(
            name='general',
            account_id=general_account.id,
            type='General',
            is_active=True,
            display_order=1
        )
        self.session.add(general_cash)
        self.session.flush()
        
        sub_account = self._create_test_account('subsidiary')
        sub_cash = CashAccount(
            name='subsidiary',
            account_id=sub_account.id,
            type='Subsidiary',
            parent_cash_id=general_cash.id,
            is_active=True,
            display_order=2
        )
        self.session.add(sub_cash)
        self.session.commit()
        
        # بدون nested eager loading
        sub_cash_no_eager = self.session.query(CashAccount).filter_by(
            parent_cash_id=general_cash.id
        ).first()
        
        # مع nested eager loading
        sub_cash_with_eager = self.session.query(CashAccount).options(
            joinedload(CashAccount.account)
        ).filter_by(parent_cash_id=general_cash.id).first()
        
        # إغلاق الجلسة
        self.session.close()
        
        # بدون eager loading
        with self.assertRaises(DetachedInstanceError):
            _ = sub_cash_no_eager.account.code
        
        # مع eager loading يجب أن يعمل
        try:
            code = sub_cash_with_eager.account.code
            self.assertIsNotNone(code)
        except DetachedInstanceError:
            self.fail("nested eager loading should prevent DetachedInstanceError")


if __name__ == '__main__':
    unittest.main()
