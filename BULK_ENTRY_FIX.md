✅ تم إصلاح مشكلة الإدخال الجماعي للسلف!

## 🐛 المشكلة
عند الإدخال الجماعي للسلف، كان يتوجب الضغط على زر "إضافة صف جديد" بدلاً من الاعتماد على مفتاح Enter لإنشاء صفوف جديدة تلقائياً.

## 🔍 السبب
دالة `handleLastEnter()` في `loans/bulk.html` كانت تستخدم منطق خاطئ:
```javascript
// ❌ الكود الخاطئ
const nextRow = rows[rowId + 1];  // هذا المنطق خاطئ لأن rowId قد لا يتطابق مع فهرس الصف
if (rows[rows.length - 1] === e.target.closest('tr')) {
    // ...
}
```

المشكلة: عندما تحذف صفوفاً، المتغير `rowId` لا يعكس الموقع الفعلي للصف في الجدول.

## ✅ الحل المطبق
تم تصحيح دالة `handleLastEnter()` لاستخدام منطق أكثر موثوقية:

```javascript
// ✅ الكود الصحيح
function handleLastEnter(e, rowId) {
    if (e.key === 'Enter') {
        e.preventDefault();
        // دائماً تحقق إذا كان هذا آخر صف
        const currentRow = e.target.closest('tr');
        const tbody = document.getElementById('bulkBody');
        const isLastRow = currentRow === tbody.lastElementChild;
        
        if (isLastRow) {
            // أضف صف جديد تلقائياً
            addNewRow();
        } else {
            // انتقل إلى حقل الكود في الصف التالي
            const nextRow = currentRow.nextElementSibling;
            if (nextRow) {
                nextRow.querySelector('.emp-code').focus();
            }
        }
    }
}
```

### التحسينات:
1. ✅ استخدام `tbody.lastElementChild` بدلاً من المقارنة بـ `rowId`
2. ✅ استخدام `currentRow.nextElementSibling` للحصول على الصف التالي بشكل موثوق
3. ✅ لا يتأثر بحذف الصفوف أو إعادة ترتيبها

## 🎯 الآن يعمل كالتالي:

### السيناريو 1: الضغط على Enter في آخر صف (الأقساط)
```
المستخدم:     كود موظف → Enter
             ↓
             المبلغ → Enter
             ↓
             النوع → Enter
             ↓
             الأقساط → Enter
             ↓
البرنامج:    ✅ ينشئ صف جديد تلقائياً
```

### السيناريو 2: الضغط على Enter في صف وسطي
```
المستخدم:     كود موظف → Enter
             ↓
             المبلغ → Enter
             ↓
             النوع → Enter
             ↓
             الأقساط → Enter
             ↓
البرنامج:    ✅ ينتقل إلى الصف التالي (كود الموظف)
```

## 📝 الملف المعدل
- `app/templates/loans/bulk.html` - السطور 158-174

## 🧪 الاختبار
1. افتح صفحة "إدخال سلف جماعي"
2. أدخل بيانات الموظف الأول
3. اضغط Enter في حقل "الأقساط"
4. ✅ سيظهر صف جديد تلقائياً
5. كرر العملية

## 🎉 النتيجة
✅ الإدخال الجماعي أصبح أسرع وأسهل
✅ المستخدم يمكنه الاستمرار في الإدخال بدون الحاجة للنقر على أي أزرار
✅ نفس الأداء والموثوقية

---

**تاريخ الإصلاح**: اليوم
**الحالة**: ✅ مكتمل
**الملفات المتأثرة**: 1 ملف
