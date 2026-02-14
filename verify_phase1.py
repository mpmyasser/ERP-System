#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import sqlite3
import os

if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("\n" + "="*60)
print("✅ اختبار Phase 1: Database Migration & Error Fix")
print("="*60 + "\n")

db_path = 'core/hr.db'

if not os.path.exists(db_path):
    print(f"❌ قاعدة البيانات غير موجودة: {db_path}")
    sys.exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("📋 فحص أعمدة جدول cash_accounts:")
cursor.execute("PRAGMA table_info(cash_accounts)")
columns = {row[1]: row[2] for row in cursor.fetchall()}

required_columns = {
    'id': 'INTEGER',
    'name': 'VARCHAR(100)',
    'account_id': 'INTEGER',
    'type': 'VARCHAR(20)',
    'parent_cash_id': 'INTEGER',
    'user_id': 'INTEGER',
    'is_active': 'BOOLEAN',
    'display_order': 'INTEGER'
}

all_ok = True
for col_name, col_type in required_columns.items():
    if col_name in columns:
        print(f"   ✅ {col_name}")
    else:
        print(f"   ❌ {col_name} (مفقود)")
        all_ok = False

conn.close()

print("\n📦 فحص نموذج CashAccount:")
try:
    from core.treasury_models import CashAccount
    print("   ✅ تم تحميل CashAccount")
    
    ca = CashAccount()
    
    if hasattr(ca, 'parent_cash_id'):
        print("   ✅ خاصية parent_cash_id موجودة")
    else:
        print("   ❌ خاصية parent_cash_id مفقودة")
        all_ok = False
    
    if hasattr(ca, 'is_general'):
        print("   ✅ دالة is_general() موجودة")
    else:
        print("   ❌ دالة is_general() مفقودة")
        all_ok = False
    
    if hasattr(ca, 'is_subsidiary'):
        print("   ✅ دالة is_subsidiary() موجودة")
    else:
        print("   ❌ دالة is_subsidiary() مفقودة")
        all_ok = False
        
    if hasattr(ca, 'get_account_type_label'):
        print("   ✅ دالة get_account_type_label() موجودة")
    else:
        print("   ❌ دالة get_account_type_label() مفقودة")
        all_ok = False
        
except Exception as e:
    print(f"   ❌ خطأ في تحميل CashAccount: {e}")
    all_ok = False

print("\n🔧 فحص مسار dashboard في treasury.py:")
try:
    from app.routes.treasury import treasury_bp
    print("   ✅ تم تحميل treasury blueprint")
except Exception as e:
    print(f"   ❌ خطأ في تحميل treasury blueprint: {e}")
    all_ok = False

print("\n" + "="*60)
if all_ok:
    print("✅ جميع الاختبارات نجحت!")
    print("="*60)
    sys.exit(0)
else:
    print("❌ بعض الاختبارات فشلت")
    print("="*60)
    sys.exit(1)
