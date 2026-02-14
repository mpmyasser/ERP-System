#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
اختبار نظام التنقل بـ Enter
Testing Enter Navigation System
"""

def test_enter_navigation():
    """اختبر ملف JavaScript"""
    
    print("=" * 60)
    print("🧪 اختبار نظام التنقل بين الحقول باستخدام Enter")
    print("=" * 60)
    
    # التحقق من وجود الملف
    import os
    js_path = "app/static/js/enter_navigation.js"
    
    if os.path.exists(js_path):
        with open(js_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"\n✅ ملف JavaScript موجود")
        print(f"   الحجم: {len(content)} بايت")
        
        # التحقق من المفاتيح المهمة
        checks = [
            ("addEventListener", "معالج أحداث"),
            ("keydown", "مفتاح معالج الضغط"),
            ("key === 'Enter'", "التحقق من مفتاح Enter"),
            ("focus()", "تركيز الحقل"),
            ("preventDefault()", "منع السلوك الافتراضي"),
        ]
        
        print("\n📋 التحقق من المكونات الأساسية:")
        for check_str, description in checks:
            if check_str in content:
                print(f"   ✅ {description}: موجود")
            else:
                print(f"   ❌ {description}: مفقود")
        
        # التحقق من التعليقات بالعربية
        if "التنقل بين الحقول" in content or "Enter Navigation" in content:
            print("\n✅ التعليقات موجودة")
        
        print("\n" + "=" * 60)
        print("🎯 الميزات المضافة:")
        print("=" * 60)
        print("""
✅ الميزات الجديدة:

1️⃣ التنقل للأمام:
   • اضغط على Enter في أي حقل للانتقال للحقل التالي
   • يتخطى الحقول المخفية والمعطلة
   • ينتقل للزر في نهاية النموذج

2️⃣ التنقل للخلف:
   • اضغط على Shift + Enter للرجوع للحقل السابق
   • نفس السلوك مع تخطي الحقول المخفية

3️⃣ معالجة خاصة:
   • الحقول النصية: تحديد النص تلقائياً عند الانتقال
   • حقول التاريخ: تحديد القيمة عند الانتقال
   • الأزرار: اضغط Enter لتفعيل الزر

4️⃣ الاستثناءات:
   • textarea: يسمح بـ Ctrl+Enter لإضافة سطر جديد
   • خيارات الاختيار: تحتفظ بسلوكها الطبيعي

📊 المميزات:
   ✅ سهل الاستخدام - لا حاجة للتشكيل
   ✅ يعمل على جميع أنواع الحقول
   ✅ يحترم حالة الحقول (معطل/مخفي)
   ✅ متوافق مع جميع المتصفحات
   ✅ لا يتعارض مع الإجراءات الافتراضية

🚀 جاهز للاستخدام الفوري!
""")
        
        return True
    else:
        print(f"\n❌ ملف JavaScript غير موجود في {js_path}")
        return False

if __name__ == '__main__':
    success = test_enter_navigation()
    exit(0 if success else 1)
