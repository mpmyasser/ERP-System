# Prompt لـ Antigravity - توحيد معايير التصميم

## الخلفية والمشكلة

تم اكتشاف مشاكل كبيرة في عدم التناسق والتوحيد في مشروع حركة التشغيل:

### 1. **عدم توحيد أسماء الأزرار**
- نفس الزر يظهر بأسماء مختلفة: "بحث" و "ابحث" و "اضغط هنا"
- "إضافة" و "أضف" و "إضافة جديد"
- "طباعة" و "اطبع" و "طباعة التقرير"

### 2. **عدم توحيد أحجام الجداول**
- ارتفاعات أعمدة مختلفة من جدول إلى آخر
- padding مختلف في خلايا الجداول
- أسمك حدود مختلفة

### 3. **عدم توحيد حقول الإدخال**
- أحجام وارتفاعات مختلفة
- حالات الخطأ والنجاح غير معرّفة بوضوح
- استجابة Focus غير موحدة

### 4. **مشاكل الطباعة**
- معايير طباعة ناقصة وغير موحدة
- تنسيق الجداول في الطباعة غير متسق
- خطوط التوقيع بارتفاعات مختلفة

### 5. **مشاكل في الألوان**
- استخدام ألوان مختلفة في نفس السياق
- عدم وجود CSS variables موحدة

---

## ما تم اكتشافه وتوثيقه

تم إنشاء ملف توثيق شامل يحتوي على:

### من `design_standards_actual.md`:

**1. المعايير الفعلية المستخرجة من الكود:**
- قاموس الأزرار المستخدمة (11 زر موحد)
- الألوان الفعلية (16 لون محدد)
- أحجام الخطوط المستخدمة (من 0.75rem إلى 0.92rem)
- المسافات والحشو الفعلية (من 0.2rem إلى 1rem)
- معايير الجداول (padding: 0.58rem 0.65rem، border: 1.35px)
- معايير التوقيعات (ارتفاع: 58px، مسافات موحدة)

**2. معايير حقول الإدخال المقترحة:**
- ارتفاع موحد: 36px (عادي)، 32px (صغير)
- حشو موحد: 0.5rem 0.75rem
- حدود موحدة: 1px solid #ced4da
- نصف قطر: 0.25rem
- حالات: focus، invalid (أحمر)، valid (أخضر)
- disabled/readonly state

**3. معايير الطباعة الشاملة:**
- @page settings (A4، هوامش 10mm)
- اتجاه RTL موحد
- جداول الطباعة (padding: 6pt 4pt، font-size: 10pt)
- إخفاء العناصر غير الضرورية
- فترات الصفحات (page-break)
- معايير خطوط التوقيع
- جودة الطباعة

---

## المطلوب تنفيذه (الأولويات)

### **الأولوية 1: توحيد CSS الرئيسي (Critical)**
**الملف:** `static/app.css`

أضف CSS variables في `:root`:
```css
:root {
    --color-primary: #0d6efd;
    --color-success: #198754;
    --color-danger: #dc3545;
    --color-warning: #ffc107;
    
    --spacing-xs: 0.25rem;
    --spacing-sm: 0.5rem;
    --spacing-md: 0.75rem;
    --spacing-lg: 1rem;
    
    --table-padding: 0.58rem 0.65rem;
    --table-border: 1.35px solid #667085;
    
    --input-height: 36px;
    --input-height-sm: 32px;
    --input-padding: 0.5rem 0.75rem;
}
```

ثم طبّق على:
- جميع `.form-control` (height، padding، border)
- جميع `table` cells (padding، border)
- جميع المسافات (استخدم variables)

### **الأولوية 2: توحيد أسماء الأزرار (High)**
**الملفات:** `templates/**/*.html`

ابحث عن جميع الأزرار واستبدل الأسماء:
- ❌ "ابحث" → ✓ "بحث"
- ❌ "أضف" → ✓ "إضافة"
- ❌ "احذف" → ✓ "حذف"
- ❌ "اطبع" → ✓ "طباعة"
- ❌ "اغلق" → ✓ "إغلاق"
- ❌ "حمّل" → ✓ "استيراد"

