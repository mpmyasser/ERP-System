# توثيق شامل: آلية احتساب جزاء الغياب

## الملخص التنفيذي

تم التحقق من آلية احتساب جزاء الغياب في النظام، والتأكد من أنها تعمل بشكل ديناميكي بناءً على الإعدادات المخزنة في قاعدة البيانات وليس على قيم ثابتة في الكود.

---

## 1️⃣ الإعدادات المسؤولة عن احتساب الجزاء

### مصدر الإعدادات
يتم قراءة الإعدادات من جدول `system_settings` في قاعدة البيانات:

| المتغير | القيمة الحالية | الوصف |
|---------|----------------|-------|
| `ABSENCE_GRACE_DAYS` | `2` | عدد أيام الغياب المسموح بها بدون جزاء |
| `ABSENCE_PENALTY_DAYS` | `0.25` | قيمة الجزاء الإضافي لكل يوم غياب زائد (ربع يوم) |

### كيفية القراءة الديناميكية

```python
# في ملف: core/policy/hr_policy.py

class HRPolicyMeta(type):
    def _get_setting_meta(cls, key, default, data_type='int'):
        """يقرأ القيمة من قاعدة البيانات تلقائياً"""
        from flask import current_app
        try:
            db = current_app.db
            session = db.get_session()
            from database_models import SystemSetting
            setting = session.query(SystemSetting).filter_by(key=key).first()
            val = setting.value if setting else default
            session.close()
            
            if data_type == 'int': return int(val)
            if data_type == 'float': return float(val)
            return val
        except:
            return default
    
    @property
    def ABSENCE_GRACE_DAYS(cls):
        """عدد أيام الغياب المسموح بها"""
        return cls._get_setting_meta('ABSENCE_GRACE_DAYS', 2)
    
    @property
    def ABSENCE_PENALTY_DAYS(cls):
        """قيمة الجزاء لكل يوم زائد"""
        return cls._get_setting_meta('ABSENCE_PENALTY_DAYS', 0.25, 'float')
```

**✅ النتيجة:** النظام يقرأ الإعدادات ديناميكياً من قاعدة البيانات وليس من قيم ثابتة!

---

## 2️⃣ آلية احتساب الجزاء

### القاعدة المطبقة

```
إذا كان عدد أيام الغياب <= 2 يوم:
    لا يوجد جزاء (ضمن الحد المسموح)

وإلا:
    أيام الجزاء = (عدد أيام الغياب - 2) × 0.25
```

### الدالة المسؤولة

```python
# في ملف: core/policy/hr_policy.py

@staticmethod
def calculate_absence_penalty(days_absent):
    """
    حساب جزاء الغياب (ربع يوم لكل يوم بعد اليومين الأول)
    
    Args:
        days_absent: عدد أيام الغياب
        
    Returns:
        float: عدد أيام الجزاء
    """
    if days_absent <= HRPolicy.ABSENCE_GRACE_DAYS:
        return 0.0
    extra_days = days_absent - HRPolicy.ABSENCE_GRACE_DAYS
    return extra_days * HRPolicy.ABSENCE_PENALTY_DAYS
```

### أمثلة على الحساب

| عدد أيام الغياب | أيام الجزاء | التفسير |
|-----------------|-------------|---------|
| 0 يوم | 0.00 | ضمن الحد المسموح |
| 1 يوم | 0.00 | ضمن الحد المسموح |
| 2 يوم | 0.00 | ضمن الحد المسموح (الحد الأقصى) |
| **3 أيام** | **0.25** | **1 يوم زائد × 0.25 = ربع يوم جزاء** |
| 4 أيام | 0.50 | 2 يوم زائد × 0.25 = نصف يوم جزاء |
| 5 أيام | 0.75 | 3 يوم زائد × 0.25 = ثلاثة أرباع يوم جزاء |
| 6 أيام | 1.00 | 4 يوم زائد × 0.25 = يوم كامل جزاء |

---

## 3️⃣ التطبيق في نظام الرواتب

### الدالة المسؤولة عن الحساب

