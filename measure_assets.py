"""
Asset Size Measurement Script
Calculates total JS and CSS file sizes
"""

import os
import requests
from urllib.parse import urljoin

# Static files from local filesystem
static_dir = r"e:\backoup\H.R-11-02-2026 -\app\static"

local_js_files = [
    'js/excel_export_formatter.js',
    'js/settings_manager.js',
    'js/filter_persistence.js',
    'js/app.js',
    'js/datatables_init.js',
    'js/datatable_date_sorting.js',
    'js/datatable_checkbox_persistence.js',
    'js/aggrid_init.js',
    'js/table_resizer.js',
    'js/input_sanitizer.js',
    'js/enter_navigation.js',
    'js/date_format.js',
    'js/flatpickr_init.js',
    'js/print-handler.js',
    'js/delete_handler.js'
]

local_css_files = [
    'css/custom.css',
    'css/treasury-ui.css',
    'css/print-styles.css'
]

# CDN files (approximate sizes from CDN headers)
cdn_files = {
    'css': [
        'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.rtl.min.css',
        'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css',
        'https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap',
        'https://cdn.datatables.net/1.13.7/css/dataTables.bootstrap5.min.css',
        'https://cdn.datatables.net/buttons/2.4.2/css/buttons.bootstrap5.min.css',
        'https://cdn.datatables.net/responsive/2.5.0/css/responsive.bootstrap5.min.css',
        'https://cdn.datatables.net/colreorder/1.7.0/css/colReorder.bootstrap5.min.css',
        'https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css',
        'https://cdn.jsdelivr.net/npm/ag-grid-community@30.2.0/styles/ag-grid.min.css',
        'https://cdn.jsdelivr.net/npm/ag-grid-community@30.2.0/styles/ag-theme-alpine.min.css',
        'https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css',
        'https://cdn.jsdelivr.net/npm/select2-bootstrap-5-theme@1.3.0/dist/select2-bootstrap-5-theme.min.css'
    ],
    'js': [
        'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js',
        'https://code.jquery.com/jquery-3.7.1.min.js',
        'https://cdn.jsdelivr.net/npm/sweetalert2@11',
        'https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js',
        'https://cdn.datatables.net/1.13.7/js/dataTables.bootstrap5.min.js',
        'https://cdn.datatables.net/responsive/2.5.0/js/dataTables.responsive.min.js',
        'https://cdn.datatables.net/responsive/2.5.0/js/responsive.bootstrap5.min.js',
        'https://cdn.datatables.net/colreorder/1.7.0/js/dataTables.colReorder.min.js',
        'https://cdn.datatables.net/buttons/2.4.2/js/dataTables.buttons.min.js',
        'https://cdn.datatables.net/buttons/2.4.2/js/buttons.bootstrap5.min.js',
        'https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js',
        'https://cdn.datatables.net/buttons/2.4.2/js/buttons.html5.min.js',
        'https://cdn.datatables.net/buttons/2.4.2/js/buttons.print.min.js',
        'https://cdn.datatables.net/buttons/2.4.2/js/buttons.colVis.min.js',
        'https://cdn.jsdelivr.net/npm/flatpickr',
        'https://cdn.jsdelivr.net/npm/flatpickr/dist/l10n/ar.js',
        'https://cdn.jsdelivr.net/npm/ag-grid-community@30.2.0/dist/ag-grid-community.min.js',
        'https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js'
    ]
}

def get_local_file_size(filepath):
    """Get size of local file"""
    try:
        full_path = os.path.join(static_dir, filepath)
        if os.path.exists(full_path):
            return os.path.getsize(full_path)
    except:
        pass
    return 0

def get_cdn_file_size(url):
    """Get size of CDN file via HEAD request"""
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        if 'content-length' in response.headers:
            return int(response.headers['content-length'])
    except:
        pass
    return 0

print("="*60)
print("ASSET SIZE MEASUREMENT")
print("="*60)

# Local JS
print("\nLOCAL JS FILES:")
local_js_total = 0
for js_file in local_js_files:
    size = get_local_file_size(js_file)
    local_js_total += size
    print(f"  {js_file}: {size:,} bytes ({size/1024:.2f} KB)")

print(f"\n  TOTAL LOCAL JS: {local_js_total:,} bytes ({local_js_total/1024:.2f} KB)")

# Local CSS
print("\nLOCAL CSS FILES:")
local_css_total = 0
for css_file in local_css_files:
    size = get_local_file_size(css_file)
    local_css_total += size
    print(f"  {css_file}: {size:,} bytes ({size/1024:.2f} KB)")

print(f"\n  TOTAL LOCAL CSS: {local_css_total:,} bytes ({local_css_total/1024:.2f} KB)")

# CDN CSS
print("\nCDN CSS FILES (fetching sizes...):")
cdn_css_total = 0
for css_url in cdn_files['css']:
    size = get_cdn_file_size(css_url)
    cdn_css_total += size
    filename = css_url.split('/')[-1][:50]
    print(f"  {filename}: {size:,} bytes ({size/1024:.2f} KB)")

print(f"\n  TOTAL CDN CSS: {cdn_css_total:,} bytes ({cdn_css_total/1024:.2f} KB)")

# CDN JS
print("\nCDN JS FILES (fetching sizes...):")
cdn_js_total = 0
for js_url in cdn_files['js']:
    size = get_cdn_file_size(js_url)
    cdn_js_total += size
    filename = js_url.split('/')[-1][:50]
    print(f"  {filename}: {size:,} bytes ({size/1024:.2f} KB)")

print(f"\n  TOTAL CDN JS: {cdn_js_total:,} bytes ({cdn_js_total/1024:.2f} KB)")

# Grand totals
total_js = local_js_total + cdn_js_total
total_css = local_css_total + cdn_css_total

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"\nTOTAL JS SIZE:  {total_js:,} bytes ({total_js/1024:.2f} KB) ({total_js/1024/1024:.2f} MB)")
print(f"  - Local:      {local_js_total:,} bytes ({local_js_total/1024:.2f} KB)")
print(f"  - CDN:        {cdn_js_total:,} bytes ({cdn_js_total/1024:.2f} KB)")

print(f"\nTOTAL CSS SIZE: {total_css:,} bytes ({total_css/1024:.2f} KB) ({total_css/1024/1024:.2f} MB)")
print(f"  - Local:      {local_css_total:,} bytes ({local_css_total/1024:.2f} KB)")
print(f"  - CDN:        {cdn_css_total:,} bytes ({cdn_css_total/1024:.2f} KB)")

print(f"\nGRAND TOTAL:    {total_js + total_css:,} bytes ({(total_js + total_css)/1024:.2f} KB) ({(total_js + total_css)/1024/1024:.2f} MB)")
print("="*60)
