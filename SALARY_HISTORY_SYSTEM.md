# 📊 نظام السجل التاريخي للرواتب
# Salary History Tracking System

## النظرة العامة

تم تطوير نظام متكامل لتتبع جميع التعديلات التي تتم على رواتب الموظفين مع حفظ معلومات كاملة عن:
- الراتب السابق والجديد
- قيمة التغيير والنسبة المئوية
- تاريخ التعديل والوقت
- السبب والملاحظات
- الشخص الذي قام بالتعديل

---

## المكونات

### 1. قاعدة البيانات (Database Model)

#### الجدول: `salary_history`

```python
class SalaryHistory(Base):
    __tablename__ = 'salary_history'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    old_salary = Column(Float, nullable=False)           # الراتب السابق
    new_salary = Column(Float, nullable=False)           # الراتب الجديد
    salary_change = Column(Float, nullable=False)        # الفرق (جديد - سابق)
    change_date = Column(DateTime, default=datetime.now) # تاريخ التعديل
    reason = Column(String(255))                          # السبب
    notes = Column(Text)                                  # ملاحظات إضافية
    modified_by = Column(String(100))                    # المعدل بواسطة
    
    # العلاقات
    employee = relationship("Employee", back_populates="salary_history")
    
    # الخصائص المحسوبة
    @property
    def formatted_change_date(self):
        return self.change_date.strftime('%d/%m/%Y %H:%M')
    
    @property
    def change_type(self):
        if self.salary_change > 0:
            return 'زيادة'
        elif self.salary_change < 0:
            return 'تخفيض'
        else:
            return 'بدون تغيير'
```

---

### 2. وظائف إدارة البيانات (Database Functions)

#### في `core/db_manager.py`:

```python
def add_salary_history(self, employee_id, old_salary, new_salary, reason=None, notes=None, modified_by=None):
    """
    تسجيل تعديل على راتب الموظف
    
    المعاملات:
        employee_id: معرف الموظف
        old_salary: الراتب السابق
        new_salary: الراتب الجديد
        reason: السبب (اختياري)
        notes: ملاحظات (اختياري)
        modified_by: الشخص الذي قام بالتعديل (اختياري)
    
    الإرجاع:
        كائن SalaryHistory الجديد
    """

def get_employee_salary_history(self, employee_id):
    """
    الحصول على السجل التاريخي الكامل لتعديلات راتب موظف معين
    
    المعاملات:
        employee_id: معرف الموظف
    
    الإرجاع:
        قائمة السجلات مرتبة من الأحدث
    """

def get_salary_history_report(self, employee_id=None, from_date=None, to_date=None):
    """
    الحصول على تقرير السجل التاريخي للرواتب مع الفلترة
    
    المعاملات:
        employee_id: معرف الموظف (اختياري)
        from_date: تاريخ البداية (اختياري)
        to_date: تاريخ النهاية (اختياري)
    
    الإرجاع:
        قائمة السجلات المطابقة
    """

def get_salary_history_with_employee(self, employee_id):
    """
    الحصول على السجل التاريخي مع تحميل بيانات الموظف
    
    المعاملات:
        employee_id: معرف الموظف
    
    الإرجاع:
        قائمة السجلات مع تحميل علاقات الموظف
    """
```

---

### 3. المسارات والمعالجات (Routes)

#### في `app/routes/reports.py`:

```
GET /reports/salary_history
    عرض تقرير السجل التاريخي للرواتب
    معاملات البحث:
        - employee_id: معرف الموظف
        - from_date: من التاريخ
        - to_date: إلى التاريخ
    
    يعرض:
        - قائمة بجميع التعديلات
        - إحصائيات (عدد التعديلات، إجمالي الزيادات، إجمالي التخفيضات)

GET /reports/salary_history/<emp_id>
    عرض تقرير مفصل لموظف محدد
    
    يعرض:
        - الراتب الحالي والمتوسط
        - رسم بياني للتطور الزمني
        - جدول بجميع التعديلات

GET /reports/salary_history/export
    تصدير التقرير إلى Excel
    معاملات البحث:
        - employee_id: معرف الموظف (اختياري)
        - from_date: من التاريخ
        - to_date: إلى التاريخ
```

---

### 4. التكامل مع عملية تحديث الموظف

عند تعديل بيانات الموظف في `app/routes/employees.py`:

