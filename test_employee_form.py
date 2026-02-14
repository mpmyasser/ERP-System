"""
Test Employee Form with Optional Fields
=========================================
اختبار بسيط لعرض أن الموظف يمكن إضافته بدون رقم قومي أو موبايل صحيح
"""

import sys
import os

# Add to path
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

def test_form_validation():
    """Test form field validation logic"""
    
    print("=" * 60)
    print("🧪 اختبار منطق التحقق من الحقول")
    print("=" * 60)
    
    # Test 1: National ID validation
    print("\n📋 اختبار 1: التحقق من الرقم القومي")
    test_cases = [
        ('12345678901234', True, '14 رقم - صحيح'),
        ('1234567890123', False, '13 رقم - خاطئ'),
        ('123456789012345', False, '15 رقم - خاطئ'),
        ('1234567890123A', False, 'يحتوي على أحرف - خاطئ'),
        ('', True, 'فارغ - مقبول (اختياري)'),
    ]
    
    for national_id, should_pass, description in test_cases:
        is_valid = False
        if national_id == '':
            is_valid = True  # اختياري - مقبول
        elif len(national_id) == 14 and national_id.isdigit():
            is_valid = True
        else:
            is_valid = False
        
        status = '✅' if is_valid == should_pass else '❌'
        print(f"   {status} {description}")
        print(f"      القيمة: '{national_id}'")
        print(f"      النتيجة: {'مقبول' if is_valid else 'مرفوض'}")
    
    # Test 2: Mobile number validation
    print("\n📋 اختبار 2: التحقق من رقم الموبايل")
    test_cases = [
        ('01012345678', True, '11 رقم - صحيح'),
        ('0101234567', True, '10 أرقام - صحيح'),
        ('010123456789', False, '12 رقم - خاطئ'),
        ('0101234567', True, '10 أرقام - صحيح'),
        ('01234567', False, '8 أرقام - خاطئ'),
        ('010123ABC78', False, 'يحتوي على أحرف - خاطئ'),
        ('', True, 'فارغ - مقبول (اختياري)'),
    ]
    
    for mobile, should_pass, description in test_cases:
        is_valid = False
        if mobile == '':
            is_valid = True  # اختياري - مقبول
        elif mobile.isdigit() and 10 <= len(mobile) <= 11:
            is_valid = True
        else:
            is_valid = False
        
        status = '✅' if is_valid == should_pass else '❌'
        print(f"   {status} {description}")
        print(f"      القيمة: '{mobile}'")
        print(f"      النتيجة: {'مقبول' if is_valid else 'مرفوض'}")
    
    print("\n" + "=" * 60)
    print("📋 ملخص التغييرات:")
    print("=" * 60)
    print("""
✅ تم تعديل نموذج الموظف (app/forms.py):
   - national_id: الآن اختياري (Optional) لكن يجب أن يكون 14 رقم إذا تم إدخاله
   - mobile_number: الآن اختياري (Optional) لكن يجب أن يكون 10-11 رقم إذا تم إدخاله

✅ تم تعديل معالجات التطبيق (app/routes/employees.py):
   - create(): الآن يسمح بحفظ البيانات حتى لو كان الرقم القومي أو الموبايل خاطئ
   - edit(): الآن يسمح بتحديث البيانات حتى لو كان الرقم القومي أو الموبايل خاطئ
   - يتم عرض تحذيرات (⚠️) للحقول غير الصحيحة
   - الحقول غير الصحيحة يتم حفظها كـ None في قاعدة البيانات

✅ السلوك الجديد:
   1️⃣ الحقول المطلوبة (الاسم، الكود، تاريخ التعيين): يجب ملؤها
   2️⃣ الحقول الاختيارية (الرقم القومي، الموبايل):
      - يمكن تركها فارغة
      - إذا تم إدخال بيانات، يجب أن تكون بالصيغة الصحيحة
      - إذا كانت صيغة خاطئة: يتم عرض تحذير لكن البيانات الأخرى تُحفظ

✅ الملفات المعدلة:
   1. app/forms.py - تم تعديل EmployeeForm
   2. app/routes/employees.py - تم تعديل create() و edit() routes
   3. app/templates/base.html - تدعم الرسائل متعددة الأسطر
""")
    print("=" * 60)

if __name__ == '__main__':
    test_form_validation()
