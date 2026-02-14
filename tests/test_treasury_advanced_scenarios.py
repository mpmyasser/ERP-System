import unittest
from datetime import datetime, date
import sys
import uuid
sys.path.insert(0, 'd:\\H.R')

from core.db_manager import DBManager
from core.treasury_models import CashAccount, BankAccount, CashTransfer
from core.accounting_models import Account, AccountType
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import DetachedInstanceError


class TestCashAccountHierarchies(unittest.TestCase):
    """
    اختبار الخزائن الهرمية (عمومية وفرعية) مع eager loading
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
    
    def test_parent_child_cash_accounts_with_eager_loading(self):
        """
        اختبار: الوصول للحساب المرتبط في الخزائن الهرمية بعد إغلاق الجلسة
        """
        # إنشاء حساب عمومي
        general_account = self._create_test_account('عمومي')
        general_cash = CashAccount(
            name='خزينة عمومية',
            account_id=general_account.id,
            type='General',
            is_active=True,
            display_order=1
        )
        self.session.add(general_cash)
        self.session.flush()
        
        # إنشاء حساب فرعي
        subsidiary_account = self._create_test_account('فرعي')
        subsidiary_cash = CashAccount(
            name='خزينة فرعية',
            account_id=subsidiary_account.id,
            type='Subsidiary',
            parent_cash_id=general_cash.id,
            is_active=True,
            display_order=2
        )
        self.session.add(subsidiary_cash)
        self.session.commit()
        
        # استعلام مع eager loading
        general = self.session.query(CashAccount).options(
            joinedload(CashAccount.account)
        ).filter(CashAccount.id == general_cash.id).first()
        
        subsidiary = self.session.query(CashAccount).options(
            joinedload(CashAccount.account)
        ).filter(CashAccount.id == subsidiary_cash.id).first()
        
        general_code = general.account.code
        subsidiary_code = subsidiary.account.code
        
        # إغلاق الجلسة
        self.session.close()
        
        # يجب أن يعمل الوصول للحسابات المرتبطة
        self.assertEqual(general.account.code, general_code)
        self.assertEqual(subsidiary.account.code, subsidiary_code)
        self.assertTrue(general.is_general())
        self.assertTrue(subsidiary.is_subsidiary())
        self.assertEqual(subsidiary.parent_cash_id, general.id)
    
    def test_multiple_subsidiaries_with_eager_loading(self):
        """
        اختبار: خزينة عمومية لديها عدة خزائن فرعية
        """
        # إنشاء خزينة عمومية
        general_account = self._create_test_account('عمومي')
        general_cash = CashAccount(
            name='الخزينة الرئيسية',
            account_id=general_account.id,
            type='General',
            is_active=True,
            display_order=1
        )
        self.session.add(general_cash)
        self.session.flush()
        
        # إنشاء عدة خزائن فرعية
        subsidiary_cashes = []
        for i in range(3):
            sub_account = self._create_test_account(f'فرعي {i}')
            sub_cash = CashAccount(
                name=f'الفرع {i}',
                account_id=sub_account.id,
                type='Subsidiary',
                parent_cash_id=general_cash.id,
                is_active=True,
                display_order=i+2
            )
            self.session.add(sub_cash)
            subsidiary_cashes.append(sub_cash)
        
        self.session.commit()
        
        # استعلام الخزينة العمومية مع الفروع
        general = self.session.query(CashAccount).options(
            joinedload(CashAccount.account)
        ).filter(CashAccount.id == general_cash.id).first()
        
        # استعلام الفروع
        subsidiaries = self.session.query(CashAccount).options(
            joinedload(CashAccount.account)
        ).filter_by(parent_cash_id=general_cash.id).all()
        
        self.assertEqual(len(subsidiaries), 3)
        
        # إغلاق الجلسة
        self.session.close()
        
        # يجب أن نتمكن من الوصول لجميع البيانات
        self.assertIsNotNone(general.account.code)
        for sub in subsidiaries:
            self.assertIsNotNone(sub.account.code)
            self.assertIsNotNone(sub.account.name)
            self.assertEqual(sub.parent_cash_id, general.id)


class TestCashTransferWithRelationships(unittest.TestCase):
    """
    اختبار تحويلات الخزائن مع eager loading للعلاقات المتعددة
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
    
    def test_cash_transfer_with_nested_eager_loading(self):
        """
        اختبار: تحويل خزينة مع eager loading للحسابات المرتبطة
        """
        # إنشاء خزينتين
        from_account = self._create_test_account('من')
        from_cash = CashAccount(
            name='خزينة المصدر',
            account_id=from_account.id,
            type='General',
            is_active=True,
            display_order=1
        )
        self.session.add(from_cash)
        self.session.flush()
        
        to_account = self._create_test_account('إلى')
        to_cash = CashAccount(
            name='خزينة الوجهة',
            account_id=to_account.id,
            type='Subsidiary',
            parent_cash_id=from_cash.id,
            is_active=True,
            display_order=2
        )
        self.session.add(to_cash)
        self.session.flush()
        
        # إنشاء تحويل خزينة
        transfer = CashTransfer(
            from_cash_id=from_cash.id,
            to_cash_id=to_cash.id,
            amount=1000.0,
            transfer_date=date.today(),
            description='اختبار تحويل',
            status='Pending'
        )
        self.session.add(transfer)
        self.session.commit()
        
        # استعلام التحويل مع eager loading للعلاقات
        queried_transfer = self.session.query(CashTransfer).options(
            joinedload(CashTransfer.from_cash).joinedload(CashAccount.account),
            joinedload(CashTransfer.to_cash).joinedload(CashAccount.account)
        ).filter(CashTransfer.id == transfer.id).first()
        
        # الحصول على البيانات قبل إغلاق الجلسة
        from_cash_name = queried_transfer.from_cash.name
        from_account_code = queried_transfer.from_cash.account.code
        to_cash_name = queried_transfer.to_cash.name
        to_account_code = queried_transfer.to_cash.account.code
        
        # إغلاق الجلسة
        self.session.close()
        
        # يجب أن نتمكن من الوصول لجميع البيانات بعد إغلاق الجلسة
        self.assertEqual(queried_transfer.from_cash.name, from_cash_name)
        self.assertEqual(queried_transfer.from_cash.account.code, from_account_code)
        self.assertEqual(queried_transfer.to_cash.name, to_cash_name)
        self.assertEqual(queried_transfer.to_cash.account.code, to_account_code)
        self.assertEqual(queried_transfer.amount, 1000.0)
    
    def test_multiple_transfers_with_eager_loading(self):
        """
        اختبار: عدة تحويلات مع eager loading (سيناريو receive_transfers)
        """
        # إنشاء خزينة عمومية وعدة خزائن فرعية
        general_account = Account(
            code=self._generate_unique_code(),
            name='الخزينة الرئيسية',
            type=AccountType.ASSET.value,
            is_active=1
        )
        self.session.add(general_account)
        self.session.flush()
        
        general_cash = CashAccount(
            name='الخزينة الرئيسية',
            account_id=general_account.id,
            type='General',
            is_active=True,
            display_order=1
        )
        self.session.add(general_cash)
        self.session.flush()
        
        # إنشاء عدة خزائن فرعية وتحويلات
        transfers = []
        for i in range(3):
            sub_account = Account(
                code=self._generate_unique_code(),
                name=f'الفرع {i}',
                type=AccountType.ASSET.value,
                is_active=1
            )
            self.session.add(sub_account)
            self.session.flush()
            
            sub_cash = CashAccount(
                name=f'الفرع {i}',
                account_id=sub_account.id,
                type='Subsidiary',
                parent_cash_id=general_cash.id,
                is_active=True,
                display_order=i+2
            )
            self.session.add(sub_cash)
            self.session.flush()
            
            transfer = CashTransfer(
                from_cash_id=general_cash.id,
                to_cash_id=sub_cash.id,
                amount=1000.0 * (i + 1),
                transfer_date=date.today(),
                description=f'تحويل إلى الفرع {i}',
                status='Pending'
            )
            self.session.add(transfer)
            transfers.append(transfer)
        
        self.session.commit()
        
        # استعلام جميع التحويلات مع eager loading (مثل receive_transfers)
        pending_transfers = self.session.query(CashTransfer).options(
            joinedload(CashTransfer.from_cash).joinedload(CashAccount.account),
            joinedload(CashTransfer.to_cash).joinedload(CashAccount.account)
        ).filter_by(status='Pending').order_by(CashTransfer.transfer_date.desc()).all()
        
        self.assertGreaterEqual(len(pending_transfers), 3)
        
        # حفظ البيانات قبل إغلاق الجلسة
        transfer_data = [
            {
                'from_name': t.from_cash.name,
                'from_code': t.from_cash.account.code,
                'to_name': t.to_cash.name,
                'to_code': t.to_cash.account.code,
                'amount': t.amount
            }
            for t in pending_transfers[:3]
        ]
        
        # إغلاق الجلسة
        self.session.close()
        
        # يجب أن نتمكن من الوصول لجميع البيانات (مثل template access)
        for i, transfer in enumerate(pending_transfers[:3]):
            self.assertEqual(transfer.from_cash.name, transfer_data[i]['from_name'])
            self.assertEqual(transfer.from_cash.account.code, transfer_data[i]['from_code'])
            self.assertEqual(transfer.to_cash.name, transfer_data[i]['to_name'])
            self.assertEqual(transfer.to_cash.account.code, transfer_data[i]['to_code'])


