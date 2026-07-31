# AI Engineering Team — Handoff & Coordination Log

هذا الملف هو نقطة التنسيق بين النماذج التي تعمل على هذا المشروع كفريق هندسي واحد.
الهدف: أي نموذج يبدأ العمل يقرأ هذا الملف أولًا، يعرف أين توقف الآخر، وماذا يفعل بعده،
ثم يُسجّل ما أنجزه هنا بنفس التنسيق قبل أن يُسلِّم الدور مرة أخرى.

## أعضاء الفريق

| الاسم | الدور | البيئة |
|-------|------|--------|
| Claude (Sonnet) | Lead Software Engineer | Claude.ai / Claude Code |
| `@cf/zai-org/glm-5.2` | Software Engineer | VS Code |

## ⚠️ قاعدة أساسية يجب على أي عضو جديد اتباعها

**المستودع هو مصدر الحقيقة الوحيد — وليس أي تقرير أو ملف تسليم، بما في ذلك هذا الملف.**
`AUDIT_REPORT.md` و`VERIFIED_AUDIT_REPORT.md` هما فهرس فقط لتسريع إيجاد المشاكل المحتملة،
وقد ثبت مرارًا أثناء هذا العمل أن عناصر مُصنَّفة "VERIFIED 100%" فيهما كانت **خاطئة فعليًا**
عند فحص الكود المصدري مباشرة (انظر قسم "عناصر تم دحضها" أدناه). **لا تُنفِّذ أي إصلاح دون قراءة
الكود المصدري الفعلي أولًا والتحقق المباشر.**

## بروتوكول العمل المُتَّبَع (يجب الالتزام به من أي نموذج ينضم)

1. **مهمة منطقية واحدة في كل مرة** — لا تخلط تعديلات غير مرتبطة في نفس التغيير.
2. **تحقَّق من كل ادعاء بالكود المصدري مباشرة** قبل الوثوق به، حتى لو كان مصنَّفًا "VERIFIED".
3. **الحفاظ على جاهزية الإنتاج بعد كل تعديل** — لا حالات وسيطة معطوبة.
4. **تحقق آلي كامل بعد كل تنفيذ، وليس فقط فحص الصياغة**: `compileall`, `flake8 --select=F821,F,E9`,
   بناء التطبيق الكامل (`create_app()` والتأكد من عدد المسارات)، محاكاة فعلية عبر `Flask test_client`
   أو سكريبت تكرار مباشر (وليس تحليلًا نظريًا)، ثم `pytest tests/` كاملة (شغّلها أكثر من مرة إن كان
   هناك شك في الحتمية).
   - **مهم:** استخدم `PYTHONPATH="core:app:."` عند تشغيل أي أمر Python بسبب نمط الاستيراد المسطَّح
     في هذا المشروع (`from database_models import ...` بدل `from core.database_models import ...`).
   - **لا تُسلسل أوامر بـ`&&` إذا كان أي أمر فيها قد يُعيد رمز خروج غير صفري بشكل شرعي** (مثل
     `flake8`)، لأن ذلك يُوقف التسلسل ويُلغي تنفيذ ما بعده بصمت (وقع هذا فعليًا أثناء هذا العمل
     وتسبَّب بضياع إصلاح مؤقتًا في `git stash`).
5. **أي مشكلة جديدة تُكتشَف أثناء التحقق ولا علاقة لها بالمهمة الحالية**: لا تُصلَح فورًا. بدلًا من ذلك:
   تحقَّق منها → صنِّف خطورتها → أضفها لـ`TECHNICAL_DEBT.md` بمعرِّف فريد (`TD-XXX` تالٍ) → اشرح
   سبب التأجيل → قدِّر الأثر والجهد → اربطها بأي عنصر ذي صلة.
6. **`TECHNICAL_DEBT.md` يحتوي فقط حقائق مُثبَتة بدليل تنفيذ مباشر** (سكريبت، اختبار، مخرجات أمر
   فعلي) — لا افتراضات ولا تفسيرات. أي استنتاج غير مؤكَّد يذهب إلى `ENGINEERING_HYPOTHESES.md`
   بمعرِّف `HYP-XXX`، مع ذكر الأدلة المتوفرة والناقصة صراحة، ولا يُرقَّى لـ`TECHNICAL_DEBT.md` إلا
   بعد تحقق مباشر إضافي.
