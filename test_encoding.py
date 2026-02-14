import pandas as pd

# Try to read and fix the columns
df = pd.read_excel('app/uploads/1.xls', engine='xlrd')
print("Original columns:")
print(df.columns.tolist())

# Fix encoding
new_columns = []
for col in df.columns:
    if isinstance(col, str):
        try:
            col_str = str(col)
            if 'Ñ' in col_str or 'Ç' in col_str or 'á' in col_str:
                try:
                    col_bytes = col_str.encode('iso-8859-1')
                    col = col_bytes.decode('utf-8')
                except:
                    pass
        except:
            pass
    new_columns.append(col)

df.columns = new_columns
print("\nFixed columns:")
print(df.columns.tolist())
print("\nFirst row:")
print(df.iloc[0])
