#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick verification script for date filtering fixes
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

print("=" * 70)
print("🔍 التحقق من إصلاحات معالجة التواريخ")
print("=" * 70)

# 1. Check parse_date_compact exists
print("\n✓ اختبار 1: التحقق من وجود دالة parse_date_compact")
try:
    from utils.helpers import parse_date_compact
    print("  ✅ تم العثور على parse_date_compact في core/utils/helpers.py")
except ImportError as e:
    print(f"  ❌ فشل: {e}")
    sys.exit(1)

# 2. Test parse_date_compact function
print("\n✓ اختبار 2: اختبار تحويل التواريخ")
test_cases = [
    ("25/11/2025", "2025-11-25"),
    ("24/12/2025", "2025-12-24"),
    ("01/01/2025", "2025-01-01"),
    ("31/12/2024", "2024-12-31"),
]

all_passed = True
for input_date, expected in test_cases:
    result = parse_date_compact(input_date)
    expected_date_str = str(result)
    status = "✅" if expected_date_str == expected else "❌"
    print(f"  {status} {input_date:12} → {result}")
    if expected_date_str != expected:
        all_passed = False

if not all_passed:
    print("  ❌ فشلت بعض التحويلات!")
    sys.exit(1)

# 3. Check db_manager.py imports
print("\n✓ اختبار 3: التحقق من db_manager.py")
try:
    from db_manager import DBManager
    print("  ✅ تم تحميل DBManager بنجاح")
    
    # Check if search_loans uses parse_date_compact
    import inspect
    source = inspect.getsource(DBManager.search_loans)
    if "parse_date_compact" in source:
        print("  ✅ search_loans() تستخدم parse_date_compact")
    else:
        print("  ❌ search_loans() لا تستخدم parse_date_compact!")
        all_passed = False
        
except Exception as e:
    print(f"  ❌ خطأ: {e}")
    all_passed = False

# 4. Check routes files
print("\n✓ اختبار 4: التحقق من ملفات الـ Routes")
routes_files = [
    "app/routes/bonuses.py",
    "app/routes/penalties.py",
    "app/routes/permissions.py",
    "app/routes/leaves.py",
    "app/routes/loans.py",
    "app/routes/reports.py",
]

for file_path in routes_files:
    full_path = os.path.join(os.path.dirname(__file__), file_path)
    if os.path.exists(full_path):
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if "parse_date_compact" in content or "search_loans" in content:
                print(f"  ✅ {file_path} - معالجة التواريخ موجودة")
            else:
                print(f"  ⚠️  {file_path} - قد لا تحتوي على معالجة تواريخ")
    else:
        print(f"  ⚠️  {file_path} - الملف غير موجود")

# 5. Summary
print("\n" + "=" * 70)
if all_passed:
    print("✅ جميع الاختبارات نجحت! البحث جاهز للعمل.")
else:
    print("❌ بعض الاختبارات فشلت. يرجى مراجعة النتائج أعلاه.")
    sys.exit(1)

print("=" * 70)
