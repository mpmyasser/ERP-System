"""
Excel Import Helpers
====================
Shared utilities for the Excel-based data importers (chart of accounts,
partners, fabric rolls, ...). Centralizes the column validation, cell
normalization and error handling that were previously copy-pasted across the
individual importer modules.
"""

import traceback
from typing import Optional, Tuple

import pandas as pd


def load_excel(file_path, required_cols) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Read an Excel file and validate that required columns are present.

    Returns a ``(dataframe, None)`` tuple on success, or ``(None, error_message)``
    if any required column is missing.
    """
    df = pd.read_excel(file_path)
    for col in required_cols:
        if col not in df.columns:
            return None, f"العمود المطلوب غير موجود: {col}"
    return df, None


def clean_str(value, default=''):
    """Return a stripped string for an Excel cell, mapping NaN/'nan' to ``default``."""
    text = str(value).strip()
    return default if text == 'nan' else text


def safe_float(value, default=None):
    """Convert an Excel cell to ``float``, returning ``default`` when not possible."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def handle_import_error(db_session, error):
    """Roll back the session and log an import exception.

    Returns the string representation of ``error`` so callers can propagate it
    to the user.
    """
    db_session.rollback()
    print(f"خطأ أثناء الاستيراد: {str(error)}\n{traceback.format_exc()}")
    return str(error)
