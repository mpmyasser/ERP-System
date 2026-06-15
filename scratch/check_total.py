import os
import sys

sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('./حركة التشغيل'))

try:
    from app.routes import operation_storage as storage
    items = storage.get_reference_items(limit=1000, offset=0)
    print(f"Total items fetched: {len(items)}")
    codes = [item.get('code') for item in items]
    print("All available codes in DB:")
    print(sorted(codes, key=lambda x: int(x) if str(x).isdigit() else 9999))
except Exception as e:
    print(f"Error checking DB: {e}")