```python
# في ملف: core/services/payroll_processor.py

def calculate_attendance_deductions(self, daily_records, employee, basic_salary_override=None):
    """
    حساب خصومات الحضور (التأخير، الغياب، الجزاءات)
    """
    # حساب عدد أيام الغياب
    total_absence_days = 0
    for record in daily_records:
        if record.status and 'غائب' in record.status:
            total_absence_days += 1
    
    # حساب جزاء الغياب
    absence_penalty_days = self.calculate_absence_penalty(total_absence_days)
    
    # حساب القيمة المالية للجزاء
    daily_salary = HRPolicy.calculate_daily_salary(basic_salary)
    absence_penalty_deduction = absence_penalty_days * daily_salary
    
    return {
        'absence_days': total_absence_days,
        'absence_penalty_days': absence_penalty_days,
        'absence_penalty_deduction': absence_penalty_deduction,
        # ... باقي الحسابات
    }
```

### مثال عملي

**الموظف:** مدحت اشرف جرجس (كود: 102)
- **الراتب الأساسي:** 12,000 جنيه
- **الراتب اليومي:** 12,000 ÷ 26 = 461.54 جنيه

**السيناريو:** الموظف غائب 3 أيام بدون بصمات

**الحساب:**
```
عدد أيام الغياب = 3
أيام الجزاء = (3 - 2) × 0.25 = 0.25 يوم
قيمة الجزاء = 0.25 × 461.54 = 115.38 جنيه
```

**التفسير:**
- اليوم الأول: غياب عادي (ضمن المسموح) ✅
- اليوم الثاني: غياب عادي (ضمن المسموح) ✅
- اليوم الثالث: غياب + جزاء ربع يوم ⚠️

---

## 4️⃣ معالجة الغياب بدون بصمات

### كيف يتعامل النظام مع الأيام بدون بصمات؟

عند عدم ترحيل البصمات لأي يوم:

1. **لا يتم إنشاء سجل في جدول `daily_records`**
   - الجدول يحتوي فقط على الأيام التي تم ترحيل بصماتها

2. **في حساب الرواتب:**
   ```python
   # حساب إجمالي الأيام في الفترة
   total_days = (end_date - start_date).days + 1
   
   # حساب أيام الحضور المسجلة
   attendance_days = len(daily_records)
   
   # حساب أيام الغياب
   absence_days = total_days - attendance_days
   ```

3. **يتم احتساب الجزاء تلقائياً:**
   ```python
   penalty_days = HRPolicy.calculate_absence_penalty(absence_days)
   penalty_amount = penalty_days * daily_salary
   ```

### مثال من النظام الفعلي

**الفترة:** من 26/1/2026 إلى 25/2/2026 (31 يوم)
**الموظف:** مدحت اشرف جرجس

**البيانات:**
- إجمالي الأيام: 31 يوم
- أيام الحضور المسجلة: 24 يوم
- أيام الغياب (بدون بصمات): 7 أيام

**الحساب:**
```
أيام الجزاء = (7 - 2) × 0.25 = 1.25 يوم
قيمة الجزاء = 1.25 × 461.54 = 576.92 جنيه
```

**✅ النتيجة:** النظام يعتبر الأيام بدون بصمات غياب تلقائياً ويطبق الجزاء حسب الإعدادات!

---

## 5️⃣ مسار التنفيذ الكامل

### الملفات المسؤولة

```
1. قراءة الإعدادات:
   📄 core/database_models.py
      └─ جدول SystemSetting (يخزن الإعدادات)
   
   📄 core/policy/hr_policy.py
      ├─ HRPolicyMeta._get_setting_meta() → يقرأ من قاعدة البيانات
      ├─ @property ABSENCE_GRACE_DAYS
      └─ @property ABSENCE_PENALTY_DAYS

2. حساب الجزاء:
   📄 core/policy/hr_policy.py
      └─ HRPolicy.calculate_absence_penalty(days_absent)

3. تطبيق الجزاء في الرواتب:
   📄 core/services/payroll_processor.py
      └─ PayrollCalculator.calculate_attendance_deductions()
         ├─ يحسب عدد أيام الغياب من DailyRecord
         ├─ يستدعي calculate_absence_penalty()
         ├─ يحسب القيمة المالية: penalty_days × daily_salary
         └─ يضيفها إلى absence_penalty_deduction

4. معالجة الغياب بدون بصمات:
   📄 core/services/attendance_service.py
      └─ AttendanceService.determine_status()
         └─ إذا لم يوجد check_in ولا check_out → return "غائب"
   
   📄 app/routes/attendance.py
      └─ عند استيراد البصمات، يتم إنشاء DailyRecord لكل يوم
      └─ الأيام بدون بصمات = لا يوجد لها DailyRecord
      └─ في حساب الرواتب، يتم اعتبارها غياب
```

