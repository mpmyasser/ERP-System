/*
* Table Resizer Logic (Vanilla JS) - Fixed Version
* Adds draggable handles to table headers for resizing columns.
* Supports RTL (Right-to-Left) layout where resizing happens from the left edge of the column.
* Uses table-layout: fixed to prevent columns from affecting each other during resize.
* Persists widths through centralized SettingsManager.
*/

document.addEventListener('DOMContentLoaded', function () {
    const tables = document.querySelectorAll('table');

    tables.forEach(function (table) {
        createResizableTable(table);
    });

    function getStoredMap(key) {
        if (!window.HRSettingsUtil) return {};
        return window.HRSettingsUtil.getObject(key, {});
    }

    function setStoredMap(key, value) {
        if (!window.HRSettingsUtil) return;
        window.HRSettingsUtil.setObject(key, value);
    }

    function createResizableTable(table) {
        // Skip specific types
        if (table.classList.contains('no-auto-resize') || table.classList.contains('table-borderless')) {
            return;
        }
        table.style.tableLayout = 'fixed';

        const tableId = table.id || 'table-' + Math.random().toString(36).substr(2, 9);
        const cols = table.querySelectorAll('thead th');

        // Use a generic key for loans related tables to share widths if possible
        const isLoansTable = tableId === 'loans-table' || tableId.startsWith('loans-table-');
        const storageKey = isLoansTable ? 'table_widths_loans_global' : ('table_widths_' + tableId);

        // Load saved widths (keyed by header text for cross-table compatibility)
        const savedWidths = getStoredMap(storageKey);

        [].forEach.call(cols, function (col) {
            const headerText = col.innerText.trim();

            // Restore saved width if exists for this header text
            if (savedWidths[headerText]) {
                col.style.width = savedWidths[headerText];
                col.style.minWidth = savedWidths[headerText];
            } else if (col.getAttribute('width')) {
                // Use the width attribute if specified
                const attrWidth = col.getAttribute('width') + 'px';
                col.style.width = attrWidth;
                col.style.minWidth = attrWidth;
            }

            // Add a resizer element to the column
            const resizer = document.createElement('div');
            resizer.classList.add('resizer');
            resizer.style.height = `${table.offsetHeight}px`;
            col.appendChild(resizer);

            createResizableColumn(col, resizer, storageKey, headerText, table);
        });

        // Calculate and set initial table width from columns
        let totalWidth = 0;
        cols.forEach(col => {
            const w = parseInt(col.style.width, 10) || col.offsetWidth || 100;
            totalWidth += w;
        });
        table.style.width = totalWidth + 'px';
        table.style.minWidth = totalWidth + 'px';
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

            // Set minimum width to prevent column from becoming too small
            const minWidth = 80;
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
            const tableId = table.id || 'table-' + Math.random().toString(36).substr(2, 9);
            const isLoansTable = tableId === 'loans-table' || tableId.startsWith('loans-table-');
            const storageKey = isLoansTable ? 'table_widths_loans_global' : ('table_widths_' + tableId);

            const savedWidths = getStoredMap(storageKey);
            savedWidths[headerText] = header.style.width;
            setStoredMap(storageKey, savedWidths);
        }
    };
});
