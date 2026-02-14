# دليل استخراج البيانات من الرقم القومي المصري
# Egyptian National ID Parser Guide

## نظرة عامة | Overview

تم تطوير نظام متكامل لاستخراج تاريخ الميلاد والعمر من الرقم القومي المصري بشكل تلقائي.

**A comprehensive system has been developed to automatically extract birth date and age from the Egyptian National ID.**

---

## تركيب الرقم القومي المصري | Egyptian National ID Structure

الرقم القومي المصري يتكون من **14 رقم** بالصيغة التالية:

| الموضع | العدد | الوصف | الرموز |
|-------|-------|--------|--------|
| 1 | 1 | رقم تحديد القرن (Century Digit) | 2 = 1900s, 3 = 2000s |
| 2-3 | 2 | السنة بصيغة ثنائية (Two-digit Year) | YY |
| 4-5 | 2 | الشهر (Month) | MM |
| 6-7 | 2 | اليوم (Day) | DD |
| 8-12 | 5 | رقم تسلسلي (Serial/Governorate Number) | SSSSS |
| 13-14 | 2 | رقم التحقق (Checksum) | CC |

### مثال | Example

الرقم القومي: **28104111401638**

```
2    81   04   11   01401  638
↓    ↓    ↓    ↓    ↓      ↓
|    |    |    |    |      +-- Checksum
|    |    |    |    +--------- Serial Number
|    |    |    +------------- Day (11)
|    |    +----------------- Month (04)
|    +---------------------- Year (81)
+--------------------------- Century (2 = 1900s)

القرن: 1900s
السنة: 81 → 1981
الشهر: 04 (أبريل)
اليوم: 11

تاريخ الميلاد: 11 أبريل 1981 → 1981-04-11 (ISO)
```

---

## دوال Python | Python Functions

جميع الدوال موجودة في: `core/utils/helpers.py`

### 1. `extract_birthdate_from_national_id(national_id)`

استخراج تاريخ الميلاد من الرقم القومي.

**Parameters:**
- `national_id` (str): الرقم القومي (14 رقم)

**Returns:**
- `datetime.date`: تاريخ الميلاد أو `None` إذا كان غير صحيح

**Example:**
```python
from core.utils.helpers import extract_birthdate_from_national_id

birthdate = extract_birthdate_from_national_id("28104111401638")
print(birthdate)  # 1981-04-11
print(birthdate.strftime('%d/%m/%Y'))  # 11/04/1981
```

### 2. `calculate_age_from_national_id(national_id)`

حساب العمر الحالي من الرقم القومي.

**Parameters:**
- `national_id` (str): الرقم القومي (14 رقم)

**Returns:**
- `dict`: قاموس يحتوي على:
  - `years` (int): السنوات
  - `months` (int): الأشهر
  - `days` (int): الأيام
  - `total_days` (int): إجمالي الأيام
- أو `None` إذا كان الرقم غير صحيح

**Example:**
```python
from core.utils.helpers import calculate_age_from_national_id

age = calculate_age_from_national_id("28104111401638")
print(age)  
# {'years': 44, 'months': 7, 'days': 29, 'total_days': 16314}

print(f"العمر: {age['years']} سنة و {age['months']} شهر و {age['days']} يوم")
# العمر: 44 سنة و 7 شهر و 29 يوم
```

---

## دوال JavaScript | JavaScript Functions

جميع الدوال موجودة في: `app/static/js/national_id_parser.js`

### 1. `EgyptianNationalIDParser.extractBirthDate(nationalId)`

استخراج تاريخ الميلاد.

**Parameters:**
- `nationalId` (string): الرقم القومي (14 رقم)

**Returns:**
- `Date`: كائن التاريخ أو `null`

**Example:**
```javascript
const birthDate = EgyptianNationalIDParser.extractBirthDate("28104111401638");
if (birthDate) {
    console.log(birthDate.toLocaleDateString('en-CA')); // 1981-04-11
}
```

### 2. `EgyptianNationalIDParser.calculateAge(birthDate)`

حساب العمر من تاريخ الميلاد.

**Parameters:**
- `birthDate` (Date): تاريخ الميلاد

**Returns:**
- `object`: {years, months, days, totalDays}

**Example:**
```javascript
const birthDate = EgyptianNationalIDParser.extractBirthDate("28104111401638");
const age = EgyptianNationalIDParser.calculateAge(birthDate);
console.log(age); // {years: 44, months: 7, days: 29, totalDays: 16314}
```

### 3. `EgyptianNationalIDParser.formatAgeArabic(ageObj)`

تنسيق العمر بصيغة عربية.

**Example:**
```javascript
const ageText = EgyptianNationalIDParser.formatAgeArabic(age);
console.log(ageText); // "44 سنة و 7 أشهر و 29 يوم"
```

### 4. `EgyptianNationalIDParser.formatAgeShort(ageObj)`

تنسيق العمر بصيغة مختصرة.

