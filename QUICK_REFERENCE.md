# ⚡ مرجع سريع - نظام الموارد البشرية

## 🎯 الروابط المهمة

### 🏠 الصفحة الرئيسية
```
http://localhost:5000/
```

### 👥 إدارة الموظفين
```
http://localhost:5000/employees              # القائمة
http://localhost:5000/employees/create       # إضافة موظف جديد
```

### 🏢 إدارة الأقسام
```
http://localhost:5000/departments            # القائمة
http://localhost:5000/departments/create     # إضافة قسم جديد
```

### 🤝 السلف (Loans)
```
http://localhost:5000/loans                  # القائمة
http://localhost:5000/loans/create           # إضافة سلفة جديدة
http://localhost:5000/loans/<id>             # عرض التفاصيل
http://localhost:5000/loans/<id>/delete      # حذف (POST)
```

### ⚠️ الجزاءات والمكافآت (Penalties)
```
http://localhost:5000/penalties              # القائمة
http://localhost:5000/penalties/create       # إضافة جزاء/مكافأة جديدة
http://localhost:5000/penalties/<id>/delete  # حذف (POST)
```

### 📋 التصاريح (Permissions)
```
http://localhost:5000/permissions            # القائمة
http://localhost:5000/permissions/create     # إضافة تصريح جديد
http://localhost:5000/permissions/<id>/delete# حذف (POST)
```

### 📊 الحضور والبصمة (Attendance)
```
http://localhost:5000/attendance/            # عرض اليومي
http://localhost:5000/attendance/import      # استيراد من Excel
http://localhost:5000/attendance/employee/<id> # سجل الموظف
```

---

## 🚀 تشغيل التطبيق (تصحيح الأخطاء)

1. افتح PowerShell في مجلد المشروع (حيث يوجد `run.py`).
2. نفِّذ الأوامر التالية:
     - تنشيط البيئة الافتراضية إن كانت موجودة:
         - `venv\Scripts\activate.bat`
     - تثبيت المتطلبات (إن لم تكن مثبتة):
         - `py -3 -m pip install -r requirements.txt`
     - تشغيل التطبيق في نافذة الحاضر (لرؤية الأخطاء مباشرة):
         - `start_debug.bat` أو `py -3 run.py`

3. إذا لم يعمل الخادم:
     - تأكد أن المنفذ 5000 غير مستخدم: `netstat -aon | findstr 5000`.
     - إذا احتجت لفتح الـ endpoint محليًا استخدم: `Invoke-WebRequest -Uri http://127.0.0.1:5000`.
     - إذا ظهر خطأ في نافذة المفسر، انسخ رسالة الخطأ هنا لأساعدك في تحليلها.

---

## 📝 نماذج البيانات

### نموذج السلفة (Loan Form)
```python
employee_id: int           # معرّف الموظف
loan_type: str            # "monthly" أو "emergency"
amount: float             # المبلغ بالجنيه
number_of_installments: int  # عدد الأقساط
```

### نموذج الجزاء (Penalty Form)
```python
employee_id: int          # معرّف الموظف
penalty_type: str         # "Penalty" أو "Bonus"
amount: float             # المبلغ بالجنيه
reason: str              # السبب
date: date               # التاريخ
```

### نموذج التصريح (Permission Form)
```python
employee_id: int          # معرّف الموظف
date: date               # التاريخ
from_time: time          # وقت البداية
to_time: time            # وقت النهاية
reason: str              # السبب (اختياري)
is_paid: bool            # تصريح مدفوع؟
```

### نموذج استيراد البصمة (Attendance Import)
```python
# ملف Excel مع الأعمدة:
كود الموظف / employee_code      # string
التاريخ والوقت / timestamp      # datetime
النوع / type                    # string ("IN" أو "OUT")
```

---

## 🔧 دوال قاعدة البيانات (DBManager)

### السلف
```python
# إضافة سلفة
db.add_loan(
    employee_id=1,
    amount=1000.0,
    loan_type="monthly",
    number_of_installments=12,
    date_issued=date.today()
)

# الحصول على جميع السلف
loans = db.get_all_loans()

# الحصول على سلفة بواسطة المعرّف
loan = db.get_loan_by_id(loan_id)

# حذف سلفة
db.delete_loan(loan_id)
```

### الجزاءات
```python
# إضافة جزاء/مكافأة
db.add_penalty(
    employee_id=1,
    penalty_type="Penalty",  # أو "Bonus"
    amount=100.0,
    reason="تأخر متكرر",
    date=date.today()
)

# الحصول على جميع الجزاءات
penalties = db.get_all_penalties()

# الحصول على جزاء بواسطة المعرّف
penalty = db.get_penalty_by_id(penalty_id)

# حذف جزاء
db.delete_penalty(penalty_id)
```

### التصاريح
```python
# إضافة تصريح
db.add_permission(
    employee_id=1,
    date=date.today(),
    from_time=time(8, 30),
    to_time=time(17, 0),
    reason="موعد طبي",
    is_paid=True
)

# الحصول على جميع التصاريح
permissions = db.get_all_permissions()

# حذف تصريح
db.delete_permission(permission_id)
```

### الحضور والبصمة
```python
# إضافة سجل حضور
db.add_attendance_log(
    employee_code="EMP001",
    timestamp=datetime.now(),
    type="IN"  # أو "OUT"
)

# الحصول على الحضور اليومي
records = db.get_attendance_by_date(date.today())

# سجل الموظف
employee_records = db.get_employee_attendance(employee_id)
```

---

## 💾 نماذج SQL

