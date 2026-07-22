"""
Flask Application Configuration
===============================
"""

import os
import secrets


def _load_secret_key():
    """Return the session/CSRF secret key.

    Prefer the SECRET_KEY environment variable. If it is not set we generate a
    random ephemeral key so the app never falls back to a well-known hardcoded
    value (which would allow session cookie forgery). The ephemeral key changes
    on every restart, so SECRET_KEY must be set in any real deployment for
    sessions to persist.
    """
    key = os.environ.get('SECRET_KEY')
    if key:
        return key
    print(
        "[WARNING] SECRET_KEY is not set; generating a temporary random key. "
        "Set SECRET_KEY in the environment for stable, secure sessions."
    )
    return secrets.token_hex(32)


def _env_flag(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


class Config:
    """Flask configuration"""
    
    # Secret key for sessions and CSRF
    SECRET_KEY = _load_secret_key()
    
    # Database
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'core', 'hr.db')
    
    # WTForms
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # Flask - never enable debug by default; opt in via FLASK_DEBUG only
    DEBUG = _env_flag('FLASK_DEBUG', False)
    
    # Pagination
    ITEMS_PER_PAGE = 20
