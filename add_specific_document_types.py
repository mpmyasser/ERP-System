import sqlite3
import os

def add_specific_document_types():
    db_path = os.path.join('core', 'hr.db')
    if not os.path.exists(db_path):
        print(f"[!] قاعدة البيانات غير موجودة في {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("[*] بدء إضافة أنواع المستندات الجديدة...")

    new_types = [
        ('برنت تأميني', 'Insurance Printout', 1),
        ('كعب العمل', 'Employment Status Form', 0),
        ('شهادة قياس مستوى مهارة', 'Skill Level Measurement Certificate', 1),
        ('صورة رخصة القيادة', 'Driving License Copy', 1),
        ('صورة البطاقة الشخصية', 'National ID Card Copy', 1)
    ]

    for name, desc, needs_expiry in new_types:
        try:
            # محاولة الإضافة أو التحديث إذا كان موجوداً
            cursor.execute('''
                INSERT INTO document_types (name, description, needs_expiry) 
                VALUES (?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET 
                    description=excluded.description,
                    needs_expiry=excluded.needs_expiry
            ''', (name, desc, needs_expiry))
            print(f"[+] تم إضافة/تحديث: {name}")
        except Exception as e:
            print(f"[-] خطأ أثناء إضافة {name}: {str(e)}")

    try:
        conn.commit()
        print("[OK] تم حفظ التغييرات بنجاح.")
    except Exception as e:
        print(f"[ERROR] فشل حفظ التغييرات: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_specific_document_types()
