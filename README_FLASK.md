# 🌐 نظام الموارد البشرية - Flask Edition

## 📋 نظرة عامة

تم تحويل نظام الموارد البشرية من **Streamlit** إلى **Flask** مع الاحتفاظ الكامل بجميع الوظائف والمنطق الأساسي.

---

## ✨ الميزات المكتملة

### ✅ المرحلة الأولى (MVP):
- **Dashboard** - لوحة تحكم مع إحصائيات
- **إدارة الموظفين الكاملة**:
  - قائمة الموظفين مع البحث والتصفية
  - إضافة موظف جديد
  - تعديل بيانات الموظف
  - عرض تفاصيل الموظف
  - التنقل (التالي/السابق)
  - حذف موظف

---

## 🚀 طريقة التشغيل

### 1. تثبيت المكتبات:
```bash
pip install -r requirements.txt
```

### 2. تشغيل التطبيق:
```bash
python run.py
```

### 3. فتح المتصفح:
افتح: `http://127.0.0.1:5000`

---

## 📂 هيكل المشروع

```
d:/H.R/
├── app/                          # تطبيق Flask
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # الإعدادات
│   ├── forms.py                 # WTForms
│   ├── routes/                  # المسارات
│   │   ├── main.py             # Dashboard
│   │   └── employees.py        # إدارة الموظفين
│   ├── templates/               # قوالب HTML
│   │   ├── base.html           # القالب الأساسي
│   │   ├── dashboard.html      # Dashboard
│   │   └── employees/          # قوالب الموظفين
│   │       ├── list.html       # قائمة الموظفين
│   │       ├── form.html       # نموذج إضافة/تعديل
│   │       └── view.html       # عرض التفاصيل
│   └── static/                  # الملفات الثابتة
│       ├── css/custom.css      # تنسيقات مخصصة
│       └── js/app.js           # JavaScript
│
├── core/                        # الكود الأساسي (من Streamlit)
│   ├── db_manager.py           # إدارة قاعدة البيانات
│   ├── database_models.py      # نماذج البيانات
│   ├── policy/                 # سياسات الشركة
│   │   └── hr_policy.py
│   ├── services/               # الخدمات
│   │   ├── payroll_processor.py
│   │   ├── attendance_service.py
│   │   ├── loans_service.py
│   │   └── permissions_service.py
│   └── utils/                  # المساعدات
│       ├── qr_generator.py
│       ├── printing.py
│       └── helpers.py
│
└── run.py                       # ملف التشغيل الرئيسي
```

---

## 🛠 التقنيات المستخدمة

### Backend:
- **Flask 3.0** - إطار العمل الأساسي
- **Flask-WTF** - نماذج وحماية CSRF
- **SQLAlchemy** - قاعدة البيانات (عبر db_manager)
- **Python 3.11+**

### Frontend:
- **Bootstrap 5.3 RTL** - التصميم
- **Font Awesome 6** - الأيقونات
- **Google Fonts (Cairo)** - الخط العربي
- **jQuery** (اختياري)

---

## 📊 الصفحات المتاحة

| الصفحة | المسار | الوصف |
|--------|--------|-------|
| Dashboard | `/` أو `/dashboard` | لوحة التحكم الرئيسية |
| قائمة الموظفين | `/employees/` | عرض جميع الموظفين |
| إضافة موظف | `/employees/create` | إضافة موظف جديد |
| عرض موظف | `/employees/<id>` | عرض تفاصيل موظف |
| تعديل موظف | `/employees/<id>/edit` | تعديل بيانات موظف |

---

## 🔧 الإعدادات

يمكن تعديل الإعدادات في `app/config.py`:

```python
class Config:
    SECRET_KEY = 'your-secret-key'  # غيّر هذا في الإنتاج
    DATABASE_PATH = 'path/to/hr.db'
    DEBUG = True  # False في الإنتاج
    ITEMS_PER_PAGE = 20  # عدد العناصر في الصفحة
```

---

## 📝 ملاحظات مهمة

### ✅ ما تم الاحتفاظ به:
- جميع حسابات الرواتب (`PayrollCalculator`)
- جميع الخدمات (`services/`)
- سياسات الشركة (`policy/hr_policy.py`)
- قاعدة البيانات SQLite الموجودة
- جميع المساعدات (`utils/`)

### 🔄 ما تم تغييره:
- الواجهة فقط: من Streamlit → Flask
- إدارة الحالة: من `st.session_state` → Flask sessions
- النماذج: من Streamlit widgets → WTForms

### ⏳ ما لم يتم تنفيذه بعد:
- إدارة الأقسام
- الحضور والانصراف
- حساب الرواتب (الواجهة فقط - الخدمة موجودة)
- التقارير
- السلف والجزاءات

---

## 🐛 استكشاف الأخطاء

### مشكلة: `ModuleNotFoundError: No module named 'app'`
**الحل:** تأكد من تشغيل `python run.py` من مجلد `d:/H.R`

### مشكلة: `No such table: employees`
**الحل:** تأكد من وجود قاعدة البيانات في `core/hr.db`

### مشكلة: صفحة فارغة
**الحل:** افتح Developer Tools (F12) وتحقق من الأخطاء في Console

---

## 📞 الدعم

للمساعدة أو الأسئلة، راجع:
- `implementation_plan.md` - خطة التنفيذ الكاملة
- `task.md` - حالة المهام
- `walkthrough.md` - دليل شامل

---

## 🎯 الخطوات التالية

لإكمال باقي الصفحات:
1. إضافة routes للأقسام
2. إضافة routes للحضور
3. إضافة routes للرواتب
4. إضافة routes للتقارير

---

**✨ النظام جاهز للاستخدام!**
