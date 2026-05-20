/*
* Table Resizer Logic (Vanilla JS) - Unified & Fixed Version
*/
document.addEventListener('DOMContentLoaded', function () {
    const DEFAULT_MIN_COLUMN_WIDTH = 30;
    const TABLE_SELECTOR = '.table-responsive table, table.table, table.datatable, table.dataTable';
    const DATATABLE_REFRESH_DELAY = 180;

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
            createResizableTable(table);
        });
    }

    function getStoredMap(key) {
        if (!window.HRSettingsUtil) return {};
        return window.HRSettingsUtil.getObject(key, {});
    }

    function setStoredMap(key, value) {
        if (!window.HRSettingsUtil) return;
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
            total += parseInt(col.style.width, 10) || col.offsetWidth || 100;
        });
        table.style.width = total + 'px';
        table.style.minWidth = total + 'px';
    }

    function syncResizerHeights(table) {
        const h = Math.max(table.offsetHeight, table.scrollHeight, 40) + 'px';
        table.querySelectorAll('.resizer').forEach(r => r.style.height = h);
    }

    function getMinimumColumnWidth(col) {
        return parseInt(col.dataset.minWidth || col.getAttribute('data-min-width'), 10) || DEFAULT_MIN_COLUMN_WIDTH;
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

        cols.forEach(col => {
            const headerText = col.innerText.trim();
            if (savedWidths[headerText]) {
                col.style.width = savedWidths[headerText];
                col.style.minWidth = savedWidths[headerText];
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
        let x = 0, w = 0, frame = null, latestClientX = 0;

        const onMouseDown = (e) => {
            x = e.clientX;
            latestClientX = e.clientX;
            w = parseInt(window.getComputedStyle(col).width, 10);
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
                    const min = getMinimumColumnWidth(col);
                    if (nw < min) nw = min;

                    const delta = nw - w;
                    col.style.width = nw + 'px';
                    col.style.minWidth = nw + 'px';

                    const tw = parseInt(table.style.width, 10) || table.offsetWidth;
                    table.style.width = (tw + delta) + 'px';
                    table.style.minWidth = (tw + delta) + 'px';

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
