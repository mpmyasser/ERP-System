import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app

app = create_app()
with app.test_request_context('/attendance/?date_from=26/01/2026&date_to=11/02/2026&department_ids=2&code=123'):
    from app.routes.attendance import daily
    resp = daily()
    print('Rendered attendance page type:', type(resp))
    print('Length:', len(resp))
