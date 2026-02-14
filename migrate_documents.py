import sqlite3
import os

def migrate_documents():
    db_path = os.path.join('core', 'hr.db')
    if not os.path.exists(db_path):
        print(f"[!] قاعدة البيانات غير موجودة في {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("[*] بدء تحديث جداول المستندات...")

    try:
        # 1. إنشاء جدول أنواع المستندات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                needs_expiry BOOLEAN DEFAULT 0
            )
        ''')
        print("[+] تم إنشاء جدول document_types بنجاح.")

        # 2. إضافة الأنواع الافتراضية
        default_types = [
            ('صورة البطاقة', 'ID Card Copy', 1),
            ('شهادة الميلاد', 'Birth Certificate', 0),
            ('الموقف من التجنيد', 'Military Status', 0),
            ('عقد العمل', 'Employment Contract', 1),
            ('شهادة صحية', 'Health Certificate', 1),
            ('فيش جنائي', 'Background Check', 0),
            ('أخرى', 'Other documents', 0)
        ]
        
        for t in default_types:
            try:
                cursor.execute('INSERT INTO document_types (name, description, needs_expiry) VALUES (?, ?, ?)', t)
            except sqlite3.IntegrityError:
                pass # النوع موجود مسبقاً
        print("[+] تم إضافة الأنواع الافتراضية للمستندات.")

        # 3. تحديث جدول مستندات الموظفين
        # الكولومز الجديدة: type_id, expiry_date, notes
        
        cols_to_add = [
            ('type_id', 'INTEGER'),
            ('expiry_date', 'DATE'),
            ('notes', 'TEXT')
        ]

        for col_name, col_type in cols_to_add:
            try:
                cursor.execute(f'ALTER TABLE employee_documents ADD COLUMN {col_name} {col_type}')
                print(f"[+] تم إضافة العمود {col_name} لجدول employee_documents.")
            except sqlite3.OperationalError:
                print(f"[-] العمود {col_name} موجود بالفعل.")

        conn.commit()
        print("[OK] اكتملت عملية التحديث بنجاح.")

    except Exception as e:
        print(f"[ERROR] حدث خطأ أثناء التحديث: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_documents()