**Example:**
```javascript
const shortAge = EgyptianNationalIDParser.formatAgeShort(age);
console.log(shortAge); // "44 سنة"
```

---

## الاستخدام في النموذج | Form Implementation

### في `app/templates/employees/form.html`

تم إضافة المكونات التالية:

```html
<!-- حقل الرقم القومي -->
<div class="mb-3">
    <label for="national_id" class="form-label">الرقم القومي</label>
    <input type="text" class="form-control" id="national_id" 
           name="national_id" maxlength="14"
           placeholder="أدخل 14 رقم">
    <small class="text-muted">سيتم استخراج تاريخ الميلاد والعمر تلقائياً</small>
</div>

<!-- حقل تاريخ الميلاد (سيتم ملؤه تلقائياً) -->
<div class="mb-3">
    <label for="date_of_birth" class="form-label">تاريخ الميلاد</label>
    <input type="text" class="form-control date-string" id="date_of_birth" 
           name="date_of_birth" placeholder="DD/MM/YYYY"
           readonly>
</div>

<!-- عرض العمر والمعلومات -->
<div id="age-display"></div>

<!-- تحميل السكريبت -->
<script src="{{ url_for('static', filename='js/national_id_parser.js') }}"></script>
```

---

## مثال عملي | Practical Example

### استخدام في Route

```python
from flask import request
from core.utils.helpers import extract_birthdate_from_national_id, calculate_age_from_national_id

@app.route('/api/extract-birthdate', methods=['POST'])
def extract_birthdate():
    data = request.json
    national_id = data.get('national_id')
    
    birthdate = extract_birthdate_from_national_id(national_id)
    if not birthdate:
        return {'error': 'Invalid national ID'}, 400
    
    age = calculate_age_from_national_id(national_id)
    
    return {
        'birthdate': birthdate.isoformat(),
        'birthdate_formatted': birthdate.strftime('%d/%m/%Y'),
        'age': age
    }
```

### استخدام في JavaScript

```javascript
document.getElementById('national_id').addEventListener('input', function(e) {
    const nationalId = e.target.value.trim();
    
    const birthDate = EgyptianNationalIDParser.extractBirthDate(nationalId);
    if (!birthDate) {
        document.getElementById('date_of_birth').value = '';
        document.getElementById('age-display').innerHTML = '';
        return;
    }
    
    // ملء تاريخ الميلاد
    const year = birthDate.getFullYear();
    const month = String(birthDate.getMonth() + 1).padStart(2, '0');
    const day = String(birthDate.getDate()).padStart(2, '0');
    document.getElementById('date_of_birth').value = `${day}/${month}/${year}`;
    
    // عرض العمر
    const age = EgyptianNationalIDParser.calculateAge(birthDate);
    const ageText = EgyptianNationalIDParser.formatAgeArabic(age);
    document.getElementById('age-display').innerHTML = `
        <div class="alert alert-info">
            <strong>العمر:</strong> ${ageText}
        </div>
    `;
});
```

---

## التحقق من الصحة | Validation

### القواعد:
1. ✅ الرقم يجب أن يكون **14 رقم** بالضبط
2. ✅ الرقم الأول يجب أن يكون **2 أو 3** فقط
3. ✅ الشهر يجب أن يكون بين **01** و **12**
4. ✅ اليوم يجب أن يكون بين **01** و **31**
5. ✅ يجب أن يكون التاريخ **صحيح** (مثلاً 31 فبراير غير صحيح)

### أمثلة خاطئة:
```
28104311401638  ← شهر 43 (غير صحيح)
28132111401638  ← يوم 32 (غير صحيح)
1234567890123   ← 13 رقم فقط (غير صحيح)
18104111401638  ← century digit 1 (غير صحيح)
```

---

## ملاحظات مهمة | Important Notes

1. **النطاق الزمني للسنوات:**
   - القرن رقم 2: 1900-1999 (الرقم الأول = 2)
   - القرن رقم 3: 2000-2099 (الرقم الأول = 3)

2. **التوافقية:**
   - الدوال متوفرة في كل من Python و JavaScript
   - تستخدم نفس منطق استخراج البيانات

3. **الخطأ الشائع:**
   - تأكد من **عدم إضافة مسافات أو علامات ترقيم** في الرقم القومي

---

## اختبار سريع | Quick Test

```bash
# Python test
python -c "
from core.utils.helpers import extract_birthdate_from_national_id, calculate_age_from_national_id

bd = extract_birthdate_from_national_id('28104111401638')
age = calculate_age_from_national_id('28104111401638')

print(f'Birth Date: {bd}')
print(f'Age: {age}')
"
```

---

## التكامل مع قاعدة البيانات | Database Integration

عند حفظ الموظف:

```python
# Extract birth date from national ID automatically
birthdate = extract_birthdate_from_national_id(employee.national_id)
if birthdate:
    employee.date_of_birth = birthdate
    db.session.commit()
```

---

**تم إنشاء هذا النظام لتحسين دقة وسرعة معالجة بيانات الموظفين.**