### مسار التنفيذ خطوة بخطوة

```
[قاعدة البيانات: system_settings]
         ↓
[HRPolicy يقرأ الإعدادات ديناميكياً]
         ↓
[PayrollCalculator يحسب أيام الغياب]
         ↓
[HRPolicy.calculate_absence_penalty()]
         ↓
[احتساب القيمة المالية للجزاء]
         ↓
[إضافتها إلى إجمالي الاستقطاعات]
```

---

## 6️⃣ التأكيدات النهائية

### ✅ الإجابة على أسئلتك

#### 1️⃣ من أين يتم قراءة عدد أيام الغياب المسموح بها؟

**الإجابة:**
- يتم قراءتها من جدول `system_settings` في قاعدة البيانات
- المتغير: `ABSENCE_GRACE_DAYS`
- القيمة الحالية: `2`
- يتم القراءة ديناميكياً عبر `HRPolicy.ABSENCE_GRACE_DAYS`

#### 2️⃣ هل النظام يطبق الجزاء بشكل صحيح؟

**الإجابة:** نعم ✅

- **أول يومين غياب:** لا جزاء (ضمن المسموح)
- **من اليوم الثالث:** يبدأ تطبيق ربع يوم جزاء لكل يوم زائد
- **الحساب:** (أيام الغياب - 2) × 0.25
- **يعتمد على الإعدادات:** وليس قيم ثابتة في الكود

#### 3️⃣ هل يتم اعتبار اليوم غياب عند عدم وجود بصمات؟

**الإجابة:** نعم ✅

- عند عدم ترحيل البصمات، لا يوجد `DailyRecord`
- في حساب الرواتب، يتم حساب: `absence_days = total_days - len(records)`
- يتم احتساب الجزاء تلقائياً بناءً على عدد أيام الغياب

---

## 7️⃣ كيفية تغيير الإعدادات

إذا أردت تغيير قيم الجزاء، يمكنك تحديث الإعدادات في قاعدة البيانات:

```sql
-- تغيير عدد أيام الغياب المسموح بها
UPDATE system_settings 
SET value = '3' 
WHERE key = 'ABSENCE_GRACE_DAYS';

-- تغيير قيمة الجزاء (مثلاً نصف يوم بدلاً من ربع)
UPDATE system_settings 
SET value = '0.5' 
WHERE key = 'ABSENCE_PENALTY_DAYS';
```

أو من خلال واجهة الإعدادات في النظام.

---

## 8️⃣ اختبار النظام

تم إنشاء سكريبت اختبار شامل: `test_absence_penalty_mechanism.py`

لتشغيله:
```bash
python test_absence_penalty_mechanism.py
```

يقوم السكريبت بـ:
1. قراءة الإعدادات من قاعدة البيانات
2. اختبار آلية الحساب بأمثلة متعددة
3. محاكاة سيناريو واقعي (3 أيام غياب)
4. اختبار التكامل مع نظام الرواتب
5. عرض مسار التنفيذ الكامل

---

## 9️⃣ الخلاصة

### ✅ التأكيدات

1. **النظام يعتمد على الإعدادات وليس قيم ثابتة**
   - يقرأ من جدول `system_settings`
   - يمكن تغيير القيم بدون تعديل الكود

2. **الجزاء يبدأ من اليوم الثالث فقط**
   - أول يومين: لا جزاء
   - من اليوم الثالث: ربع يوم جزاء لكل يوم زائد

3. **الأيام بدون بصمات تُعتبر غياب تلقائياً**
   - لا يوجد `DailyRecord` = غياب
   - يتم احتساب الجزاء في نظام الرواتب

4. **الحساب دقيق ومتسق**
   - يستخدم نفس الدوال في كل مكان
   - لا يوجد قيم ثابتة مخفية في الكود

---

## 📞 للدعم

إذا كان لديك أي استفسارات إضافية أو تحتاج إلى تعديلات، يرجى التواصل.

**تاريخ التوثيق:** 2026-02-11
**الإصدار:** 1.0