```python
@employees_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    # ... كود التحديث ...
    
    # تسجيل التعديل على الراتب
    old_salary = employee.basic_salary
    new_salary = employee_data.get('basic_salary', old_salary)
    
    if old_salary != new_salary:
        db.add_salary_history(
            employee_id=id,
            old_salary=old_salary,
            new_salary=new_salary,
            reason='تعديل يدوي على الراتب',
            modified_by='admin'
        )
    
    db.update_employee(id, **employee_data)
```

---

### 5. الواجهات المستخدم (Templates)

#### `app/templates/reports/salary_history.html`
- تقرير السجل التاريخي الشامل
- مرشحات البحث (موظف، تاريخ)
- إحصائيات عامة
- جدول مفصل بجميع التعديلات

#### `app/templates/reports/salary_history_employee.html`
- تقرير مفصل لموظف واحد
- بطاقات الإحصائيات
- رسم بياني للتطور الزمني
- جدول التعديلات

---

## أمثلة الاستخدام

### 1. تسجيل تعديل على الراتب

```python
db = DBManager()

# تسجيل زيادة راتب
db.add_salary_history(
    employee_id=101,
    old_salary=9250,
    new_salary=10000,
    reason='زيادة سنوية',
    notes='بناءً على تقييم الأداء الإيجابي',
    modified_by='admin'
)
```

### 2. الحصول على السجل التاريخي لموظف

```python
history = db.get_employee_salary_history(101)

for record in history:
    print(f"{record.formatted_change_date} - {record.old_salary} → {record.new_salary} ({record.change_type})")
```

### 3. الحصول على تقرير مفصل

```python
from datetime import date, timedelta

# تقرير السنة الماضية
start_date = date.today() - timedelta(days=365)
report = db.get_salary_history_report(from_date=start_date)

total_increases = sum(r.salary_change for r in report if r.salary_change > 0)
total_decreases = sum(r.salary_change for r in report if r.salary_change < 0)

print(f"إجمالي الزيادات: {total_increases}")
print(f"إجمالي التخفيضات: {total_decreases}")
```

---

## الإحصائيات المتوفرة

- **عدد التعديلات**: إجمالي عدد التعديلات على الرواتب
- **إجمالي الزيادات**: مجموع كل الزيادات الموجبة
- **إجمالي التخفيضات**: مجموع كل التخفيضات السالبة
- **الفرق الإجمالي**: مجموع جميع التعديلات
- **متوسط الراتب**: متوسط الرواتب عبر التعديلات
- **النسبة المئوية للتغير**: التغير كنسبة من الراتب الحالي

---

## التقارير المتاحة

### 1. التقرير الشامل
- عرض جميع تعديلات الرواتب
- تصفية حسب الموظف والتاريخ
- عرض الإحصائيات الكلية

### 2. تقرير الموظف
- رسم بياني للتطور الزمني
- بطاقات الإحصائيات
- جدول مفصل التعديلات

### 3. تقرير Excel
- تصدير شامل لجميع البيانات
- قابل للطباعة والتحليل
- يتضمن الأسباب والملاحظات

---

## الميزات الأمان

✅ تسجيل من قام بالتعديل  
✅ حفظ الراتب السابق والجديد  
✅ تسجيل الوقت والتاريخ الدقيق  
✅ حفظ السبب والملاحظات  
✅ عدم حذف السجلات (append-only)  
✅ ربط قوي بسجلات الموظفين  

---

## الخطوات التالية (المخطط)

- [ ] إضافة موافقات إدارية لتعديلات الراتب
- [ ] إشعارات تلقائية عند تعديل الرواتب
- [ ] مقارنة الرواتب بين الموظفين
- [ ] تحليل الاتجاهات والأنماط
- [ ] تنبيهات الأخطاء والشذوذ
- [ ] تقرير سنوي شامل

---

## اختبار النظام

تم تشغيل الاختبارات بنجاح:

```
✅ اختبار 1: تسجيل تعديل على الراتب
✅ اختبار 2: الحصول على السجل التاريخي للموظف
✅ اختبار 3: الحصول على تقرير السجل التاريخي الكامل
✅ اختبار 4: الحصول على السجل مع بيانات الموظف
```

---

## ملاحظات مهمة

1. **التاريخ والوقت**: يتم حفظ الوقت الكامل (ساعة:دقيقة:ثانية)
2. **الصيغة**: جميع الرسائل والأسباب باللغة العربية
3. **الحفظ التلقائي**: يتم تسجيل التعديل تلقائياً عند تحديث الراتب
4. **عدم الحذف**: السجلات التاريخية لا تُحذف أبداً
5. **الفهرسة**: معرف الموظف مفهرس لسرعة البحث

---

آخر تحديث: 31/12/2025
