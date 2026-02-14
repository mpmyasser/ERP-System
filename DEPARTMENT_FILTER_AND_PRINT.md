# Department Filter & Print Feature - Implementation Summary

## Overview
Added multi-select department filter and print button to employee list page (`/employees/`).

## Changes Made

### 1. Backend Route Update: `app/routes/employees.py`
**Location**: `list()` function

**Changes**:
- Added `dept_ids = request.args.getlist('departments')` to capture multiple selected department IDs
- Added filtering logic to only include employees whose `department_id` matches selected departments
- Added `departments = db.get_departments()` to fetch all departments for dropdown
- Updated template context to pass:
  - `selected_departments`: List of currently selected department IDs
  - `departments`: List of all available departments
  - All other existing variables (search, pagination, etc.)

**Code**:
```python
dept_ids = request.args.getlist('departments')  # Get multiple department IDs
if dept_ids:
    dept_ids = [int(d) for d in dept_ids if d]  # Convert to integers
    employees = [e for e in employees if e.department_id in dept_ids]

departments = db.get_departments()

return render_template('employees/list.html',
                       ...,
                       selected_departments=dept_ids,
                       departments=departments,
                       ...)
```

### 2. Template Update: `app/templates/employees/list.html`

#### A. Search & Filter Form
- Reorganized search form to include department filter
- Added multi-select `<select>` element for departments
- Added print button (`<button onclick="window.print()">`)
- Added reset button to clear filters

**HTML**:
```html
<div class="col-md-4">
    <select name="departments" id="dept-filter" class="form-select" multiple>
        <option value="">-- اختر الأقسام --</option>
        {% for dept in departments %}
        <option value="{{ dept.id }}" 
            {% if dept.id in selected_departments %}selected{% endif %}>
            {{ dept.name }}
        </option>
        {% endfor %}
    </select>
</div>
```

#### B. Department Filter Script
- JavaScript to handle multi-select change events
- Auto-submits form when department selection changes
- Preserves search query when filtering by department
- Builds URL with proper query parameters

**Script**:
```javascript
document.getElementById('dept-filter')?.addEventListener('change', function() {
    const selected = Array.from(this.selectedOptions).map(opt => opt.value).filter(v => v);
    let url = '{{ url_for("employees.list") }}';
    const params = new URLSearchParams();
    
    if ('{{ search }}'.trim()) {
        params.append('search', '{{ search }}');
    }
    
    selected.forEach(dept => params.append('departments', dept));
    
    if (params.toString()) {
        url += '?' + params.toString();
    }
    
    window.location.href = url;
});
```

#### C. Print CSS
- Added `@media print` styles to hide form and toolbar when printing
- Configured page size as A4 with 10mm margins
- Prevented table breaks mid-page for better readability
- Set font size to 12pt for optimal print quality

**CSS**:
```css
@media print {
    .btn-toolbar, form, .d-flex.justify-content-between, .row.mb-3:first-child {
        display: none !important;
    }
    
    @page {
        size: A4;
        margin: 10mm;
    }
    
    body {
        font-size: 12pt;
    }
    
    .table {
        page-break-inside: avoid;
    }
}
```

## Features

### Multi-Select Department Filter
- Users can select multiple departments from dropdown
- Selection automatically applies filter to employee list
- Selected departments remain highlighted in dropdown
- Filter works in combination with search functionality
- URL query parameters reflect current filter state

### Print Button
- Integrated print button in employee list toolbar
- Triggers browser print dialog (`window.print()`)
- Print stylesheet automatically hides filter form and toolbar
- Displays only employee table with necessary columns
- A4 page size with appropriate margins

### Reset Functionality
- "إعادة تعيين" (Reset) button clears all filters
- Only displays when filters are active
- Returns to full employee list

## URL Structure

### With Department Filter
```
/employees/?departments=1&departments=3&search=ahmed
```

### Without Filter
```
/employees/
```

### With Search Only
```
/employees/?search=mahmoud
```

## User Experience

1. **Viewing employees**: User lands on employee list with all employees
2. **Selecting departments**: User clicks department dropdown and selects one or more departments
3. **Auto-filter**: Page automatically refreshes showing only employees from selected departments
4. **Printing**: User clicks print button and browser print dialog opens
5. **Print output**: Only the table is printed (no form, toolbar, pagination)
6. **Resetting**: User clicks reset button to return to full list

## Technical Details

- **Backend**: Flask route handles query parameters without page reload optimization
- **Frontend**: Plain JavaScript without jQuery dependency
- **Browser compatibility**: Works with all modern browsers supporting `URLSearchParams`
- **RTL support**: Bootstrap RTL classes applied to filter form
- **Multiple selections**: Form uses `request.args.getlist()` to capture multiple department IDs

## Testing

To test:
1. Navigate to `/employees/`
2. Select one or more departments from dropdown
3. Verify employees filter correctly
4. Click print button and verify print preview looks correct
5. Try combining search + department filter
6. Click reset and verify all employees appear

## Notes

- Print functionality uses browser's built-in print system (no external libraries required)
- Selected departments are preserved if user modifies search
- Department dropdown maintains selection state on page refresh
- RTL text direction maintained for Arabic interface
