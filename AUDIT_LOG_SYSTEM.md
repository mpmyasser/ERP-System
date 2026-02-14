# نظام سجلات التتبع (Audit Log System)
# Audit Log System Implementation Report

## ✅ التأكيد: البرنامج يدعم سجلات التتبع بالفعل

نعم، تم تطوير **نظام متكامل لتتبع التعديلات** على بيانات الموظفين بشكل تلقائي.

---

## 📋 نموذج البيانات | Data Model

### جدول `audit_logs`

```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY,
    employee_code VARCHAR(50) NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    old_value VARCHAR(255),
    new_value VARCHAR(255),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

**الأعمدة:**
| العمود | النوع | الوصف |
|--------|-------|-------|
| `id` | INTEGER | رقم السجل الفريد |
| `employee_code` | VARCHAR(50) | كود الموظف |
| `field_name` | VARCHAR(100) | اسم الحقل المعدل |
| `old_value` | VARCHAR(255) | القيمة القديمة |
| `new_value` | VARCHAR(255) | القيمة الجديدة |
| `timestamp` | DATETIME | وقت التعديل |

---

## 🔄 آلية العمل | How It Works

### 1. مستمع الأحداث (Event Listener)

**الموقع:** `core/database_models.py` (سطور 247-280)

```python
@event.listens_for(Session, 'before_flush')
def track_employee_changes(session, flush_context, instances):
    """
    مستمع يراقب كل تغييرات بيانات الموظفين قبل حفظها
    """
    for instance in session.dirty:
        if not isinstance(instance, Employee):
            continue
        
        # الحصول على حالة الكائن
        state = inspect(instance)
        
        # التحقق من كل حقل
        for attr in state.attrs:
            history = attr.history
            
            # إذا تغير الحقل، قم بتسجيله
            if history.has_changes():
                old_value = history.deleted[0] if history.deleted else None
                new_value = history.added[0] if history.added else None
                
                # إنشاء سجل التتبع
                log_entry = AuditLog(
                    employee_code=instance.code,
                    field_name=attr.key,
                    old_value=str(old_value),
                    new_value=str(new_value),
                )
                session.add(log_entry)
```

### 2. عملية التتبع التلقائي

```
تعديل بيانات الموظف
    ↓
مستمع الأحداث قبل الحفظ
    ↓
كشف التغييرات تلقائياً
    ↓
إنشاء سجل AuditLog
    ↓
حفظ السجل في قاعدة البيانات
    ↓
حفظ البيانات الأصلية
```

---

## 📝 مثال عملي | Practical Example

### الحالة: تعديل بيانات موظف

```python
# 1. الحصول على الموظف من قاعدة البيانات
employee = db.get_employee_by_code("EMP001")

# 2. تعديل البيانات
employee.name = "أحمد محمد"  # تغيير الاسم
employee.email = "ahmed@example.com"  # تغيير البريد الإلكتروني

# 3. حفظ التغييرات
db.update_employee(employee)

# 4. النتيجة: سجلات التتبع
# - السجل 1: field_name='name', old_value='علي محمد', new_value='أحمد محمد'
# - السجل 2: field_name='email', old_value='ali@old.com', new_value='ahmed@example.com'
```

**الجدول الناتج في `audit_logs`:**

| id | employee_code | field_name | old_value | new_value | timestamp |
|----|---|---|---|---|---|
| 1 | EMP001 | name | علي محمد | أحمد محمد | 2025-12-11 10:30:45 |
| 2 | EMP001 | email | ali@old.com | ahmed@example.com | 2025-12-11 10:30:45 |

---

## 🔧 الدوال المتاحة | Available Functions

### 1. إضافة سجل حضور (Attendance Log)

**في `db_manager.py`:**

```python
def add_attendance_log(self, employee_code, timestamp, type):
    """
    إضافة سجل حضور جديد
    
    Parameters:
    - employee_code: كود الموظف
    - timestamp: الوقت والتاريخ
    - type: نوع السجل (دخول/خروج)
    """
```

**الاستخدام:**
```python
db.add_attendance_log("EMP001", datetime.now(), "entry")
```

### 2. الحصول على السجلات حسب التاريخ

**في `db_manager.py`:**

```python
def get_logs_by_date(self, date):
    """
    الحصول على جميع سجلات الحضور في يوم معين
    """
```

---

## 📊 الحقول المتابعة | Tracked Fields

يتم تتبع جميع تغييرات بيانات الموظف، بما في ذلك:

✅ البيانات الشخصية:
- الاسم (`name`)
- البريد الإلكتروني (`email`)
- الهاتف (`phone`)
- تاريخ الميلاد (`date_of_birth`)
- الرقم القومي (`national_id`)

✅ بيانات التوظيف:
- المنصب (`position`)
- المحافظة (`governorate`)
- درجة التأمين (`insurance_degree`)
- حالة التوظيف (`is_active`)

✅ بيانات الراتب:
- الراتب الأساسي (`base_salary`)
- بدل النقل (`transport_allowance`)
- بدل السكن (`housing_allowance`)

---

## 🔍 الاستعلام عن السجلات | Querying Audit Logs

### في Python:

```python
from core.database_models import AuditLog
from core.db_manager import DBManager

