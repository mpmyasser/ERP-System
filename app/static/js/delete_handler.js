/**
 * دوال الحذف الموحدة لجميع الجداول
 * يتم استخدام data-* attributes بدلاً من inline JavaScript
 */

document.addEventListener('DOMContentLoaded', function () {
    // إضافة مستمع للنقر على أزرار الحذف
    document.addEventListener('click', function (event) {
        const deleteBtn = event.target.closest('.delete-record-btn');
        if (!deleteBtn) return;

        event.preventDefault();

        const module = deleteBtn.dataset.module;
        const recordId = deleteBtn.dataset.id;
        const confirmMessage = deleteBtn.dataset.confirm || 'هل أنت متأكد من الحذف؟';

        if (!confirm(confirmMessage)) {
            return;
        }

        // بناء رابط الحذف بناءً على الموديول
        let deleteUrl = '';
        switch (module) {
            case 'employees':
                deleteUrl = `/employees/${recordId}/delete`;
                break;
            case 'bonuses':
                deleteUrl = `/bonuses/${recordId}/delete`;
                break;
            case 'penalties':
                deleteUrl = `/penalties/${recordId}/delete`;
                break;
            case 'permissions':
                deleteUrl = `/permissions/${recordId}/delete`;
                break;
            case 'leaves':
                deleteUrl = `/leaves/${recordId}/delete`;
                break;
            case 'loans':
                deleteUrl = `/loans/${recordId}/delete`;
                break;
            default:
                console.error('Unknown module:', module);
                return;
        }

        // الحصول على CSRF token
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content ||
            document.querySelector('input[name="csrf_token"]')?.value || '';

        // إرسال طلب الحذف
        fetch(deleteUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            }
        })
            .then(response => {
                if (response.ok) {
                    // إعادة تحميل الصفحة للحفاظ على الفلاتر والترتيب بشكل تلقائي
                    window.location.reload();
                } else {
                    alert('حدث خطأ في حذف السجل');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('حدث خطأ في الاتصال');
            });
    });
});
