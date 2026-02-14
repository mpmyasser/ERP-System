/**
 * Flatpickr Date Picker Configuration
 * يوفر تقويم منسدل مع دعم صيغة DD/MM/YYYY
 */

document.addEventListener('DOMContentLoaded', function () {
    // إعدادات Flatpickr العامة
    // إعدادات Flatpickr الأساسية
    const baseConfig = {
        dateFormat: "d/m/Y",           // عرض بصيغة DD/MM/YYYY
        mode: "single",                // تحديد تاريخ واحد
        // لا نحدد "locale" مباشرةً هنا لنتحقق أولاً إن كان locale العربي محملاً
        allowInput: true,              // السماح بالإدخال اليدوي
        clickOpens: true,              // فتح التقويم عند النقر
        time_24hr: true,
    };

    // تحقّق مبكر ما إذا كان locale العربي محملاً (قد يتم تحميله من CDN في القالب)
    const hasArabicLocale = (window.flatpickr && flatpickr.l10ns && flatpickr.l10ns.ar);
    if (!hasArabicLocale) console.warn('flatpickr: invalid locale ar - not loaded; falling back to default');

    // تطبيق Flatpickr على جميع حقول class="date-string"
    const dateInputs = document.querySelectorAll('input.date-string');

    dateInputs.forEach(input => {
        // تحويل القيم الموجودة من ISO إلى DD/MM/YYYY إذا لزم الأمر
        if (input.value && input.value.indexOf('-') >= 0) {
            const parts = input.value.split('-');
            if (parts.length === 3 && parts[0].length === 4) {
                // YYYY-MM-DD إلى DD/MM/YYYY
                input.value = parts[2] + '/' + parts[1] + '/' + parts[0];
            }
        }

        // إعداد الكونفيج الخاص بهذا الحقل
        let specificConfig = { ...baseConfig };
        if (hasArabicLocale) specificConfig.locale = flatpickr.l10ns.ar;
        else delete specificConfig.locale;

        // التحكم في التاريخ الأقصى المسموح به
        if (input.classList.contains('allow-future')) {
            // يسمح بجميع التواريخ المستقبلية
            delete specificConfig.maxDate;
        } else if (input.classList.contains('allow-month-end')) {
            // يسمح بالتواريخ حتى نهاية الشهر الحالي فقط (للسلف)
            const today = new Date();
            const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);
            specificConfig.maxDate = lastDay;
        } else {
            // الوضع الافتراضي: يمنع التواريخ المستقبلية تماماً
            specificConfig.maxDate = "today";
        }

        // تطبيق Flatpickr
        flatpickr(input, specificConfig);
    });

    // إعادة تطبيق Flatpickr على الحقول المضافة ديناميكياً (مثل الصفوف في الجداول الديناميكية)
    const observerConfig = {
        childList: true,               // مراقبة إضافة/حذف العناصر
        subtree: true,                 // مراقبة جميع الأطفال
        attributes: false
    };

    const mutationObserver = new MutationObserver(function (mutations) {
        mutations.forEach(function (mutation) {
            // البحث عن حقول date-string جديدة
            const newDateInputs = mutation.target.querySelectorAll('input.date-string:not([data-flatpickr-loaded])');

            newDateInputs.forEach(input => {
                // إضافة علامة لتجنب التطبيق المتكرر
                input.setAttribute('data-flatpickr-loaded', 'true');

                // إعداد الكونفيج الخاص بهذا الحقل الجديد
                let specificConfig = { ...baseConfig };
                if (hasArabicLocale) specificConfig.locale = flatpickr.l10ns.ar;
                else delete specificConfig.locale;

                if (input.classList.contains('allow-future')) {
                    delete specificConfig.maxDate;
                } else if (input.classList.contains('allow-month-end')) {
                    const today = new Date();
                    const lastDay = new Date(today.getFullYear(), today.getMonth() + 1, 0);
                    specificConfig.maxDate = lastDay;
                } else {
                    specificConfig.maxDate = "today";
                }

                // تطبيق Flatpickr على الحقل الجديد
                flatpickr(input, specificConfig);
            });
        });
    });

    // بدء مراقبة الـ document
    mutationObserver.observe(document.body, observerConfig);
});
