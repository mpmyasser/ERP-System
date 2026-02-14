#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import sys
import os
import sqlite3
from datetime import datetime, date

if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.db_manager import DBManager
from core.treasury_models import CashAccount, BankAccount
from core.auth_models import User, SystemPermission
from core.accounting_models import Account


class TreasuryFilteringTests(unittest.TestCase):
    """اختبارات فصل الحسابات حسب النوع"""
    
    @classmethod
    def setUpClass(cls):
        cls.db = DBManager()
        cls.test_user_id = None
        cls.test_general_account_id = None
        cls.test_subsidiary_account_id = None
        cls.test_account_id = None
    
    def setUp(self):
        """إعداد قاعدة البيانات قبل كل اختبار"""
        self.session = self.db.get_session()
    
    def tearDown(self):
        """تنظيف بعد كل اختبار"""
        if self.session:
            self.session.close()
    
    def test_01_create_test_account(self):
        """اختبار 1: إنشاء حساب اختبار"""
        print("\n📋 اختبار 1: إنشاء حساب اختبار في شجرة الحسابات")
        
        try:
            acc = Account(
                code='9999-TEST-001',
                name='اختبار - خزينة عمومية',
                type='Cash',
                is_active=1
            )
            self.session.add(acc)
            self.session.flush()
            self.__class__.test_account_id = acc.id
            self.session.commit()
            print(f"   ✅ تم إنشاء حساب اختبار برقم {acc.id}")
            self.assertIsNotNone(self.__class__.test_account_id)
        except Exception as e:
            print(f"   ❌ خطأ: {e}")
            self.session.rollback()
            raise
    
    def test_02_create_test_user(self):
        """اختبار 2: إنشاء مستخدم اختبار"""
        print("\n📋 اختبار 2: إنشاء مستخدم اختبار (مدير مالي)")
        
        import random
        try:
            user = User(
                username=f'test_financial_manager_{random.randint(10000, 99999)}',
                full_name='مدير مالي اختبار',
                is_active=True,
                is_admin=False
            )
            user.set_password('test123')
            self.session.add(user)
            self.session.flush()
            self.__class__.test_user_id = user.id
            self.session.commit()
            print(f"   ✅ تم إنشاء مستخدم اختبار برقم {user.id}")
            self.assertIsNotNone(self.__class__.test_user_id)
        except Exception as e:
            print(f"   ❌ خطأ: {e}")
            self.session.rollback()
            raise
    
    def test_03_create_general_cash_account(self):
        """اختبار 3: إنشاء خزينة عمومية"""
        print("\n📋 اختبار 3: إنشاء خزينة عمومية (بدون أم)")
        
        if not self.test_account_id or not self.test_user_id:
            self.skipTest("لم يتم إنشاء الحساب أو المستخدم")
        
        try:
            general = CashAccount(
                name='خزينة عمومية اختبار',
                account_id=self.test_account_id,
                type='General',
                parent_cash_id=None,
                user_id=self.test_user_id,
                is_active=True,
                display_order=1
            )
            self.session.add(general)
            self.session.flush()
            self.__class__.test_general_account_id = general.id
            self.session.commit()
            
            # التحقق من الخصائص
            self.assertTrue(general.is_general())
            self.assertFalse(general.is_subsidiary())
            self.assertEqual(general.get_account_type_label(), 'عمومية')
            
            print(f"   ✅ تم إنشاء خزينة عمومية برقم {general.id}")
            print(f"   ✅ is_general() = {general.is_general()}")
            print(f"   ✅ is_subsidiary() = {general.is_subsidiary()}")
            print(f"   ✅ get_account_type_label() = {general.get_account_type_label()}")
        except Exception as e:
            print(f"   ❌ خطأ: {e}")
            self.session.rollback()
            raise
    
    def test_04_create_subsidiary_cash_account(self):
        """اختبار 4: إنشاء خزينة فرعية (تابعة للعمومية)"""
        print("\n📋 اختبار 4: إنشاء خزينة فرعية")
        
        if not self.test_account_id or not self.test_user_id or not self.test_general_account_id:
            self.skipTest("لم يتم إنشاء الحسابات المطلوبة")
        
        try:
            subsidiary = CashAccount(
                name='خزينة فرعية اختبار',
                account_id=self.test_account_id,
                type='Subsidiary',
                parent_cash_id=self.test_general_account_id,
                user_id=self.test_user_id,
                is_active=True,
                display_order=2
            )
            self.session.add(subsidiary)
            self.session.flush()
            self.__class__.test_subsidiary_account_id = subsidiary.id
            self.session.commit()
            
            # التحقق من الخصائص
            self.assertFalse(subsidiary.is_general())
            self.assertTrue(subsidiary.is_subsidiary())
            self.assertEqual(subsidiary.get_account_type_label(), 'فرعية')
            self.assertEqual(subsidiary.parent_cash_id, self.test_general_account_id)
            
            print(f"   ✅ تم إنشاء خزينة فرعية برقم {subsidiary.id}")
            print(f"   ✅ is_general() = {subsidiary.is_general()}")
            print(f"   ✅ is_subsidiary() = {subsidiary.is_subsidiary()}")
            print(f"   ✅ get_account_type_label() = {subsidiary.get_account_type_label()}")
            print(f"   ✅ parent_cash_id = {subsidiary.parent_cash_id}")
        except Exception as e:
            print(f"   ❌ خطأ: {e}")
            self.session.rollback()
            raise
    
    def test_05_query_general_accounts(self):
        """اختبار 5: استعلام الخزائن العمومية فقط"""
        print("\n📋 اختبار 5: استعلام الخزائن العمومية")
        
        try:
            all_accounts = self.session.query(CashAccount).filter_by(is_active=True).all()
            general_accounts = [c for c in all_accounts if c.is_general()]
            
            print(f"   ✅ عدد الخزائن الكلي: {len(all_accounts)}")
            print(f"   ✅ عدد الخزائن العمومية: {len(general_accounts)}")
            
            for acc in general_accounts:
                print(f"      - {acc.name} (ID: {acc.id})")
            
            self.assertGreater(len(general_accounts), 0)
            for acc in general_accounts:
                self.assertTrue(acc.is_general())
        except Exception as e:
            print(f"   ❌ خطأ: {e}")
            raise
    
    def test_06_query_subsidiary_accounts(self):
        """اختبار 6: استعلام الخزائن الفرعية فقط"""
        print("\n📋 اختبار 6: استعلام الخزائن الفرعية")
        
        try:
            all_accounts = self.session.query(CashAccount).filter_by(is_active=True).all()
            subsidiary_accounts = [c for c in all_accounts if c.is_subsidiary()]
            
            print(f"   ✅ عدد الخزائن الفرعية: {len(subsidiary_accounts)}")
            
            for acc in subsidiary_accounts:
                print(f"      - {acc.name} (ID: {acc.id}, Parent: {acc.parent_cash_id})")
            
            if subsidiary_accounts:
                for acc in subsidiary_accounts:
                    self.assertTrue(acc.is_subsidiary())
        except Exception as e:
            print(f"   ❌ خطأ: {e}")
            raise
    
    def test_07_hierarchy_relationship(self):
        """اختبار 7: العلاقة الهرمية بين الخزائن"""
        print("\n📋 اختبار 7: فحص العلاقة الهرمية")
        
        if not self.test_general_account_id or not self.test_subsidiary_account_id:
            self.skipTest("لم يتم إنشاء الخزائن المطلوبة")
        
        try:
            general = self.session.query(CashAccount).get(self.test_general_account_id)
            subsidiary = self.session.query(CashAccount).get(self.test_subsidiary_account_id)
            
            # التحقق من العلاقة
            self.assertIsNotNone(general)
            self.assertIsNotNone(subsidiary)
            self.assertEqual(subsidiary.parent_cash_id, general.id)
            
            print(f"   ✅ العمومية: {general.name}")
            print(f"   ✅ الفرعية: {subsidiary.name}")
            print(f"   ✅ العلاقة: {subsidiary.name} تابعة لـ {general.name}")
            
            # التحقق من backref
            self.assertIn(subsidiary, general.subsidiaries)
            print(f"   ✅ Backref: عدد الخزائن الفرعية = {len(general.subsidiaries)}")
        except Exception as e:
            print(f"   ❌ خطأ: {e}")
            raise
    
    def test_08_user_assigned_accounts(self):
        """اختبار 8: استعلام الخزائن المخصصة للمستخدم"""
        print("\n📋 اختبار 8: استعلام الخزائن المخصصة للمستخدم")
        
        if not self.test_user_id:
            self.skipTest("لم يتم إنشاء مستخدم اختبار")
        
        try:
            user_accounts = self.session.query(CashAccount).filter_by(
                user_id=self.test_user_id,
                is_active=True
            ).all()
            
            print(f"   ✅ عدد الخزائن المخصصة للمستخدم {self.test_user_id}: {len(user_accounts)}")
            
            for acc in user_accounts:
                print(f"      - {acc.name} ({acc.get_account_type_label()})")
            
            self.assertGreater(len(user_accounts), 0)
            for acc in user_accounts:
                self.assertEqual(acc.user_id, self.test_user_id)
        except Exception as e:
            print(f"   ❌ خطأ: {e}")
            raise
    
    @classmethod
    def tearDownClass(cls):
        """تنظيف البيانات بعد الانتهاء من جميع الاختبارات"""
        print("\n🧹 تنظيف بيانات الاختبار...")
        session = cls.db.get_session()
        try:
            if cls.test_subsidiary_account_id:
                session.query(CashAccount).filter_by(id=cls.test_subsidiary_account_id).delete()
            if cls.test_general_account_id:
                session.query(CashAccount).filter_by(id=cls.test_general_account_id).delete()
            if cls.test_user_id:
                session.query(User).filter_by(id=cls.test_user_id).delete()
            if cls.test_account_id:
                session.query(Account).filter_by(id=cls.test_account_id).delete()
            session.commit()
            print("   ✅ تم تنظيف البيانات")
        except Exception as e:
            print(f"   ⚠️ خطأ في التنظيف: {e}")
        finally:
            session.close()


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🧪 اختبارات فصل الخزائن حسب النوع")
    print("="*60)
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TreasuryFilteringTests)
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