7. **بعد كل تنفيذ**, سجّل في قسم "سجل نشاط الفريق" أسفل هذا الملف: الملفات المُعدَّلة، ملخص التغيير،
   الآثار الجانبية المحتملة، التحقق المُنفَّذ فعليًا، ورسالة `git commit` مقترحة.
8. **حالة Git الحالية مهمة**: كل التعديلات الموصوفة في هذا الملف **لم تُعمَل لها `commit` بعد** —
   هي تعديلات محلية غير مُلتَزَم بها (`git status` يُظهرها كـ`modified`). قبل البدء، شغّل `git status`
   وتأكَّد من مطابقة ما تراه لما هو موثَّق هنا، فقد يكون عضو آخر من الفريق عدَّل شيئًا لم يُسجَّل هنا بعد.

## ملفات مرجعية أساسية (اقرأها بهذا الترتيب)

1. `TECHNICAL_DEBT.md` — كل المشاكل الحقيقية المؤجَّلة والمُصلَحة (السجل الدائم)
2. `ENGINEERING_HYPOTHESES.md` — استنتاجات غير مؤكَّدة بعد
3. `VERIFIED_AUDIT_REPORT.md` و`AUDIT_REPORT.md` — فهرس أولي فقط، غير موثوق دون تحقق
4. هذا الملف (`AI_TEAM_HANDOFF.md`) — للتنسيق بين أعضاء الفريق فقط

## ملخص ما تم إنجازه حتى الآن (بواسطة Claude)

جميعها مُنفَّذة ومُتحقَّق منها بالكامل (تحقق آلي + محاكاة فعلية + `pytest` كامل)، لكن **لم يُعمَل
لها `commit` بعد**:

| المعرّف | الوصف | الملفات |
|---------|-------|---------|
| P1-C10 | إصلاح `except: pass` عارية في حساب المكافآت (رواتب) | `core/services/payroll_processor.py` |
| P1-B03 | إصلاح `NameError` مضمون في حذف مستندات الموظفين | `app/routes/employees.py` |
| TD-004 | إصلاح `NameError` مضمون في تصدير Excel للموظفين | `app/routes/employees.py` |
| P1-B05 | حد محاولات OTP (5) + إتاحة مسار نسيان كلمة المرور لغير المسجَّلين | `app/routes/auth.py`, `app/__init__.py` |
| P2-BH5 | إصلاح Open Redirect عبر `request.referrer` غير مُتحقَّق منه | `app/routes/auth.py`, `commercial.py`, `reports.py` |
| P3-M07 | استبدال حلقة Python بـ`SQL MAX` لتوليد كود الموظف | `core/db_manager.py` |
| P1-C15 | ترحيل أزرار الحذف لـ`data-delete-url` (5 قوالب) | `permissions/employees/bonuses/penalties list.html` |
| TD-002 | عزل اختبارات الخزينة بقاعدة بيانات مؤقتة | `tests/test_treasury_routes.py` |
| TD-005 | إصلاح `joinedload().get()` الخطير (يتجاوز eager loading بصمت) | `treasury.py`, `accounting.py` |
| TD-003 | إصلاح تصميم اختبارات الانحدار المعيب + عزلها | `tests/test_treasury_route_eager_loading.py` |
| (إغلاق) | إغلاق سلسلة TD-002/003/005 في آخر ملف اختبار | `tests/test_treasury_routes.py` |
| TD-001 | تنظيف استيرادات غير مستخدمة | `core/services/payroll_processor.py` |
| P2-BH6 | تعطيل زر الحفظ الجماعي للرواتب لمنع الإرسال المزدوج | `employees/bulk_salaries.html` |
| P4-L03 | إصلاح عضو `THURSDAY` الناقص من `Enum` العطلة الأسبوعية | `core/database_models.py` |
| P4-L07 | حذف تحميل Font Awesome JS مكرر | `manufacturing/base_manufacturing.html` |

**نتيجة `pytest tests/` الحالية: `36 passed`، صفر فشل، ثابتة عبر تشغيلات متعددة.**

### عناصر من التقرير تم دحضها بعد تحقق مباشر (لا تُعِد فحصها ما لم يتغيّر الكود المعني)
P1-C08 (XSS مزعوم)، P1-B05 الوصف الأصلي (تجاوز OTP عبر session replay)، P2-H05 (تسريب CSRF)،
P2-H14/P3-M15 (التزام جزئي في تحديث الرواتب — الكود فعليًا ذرّي وصحيح)، P2-H17 (تكرار مزعوم في
`leave_service.py` — الدوال المذكورة غير موجودة أصلًا هناك). التفاصيل الكاملة في `TECHNICAL_DEBT.md`.

