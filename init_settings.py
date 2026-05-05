import sqlite3
import os

def init_system_settings():
    db_path = os.path.join('core', 'hr.db')
    if not os.path.exists(db_path):
        print(f"[!] قاعدة البيانات غير موجودة في {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("[*] بدء جرد وتهيئة إعدادات النظام...")

    # 1. إنشاء الجدول إذا لم يكن موجوداً
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE,
            value TEXT NOT NULL,
            description TEXT,
            category TEXT,
            data_type TEXT DEFAULT 'string'
        )
    ''')
    print("[+] تم التأكد من وجود جدول system_settings.")

    # 2. الإعدادات الافتراضية بناءً على HRPolicy
    settings = [
        # الحضور والتأخير
        ('WORKING_DAYS_PER_MONTH', '26', 'عدد أيام العمل في الشهر لحساب اليومية', 'Financial', 'int'),
        ('LATE_GRACE_PERIOD_MINUTES', '10', 'فترة السماح للتأخير الصباحي بالدقائق', 'Attendance', 'int'),
        ('LATE_MULTIPLIER', '1.0', 'مضاعف خصم دقائق التأخير (1.0 يعني دقيقة بدقيقة)', 'Attendance', 'float'),
        ('EARLY_DEPARTURE_GRACE_PERIOD_MINUTES', '0', 'فترة السماح للانصراف المبكر بالدقائق', 'Attendance', 'int'),
        ('EARLY_DEPARTURE_MULTIPLIER', '1.0', 'مضاعف خصم دقائق الانصراف المبكر', 'Attendance', 'float'),
        
        # الإضافي والحوافز
        ('OVERTIME_MIN_MINUTES', '60', 'الحد الأدنى لاستحقاق الإضافي بالأدقائق (عتبة الاستحقاق)', 'Overtime', 'int'),
        ('OVERTIME_RATE', '1.5', 'معدل حساب ساعة الإضافي (مثلا 1.5 يعني الساعة بساعة ونصف)', 'Overtime', 'float'),
        ('OVERTIME_FIRST_HOUR_FIXED', 'True', 'تثبيت أول ساعة إضافي كساعة كاملة بمجرد تجاوز الحد الأدنى (True/False)', 'Overtime', 'boolean'),
        ('OVERTIME_ROUNDING_MODE', 'HALF_HOUR', 'طريقة تقريب الإضافي بعد الساعة الأولى (HALF_HOUR / FULL_HOUR / NONE)', 'Overtime', 'select'),
        ('OVERTIME_ROUND_THRESHOLD_MINUTES', '30', 'عدد الدقائق اللازمة للتقريب لأعلى (مثلاً 30 دقيقة تساوي نصف ساعة)', 'Overtime', 'int'),
        ('INCENTIVE_FULL_THRESHOLD', '24', 'عدد أيام الحضور المطلوبة لاستحقاق حافز الانتظام الكامل', 'Incentives', 'int'),
        ('INCENTIVE_HALF_THRESHOLD', '15', 'عدد أيام الحضور المطلوبة لاستحقاق نصف حافز الانتظام', 'Incentives', 'int'),
        
        # الغياب والجزاءات
        ('ABSENCE_GRACE_DAYS', '2', 'عدد أيام الغياب المسموحة (يوم بيوم) قبل تطبيق الجزاء الإضافي', 'Absence', 'int'),
        ('ABSENCE_PENALTY_DAYS', '0.25', 'قيمة الجزاء الإضافي لكل يوم غياب زائد عن المسموح (باليوم)', 'Absence', 'float'),
        
        # الدورة المالية والتقريب
        ('PAYROLL_START_DAY', '26', 'يوم بداية الدورة الشهرية للرواتب', 'Financial', 'int'),
        ('PAYROLL_END_DAY', '25', 'يوم نهاية الدورة الشهرية للرواتب', 'Financial', 'int'),
        ('ROUNDING_BASE', '5', 'قاعدة تقريب صافي الراتب (مثلاً لأقرب 5 جنيهات)', 'Financial', 'int')
    ]

    for key, val, desc, cat, dtype in settings:
        try:
            cursor.execute('''
                INSERT INTO system_settings (key, value, description, category, data_type)
                VALUES (?, ?, ?, ?, ?)
            ''', (key, val, desc, cat, dtype))
            print(f"[+] إضافة الإعداد: {key} = {val}")
        except sqlite3.IntegrityError:
            print(f"[-] الإعداد {key} موجود مسبقاً، تخطي.")

    conn.commit()
    conn.close()
    print("[OK] اكتملت تهيئة الإعدادات.")

if __name__ == "__main__":
    init_system_settings()
