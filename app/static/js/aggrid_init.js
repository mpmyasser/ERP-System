/**
 * AG-Grid Initialization Script
 * ==============================
 * For large data tables with advanced features
 */

// Arabic locale for AG-Grid
const arabicLocale = {
    page: 'صفحة',
    more: 'المزيد',
    to: 'إلى',
    of: 'من',
    next: 'التالي',
    last: 'الأخير',
    first: 'الأول',
    previous: 'السابق',
    loadingOoo: 'جاري التحميل...',
    selectAll: 'تحديد الكل',
    searchOoo: 'بحث...',
    blanks: 'فارغ',
    filterOoo: 'تصفية...',
    equals: 'يساوي',
    notEqual: 'لا يساوي',
    lessThan: 'أقل من',
    greaterThan: 'أكبر من',
    lessThanOrEqual: 'أقل من أو يساوي',
    greaterThanOrEqual: 'أكبر من أو يساوي',
    inRange: 'في النطاق',
    contains: 'يحتوي',
    notContains: 'لا يحتوي',
    startsWith: 'يبدأ بـ',
    endsWith: 'ينتهي بـ',
    andCondition: 'و',
    orCondition: 'أو',
    noRowsToShow: 'لا توجد صفوف لعرضها',
    enabled: 'مفعل',
    disabled: 'معطل',
    pinColumn: 'تثبيت العمود',
    autosizeThiscolumn: 'ضبط حجم هذا العمود تلقائياً',
    autosizeAllColumns: 'ضبط حجم جميع الأعمدة تلقائياً',
    groupBy: 'تجميع حسب',
    ungroupBy: 'إلغاء التجميع حسب',
    resetColumns: 'إعادة تعيين الأعمدة',
    expandAll: 'توسيع الكل',
    collapseAll: 'طي الكل',
    copy: 'نسخ',
    ctrlC: 'Ctrl+C',
    copyWithHeaders: 'نسخ مع العناوين',
    paste: 'لصق',
    ctrlV: 'Ctrl+V',
    export: 'تصدير'
};

// Default AG-Grid configuration
const defaultGridOptions = {
    localeText: arabicLocale,
    defaultColDef: {
        sortable: true,
        filter: true,
        resizable: true,
        minWidth: 100,
        flex: 1
    },
    enableRtl: true,
    animateRows: true,
    rowSelection: 'multiple',
    pagination: true,
    paginationPageSize: 50,
    paginationPageSizeSelector: [25, 50, 100, 200],
    suppressExcelExport: false,
    enableCellTextSelection: true,
    ensureDomOrder: true
};

// Initialize AG-Grid for attendance daily view
function initAttendanceGrid(elementId, rowData, columnDefs) {
    const gridDiv = document.querySelector('#' + elementId);
    if (!gridDiv) return;

    const gridOptions = {
        ...defaultGridOptions,
        columnDefs: columnDefs,
        rowData: rowData,
        onFirstDataRendered: (params) => {
            params.api.sizeColumnsToFit();
        }
    };

    new agGrid.Grid(gridDiv, gridOptions);
    return gridOptions;
}

// Initialize AG-Grid for reports
function initReportsGrid(elementId, rowData, columnDefs) {
    const gridDiv = document.querySelector('#' + elementId);
    if (!gridDiv) return;

    const gridOptions = {
        ...defaultGridOptions,
        columnDefs: columnDefs,
        rowData: rowData,
        enableRangeSelection: true,
        enableCharts: true,
        sideBar: {
            toolPanels: [
                {
                    id: 'columns',
                    labelDefault: 'الأعمدة',
                    labelKey: 'columns',
                    iconKey: 'columns',
                    toolPanel: 'agColumnsToolPanel'
                },
                {
                    id: 'filters',
                    labelDefault: 'الفلاتر',
                    labelKey: 'filters',
                    iconKey: 'filter',
                    toolPanel: 'agFiltersToolPanel'
                }
            ]
        },
        onFirstDataRendered: (params) => {
            params.api.sizeColumnsToFit();
        }
    };

    new agGrid.Grid(gridDiv, gridOptions);
    return gridOptions;
}

// Export AG-Grid to Excel
function exportGridToExcel(gridApi, filename = 'data') {
    gridApi.exportDataAsExcel({
        fileName: filename + '.xlsx',
        sheetName: 'البيانات'
    });
}

// Export AG-Grid to CSV
function exportGridToCSV(gridApi, filename = 'data') {
    gridApi.exportDataAsCsv({
        fileName: filename + '.csv'
    });
}

// Helper function to create column definitions from table headers
function createColumnDefsFromTable(tableId) {
    const table = document.querySelector('#' + tableId);
    if (!table) return [];

    const headers = table.querySelectorAll('thead th');
    const columnDefs = [];

    headers.forEach((header, index) => {
        columnDefs.push({
            headerName: header.textContent.trim(),
            field: 'col' + index,
            sortable: true,
            filter: true,
            resizable: true
        });
    });

    return columnDefs;
}

// Helper function to extract row data from table
function extractRowDataFromTable(tableId) {
    const table = document.querySelector('#' + tableId);
    if (!table) return [];

    const rows = table.querySelectorAll('tbody tr');
    const rowData = [];

    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        const rowObj = {};

        cells.forEach((cell, index) => {
            rowObj['col' + index] = cell.textContent.trim();
        });

        rowData.push(rowObj);
    });

    return rowData;
}
