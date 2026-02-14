"""
Flask Application Configuration
===============================
"""

import os

class Config:
    """Flask configuration"""
    
    # Secret key for sessions and CSRF
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'core', 'hr.db')
    
    # WTForms
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Flask
    DEBUG = True
    
    # Pagination
    ITEMS_PER_PAGE = 20
