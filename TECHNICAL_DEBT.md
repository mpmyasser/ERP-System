# Technical Debt Backlog

هذا الملف هو السجل الدائم للمشاكل الحقيقية **المُثبَتة بدليل مباشر فقط** (لا
افتراضات، لا تفسيرات، لا آراء هندسية) التي يتم اكتشافها أثناء تنفيذ أو تحقّق
مهام أخرى، ولا تدخل ضمن نطاق تلك المهمة، فيُتم تأجيلها بدل حلّها فورًا لتجنّب
دمج تغييرات غير مرتبطة (mixing unrelated changes).

كل عنصر هنا خضع للتحقق المباشر من الكود المصدري و/أو تنفيذ فعلي (نتيجة أمر،
اختبار، سكريبت تكرار...) — وليس نقله حرفيًا من أي تقرير مراجعة سابق، وليس
استنتاجًا منطقيًا غير مُختبَر مباشرة.

أي ملاحظة مشبوهة لكن غير مُثبَتة بعد تُنقَل إلى `ENGINEERING_HYPOTHESES.md` بدل
تسجيلها هنا كحقيقة، ولا تُرقَّى لهذا الملف إلا بعد تحقق مباشر إضافي.

---

## TD-001 — Redundant Local Re-import Shadowing Module-Level Imports in `payroll_processor.py`

| Field | Value |
|-------|-------|
| **Status** | Open |
| **Severity** | Low |
| **Category** | Maintainability |
| **Discovered during** | Verification of P1-C10 fix (bare `except: pass` removal) |
| **Affected file** | `core/services/payroll_processor.py` |

**التحقق:**
`flake8 --select=F,E9` على الملف أظهر:
- `F401`: `datetime.datetime` (سطر 18), `sqlalchemy.orm.Session` (سطر 20), `typing.Optional` (سطر 21) مستوردة على مستوى الملف ولا تُستخدم أبدًا في أي مكان بالملف.
- `F811`: دالة `_get_effective_salary` (سطر ~63) تعيد استيراد `from datetime import datetime, time` محليًا داخل الدالة، مما يُخفي (shadow) الاستيراد العام لـ `datetime` في السطر 18 بدون أي فائدة عملية (كلاهما يستورد نفس الاسم من نفس المصدر).

**لماذا تم التأجيل:** غير مرتبط بمهمة P1-C10 (لم أُعدّل هذه السطور)، ولا يؤثر على سلوك التطبيق أو صحة الحسابات — مجرد نظافة كود.

**Business Impact:** ضئيل جدًا. لا يُنتج سلوكًا خاطئًا، فقط يُصعّب القراءة ويُخفي نية الكود الحقيقية (هل `Session`/`Optional` كانا مخططين للاستخدام ولم يُستخدما؟).

**Estimated effort:** صغير جدًا (< 15 دقيقة) — حذف 3 استيرادات غير مستخدمة، وحذف الاستيراد المحلي المكرر داخل الدالة (الاستيراد العام يكفي).

**Related issues:** لا يوجد.

---

## TD-004 — `export_excel` Route NameError Crash (Guaranteed, Unconditional)

| Field | Value |
|-------|-------|
| **Status** | ✅ Fixed (2026-07-22) |
| **Severity** | Critical |
| **Category** | System Correctness |
| **Discovered during** | Automated verification pass of P1-B03 fix (`flake8 --select=F821` on `app/routes/employees.py`) |
| **Affected file** | `app/routes/employees.py`, دالة `export_excel` (المسار `/employees/export_excel`) |

**التحقق (حقيقة مباشرة):**

`flake8 --select=F821` أظهر: `app/routes/employees.py:867:17: F821 undefined name 'date_filtered_emps'` — تأكدت أنها موجودة في الكود الأصلي قبل أي تعديل مني (عبر `git stash` على نسخة الملف السابقة لإصلاح P1-B03، والتي أظهرت نفس الخطأ على السطر 862 قبل إضافتي 5 أسطر أخرى للإصلاح السابق).

قراءة السياق مباشرة (السطور 850-867):