### جدول السلف (loans)
```sql
CREATE TABLE loans (
    id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL,
    amount FLOAT NOT NULL,
    type VARCHAR NOT NULL,           -- "monthly", "emergency"
    installments_count INTEGER,
    remaining_balance FLOAT,
    is_paid_off BOOLEAN,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);
```

### جدول الجزاءات والمكافآت (penalties_and_bonuses)
```sql
CREATE TABLE penalties_and_bonuses (
    id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL,
    date DATE,
    type VARCHAR NOT NULL,           -- "Penalty", "Bonus"
    amount FLOAT NOT NULL,
    reason VARCHAR,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);
```

### جدول التصاريح (permissions)
```sql
CREATE TABLE permissions (
    id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL,
    date DATE NOT NULL,
    from_time TIME NOT NULL,
    to_time TIME NOT NULL,
    reason VARCHAR,
    is_paid BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);
```

---

## 🎨 CSS Classes و Bootstrap

### الأزرار
```html
<!-- إضافة -->
<a href="#" class="btn btn-primary">
    <i class="fas fa-plus"></i> إضافة
</a>

<!-- عرض -->
<a href="#" class="btn btn-info">
    <i class="fas fa-eye"></i>
</a>

<!-- حذف -->
<button class="btn btn-danger">
    <i class="fas fa-trash"></i>
</button>

<!-- إلغاء -->
<a href="#" class="btn btn-secondary">
    <i class="fas fa-times"></i> إلغاء
</a>
```

### البطاقات والشارات (Badges)
```html
<!-- أحمر (خطر) -->
<span class="badge bg-danger">خصم</span>

<!-- أخضر (نجاح) -->
<span class="badge bg-success">مكافأة</span>

<!-- أزرق (معلومات) -->
<span class="badge bg-primary">شهرية</span>

<!-- أصفر (تحذير) -->
<span class="badge bg-warning text-dark">طارئة</span>

<!-- رمادي (ثانوي) -->
<span class="badge bg-secondary">أخرى</span>
```

### النماذج (Forms)
```html
<!-- حقل نص -->
<input type="text" class="form-control" required>

<!-- حقل رقمي -->
<input type="number" step="0.01" class="form-control" min="0">

<!-- اختيار من قائمة -->
<select class="form-select" required>
    <option value="">-- اختر --</option>
</select>

<!-- تاريخ -->
<input type="date" class="form-control" required>

<!-- وقت -->
<input type="time" class="form-control" required>

<!-- منطقة نص -->
<textarea class="form-control" rows="4"></textarea>

<!-- checkbox -->
<input type="checkbox" class="form-check-input">
```

---

## 🔐 CSRF Protection

### في جميع النماذج
```html
<form method="post">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <!-- باقي الحقول -->
</form>
```

---

## 📊 DataTables الجداول

### التهيئة التلقائية
```javascript
// في datatables_init.js
$('.datatable').each(function() {
    if (!$.fn.DataTable.isDataTable(this)) {
        $(this).DataTable(defaultDataTableConfig);
    }
});
```

### الجداول الموجودة
- `#loans-table` - جدول السلف
- `#penalties-table` - جدول الجزاءات
- `#permissions-table` - جدول التصاريح
- `#employees-table` - جدول الموظفين
- `#departments-table` - جدول الأقسام

---

## 🔍 رسائل التنبيهات (Flash Messages)

### النجاح (Success)
```python
flash('تم إضافة السلفة بنجاح', 'success')
```

### الخطأ (Danger)
```python
flash('حدث خطأ: رسالة الخطأ', 'danger')
```

### التحذير (Warning)
```python
flash('⚠ حذر: رسالة التحذير', 'warning')
```

### المعلومات (Info)
```python
flash('ℹ معلومة: رسالة المعلومة', 'info')
```

---

## 🛠️ أوامر مفيدة

### تشغيل التطبيق
```bash
python run.py
```

### تثبيت المكتبات
```bash
pip install -r requirements.txt
```

### اختبار الملف
```bash
python -m py_compile app/routes/loans.py
```

### تنظيف ملفات Python المصرفة
```bash
find . -type d -name __pycache__ -exec rm -r {} +
```

---

## 📁 هيكل المجلدات

```
H.R/
├── app/
│   ├── routes/
│   │   ├── attendance.py
│   │   ├── loans.py
│   │   ├── penalties.py
│   │   ├── permissions.py
│   │   └── ...
│   ├── templates/
│   │   ├── loans/
│   │   │   ├── list.html
│   │   │   └── form.html
│   │   ├── penalties/
│   │   ├── permissions/
│   │   └── ...
│   ├── forms.py
│   └── __init__.py
├── core/
│   ├── db_manager.py
│   └── database_models.py
├── static/
│   ├── css/
│   └── js/
├── requirements.txt
├── run.py
└── SETUP_GUIDE.md
```

---

## 📚 ملفات التوثيق

- **SETUP_GUIDE.md** - دليل الاستخدام الشامل
- **CHANGES_LOG.md** - سجل التغييرات التفصيلي
- **QUICK_REFERENCE.md** - هذا الملف (المرجع السريع)

---

## ✅ قائمة التحقق (Checklist)

- [ ] تثبيت جميع المكتبات: `pip install -r requirements.txt`
- [ ] إنشاء قاعدة بيانات أولية
- [ ] إضافة موظفين أوليين
- [ ] اختبار إضافة سلفة
- [ ] اختبار إضافة جزاء
- [ ] اختبار إضافة تصريح
- [ ] اختبار استيراد البصمة
- [ ] التحقق من جميع الجداول تعرض البيانات
- [ ] اختبار الحذف

---

**آخر تحديث**: 2025-12-03  
**سهولة الاستخدام**: ⭐⭐⭐⭐⭐
