import sqlite3

conn = sqlite3.connect('core/hr.db')
cursor = conn.cursor()

cursor.execute('SELECT national_id, COUNT(*) FROM employees GROUP BY national_id HAVING COUNT(*) > 1')
print('Duplicate national_ids:')
for row in cursor.fetchall():
    print(f'  {repr(row[0])}: {row[1]} times')

conn.close()
