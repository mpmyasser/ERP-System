#!/usr/bin/env python3
"""
Accessibility Fix Script for HTML Templates
============================================
This script fixes accessibility issues in all HTML template files.

Fixes applied:
1. Add aria-hidden="true" to all Font Awesome icons
2. Replace style="display:none" with class="d-none"
3. Replace style="display:inline" with class="d-inline"
4. Replace aria-label="Close" with aria-label="إغلاق"
5. Add aria-label to buttons with only icons
6. Fix common inline styles with Bootstrap classes
"""

import os
import re
from pathlib import Path

TEMPLATES_DIR = Path('app/templates')

def fix_icon_aria_hidden(content):
    """Add aria-hidden='true' to Font Awesome icons that don't have it."""
    # Pattern for <i class="fas ..."> or <i class="fa ..."> without aria-hidden
    pattern = r'(<i\s+class="fa[sbr]?\s+[^"]*"(?![^>]*aria-hidden)[^>]*>)'
    
    def add_aria_hidden(match):
        tag = match.group(1)
        if 'aria-hidden' not in tag:
            # Insert before the closing >
            return tag[:-1] + ' aria-hidden="true">'
        return tag
    
    return re.sub(pattern, add_aria_hidden, content)

def fix_display_none(content):
    """Replace style='display: none' or style='display:none' with class='d-none'."""
    # Various patterns for display:none
    patterns = [
        (r'style="display:\s*none;?"', 'class="d-none"'),
        (r"style='display:\s*none;?'", 'class="d-none"'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    return content

def fix_display_inline(content):
    """Replace style='display: inline' with class='d-inline'."""
    patterns = [
        (r'style="display:\s*inline;?"', 'class="d-inline"'),
        (r"style='display:\s*inline;?'", 'class="d-inline"'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    return content

def fix_close_aria_label(content):
    """Replace aria-label='Close' with aria-label='إغلاق'."""
    patterns = [
        ('aria-label="Close"', 'aria-label="إغلاق"'),
        ("aria-label='Close'", "aria-label='إغلاق'"),
    ]
    
    for pattern, replacement in patterns:
        content = content.replace(pattern, replacement)
    
    return content

def fix_navbar_toggler(content):
    """Add aria-label and title to navbar-toggler buttons."""
    pattern = r'(<button\s+class="navbar-toggler"[^>]*)(>)'
    
    def add_attrs(match):
        before = match.group(1)
        after = match.group(2)
        if 'aria-label' not in before:
            return before + ' aria-label="فتح أو إغلاق القائمة" title="فتح أو إغلاق القائمة"' + after
        return match.group(0)
    
    return re.sub(pattern, add_attrs, content)

def fix_btn_close(content):
    """Add title to btn-close buttons."""
    pattern = r'(<button[^>]*class="[^"]*btn-close[^"]*"[^>]*)(>)'
    
    def add_title(match):
        before = match.group(1)
        after = match.group(2)
        if 'title=' not in before:
            return before + ' title="إغلاق"' + after
        return match.group(0)
    
    return re.sub(pattern, add_title, content)

def fix_inline_styles(content, filename):
    """Convert common inline styles to Bootstrap classes."""
    # Skip print-specific styles
    if 'print' in filename.lower():
        return content
    
    # Width styles - only for form elements
    width_patterns = [
        (r'style="width:\s*70px;?"', 'style="width:70px"'),  # Keep specific widths for now
        (r'style="width:\s*100%;?"', 'class="w-100"'),
        (r'style="max-width:\s*120px;?"', 'class="w-max-120"'),
        (r'style="max-width:\s*150px;?"', 'class="w-max-150"'),
    ]
    
    for pattern, replacement in width_patterns:
        content = re.sub(pattern, replacement, content)
    
    return content

def process_file(filepath):
    """Process a single HTML file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply all fixes
        content = fix_icon_aria_hidden(content)
        content = fix_display_none(content)
        content = fix_display_inline(content)
        content = fix_close_aria_label(content)
        content = fix_navbar_toggler(content)
        content = fix_btn_close(content)
        content = fix_inline_styles(content, filepath.name)
        
        # Only write if content changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    """Main function to process all HTML templates."""
    print("=" * 60)
    print("Accessibility Fix Script")
    print("=" * 60)
    
    modified_files = []
    
    # Process all HTML files in templates directory
    for filepath in TEMPLATES_DIR.rglob('*.html'):
        if process_file(filepath):
            modified_files.append(str(filepath))
            print(f"✓ Fixed: {filepath}")
    
    print("\n" + "=" * 60)
    print(f"Total files modified: {len(modified_files)}")
    print("=" * 60)
    
    if modified_files:
        print("\nModified files:")
        for f in modified_files:
            print(f"  - {f}")

if __name__ == '__main__':
    main()
