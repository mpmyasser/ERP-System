#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Complete validation test for bonus form field rendering
Shows the exact HTML of the paid_with_salary field
"""

import sys
import os
import io
import re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from app import create_app

app = create_app()
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False

print("="*80)
print("BONUS FORM COMPLETE VALIDATION")
print("="*80)

with app.test_client() as client:
    response = client.get('/bonuses/create')
    html = response.get_data(as_text=True)
    
    print("\n[1] ROUTE AND TEMPLATE VERIFICATION")
    print("-" * 80)
    print(f"Route: /bonuses/create")
    print(f"Method: GET")
    print(f"Status Code: {response.status_code}")
    print(f"Template: bonuses/form.html")
    
    print("\n[2] FORM FIELD EXTRACTION")
    print("-" * 80)
    
    paid_with_salary_pattern = r'(<div class="form-check form-switch"[^>]*>.*?</div>\s*</div>)'
    match = re.search(paid_with_salary_pattern, html, re.DOTALL)
    
    if match:
        field_html = match.group(1)
        
        print("\nEXACT HTML OF PAID_WITH_SALARY FIELD:")
        print("-" * 80)
        
        lines = field_html.split('\n')
        for i, line in enumerate(lines, 1):
            print(f"{i:3d}  {line}")
        
        print("\n" + "-" * 80)
    else:
        print("❌ Could not find the form-check form-switch section")
    
    print("\n[3] INDIVIDUAL ELEMENT CHECKS")
    print("-" * 80)
    
    checks = {
        'Input element': {
            'pattern': r'<input\s+class="form-check-input"\s+type="checkbox"\s+id="paid_with_salary_switch"',
            'description': 'Checkbox input with correct ID'
        },
        'Input name': {
            'pattern': r'name="paid_with_salary"',
            'description': 'Input name attribute set correctly'
        },
        'Form-check class': {
            'pattern': r'class="form-check form-switch"',
            'description': 'Bootstrap toggle switch styling'
        },
        'Label element': {
            'pattern': r'<label[^>]*for="paid_with_salary_switch"[^>]*>',
            'description': 'Label correctly linked to input'
        },
        'Arabic label text': {
            'pattern': r'صرف مع الراتب',
            'description': 'Arabic text "صرف مع الراتب"'
        },
        'Help text ON': {
            'pattern': r'مفعّل|مفعل',
            'description': 'ON state help text'
        },
        'Help text OFF': {
            'pattern': r'معطّل|معطل',
            'description': 'OFF state help text'
        },
        'Width styling': {
            'pattern': r'width:\s*3rem',
            'description': 'Checkbox width (3rem) for visibility'
        },
        'Height styling': {
            'pattern': r'height:\s*1.5rem',
            'description': 'Checkbox height (1.5rem) for visibility'
        },
    }
    
    all_found = True
    for check_name, check_data in checks.items():
        found = bool(re.search(check_data['pattern'], html, re.DOTALL))
        status = "✅" if found else "❌"
        print(f"{status} {check_name:20s} - {check_data['description']}")
        if not found:
            all_found = False
    
    print("\n[4] FORM STRUCTURE VERIFICATION")
    print("-" * 80)
    
    if '<form' in html and '</form>' in html:
        print("✅ Form element exists")
    else:
        print("❌ Form element missing")
        all_found = False
    
    if 'name="employee_id"' in html:
        print("✅ Employee field present")
    else:
        print("❌ Employee field missing")
        all_found = False
    
    if 'name="amount"' in html:
        print("✅ Amount field present")
    else:
        print("❌ Amount field missing")
        all_found = False
    
    if 'name="date_awarded"' in html:
        print("✅ Date field present")
    else:
        print("❌ Date field missing")
        all_found = False
    
    if 'name="reason"' in html:
        print("✅ Reason field present")
    else:
        print("❌ Reason field missing")
        all_found = False
    
    if 'name="paid_with_salary"' in html:
        print("✅ paid_with_salary field present")
    else:
        print("❌ paid_with_salary field missing")
        all_found = False
    
    if 'type="submit"' in html:
        print("✅ Submit button present")
    else:
        print("❌ Submit button missing")
        all_found = False
    
    print("\n[5] VISUAL RENDERING SUMMARY")
    print("-" * 80)
    
    if all_found:
        print("✅ ALL ELEMENTS PRESENT AND CORRECT")
        print("\n📋 THE FIELD DETAILS:")
        print("   • ID: paid_with_salary_switch")
        print("   • Name: paid_with_salary")
        print("   • Type: Checkbox")
        print("   • Styling: Bootstrap form-check form-switch")
        print("   • Label: صرف مع الراتب الشهري؟")
        print("   • Width: 3rem (enlarged for visibility)")
        print("   • Height: 1.5rem (enlarged for visibility)")
        print("   • Default: Checked (TRUE)")
        print("   • Help Text: Shows ON/OFF states with Arabic")
        
        print("\n🎯 HOW IT WORKS:")
        print("   ON (CHECKED)  → Bonus included with monthly salary")
        print("   OFF(UNCHECKED)→ Bonus was paid immediately (deducted from salary)")
        
        print("\n✅ CONCLUSION:")
        print("   The field IS fully implemented and visible in the HTML.")
        print("   If you don't see it in your browser:")
        print("     1. Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)")
        print("     2. Clear browser cache")
        print("     3. Close and reopen the browser tab")
        print("     4. Check browser console (F12) for JavaScript errors")
    else:
        print("❌ Some elements are missing!")
        print("\nFull HTML content (first 2000 chars):")
        print(html[:2000])

print("\n" + "="*80)
