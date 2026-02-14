# 🚀 البدء السريع - نظام سجل التعديلات

## ⚡ في 3 خطوات فقط:

### 1️⃣ تشغيل التطبيق
```bash
python run.py
```
الآن التطبيق يعمل على: **http://localhost:5000**

### 2️⃣ الذهاب للتقارير
في المتصفح، اذهب إلى:
```
http://localhost:5000/reports
```

### 3️⃣ اختيار سجل التعديلات
ستجد بطاقة حمراء تقول "سجل التعديلات" - اضغط عليها!

---

## 📍 الروابط المباشرة

| الوظيفة | الرابط |
|---|---|
| 📊 آخر التعديلات | `/audit_trail` |
| 👤 تعديلات موظف | `/employee_history/E001` |
| 📥 تنزيل CSV | `/audit_export` |

---

## 🔍 نصائح البحث

### البحث عن موظف معين:
```
http://localhost:5000/audit_trail?employee_code=E001
```

### البحث عن حقل معين:
```
http://localhost:5000/audit_trail?field_name=email
```

### البحث عن موظف وحقل معين:
```
http://localhost:5000/audit_trail?employee_code=E001&field_name=phone
```

### تحديد عدد النتائج:
```
http://localhost:5000/audit_trail?limit=50
```

---

## 💻 من الكود Python

```python
from core.db_manager import DBManager

db = DBManager()

# آخر 100 تعديل
logs = db.get_audit_logs_recent()

# تعديلات موظف
logs = db.get_audit_logs_by_employee('E001')

# تعديلات حقل
logs = db.get_audit_logs_by_field('email')

# ملخص
summary = db.get_audit_log_summary('E001')

# تصدير
db.export_audit_logs_csv('report.csv')
```

---

## ❓ أسئلة سريعة

**س**: أين تظهر التعديلات؟
ج: بمجرد ما تعدل بيانات أي موظف وتحفظ، يتم التسجيل تلقائياً!

**س**: كم تعديل يمكن عرضه؟
ج: من 10 إلى 500 تعديل في المرة الواحدة.

**س**: هل يمكن تصدير البيانات؟
ج: نعم! اضغط على زر "تصدير CSV".

**س**: هل يمكن استرجاع البيانات القديمة؟
ج: نعم، جميع القيم القديمة محفوظة في السجل.

---

## ✅ تم!

الآن أنت جاهز للاستخدام!
