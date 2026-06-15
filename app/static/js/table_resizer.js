/*
* Table Resizer Logic (Vanilla JS) - Unified & Fixed Version
*/
document.addEventListener('DOMContentLoaded', function () {
    const DEFAULT_MIN_COLUMN_WIDTH = 30;
    const TABLE_SELECTOR = '.table-responsive table, table.table, table.datatable, table.dataTable';
    const DATATABLE_REFRESH_DELAY = 180;

    // احفظ جميع الجداول المهيأة لإعادة التحقق منها
    const initializedTables = new Set();

    initializeTables();

    // Re-init on window resize
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            document.querySelectorAll(TABLE_SELECTOR).forEach(table => {
                if (table.dataset.resizerInitialized) {
                    syncTableWidth(table);
                    syncResizerHeights(table);
                }
            });
        }, 150);
    });

    if (window.jQuery) {
        $(document).on('init.dt draw.dt column-reorder.dt column-visibility.dt responsive-resize.dt', function (e, settings) {
            const table = settings?.nTable || (e.target.tagName === 'TABLE' ? e.target : null);
            if (table) queueDataTableRefresh(table);
        });
    }

    function initializeTables() {
        document.querySelectorAll(TABLE_SELECTOR).forEach(table => {
            if (table.classList.contains('no-auto-resize') || table.classList.contains('table-borderless')) return;
            const tableId = table.id || table.dataset.hrTableKey;
            if (!initializedTables.has(tableId)) {
                createResizableTable(table);
                initializedTables.add(tableId);
            }
        });
    }

    function getStoredMap(key) {
        if (!window.HRSettingsUtil) {
            // fallback إلى localStorage مباشرة إذا لم يكن HRSettingsUtil متاحاً
            try {
                return JSON.parse(localStorage.getItem(key) || '{}');
            } catch {
                return {};
            }
        }
        return window.HRSettingsUtil.getObject(key, {});
    }

    function setStoredMap(key, value) {
        if (!window.HRSettingsUtil) {
            // fallback إلى localStorage مباشرة
            try {
                localStorage.setItem(key, JSON.stringify(value));
            } catch {
                return;
            }
            return;
        }
        window.HRSettingsUtil.setObject(key, value);
    }

    function queueDataTableRefresh(table) {
        clearTimeout(table._hrResizerTimer);
        table._hrResizerTimer = setTimeout(() => {
            if (!table.isConnected) return;
            if (!table.dataset.resizerInitialized) {
                createResizableTable(table);
            } else {
                syncTableWidth(table);
                syncResizerHeights(table);
            }
        }, DATATABLE_REFRESH_DELAY);
    }

    function getStorageKey(table) {
        const id = table.id || table.dataset.hrTableKey || (table.dataset.hrTableKey = 'table-' + Math.random().toString(36).slice(2, 7));
        return (id === 'loans-table' || id.startsWith('loans-table-')) ? 'table_widths_loans_global' : ('table_widths_' + id);
    }

    function syncTableWidth(table) {
        const cols = table.querySelectorAll('thead th');
        if (!cols.length) return;
        
        let total = 0;
        cols.forEach(col => {
            total += getColumnPixelWidth(col);
        });
        table.style.width = total + 'px';
        table.style.minWidth = total + 'px';
    }

    function syncResizerHeights(table) {
        const h = Math.max(table.offsetHeight, table.scrollHeight, 40) + 'px';
        table.querySelectorAll('.resizer').forEach(r => r.style.height = h);
    }

    function getMinimumColumnWidth(col, isResizing = false) {
        // عند السحب للتضيق، نستخدم حد أدنى بناءً على محتوى الخلايا فقط
        if (isResizing) {
            return calculateContentBasedMinWidth(col);
        }

        const explicitMin = parseInt(col.dataset.minWidth || col.getAttribute('data-min-width'), 10);
        if (explicitMin) return explicitMin;

        const baseMin = parseInt(col.dataset.resizerBaseMinWidth, 10);
        if (baseMin) return baseMin;

        const computedMin = parseInt(window.getComputedStyle(col).minWidth, 10);
        return computedMin || DEFAULT_MIN_COLUMN_WIDTH;
    }

    function calculateContentBasedMinWidth(col) {
        const table = col.closest('table');
        if (!table) return DEFAULT_MIN_COLUMN_WIDTH;

        const colIndex = Array.from(col.parentElement.children).indexOf(col);
        let maxContentWidth = 0;

        // حساب أعرض محتوى في العمود من الصفوف فقط (بدون الرأس)
        table.querySelectorAll('tbody tr').forEach(row => {
            const cell = row.cells[colIndex];
            if (cell) {
                const textContent = cell.innerText.trim();
                if (textContent) {
                    // استخدام offsetWidth الفعلي للخلية بدون قيود
                    const tempStyle = window.getComputedStyle(cell);
                    const fontSize = tempStyle.fontSize;
                    const fontFamily = tempStyle.fontFamily;
                    const fontWeight = tempStyle.fontWeight;

                    const canvas = document.createElement('canvas');
                    const ctx = canvas.getContext('2d');
                    ctx.font = `${fontWeight} ${fontSize} ${fontFamily}`;
                    const textWidth = ctx.measureText(textContent).width;

                    // إضافة padding بدون أي مساحة إضافية
                    const paddingLR = 2; // minimal padding
                    const borderLR = 0;

                    maxContentWidth = Math.max(maxContentWidth, textWidth + paddingLR + borderLR);
                }
            }
        });

        // أيضاً حساب الرأس
        const headerText = col.innerText.trim();
        if (headerText) {
            const tempStyle = window.getComputedStyle(col);
            const fontSize = tempStyle.fontSize;
            const fontFamily = tempStyle.fontFamily;
            const fontWeight = tempStyle.fontWeight;

            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            ctx.font = `${fontWeight} ${fontSize} ${fontFamily}`;
            const textWidth = ctx.measureText(headerText).width;

            const paddingLR = 2; // minimal padding
            const borderLR = 0;

            maxContentWidth = Math.max(maxContentWidth, textWidth + paddingLR + borderLR);
        }

        // حد أدنى معقول جداً (8px فقط للحروف الصغيرة جداً)
        return Math.max(maxContentWidth, 8);
    }

    function getColumnPixelWidth(col) {
        const inlineWidth = (col.style.width || '').trim();
        if (inlineWidth.endsWith('px')) {
            const px = parseFloat(inlineWidth);
            if (px > 0) return px;
        }

        const measured = col.getBoundingClientRect().width || col.offsetWidth;
        return Math.max(measured || 100, getMinimumColumnWidth(col));
    }

    function getTableColumnElement(table, index) {
        const tableColumns = table.querySelectorAll('colgroup col');
        return tableColumns[index] || null;
    }

    function setColumnWidth(table, col, index, width, minWidth) {
        const safeMin = minWidth || getMinimumColumnWidth(col);
        const safeWidth = Math.max(width, safeMin);
        const pxWidth = safeWidth + 'px';
        const pxMin = safeMin + 'px';
        const tableColumn = getTableColumnElement(table, index);

        col.style.width = pxWidth;
        col.style.minWidth = pxMin;

        if (tableColumn) {
            tableColumn.style.width = pxWidth;
            tableColumn.style.minWidth = pxMin;
        }

        return safeWidth;
    }

    function freezeColumnWidths(table) {
        const cols = Array.from(table.querySelectorAll('thead th'));
        const widths = cols.map(col => {
            // احصل على العرض الفعلي المحفوظ (style.width)
            const inlineWidth = (col.style.width || '').trim();
            if (inlineWidth.endsWith('px')) {
                return parseFloat(inlineWidth);
            }
            // إذا لم يكن هناك عرض محفوظ، استخدم العرض الحالي
            return col.offsetWidth;
        });

        cols.forEach((col, index) => {
            // مرّر العرض بدون فرض حد أدنى - الحفاظ على العرض المضيق بالضبط
            const pxWidth = widths[index] + 'px';
            col.style.width = pxWidth;
            col.style.minWidth = '0px'; // لا تفرض حد أدنى عند التجميد
            const tableColumn = getTableColumnElement(table, index);
            if (tableColumn) {
                tableColumn.style.width = pxWidth;
                tableColumn.style.minWidth = '0px';
            }
        });

        const total = widths.reduce((sum, width) => sum + width, 0);
        table.style.width = total + 'px';
        table.style.minWidth = total + 'px';

        return { cols, widths };
    }

    function createResizableTable(table) {
        if (table.dataset.resizerInitialized === '1') {
            syncTableWidth(table);
            syncResizerHeights(table);
            return;
        }

        const cols = table.querySelectorAll('thead th');
        if (!cols.length) return;

        table.style.tableLayout = 'fixed';
        table.dataset.resizerInitialized = '1';
        const storageKey = getStorageKey(table);
        const savedWidths = getStoredMap(storageKey);

        cols.forEach((col, index) => {
            const headerText = col.innerText.trim();
            const minWidth = getMinimumColumnWidth(col);
            col.dataset.resizerBaseMinWidth = minWidth;
            const savedWidth = savedWidths[headerText];
            const savedPx = typeof savedWidth === 'string' && savedWidth.trim().endsWith('px')
                ? parseFloat(savedWidth)
                : 0;

            // استعادة العرض المحفوظ بدون فرض حد أدنى
            if (savedPx > 0) {
                const pxWidth = savedPx + 'px';
                col.style.width = pxWidth;
                col.style.minWidth = '0px';
                const tableColumn = getTableColumnElement(table, index);
                if (tableColumn) {
                    tableColumn.style.width = pxWidth;
                    tableColumn.style.minWidth = '0px';
                }
            } else if (savedWidth) {
                delete savedWidths[headerText];
            }

            if (!col.querySelector('.resizer')) {
                const resizer = document.createElement('div');
                resizer.className = 'resizer';
                col.appendChild(resizer);
                createResizableColumn(col, resizer, storageKey, headerText, table);
            }
        });

        syncTableWidth(table);
        syncResizerHeights(table);
        setStoredMap(storageKey, savedWidths);

        // Sidebar/Layout shift compatibility: Listen for container size changes
        // Guard against infinite loop: ResizeObserver fires when we change width,
        // which triggers another observation, creating an endless cycle.
        if (window.ResizeObserver) {
            let roTimer = null;
            let lastKnownWidth = table.offsetWidth;
            const ro = new ResizeObserver(() => {
                // Only react if the table width actually changed externally
                // (e.g. sidebar toggle, window resize), not from our own syncTableWidth call
                const currentWidth = table.offsetWidth;
                if (Math.abs(currentWidth - lastKnownWidth) < 2) return;
                lastKnownWidth = currentWidth;
                clearTimeout(roTimer);
                roTimer = setTimeout(() => {
                    syncResizerHeights(table);
                }, 200);
            });
            ro.observe(table);
        }
    }

    function createResizableColumn(col, resizer, storageKey, headerText, table) {
        let x = 0, w = 0, frame = null, latestClientX = 0, activeColumnIndex = -1, frozenWidths = [];

        const onMouseDown = (e) => {
            const frozen = freezeColumnWidths(table);
            activeColumnIndex = frozen.cols.indexOf(col);
            frozenWidths = frozen.widths;
            x = e.clientX;
            latestClientX = e.clientX;
            w = frozenWidths[activeColumnIndex] || getColumnPixelWidth(col);
            resizer.classList.add('resizing');
            table.classList.add('is-resizing');
            document.body.style.userSelect = 'none';
            document.body.style.cursor = 'col-resize';
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
            e.preventDefault();
            e.stopPropagation();
        };

        const onMouseMove = (e) => {
            latestClientX = e.clientX;
            if (!frame) {
                frame = requestAnimationFrame(() => {
                    frame = null;
                    const dx = latestClientX - x;
                    const isRTL = document.dir === 'rtl' || document.documentElement.dir === 'rtl';
                    let nw = isRTL ? (w - dx) : (w + dx);
                    const min = getMinimumColumnWidth(col, true);
                    if (nw < min) nw = min;

                    if (activeColumnIndex < 0) return;

                    frozenWidths[activeColumnIndex] = setColumnWidth(table, col, activeColumnIndex, nw, min);

                    const total = frozenWidths.reduce((sum, width) => sum + width, 0);
                    table.style.width = total + 'px';
                    table.style.minWidth = total + 'px';

                    w = nw;
                    x = latestClientX;
                });
            }
            e.preventDefault();
        };

        const onMouseUp = () => {
            if (frame) {
                cancelAnimationFrame(frame);
                frame = null;
            }
            resizer.classList.remove('resizing');
            table.classList.remove('is-resizing');
            document.body.style.userSelect = '';
            document.body.style.cursor = '';
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);

            const widths = getStoredMap(storageKey);
            widths[headerText] = col.style.width;
            setStoredMap(storageKey, widths);
        };

        resizer.addEventListener('mousedown', onMouseDown);
        resizer.addEventListener('click', e => {
            e.preventDefault();
            e.stopPropagation();
        });
    }

    window.HRTableResizer = {
        init: initializeTables,
        autoSize: function(table, idx) {
            // Placeholder for autoSize if needed
        }
    };
});
