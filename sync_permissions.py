import sys
import os

# Add core to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
core_dir = os.path.join(current_dir, 'core')
if core_dir not in sys.path:
    sys.path.insert(0, core_dir)

from db_manager import DBManager
from auth_models import SystemPermission

def add_new_permissions():
    print("Adding HR granular permissions...")
    db = DBManager()
    session = db.get_session()
    
    # List of new permissions to target
    new_perms = [
        # Dashboard & Navigation
        {'name': 'view_dashboard', 'desc': 'عرض لوحة التحكم الرئيسية', 'cat': 'Core'},
        # HR Detailed
        {'name': 'view_employees', 'desc': 'عرض شاشة الموظفين', 'cat': 'HR'},
        {'name': 'view_departments', 'desc': 'عرض شاشة الأقسام', 'cat': 'HR'},
        {'name': 'view_loans', 'desc': 'عرض شاشة السلف', 'cat': 'HR'},
        {'name': 'view_loans_report', 'desc': 'تقرير السلف المستديمة والمؤقتة', 'cat': 'HR'},
        {'name': 'view_attendance', 'desc': 'عرض كشوف الحضور والانصراف', 'cat': 'HR'},
        {'name': 'view_penalties', 'desc': 'عرض وإدارة الجزاءات', 'cat': 'HR'},
        {'name': 'view_bonuses', 'desc': 'عرض وإدارة المكافآت', 'cat': 'HR'},
        {'name': 'view_permissions', 'desc': 'عرض وإدارة تصاريح الخروج', 'cat': 'HR'},
        {'name': 'view_leaves', 'desc': 'عرض وإدارة الإجازات', 'cat': 'HR'},
        {'name': 'view_payroll', 'desc': 'عرض معالجة الرواتب والشرائح', 'cat': 'HR'},
        {'name': 'view_hr_reports', 'desc': 'عرض التقارير الإدارية وتقارير الموظفين', 'cat': 'HR'},
        {'name': 'bulk_salary_manage', 'desc': 'إدارة تعديل المرتبات جماعياً (حفظ/تراجع)', 'cat': 'HR'},
        # Commercial Detailed
        {'name': 'view_commercial', 'desc': 'عرض دورة المبيعات والمشتريات', 'cat': 'Commercial'},
        {'name': 'view_treasury', 'desc': 'عرض الخزينة والحسابات البنكية', 'cat': 'Treasury'},
        {'name': 'view_manufacturing', 'desc': 'عرض الإنتاج وتتبع القصات', 'cat': 'Manufacturing'}
    ]
    
    added_count = 0
    for p_data in new_perms:
        existing = session.query(SystemPermission).filter_by(name=p_data['name']).first()
        if not existing:
            new_p = SystemPermission(
                name=p_data['name'],
                description=p_data['desc'],
                category=p_data['cat']
            )
            session.add(new_p)
            added_count += 1
            print(f"Added: {p_data['name']}")
    
    session.commit()
    print(f"Done. Added {added_count} new permissions.")
    session.close()

if __name__ == "__main__":
    add_new_permissions()
