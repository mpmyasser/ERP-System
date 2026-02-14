#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import sys
import os
from datetime import datetime, date

if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.db_manager import DBManager
from core.treasury_models import CashAccount, CashTransfer
from core.auth_models import User
from core.accounting_models import Account, JournalEntry


class TransferDirectionTests(unittest.TestCase):
    """اختبارات صحة اتجاه التحويلات بين الخزائن"""
    
    @classmethod
    def setUpClass(cls):
        cls.db = DBManager()
        cls.test_user_id = None
        cls.test_account_id = None
        cls.test_general_id = None
        cls.test_subsidiary1_id = None
        cls.test_subsidiary2_id = None
    
    def setUp(self):
        self.session = self.db.get_session()
    
    def tearDown(self):
        if self.session:
            self.session.close()
    
    def test_01_setup_test_data(self):
        """اختبار 1: إعداد بيانات الاختبار"""
        print("\n📋 اختبار 1: إعداد بيانات الاختبار")
        
        try:
            # Create account
            acc = Account(
                code='9999-DIR-TEST',
                name='اختبار - توجيه التحويلات',
                type='Cash',
                is_active=1
            )
            self.session.add(acc)
            self.session.flush()
            self.__class__.test_account_id = acc.id
            
            # Create user
            import random
            user = User(
                username=f'test_dir_{random.randint(10000, 99999)}',
                full_name='اختبار توجيه',
                is_active=True,
                is_admin=False
            )
            user.set_password('test123')
            self.session.add(user)
            self.session.flush()
            self.__class__.test_user_id = user.id
            
            # Create general cash account
            general = CashAccount(
                name='خزينة عمومية - اختبار توجيه',
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
            
            # Create subsidiary 1
            subsidiary1 = CashAccount(
                name='خزينة فرعية 1 - اختبار توجيه',
                account_id=self.test_account_id,
                type='Subsidiary',
                parent_cash_id=self.test_general_id,
                user_id=self.test_user_id,
                is_active=True,
                display_order=2
            )
            self.session.add(subsidiary1)
            self.session.flush()
            self.__class__.test_subsidiary1_id = subsidiary1.id
            
            # Create subsidiary 2
            subsidiary2 = CashAccount(
                name='خزينة فرعية 2 - اختبار توجيه',
                account_id=self.test_account_id,
                type='Subsidiary',
                parent_cash_id=self.test_general_id,
                user_id=self.test_user_id,
                is_active=True,
                display_order=3
            )
            self.session.add(subsidiary2)
            self.session.flush()
            self.__class__.test_subsidiary2_id = subsidiary2.id
            
            self.session.commit()
            
            print(f"   ✅ تم إنشاء بيانات الاختبار:")
            print(f"      - General: {general.name} (ID: {general.id})")
            print(f"      - Subsidiary 1: {subsidiary1.name} (ID: {subsidiary1.id})")
            print(f"      - Subsidiary 2: {subsidiary2.name} (ID: {subsidiary2.id})")
            
        except Exception as e:
            print(f"   ❌ خطأ: {e}")
            self.session.rollback()
            raise
    
    def test_02_general_to_subsidiary_allowed(self):
        """اختبار 2: التحويل من عمومية → فرعية مسموح"""
        print("\n📋 اختبار 2: التحويل من عمومية → فرعية (مسموح)")
        
        if not self.test_general_id or not self.test_subsidiary1_id:
            self.skipTest("لم يتم إعداد بيانات الاختبار")
        
        try:
            general = self.session.query(CashAccount).get(self.test_general_id)
            subsidiary = self.session.query(CashAccount).get(self.test_subsidiary1_id)
            
            # Check conditions
            self.assertTrue(general.is_general())
            self.assertTrue(subsidiary.is_subsidiary())
            self.assertEqual(subsidiary.parent_cash_id, general.id)
            
            # This transfer should be allowed
            allow_transfer = (
                general.is_general() and 
                subsidiary.is_subsidiary() and 
                subsidiary.parent_cash_id == general.id
            )
            
            print(f"   ✅ من: {general.name} ({general.get_account_type_label()})")
            print(f"   ✅ إلى: {subsidiary.name} ({subsidiary.get_account_type_label()})")
            print(f"   ✅ التحويل مسموح: {allow_transfer}")
            
            self.assertTrue(allow_transfer)
        except Exception as e:
            print(f"   ❌ خطأ: {e}")
            raise
    
    def test_03_subsidiary_to_subsidiary_rejected(self):
        """اختبار 3: التحويل من فرعية → فرعية غير مسموح"""
        print("\n📋 اختبار 3: التحويل من فرعية → فرعية (غير مسموح)")
        
        if not self.test_subsidiary1_id or not self.test_subsidiary2_id:
            self.skipTest("لم يتم إعداد بيانات الاختبار")
        
        try:
            subsidiary1 = self.session.query(CashAccount).get(self.test_subsidiary1_id)
            subsidiary2 = self.session.query(CashAccount).get(self.test_subsidiary2_id)
            
            # Check conditions
            self.assertTrue(subsidiary1.is_subsidiary())
            self.assertTrue(subsidiary2.is_subsidiary())
            
            # This transfer should be REJECTED
            allow_transfer = not (subsidiary1.is_subsidiary() and subsidiary2.is_subsidiary())
            
            print(f"   ❌ من: {subsidiary1.name} ({subsidiary1.get_account_type_label()})")
            print(f"   ❌ إلى: {subsidiary2.name} ({subsidiary2.get_account_type_label()})")
            print(f"   ✅ التحويل مرفوض: {not allow_transfer}")
            
            self.assertFalse(allow_transfer)
        except Exception as e:
            print(f"   ❌ خطأ: {e}")
            raise
    
    def test_04_subsidiary_to_general_rejected(self):
        """اختبار 4: التحويل من فرعية → عمومية غير مسموح"""
        print("\n📋 اختبار 4: التحويل من فرعية → عمومية (غير مسموح)")
        
        if not self.test_general_id or not self.test_subsidiary1_id:
            self.skipTest("لم يتم إعداد بيانات الاختبار")
        
        try:
            general = self.session.query(CashAccount).get(self.test_general_id)
            subsidiary = self.session.query(CashAccount).get(self.test_subsidiary1_id)
            
            # Check conditions
            self.assertTrue(general.is_general())
            self.assertTrue(subsidiary.is_subsidiary())
            
            # This transfer should be REJECTED
            allow_transfer = not (subsidiary.is_subsidiary() and general.is_general())
            
            print(f"   ❌ من: {subsidiary.name} ({subsidiary.get_account_type_label()})")
            print(f"   ❌ إلى: {general.name} ({general.get_account_type_label()})")
            print(f"   ✅ التحويل مرفوض: {not allow_transfer}")
            
            self.assertFalse(allow_transfer)
        except Exception as e:
            print(f"   ❌ خطأ: {e}")
            raise
    
    def test_05_general_to_general_rejected(self):
        """اختبار 5: التحويل من عمومية → عمومية غير مسموح"""
        print("\n📋 اختبار 5: التحويل من عمومية → عمومية (غير مسموح)")
        
        if not self.test_account_id or not self.test_user_id:
            self.skipTest("لم يتم إعداد بيانات الاختبار")
        
        try:
            # Create another general account
            general2 = CashAccount(
                name='خزينة عمومية أخرى - اختبار',
                account_id=self.test_account_id,
                type='General',
                parent_cash_id=None,
                user_id=self.test_user_id,
                is_active=True,
                display_order=4
            )
            self.session.add(general2)
            self.session.flush()
            general2_id = general2.id
            
            general1 = self.session.query(CashAccount).get(self.test_general_id)
            
            # Check conditions
            self.assertTrue(general1.is_general())
            self.assertTrue(general2.is_general())
            
            # This transfer should be REJECTED
            allow_transfer = not (general1.is_general() and general2.is_general())
            
            print(f"   ❌ من: {general1.name} ({general1.get_account_type_label()})")
            print(f"   ❌ إلى: {general2.name} ({general2.get_account_type_label()})")
            print(f"   ✅ التحويل مرفوض: {not allow_transfer}")
            
            self.assertFalse(allow_transfer)
            
            # Cleanup
            self.session.delete(general2)
            self.session.commit()
        except Exception as e:
            print(f"   ❌ خطأ: {e}")
            self.session.rollback()
            raise
    
    def test_06_parent_child_validation(self):
        """اختبار 6: التحقق من العلاقة الأب-الابن"""
        print("\n📋 اختبار 6: التحقق من العلاقة الأب-الابن")
        
        if not self.test_general_id or not self.test_subsidiary1_id:
            self.skipTest("لم يتم إعداد بيانات الاختبار")
        
        try:
            general = self.session.query(CashAccount).get(self.test_general_id)
            subsidiary = self.session.query(CashAccount).get(self.test_subsidiary1_id)
            
            # Valid: Child should have parent_id pointing to parent
            self.assertEqual(subsidiary.parent_cash_id, general.id)
            
            # Valid: Parent should have None for parent_cash_id
            self.assertIsNone(general.parent_cash_id)
            
            # Valid: Parent should have subsidiary in its backref
            self.assertIn(subsidiary, general.subsidiaries)
            
            print(f"   ✅ {general.name} (parent_id=None)")
            print(f"   ✅ {subsidiary.name} (parent_id={subsidiary.parent_cash_id})")
            print(f"   ✅ العلاقة صحيحة: subsidiary in general.subsidiaries")
        except Exception as e:
            print(f"   ❌ خطأ: {e}")
            raise
    
    @classmethod
    def tearDownClass(cls):
        """تنظيف بيانات الاختبار"""
        print("\n🧹 تنظيف بيانات الاختبار...")
        session = cls.db.get_session()
        try:
            if cls.test_subsidiary1_id:
                session.query(CashAccount).filter_by(id=cls.test_subsidiary1_id).delete()
            if cls.test_subsidiary2_id:
                session.query(CashAccount).filter_by(id=cls.test_subsidiary2_id).delete()
            if cls.test_general_id:
                session.query(CashAccount).filter_by(id=cls.test_general_id).delete()
            if cls.test_user_id:
                session.query(User).filter_by(id=cls.test_user_id).delete()
            if cls.test_account_id:
                session.query(Account).filter_by(id=cls.test_account_id).delete()
            session.commit()
            print("   ✅ تم تنظيف البيانات")
        except Exception as e:
            print(f"   ⚠️ خطأ في التنظيف: {e}")
            session.rollback()
        finally:
            session.close()


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🧪 اختبارات توجيه التحويلات بين الخزائن")
    print("="*60)
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TransferDirectionTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*60)
    if result.wasSuccessful():
        print("✅ جميع الاختبارات نجحت!")
    else:
        print(f"❌ فشلت {len(result.failures)} اختبارات")
        print(f"❌ أخطاء: {len(result.errors)}")
    print("="*60)
    
    sys.exit(0 if result.wasSuccessful() else 1)
