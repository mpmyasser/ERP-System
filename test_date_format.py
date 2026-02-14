#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
اختبار صيغة إدخال التواريخ
Testing Date Input Format (DD/MM/YYYY)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from utils.helpers import parse_date_compact
from datetime import date

def test_date_parsing():
    """اختبر صيغ إدخال التواريخ المختلفة"""
    
    print("=" * 70)
    print("🧪 اختبار صيغ إدخال التواريخ")
    print("=" * 70)
    
    test_cases = [
        # (input, expected_output, description)
        ("08/12/2025", date(2025, 12, 8), "DD/MM/YYYY مع علامات"),
        ("08122025", date(2025, 12, 8), "DDMMYYYY بدون علامات"),
        ("08-12-2025", date(2025, 12, 8), "DD-MM-YYYY بعلامات الشرطة"),
        ("1/1/2024", date(2024, 1, 1), "D/M/YYYY بدون أصفار"),
        ("31/12/2023", date(2023, 12, 31), "آخر يوم في السنة"),
        ("01/01/2000", date(2000, 1, 1), "أول يوم في السنة"),
        ("2025-12-08", date(2025, 12, 8), "YYYY-MM-DD (ISO format)"),
        # اختبارات خاطئة
        ("32/12/2025", None, "يوم غير صحيح (32)"),
        ("08/13/2025", None, "شهر غير صحيح (13)"),
        ("08/12/1899", None, "سنة قديمة جداً"),
        ("", None, "فارغ"),
        ("invalid", None, "نص غير صحيح"),
        ("12252025", None, "صيغة خاطئة (8 أرقام في ترتيب خاطئ)"),
    ]
    
    print("\n📋 نتائج الاختبارات:\n")
    
    passed = 0
    failed = 0
    
    for input_str, expected, description in test_cases:
        result = parse_date_compact(input_str)
        is_correct = result == expected
        status = "✅" if is_correct else "❌"
        
        if is_correct:
            passed += 1
        else:
            failed += 1
        
        expected_str = str(expected) if expected else "None"
        result_str = str(result) if result else "None"
        
        print(f"{status} {description}")
        print(f"   الإدخال: {input_str}")
        print(f"   المتوقع: {expected_str}")
        print(f"   النتيجة: {result_str}")
        print()
    
    # الملخص
    print("=" * 70)
    print(f"📊 النتائج: ✅ {passed} نجح | ❌ {failed} فشل | المجموع: {passed + failed}")
    print("=" * 70)
    
    print("\n📌 ملاحظات مهمة:")
    print("""
✅ الصيغ المقبولة:
   1. DD/MM/YYYY  (مثال: 08/12/2025)
   2. DDMMYYYY     (مثال: 08122025)
   3. DD-MM-YYYY   (مثال: 08-12-2025)
   4. D/M/YYYY     (مثال: 8/12/2025 - بدون أصفار)
   5. YYYY-MM-DD   (مثال: 2025-12-08 - ISO format)

✅ الترتيب دائماً: يوم / شهر / سنة
   • أول رقمين: اليوم (01-31)
   • الرقمين التاليين: الشهر (01-12)
   • آخر 4 أرقام: السنة (1900-2100)

✅ أمثلة صحيحة:
   • 1/1/2024      → يناير 1، 2024
   • 31/12/2025    → ديسمبر 31، 2025
   • 15/06/2023    → يونيو 15، 2023
   • 08122025      → ديسمبر 8، 2025

❌ أمثلة خاطئة:
   • 32/12/2025    → يوم غير صحيح
   • 08/13/2025    → شهر غير صحيح
   • 2025-08-12    → ترتيب خاطئ (سنة-يوم-شهر)
""")
    
    return failed == 0

if __name__ == '__main__':
    success = test_date_parsing()
    exit(0 if success else 1)
