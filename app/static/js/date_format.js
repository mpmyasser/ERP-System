/**
 * فرض صيغة التاريخ DD/MM/YYYY
 * Force Date Format DD/MM/YYYY
 * يتعامل مع الإدخال اليدوي والحقول النصية
 * Flatpickr يتولى حقول التاريخ (date-string)
 */

document.addEventListener('DOMContentLoaded', function () {
    // الحصول على جميع حقول التاريخ النصية المحددة (class date-string)
    const dateInputs = document.querySelectorAll('input.date-string');

    dateInputs.forEach(input => {
        // Format on load if value exists (ISO to DD/MM/YYYY)
        if (input.value && input.value.indexOf('-') >= 0) {
            const parts = input.value.split('-');
            if (parts.length === 3) {
                // Check if it is YYYY-MM-DD (4-2-2)
                if (parts[0].length === 4) {
                    input.value = parts[2] + '/' + parts[1] + '/' + parts[0];
                }
            }
        }

        // Focus handler: show placeholder
        input.addEventListener('focus', function () {
            if (!this.value) {
                this.setAttribute('placeholder', 'DD/MM/YYYY');
            }
        });

        // On blur: normalize ISO YYYY-MM-DD to DD/MM/YYYY and trim
        input.addEventListener('blur', function () {
            if (this.value) {
                if (this.value.indexOf('-') >= 0) {
                    const parts = this.value.split('-');
                    if (parts.length === 3) {
                        // Check if it is YYYY-MM-DD (4-2-2)
                        if (parts[0].length === 4) {
                            this.value = parts[2] + '/' + parts[1] + '/' + parts[0];
                        }
                    }
                }
                this.value = this.value.trim();
            }
        });

        // Input handler: allow DDMMYYYY or DD/MM/YYYY, auto-format
        // تخطي هذا إذا كان Flatpickr يتولى الحقل
        if (!input.getAttribute('data-flatpickr-loaded')) {
            input.addEventListener('input', function (e) {
                const value = this.value || '';
                if (!value) return;
                const cleaned = value.replace(/\D/g, '');
                let formatted = '';

                if (cleaned.length <= 2) {
                    formatted = cleaned;
                } else if (cleaned.length <= 4) {
                    formatted = cleaned.substring(0, 2) + '/' + cleaned.substring(2);
                } else if (cleaned.length <= 8) {
                    formatted = cleaned.substring(0, 2) + '/' + cleaned.substring(2, 4) + '/' + cleaned.substring(4, 8);
                }

                this.value = formatted;
            });
        }
    });
});
