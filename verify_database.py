#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3
import os

print("\n" + "="*80)
print("DATABASE VERIFICATION - CLEANUP & CONSOLIDATION")
print("="*80)

core_db = os.path.join(os.path.dirname(__file__), 'core', 'hr.db')

print("\n[CHECK 1] Scanning for all .db files...")
found_files = []
for root, dirs, files in os.walk(os.path.dirname(__file__)):
    for file in files:
        if file.endswith('.db'):
            full_path = os.path.join(root, file)
            size = os.path.getsize(full_path)
            found_files.append((full_path, size))
            print("     - {} ({} bytes)".format(full_path, size))

if not found_files:
    print("     (No .db files found)")

print("\n[CHECK 2] Core database status...")
if os.path.exists(core_db):
    print("     [OK] core/hr.db EXISTS")
    try:
        conn = sqlite3.connect(core_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("     [OK] Contains {} tables".format(len(tables)))
        
        for table in tables:
            table_name = table[0]
            cursor.execute('SELECT COUNT(*) FROM [{}]'.format(table_name))
            count = cursor.fetchone()[0]
            print("          - {} ({} rows)".format(table_name, count))
        
        conn.close()
    except Exception as e:
        print("     [ERROR] Failed to read database: {}".format(str(e)))
else:
    print("     [WARNING] core/hr.db DOES NOT EXIST")
    print("     [WARNING] Database will be created on first application run")

print("\n[CHECK 3] Verifying no hr_system.db exists...")
hr_system_exists = False
for root, dirs, files in os.walk(os.path.dirname(__file__)):
    if 'hr_system.db' in files:
        full_path = os.path.join(root, 'hr_system.db')
        print("     [ERROR] Found hr_system.db at: {}".format(full_path))
        hr_system_exists = True

if not hr_system_exists:
    print("     [OK] No hr_system.db files found")

print("\n" + "="*80)
print("VERIFICATION COMPLETE")
print("="*80)
print("\nSummary:")
print("  - Core database location: {}".format(core_db))
print("  - Database exists: {}".format(os.path.exists(core_db)))
print("  - Old hr_system.db cleaned up: {}".format(not hr_system_exists))
print("\nStatus: Ready to start application")
print("="*80 + "\n")
