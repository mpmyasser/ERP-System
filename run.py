# -*- coding: utf-8 -*-
"""
Flask Application Entry Point
=============================
Run this file to start the HR system web application
"""

import os
import sys
from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 80)
    print("HR SYSTEM - DATABASE VERIFICATION")
    print("=" * 80)
    
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))
    from db_manager import DBManager
    
    db = DBManager()
    expected_db = os.path.abspath(os.path.join(os.path.dirname(__file__), 'core', 'hr.db'))
    actual_db = db.db_path
    
    print("Expected Database:  {}".format(expected_db))
    print("Active Database:    {}".format(actual_db))
    print("Database Exists:    {}".format(os.path.exists(actual_db)))
    
    if actual_db != expected_db:
        print("\n[ERROR] CRITICAL: Wrong database in use!")
        print("[ERROR] Aborting startup - database path mismatch")
        print("[ERROR] Expected: {}".format(expected_db))
        print("[ERROR] Got:      {}".format(actual_db))
        sys.exit(1)
    
    print("\n[OK] Database path verified - using core/hr.db")
    print("=" * 80)
    print("nizam al-mawared al-bashariya - Flask Edition")
    print("=" * 80)
    print("URL: http://127.0.0.1:5000")
    print("=" * 80 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
