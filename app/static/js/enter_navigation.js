/**
 * نظام التنقل بين الحقول باستخدام Enter
 * Enter Navigation System - Allows form navigation using Enter key
 */

document.addEventListener('DOMContentLoaded', function() {
    // الحصول على جميع مدخلات النموذج (input, select, textarea)
    const formInputs = document.querySelectorAll('input:not([type="hidden"]):not([type="checkbox"]):not([type="radio"]), select, textarea');
    
    // إضافة معالج الأحداث لكل حقل
    formInputs.forEach((input, index) => {
        input.addEventListener('keydown', function(e) {
            // إذا تم الضغط على Enter
            if (e.key === 'Enter') {
                // الحقول الخاصة التي يجب أن تعمل فيها Enter بشكل طبيعي (مثل textarea)
                if (this.tagName === 'TEXTAREA' && !e.ctrlKey) {
                    return; // السماح بـ Enter العادي في textarea
                }
                
                e.preventDefault(); // منع الإرسال الافتراضي
                
                // --- التحقق من صحة الحقل قبل الانتقال (Validation) ---
                
                // 1. حقل كود الموظف
                if (this.classList.contains('emp-code')) {
                    if (!this.value.trim()) {
                        this.classList.add('is-invalid');
                        // لا تحبس التركيز إذا كان الحقل فارغاً في الإدخال الجماعي لسهولة التنقل
                        const isBulk = document.getElementById('bulkBody') !== null;
                        if (!isBulk) {
                            this.focus();
                            this.select();
                        }
                        return;
                    }
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                }
                
                // 2. حقل المبلغ
                if (this.classList.contains('amount') || this.id === 'amount' || this.name === 'amount') {
                    const val = parseFloat(this.value);
                    if (isNaN(val) || val <= 0) {
                        // استثناء: في الجزاءات قد يكون المبلغ 0 إذا تم اختيار أيام خصم
                        const row = this.closest('tr');
                        const days = row ? row.querySelector('.days')?.value : null;
                        
                        if (!(days && parseFloat(days) > 0)) {
                            this.classList.add('is-invalid');
                            this.focus();
                            this.select();
                            return;
                        }
                    }
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                }

                // 3. حقول الاختيار الإلزامية
                if (this.tagName === 'SELECT' && this.required && !this.value) {
                    this.classList.add('is-invalid');
                    this.focus();
                    return;
                }
                
                // --- الانتقال إلى الحقل التالي ---
                let nextIndex = index + 1;
                
                // تخطي الحقول المخفية والمعطلة
                while (nextIndex < formInputs.length) {
                    if (!formInputs[nextIndex].disabled && formInputs[nextIndex].offsetParent !== null) {
                        formInputs[nextIndex].focus();
                        // تحديد النص في حقول الإدخال
                        if (formInputs[nextIndex].type === 'text' || formInputs[nextIndex].type === 'date') {
                            formInputs[nextIndex].select();
                        }
                        return;
                    }
                    nextIndex++;
                }
                
                // إذا كان هذا آخر حقل، ركز على زر الإرسال
                const submitBtn = document.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.focus();
                }
            }
            
            // السماح بـ Shift+Enter للرجوع للحقل السابق
            if (e.key === 'Enter' && e.shiftKey) {
                e.preventDefault();
                
                let prevIndex = index - 1;
                
                while (prevIndex >= 0) {
                    if (!formInputs[prevIndex].disabled && formInputs[prevIndex].offsetParent !== null) {
                        formInputs[prevIndex].focus();
                        if (formInputs[prevIndex].type === 'text' || formInputs[prevIndex].type === 'date') {
                            formInputs[prevIndex].select();
                        }
                        return;
                    }
                    prevIndex--;
                }
            }
        });
    });
    
    // معالج خاص للأزرار
    const buttons = document.querySelectorAll('button');
    buttons.forEach((button, index) => {
        button.addEventListener('keydown', function(e) {
            // السماح بـ Enter لتفعيل الزر
            if (e.key === 'Enter') {
                e.preventDefault();
                this.click();
            }
        });
    });
});
