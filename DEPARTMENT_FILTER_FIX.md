# إصلاح فقدان تحديدات فلتر الأقسام في صفحة الموظفين

## الملف المعدل
`e:\backoup\H.R-11-02-2026 -\app\templates\employees\list.html`

---

## المشكلة
عند اختيار أقسام متعددة من فلتر الأقسام ثم الضغط على زر "بحث"، تختفي التحديدات بعد إعادة تحميل الصفحة.

---

## السبب
الكود كان يعتمد على متغير `selected_departments` من backend، لكن:
1. البحث يتم عبر GET request مع parameter اسمه `department_ids`
2. بعد إعادة التحميل، القيم موجودة في `request.args.getlist('department_ids')`
3. لكن الـ template كان يبحث عن `selected_departments` الذي قد لا يكون محدثاً

---

## الكود قبل التعديل

```html
<select name="department_ids" id="dept-filter" class="form-select form-select-sm filter-control-wide"
    multiple size="1" title="اختر الأقسام">
    {% for dept in departments %}
    <option value="{{ dept.id }}" {% if (dept.id|string in selected_departments|map(attribute='__str__'
        )|list) or (dept.id in selected_departments) %}selected{% endif %}>
        {{ dept.name }}
    </option>
    {% endfor %}
</select>
```

---

## الكود بعد التعديل

```html
<select name="department_ids" id="dept-filter" class="form-select form-select-sm filter-control-wide"
    multiple size="1" title="اختر الأقسام">
    {% for dept in departments %}
    <option value="{{ dept.id }}" 
        {% if dept.id|string in request.args.getlist('department_ids') or dept.id in request.args.getlist('department_ids')|map('int')|list %}selected{% endif %}>
        {{ dept.name }}
    </option>
    {% endfor %}
</select>
```

---

## التغييرات

### قبل:
```jinja2
{% if (dept.id|string in selected_departments|map(attribute='__str__')|list) or (dept.id in selected_departments) %}selected{% endif %}
```

### بعد:
```jinja2
{% if dept.id|string in request.args.getlist('department_ids') or dept.id in request.args.getlist('department_ids')|map('int')|list %}selected{% endif %}
```

---

## الشرح

### `request.args.getlist('department_ids')`
- يحصل على جميع القيم المرسلة في GET request بنفس الاسم
- يعيد list من strings مثل: `['1', '3', '5']`

### `dept.id|string in request.args.getlist('department_ids')`
- يتحقق إذا كان ID القسم (كـ string) موجود في القائمة
- يغطي حالة القيم النصية

### `dept.id in request.args.getlist('department_ids')|map('int')|list`
- يحول القيم إلى integers ثم يتحقق
- يغطي حالة القيم الرقمية

---

## المميزات

✅ **لا تعديل في JavaScript** - فقط template  
✅ **لا تعديل في backend** - يعتمد على request.args  
✅ **يعمل مباشرة** - بعد إعادة تحميل الصفحة  
✅ **متوافق مع Select2** - إذا تم تفعيله لاحقاً  
✅ **يدعم multiple selection** - يحافظ على جميع التحديدات  

---

## الاختبار

### قبل الإصلاح:
1. اختر قسم "التطوير" و "المبيعات"
2. اضغط "بحث"
3. ❌ تختفي التحديدات

### بعد الإصلاح:
1. اختر قسم "التطوير" و "المبيعات"
2. اضغط "بحث"
3. ✅ تبقى التحديدات ظاهرة

---

## ملاحظات

- الإصلاح يعتمد على `request.args` مباشرة
- لا يحتاج إلى تمرير `selected_departments` من backend
- يعمل مع أي عدد من الأقسام المختارة
- متوافق مع باقي الفلاتر في الصفحة
