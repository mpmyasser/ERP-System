import os
import sys
import sqlite3

# إضافة مسار المشروع ومجلد حركة التشغيل
sys.path.insert(0, os.path.abspath('.'))

op_db_path = r'e:\backoup\25-2-2026\حركة التشغيل\data\operation.db'
seed_file_path = r'e:\backoup\25-2-2026\seed_products.py'

if not os.path.exists(op_db_path):
    print("Operation DB not found.")
    sys.exit(1)

if not os.path.exists(seed_file_path):
    print("seed_products.py not found.")
    sys.exit(1)

# استخراج raw_data من ملف seed_products.py ديناميكياً لتجنب إعادة كتابتها
raw_data = ""
with open(seed_file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
# البحث عن بداية ونهاية raw_data في الملف
in_raw_data = False
for line in lines:
    if 'raw_data = """' in line:
        in_raw_data = True
        continue
    elif in_raw_data and '"""' in line:
        in_raw_data = False
        break
    if in_raw_data:
        raw_data += line

if not raw_data:
    print("Could not extract raw_data from seed_products.py")
    sys.exit(1)

# تحليل البيانات
products_to_add = []
for line in raw_data.strip().split('\n'):
    parts = line.split('\t')
    if len(parts) < 2:
        continue
    code = parts[0].strip()
    name = parts[1].strip()
    size = parts[2].strip() if len(parts) > 2 else ""
    if code and name:
        products_to_add.append((code, name, size))

print(f"Extracted {len(products_to_add)} products from seed_products.py")

# إدراجها في قاعدة البيانات
conn = sqlite3.connect(op_db_path)
cursor = conn.cursor()

inserted_count = 0
for code, name, size in products_to_add:
    # التحقق مما إذا كان كود الصنف موجوداً بالفعل في جدول operation_products
    cursor.execute("SELECT COUNT(*) FROM operation_products WHERE code = ?", (code,))
    exists = cursor.fetchone()[0] > 0
    if not exists:
        cursor.execute(
            "INSERT INTO operation_products (code, name, size) VALUES (?, ?, ?)",
            (code, name, size)
        )
        inserted_count += 1

conn.commit()
conn.close()

print(f"Successfully restored database. Added {inserted_count} new products. Total products now in operation_products table should be verified.")