## المهمة التالية الجاهزة لـ `@cf/zai-org/glm-5.2`

### TD-006 (مسجَّلة بالفعل في `TECHNICAL_DEBT.md`) أو إحدى المهام الكبرى التالية

بعد استنفاد كل المهام الصغيرة الآمنة، المتبقي يقع في فئتين:

**أ) مهمة صغيرة متاحة فورًا:**
- **P4-L05** — تنظيف استيرادات غير مستخدمة عبر المشروع (`flake8 --select=F401 core/ app/` أظهر
  ~80 حالة عبر ~35 ملفًا). **لم أنفِّذها لأنها كبيرة جدًا لتُفعَل بأمان دفعة واحدة** — أوصي بتقسيمها
  إلى دفعات صغيرة (5-10 ملفات في كل مهمة)، والتحقق أولًا من كل استيراد: هل هو حقًا غير مُستخدَم،
  أم أنه يُعاد تصديره لملفات أخرى عبر نمط الاستيراد المسطَّح في هذا المشروع (مثال: تحقَّقت أن بعض
  استيرادات `db_manager.py` قد تبدو غير مستخدمة لكنها في الحقيقة تحتاج فحصًا دقيقًا كما حدث معي
  في TD-001 حيث كدت أحذف استيرادًا مُستخدَمًا فعليًا بالخطأ قبل أن يُنقذني `flake8`).

**ب) مبادرات كبرى تحتاج تخطيطًا مرحليًا (لا تُنفَّذ كمهمة واحدة):**
- `P1-C02` — تفكيك `DBManager` (God Class، 1,890+ سطرًا). فحصت الملف ووجدت دليلًا داعمًا حقيقيًا
  (تكرار دوال: `get_employee_by_code`, `get_all_loans` معرَّفة مرتين — `F811` من `flake8` يؤكد ذلك).
- `P1-C01` — توحيد JavaScript المُضمَّن في 15+ قالبًا
- `P1-C06`/`P1-C07` — توحيد أنظمة طباعة/تصدير متنافسة
- `P1-C11` — توريث قوالب المصادقة (3 قوالب مستقلة، من بينها صفحة تسجيل الدخول) — **يحتاج تحقُّقًا
  بصريًا** (لقطات شاشة/رندر فعلي) للتأكد من عدم كسر التنسيق، وهو أمر لم أستطع فعله في بيئتي.
  إن كانت أداة VS Code الخاصة بـ`GLM-5.2` تملك قدرة معاينة/رندر مرئي، فهذه فرصة جيدة للبدء بها.

**قرارات تحتاج تأكيدًا بشريًا من Yasser مباشرة (ليست مهام تقنية):**
- `P3-M04` — مسح البحث/الصفحة في `DataTables` بعد 30 يومًا: يبدو **مقصودًا** (يُصفّر `search` و`start`
  معًا)، وليس عطلًا. لا تُغيِّره دون تأكيد من Yasser أن هذا فعلًا غير مرغوب.
- `P4-L09` — ملف `core/services/erp_service.py` كود placeholder معلَّق صراحة لتكامل مستقبلي
  (`self.enabled = False`)، غير مُستورَد في أي مكان. حذفه أو الإبقاء عليه قرار منتج، ليس تقنيًا.

## سجل نشاط الفريق

> كل عضو يُضيف قسمًا جديدًا هنا بعد كل مهمة، بنفس هذا التنسيق، ولا يحذف أو يُعدِّل ما كتبه غيره.

### 2026-07-22 — Claude — جلسة التأسيس الأولى
انظر قائمة "ملخص ما تم إنجازه حتى الآن" أعلاه لكل التفاصيل. آخر حالة: 15 مهمة مُنفَّذة ومُتحقَّق
منها، `36/36` اختبار ناجح، لا شيء تم عمل `commit` له بعد.

### 2026-07-22 — Claude — الدفعة الأولى من P4-L05 (core/db_manager.py)

**⚠️ درس حرج لأي عضو يكمل باقي دفعات P4-L05:** حاولت حذف كل استيرادات النماذج

(ORM models)

التي أظهرها

flake8 --select=F401

كغير مستخدمة في رأس `core/db_manager.py`

(User, SystemPermission, CashAccount, BankAccount, CheckRecord, Account, CostCenter,

JournalEntry, JournalItem, Partner, Invoice, InvoiceItem, Warehouse, Product, FabricRoll,

ProductionMessage, FabricDesign)، فتعطَّل بناء التطبيق فورًا بخطأ:

