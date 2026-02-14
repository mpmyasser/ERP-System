#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Debug test to verify the bonus form field is being rendered correctly
Checks the actual HTML rendered by the form
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
print("BONUS FORM HTML DEBUG TEST")
print("="*80)

with app.test_client() as client:
    print("\n[1] Requesting /bonuses/create...")
    response = client.get('/bonuses/create')
    
    print(f"    Status Code: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ ERROR: Got status {response.status_code}, expected 200")
        sys.exit(1)
    
    html = response.get_data(as_text=True)
    
    print("\n[2] Checking for critical form elements...")
    
    checks = {
        'Checkbox input exists': 'id="paid_with_salary_switch"' in html,
        'Checkbox name correct': 'name="paid_with_salary"' in html,
        'Toggle styling present': 'form-check form-switch' in html,
        'Arabic label present': 'صرف مع الراتب' in html,
        'ON state help text': 'مفعّل' in html or 'مفعل' in html,
        'OFF state help text': 'معطّل' in html or 'معطل' in html,
    }
    
    all_present = True
    for desc, found in checks.items():
        status = "✅" if found else "❌"
        print(f"    {status} {desc}")
        if not found:
            all_present = False
    
    if not all_present:
        print("\n[3] Extracting relevant HTML section...")
        
        import re
        # Find the form section
        form_match = re.search(r'<form[^>]*>.*?</form>', html, re.DOTALL)
        if form_match:
            form_html = form_match.group(0)
            
            # Find the paid_with_salary section
            field_match = re.search(
                r'<div class="mb-3">.*?paid_with_salary.*?</div>.*?</div>',
                form_html,
                re.DOTALL
            )
            
            if field_match:
                field_html = field_match.group(0)
                print("\nPAID_WITH_SALARY FIELD HTML:")
                print(field_html[:500])
                if len(field_html) > 500:
                    print("... (truncated)")
    
    print("\n[4] Checking form fields...")
    
    # Extract all form field names
    field_pattern = r'<input[^>]+name="([^"]+)"'
    fields = re.findall(field_pattern, html)
    print(f"    Form fields found: {fields}")
    
    if 'paid_with_salary' not in fields:
        print("    ❌ CRITICAL: paid_with_salary field not in HTML!")
    else:
        print("    ✅ paid_with_salary field is in HTML")
    
    print("\n[5] Checking for display:none or hidden attributes...")
    
    # Look for any CSS that might hide elements
    if 'display:none' in html or 'visibility:hidden' in html:
        print("    ⚠️  WARNING: Found display:none or visibility:hidden in page")
    else:
        print("    ✅ No display:none or visibility:hidden found")
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    if all_present:
        print("✅ ALL CHECKS PASSED")
        print("\nThe paid_with_salary field IS rendered in the HTML and should be visible.")
        print("\nIf you don't see it in the browser:")
        print("  1. Clear your browser cache")
        print("  2. Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)")
        print("  3. Check browser console for JavaScript errors")
    else:
        print("❌ Some elements are missing from the HTML")
        print("\nFull HTML Response:")
        print("="*80)
        print(html)
        print("="*80)