القائمة الموحدة (11 زر فقط):
1. إضافة
2. تعديل
3. حفظ
4. حذف
5. استلام
6. مسح
7. إلغاء
8. إغلاق
9. استيراد
10. طباعة
11. بحث

### **الأولوية 3: توحيد حقول الإدخال (High)**
**الملف:** `static/app.css`

أضف هذه الأقسام:
```css
.form-control {
    height: var(--input-height);
    padding: var(--input-padding);
    font-size: 0.9rem;
    border: 1px solid #ced4da;
}

.form-control-sm {
    height: var(--input-height-sm);
    padding: 0.25rem 0.5rem;
}

.form-control.is-invalid {
    border-color: var(--color-danger);
    box-shadow: 0 0 0 0.15rem rgba(220, 53, 69, 0.2);
}

.form-control.is-valid {
    border-color: var(--color-success);
    box-shadow: 0 0 0 0.15rem rgba(25, 135, 84, 0.2);
}

.form-control:disabled,
.form-control[readonly] {
    background-color: #e9ecef;
    color: #6c757d;
}
```

### **الأولوية 4: توحيد الجداول (Medium)**
**الملفات:** كل ملفات HTML التي تحتوي على `table`

جعل جميع الجداول تستخدم:
```css
table {
    border-collapse: collapse;
}

table th,
table td {
    padding: var(--table-padding);
    border: var(--table-border);
}

table thead th {
    background-color: #f3f4f6;
    font-weight: 700;
}

table tbody tr:nth-child(even) {
    background-color: #f8f9fa;
}
```

### **الأولوية 5: توحيد الطباعة (Medium)**
**الملفات:** `static/print.css` و `@media print` في جميع HTML

**في print.css:**
```css
@page {
    size: A4;
    margin: 10mm;
}

@media print {
    * {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    html, body {
        direction: rtl !important;
        text-align: right !important;
        font-family: "Cairo", Arial, sans-serif;
        background-color: white !important;
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
    }
    
    table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 12pt;
    }
    
    table th, table td {
        padding: 6pt 4pt;
        border: 1px solid #333;
        font-size: 10pt;
    }
    
    .no-print, .btn, nav, footer, .sidebar {
        display: none !important;
    }
    
    .signature-line {
        border-top: 1px solid #000;
        width: 150px;
        margin-top: 20pt;
    }
}
```

### **الأولوية 6: توحيد الألوان في كل المكان (Low)**
**الملفات:** كل الملفات

استخدم CSS variables بدلاً من الأكواد الثابتة:
- ❌ `color: #0d6efd` → ✓ `color: var(--color-primary)`
- ❌ `background: #198754` → ✓ `background: var(--color-success)`

---

## ملفات مرجعية

تم إنشاء ملف توثيق شامل:
📄 **`design_standards_actual.md`** (في `/memories/repo/`)

يحتوي على:
- جميع المعايير الفعلية المستخرجة من الكود
- المعايير المقترحة للتوحيد
- أمثلة CSS كاملة جاهزة للاستخدام

---

## الخطوات العملية الموصى بها

1. **أضف CSS variables أولاً** (10 دقائق)
   - في `static/app.css` الأساسي
   
2. **وحّد أسماء الأزرار** (30 دقيقة)
   - ابحث واستبدل في جميع الـ templates
   
3. **طبّق معايير حقول الإدخال** (20 دقيقة)
   - في `static/app.css`
   
4. **طبّق معايير الجداول** (20 دقيقة)
   - في `static/app.css`
   
5. **حدّث الطباعة** (15 دقيقة)
   - في `static/print.css` و `@media print`
   
6. **اختبر كل شيء** (30 دقيقة)
   - جميع الصفحات
   - جميع الحقول
   - الطباعة

**الوقت الإجمالي:** ~125 دقيقة (ساعتين)

---

## الملاحظات المهمة

⚠️ **اختبر بعد كل خطوة** للتأكد من عدم كسر شيء
⚠️ **احفظ نسخة احتياطية** قبل البدء
⚠️ **استخدم find/replace بحذر** في تغيير أسماء الأزرار
✓ **وثّق أي تغييرات مخصصة** خارج المعايير

---

**آخر تحديث:** 20 أبريل 2026
**الحالة:** جاهز للتنفيذ
