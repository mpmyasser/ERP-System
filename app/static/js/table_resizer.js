/*
* Table Resizer Logic (Vanilla JS) - Fixed Version
* Adds draggable handles to table headers for resizing columns.
* Supports RTL (Right-to-Left) layout where resizing happens from the left edge of the column.
* Uses table-layout: fixed to prevent columns from affecting each other during resize.
* Persists widths through centralized SettingsManager.
*/

document.addEventListener('DOMContentLoaded', function () {
    const DEFAULT_MIN_COLUMN_WIDTH = 30;
    const TABLE_SELECTOR = '.table-responsive table, table.table, table.datatable, table.dataTable';
    const DATATABLE_REFRESH_DELAY = 180;

    initializeTables();

    if (window.jQuery) {
        $(document).on('init.dt.hrResizer draw.dt.hrResizer column-reorder.dt.hrResizer column-visibility.dt.hrResizer responsive-resize.dt.hrResizer', function (event, settings) {
            const table = resolveTableFromEvent(event, settings);
            if (table) {
                queueDataTableRefresh(table);
            }
        });
    }

    window.addEventListener('load', function () {
        document.querySelectorAll('table.datatable, table.dataTable').forEach(function (table) {
            queueDataTableRefresh(table, DATATABLE_REFRESH_DELAY);
        });
    });

    function initializeTables() {
        const tables = document.querySelectorAll(TABLE_SELECTOR);

        tables.forEach(function (table) {
            if (isDataTableManaged(table)) {
                queueDataTableRefresh(table, DATATABLE_REFRESH_DELAY);
                return;
            }

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

    function resolveTableFromEvent(event, settings) {
        if (settings && settings.nTable) {
            return settings.nTable;
        }

        if (event && event.target && event.target.tagName === 'TABLE') {
            return event.target;
        }

        return null;
    }

    function isDataTableManaged(table) {
        if (!table) return false;

        if (table.classList.contains('datatable') || table.classList.contains('dataTable') || table.closest('.dataTables_wrapper')) {
            return true;
        }

        return !!(window.jQuery && $.fn && $.fn.DataTable && $.fn.DataTable.isDataTable(table));
    }

    function queueDataTableRefresh(table, delay) {
        if (!table) return;

        const wait = typeof delay === 'number' ? delay : DATATABLE_REFRESH_DELAY;
        clearTimeout(table._hrResizerRefreshTimer);
        table._hrResizerRefreshTimer = setTimeout(function () {
            if (!table.isConnected) return;

            if (!table.dataset.resizerInitialized) {
                createResizableTable(table);
                return;
            }

            restoreSavedWidths(table);
            syncTableWidth(table);
            syncResizerHeights(table);
        }, wait);
    }

    function getTableIdentity(table) {
        if (table.id) {
            return table.id;
        }

        if (!table.dataset.hrTableKey) {
            table.dataset.hrTableKey = 'table-' + Math.random().toString(36).slice(2, 11);
        }

        return table.dataset.hrTableKey;
    }

    function getStorageKey(table) {
        const tableId = getTableIdentity(table);
        const isLoansTable = tableId === 'loans-table' || tableId.startsWith('loans-table-');
        return isLoansTable ? 'table_widths_loans_global' : ('table_widths_' + tableId);
    }

    function restoreSavedWidths(table, cols, storageKey) {
        const targetCols = cols || table.querySelectorAll('thead th');
        if (!targetCols.length) return;

        const savedWidths = getStoredMap(storageKey || getStorageKey(table));

        [].forEach.call(targetCols, function (col) {
            const headerText = col.innerText.trim();

            if (savedWidths[headerText]) {
                col.style.width = savedWidths[headerText];
                col.style.minWidth = savedWidths[headerText];
            } else if (col.getAttribute('width')) {
                const attrWidth = col.getAttribute('width') + 'px';
                col.style.width = attrWidth;
                col.style.minWidth = attrWidth;
            }
        });
    }

    function syncTableWidth(table, cols) {
        const targetCols = cols || table.querySelectorAll('thead th');
        if (!targetCols.length) return;

        let totalWidth = 0;
        [].forEach.call(targetCols, function (col) {
            const width = parseInt(col.style.width, 10) || col.offsetWidth || 100;
            totalWidth += width;
        });

        table.style.width = totalWidth + 'px';
        table.style.minWidth = totalWidth + 'px';
    }

    function syncResizerHeights(table) {
        const height = table.offsetHeight + 'px';
        table.querySelectorAll('thead th .resizer').forEach(function (resizer) {
            resizer.style.height = height;
        });
    }

    function getMinimumColumnWidth(col) {
        const explicitMin = parseInt(col.dataset.minWidth || col.getAttribute('data-min-width'), 10);
        if (!Number.isNaN(explicitMin) && explicitMin > 0) {
            return explicitMin;
        }
        return DEFAULT_MIN_COLUMN_WIDTH;
    }

    function createResizableTable(table) {
        // Skip specific types
        if (table.classList.contains('no-auto-resize') || table.classList.contains('table-borderless')) {
            return;
        }
        if (table.dataset.resizerInitialized === '1') {
            restoreSavedWidths(table);
            syncTableWidth(table);
            syncResizerHeights(table);
            return;
        }

        const cols = table.querySelectorAll('thead th');
        if (!cols.length) {
            return;
        }

        table.style.tableLayout = 'fixed';
        table.dataset.resizerInitialized = '1';

        // Use a generic key for loans related tables to share widths if possible
        const storageKey = getStorageKey(table);

        restoreSavedWidths(table, cols, storageKey);

        [].forEach.call(cols, function (col) {
            // Add a resizer element to the column
            if (col.querySelector('.resizer')) {
                return;
            }

            const headerText = col.innerText.trim();
            const resizer = document.createElement('div');
            resizer.classList.add('resizer');
            resizer.style.height = `${table.offsetHeight}px`;
            col.appendChild(resizer);

            createResizableColumn(col, resizer, storageKey, headerText, table);
        });

        syncTableWidth(table, cols);
    }

    function createResizableColumn(col, resizer, storageKey, headerText, table) {
        let x = 0;
        let w = 0;

        const mouseDownHandler = function (e) {
            x = e.clientX;
            const styles = window.getComputedStyle(col);
            w = parseInt(styles.width, 10);

            // Add active resizing class
            resizer.classList.add('resizing');
            table.classList.add('is-resizing');

            // Prevent text selection during resize
            document.body.style.userSelect = 'none';
            document.body.style.cursor = 'col-resize';

            document.addEventListener('mousemove', mouseMoveHandler);
            document.addEventListener('mouseup', mouseUpHandler);
            e.preventDefault();
            e.stopPropagation();
        };

        const mouseMoveHandler = function (e) {
            const dx = e.clientX - x;
            const isRTL = document.dir === 'rtl' || document.documentElement.dir === 'rtl';

            // Calculate new width with minimum constraint
            let newWidth = isRTL ? (w - dx) : (w + dx);

            // Respect the real per-column minimum instead of a hard lock at 80px
            const minWidth = getMinimumColumnWidth(col);
            if (newWidth < minWidth) {
                newWidth = minWidth;
            }

            // Calculate the delta width change
            const deltaWidth = newWidth - w;

            // Apply the new width directly to the column
            col.style.width = `${newWidth}px`;
            col.style.minWidth = `${newWidth}px`;

            // Increase table width by the same delta to prevent other columns from shrinking
            const currentTableWidth = parseInt(table.style.width, 10) || table.offsetWidth;
            table.style.width = `${currentTableWidth + deltaWidth}px`;
            table.style.minWidth = `${currentTableWidth + deltaWidth}px`;

            // Update w to track current width for next move
            w = newWidth;
            x = e.clientX;

            e.preventDefault();
        };

        const mouseUpHandler = function () {
            resizer.classList.remove('resizing');
            table.classList.remove('is-resizing');

            // Restore text selection and cursor
            document.body.style.userSelect = '';
            document.body.style.cursor = '';

            document.removeEventListener('mousemove', mouseMoveHandler);
            document.removeEventListener('mouseup', mouseUpHandler);

            // Save width by header text
            const savedWidths = getStoredMap(storageKey);
            savedWidths[headerText] = col.style.width;
            setStoredMap(storageKey, savedWidths);

            // Trigger sync across all tables with the same category
            try {
                if (storageKey === 'table_widths_loans_global') {
                    applyGlobalWidths(storageKey);
                }
            } catch (e) { /* ignore */ }
        };

        resizer.addEventListener('mousedown', mouseDownHandler);
    }

    // Function to force update all similar tables on the page
    function applyGlobalWidths(key) {
        const savedWidths = getStoredMap(key);
        document.querySelectorAll('table').forEach(table => {
            const currentTableId = table.id || '';
            if (currentTableId === 'loans-table' || currentTableId.startsWith('loans-table-')) {
                table.querySelectorAll('th').forEach(th => {
                    const text = th.innerText.trim();
                    if (savedWidths[text]) {
                        th.style.width = savedWidths[text];
                        th.style.minWidth = savedWidths[text];
                    }
                });
                syncTableWidth(table);
                syncResizerHeights(table);
            }
        });
    }

    // Expose autoSize function for external use (for Enter key functionality)
    window.HRTableResizer = {
        autoSize: function (table, columnIndex) {
            const headers = table.querySelectorAll('thead th');
            const rows = table.querySelectorAll('tbody tr');

            if (!headers[columnIndex]) return;

            const header = headers[columnIndex];
            const headerText = header.innerText.trim();

            // Find max content width in this column
            let maxWidth = header.scrollWidth;

            rows.forEach(row => {
                const cell = row.cells[columnIndex];
                if (cell) {
                    const input = cell.querySelector('input, select');
                    if (input) {
                        // For inputs, use scrollWidth + padding
                        maxWidth = Math.max(maxWidth, input.scrollWidth + 40);
                    } else {
                        maxWidth = Math.max(maxWidth, cell.scrollWidth);
                    }
                }
            });

            // Add some padding
            maxWidth += 20;

            // Calculate old width and delta
            const oldWidth = parseInt(header.style.width, 10) || header.offsetWidth;
            const deltaWidth = maxWidth - oldWidth;

            // Apply the width
            header.style.width = `${maxWidth}px`;
            header.style.minWidth = `${maxWidth}px`;

            // Increase table width by delta
            const currentTableWidth = parseInt(table.style.width, 10) || table.offsetWidth;
            table.style.width = `${currentTableWidth + deltaWidth}px`;
            table.style.minWidth = `${currentTableWidth + deltaWidth}px`;

            // Save to centralized storage
            const storageKey = getStorageKey(table);
            const savedWidths = getStoredMap(storageKey);
            savedWidths[headerText] = header.style.width;
            setStoredMap(storageKey, savedWidths);
        }
    };
});
