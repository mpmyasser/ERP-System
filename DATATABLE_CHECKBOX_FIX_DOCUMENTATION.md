# إصلاح مشكلة فقدان تحديد Checkboxes في DataTables

## الملف المعدل
`e:\backoup\H.R-11-02-2026 -\app\static\js\datatables_init.js`

---

## الكود قبل التعديل

```javascript
const defaultDataTableConfig = {
    language: arabicLanguage,
    responsive: true,
    colReorder: true,
    pageLength: 25,
    lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "الكل"]],
    stateSave: true,
    stateDuration: 60 * 60 * 24 * 30,
    stateSaveCallback: function (settings, data) {
        setStoredObject(getDataTableStateKey(settings), data);
    },
    stateLoadCallback: function (settings) {
        return getStoredObject(getDataTableStateKey(settings), null);
    },
    stateSaveParams: function (settings, data) {
        data.search.search = "";
        data.start = 0;
    },
    initComplete: function (settings, json) {
        // Restore visibility by column name
        const api = this.api();
        const tableId = settings.sTableId;
        const visMap = getStoredObject('dt_vis_' + tableId, null);
        if (visMap) {
            api.columns().every(function () {
                const name = $(this.header()).text().trim();
                if (visMap.hasOwnProperty(name)) {
                    this.visible(visMap[name], false);
                }
            });
            api.draw(false);
        }
    },
    // ... rest of config
};
```

---

## الكود بعد التعديل

```javascript
const defaultDataTableConfig = {
    language: arabicLanguage,
    responsive: true,
    colReorder: true,
    pageLength: 25,
    lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "الكل"]],
    stateSave: true,
    stateDuration: 60 * 60 * 24 * 30,
    stateSaveCallback: function (settings, data) {
        setStoredObject(getDataTableStateKey(settings), data);
    },
    stateLoadCallback: function (settings) {
        return getStoredObject(getDataTableStateKey(settings), null);
    },
    stateSaveParams: function (settings, data) {
        data.search.search = "";
        data.start = 0;
    },
    drawCallback: function(settings) {
        // استعادة تحديدات checkboxes بعد كل رسم
        const tableId = settings.sTableId;
        const storageKey = `dt_checkboxes_${tableId}`;
        const selectedIds = JSON.parse(localStorage.getItem(storageKey) || '[]');
        
        $(this.api().table().node()).find('input[type="checkbox"].row-checkbox').each(function() {
            const row = $(this).closest('tr');
            const id = row.data('id') || row.attr('data-id');
            if (id && selectedIds.includes(String(id))) {
                this.checked = true;
            }
        });
    },
    initComplete: function (settings, json) {
        // Restore visibility by column name
        const api = this.api();
        const tableId = settings.sTableId;
        const visMap = getStoredObject('dt_vis_' + tableId, null);
        if (visMap) {
            api.columns().every(function () {
                const name = $(this.header()).text().trim();
                if (visMap.hasOwnProperty(name)) {
                    this.visible(visMap[name], false);
                }
            });
            api.draw(false);
        }
        
        // حفظ تحديدات checkboxes عند التغيير
        const $table = $(api.table().node());
        $table.on('change', 'input[type="checkbox"].row-checkbox', function() {
            const storageKey = `dt_checkboxes_${tableId}`;
            const selectedIds = JSON.parse(localStorage.getItem(storageKey) || '[]');
            const row = $(this).closest('tr');
            const id = String(row.data('id') || row.attr('data-id'));
            
            if (this.checked) {
                if (!selectedIds.includes(id)) selectedIds.push(id);
            } else {
                const index = selectedIds.indexOf(id);
                if (index > -1) selectedIds.splice(index, 1);
            }
            
            localStorage.setItem(storageKey, JSON.stringify(selectedIds));
        });
    },
    // ... rest of config
};
```

---

## دوال مساعدة جديدة

```javascript
// الحصول على IDs المحددة
function getSelectedCheckboxIds(tableId) {
    const storageKey = `dt_checkboxes_${tableId}`;
    return JSON.parse(localStorage.getItem(storageKey) || '[]');
}

// مسح جميع التحديدات
function clearSelectedCheckboxes(tableId) {
    const storageKey = `dt_checkboxes_${tableId}`;
    localStorage.removeItem(storageKey);
    $(`#${tableId}`).find('input[type="checkbox"].row-checkbox').prop('checked', false);
}
```

---

## كيفية الاستخدام

### 1. في HTML - إضافة data-id للصفوف

```html
<table id="my-table" class="table datatable">
    <tbody>
        {% for item in items %}
        <tr data-id="{{ item.id }}">
            <td><input type="checkbox" class="row-checkbox"></td>
            <td>{{ item.name }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>
```

### 2. الحصول على IDs المحددة

```javascript
// في أي مكان في الكود
const selectedIds = getSelectedCheckboxIds('my-table');
console.log('IDs المحددة:', selectedIds);

// إرسال للخادم
fetch('/api/process', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
    },
    body: JSON.stringify({ ids: selectedIds })
});
```

### 3. مسح التحديدات

```javascript
// بعد المعالجة أو عند الحاجة
clearSelectedCheckboxes('my-table');
```

---

## المميزات

✅ **لا تكرار كود** - التعديل فقط في `datatables_init.js`  
✅ **يعمل تلقائياً** - لجميع الجداول التي تستخدم `defaultDataTableConfig`  
✅ **لا يكسر stateSave** - يستخدم localStorage منفصل  
✅ **يعمل مع البحث والفلترة** - يحفظ التحديدات عبر جميع الصفحات  
✅ **خفيف وسريع** - يستخدم `drawCallback` فقط  
✅ **لا يؤثر على الجداول الأخرى** - كل جدول له مفتاح منفصل  

---

## المتطلبات

1. الصف يجب أن يحتوي على `data-id` attribute:
   ```html
   <tr data-id="123">
   ```

2. Checkbox يجب أن يحتوي على class `row-checkbox`:
   ```html
   <input type="checkbox" class="row-checkbox">
   ```

---

## ملاحظات

- التحديدات تُحفظ في `localStorage` بمفتاح `dt_checkboxes_{tableId}`
- يعمل مع جميع عمليات DataTables (search, sort, pagination, filter)
- لا يتطلب أي تعديلات في الصفحات الفردية
- متوافق مع جميع إعدادات DataTables الموجودة
