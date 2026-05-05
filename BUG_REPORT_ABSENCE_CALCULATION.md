# تقرير الأخطاء المكتشفة في احتساب الغياب والجزاء

## الخلاصة الفورية

**تم اكتشاف 3 أخطاء حرجة:**

1. ❌ **الغياب لا يتم احتسابه إطلاقاً** (يظهر 0 دائماً)
2. ❌ **الأيام المستقبلية تُحسب كغياب** (يجب استبعادها)
3. ❌ **الإجازات الأسبوعية تُحسب كغياب** (يجب استبعادها)

---

## الخطأ #1: الغياب لا يتم احتسابه إطلاقاً ❌

### الحالة الفعلية (الموظف 236):

```
الفترة: 26/1/2026 - 25/2/2026
اليوم الحالي: 23/2/2026

الحساب الصحيح:
- أيام التقويم: 31 يوم
- أيام الحضور المسجلة: 16 يوم
- الإجازات الأسبوعية: 4 أيام
- الإجازات المعتمدة: 1 يوم
- الأيام المستقبلية: 2 يوم (24، 25 فبراير)

الغياب الفعلي = 31 - 16 - 4 - 1 - 2 = 8 أيام
الجزاء = (8 - 2) × 0.25 = 1.5 يوم
القيمة = 1.5 × 96.15 = 144.23 جنيه
```

### ما يحسبه النظام الحالي:

```
أيام الحضور المحسوبة: 16
أيام الغياب المحسوبة: 0 ❌
أيام الجزاء المحسوبة: 0.0 ❌
قيمة الجزاء: 0.00 ❌
```

### السبب الجذري:

في ملف `core/services/payroll_processor.py` - دالة `calculate_attendance_deductions()`:

```python
for record in daily_records:
    if record.status and 'غائب' in record.status:
        total_absence_days += 1
    else:
        attendance_days += 1
```

**المشكلة:** الدالة تعتمد على `daily_records` فقط!

- إذا لم يوجد `DailyRecord` → لا يتم عد اليوم كغياب
- الأيام بدون سجلات = لا تُحسب إطلاقاً
- النتيجة: `total_absence_days = 0` دائماً

---

## الخطأ #2: الأيام المستقبلية تُحسب كغياب ❌

### المشكلة:

```
الفترة: 26/1/2026 - 25/2/2026
اليوم الحالي: 23/2/2026

الأيام المستقبلية: 24، 25 فبراير (2 يوم)

هذه الأيام لم تأتِ بعد، لا يمكن احتسابها كغياب!
```

### السبب:

في `_get_monthly_records()`:

```python
def _get_monthly_records(self, employee_id: int, month: int, year: int):
    start_date, end_date = self.get_salary_month_date_range(month, year)
    
    records = self.session.query(DailyRecord).filter(
        DailyRecord.employee_id == employee_id,
        DailyRecord.date >= start_date,
        DailyRecord.date <= end_date  # ❌ لا يوجد فلتر للأيام المستقبلية
    ).all()
```

**لا يوجد شرط يمنع الأيام المستقبلية!**

---

## الخطأ #3: الإجازات الأسبوعية تُحسب كغياب ❌

### المشكلة:

```
الإجازات الأسبوعية: 4 أيام (الجمعة من كل أسبوع)

هذه الأيام يجب استبعادها من حساب الغياب!
```

### السبب:

في `calculate_attendance_deductions()`:

```python
for record in daily_records:
    if record.status and 'غائب' in record.status:
        total_absence_days += 1
    else:
        attendance_days += 1
```

**لا يوجد فلتر للإجازات الأسبوعية!**

الدالة تحسب فقط السجلات الموجودة، لا تستبعد الإجازات.

---

## الحل المقترح

### 1. إصلاح حساب الغياب الفعلي

**الملف:** `core/services/payroll_processor.py`

**الدالة المسؤولة:** `calculate_attendance_deductions()`

**التعديل:**

