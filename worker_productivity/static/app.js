/**
 * نظام تتبع إنتاج العمال - JavaScript
 */

// ========== إدارة العمال ==========

function showManageWorkers() {
    const modal = new bootstrap.Modal(document.getElementById('workersModal'));
    loadWorkers();
    modal.show();
}

function loadWorkers() {
    fetch('/api/workers')
        .then(r => r.json())
        .then(data => {
            const tbody = document.getElementById('workersTableBody');
            tbody.innerHTML = data.workers.map(w => `
                <tr>
                    <td>${w.code}</td>
                    <td>${w.name}</td>
                    <td>${w.hire_date}</td>
                    <td>${w.is_insured}</td>
                    <td>${w.salary.toLocaleString()}</td>
                    <td>${w.record_count}</td>
                    <td><button class="btn btn-danger btn-sm" onclick="deleteWorker('${w.code}')"><i class="bi bi-trash"></i></button></td>
                </tr>
            `).join('');
        });
}

function addWorker() {
    const code = document.getElementById('newWorkerCode').value.trim();
    const name = document.getElementById('newWorkerName').value.trim();
    const salary = document.getElementById('newWorkerSalary').value;

    if (!code || !name) {
        alert('الكود والاسم مطلوبان');
        return;
    }

    fetch('/api/workers/add', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({code, name, salary})
    })
    .then(r => r.json())
    .then(data => {
        if (data.ok) {
            document.getElementById('newWorkerCode').value = '';
            document.getElementById('newWorkerName').value = '';
            document.getElementById('newWorkerSalary').value = '';
            loadWorkers();
        } else {
            alert('خطأ: ' + data.message);
        }
    });
}

function deleteWorker(code) {
    if (!confirm(`هل تريد حذف العامل ${code} وجميع سجلاته؟`)) return;
    fetch('/api/workers/delete', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({code})
    })
    .then(r => r.json())
    .then(data => {
        if (data.ok) loadWorkers();
        else alert('خطأ: ' + data.message);
    });
}

// ========== إدارة المراحل ==========

function showManageStages() {
    const modal = new bootstrap.Modal(document.getElementById('stagesModal'));
    loadStages();
    modal.show();
}

function loadStages() {
    fetch('/api/stages')
        .then(r => r.json())
        .then(data => {
            const tbody = document.getElementById('stagesTableBody');
            tbody.innerHTML = data.stages.map(s => `
                <tr>
                    <td>${s.code}</td>
                    <td>${s.name}</td>
                    <td>${s.machine_type}</td>
                    <td>${s.product_type}</td>
                </tr>
            `).join('');
        });
}

function addStage() {
    const code = document.getElementById('newStageCode').value.trim();
    const name = document.getElementById('newStageName').value.trim();
    const machine_type = document.getElementById('newStageMachine').value;

    if (!code || !name) {
        alert('الكود والاسم مطلوبان');
        return;
    }

    fetch('/api/stages/add', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({code, name, machine_type})
    })
    .then(r => r.json())
    .then(data => {
        if (data.ok) {
            document.getElementById('newStageCode').value = '';
            document.getElementById('newStageName').value = '';
            document.getElementById('newStageMachine').value = '';
            loadStages();
        } else {
            alert('خطأ: ' + data.message);
        }
    });
}

// ========== إدارة الأصناف ==========

function showManageProducts() {
    const modal = new bootstrap.Modal(document.getElementById('productsModal'));
    loadProducts();
    modal.show();
}

function loadProducts() {
    fetch('/api/products')
        .then(r => r.json())
        .then(data => {
            const tbody = document.getElementById('productsTableBody');
            tbody.innerHTML = data.products.map(p => `
                <tr>
                    <td>${p.code}</td>
                    <td>${p.name}</td>
                    <td>${p.size}</td>
                </tr>
            `).join('');
        });
}

function addProduct() {
    const code = document.getElementById('newProductCode').value.trim();
    const name = document.getElementById('newProductName').value.trim();
    const size = document.getElementById('newProductSize').value.trim();

    if (!code || !name || !size) {
        alert('الكود والاسم والمقاس مطلوبون');
        return;
    }

    fetch('/api/products/add', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({code, name, size})
    })
    .then(r => r.json())
    .then(data => {
        if (data.ok) {
            document.getElementById('newProductCode').value = '';
            document.getElementById('newProductName').value = '';
            document.getElementById('newProductSize').value = '';
            loadProducts();
        } else {
            alert('خطأ: ' + data.message);
        }
    });
}

// ========== استيراد من Excel ==========

function showImportFromExcel() {
    const modal = new bootstrap.Modal(document.getElementById('importModal'));
    document.getElementById('importResult').style.display = 'none';
    document.getElementById('importProgress').style.display = 'none';
    modal.show();
}

function importFromExcel() {
    const filePath = document.getElementById('excelFilePath').value.trim();
    if (!filePath) {
        alert('أدخل مسار ملف Excel');
        return;
    }

    document.getElementById('importProgress').style.display = 'block';
    document.getElementById('importResult').style.display = 'none';

    fetch('/api/import-excel-data', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({file_path: filePath})
    })
    .then(r => r.json())
    .then(data => {
        document.getElementById('importProgress').style.display = 'none';
        document.getElementById('importResult').style.display = 'block';
        if (data.ok) {
            document.getElementById('importResult').className = 'alert alert-success';
            document.getElementById('importResult').innerHTML = `
                <h5><i class="bi bi-check-circle"></i> تم الاستيراد بنجاح!</h5>
                <ul>
                    <li>العمال: ${data.workers} مضافة</li>
                    <li>المراحل: ${data.stages} مضافة</li>
                    <li>الأصناف: ${data.products} مضافة</li>
                    <li>سجلات الإنتاج: ${data.records} مضافة</li>
                </ul>
                ${data.errors && data.errors.length > 0 ? '<hr><div class="text-danger"><small>' + data.errors.slice(0, 5).join('<br>') + '</small></div>' : ''}
            `;
        } else {
            document.getElementById('importResult').className = 'alert alert-danger';
            document.getElementById('importResult').innerHTML = 'خطأ: ' + data.message;
        }
    })
    .catch(err => {
        document.getElementById('importProgress').style.display = 'none';
        document.getElementById('importResult').style.display = 'block';
        document.getElementById('importResult').className = 'alert alert-danger';
        document.getElementById('importResult').innerHTML = 'خطأ في الاتصال: ' + err;
    });
}