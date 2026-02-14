#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Temporary script to add salary rounding"""

# Read file
with open(r'd:\H.R\core\services\payroll_processor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# First replacement - line 233
content = content.replace(
    '        net_salary = gross_salary + total_additions - total_deductions\n        \n        result = {',
    '        net_salary = gross_salary + total_additions - total_deductions\n        net_salary = round(net_salary / 5) * 5\n        \n        result = {'
)

# Second replacement - line 740
old_text = '''        )
        
        net_salary = gross_salary + total_additions - total_deductions

        return {'''

new_text = '''        )
        
        net_salary = gross_salary + total_additions - total_deductions
        net_salary = round(net_salary / 5) * 5

        return {'''

content = content.replace(old_text, new_text)

# Write back
with open(r'd:\H.R\core\services\payroll_processor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated payroll_processor.py - added net salary rounding to nearest 5')
