================================================================================
تحليل استقرار نظام استقطاع الغياب - المنظور المحاسبي
================================================================================

1️⃣ تحميل WORKING_DAYS_PER_MONTH
════════════════════════════════════════════════════════════════════════════

❌ المشكلة: يتم تحميله عند كل عملية حساب

الكود الحالي (hr_policy.py - السطر 20-32):
```python
def _get_setting_meta(cls, key, default, data_type='int'):
    from flask import current_app
    try:
        db = current_app.db
        session = db.get_session()
        from database_models import SystemSetting
        setting = session.query(SystemSetting).filter_by(key=key).first()
        val = setting.value if setting else default
        session.close()
        return int(val) if data_type == 'int' else float(val)
    except:
        return default
```

⚠️ التأثير:
- يتم فتح session جديد لكل استدعاء
- يتم تنفيذ SELECT query لكل موظف
- إذا تم حساب 100 موظف = 100 query لنفس القيمة

مثال:
```
الموظف 1: SELECT value FROM system_settings WHERE key='WORKING_DAYS_PER_MONTH'
الموظف 2: SELECT value FROM system_settings WHERE key='WORKING_DAYS_PER_MONTH'
الموظف 3: SELECT value FROM system_settings WHERE key='WORKING_DAYS_PER_MONTH'
...
```

✅ الحل المطلوب:
- Cache القيمة عند تشغيل السيرفر
- أو Cache لمدة محددة (مثلاً 1 ساعة)


2️⃣ حفظ daily_salary و absence_deduction
════════════════════════════════════════════════════════════════════════════

❌ المشكلة الكبرى: لا يوجد جدول Payroll في قاعدة البيانات

التحقق:
```python
# تم البحث في database_models.py
# النتيجة: لا يوجد class Payroll
```

⚠️ التأثير الخطير:
1. يتم إعادة حساب الراتب عند كل عرض
2. إذا تغيرت الإعدادات، تتغير الرواتب السابقة
3. لا يوجد audit trail للرواتب المعتمدة
4. لا يمكن مراجعة الرواتب التاريخية

مثال خطير:
```
يناير 2026:
- WORKING_DAYS_PER_MONTH = 26
- راتب الموظف = 5200 جنيه
- daily_salary = 5200 / 26 = 200 جنيه
- غياب 3 أيام = 600 جنيه خصم

فبراير 2026:
- المدير يغير WORKING_DAYS_PER_MONTH إلى 30
- عند عرض راتب يناير مرة أخرى:
  daily_salary = 5200 / 30 = 173.33 جنيه
  غياب 3 أيام = 520 جنيه خصم
  
❌ الراتب تغير بأثر رجعي!
```

✅ الحل المطلوب:
```sql
CREATE TABLE payroll_records (
    id INTEGER PRIMARY KEY,
    employee_id INTEGER,
    month INTEGER,
    year INTEGER,
    basic_salary DECIMAL(10,2),
    daily_salary DECIMAL(10,2),        -- ✅ محفوظ
    attendance_days INTEGER,
    absence_days INTEGER,
    absence_deduction DECIMAL(10,2),   -- ✅ محفوظ
    lateness_deduction DECIMAL(10,2),
    overtime_value DECIMAL(10,2),
    net_salary DECIMAL(10,2),
    working_days_used INTEGER,         -- ✅ عدد أيام العمل المستخدم
    created_at TIMESTAMP,
    approved_at TIMESTAMP,
    approved_by INTEGER,
    is_approved BOOLEAN DEFAULT FALSE,
    UNIQUE(employee_id, month, year)
);
```


3️⃣ تجاوز total_absence_days لعدد أيام العمل
════════════════════════════════════════════════════════════════════════════

❌ المشكلة: لا يوجد validation

الكود الحالي (payroll_processor.py - السطر 267):
```python
absence_deduction = total_absence_days * daily_salary
```

⚠️ السيناريو الخطير:
```
راتب الموظف = 5200 جنيه
WORKING_DAYS_PER_MONTH = 26
daily_salary = 200 جنيه

الموظف غائب 30 يوم (أكثر من أيام العمل!)
absence_deduction = 30 × 200 = 6000 جنيه

❌ الخصم أكبر من الراتب!
```

الكود الحالي (السطر 100-105):
```python
if employee.salary_type == 'ضيافة':
    gross_salary = employee.basic_salary
else:
    gross_salary = min(attendance_days * daily_salary, employee.basic_salary)
```

✅ gross_salary محمي بـ min()
❌ لكن absence_deduction غير محمي

النتيجة:
```
gross_salary = 5200 جنيه
absence_deduction = 6000 جنيه
net_salary = 5200 - 6000 = -800 جنيه ❌
```


4️⃣ إمكانية net_salary سالب
════════════════════════════════════════════════════════════════════════════

✅ نعم، يمكن أن يصبح سالبًا

الكود الحالي (السطر 145-155):
```python
total_deductions = (
    attendance_data['lateness_deduction'] +
    attendance_data.get('early_deduction', 0.0) +
    attendance_data['absence_penalty_deduction'] +
    loans_deduction +
    permissions_deduction +
    admin_penalties +
    insurance_deduction
)

net_salary = gross_salary + total_additions - total_deductions
```

❌ لا يوجد:
```python
net_salary = max(0, gross_salary + total_additions - total_deductions)
```

مثال واقعي:
```
راتب أساسي = 3000 جنيه
غياب 20 يوم = 2307 جنيه خصم
تأخير = 200 جنيه
سلفة = 500 جنيه
تأمين = 330 جنيه
جزاءات = 200 جنيه

إجمالي الخصومات = 3537 جنيه
الراتب الصافي = 3000 - 3537 = -537 جنيه ❌
```


════════════════════════════════════════════════════════════════════════════
الملخص التنفيذي
════════════════════════════════════════════════════════════════════════════

المشاكل الحرجة:
1. ❌ لا يوجد جدول payroll_records
2. ❌ إعادة حساب الرواتب عند كل عرض
3. ❌ تغيير الإعدادات يؤثر بأثر رجعي
4. ❌ لا يوجد حماية من net_salary سالب
5. ❌ لا يوجد حد أقصى لخصم الغياب
6. ⚠️ استعلام DB لكل موظف لجلب WORKING_DAYS_PER_MONTH

الحلول المطلوبة:
1. ✅ إنشاء جدول payroll_records
2. ✅ حفظ القيم المحسوبة عند الاعتماد
3. ✅ إضافة approved_at و approved_by
4. ✅ إضافة validation: net_salary >= 0
5. ✅ إضافة validation: absence_deduction <= basic_salary
6. ✅ Cache لـ WORKING_DAYS_PER_MONTH

════════════════════════════════════════════════════════════════════════════
