#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TEST: Verify database path at startup
"""

import os
import sys

print("\n" + "="*80)
print("STARTUP DATABASE VERIFICATION TEST")
print("="*80)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
from db_manager import DBManager

print("\n[TEST 1] Creating DBManager with default path...")
db = DBManager()
expected_db = os.path.abspath(os.path.join(os.path.dirname(__file__), 'core', 'hr.db'))

print("Expected Path:  {}".format(expected_db))
print("Actual Path:    {}".format(db.db_path))
print("Database Exists: {}".format(os.path.exists(db.db_path)))

if db.db_path == expected_db:
    print("\n[OK] PASS: Database path is correct!")
    print("[OK] Single database unified to: core/hr.db")
    print("\n" + "="*80)
    sys.exit(0)
else:
    print("\n[ERROR] FAIL: Database path mismatch!")
    print("[ERROR] Expected: {}".format(expected_db))
    print("[ERROR] Got:      {}".format(db.db_path))
    print("\n" + "="*80)
    sys.exit(1)