```
sqlalchemy.exc.NoReferencedTableError: Foreign key associated with column
'loans.disbursed_by' could not find table 'users' with which to generate
a foreign key to target column 'id'
```

**السبب:** `DBManager.__init__` يستدعي `Base.metadata.create_all(self.engine)`. لكي تُنشَأ كل الجداول بنجاح، يجب أن تكون كل موديلات

SQLAlchemy

قد استُوردت (فسُجِّلت في

Base

metadata) **في مكان ما قبل هذا الاستدعاء**، حتى لو لم يُستخدَم الاسم مباشرة في كود

Python

بعد الاستيراد. استيراد النموذج نفسه له **أثر جانبي ضروري**

(side effect)

، وهذا ما لا يستطيع

flake8

اكتشافه — هو يفحص فقط استخدام الاسم في الكود، لا الأثر الجانبي للتسجيل.

**القاعدة المُستخلَصة لأي دفعة قادمة من P4-L05:** لا تحذف أبدًا استيراد أي صنف يرث من

Base

(أي موديل

SQLAlchemy)

حتى لو ظهر "غير مستخدَم"، إلا إذا تأكَّدت أن الملف الذي يحذفه **ليس** الملف الذي يستدعي

create_all()

، أو تحققت فعليًا ببناء التطبيق كامل بعد كل حذف (وليس فقط `flake8`/`compileall`).

### ما تم تنفيذه فعليًا في هذه الدفعة (بعد التراجع عن الجزء الخطير)

**Files changed:** `core/db_manager.py` (سطران فقط)

**Summary:** حذف استيرادين محليين

(local, function-scope)

من مكتبة

datetime

القياسية فقط (`date as date_type` في `search_loans`, و`datetime` في `export_audit_logs_csv`) — هذان آمنان لأنهما ليسا موديلات

ORM

ولا أثر جانبي لهما.

**لم يُحذَف** أي استيراد موديل من رأس الملف (تراجعت عن كل المحاولة الأولى للأسباب أعلاه).

**Verification performed:**
- `compileall` + `flake8 --select=F401,F821` ✅ (تأكدت أن السطرين المحذوفين فقط غير مُشار إليهما بعد الآن)
- بناء التطبيق الكامل (`create_app()`) ✅ 257 مسارًا — **هذا هو الفحص الذي كشف الخطأ في المحاولة الأولى**
- محاكاة فعلية: طلب `HTTP` حقيقي لـ`/loans/api/data` (يستدعي `search_loans` داخليًا) → `200 OK`
- محاكاة فعلية: استدعاء `export_audit_logs_csv()` ضمن `app_context()` حقيقي → أنشأ ملف `CSV` صحيحًا بترويسات عربية
- `pytest tests/` كاملة → `36 passed`، لا انحدار

**Suggested git commit message:**
```
refactor(db_manager): remove 2 genuinely-unused local datetime imports

Removed `from datetime import date as date_type` (search_loans) and
`from datetime import datetime` (export_audit_logs_csv) — both were
local function-scope imports never referenced in the function body.

Did NOT remove the ~18 module-level "unused" ORM model imports
(User, CashAccount, Account, etc.) that flake8 also flagged — these
turned out to be load-bearing: DBManager.__init__ calls
Base.metadata.create_all(), which requires every SQLAlchemy model to
have been imported somewhere first so it's registered in Base's
metadata, even if the class name is never referenced directly in
db_manager.py. Removing them broke app startup with
NoReferencedTableError (loans.disbursed_by -> users.id).

Verified via full create_app() build + real HTTP request + direct
function call, not just static analysis.

Refs: TECHNICAL_DEBT.md P4-L05 (partial — see AI_TEAM_HANDOFF.md for
remaining safe/unsafe batches)
```

**بقية دفعات P4-L05 المتبقية** (حوالي 78 حالة أخرى عبر ~34 ملفًا): أغلبها في ملفات

routes/

تستورد `DBManager` فقط بدون استخدامه في نطاق الاستيراد نفسه (مختلف عن حالة db_manager.py) — هذه على الأرجح آمنة، **لكن طبِّق نفس الفحص الإلزامي: بناء التطبيق الكامل بعد كل حذف، لا تكتفِ بـ`flake8`/`compileall` فقط.**

<!-- العضو التالي: أضف قسمك هنا فوق هذا التعليق -->
