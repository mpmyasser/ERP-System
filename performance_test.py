"""
Performance Measurement Script
Measures backend and frontend metrics for specified pages
"""

import time
import sys
import os
from datetime import datetime
from flask import Flask
from werkzeug.test import Client
from werkzeug.serving import WSGIRequestHandler

# Add core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

# Import app
from app import create_app

# Monkey patch SQLAlchemy to track query times
query_times = []
query_count = 0

def measure_page_performance(client, url, page_name):
    """Measure backend performance for a page"""
    global query_times, query_count
    
    # Reset metrics
    query_times = []
    query_count = 0
    
    # Patch SQLAlchemy engine to track queries
    from sqlalchemy import event
    from sqlalchemy.engine import Engine
    
    @event.listens_for(Engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault('query_start_time', []).append(time.time())
    
    @event.listens_for(Engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        global query_times, query_count
        total = time.time() - conn.info['query_start_time'].pop(-1)
        query_times.append(total * 1000)  # Convert to ms
        query_count += 1
    
    # Make request
    start_time = time.time()
    response = client.get(url)
    total_time = (time.time() - start_time) * 1000  # Convert to ms
    
    # Calculate SQL metrics
    sql_time = sum(query_times) if query_times else 0
    
    # Get response size
    response_size = len(response.data)
    
    print(f"\n{'='*60}")
    print(f"PERFORMANCE METRICS: {page_name}")
    print(f"{'='*60}")
    print(f"\nA) BACKEND")
    print(f"   Total request time: {total_time:.2f} ms")
    print(f"   SQL execution time: {sql_time:.2f} ms")
    print(f"   Number of queries: {query_count}")
    print(f"   Non-SQL time: {total_time - sql_time:.2f} ms")
    print(f"\nB) FRONTEND (Estimated from HTML)")
    print(f"   Response size: {response_size:,} bytes ({response_size/1024:.2f} KB)")
    
    # Parse HTML to estimate frontend metrics
    html = response.data.decode('utf-8', errors='ignore')
    
    # Count DataTable rows
    import re
    tbody_match = re.search(r'<tbody[^>]*>(.*?)</tbody>', html, re.DOTALL)
    if tbody_match:
        row_count = len(re.findall(r'<tr[^>]*>', tbody_match.group(1)))
        print(f"   DOM rows in DataTable: {row_count}")
    else:
        print(f"   DOM rows in DataTable: N/A")
    
    # Estimate JS/CSS sizes
    js_files = re.findall(r'<script[^>]*src=["\']([^"\']+)["\']', html)
    css_files = re.findall(r'<link[^>]*href=["\']([^"\']+\.css)["\']', html)
    
    print(f"   JS files loaded: {len(js_files)}")
    print(f"   CSS files loaded: {len(css_files)}")
    
    print(f"\nC) ASSETS (Approximate)")
    print(f"   Note: Actual file sizes require filesystem access")
    print(f"   JS files: {len(js_files)} files")
    print(f"   CSS files: {len(css_files)} files")
    
    print(f"\nD) MEMORY")
    print(f"   Note: JS heap measurement requires browser instrumentation")
    print(f"   Server memory: Not measured (requires psutil)")
    
    print(f"\n{'='*60}\n")
    
    return {
        'page': page_name,
        'url': url,
        'backend': {
            'total_time_ms': round(total_time, 2),
            'sql_time_ms': round(sql_time, 2),
            'query_count': query_count,
            'non_sql_time_ms': round(total_time - sql_time, 2)
        },
        'frontend': {
            'response_size_bytes': response_size,
            'response_size_kb': round(response_size/1024, 2),
            'dom_rows': row_count if tbody_match else 'N/A',
            'js_files_count': len(js_files),
            'css_files_count': len(css_files)
        }
    }

if __name__ == '__main__':
    print("Starting Performance Measurement...")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Create app
    app = create_app()
    app.config['TESTING'] = True
    
    # Create test client with session
    client = app.test_client()
    
    # Simulate logged-in session
    with client.session_transaction() as sess:
        sess['user_id'] = 1  # Assume admin user
        sess['is_admin'] = True
    
    # Test pages
    pages = [
        {
            'name': 'Employees List (Filtered)',
            'url': '/employees/?date_from=01/02/2020&date_to=20/02/2026&department_ids=3&status=active'
        },
        {
            'name': 'Loans List',
            'url': '/loans/'
        }
    ]
    
    results = []
    for page in pages:
        result = measure_page_performance(client, page['url'], page['name'])
        results.append(result)
        time.sleep(0.5)  # Brief pause between tests
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for result in results:
        print(f"\n{result['page']}:")
        print(f"  Backend: {result['backend']['total_time_ms']} ms ({result['backend']['query_count']} queries)")
        print(f"  SQL Time: {result['backend']['sql_time_ms']} ms")
        print(f"  Response: {result['frontend']['response_size_kb']} KB")
        print(f"  DOM Rows: {result['frontend']['dom_rows']}")
    
    print("\n" + "="*60)
    print("NOTES:")
    print("- Frontend timing (DOMContentLoaded, DataTable init) requires browser")
    print("- Asset sizes require filesystem measurement")
    print("- JS heap requires browser DevTools")
    print("="*60)
