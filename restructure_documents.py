# -*- coding: utf-8 -*-
"""
Script to restructure document types:
1. Merge "صورة البطاقة الشخصية" into "صورة البطاقة" 
2. Add new type "صورة شخصية"
"""

import sqlite3
import sys
import os

# Set UTF-8 encoding for console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

DB_PATH = 'core/hr.db'

def main():
    print("=" * 60)
    print("📋 إعادة هيكلة أنواع المستندات")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Step 1: Display current document types
        print("\n1️⃣ الأنواع الحالية:")
        print("-" * 60)
        cursor.execute('SELECT id, name, is_required FROM document_types ORDER BY id')
        types = cursor.fetchall()
        for t in types:
            print(f"   {t[0]:2d}. {t[1]} (مطلوب: {'نعم' if t[2] else 'لا'})")
        
        # Step 2: Find IDs for both "صورة البطاقة" types
        cursor.execute('SELECT id FROM document_types WHERE name = ?', ('صورة البطاقة',))
        id_card_result = cursor.fetchone()
        
        cursor.execute('SELECT id FROM document_types WHERE name = ?', ('صورة البطاقة الشخصية',))
        personal_id_result = cursor.fetchone()
        
        if not id_card_result:
            print("\n⚠️ لم يتم العثور على نوع 'صورة البطاقة'")
            print("   سيتم إنشاؤه...")
            cursor.execute('''INSERT INTO document_types (name, description, needs_expiry, is_required) 
                           VALUES (?, ?, ?, ?)''', 
                         ('صورة البطاقة', 'نسخة من البطاقة الشخصية', 1, 1))
            conn.commit()
            id_card_id = cursor.lastrowid
            print(f"   ✅ تم إنشاء نوع 'صورة البطاقة' بالرقم {id_card_id}")
        else:
            id_card_id = id_card_result[0]
            print(f"\n✅ تم العثور على 'صورة البطاقة' (ID: {id_card_id})")
        
        if personal_id_result:
            personal_id_id = personal_id_result[0]
            print(f"✅ تم العثور على 'صورة البطاقة الشخصية' (ID: {personal_id_id})")
            
            # Step 3: Check if there are documents with "صورة البطاقة الشخصية"
            cursor.execute('''SELECT COUNT(*) FROM employee_documents 
                           WHERE type_id = ?''', (personal_id_id,))
            count = cursor.fetchone()[0]
            
            print(f"\n2️⃣ عدد المستندات المرفوعة لـ'صورة البطاقة الشخصية': {count}")
            
            if count > 0:
                # Step 4: Migrate documents to "صورة البطاقة"
                print(f"   🔄 نقل {count} مستند إلى 'صورة البطاقة'...")
                cursor.execute('''UPDATE employee_documents 
                               SET type_id = ? 
                               WHERE type_id = ?''', (id_card_id, personal_id_id))
                conn.commit()
                print("   ✅ تم النقل بنجاح")
            
            # Step 5: Delete "صورة البطاقة الشخصية" type
            print(f"\n3️⃣ حذف نوع 'صورة البطاقة الشخصية'...")
            cursor.execute('DELETE FROM document_types WHERE id = ?', (personal_id_id,))
            conn.commit()
            print("   ✅ تم الحذف بنجاح")
        else:
            print("\nℹ️ لا يوجد نوع 'صورة البطاقة الشخصية' للحذف")
        
        # Step 6: Add "صورة شخصية" if it doesn't exist
        cursor.execute('SELECT id FROM document_types WHERE name = ?', ('صورة شخصية',))
        photo_result = cursor.fetchone()
        
        if not photo_result:
            print(f"\n4️⃣ إضافة نوع 'صورة شخصية' الجديد...")
            cursor.execute('''INSERT INTO document_types (name, description, needs_expiry, is_required) 
                           VALUES (?, ?, ?, ?)''', 
                         ('صورة شخصية', 'صورة شخصية للموظف', 0, 0))
            conn.commit()
            photo_id = cursor.lastrowid
            print(f"   ✅ تم إنشاء 'صورة شخصية' بالرقم {photo_id} (اختياري)")
        else:
            print(f"\nℹ️ نوع 'صورة شخصية' موجود بالفعل (ID: {photo_result[0]})")
        
        # Step 7: Display final document types
        print("\n5️⃣ الأنواع النهائية:")
        print("-" * 60)
        cursor.execute('SELECT id, name, is_required FROM document_types ORDER BY id')
        types = cursor.fetchall()
        for t in types:
            required_text = 'مطلوب' if t[2] else 'اختياري'
            print(f"   {t[0]:2d}. {t[1]} ({required_text})")
        
        print("\n" + "=" * 60)
        print("✅ اكتملت عملية إعادة الهيكلة بنجاح!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ حدث خطأ: {e}")
        conn.rollback()
        return 1
    finally:
        conn.close()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