class TestComplexFilteringWithEagerLoading(unittest.TestCase):
    """
    اختبار التصفية المعقدة مع eager loading (الأدمن vs المستخدم العادي)
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
    
    def test_admin_cash_accounts_with_eager_loading(self):
        """
        اختبار: استعلام الأدمن لجميع الخزائن مع eager loading
        """
        # إنشاء خزائن نشطة ومعطلة
        for i in range(2):
            account = self._create_test_account(f'خزينة {i}')
            cash = CashAccount(
                name=f'خزينة {i}',
                account_id=account.id,
                type='General',
                is_active=True,
                display_order=i
            )
            self.session.add(cash)
        
        # خزينة معطلة
        account = self._create_test_account('خزينة معطلة')
        inactive_cash = CashAccount(
            name='خزينة معطلة',
            account_id=account.id,
            type='General',
            is_active=False,
            display_order=99
        )
        self.session.add(inactive_cash)
        self.session.commit()
        
        # استعلام الأدمن (يرى جميع الخزائن النشطة)
        admin_cash_accounts = self.session.query(CashAccount).options(
            joinedload(CashAccount.account)
        ).filter_by(is_active=True).order_by(CashAccount.display_order).all()
        
        self.assertGreaterEqual(len(admin_cash_accounts), 2)
        
        # إغلاق الجلسة
        self.session.close()
        
        # يجب أن نتمكن من الوصول لجميع الخزائن والحسابات المرتبطة
        for cash in admin_cash_accounts:
            self.assertIsNotNone(cash.account.code)
            self.assertIsNotNone(cash.account.name)
            self.assertTrue(cash.is_active)
    
    def test_user_specific_cash_accounts_with_eager_loading(self):
        """
        اختبار: استعلام المستخدم للخزائن المسندة إليه مع eager loading
        """
        user_id = 123  # معرف مستخدم تجريبي
        
        # إنشاء خزائن للمستخدم
        for i in range(2):
            account = self._create_test_account(f'خزينة المستخدم {i}')
            cash = CashAccount(
                name=f'خزينة المستخدم {i}',
                account_id=account.id,
                type='General',
                user_id=user_id,
                is_active=True,
                display_order=i
            )
            self.session.add(cash)
        
        # إنشاء خزائن لمستخدم آخر
        for i in range(2):
            account = self._create_test_account(f'خزينة مستخدم آخر {i}')
            cash = CashAccount(
                name=f'خزينة مستخدم آخر {i}',
                account_id=account.id,
                type='General',
                user_id=999,
                is_active=True,
                display_order=i+2
            )
            self.session.add(cash)
        
        self.session.commit()
        
        # استعلام خزائن هذا المستخدم
        user_cash_accounts = self.session.query(CashAccount).options(
            joinedload(CashAccount.account)
        ).filter_by(user_id=user_id, is_active=True).all()
        
        self.assertGreaterEqual(len(user_cash_accounts), 2)
        
        # إغلاق الجلسة
        self.session.close()
        
        # يجب أن نتمكن من الوصول لجميع البيانات
        for cash in user_cash_accounts:
            self.assertEqual(cash.user_id, user_id)
            self.assertIsNotNone(cash.account.code)


class TestTemplateAccessPatterns(unittest.TestCase):
    """
    اختبار أنماط الوصول التي تحدث في templates (مثل dashboard.html)
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
    
    def test_dashboard_template_access_pattern(self):
        """
        اختبار: نمط الوصول في dashboard.html (c.account.code و c.account.name)
        """
        # إنشاء بيانات
        account = self._create_test_account('داشبورد')
        cash = CashAccount(
            name='خزينة الداشبورد',
            account_id=account.id,
            type='General',
            is_active=True,
            display_order=1
        )
        self.session.add(cash)
        self.session.commit()
        
        # محاكاة استعلام dashboard
        cash_accounts = self.session.query(CashAccount).options(
            joinedload(CashAccount.account)
        ).filter_by(is_active=True).order_by(CashAccount.display_order).all()
        
        # إغلاق الجلسة (كما في treasury.py)
        self.session.close()
        
        # محاكاة template access: {% for c in cash_accounts %}
        #     {{ c.account.code }} - {{ c.account.name }}
        for c in cash_accounts:
            code = c.account.code
            name = c.account.name
            self.assertIsNotNone(code)
            self.assertIsNotNone(name)
    
    def test_bank_accounts_template_access_pattern(self):
        """
        اختبار: نمط الوصول في templates للحسابات البنكية
        """
        # إنشاء بيانات
        account = self._create_test_account('بنك')
        bank = BankAccount(
            bank_name='البنك الأول',
            account_number='123456789',
            account_id=account.id,
            is_active=True,
            display_order=1
        )
        self.session.add(bank)
        self.session.commit()
        
        # محاكاة استعلام
        bank_accounts = self.session.query(BankAccount).options(
            joinedload(BankAccount.account)
        ).order_by(BankAccount.display_order).all()
        
        # إغلاق الجلسة
        self.session.close()
        
        # محاكاة template access
        for bank in bank_accounts:
            self.assertIsNotNone(bank.bank_name)
            self.assertIsNotNone(bank.account.code)
            self.assertIsNotNone(bank.account.name)
    
    def test_grouped_access_pattern_like_receive_transfers(self):
        """
        اختبار: نمط الوصول المتكرر (مثل receive_transfers الذي يجمع البيانات في قاموس)
        """
        # إنشاء خزينة عمومية وتحويلات
        general_account = self._create_test_account('عمومي')
        general_cash = CashAccount(
            name='الخزينة العمومية',
            account_id=general_account.id,
            type='General',
            is_active=True,
            display_order=1
        )
        self.session.add(general_cash)
        self.session.flush()
        
        # إنشاء عدة تحويلات
        for i in range(3):
            to_account = self._create_test_account(f'فرع {i}')
            to_cash = CashAccount(
                name=f'الفرع {i}',
                account_id=to_account.id,
                type='Subsidiary',
                parent_cash_id=general_cash.id,
                is_active=True,
                display_order=i+2
            )
            self.session.add(to_cash)
            self.session.flush()
            
            transfer = CashTransfer(
                from_cash_id=general_cash.id,
                to_cash_id=to_cash.id,
                amount=1000.0 * (i + 1),
                transfer_date=date.today(),
                description=f'تحويل {i}',
                status='Pending'
            )
            self.session.add(transfer)
        
        self.session.commit()
        
        # محاكاة receive_transfers الذي يجمع البيانات
        pending_transfers = self.session.query(CashTransfer).options(
            joinedload(CashTransfer.from_cash).joinedload(CashAccount.account),
            joinedload(CashTransfer.to_cash).joinedload(CashAccount.account)
        ).filter_by(status='Pending').order_by(CashTransfer.transfer_date.desc()).all()
        
        # محاكاة التجميع في قاموس (كما في receive_transfers)
        transfers_by_source = {}
        for transfer in pending_transfers:
            source_name = transfer.from_cash.name
            if source_name not in transfers_by_source:
                transfers_by_source[source_name] = {
                    'from_account': transfer.from_cash,
                    'transfers': [],
                    'total_amount': 0
                }
            transfers_by_source[source_name]['transfers'].append(transfer)
            transfers_by_source[source_name]['total_amount'] += transfer.amount
        
        # إغلاق الجلسة
        self.session.close()
        
        # محاكاة template access للبيانات المجمعة
        for source_name, group_data in transfers_by_source.items():
            # يجب أن نتمكن من الوصول لـ from_account.account
            self.assertIsNotNone(group_data['from_account'].account.code)
            self.assertIsNotNone(group_data['from_account'].account.name)
            
            # يجب أن نتمكن من الوصول لكل تحويل و to_cash.account
            for transfer in group_data['transfers']:
                self.assertIsNotNone(transfer.to_cash.account.code)
                self.assertIsNotNone(transfer.to_cash.account.name)


