// Custom JavaScript for HR System

// Show a centered flash dialog (used by server-side flashes with category 'center')
// - If SweetAlert2 (Swal) is available we show a centered modal
// - Otherwise fall back to a browser alert
function showCenteredFlash(message, category = 'info') {
    const iconMap = {
        success: 'success',
        danger: 'error',
        error: 'error',
        warning: 'warning',
        info: 'info',
        center: 'info'
    };
    const icon = iconMap[category] || 'info';

    // Prefer SweetAlert2 for a centered modal
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            icon: icon,
            title: '',
            html: `<div lang="ar" dir="rtl">${message}</div>`,
            confirmButtonText: 'حسنًا',
            allowOutsideClick: true,
            didOpen: (popup) => {
                popup.setAttribute('lang', 'ar');
                popup.setAttribute('dir', 'rtl');
            }
        });
        return;
    }

    // Fallback to simple alert (strip HTML tags)
    const plain = message.replace(/<[^>]*>/g, '').replace(/\n+/g, '\\n');
    alert(plain);
}

document.addEventListener('DOMContentLoaded', function () {
    // Auto-hide only flash alerts marked with `auto-dismiss` after 5 seconds
    const alerts = document.querySelectorAll('.alert.auto-dismiss');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.remove('show');
            setTimeout(() => alert.remove(), 150);
        }, 5000);
    });

    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function (e) {
            if (!confirm('هل أنت متأكد من الحذف؟')) {
                e.preventDefault();
            }
        });
    });
});
