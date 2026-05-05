/**
 * DataTable Checkbox Persistence
 * Compatibility layer - persistence is centralized in datatables_init.js
 */

(function () {
    'use strict';

    window.initCheckboxPersistence = function (tableId, checkboxSelector, getIdCallback) {
        const tableSelector = `#${tableId}`;
        if (!$.fn.DataTable.isDataTable(tableSelector)) return;
        if (checkboxSelector !== '.row-checkbox') return;
        const table = new $.fn.dataTable.Api(tableSelector);
        table.draw(false);
    };

    window.getSelectedIds = function (tableId) {
        if (typeof window.getSelectedCheckboxIds === 'function') {
            return window.getSelectedCheckboxIds(tableId);
        }
        return [];
    };

    window.clearSelectedIds = function (tableId) {
        if (typeof window.clearSelectedCheckboxes === 'function') {
            window.clearSelectedCheckboxes(tableId);
            return;
        }
        const tableSelector = `#${tableId}`;
        if ($.fn.DataTable.isDataTable(tableSelector)) {
            const table = new $.fn.dataTable.Api(tableSelector);
            table.draw(false);
        }
    };

    window.selectAllCurrentPage = function (tableId, checkboxSelector, getIdCallback) {
        const tableSelector = `#${tableId}`;
        if (!$.fn.DataTable.isDataTable(tableSelector)) return;
        const table = new $.fn.dataTable.Api(tableSelector);
        table.rows({ page: 'current' }).every(function () {
            const row = this.node();
            const checkbox = $(row).find(checkboxSelector)[0];
            if (!checkbox) return;
            checkbox.checked = true;
            $(checkbox).trigger('change');
        });
    };
})();