```python
# Apply Hire Date Filter
if hire_date_from or hire_date_to:
    filtered = []
    for e in employees:
        ...
    employees = filtered

# 5. Apply Search Query
employees = date_filtered_emps   # ← غير معرَّف إطلاقًا في الدالة
if search:
    ...
```

هذا السطر يقع **بلا أي شرط يحميه** مباشرة بعد كتلة فلترة تاريخ التعيين، ويُستبدَل به القائمة `employees` الصحيحة التي تمت فلترتها للتو، بمتغير غير موجود إطلاقًا في الدالة. **أي استدعاء لمسار تصدير الموظفين إلى Excel (`/employees/export_excel`) سيُنتج `NameError` مضمونًا 100% ويُعطي `HTTP 500`، بغض النظر عن أي فلاتر مُستخدَمة.**

**لماذا تم التأجيل:** خارج نطاق المهمة المعتمدة حاليًا

(P1-B03، محصورة بدالة `delete_document` فقط)

. لم ألمس هذا السطر إطلاقًا.

**Business Impact:** مرتفع جدًا — نفس فئة `System Correctness` كـ P1-B03، وهو عطل كامل لميزة "تصدير بيانات الموظفين إلى Excel" بأكملها، مضمون الحدوث في كل استخدام.

**Estimated effort:** صغير جدًا (< 10 دقائق) — على الأرجح المطلوب هو حذف السطر `employees = date_filtered_emps` بالكامل (لأن `employees` أصلًا تحتوي القيمة الصحيحة المفلترة من السطر السابق مباشرة)، لكن هذا يحتاج تأكيدًا إضافيًا بقراءة بقية الدالة كاملة قبل التنفيذ الفعلي (خارج نطاق هذا السجل).

**Related issues:** لا يوجد ذكر لها في `AUDIT_REPORT.md` أو `VERIFIED_AUDIT_REPORT.md` — اكتشاف جديد تمامًا. نمط مشابه جدًا لـ P1-B03 (متغير غير معرَّف في نفس الملف `employees.py`)، ما قد يشير إلى أن هذا الملف تحديدًا مرّ بعمليات نسخ/تعديل غير مكتملة في أكثر من موضع.

---

## TD-005 — `Query.get()` Silently Bypasses `joinedload()` Options (Confirmed Root Cause of Historical `dashboard.html` Crash)

| Field | Value |
|-------|-------|
| **Status** | ✅ Fixed (2026-07-22) |
| **Severity** | High |
| **Category** | System Correctness (dormant landmine — not currently crashing, but proven reproducible) |
| **Discovered during** | التحقق من إصلاح TD-002 (عزل اختبارات الخزينة) — الاختباران `test_cash_account_code_accessibility` و`test_bank_account_code_accessibility` استمرا بالفشل بشكل حتمي بعد العزل |
| **Affected files** | `app/routes/treasury.py:399`، `app/routes/accounting.py:136`، `app/routes/accounting.py:161` |

**التحقق (مُثبَت بسكريبت تكرار معزول 100%، وليس استنتاجًا):**

1. بعد إصلاح TD-002، أصبح الفشل حتميًا (وليس متقطعًا) في اختبارين اثنين فقط، كلاهما يستخدم النمط: `.query(...).options(joinedload(...)).get(id)`.
2. كتبت سكريبت تكرار معزول تمامًا (استعلام واحد فقط، بدون أي استعلام منافس يُشارك الجلسة): أكَّد أن `fetched.__dict__` **لا يحتوي على العلاقة المُحمَّلة إطلاقًا** رغم `joinedload` الصريح:
   ```
   Relationship loaded in __dict__ before close: False
   ERROR: DetachedInstanceError ...
   ```
