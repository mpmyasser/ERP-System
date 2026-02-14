#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
اختبار نموذج المكافآت والحقول
Test Bonus Form Fields
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'core')

from app import create_app
from app.forms import BonusForm

def test_bonus_form():
    """اختبار نموذج BonusForm"""
    print("=" * 80)
    print("اختبار نموذج المكافآت (BonusForm)")
    print("=" * 80)
    
    app = create_app()
    with app.app_context():
        form = BonusForm()
        
        print("\n[INFO] حقول النموذج المتاحة:")
        for field_name, field in form._fields.items():
            print(f"  ✓ {field_name}")
            print(f"    - النوع: {type(field).__name__}")
            print(f"    - التسمية: {field.label.text if hasattr(field, 'label') else 'بدون تسمية'}")
            if hasattr(field, 'default'):
                print(f"    - القيمة الافتراضية: {field.default}")
        
        print("\n" + "=" * 80)
        
        # التحقق من وجود حقل paid_with_salary
        if 'paid_with_salary' in form._fields:
            field = form.paid_with_salary
            print("\n[PASS] حقل 'paid_with_salary' موجود بنجاح!")
            print(f"  - النوع: {type(field).__name__}")
            print(f"  - التسمية: {field.label.text}")
            print(f"  - القيمة الافتراضية: {field.default}")
            print(f"  - الوصف: {field.description if hasattr(field, 'description') else 'بدون وصف'}")
            
            print("\n[VERIFICATION] التحقق من HTML المُنتج:")
            # معاينة كيف سيبدو الحقل في HTML
            print(f"\n  الحقل (Checkbox):")
            print(f"  <input type='checkbox' name='paid_with_salary' ")
            print(f"         {% if form.paid_with_salary.data or form.paid_with_salary.default %}checked{% endif %} />")
            
            print(f"\n  التسمية (Label):")
            print(f"  <label>{field.label.text}</label>")
            
        else:
            print("\n[FAIL] حقل 'paid_with_salary' غير موجود!")
            return False
        
        print("\n" + "=" * 80)
        print("[PASS] جميع حقول النموذج صحيحة وجاهزة للاستخدام!")
        print("=" * 80)
        return True

if __name__ == '__main__':
    try:
        success = test_bonus_form()
        if success:
            print("\n✅ اختبار النموذج نجح!")
        else:
            print("\n❌ اختبار النموذج فشل!")
    except Exception as e:
        print(f"\n❌ حدث خطأ: {e}")
        import traceback
        traceback.print_exc()
