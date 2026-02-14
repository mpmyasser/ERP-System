"""
Helper Functions
===============
General utility functions used across the application
"""

from datetime import datetime, date, time


def format_currency(amount, currency="جنيه"):
    """Format amount as currency"""
    return f"{amount:,.2f} {currency}"


def format_date_ar(date_obj):
    """Format date in Arabic"""
    if not date_obj:
        return ""
    if isinstance(date_obj, str):
        return date_obj
    # Display dates as DD/MM/YYYY for Arabic interface
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


def parse_date_compact(date_string):
    """
    Parse date from various formats.
    Accepts formats: YYYY-MM-DD, DD-MM-YYYY, DDMMYYYY, DD/MM/YYYY
    All formats treat input as: Day/Month/Year (DD/MM/YYYY)
    Returns: date object or None if invalid
    """
    if not date_string:
        return None
    
    date_string = str(date_string).strip()
    
    # Replace Arabic numerals with Western numerals
    arabic_digits = "٠١٢٣٤٥٦٧٨٩"
    western_digits = "0123456789"
    translation_table = str.maketrans(arabic_digits, western_digits)
    date_string = date_string.translate(translation_table)

    # Try parsing with dash separators: prefer ISO YYYY-MM-DD, but accept DD-MM-YYYY too
    try:
        if '-' in date_string:
            parts = date_string.split('-')
            if len(parts) == 3:
                # If starts with 4-digit year, parse as YYYY-MM-DD
                if len(parts[0]) == 4:
                    return datetime.strptime(date_string, '%Y-%m-%d').date()
                # Otherwise, try DD-MM-YYYY
                return datetime.strptime(date_string, '%d-%m-%Y').date()
    except (ValueError, AttributeError):
        pass # If it fails, fall through to other formats

    # Parse with slash: DD/MM/YYYY format
    try:
        if '/' in date_string:
            parts = date_string.split('/')
            if len(parts) != 3:
                return None
            day = int(parts[0])
            month = int(parts[1])
            year = int(parts[2])
        else:
            # Without separators: DDMMYYYY format (8 digits)
            date_string_clean = ''.join(c for c in date_string if c.isdigit())
            
            if len(date_string_clean) != 8:
                return None
            
            # Format is DDMMYYYY (day-month-year)
            day = int(date_string_clean[0:2])
            month = int(date_string_clean[2:4])
            year = int(date_string_clean[4:8])
        
        if day < 1 or day > 31 or month < 1 or month > 12 or year < 1900 or year > 2100:
            return None
        
        return date(year, month, day)
    except (ValueError, AttributeError):
        return None


def validate_date_format(date_string):
    """Validate if date_string is in valid format"""
    return parse_date_compact(date_string) is not None


def format_date_input_hint():
    """Return hint text for date input format"""
    return "صيغة التاريخ: DDMMYYYY (مثال: 08122025 لـ 8/12/2025) أو DD/MM/YYYY (مثال: 08/12/2025)"


def extract_birthdate_from_national_id(national_id):
    """
    استخراج تاريخ الميلاد من الرقم القومي المصري
    
    تركيب الرقم القومي (14 رقم):
    - الرقم 1: تحديد القرن (2 = 1900s, 3 = 2000s)
    - الأرقام 2-7: تاريخ الميلاد بصيغة YYMMDD
      - 2-3: السنة (YY)
      - 4-5: الشهر (MM)
      - 6-7: اليوم (DD)
    - الأرقام 8-12: رقم تسلسلي (محافظة + رقم)
    - الأرقام 13-14: رقم التحقق (Checksum)
    
    Args:
        national_id: الرقم القومي (سلسلة نصية مكونة من 14 رقماً)
    
    Returns:
        date: تاريخ الميلاد أو None إذا كان الرقم غير صحيح
    
    Example:
        >>> extract_birthdate_from_national_id("28104111401638")
        datetime.date(1981, 4, 11)
    """
    if not national_id:
        return None
    
    # تنظيف المدخلات
    cleaned = str(national_id).strip().replace(' ', '').replace('-', '')
    
    # التحقق من أن الرقم يحتوي على 14 رقم فقط
    if not cleaned.isdigit() or len(cleaned) != 14:
        return None
    
    # استخراج القرن من الرقم الأول
    century_digit = int(cleaned[0])
    
    # استخراج تاريخ الميلاد من الأرقام 2-7 (positions 1-6 في نظام 0-indexing)
    year_2digit = int(cleaned[1:3])      # positions 1-2
    month = int(cleaned[3:5])             # positions 3-4
    day = int(cleaned[5:7])               # positions 5-6
    
    # تحديد القرن بناءً على الرقم الأول
    if century_digit == 2:
        # 1900s
        full_year = 1900 + year_2digit
    elif century_digit == 3:
        # 2000s
        full_year = 2000 + year_2digit
    else:
        # رقم قومي غير صحيح - قيمة غير صحيحة للقرن
        return None
    
    # التحقق من صحة الشهر واليوم
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return None
    
    # محاولة إنشاء التاريخ والتحقق من صحته
    try:
        birth_date = date(full_year, month, day)
        return birth_date
    except ValueError:
        # تاريخ غير صحيح (مثل 31 فبراير)
        return None


def calculate_age_from_national_id(national_id):
    """
    حساب العمر من الرقم القومي المصري
    
    Args:
        national_id: الرقم القومي
    
    Returns:
        dict: قاموس يحتوي على:
            - years: السنوات
            - months: الأشهر
            - days: الأيام
            - total_days: إجمالي الأيام
        أو None إذا كان الرقم غير صحيح
    
    Example:
        >>> age = calculate_age_from_national_id("28104111401638")
        >>> print(age)
        {'years': 44, 'months': 7, 'days': 29, 'total_days': 16314}
    """
    birth_date = extract_birthdate_from_national_id(national_id)
    if not birth_date:
        return None
    
    today = date.today()
    
    # حساب الفرق
    years = today.year - birth_date.year
    months = today.month - birth_date.month
    days = today.day - birth_date.day
    
    # تصحيح الأيام
    if days < 0:
        months -= 1
        # حساب أيام الشهر السابق
        if today.month == 1:
            prev_month_year = today.year - 1
            prev_month = 12
        else:
            prev_month_year = today.year
            prev_month = today.month - 1
        
        # عدد أيام الشهر السابق
        if prev_month == 2:
            # فبراير
            is_leap = (prev_month_year % 4 == 0 and prev_month_year % 100 != 0) or (prev_month_year % 400 == 0)
            days_in_prev_month = 29 if is_leap else 28
        elif prev_month in [4, 6, 9, 11]:
            days_in_prev_month = 30
        else:
            days_in_prev_month = 31
        
        days += days_in_prev_month
    
    # تصحيح الأشهر
    if months < 0:
        years -= 1
        months += 12
    
    # حساب إجمالي الأيام
    total_days = (today - birth_date).days
    
    return {
        'years': years,
        'months': months,
        'days': days,
        'total_days': total_days
    }