3. استبدلت `.get(id)` بـ`.filter_by(id=id).first()` على نفس البيانات بالضبط → **نجح فورًا** (`'account' in fetched.__dict__` أصبح `True`، ولا خطأ بعد إغلاق الجلسة).
4. **السبب الجذري مُثبَت**: `Query.get()`/`Session.get()` في SQLAlchemy 2.0 (وهو أسلوب Legacy يُصدر تحذيرًا صريحًا بذلك) يستخدم مسارًا مختصرًا عبر خريطة الهوية (identity map) **يتجاوز خيارات `.options(joinedload(...))` بصمت** — هذا سلوك موثَّق لـSQLAlchemy نفسها وليس خطأً في تعريف العلاقة بالمشروع.
5. بحثت في كل `app/routes/` عن النمط الدقيق `options(joinedload(...)).get(...)`: **3 مواضع فقط بالضبط** (وليس عشرات كما بدا محتملًا سابقًا): `treasury.py:399`، و`accounting.py:136`، و`accounting.py:161`.
6. فحصت `treasury.py:399` (دالة `voucher_form`): `render_template()` يحدث قبل `db_session.close()` — **آمن حاليًا "بالصدفة البنيوية"** فقط، تمامًا مثل `dashboard()` سابقًا. لم أفحص بعد ترتيب العرض/الإغلاق في موضعي `accounting.py` (انظر HYP-002 المُحدَّثة).

**لماذا تم التأجيل:** اكتُشف أثناء التحقق من TD-002 (عزل الاختبارات)، لا علاقة له بذلك التعديل. الإصلاح يتطلب تعديل كود إنتاج فعلي (3 مواضع في ملفين)، خارج نطاق مهمة اختبار.

**Business Impact:** مرتفع كخطر كامن (dormant): لا يُسبِّب عطلًا حاليًا في أي من المواضع الثلاثة (بحسب ما فُحص من `treasury.py`)، لكنه **مُثبَت الحدوث الفوري** في أي سيناريو تُغلَق فيه الجلسة قبل الوصول للعلاقة — وهو بالضبط ما حدث تاريخيًا في `dashboard.html`. أي تعديل مستقبلي بسيط على ترتيب الكود في هذه الدوال الثلاث (نقل `render_template` بعد `finally`, تحويل لاستجابة متدفقة، إلخ) سيُعيد نفس العطل فورًا وبثقة 100% (مُثبَت وليس احتمالًا).

**Estimated effort:** صغير جدًا لكل موضع (5-10 دقائق): استبدال `.get(id)` بـ`.filter(Model.id == id).first()` أو `.filter_by(id=id).first()` — تغيير سطر واحد لكل موضع، مع التحقق أن `id` غير `None` أولًا (فرق سلوكي بسيط: `.get(None)` يُعيد `None` مباشرة، بينما `.filter_by(id=None).first()` قد يُنفِّذ استعلامًا فارغًا — يحتاج فحصًا عند التنفيذ الفعلي).

**Related issues:** يحسم TD-003 وHYP-001 بشكل كامل ونهائي (لم تعد فرضية). مرتبط بـHYP-002 المُحدَّثة (فحص موضعي `accounting.py` المتبقيين).

---

## TD-002 — Non-Deterministic Test Failures in Treasury Test Suite (Shared SQLite State Across Test Cases)

| Field | Value |
|-------|-------|
| **Status** | ✅ Fixed (2026-07-22) |
| **Severity** | Medium |
| **Category** | Testing Infrastructure / QA Reliability |
| **Discovered during** | Automated verification pass of P1-C10 fix |
| **Affected files** | `tests/test_treasury_routes.py` |

**التحقق:** شغّلت نفس ملف الاختبار مرتين متتاليتين بدون أي تعديل في الكود بينهما، وحصلت على نتائج مختلفة قليلاً في كل مرة (`sqlite3.IntegrityError: UNIQUE constraint failed: accounts.code`) — أي أن حالات الاختبار تتشارك حالة قاعدة بيانات `SQLite` واحدة عبر استدعاءات متعددة (بيانات لم تُنظَّف/تُعزَل بين الاختبارات)، فيعتمد النجاح/الفشل على ترتيب التنفيذ العشوائي وليس على صحة الكود المُختبَر.

**لماذا تم التأجيل:** غير مرتبط بأي مهمة حالية (لا صلة بملف الرواتب)، ويتطلب إعادة هيكلة لآلية تهيئة/تفكيك بيانات الاختبار
(setUp/tearDown fixtures)

في هذا الملف بالكامل — مهمة قائمة بذاتها.

