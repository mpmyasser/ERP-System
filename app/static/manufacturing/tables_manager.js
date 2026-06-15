/**
 * tables_manager.js - Global Table Management for Manufacturing Module
 * Handles: Persistent Sorting, Column Reordering (Drag & Drop), and UI State.
 */
window.TablesManager = (() => {
    
    function init() {
        document.querySelectorAll('table').forEach(table => {
            if (table.dataset.managed === 'true') return;
            try {
                setupTable(table);
                table.dataset.managed = 'true';
            } catch (e) {
                console.error("Table Manager Error on:", table.id, e);
            }
        });
    }

    function setupTable(table) {
        const tableId = table.id || 'table_' + Math.random().toString(36).substr(2, 5);
        if (!table.id) table.id = tableId; // Ensure the table has an ID for saving state
        const headers = table.querySelectorAll('thead th');
        
        // 1. Column Reordering Setup
        headers.forEach((th, index) => {
            if (th.classList.contains('no-reorder')) return;
            th.draggable = true;
            th.addEventListener('dragstart', handleDragStart);
            th.addEventListener('dragover', handleDragOver);
            th.addEventListener('drop', e => handleDrop(e, tableId));
            th.addEventListener('dragenter', handleDragEnter);
            th.addEventListener('dragleave', handleDragLeave);
        });

        // 2. Persistent Sorting Setup
        headers.forEach((th, index) => {
            if (th.classList.contains('no-sort') || th.dataset.print === 'no') return;
            th.style.cursor = 'pointer';
            th.addEventListener('click', (e) => {
                if (e.target.classList.contains('resizer') || e.target.tagName.toLowerCase() === 'input') return;
                const currentSort = getSortState(tableId) || {};
                const direction = (currentSort.colIndex === index && currentSort.direction === 'asc') ? 'desc' : 'asc';
                applySort(table, index, direction);
            });
            // Initial sort icon
            if (!th.querySelector('.sort-icon')) {
                const icon = document.createElement('i');
                icon.className = 'fas fa-sort ms-1 text-muted sort-icon small';
                th.appendChild(icon);
            }
        });

        // 3. Load Saved States
        try { loadColumnOrder(table, tableId); } catch(e) {}
        
        // 4. Initial Sort Application & Dynamic Data Observer
        const savedSort = getSortState(tableId);
        if (savedSort) {
            // Apply immediately if data exists
            applySort(table, savedSort.colIndex, savedSort.direction, false);
            
            // Watch for dynamic data loads (like AJAX fetch in cuts_entry.html)
            const tbody = table.querySelector('tbody');
            if (tbody) {
                const observer = new MutationObserver((mutations) => {
                    if (table._hrTableManagerSorting) return;
                    let shouldResort = false;
                    for (let m of mutations) {
                        if (m.addedNodes.length > 0 && m.addedNodes[0].tagName === 'TR') {
                            shouldResort = true; break;
                        }
                    }
                    if (shouldResort) {
                        applySort(table, savedSort.colIndex, savedSort.direction, false);
                    }
                });
                observer.observe(tbody, { childList: true });
            }
        }
    }

    // --- SORTING LOGIC ---
    function applySort(table, colIndex, direction, save = true) {
        if (table._hrTableManagerSorting) return;
        const tableId = table.id;
        const tbody = table.querySelector('tbody');
        if (!tbody) return;
        const rows = Array.from(tbody.querySelectorAll('tr'));
        if (!rows.length) return; // Nothing to sort yet

        table._hrTableManagerSorting = true;
        try {
            const headers = table.querySelectorAll('thead th');

            headers.forEach((th, idx) => {
                const icon = th.querySelector('.sort-icon');
                if (icon) {
                    icon.className = 'fas fa-sort ms-1 text-muted sort-icon small';
                    if (idx === colIndex) {
                        icon.className = `fas fa-sort-${direction === 'asc' ? 'up' : 'down'} ms-1 text-primary sort-icon`;
                    }
                }
            });

            const sortedRows = rows.sort((a, b) => {
                const getVal = (row) => {
                    const cells = row.querySelectorAll('td');
                    if (!cells || !cells[colIndex]) return '';
                    const cell = cells[colIndex];
                    const input = cell.querySelector('input:not([type="hidden"]), select');
                    return (input ? input.value : cell.innerText).trim().toLowerCase();
                };
                const valA = getVal(a); const valB = getVal(b);
                if (valA === valB) return 0;
                
                // Handle dates specifically if they match DD/MM/YYYY
                const dateRegex = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/;
                const matchA = valA.match(dateRegex);
                const matchB = valB.match(dateRegex);
                if (matchA && matchB) {
                    const dateA = new Date(matchA[3], matchA[2]-1, matchA[1]).getTime();
                    const dateB = new Date(matchB[3], matchB[2]-1, matchB[1]).getTime();
                    return direction === 'asc' ? dateA - dateB : dateB - dateA;
                }

                const numA = parseFloat(valA); const numB = parseFloat(valB);
                if (!isNaN(numA) && !isNaN(numB)) {
                    return direction === 'asc' ? numA - numB : numB - numA;
                }
                return direction === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
            });

            tbody.innerHTML = '';
            sortedRows.forEach(row => tbody.appendChild(row));
            if (save) localStorage.setItem(`sort_${tableId}`, JSON.stringify({ colIndex, direction }));
        } finally {
            setTimeout(() => {
                table._hrTableManagerSorting = false;
            }, 0);
        }
    }

    function getSortState(tableId) {
        try { return JSON.parse(localStorage.getItem(`sort_${tableId}`)); } catch(e) { return null; }
    }

    // --- DRAG & DROP LOGIC ---
    let dragSrcEl = null;

    function handleDragStart(e) {
        dragSrcEl = this;
        e.dataTransfer.effectAllowed = 'move';
        this.classList.add('dragging');
    }

    function handleDragOver(e) {
        if (e.preventDefault) e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        return false;
    }

    function handleDragEnter() { this.classList.add('over'); }
    function handleDragLeave() { this.classList.remove('over'); }

    function handleDrop(e, tableId) {
        if (e.stopPropagation) e.stopPropagation();
        this.classList.remove('over');
        if (dragSrcEl !== this) {
            const table = this.closest('table');
            const fromIndex = Array.from(dragSrcEl.parentNode.children).indexOf(dragSrcEl);
            const toIndex = Array.from(this.parentNode.children).indexOf(this);
            
            reorderColumns(table, fromIndex, toIndex);
            saveColumnOrder(table, tableId);
        }
        return false;
    }

    function reorderColumns(table, from, to) {
        const rows = table.querySelectorAll('tr');
        rows.forEach(row => {
            const cells = Array.from(row.children);
            if (cells[from] && cells[to]) {
                if (from < to) {
                    row.insertBefore(cells[from], cells[to].nextSibling);
                } else {
                    row.insertBefore(cells[from], cells[to]);
                }
            }
        });
    }

    function saveColumnOrder(table, tableId) {
        const order = Array.from(table.querySelectorAll('thead th')).map(th => th.innerText.trim());
        localStorage.setItem(`order_${tableId}`, JSON.stringify(order));
    }

    function loadColumnOrder(table, tableId) {
        const saved = JSON.parse(localStorage.getItem(`order_${tableId}`));
        if (!saved) return;

        const headers = Array.from(table.querySelectorAll('thead th'));
        saved.forEach((title, targetIdx) => {
            const currentIdx = headers.findIndex(th => th.innerText.trim() === title);
            if (currentIdx !== -1 && currentIdx !== targetIdx) {
                reorderColumns(table, currentIdx, targetIdx);
                // Refresh headers array after move
                const newHeaders = Array.from(table.querySelectorAll('thead th'));
                headers.length = 0;
                headers.push(...newHeaders);
            }
        });
    }

    // Expose a way to re-init manually if the page adds tables via AJAX
    window.HRTableManagerReinit = init;
    document.addEventListener('DOMContentLoaded', init);
    return { init, setupTable };
})();
