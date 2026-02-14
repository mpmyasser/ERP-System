from flask import Flask, url_for

app = Flask(__name__)

with app.test_request_context():
    # Test 1: Simple list
    url = url_for('static', filename='test', department_id=[1, 2])
    print(f"URL with list: {url}")
    
    # Test 2: Unpacking dict with list
    filters = {'department_id': ['3', '4'], 'date_from': '01/01/2026'}
    url2 = url_for('static', filename='test', **filters)
    print(f"URL with unpacked dict: {url2}")
