import sqlite3
import os
import sys
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def migrate():
    db_path = os.path.join(os.path.dirname(__file__), '..', 'core', 'hr.db')
    
    if not os.path.exists(db_path):
        print(f"❌ قاعدة البيانات غير موجودة: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 بدء الهجرة...")
        print(f"📍 قاعدة البيانات: {db_path}")
        
        cursor.execute("PRAGMA table_info(cash_accounts)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        
        print(f"\n📋 الأعمدة الحالية: {list(columns.keys())}")
        
        changes_made = False
        
        if 'parent_cash_id' not in columns:
            print("\n➕ إضافة عمود parent_cash_id...")
            cursor.execute("""
                ALTER TABLE cash_accounts 
                ADD COLUMN parent_cash_id INTEGER REFERENCES cash_accounts(id)
            """)
            print("   ✅ تم إضافة parent_cash_id")
            changes_made = True
        else:
            print("\n✓ عمود parent_cash_id موجود بالفعل")
        
        if 'display_order' not in columns:
            print("\n➕ إضافة عمود display_order...")
            cursor.execute("""
                ALTER TABLE cash_accounts 
                ADD COLUMN display_order INTEGER DEFAULT 0
            """)
            print("   ✅ تم إضافة display_order")
            changes_made = True
        else:
            print("\n✓ عمود display_order موجود بالفعل")
        
        if 'type' not in columns:
            print("\n➕ إضافة عمود type...")
            cursor.execute("""
                ALTER TABLE cash_accounts 
                ADD COLUMN type VARCHAR(20) DEFAULT 'General'
            """)
            print("   ✅ تم إضافة type")
            changes_made = True
        else:
            print("\n✓ عمود type موجود بالفعل")
        
        if 'user_id' not in columns:
            print("\n➕ إضافة عمود user_id...")
            cursor.execute("""
                ALTER TABLE cash_accounts 
                ADD COLUMN user_id INTEGER REFERENCES users(id)
            """)
            print("   ✅ تم إضافة user_id")
            changes_made = True
        else:
            print("\n✓ عمود user_id موجود بالفعل")
        
        if changes_made:
            cursor.execute("""
                UPDATE cash_accounts 
                SET display_order = id 
                WHERE display_order IS NULL OR display_order = 0
            """)
            print("\n📊 تحديث قيم display_order...")
            
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_cash_accounts_parent_id ON cash_accounts(parent_cash_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_cash_accounts_user_id ON cash_accounts(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_cash_accounts_type ON cash_accounts(type)")
            except:
                pass
            
            print("📑 تم إنشاء الفهارس للأداء الأفضل")
        
        conn.commit()
        
        cursor.execute("PRAGMA table_info(cash_accounts)")
        final_columns = [row[1] for row in cursor.fetchall()]
        
        print("\n" + "="*50)
        print("✅ الهجرة اكتملت بنجاح!")
        print("="*50)
        print(f"الأعمدة النهائية: {final_columns}\n")
        
        required_cols = ['parent_cash_id', 'display_order', 'type']
        missing = [col for col in required_cols if col not in final_columns]
        
        if missing:
            print(f"⚠️ أعمدة مفقودة: {missing}")
            return False
        
        print("✅ جميع الأعمدة المطلوبة موجودة الآن")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ خطأ أثناء الهجرة: {e}")
        return False

if __name__ == '__main__':
    success = migrate()
    exit(0 if success else 1)
