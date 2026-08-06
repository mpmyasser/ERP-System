"""
Helper Functions
===============
General utility functions used across the application
"""

from datetime import date


def format_currency(amount, currency="جنيه"):
    """Format amount as currency"""
    return f"{amount:,.2f} {currency}"


def format_date_ar(date_obj):
    """Format date in Arabic"""
    if not date_obj:
        return ""
    if isinstance(date_obj, str):
        return date_obj
    return date_obj.strftime("%d/%m/%Y")


def calculate_age(birth_date):
    """Calculate age from birth date"""
    if not birth_date:
        return None
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def minutes_to_hours(minutes):
    """Convert minutes to hours"""
    return minutes / 60.0


def hours_to_minutes(hours):
    """Convert hours to minutes"""
    return hours * 60