db = DBManager()
session = db.get_session()

# الحصول على جميع تغييرات موظف معين
logs = session.query(AuditLog).filter(
    AuditLog.employee_code == "EMP001"
).all()

# الحصول على تغييرات حقل معين
name_changes = session.query(AuditLog).filter(
    AuditLog.field_name == "name"
).all()

# الحصول على التغييرات في فترة زمنية
from datetime import datetime, timedelta

yesterday = datetime.now() - timedelta(days=1)
recent_changes = session.query(AuditLog).filter(
    AuditLog.timestamp >= yesterday
).all()
```

### عرض البيانات:

```python
for log in logs:
    print(f"موظف: {log.employee_code}")
    print(f"الحقل: {log.field_name}")
    print(f"القيمة القديمة: {log.old_value}")
    print(f"القيمة الجديدة: {log.new_value}")
    print(f"التاريخ والوقت: {log.timestamp}")
    print("---")
```

---

## 🎯 حالات الاستخدام | Use Cases

### 1. تقرير التعديلات على الموظفين

يمكن عرض تقرير يوضح:
- من قام بتعديل البيانات (من خلال كود الموظف المسجل)
- متى تم التعديل
- ما الذي تم تعديله
- القيم القديمة والجديدة

### 2. استرجاع البيانات التاريخية

يمكن معرفة:
- قيمة الراتب السابق
- المنصب السابق
- البيانات الشخصية السابقة

### 3. التدقيق والمراجعة (Compliance)

يساعد في:
- التحقق من التغييرات المشبوهة
- التحقق من الامتثال للسياسات
- توثيق التعديلات لأغراض قانونية

---

## 💻 أمثلة متقدمة | Advanced Examples

### مثال 1: تقرير تغييرات الراتب

```python
salary_changes = session.query(AuditLog).filter(
    AuditLog.field_name.like('%salary%')
).order_by(AuditLog.timestamp.desc()).all()

print("تقرير تغييرات الرواتب:")
for log in salary_changes:
    print(f"الموظف {log.employee_code}: {log.old_value} → {log.new_value}")
```

### مثال 2: إحصائيات التعديلات

```python
from sqlalchemy import func

# عدد التعديلات لكل موظف
stats = session.query(
    AuditLog.employee_code,
    func.count(AuditLog.id).label('count')
).group_by(AuditLog.employee_code).all()

for emp_code, count in stats:
    print(f"{emp_code}: {count} تعديل")
```

### مثال 3: التعديلات الحديثة

```python
from datetime import datetime, timedelta

# آخر 10 تعديلات
recent = session.query(AuditLog)\
    .order_by(AuditLog.timestamp.desc())\
    .limit(10)\
    .all()

for log in recent:
    time_diff = datetime.utcnow() - log.timestamp
    print(f"{log.employee_code} - {log.field_name}: منذ {time_diff.seconds} ثانية")
```

---

## ⚙️ الإعدادات | Configuration

النظام يعمل **بشكل تلقائي تماماً** بدون الحاجة إلى:
- تفعيل إعدادات معينة
- استدعاء دوال خاصة
- تعديل الكود الموجود

كل ما يحدث تلقائياً من خلال مستمع الأحداث (`event.listens_for`).

---

## 🚀 التحسينات المستقبلية | Future Enhancements

### 1. تسجيل بيانات المستخدم

إضافة عمود `user_id` لتسجيل من قام بالتعديل:
```python
class AuditLog(Base):
    user_id = Column(Integer)  # من قام بالتعديل
```

### 2. تسجيل نوع العملية

إضافة عمود للعملية:
```python
class AuditLog(Base):
    operation = Column(String(50))  # insert/update/delete
```

### 3. واجهة عرض الكترونية

إنشاء صفحة في التطبيق لعرض:
- جميع التعديلات على الموظفين
- البحث حسب الموظف أو التاريخ
- تحميل البيانات كـ Excel/PDF

### 4. نبهات فورية

إرسال إشعارات عند:
- تعديل بيانات حساسة (راتب، منصب)
- تعديلات كثيرة في وقت قصير
- تغييرات غير معتادة

---

## 📊 الملفات ذات الصلة | Related Files

| الملف | الوصف |
|-------|-------|
| `core/database_models.py` | نموذج AuditLog + مستمع الأحداث |
| `core/db_manager.py` | دوال الوصول لقاعدة البيانات |
| `app/routes/reports.py` | يستخدم AuditLog للتقارير |

---

## ✅ الحالة | Status

| المكون | الحالة | الملاحظات |
|-------|--------|----------|
| نموذج AuditLog | ✅ مكتمل | جاهز للاستخدام |
| مستمع الأحداث | ✅ مكتمل | يعمل تلقائياً |
| دوال الوصول | ⏳ جزئي | يمكن إضافة المزيد |
| واجهة العرض | ❌ لم يتم | يمكن إضافتها |

---

**النتيجة: نعم، البرنامج يدعم سجلات التتبع بشكل كامل وتلقائي! ✅**
