# AI Agents Skills Manifest (دليل مهارات وكلاء الذكاء الاصطناعي)

**Last Updated**: 2026-06-15

هذا الملف يجمع جميع المهارات المتاحة للـ AI agents. يجب قراءة هذا الملف بالكامل قبل تنفيذ أي مهمة.

---

## 📋 جدول المحتويات

1. [Print Governance Skill](#print-governance-skill)

---

## Print Governance Skill

**المسار**: `.agents/skills/print_governance/SKILL.md`

**الوصف**: تعليمات للحفاظ على حماية نظام الطباعة الذكي في DataTables.

### 🛡️ الأجزاء المحمية (Protected Logic)

الأجزاء التالية **يجب ألا تُستبدل** برمز عام:

1. **Smart Grouping Detection**: الكود الذي يستخدم `groupKeywords` للعثور على عمود التجميع
2. **Sectional Printing**: منطق تقسيم البيانات إلى `groups` والتكرار عليها
3. **Variable Initialization**: تأكد دائماً من تعريف `settings`, `$printBody`, `marginTop`, `marginBottom`, و `orientation` في بداية دالة `customize`
4. **Subtotals and Grand Totals**: منطق حساب التذييل داخل حلقة كل مجموعة والجدول الإجمالي النهائي
5. **Paper Saving (Continuous Flow)**: استخدام `$groupWrapper` مع `page-break-inside: avoid` بدلاً من فواصل الصفحات القسرية
6. **Column Width Sync**: استخدام `_capturedWidths` لتطبيق عرض الشاشة على خلايا الطباعة

### ⚠️ الأخطاء الشائعة (Common Pitfalls)

**يجب تجنب**:
- استخدام `$(win.document.body).empty()` إلا إذا تبعته مباشرة بـ `.append($wrapper)`
- تأكد دائماً من أن `settings` تم تحليله من `localStorage` قبل استخدام أي متغير إعدادات
- عند إضافة ميزات جديدة، استخدم `multi_replace_file_content` لتحرير أسطر محددة بدلاً من استبدال كتلة `customize` بأكملها

### 🖋️ معيار التوقيعات الموحد (Global Signature Standard)

أي تقرير أو مستند يتطلب توقيعات (الإيصالات والبيانات والقسائم وما إلى ذلك) **يجب** أن يتوافق مع المعيار العام التالي:

1. **Strict Vertical Centering**: خطوط التوقيع **يجب** أن تكون مركزة تماماً بين التسمية (مثل "Receiver Signature") والحافة السفلية لحاويتها
2. **Container Height**: صناديق/حاويات التوقيع **يجب** أن يكون لها حد أدنى من الارتفاع `85px` لضمان مساحة كافية للتوسيط والتوقيع اليدوي
3. **Self-Containment (العزل التام)**: لا تعتمد على متغيرات CSS خارجية (مثل `var(--sig-line-style)`). قم بترميز النمط مباشرة في كتلة النمط الخاصة بالقالب لضمان الرؤية في نوافذ الطباعة المستقلة
4. **High-Contrast Lines**: استخدم `border-bottom: 2px solid #000 !important;` لجميع خطوط التوقيع. يجب أن يكون عرضها `180px` ومركزة أفقياً داخل صندوقها
5. **Layout**: استخدم `flexbox` مع `flex-direction: column` و `justify-content: space-between` لدفع التسمية إلى الأعلى والخط إلى الأسفل من الحاوية
6. **Zero Timestamp Redundancy (منع التكرار)**: لا تضمن التاريخ/الوقت داخل نص التقرير إذا كان موجوداً في الرأس. يجب أن يتحكم مفتاح "Show Time" في التاريخ والوقت معاً لتحسين المساحة الرأسية
7. **Reference Integrity (سلامة المراجع)**: أعد تهيئة مراجع DOM الحرجة (مثل Balance و Deduction و Totals) محلياً داخل معالج النقر/الطباعة. هذا يمنع فقدان البيانات إذا تم حجب المؤشرات العامة أو فقدانها أثناء إعادة الهيكلة
8. **Smart Advance Hiding (الإخفاء الذكي)**: بطاقات Advance/Balance في "Quick Reports" يجب أن تكون **مخفية فقط** إذا كانت جميع القيم الثلاث (Previous Balance و Deduction و Balance After) تساوي صفراً بالضبط. يجب الحفاظ على هذا المنطق للحفاظ على الشفافية المالية
9. **Backend Connectivity Integrity (سلامة الاتصال بالخلفية)**: الوظائف المالية الأساسية (خاصة `get_factory_balance`) هي قلب النظام. لا تزل أو تعدل استيراداتها في `operation_app.py` دون التحقق من أن جميع الوحدات المحاسبية (Summary Bar و Reports و Archives) لا تزال تعمل
10. **Print Contrast & Formatting (جودة التباين والخطوط)**: جميع القيم المالية في التقارير المطبوعة **يجب** أن تكون مجبرة على اللون الأسود العميق (`#000 !important`). لا تستخدم فئات ألوان Bootstrap (`text-success` و `text-warning`) في المخرجات المطبوعة لأنها تبدو باهتة. خطوط التوقيع **يجب** أن تكون صلبة (`1.5px solid #000`)، وليست منقطة أو رمادية فاتحة
11. **Flexible Row Height (التحكم في ارتفاع الصفوف)**: يمكن للمستخدمين التحكم في الكثافة الرأسية للطباعة عبر منزلق. يتم تنفيذ هذا عالمياً باستخدام مفتاح `global_print_row_padding_pt` في `localStorage` و متغير CSS `--table-row-padding-pt` و تكوين `rowPadding` في `printTable`. لا تقم بترميز الحشو الرأسي الثابت في أنماط الجدول التي قد تتجاوز تفضيل المستخدم العام هذا

### 🛠️ كيفية إضافة ميزة جديدة

إذا كنت بحاجة إلى إضافة خيار طباعة جديد:

1. حدّث لوحة الإعدادات لإضافة عنصر واجهة المستخدم
2. حدّث معالج الحدث لحفظ القيمة في `localStorage`
3. في منطق الطباعة، اقرأ القيمة وطبقها بدقة
4. **GUARD COMMENTS**: عند تحرير كتل الطباعة الحرجة، لفها في تعليقات:
   ```
   /* GUARD: CRITICAL PRINT LOGIC - DO NOT REMOVE */
   ```
5. **REGRESSION CHECK**: قارن دائماً المخرجات الجديدة مع `manufacturer_accounts.html.before_compact_print.bak` للتأكد من عدم فقدان أي منطق أصلي

---

## 📝 ملاحظات للـ AI Agents

### قبل البدء بأي مهمة:

1. **اقرأ هذا الملف بالكامل** - جميع المهارات والقيود موثقة هنا
2. **تحقق من المهارات ذات الصلة** - إذا كانت مهمتك تتعلق بالطباعة، راجع Print Governance Skill
3. **احترم الأجزاء المحمية** - لا تستبدل الكود المحمي برمز عام
4. **استخدم التحرير الجراحي** - استخدم `multi_replace_file_content` للتعديلات الدقيقة
5. **اختبر الانحدار** - تأكد من عدم كسر الوظائف الموجودة

---

**آخر تحديث**: 2026-06-15