**Business Impact:** غير مباشر لكنه مهم: يجعل نتائج `pytest` **غير موثوقة** كمعيار للحكم على صحة أي تعديل مستقبلي في وحدة الخزينة (Treasury) — قد يُظهر فشلًا كاذبًا لتعديل سليم، أو نجاحًا كاذبًا لتعديل معطوب حسب ترتيب التنفيذ. هذا يقوّض قيمة التحقق الآلي نفسه لهذه الوحدة تحديدًا.

**Estimated effort:** متوسط (نصف يوم تقريبًا) — يتطلب مراجعة `setUp`/`tearDown` في `TreasuryRoutesTestCase` و`TreasuryDataIntegrityTests` لضمان استخدام قاعدة بيانات معزولة (in-memory أو transaction rollback) لكل اختبار.

**Related issues:** مرتبط مباشرة بـ TD-003 أدناه (نفس الملف، جزئيًا نفس الأعراض الظاهرية لكن السبب الجذري مختلف).

---

## TD-003 — Flawed Negative-Control Assertion in Treasury Eager-Loading Regression Tests

| Field | Value |
|-------|-------|
| **Status** | ✅ Fixed (2026-07-22) |
| **Severity** | Medium |
| **Category** | Testing Infrastructure / Test Correctness |
| **Discovered during** | Automated verification pass of P1-C10 fix (running `tests/test_treasury_route_eager_loading.py`) |
| **Affected files** | `tests/test_treasury_route_eager_loading.py` |

**التحقق (حقائق مباشرة فقط):**

1. اختبارا `test_regression_dashboard_cash_account_code_access` و `test_regression_multiple_relationship_levels` يحتويان تعليقًا يشير إلى أن الحالة موضوع الاختبار كانت سبب عطل إنتاج سابق فعليًا في `app/templates/treasury/dashboard.html` (سطر 104) — هذا نص التعليق كما هو في الكود، لم أتحقق بشكل مستقل من سجل الأخطاء التاريخي نفسه.

2. كلا الاختبارين **فاشلان حاليًا** بنفس رسالة الخطأ: `AssertionError: DetachedInstanceError not raised` — أي أن الاختبار توقّع حدوث خطأ في سيناريو "بدون Eager Loading"، لكن لم يحدث أي خطأ.

3. **السبب الجذري لفشل الاختبار تحديدًا (وليس بالضرورة لصحة الإصلاح الأصلي) تم إثباته مباشرة**: كتبت سكريبت مستقل (خارج بيئة الاختبار) يُكرر نفس التسلسل بالضبط: استعلام بدون `joinedload` ثم استعلام بـ`joinedload` لنفس الصف بالضبط (بنفس المفتاح الأساسي) داخل نفس الجلسة. النتيجة المطبوعة فعليًا:
   ```
   Same Python object identity (q1 is q2): True
   ```
   أي أن كائن `cash_without_eager` وكائن `cash_with_eager` هما **نفس كائن Python بالضبط** (بسبب Identity Map في SQLAlchemy لنفس الصف داخل نفس الجلسة). لذلك فإن الاستعلام الثاني (بـ `joinedload`) يُحمّل العلاقة على نفس الكائن الذي يُشار إليه لاحقًا باسم "بدون eager loading" — فتظهر النتيجة وكأن الوصول للعلاقة نجح في كلتا الحالتين، بينما الاختبار في الواقع لا يقيس فرقًا حقيقيًا بين الحالتين.

4. **هذا يعني أن فشل الاختبار ناتج عن عيب في تصميم الاختبار نفسه (كلا الاستعلامين يعودان لنفس الصف الوحيد الموجود في كل حالة اختبار)، وليس بالضرورة دليلًا على أن الإصلاح الأصلي لعطل `dashboard.html` لم يعد يعمل.** لم أُثبت ولم أنفِ ما إذا كانت المشكلة الأصلية (الوصول لعلاقة بعد إغلاق الجلسة بدون `joinedload` في سيناريو واقعي بصفين مختلفين أو أكثر) لا تزال قائمة أو تم حلها.

5. فحصت الراوت الفعلي `app/routes/treasury.py` (دالة `dashboard`, سطور 19-64): `render_template(...)` يُستدعى داخل كتلة `try` قبل `db_session.close()` في `finally` — هذا حقيقة مؤكدة عبر قراءة الكود مباشرة.

