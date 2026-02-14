// Table Resizer - makes columns independently resizable and persists widths per page and table
(function () {
    const STORAGE_PREFIX = 'hr_table_widths:';

    function readStoredValue(key) {
        if (!window.HRSettingsUtil) return null;
        return window.HRSettingsUtil.get(key, null);
    }

    function writeStoredValue(key, value) {
        if (!window.HRSettingsUtil) return;
        window.HRSettingsUtil.set(key, value);
    }

    function removeStoredValue(key) {
        if (!window.HRSettingsUtil) return;
        window.HRSettingsUtil.remove(key);
    }

    function listStoredKeysByPrefix(prefix) {
        if (!window.HRSettingsUtil) return [];
        return window.HRSettingsUtil.listKeys(prefix || '');
    }

    // Inject minimal CSS for resizer UI so it's visible across pages
    (function injectStyles() {
        if (document.getElementById('hr-table-resizer-styles')) return;
        const css = `
        .col-resizer{position:absolute; top:0; right:0; width:8px; cursor:col-resize; background:transparent; transition:background .12s}
        .col-resizer:hover{background:rgba(13,110,253,0.15)}
        .col-lock{background:rgba(255,255,255,0.9); border-radius:4px; padding:2px 6px; font-size:0.85rem; color:#222}
        .hr-resizer-reset, .hr-resizer-lockall{opacity:0.95}
        `;
        const s = document.createElement('style'); s.id = 'hr-table-resizer-styles'; s.innerHTML = css; document.head.appendChild(s);
    })();

    function getKey(table) {
        const tId = table.id || table.getAttribute('data-table-key') || Array.from(document.querySelectorAll('table')).indexOf(table);
        return STORAGE_PREFIX + location.pathname + ':' + tId;
    }

    function getTableIdentifier(table) {
        return table.id || table.getAttribute('data-table-key') || Array.from(document.querySelectorAll('table')).indexOf(table).toString();
    }

    function getHeaderMeta(table) {
        const header = table.tHead;
        if (!header) return null;
        const rows = Array.from(header.rows);
        if (rows.length === 0) return null;

        // Determine total columns using max colSpan sum across header rows
        let colCount = 0;
        rows.forEach(r => {
            const sum = Array.from(r.cells).reduce((acc, th) => acc + (th.colSpan || 1), 0);
            if (sum > colCount) colCount = sum;
        });

        // Build a grid to map header cells to column indices (handles rowSpan/colSpan)
        const grid = Array.from({ length: rows.length }, () => Array(colCount).fill(null));
        const cellMap = new Map();

        rows.forEach((row, rIdx) => {
            let cIdx = 0;
            Array.from(row.cells).forEach(cell => {
                while (grid[rIdx][cIdx]) cIdx++;
                const spanCols = cell.colSpan || 1;
                const spanRows = cell.rowSpan || 1;
                cellMap.set(cell, cIdx);
                for (let rr = 0; rr < spanRows; rr++) {
                    for (let cc = 0; cc < spanCols; cc++) {
                        if (rIdx + rr < rows.length && cIdx + cc < colCount) {
                            grid[rIdx + rr][cIdx + cc] = cell;
                        }
                    }
                }
                cIdx += spanCols;
            });
        });

        return { header, rows, lastRow: rows[rows.length - 1], colCount, cellMap };
    }

    function createColGroupIfMissing(table) {
        let colgroup = table.querySelector('colgroup');
        const meta = getHeaderMeta(table);
        if (!meta) return null;
        const columns = meta.colCount;

        if (!colgroup) {
            colgroup = document.createElement('colgroup');
            for (let i = 0; i < columns; i++) {
                const col = document.createElement('col');
                colgroup.appendChild(col);
            }
            table.insertBefore(colgroup, table.firstChild);
        } else {
            // Ensure enough <col>
            const existing = colgroup.children.length;
            for (let i = existing; i < columns; i++) colgroup.appendChild(document.createElement('col'));
        }
        return colgroup;
    }

    function loadWidths(table) {
        try {
            const key = getKey(table);
            const raw = readStoredValue(key);
            if (!raw) return null;
            const widths = JSON.parse(raw);
            return widths;
        } catch (e) {
            console.error('Failed to load widths', e);
            return null;
        }
    }

    function saveWidths(table) {
        try {
            // Ensure table width matches column widths
            updateTableWidthFromCols(table);

            const key = getKey(table);
            const cols = table.querySelectorAll('colgroup col');
            const widths = Array.from(cols).map(c => c.style.width || window.getComputedStyle(c).width || null);
            writeStoredValue(key, JSON.stringify(widths));

            // Send to server if user is authenticated (best-effort, non-blocking)
            try {
                const csrf = document.querySelector('meta[name="csrf-token"]') ? document.querySelector('meta[name="csrf-token"]').getAttribute('content') : null;
                const payload = { page: location.pathname, table_key: getTableIdentifier(table), widths: widths };
                fetch('/settings/table_widths', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
                    body: JSON.stringify(payload),
                    credentials: 'same-origin'
                }).then(res => res.json()).then(data => {
                    if (!data || !data.success) {
                        // silently ignore failure (user may be not authenticated)
                    }
                }).catch(err => {
                    // ignore network errors
                });
            } catch (e) { /* noop */ }

        } catch (e) {
            console.error('Failed to save widths', e);
        }
    }

    function applyWidths(table, widths) {
        const cols = table.querySelectorAll('colgroup col');
        if (!widths || !cols || cols.length === 0) return;
        widths.forEach((w, idx) => {
            if (!w) return;
            // Ensure pixel values
            if (/^\d+(px)?$/.test(w)) cols[idx].style.width = w.endsWith('px') ? w : w + 'px';
            else cols[idx].style.width = w;
        });
        // After applying column widths, make the table width equal to the sum of columns
        updateTableWidthFromCols(table);
    }

    function setInitialColWidths(table) {
        try {
            const meta = getHeaderMeta(table);
            if (!meta) return;
            const cols = table.querySelectorAll('colgroup col');
            if (!cols || cols.length === 0) return;

            // Use header cell widths to seed columns (respect rowSpan and colSpan)
            meta.rows.forEach(row => {
                Array.from(row.cells).forEach(cell => {
                    const span = cell.colSpan || 1;
                    if (span !== 1) return;
                    const colIndex = meta.cellMap.get(cell);
                    if (colIndex === undefined) return;
                    let w = null;
                    const attrW = cell.getAttribute('width');
                    if (attrW) {
                        const n = parseFloat(String(attrW).replace(/[^0-9\.]/g, ''));
                        if (!isNaN(n) && n > 0) w = n;
                    }
                    if (w === null) {
                        const styleW = cell.style.width || window.getComputedStyle(cell).width || '';
                        const n = parseFloat(String(styleW).replace(/[^0-9\.]/g, ''));
                        if (!isNaN(n) && n > 0) w = n;
                    }
                    if (w === null) w = Math.max(80, Math.round(cell.getBoundingClientRect().width));
                    if (cols[colIndex] && !cols[colIndex].style.width) cols[colIndex].style.width = Math.round(w) + 'px';
                });
            });

            updateTableWidthFromCols(table);
        } catch (e) {
            console.error('setInitialColWidths error', e);
        }
    }

    function updateTableWidthFromCols(table) {
        try {
            const cols = table.querySelectorAll('colgroup col');
            let total = 0;
            cols.forEach(c => {
                let w = c.style.width || window.getComputedStyle(c).width || '0px';
                // Extract numeric part
                const n = parseFloat(String(w).replace(/[^0-9\.]/g, ''));
                if (!isNaN(n)) total += n;
            });
            // Set explicit table width to prevent browser from shrinking other columns
            const px = Math.max(20, Math.round(total)) + 'px';
            table.style.width = px;
            table.style.minWidth = px;
            table.style.maxWidth = 'none';
        } catch (e) {
            console.error('updateTableWidthFromCols error', e);
        }
    }

    function autoSizeColumn(table, colIndex) {
        const rows = Array.from(table.rows);
        let maxWidth = 0;
        rows.forEach(row => {
            const cell = row.cells[colIndex];
            if (!cell) return;
            const input = cell.querySelector('input, select');
            let text = '';
            if (input) text = input.value || input.placeholder || cell.innerText || '';
            else text = cell.innerText || '';

            const temp = document.createElement('div');
            temp.style.cssText = 'position:absolute; visibility:hidden; white-space:nowrap; font-size:0.9rem; padding:0 10px;';
            temp.innerText = text;
            document.body.appendChild(temp);
            const w = temp.offsetWidth;
            if (w > maxWidth) maxWidth = w;
            document.body.removeChild(temp);
        });
        const final = Math.max(40, maxWidth + 20);
        const col = table.querySelectorAll('colgroup col')[colIndex];
        if (col) {
            col.style.width = final + 'px';
            updateTableWidthFromCols(table);
        }
        saveWidths(table);
    }

    function initResizerForTable(table) {
        // Skip if already initialized
        if (table.dataset.resizerInitialized) return;



        // Skip tables marked with no-auto-resize
        if (table.classList.contains('no-auto-resize')) {
            console.log('[HRTableResizer] Skipping no-auto-resize table:', table);
            return;
        }

        // Skip layout tables (table-borderless) to prevent text stacking in headers/info sections
        if (table.classList.contains('table-borderless')) {
            console.log('[HRTableResizer] Skipping table-borderless:', table);
            return;
        }
        table.dataset.resizerInitialized = '1';
        // Also mark as data attribute for easy query
        table.setAttribute('data-resizer-initialized', '1');

        // Debug: mark and show badge and console log
        try {
            console.log('[HRTableResizer] initResizerForTable for', table);
            const wrapper = table.closest('.table-responsive') || table.parentNode || table;
            if (wrapper) {
                let badge = wrapper.querySelector('.hr-resizer-badge');
                const badgeParent = wrapper || table.parentNode || table;
                if (!badge) {
                    badge = document.createElement('div');
                    badge.className = 'hr-resizer-badge';
                    badge.style.cssText = 'position:absolute; top:4px; right:4px; z-index:2147483647; background:#198754; color:#fff; padding:2px 6px; font-size:11px; border-radius:4px; pointer-events:none;';
                    badge.textContent = 'Resizer OK';
                    try { badgeParent.style.position = badgeParent.style.position || 'relative'; } catch (e) { }
                    try { badgeParent.appendChild(badge); } catch (e) { /* ignore append error */ }
                } else {
                    badge.textContent = 'Resizer OK';
                    badge.style.background = '#198754';
                }
            }
        } catch (e) { console.error('Badge error', e); }

        // Use a colgroup to control independent widths
        const colgroup = createColGroupIfMissing(table);
        if (!colgroup) return;
        const headerMeta = getHeaderMeta(table);
        if (!headerMeta) return;

        // Use fixed layout and auto width to avoid browser reflow shrinking neighbouring columns.
        // This makes each column independent and enables horizontal scrolling when total width exceeds container.
        table.style.tableLayout = 'fixed';

        // Restore widths if any (local first)
        const stored = loadWidths(table);
        if (stored) {
            applyWidths(table, stored);
            // Fill any missing widths (esp. when col count changes)
            setInitialColWidths(table);
        } else {
            // Lock initial widths so expanding a column doesn't shrink others
            setInitialColWidths(table);
        }

        // Explicitly set table width from sum of columns to prevent shrinkage
        updateTableWidthFromCols(table);

        // Then try to fetch server-side stored widths (override local if present)
        (function (t) {
            try {
                const tableKey = getTableIdentifier(t);
                fetch(`/settings/table_widths?page=${encodeURIComponent(location.pathname)}&table_key=${encodeURIComponent(tableKey)}`, { credentials: 'same-origin' })
                    .then(res => res.json())
                    .then(data => {
                        if (data && data.success && Array.isArray(data.widths) && data.widths.length > 0) {
                            applyWidths(t, data.widths);
                            // Also mirror to localStorage for quick access
                            const key = getKey(t);
                            try { writeStoredValue(key, JSON.stringify(data.widths)); } catch (e) { }
                        }
                    }).catch(err => { /* ignore */ });
            } catch (e) { }
        })(table);

        const isRTL = (window.getComputedStyle(table).direction || '').toLowerCase() === 'rtl';

        // Add resizer handles and lock buttons to the last header row's THs
        const lastRow = headerMeta.lastRow;
        Array.from(lastRow.cells).forEach((th) => {
            const colIndex = headerMeta.cellMap.get(th);
            if (colIndex === undefined) return;
            // Ensure relative positioning
            th.style.position = th.style.position || 'relative';

            // Lock button
            const lock = document.createElement('button');
            lock.type = 'button';
            lock.className = 'btn btn-link btn-sm col-lock';
            lock.innerHTML = '<i class="fas fa-lock-open"></i>';
            lock.style.cssText = 'position:absolute; left:4px; top:4px; z-index:1040; padding:4px; display:flex; align-items:center;';
            lock.title = 'قفل/إلغاء قفل هذا العمود';
            th.appendChild(lock);

            // Resizer handle on the right
            const handle = document.createElement('div');
            handle.className = 'col-resizer';
            handle.style.cssText = 'position:absolute; top:0; width:7px; cursor:col-resize; user-select:none; height:100%;';
            if (isRTL) {
                handle.style.left = '0';
                handle.style.right = 'auto';
                lock.style.left = 'auto';
                lock.style.right = '4px';
            } else {
                handle.style.right = '0';
                handle.style.left = 'auto';
            }
            th.appendChild(handle);

            let startX, startWidth;
            const cols = table.querySelectorAll('colgroup col');
            let col = cols[colIndex];

            // Toggle lock on click
            lock.addEventListener('click', function (e) {
                e.preventDefault();
                const isLocked = col.getAttribute('data-locked') === '1';
                if (isLocked) {
                    col.removeAttribute('data-locked');
                    lock.innerHTML = '<i class="fas fa-lock-open"></i>';
                } else {
                    col.setAttribute('data-locked', '1');
                    lock.innerHTML = '<i class="fas fa-lock"></i>';
                }
                // Visual feedback: change handle cursor
                handle.style.cursor = col.getAttribute('data-locked') ? 'not-allowed' : 'col-resize';
            });

            handle.addEventListener('mousedown', function (e) {
                // Prevent resizing if column is locked
                if (col.getAttribute('data-locked') === '1') return;
                e.preventDefault();
                startX = e.clientX;
                startWidth = col.getBoundingClientRect().width;

                function mouseMove(ev) {
                    const delta = ev.clientX - startX;
                    const newWidth = Math.max(80, startWidth + (isRTL ? -delta : delta));
                    col.style.width = newWidth + 'px';
                    updateTableWidthFromCols(table);
                }

                function mouseUp() {
                    document.removeEventListener('mousemove', mouseMove);
                    document.removeEventListener('mouseup', mouseUp);
                    // Ensure table width matches sum of column widths before saving
                    updateTableWidthFromCols(table);
                    saveWidths(table);
                }

                document.addEventListener('mousemove', mouseMove);
                document.addEventListener('mouseup', mouseUp);
            });

            // Double click to auto-size
            handle.addEventListener('dblclick', function (e) {
                e.stopPropagation();
                if (col.getAttribute('data-locked') === '1') return;
                autoSizeColumn(table, colIndex);
            });

            // Accessibility: allow keyboard Enter to autosize when focused (skip if locked)
            handle.tabIndex = 0;
            handle.addEventListener('keydown', function (e) {
                if (e.key === 'Enter') {
                    if (col.getAttribute('data-locked') === '1') return;
                    autoSizeColumn(table, colIndex);
                }
            });
        });

        // Reapply stored widths when window resizes (debounced)
        let resizeTimer;
        window.addEventListener('resize', function () {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(function () {
                const s = loadWidths(table);
                if (s) applyWidths(table, s);
            }, 200);
        });

        // Setup ResizeObserver on header cells to synchronize column widths and prevent browser redistribution
        try {
            const roTargets = Array.from(lastRow.cells);
            let roTimer = null;
            const ro = new ResizeObserver(entries => {
                // debounce
                clearTimeout(roTimer);
                roTimer = setTimeout(() => {
                    try {
                        entries.forEach(ent => {
                            const th = ent.target;
                            const colIndex = headerMeta.cellMap.get(th);
                            if (colIndex === undefined) return;
                            const cols = table.querySelectorAll('colgroup col');
                            const col = cols[colIndex];
                            if (!col) return;
                            // if column is locked, respect current value
                            if (col.getAttribute('data-locked') === '1') return;
                            const w = Math.max(30, th.getBoundingClientRect().width);
                            col.style.width = Math.round(w) + 'px';
                        });
                        // After updating columns, fix table width and save
                        updateTableWidthFromCols(table);
                        saveWidths(table);
                    } catch (e) { console.error('ResizeObserver handler error', e); }
                }, 50);
            });
            roTargets.forEach(t => ro.observe(t));
            // store observer reference to disconnect later if needed
            table._colResizeObserver = ro;
        } catch (e) { /* ignore */ }

        // When table content changes (e.g., reloaded), reapply widths and reinit colgroup
        const observer = new MutationObserver(function (mutations) {
            // Ensure colgroup columns match actual header columns
            createColGroupIfMissing(table);
            const s = loadWidths(table);
            if (s) applyWidths(table, s);

            // If header cells were replaced, reinitialize handles (safe reinit)
            // Clear initialized flag and re-run initResizerForTable so handles and observers are present
            try {
                table.dataset.resizerInitialized = '';
                initResizerForTable(table);
            } catch (e) { /* ignore */ }
        });
        observer.observe(table, { childList: true, subtree: true });

        // Add a small reset button (per-table) to allow user to clear saved widths and a lock/unlock-all button
        try {
            const wrapper = table.closest('.table-responsive') || table.parentNode;
            if (wrapper && !wrapper.querySelector('.hr-resizer-reset')) {
                const btn = document.createElement('button');
                btn.className = 'btn btn-sm btn-outline-secondary hr-resizer-reset';
                btn.style.cssText = 'position:absolute; top:8px; left:8px; z-index:1050; padding:4px 8px;';
                btn.title = 'إعادة ضبط أعمدة الجدول';
                btn.innerHTML = '<i class="fas fa-undo"></i>';
                btn.addEventListener('click', function (ev) {
                    ev.preventDefault();
                    window.HRTableResizer.resetForTable(table);
                    // Also remove server-side setting if possible by calling API (best effort)
                    try {
                        const csrf = document.querySelector('meta[name="csrf-token"]') ? document.querySelector('meta[name="csrf-token"]').getAttribute('content') : null;
                        const payload = { page: location.pathname, table_key: getTableIdentifier(table), widths: [] };
                        fetch('/settings/table_widths', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf }, body: JSON.stringify(payload), credentials: 'same-origin' })
                            .then(() => { }).catch(() => { });
                    } catch (e) { }
                    // Visual confirmation
                    const notice = document.createElement('div');
                    notice.className = 'alert alert-success small';
                    notice.textContent = 'تم إعادة ضبط أعمدة الجدول';
                    notice.style.cssText = 'position:fixed; left:8px; bottom:8px; z-index:1200;';
                    document.body.appendChild(notice);
                    setTimeout(() => notice.remove(), 2000);
                });
                wrapper.style.position = wrapper.style.position || 'relative';
                wrapper.appendChild(btn);

                // Lock/Unlock all button
                const lockAll = document.createElement('button');
                lockAll.className = 'btn btn-sm btn-outline-primary hr-resizer-lockall';
                lockAll.style.cssText = 'position:absolute; top:8px; left:56px; z-index:1050; padding:4px 8px;';
                lockAll.title = 'قفل/إلغاء قفل كل الأعمدة';
                lockAll.innerHTML = '<i class="fas fa-lock-open"></i>';
                lockAll.addEventListener('click', function (ev) {
                    ev.preventDefault();
                    const cols = table.querySelectorAll('colgroup col');
                    const locks = table.querySelectorAll('.col-lock');
                    // Decide: if any unlocked => lock all, else unlock all
                    const anyUnlocked = Array.from(cols).some(c => c.getAttribute('data-locked') !== '1');
                    cols.forEach((c, i) => {
                        const l = locks[i];
                        if (anyUnlocked) {
                            c.setAttribute('data-locked', '1');
                            if (l) l.innerHTML = '<i class="fas fa-lock"></i>';
                        } else {
                            c.removeAttribute('data-locked');
                            if (l) l.innerHTML = '<i class="fas fa-lock-open"></i>';
                        }
                    });
                    lockAll.innerHTML = anyUnlocked ? '<i class="fas fa-lock"></i>' : '<i class="fas fa-lock-open"></i>';
                });
                wrapper.appendChild(lockAll);
            }
        } catch (e) { /* ignore */ }
    }

    function initAll() {
        // Target common table containers: responsive wrappers, DataTables, plain tables
        const selector = '.table-responsive table, table.table, table.dataTable, table';
        try { console.log('[HRTableResizer] initAll selector', selector, 'found', document.querySelectorAll(selector).length); } catch (e) { }
        const tables = document.querySelectorAll(selector);
        Array.from(tables).forEach((t) => initResizerForTable(t));

        // Global debug panel indicating initialized tables
        try {
            if (!document.querySelector('.hr-resizer-global')) {
                const panel = document.createElement('div');
                panel.className = 'hr-resizer-global';
                panel.style.cssText = 'position:fixed; bottom:12px; right:12px; z-index:1300; background:#000; color:#fff; padding:8px 10px; border-radius:6px; font-size:12px; opacity:0.9;';
                panel.innerHTML = `<span id="hr-resizer-count">${document.querySelectorAll('table[data-resizer-initialized]').length}</span> جدول مفعل&nbsp;` +
                    `<button id="hr-resizer-refresh" style="margin-left:8px;" class="btn btn-sm btn-light">تحديث</button>`;
                document.body.appendChild(panel);
                document.getElementById('hr-resizer-refresh').addEventListener('click', () => {
                    document.getElementById('hr-resizer-count').textContent = document.querySelectorAll('table[data-resizer-initialized]').length;
                });
            } else {
                const el = document.getElementById('hr-resizer-count'); if (el) el.textContent = document.querySelectorAll('table[data-resizer-initialized]').length;
            }
        } catch (e) { /* ignore */ }

        // Observe the document for newly inserted tables (e.g., loaded by DataTables) and init them
        if (!window._hr_table_global_observer) {
            const docObserver = new MutationObserver(mutations => {
                mutations.forEach(m => {
                    Array.from(m.addedNodes || []).forEach(node => {
                        try {
                            if (node.nodeType !== 1) return;
                            if (node.matches && (node.matches('table') || node.querySelector && node.querySelector('table'))) {
                                const found = node.matches('table') ? [node] : Array.from(node.querySelectorAll('table'));
                                found.forEach(t => { if (!t.dataset.resizerInitialized) initResizerForTable(t); });
                            }
                        } catch (e) { /* ignore */ }
                    });
                });
            });
            docObserver.observe(document.body, { childList: true, subtree: true });
            window._hr_table_global_observer = docObserver;
        }
    }

    // Provide a public API to reset widths for the current page/table and autosize
    window.HRTableResizer = {
        resetForTable: function (table) {
            try {
                const key = getKey(table);
                removeStoredValue(key);
                // Remove inline widths
                table.querySelectorAll('colgroup col').forEach(c => c.style.width = '');
            } catch (e) { console.error(e); }
        },
        resetAll: function () {
            try {
                listStoredKeysByPrefix(STORAGE_PREFIX).forEach(k => { if (k.indexOf(STORAGE_PREFIX) === 0) removeStoredValue(k); });
                // Remove inline widths on all tables
                document.querySelectorAll('colgroup col').forEach(c => c.style.width = '');
            } catch (e) { console.error(e); }
        },
        autoSize: function (table, colIndex) {
            try { autoSizeColumn(table, colIndex); } catch (e) { console.error(e); }
        }
    };

    // If user presses Enter while focused inside an input/select inside a table, auto-size that column (non-intrusive)
    document.addEventListener('keydown', function (e) {
        if (e.key !== 'Enter') return;
        const target = e.target;
        if (!target) return;
        if (!(target.tagName === 'INPUT' || target.tagName === 'SELECT' || target.tagName === 'TEXTAREA')) return;
        const td = target.closest('td');
        const table = target.closest('table');
        if (!td || !table) return;
        const colIndex = td.cellIndex;
        // Defer so existing Enter handlers (like navigation) run first
        setTimeout(() => {
            try {
                window.HRTableResizer.autoSize(table, colIndex);
            } catch (err) { console.error(err); }
        }, 10);
    });

    // Init when DOM is ready
    document.addEventListener('DOMContentLoaded', initAll);
})();