class TestEdgeCasesAndBoundaryConditions(unittest.TestCase):
    """
    اختبار الحالات الحدية والشروط الحدية
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
    
    def test_empty_result_set_with_eager_loading(self):
        """
        اختبار: استعلام بنتيجة فارغة مع eager loading
        """
        # استعلام خزائن بمعرف غير موجود
        cash_accounts = self.session.query(CashAccount).options(
            joinedload(CashAccount.account)
        ).filter(CashAccount.id == 999999).all()
        
        self.assertEqual(len(cash_accounts), 0)
        
        # إغلاق الجلسة
        self.session.close()
        
        # يجب أن تكون النتيجة فارغة بدون أخطاء
        self.assertEqual(len(cash_accounts), 0)
    
    def test_single_result_with_eager_loading(self):
        """
        اختبار: استعلام نتيجة واحدة مع eager loading
        """
        account = self._create_test_account('نتيجة واحدة')
        cash = CashAccount(
            name='خزينة واحدة',
            account_id=account.id,
            type='General',
            is_active=True,
            display_order=1
        )
        self.session.add(cash)
        self.session.commit()
        
        # استعلام نتيجة واحدة
        result = self.session.query(CashAccount).options(
            joinedload(CashAccount.account)
        ).filter(CashAccount.id == cash.id).first()
        
        self.assertIsNotNone(result)
        code = result.account.code
        
        # إغلاق الجلسة
        self.session.close()
        
        # يجب أن نتمكن من الوصول للبيانات
        self.assertEqual(result.account.code, code)
    
    def test_large_result_set_with_eager_loading(self):
        """
        اختبار: استعلام نتائج كثيرة مع eager loading
        """
        # إنشاء 50 خزينة
        for i in range(50):
            account = self._create_test_account(f'خزينة {i}')
            cash = CashAccount(
                name=f'خزينة {i}',
                account_id=account.id,
                type='General',
                is_active=True,
                display_order=i
            )
            self.session.add(cash)
        
        self.session.commit()
        
        # استعلام جميع الخزائن
        cash_accounts = self.session.query(CashAccount).options(
            joinedload(CashAccount.account)
        ).filter_by(is_active=True).order_by(CashAccount.display_order).all()
        
        self.assertGreaterEqual(len(cash_accounts), 50)
        
        # إغلاق الجلسة
        self.session.close()
        
        # يجب أن نتمكن من الوصول لجميع البيانات
        count = 0
        for cash in cash_accounts:
            self.assertIsNotNone(cash.account.code)
            count += 1
        
        self.assertGreaterEqual(count, 50)


if __name__ == '__main__':
    unittest.main()
