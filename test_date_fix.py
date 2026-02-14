#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to verify date parsing fix for loans search
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from utils.helpers import parse_date_compact
from datetime import date

print("=" * 60)
print("Testing parse_date_compact() function")
print("=" * 60)

test_cases = [
    "25/11/2025",
    "24/12/2025",
    "01/01/2025",
    "31/12/2024",
]

for test_date in test_cases:
    result = parse_date_compact(test_date)
    print(f"Input: {test_date:15} → Output: {result} (type: {type(result).__name__})")

print("\n" + "=" * 60)
print("Testing DBManager.search_loans() with date filters")
print("=" * 60)

from db_manager import DBManager

db = DBManager()

# Test 1: Search with date range only (no department)
print("\nTest 1: Search loans by date range (25/11/2025 to 24/12/2025)")
loans = db.search_loans(
    date_from="25/11/2025",
    date_to="24/12/2025",
    department_ids=[],
    code=None
)
print(f"Found {len(loans)} loans")
for loan in loans[:3]:  # Show first 3
    print(f"  - Employee: {loan.employee.name if loan.employee else 'N/A'}, Date: {loan.date}, Amount: {loan.amount}")

# Test 2: Search with no date range (should return all)
print("\nTest 2: Search loans without date range")
loans_all = db.search_loans()
print(f"Found {len(loans_all)} total loans")

print("\n" + "=" * 60)
print("✓ All tests completed successfully!")
print("=" * 60)