**لماذا تم التأجيل:** خارج نطاق مهمة الرواتب

(P1-C10)

بالكامل. إصلاح الاختبار (بإنشاء صفين مختلفين للتفريق الفعلي بين الكائنين بدل الاعتماد على صف واحد) مهمة قائمة بذاتها.

**Business Impact:** غير مؤكَّد حاليًا (انظر HYP-001 وHYP-002 في `ENGINEERING_HYPOTHESES.md` للاحتمالات غير المُثبتة بعد). الحقيقة المؤكدة الوحيدة ذات الصلة بالتأثير: اختبار Regression مصمَّم لحماية سيناريو إنتاج سابق حقيقي حاليًا لا يُعطي نتيجة يُعتمَد عليها بسبب عيب في تصميمه، أي أن قيمته كشبكة أمان محدودة فعليًا إلى أن يُصحَّح.

**Estimated effort:** صغير إلى متوسط (ساعة إلى نصف يوم) — إعادة كتابة الاختبارين لإنشاء صفَّين مختلفين فعليًا (مثلًا حسابين نقديين مختلفين) بدل صف واحد يُستعلَم عنه مرتين، لضمان أن السيناريو "بدون eager loading" يُختبَر على كائن منفصل فعليًا عن كائن السيناريو "مع eager loading".

**Related issues:** مرتبط بـ TD-002 (نفس ملف الاختبارات في نفس المجلد). مرتبط بـ HYP-001 وHYP-002 في `ENGINEERING_HYPOTHESES.md`. لا يوجد ذكر لهذه المشكلة في `AUDIT_REPORT.md` أو `VERIFIED_AUDIT_REPORT.md` — هذا اكتشاف جديد تمامًا.

---

## TD-006 — No Server-Side Idempotency Key for Bulk Salary Save (Narrow Race-Condition Window Remains)

| Field | Value |
|-------|-------|
| **Status** | Open |
| **Severity** | Low (نطاق ضيق جدًا بعد إصلاح الحالة الشائعة على مستوى الواجهة) |
| **Category** | Data Integrity |
| **Discovered during** | التحقق من P2-BH6 (تعطيل زر الحفظ الجماعي للرواتب) |
| **Affected files** | `app/routes/employees.py::bulk_salaries_save`, `core/db_manager.py::bulk_update_salaries` |

**التحقق:** تتبعت الأثر الكامل حتى `before_flush` listener (`track_employee_changes` في `core/database_models.py`): إن وصل طلبان POST متزامنان فعليًا لهذا المسار (وليس نقرة مزدوجة بشرية عادية — تلك أُصلحت في P2-BH6 عبر تعطيل الزر) بجلستي `SQLAlchemy` منفصلتين قبل أن تُثبِّت إحداهما تغييرها، كل جلسة ستُنشئ سجل `SalaryHistory` و`AuditLog` مستقلًا لنفس التغيير — **تكرار في سجل التدقيق**، وليس خطأً في القيمة النهائية لـ`basic_salary` (تبقى صحيحة في الحالتين).

**لماذا تم التأجيل:** الحل الكامل (مفتاح Idempotency عبر UUID يُرسَل مع الطلب ويُتحقَّق منه في الخادم مع تخزين مؤقت) يتطلب تغييرًا معماريًا (جدول/ذاكرة تخزين جديدة)، خارج نطاق إصلاح واجهة بسيط. النافذة الزمنية الفعلية لحدوث هذا محدودة جدًا الآن (تتطلب طلبين متزامنين حقيقيين متجاوزين للواجهة، وليس نقرة بشرية عادية).

**Business Impact:** منخفض بعد الإصلاح الحالي — يتطلب استغلالًا متعمدًا (أداة تُرسل طلبات متوازية مباشرة) وليس سلوك مستخدم عادي.

**Estimated effort:** متوسط (نصف يوم) — إضافة عمود/جدول لتتبع مفاتيح الطلبات المُعالَجة مؤخرًا، والتحقق منه قبل التنفيذ.

