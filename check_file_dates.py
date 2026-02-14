import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

import pandas as pd
from datetime import datetime

# Read the file
filepath = 'app/uploads/1.xls'
df = pd.read_excel(filepath, engine='xlrd')

print("فحص محتوى ملف الاستيراد")
print("=" * 60)
print(f"عدد الصفوف الكلي: {len(df)}")
print(f"عدد الأعمدة: {len(df.columns)}")

# Extract and analyze dates
dates_in_file = set()

for index, row in df.iterrows():
    values = row.values.tolist()
    if len(values) >= 3:
        date_raw = values[2]
        if pd.notna(date_raw):
            date_str = str(date_raw).strip()
            if date_str and date_str != 'nan':
                try:
                    if '/' in date_str:
                        date_obj = pd.to_datetime(date_str, format='%d/%m/%Y').date()
                    else:
                        date_obj = pd.to_datetime(date_str).date()
                    dates_in_file.add(date_obj)
                except:
                    pass

print(f"\nالتواريخ الموجودة في الملف:")
for d in sorted(dates_in_file):
    # Count records for each date
    count = 0
    for index, row in df.iterrows():
        values = row.values.tolist()
        if len(values) >= 3:
            date_raw = values[2]
            if pd.notna(date_raw):
                date_str = str(date_raw).strip()
                if date_str and date_str != 'nan':
                    try:
                        if '/' in date_str:
                            date_obj = pd.to_datetime(date_str, format='%d/%m/%Y').date()
                        else:
                            date_obj = pd.to_datetime(date_str).date()
                        if date_obj == d:
                            count += 1
                    except:
                        pass
    print(f"  - {d}: {count} سجل")

print("\n" + "=" * 60)
print(f"إجمالي التواريخ المختلفة: {len(dates_in_file)}")
