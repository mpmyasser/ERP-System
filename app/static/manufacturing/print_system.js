window.OperationPrint = (() => {
    function getPrintPageMarginsMm() {
        try {
            const saved = localStorage.getItem('print_page_margins_mm');
            if (saved) return JSON.parse(saved);
        } catch (_) {}
        return { top: 10, right: 10, bottom: 10, left: 10 };
    }

    function setPrintPageMarginsMm(margins) {
        localStorage.setItem('print_page_margins_mm', JSON.stringify(margins));
        syncPrintMarginInputsToDom();
    }

    function clampMarginMm(val) {
        let v = parseInt(val);
        if (isNaN(v)) return 10;
        return Math.min(Math.max(v, 0), 50);
    }

    function syncPrintMarginInputsToDom() {
        const margins = getPrintPageMarginsMm();
        const map = {
            'top': 'printMarginTopInput',
            'right': 'printMarginRightInput',
            'bottom': 'printMarginBottomInput',
            'left': 'printMarginLeftInput'
        };
        for (const [key, id] of Object.entries(map)) {
            const el = document.getElementById(id);
            if (el) el.value = margins[key];
        }
    }

    function initPrintSettings(config) {
        const { tableId, storageKey, onToggle, containerId = 'unifiedPrintSettings' } = config;
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <div id="printColumnsPanel" class="d-none mt-2 p-3 border rounded bg-white shadow-sm d-print-none">
                <div class="d-flex justify-content-between align-items-center mb-2 pb-2 border-bottom">
                    <h6 class="mb-0 text-primary"><i class="fas fa-print me-1"></i> إعدادات الطباعة المتقدمة</h6>
                    <div class="d-flex gap-2">
                        <button type="button" class="btn btn-xs btn-outline-primary btn-select-all" style="font-size: 0.7rem; padding: 1px 5px;">تحديد الكل</button>
                        <button type="button" class="btn btn-xs btn-outline-secondary btn-clear-all" style="font-size: 0.7rem; padding: 1px 5px;">إلغاء الكل</button>
                    </div>
                </div>
                
                <div class="row g-2 mb-3" id="printColumnsOptions"></div>

                <div class="row g-3 border-top pt-2 mt-2">
                    <div class="col-md-6">
                        <div class="small fw-bold mb-2 text-secondary"><i class="fas fa-cog me-1"></i> خيارات عامة</div>
                        <div class="d-flex flex-wrap gap-3">
                            <div class="form-check small">
                                <input class="form-check-input" type="checkbox" id="printShowTimeCheck">
                                <label class="form-check-label" for="printShowTimeCheck">عرض التاريخ والوقت</label>
                            </div>
                            <div class="form-check small">
                                <input class="form-check-input" type="checkbox" id="printShowPageNumbersCheck">
                                <label class="form-check-label" for="printShowPageNumbersCheck">رقم الصفحة</label>
                            </div>
                            <div class="form-check small">
                                <input class="form-check-input" type="checkbox" id="printLandscapeCheck">
                                <label class="form-check-label" for="printLandscapeCheck">وضع أفقي (Landscape)</label>
                            </div>
                        </div>
                        <div class="mt-2 border-top pt-2">
                            <label class="small fw-bold text-secondary d-block mb-1"><i class="fas fa-arrows-alt-v me-1"></i> ارتفاع الصفوف (كثافة الجدول)</label>
                            <input type="range" class="form-range" id="printRowPaddingRange" min="1" max="15" step="1">
                            <div class="d-flex justify-content-between small text-muted" style="font-size: 0.65rem;">
                                <span>مضغوط</span>
                                <span>متوسط</span>
                                <span>مريح</span>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6 border-start ps-3">
                        <div class="small fw-bold mb-1 text-secondary"><i class="fas fa-arrows-alt me-1"></i> هوامش الصفحة (ملم)</div>
                        <div class="row g-1 text-center">
                            <div class="col-3"><input type="number" class="form-control form-control-xs p-1" id="printMarginTopInput" min="0" max="50" style="font-size: 0.7rem; height: 22px;" title="أعلى"></div>
                            <div class="col-3"><input type="number" class="form-control form-control-xs p-1" id="printMarginBottomInput" min="0" max="50" style="font-size: 0.7rem; height: 22px;" title="أسفل"></div>
                            <div class="col-3"><input type="number" class="form-control form-control-xs p-1" id="printMarginRightInput" min="0" max="50" style="font-size: 0.7rem; height: 22px;" title="يمين"></div>
                            <div class="col-3"><input type="number" class="form-control form-control-xs p-1" id="printMarginLeftInput" min="0" max="50" style="font-size: 0.7rem; height: 22px;" title="يسار"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        buildColumnChooser(tableId, 'printColumnsPanel', 'printColumnsOptions', storageKey, onToggle);
        bindPrintMarginInputsOnce();
        syncPrintMarginInputsToDom();

        const showTimeCheck = document.getElementById('printShowTimeCheck');
        if (showTimeCheck) {
            showTimeCheck.checked = localStorage.getItem('print_show_time') !== 'false';
            showTimeCheck.addEventListener('change', (e) => localStorage.setItem('print_show_time', e.target.checked));
        }

        const landscapeCheck = document.getElementById('printLandscapeCheck');
        if (landscapeCheck) {
            landscapeCheck.checked = localStorage.getItem('print_landscape') === 'true';
            landscapeCheck.addEventListener('change', (e) => localStorage.setItem('print_landscape', e.target.checked));
        }

        const applyLivePadding = (val) => {
            const table = document.getElementById(tableId);
            if (!table) return;
            const cells = table.querySelectorAll('th, td');
            cells.forEach(c => {
                c.style.setProperty('padding-top', val + 'px', 'important');
                c.style.setProperty('padding-bottom', val + 'px', 'important');
            });
        };

        const rowPaddingRange = document.getElementById('printRowPaddingRange');
        if (rowPaddingRange) {
            const savedPadding = localStorage.getItem('print_row_padding') || '5';
            rowPaddingRange.value = savedPadding;
            applyLivePadding(savedPadding); // Apply initial saved value
            
            rowPaddingRange.addEventListener('input', (e) => {
                const val = e.target.value;
                localStorage.setItem('print_row_padding', val);
                applyLivePadding(val);
            });
        }

        const toggleBtn = document.getElementById('togglePrintColumnsButton');
        const panel = document.getElementById('printColumnsPanel');
        toggleBtn?.addEventListener('click', () => {
            panel.classList.toggle('d-none');
            if (!panel.classList.contains('d-none')) {
                panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    }

    function buildColumnChooser(tableId, panelId, optionsId, storageKey, onToggle) {
        const table = document.getElementById(tableId);
        const options = document.getElementById(optionsId);
        if (!table || !options) return;

        const headers = Array.from(table.querySelectorAll('thead th'));
        const saved = JSON.parse(localStorage.getItem(storageKey) || '[]');
        
        options.innerHTML = '';
        headers.forEach((th, index) => {
            if (th.dataset.print === 'no' || !th.textContent.trim()) return;
            const colName = th.textContent.trim();
            const isChecked = saved.length ? saved.includes(index) : true;
            
            const div = document.createElement('div');
            div.className = 'col-auto';
            div.style.minWidth = '120px';
            div.innerHTML = `
                <div class="form-check small p-0 m-0 d-flex align-items-center gap-1">
                    <input class="form-check-input print-column-check m-0" type="checkbox" value="${index}" id="col_${tableId}_${index}" ${isChecked ? 'checked' : ''} style="width: 14px; height: 14px;">
                    <label class="form-check-label text-nowrap" for="col_${tableId}_${index}" style="font-size: 0.8rem; cursor: pointer;">${colName}</label>
                </div>
            `;
            options.appendChild(div);
        });

        const saveSelection = () => {
            const checked = Array.from(options.querySelectorAll('.print-column-check:checked')).map(i => Number(i.value));
            localStorage.setItem(storageKey, JSON.stringify(checked));
            if (onToggle) onToggle(checked);
        };
        options.addEventListener('change', saveSelection);
    }

    function bindPrintMarginInputsOnce() {
        const map = {
            'top': 'printMarginTopInput',
            'right': 'printMarginRightInput',
            'bottom': 'printMarginBottomInput',
            'left': 'printMarginLeftInput'
        };
        for (const [key, id] of Object.entries(map)) {
            const el = document.getElementById(id);
            if (!el) continue;
            el.addEventListener('change', () => {
                const margins = getPrintPageMarginsMm();
                margins[key] = clampMarginMm(el.value);
                setPrintPageMarginsMm(margins);
            });
        }
    }

    function printTable(config) {
        const { tableId, title = 'تقرير', summary = null } = config;
        const table = document.getElementById(tableId);
        if (!table) return;

        const options = document.getElementById('printColumnsOptions');
        let selected = Array.from(options.querySelectorAll('.print-column-check:checked')).map(i => Number(i.value));
        if (!selected.length) { alert('اختر عموداً واحداً على الأقل'); return; }

        const headers = Array.from(table.querySelectorAll('thead th'));
        const rows = Array.from(table.querySelectorAll('tbody tr:not(.d-none):not(.no-print)'));
        const showTime = localStorage.getItem('print_show_time') !== 'false';
        const showPageNumbers = localStorage.getItem('print_show_page_numbers') !== 'false';
        const landscape = localStorage.getItem('print_landscape') === 'true';
        const margins = getPrintPageMarginsMm();
        const rowPadding = localStorage.getItem('print_row_padding') || '5';
        const nowStr = new Date().toLocaleString('ar-EG');

        const win = window.open('', '_blank');
        win.document.write(`
            <html lang="ar" dir="rtl">
            <head>
                <title>${title}</title>
                <style>
                    @page { 
                        margin: ${margins.top}mm ${margins.right}mm ${margins.bottom}mm ${margins.left}mm; 
                        size: A4 ${landscape ? 'landscape' : ''}; 
                    }
                    body { 
                        font-family: Arial, sans-serif; 
                        direction: rtl; 
                        padding: 0;
                        margin: 0;
                    }
                    .print-header {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 15px;
                        border-bottom: 2px solid #333;
                        padding-bottom: 8px;
                    }
                    .print-title { font-size: 22px; font-weight: bold; margin: 0; }
                    .print-meta { font-size: 11px; color: #444; }
                    
                    table { width: 100%; border-collapse: collapse; margin-top: 5px; table-layout: auto; }
                    th, td { border: 1px solid #000; padding: ${rowPadding}px 3px !important; text-align: center; font-size: 12px; word-wrap: break-word; }
                    th { background: #eee; font-weight: bold; }
                    
                    .summary-box {
                        margin-top: 20px;
                        border: 2px solid #000;
                        border-radius: 12px;
                        padding: 12px;
                        display: flex;
                        justify-content: space-around;
                        font-weight: bold;
                        font-size: 16px;
                        background: #fff;
                    }
                    .summary-item { display: flex; gap: 8px; }
                    
                    .footer-info {
                        position: fixed;
                        bottom: 0;
                        left: 0;
                        right: 0;
                        display: flex;
                        justify-content: space-between;
                        font-size: 9px;
                        color: #777;
                        padding-top: 4px;
                        border-top: 1px solid #ccc;
                    }

                    @media print {
                        .page-number::after { content: counter(page); }
                        .summary-box { page-break-inside: avoid; }
                    }
                </style>
            </head>
            <body>
                <div class="print-header">
                    <div style="width:180px"></div> <!-- Spacer to balance the meta info -->
                    <div class="print-title">${title}</div>
                    <div class="print-meta" style="width:180px; text-align: left;">
                        ${showTime ? `<div>التاريخ: ${nowStr}</div>` : ''}
                    </div>
                </div>

                <table>
                    <thead>
                        <tr>${selected.map(i => `<th>${headers[i].textContent.trim()}</th>`).join('')}</tr>
                    </thead>
                    <tbody>
                        ${rows.map(row => {
                            const cells = Array.from(row.querySelectorAll('td'));
                            return `<tr>${selected.map(i => {
                                const cell = cells[i];
                                const input = cell.querySelector('input, select, textarea');
                                let val = '';
                                if (input) {
                                    val = input.value;
                                } else {
                                    val = cell.innerText || cell.textContent || '';
                                }
                                return `<td>${val.trim()}</td>`;
                            }).join('')}</tr>`;
                        }).join('')}
                    </tbody>
                </table>

                ${summary ? `
                <div class="summary-box">
                    ${summary.messages !== undefined ? `<div class="summary-item"><span>عدد الرسائل:</span><span>${summary.messages}</span></div>` : ''}
                    ${summary.items !== undefined ? `<div class="summary-item"><span>عدد الأصناف:</span><span>${summary.items}</span></div>` : ''}
                    ${summary.quantity !== undefined ? `<div class="summary-item"><span>مجموع الكميات:</span><span>${summary.quantity}</span></div>` : ''}
                </div>
                ` : ''}

                <div class="footer-info">
                    <span>نظام التشغيل والمصنع</span>
                    ${showPageNumbers ? `<span class="page-count">صفحة رقم <span class="page-number"></span></span>` : ''}
                </div>

                <script>
                    window.onload = () => {
                        setTimeout(() => { 
                            window.print(); 
                            window.close(); 
                        }, 500);
                    };
                <\/script>
            </body>
            </html>
        `);
        win.document.close();
    }

    return { initPrintSettings, printTable };
})();