```python
def calculate_attendance_deductions(self, daily_records, employee, basic_salary_override=None):
    """حساب خصومات الحضور"""
    
    # ... الكود الحالي ...
    
    # ❌ الطريقة الحالية (خاطئة):
    # total_absence_days = 0
    # for record in daily_records:
    #     if record.status and 'غائب' in record.status:
    #         total_absence_days += 1
    
    # ✅ الطريقة الصحيحة:
    # 1. احسب إجمالي الأيام في الفترة
    # 2. استبعد الأيام المستقبلية
    # 3. استبعد الإجازات الأسبوعية
    # 4. استبعد الإجازات المعتمدة
    # 5. الباقي = غياب
```

### 2. الخطوات التفصيلية للإصلاح

**أ) حساب الأيام الفعلية:**

```python
from datetime import date, timedelta

# احسب نطاق الفترة
start_date, end_date = self.get_salary_month_date_range(month, year)

# احسب الأيام الفعلية (بدون أيام مستقبلية)
today = date.today()
actual_end_date = min(end_date, today)
total_days = (actual_end_date - start_date).days + 1
```

**ب) استبعد الإجازات الأسبوعية:**

```python
weekly_off_count = 0
for d in range(total_days):
    current_date = start_date + timedelta(days=d)
    
    # تحقق من يوم الإجازة الأسبوعية
    weekday_mapping = {
        "الجمعة": "Friday",
        "السبت": "Saturday",
        # ...
    }
    target_weekday = weekday_mapping.get(HRPolicy.WEEKLY_HOLIDAY, "Friday")
    
    if current_date.strftime('%A') == target_weekday:
        weekly_off_count += 1
```

**ج) استبعد الإجازات المعتمدة:**

```python
leaves = self.session.query(Leave).filter(
    Leave.employee_id == employee.id,
    Leave.start_date <= actual_end_date,
    Leave.end_date >= start_date,
    Leave.status == LeaveStatus.APPROVED.value
).all()

leave_days = 0
for leave in leaves:
    d = leave.start_date
    while d <= leave.end_date:
        if start_date <= d <= actual_end_date:
            leave_days += 1
        d += timedelta(days=1)
```

**د) احسب الغياب الفعلي:**

```python
# عدد أيام الحضور المسجلة
attendance_days = len(daily_records)

# الغياب = الأيام الفعلية - الحضور - الإجازات الأسبوعية - الإجازات المعتمدة
total_absence_days = total_days - attendance_days - weekly_off_count - leave_days
```

---

## الملفات المطلوب تعديلها

### 1. `core/services/payroll_processor.py`

**الدوال المطلوب تعديلها:**
- `calculate_attendance_deductions()` - السطر ~250
- `_get_monthly_records()` - السطر ~450

**التغييرات:**
- إضافة فلتر للأيام المستقبلية
- إضافة حساب الإجازات الأسبوعية
- إضافة حساب الإجازات المعتمدة
- تصحيح حساب الغياب الفعلي

### 2. `core/policy/hr_policy.py`

**لا تحتاج تعديل** - الدالة `calculate_absence_penalty()` صحيحة

---

## مثال على النتيجة بعد الإصلاح

### الموظف 236:

```
قبل الإصلاح:
- أيام الغياب: 0 ❌
- الجزاء: 0.00 جنيه ❌

بعد الإصلاح:
- أيام الغياب: 8 ✅
- الجزاء: 1.5 يوم ✅
- القيمة: 144.23 جنيه ✅
```

### الموظف 102:

```
قبل الإصلاح:
- أيام الغياب: 0 ❌
- الجزاء: 0.00 جنيه ❌

بعد الإصلاح:
- أيام الغياب: 1 ✅
- الجزاء: 0 يوم (ضمن المسموح) ✅
- القيمة: 0.00 جنيه ✅
```

---

## الخلاصة

| المشكلة | السبب | الحل |
|--------|------|------|
| الغياب = 0 دائماً | تعتمد على daily_records فقط | احسب الفرق بين الأيام الفعلية والحضور |
| أيام مستقبلية = غياب | لا يوجد فلتر | أضف شرط `date <= today()` |
| إجازات أسبوعية = غياب | لا يوجد استبعاد | احسب الإجازات الأسبوعية واستبعدها |

---

## الأولويات

1. **حرج:** إصلاح حساب الغياب الفعلي (الخطأ #1)
2. **مهم:** استبعاد الأيام المستقبلية (الخطأ #2)
3. **مهم:** استبعاد الإجازات الأسبوعية (الخطأ #3)
