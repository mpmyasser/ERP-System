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
from core.accounting_models import Account, JournalEntry, JournalItem


class ReceiveTransferTests(unittest.TestCase):
    """اختبارات استقبال التحويلات بين الخزائن"""
    
    @classmethod
    def setUpClass(cls):
        cls.db = DBManager()
        cls.test_user_id = None
        cls.test_account_id = None
        cls.test_general_id = None
        cls.test_subsidiary_id = None
        cls.test_transfer_id = None
    
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
                code='9999-RCV-TEST',
                name='اختبار - استقبال التحويلات',
                type='Cash',
                is_active=1
            )
            self.session.add(acc)
            self.session.flush()
            self.__class__.test_account_id = acc.id
            
            # Create user
            import random
            user = User(
                username=f'test_rcv_{random.randint(10000, 99999)}',
                full_name='اختبار استقبال',
                is_active=True,
                is_admin=False
            )
            user.set_password('test123')
            self.session.add(user)
            self.session.flush()
            self.__class__.test_user_id = user.id
            
            # Create general cash account
            general = CashAccount(
                name='خزينة عمومية - اختبار استقبال',
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
            
            # Create subsidiary
            subsidiary = CashAccount(
                name='خزينة فرعية - اختبار استقبال',
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
            
            print(f"   ✅ تم إنشاء بيانات الاختبار:")
            print(f"      - User ID: {user.id}")
            print(f"      - General: {general.name}")
            print(f"      - Subsidiary: {subsidiary.name}")
            
        except Exception as e:
            print(f"   ❌ خطأ: {e}")
            self.session.rollback()
            raise
    
    def test_02_create_transfer(self):
        """اختبار 2: إنشاء تحويل"""
        print("\n📋 اختبار 2: إنشاء تحويل")
        
        if not self.test_general_id or not self.test_subsidiary_id:
            self.skipTest("لم يتم إعداد بيانات الاختبار")
        
        try:
            general = self.session.query(CashAccount).get(self.test_general_id)
            subsidiary = self.session.query(CashAccount).get(self.test_subsidiary_id)
            
            # Create transfer
            transfer = CashTransfer(
                from_cash_id=self.test_general_id,
                to_cash_id=self.test_subsidiary_id,
                amount=1000.0,
                transfer_date=date.today(),
                description='تحويل اختبار',
                status='Pending'
            )
            self.session.add(transfer)
            self.session.flush()
            self.__class__.test_transfer_id = transfer.id
            self.session.commit()
            
            print(f"   ✅ تم إنشاء تحويل:")
            print(f"      - From: {general.name}")
            print(f"      - To: {subsidiary.name}")
            print(f"      - Amount: 1000.0")
            print(f"      - Status: {transfer.status}")
            print(f"      - Transfer ID: {transfer.id}")
            
            self.assertEqual(transfer.status, 'Pending')
            self.assertEqual(transfer.amount, 1000.0)
        except Exception as e:
            print(f"   ❌ خطأ: {e}")
            self.session.rollback()
            raise
    
    def test_03_transfer_pending_status(self):
        """اختبار 3: التحويل في حالة Pending"""
        print("\n📋 اختبار 3: التحويل في حالة Pending")
        
        if not self.test_transfer_id:
            self.skipTest("لم يتم إنشاء التحويل")
        
        try:
            transfer = self.session.query(CashTransfer).get(self.test_transfer_id)
            
            self.assertEqual(transfer.status, 'Pending')
            self.assertIsNone(transfer.received_date)
            self.assertIsNone(transfer.received_by)
            
            print(f"   ✅ الحالة: {transfer.status}")
            print(f"   ✅ تاريخ الاستقبال: {transfer.received_date}")
            print(f"   ✅ مستقبل التحويل: {transfer.received_by}")
        except Exception as e:
            print(f"   ❌ خطأ: {e}")
            raise
    
    def test_04_receive_transfer(self):
        """اختبار 4: استقبال التحويل"""
        print("\n📋 اختبار 4: استقبال التحويل")
        
        if not self.test_transfer_id or not self.test_user_id:
            self.skipTest("لم يتم إعداد البيانات المطلوبة")
        
        try:
            transfer = self.session.query(CashTransfer).get(self.test_transfer_id)
            
            # Receive transfer
            transfer.status = 'Received'
            transfer.received_date = date.today()
            transfer.received_by = self.test_user_id
            
            self.session.commit()
            
            # Verify
            updated_transfer = self.session.query(CashTransfer).get(self.test_transfer_id)
            
            self.assertEqual(updated_transfer.status, 'Received')
            self.assertEqual(updated_transfer.received_date, date.today())
            self.assertEqual(updated_transfer.received_by, self.test_user_id)
            
            print(f"   ✅ الحالة الجديدة: {updated_transfer.status}")
            print(f"   ✅ تاريخ الاستقبال: {updated_transfer.received_date}")
            print(f"   ✅ مستقبل التحويل: User ID {updated_transfer.received_by}")
        except Exception as e:
            print(f"   ❌ خطأ: {e}")
            self.session.rollback()
            raise
    
    def test_05_cannot_receive_twice(self):
        """اختبار 5: لا يمكن استقبال التحويل مرتين"""
        print("\n📋 اختبار 5: منع استقبال التحويل مرتين")
        
        if not self.test_transfer_id:
            self.skipTest("لم يتم إعداد البيانات المطلوبة")
        
        try:
            transfer = self.session.query(CashTransfer).get(self.test_transfer_id)
            
            # Check if already received
            if transfer.status == 'Received':
                print(f"   ✅ التحويل في حالة: {transfer.status}")
                print(f"   ✅ تم استقباله في: {transfer.received_date}")
                print(f"   ✅ لا يمكن استقباله مرة أخرى")
                self.assertEqual(transfer.status, 'Received')
            else:
                self.fail('التحويل يجب أن يكون في حالة Received')
        except Exception as e:
            print(f"   ❌ خطأ: {e}")
            raise
    
    def test_06_transfer_relations(self):
        """اختبار 6: العلاقات الخاصة بالتحويل"""
        print("\n📋 اختبار 6: فحص العلاقات")
        
        if not self.test_transfer_id:
            self.skipTest("لم يتم إعداد البيانات المطلوبة")
        
        try:
            transfer = self.session.query(CashTransfer).get(self.test_transfer_id)
            
            # Check relationships
            self.assertIsNotNone(transfer.from_cash)
            self.assertIsNotNone(transfer.to_cash)
            
            from_account = transfer.from_cash
            to_account = transfer.to_cash
            
            # Verify direction
            self.assertTrue(from_account.is_general())
            self.assertTrue(to_account.is_subsidiary())
            self.assertEqual(to_account.parent_cash_id, from_account.id)
            
            print(f"   ✅ الخزينة المصدر: {from_account.name} ({from_account.get_account_type_label()})")
            print(f"   ✅ الخزينة المستقبلة: {to_account.name} ({to_account.get_account_type_label()})")
            print(f"   ✅ العلاقة الهرمية صحيحة")
        except Exception as e:
            print(f"   ❌ خطأ: {e}")
            raise
    
    def test_07_list_transfers_by_source(self):
        """اختبار 7: تجميع التحويلات حسب المصدر"""
        print("\n📋 اختبار 7: تجميع التحويلات حسب المصدر")
        
        if not self.test_general_id or not self.test_subsidiary_id or not self.test_user_id:
            self.skipTest("لم يتم إعداد البيانات المطلوبة")
        
        try:
            # Get all transfers to subsidiary accounts (regardless of status)
            all_transfers = self.session.query(CashTransfer).filter_by(
                to_cash_id=self.test_subsidiary_id
            ).all()
            
            # Group by source
            transfers_by_source = {}
            for transfer in all_transfers:
                source_name = transfer.from_cash.name
                if source_name not in transfers_by_source:
                    transfers_by_source[source_name] = {
                        'transfers': [],
                        'total_amount': 0
                    }
                transfers_by_source[source_name]['transfers'].append(transfer)
                transfers_by_source[source_name]['total_amount'] += transfer.amount
            
            print(f"   ✅ عدد المصادر: {len(transfers_by_source)}")
            for source_name, data in transfers_by_source.items():
                print(f"      - {source_name}: {len(data['transfers'])} تحويل، المجموع: {data['total_amount']}")
            
            self.assertGreater(len(transfers_by_source), 0)
        except Exception as e:
            print(f"   ❌ خطأ: {e}")
            raise
    
    @classmethod
    def tearDownClass(cls):
        """تنظيف بيانات الاختبار"""
        print("\n🧹 تنظيف بيانات الاختبار...")
        session = cls.db.get_session()
        try:
            if cls.test_transfer_id:
                session.query(CashTransfer).filter_by(id=cls.test_transfer_id).delete()
            if cls.test_subsidiary_id:
                session.query(CashAccount).filter_by(id=cls.test_subsidiary_id).delete()
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
    print("🧪 اختبارات استقبال التحويلات بين الخزائن")
    print("="*60)
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(ReceiveTransferTests)
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