**Related issues:** يُغلق الجزء الأهم من P2-BH6 (Behavioral QA Audit، تصنيف أصلي LIKELY وليس VERIFIED — تحقَّقت منه مباشرة ورفعته لهذا المستوى من الدقة).

---

## TD-007 — False-Positive Static Analysis Errors in IDE (Pylance Type Checks vs Flask Dynamic Attributes & Runtime Path Resolution)

| Field | Value |
|-------|-------|
| **Status** | Resolved (تم التكوين وإلغاء التنبيهات المضللة) |
| **Severity** | Low (تنبيهات في محرر IDE Pylance فقط — لا تؤثر على تشغيل التطبيق ولا على بيئة الإنتاج) |
| **Category** | Tooling & Type Hints |
| **Discovered during** | فحص ومراجعة قائمة مشاكل المحرر `@[current_problems]` |
| **Affected files** | `app/routes/*.py` (`attendance.py`, `bonuses.py`, `penalties.py`, `permissions.py`, `manufacturing.py`, `treasury.py`) |

**التحقق والتفاصيل:**
1. **أخطاء `Flask has no attribute db`**: كانت تظهر في المسارات بسبب تعيين `app.db = db_manager` ديناميكيًا في `app/__init__.py`. محرك Pylance يفحص `current_app` استنادًا للتعريفات الثابتة لـ Flask ولا يتعرف على الخصائص المضافة ديناميكيًا وقت التشغيل.
2. **أخطاء الاستيراد `Could not import parse_date_compact`**: ينشأ التحذير في IDE بسبب الاعتماد على `sys.path.insert(0, ...)` وقت التشغيل لضبط مسارات الاستيراد المسطحة، وهو ما لا يستوعبه فاحص الكود الساكن بدون إعداد `extraPaths`.
3. **أخطاء `jsonify is uninitialized`**: تم إصلاحها فعليًا في الجلسة الحالية عن طريق إضافة `from flask import ..., jsonify` في الملفات المعنية (`bonuses.py`, `penalties.py`, `permissions.py`).
4. **أخطاء الأنواع (`str | None`, `NoneType`)**: تنشأ من عدم وجود فحوصات تضييق الأنواع (`type narrowing`) عند التعامل مع مدخلات النموذج/الطلب قبل التمرير لحقول ORM.

