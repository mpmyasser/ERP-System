"""
Egyptian National ID Parser
استخراج البيانات من الرقم القومي المصري
"""

from datetime import datetime
from typing import Optional


def extract_birthdate(national_id: str) -> Optional[str]:
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
        str: تاريخ الميلاد بصيغة YYYY-MM-DD أو None إذا كان الرقم غير صحيح
    
    Example:
        >>> extract_birthdate("28104111401638")
        '1981-04-11'
    """
    # تنظيف المدخلات
    cleaned = str(national_id).strip().replace(' ', '').replace('-', '')
    
    # التحقق من أن الرقم يحتوي على 14 رقم فقط
    if not cleaned.isdigit() or len(cleaned) != 14:
        return None
    
    # استخراج القرن من الرقم الأول
    century_digit = int(cleaned[0])
    
    # استخراج تاريخ الميلاد من الأرقام 2-7 (positions 1-6)
    year_2digit = int(cleaned[1:3])      # positions 1-2
    month = int(cleaned[3:5])             # positions 3-4
    day = int(cleaned[5:7])               # positions 5-6
    
    # تحديد القرن بناءً على الرقم الأول
    if century_digit == 2:
        # 1900s
        year = 1900 + year_2digit
    elif century_digit == 3:
        # 2000s
        year = 2000 + year_2digit
    else:
        # رقم قومي غير صحيح
        return None
    
    # التحقق من صحة الشهر واليوم
    if not (1 <= month <= 12) or not (1 <= day <= 31):
        return None
    
    # محاولة إنشاء التاريخ والتحقق من صحته
    try:
        birth_date = datetime(year, month, day)
        # إعادة التاريخ بصيغة YYYY-MM-DD
        return birth_date.strftime('%Y-%m-%d')
    except ValueError:
        # تاريخ غير صحيح (مثل 31 فبراير)
        return None


def extract_birthdate_formatted(national_id: str, format_str: str = '%d/%m/%Y') -> Optional[str]:
    """
    استخراج تاريخ الميلاد مع تنسيق مخصص
    
    Args:
        national_id: الرقم القومي
        format_str: صيغة التاريخ المطلوبة (الافتراضي: DD/MM/YYYY)
    
    Returns:
        str: تاريخ الميلاد بالصيغة المطلوبة أو None
    
    Example:
        >>> extract_birthdate_formatted("28104111401638")
        '11/04/1981'
        >>> extract_birthdate_formatted("28104111401638", '%Y/%m/%d')
        '1981/04/11'
    """
    birthdate_iso = extract_birthdate(national_id)
    if not birthdate_iso:
        return None
    
    try:
        date_obj = datetime.strptime(birthdate_iso, '%Y-%m-%d')
        return date_obj.strftime(format_str)
    except ValueError:
        return None


def calculate_age(national_id: str) -> Optional[dict]:
    """
    حساب العمر من الرقم القومي
    
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
        >>> age = calculate_age("28104111401638")
        >>> print(f"{age['years']} سنة و {age['months']} شهر و {age['days']} يوم")
        '43 سنة و 8 أشهر و 0 يوم'
    """
    birthdate_iso = extract_birthdate(national_id)
    if not birthdate_iso:
        return None
    
    birth_date = datetime.strptime(birthdate_iso, '%Y-%m-%d')
    today = datetime.now()
    
    # حساب الفرق
    years = today.year - birth_date.year
    months = today.month - birth_date.month
    days = today.day - birth_date.day
    
    # تصحيح الأشهر والأيام
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


# اختبار الدوال
if __name__ == '__main__':
    # اختبار مع الرقم القومي من المثال
    test_id = "28104111401638"
    
    print(f"الرقم القومي: {test_id}")
    print(f"تاريخ الميلاد (ISO): {extract_birthdate(test_id)}")
    print(f"تاريخ الميلاد (DD/MM/YYYY): {extract_birthdate_formatted(test_id)}")
    
    age = calculate_age(test_id)
    if age:
        print(f"العمر: {age['years']} سنة و {age['months']} شهر و {age['days']} يوم")
        print(f"إجمالي الأيام: {age['total_days']}")
    
    print("\n--- اختبارات إضافية ---")
    # اختبار رقم غير صحيح
    print(f"رقم غير صحيح (13 رقم): {extract_birthdate('1234567890123')}")
    print(f"رقم غير صحيح (century): {extract_birthdate('18104111401638')}")
    # اختبار تاريخ غير صحيح (31 فبراير)
    print(f"تاريخ غير صحيح: {extract_birthdate('32203011401638')}")