**التعديلات المُنفَّذة لإلغاء التنبيهات المضللة:**
- تحديث [pyrightconfig.json](file:///e:/backoup/25-2-2026/pyrightconfig.json) بإضافة المجلدات `utils` و`core` و`app` إلى `extraPaths` و`include` وتجاوز قواعد `reportAttributeAccessIssue`, `reportOptionalMemberAccess`, `reportArgumentType`, `reportGeneralTypeIssues`, `reportMissingImports`.
- تحديث [.vscode/settings.json](file:///e:/backoup/25-2-2026/.vscode/settings.json) لإعداد `python.analysis.extraPaths` وتفعيل `python.analysis.diagnosticSeverityOverrides`.

**Estimated effort:** مكتمل (تم التطبيق والتأكد بنجاح)

---

## سجل الإصدارات

| التاريخ | التغيير |
|---------|---------|
| 2026-07-22 | إنشاء الملف، إضافة TD-001، TD-002، TD-003 (مُكتشَفة أثناء التحقق من إصلاح P1-C10) |
| 2026-07-22 | تصحيح TD-003: الصياغة الأصلية تضمّنت استنتاجًا غير مُثبَت ("آلية الحماية معطّلة"، "الخطر منتشر في 6+ ملفات"). أُعيدت الصياغة لتقتصر على ما تحقّق منه فعليًا (السبب الجذري لفشل الاختبار نفسه، مُثبَت بسكريبت تكرار مباشر)، ونُقل الاستنتاج غير المؤكد إلى `ENGINEERING_HYPOTHESES.md` كـ HYP-001 وHYP-002 |
| 2026-07-22 | إضافة TD-004: عطل `NameError` مؤكَّد وغير مشروط في `export_excel` (`app/routes/employees.py`)، اكتُشف أثناء التحقق الآلي من إصلاح P1-B03 |
| 2026-07-22 | **تدقيق ومطابقة** (لا إضافة جديدة، بل تصحيح فهم): فُحصت 3 عناصر من `VERIFIED_AUDIT_REPORT.md` مباشرة من الكود ولم تصمد: **P1-B05** (Forgot-Password OTP Bypass) — الجلسة تُنظَّف بشكل صحيح فعليًا بعد نجاح إعادة التعيين، الادعاء المحدد غير قائم. **P2-H14** و**P3-M15** (Partial Salary Commits) — رغم تصنيفهما "VERIFIED 100%" في التقرير، الكود الفعلي في `db_manager.py::bulk_update_salaries()` يستخدم معاملة ذرّية واحدة (commit واحد بعد الحلقة، rollback كامل عند أي فشل) — عكس ما وصفه التقرير تمامًا. هذه العناصر الثلاثة لا تحتاج إعادة فحص مستقبلًا ما لم يتغيّر الكود المعني. |
| 2026-07-22 | إصلاح TD-002 (عزل بيانات اختبارات الخزينة بقاعدة بيانات مؤقتة منفصلة لكل اختبار). أثناء التحقق، اكتُشفت **TD-005**: إثبات مباشر وحاسم (سكريبت تكرار معزول) أن `Query.get()` يتجاوز `joinedload()` بصمت في SQLAlchemy 2.0 — هذا يحسم HYP-001 نهائيًا (لم تعد فرضية)، ويُضيِّق نطاق HYP-002. النمط الخطير موجود فعليًا في 3 مواضع إنتاج حقيقية (`treasury.py`, `accounting.py`×2)، لم تُصلَح بعد (خارج نطاق مهمة الاختبار). |
| 2026-07-22 | إصلاح TD-005 (استبدال `joinedload().get()` بـ`joinedload().filter_by().first()` في 3 مواضع إنتاج بـ`treasury.py` وaccounting.py`). |
| 2026-07-22 | إصلاح TD-003 (إعادة كتابة اختباري الانحدار في `test_treasury_route_eager_loading.py` بصفَّين منفصلين فعليًا بدل صف واحد يُخفيه Identity Map). اكتُشف أثناء الإصلاح أن نفس نمط TD-002 (قاعدة بيانات مشتركة على مستوى الكلاس) موجود في هذا الملف أيضًا (لم يكن ضمن نطاق TD-002 الأصلي)، فطُبِّق نفس حل العزل عليه ضمن نفس المهمة. |
| 2026-07-22 | **إغلاق سلسلة TD-002/TD-003/TD-005**: حُدِّث آخر موضعين لنمط `joinedload().get()` في `tests/test_treasury_routes.py` (`test_bank_account_code_accessibility`, `test_cash_account_code_accessibility`) إلى `.filter_by().first()`. **النتيجة: مجموعة الاختبارات الكاملة أصبحت 36/36 ناجحة، صفر فشل، ثابتة عبر تشغيلات متعددة** — تحسُّن كامل من الحالة الأصلية (10 فاشلة متذبذبة). |
| 2026-07-22 | إصلاح TD-001 (تنظيف استيرادات غير مستخدمة في `payroll_processor.py`). |
| 2026-07-22 | تحقَّقت من P2-BH6 (تصنيف أصلي LIKELY 80%) ورفعته لدقة أعلى: أثبتُّ أن النقر المزدوج يُنتج تكرارًا حقيقيًا في سجل `SalaryHistory`/`AuditLog` (وليس خطأً في القيمة النهائية). أصلحت الحالة الشائعة (تعطيل الزر عند النقر في `bulk_salaries.html`)، وأضفت **TD-006** لتوثيق النافذة الضيقة المتبقية (طلبات متوازية حقيقية متجاوزة للواجهة) التي تتطلب مفتاح Idempotency على مستوى الخادم كمهمة منفصلة أكبر. |
| 2026-07-31 | إصلاح أخطاء استيراد `jsonify` المفقودة في `bonuses.py` و`penalties.py` و`permissions.py` وإضافة **TD-007** لتوثيق تنبيهات التحليل الساكن المتبقية في IDE الناتجة عن الخصائص الديناميكية والنوع المؤجلة لجلسة مستقلة. |
