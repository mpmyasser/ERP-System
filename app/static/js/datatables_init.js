/**
 * DataTables Initialization Script
 * =================================
 * Auto-initializes all tables with class="datatable"
 */

// Arabic language settings for DataTables
const arabicLanguage = {
    "sEmptyTable": "ليست هناك بيانات متاحة في الجدول",
    "sInfo": "إظهار _START_ إلى _END_ من أصل _TOTAL_ مدخل",
    "sInfoEmpty": "يعرض 0 إلى 0 من أصل 0 سجل",
    "sInfoFiltered": "(منتقاة من مجموع _MAX_ مُدخل)",
    "sInfoPostFix": "",
    "sInfoThousands": ",",
    "sLengthMenu": "أظهر _MENU_ مدخلات",
    "sLoadingRecords": "جارٍ التحميل...",
    "sProcessing": "جارٍ التحميل...",
    "sSearch": "ابحث:",
    "sZeroRecords": "لم يعثر على أية سجلات",
    "oPaginate": {
        "sFirst": "الأول",
        "sPrevious": "السابق",
        "sNext": "التالي",
        "sLast": "الأخير"
    },
    "oAria": {
        "sSortAscending": ": تفعيل لترتيب العمود تصاعدياً",
        "sSortDescending": ": تفعيل لترتيب العمود تنازلياً"
    },
    "buttons": {
        "colvis": "تغيير الأعمدة"
    }
};

function getStoredObject(key, fallback = null) {
    if (!window.HRSettingsUtil) return fallback;
    return window.HRSettingsUtil.getObject(key, fallback);
}

function setStoredObject(key, value) {
    if (!window.HRSettingsUtil) return;
    window.HRSettingsUtil.setObject(key, value);
}

function getDataTableStateKey(settings) {
    const tableId = settings.sTableId || settings.sInstance || 'datatable';
    return `DataTables_${tableId}:${window.location.pathname}`;
}

// Default DataTable configuration
const defaultDataTableConfig = {
    language: arabicLanguage,
    responsive: true,
    colReorder: true,
    pageLength: 25,
    lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "الكل"]],
    stateSave: true,
    stateDuration: 60 * 60 * 24 * 30, // 30 days
    stateSaveCallback: function (settings, data) {
        setStoredObject(getDataTableStateKey(settings), data);
    },
    stateLoadCallback: function (settings) {
        return getStoredObject(getDataTableStateKey(settings), null);
    },
    stateSaveParams: function (settings, data) {
        data.search.search = "";
        data.start = 0;
    },
    initComplete: function (settings, json) {
        // Restore visibility by column name (more robust than index)
        const api = this.api();
        const tableId = settings.sTableId;
        const visMap = getStoredObject('dt_vis_' + tableId, null);
        if (visMap) {
            api.columns().every(function () {
                const name = $(this.header()).text().trim();
                if (visMap.hasOwnProperty(name)) {
                    this.visible(visMap[name], false);
                }
            });
            api.draw(false);
        }
    },
    dom: '<"row d-print-none"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>' +
        '<"row d-print-none mb-2"<"col-sm-12 col-md-6"B><"col-sm-12 col-md-6"p>>' +
        '<"row"<"col-sm-12"tr>>' +
        '<"row d-print-none mt-2"<"col-sm-12 col-md-5"i><"col-sm-12 col-md-7"p>>',
    buttons: [
        {
            extend: 'excel',
            text: '<i class="fas fa-file-excel"></i> Excel',
            className: 'btn btn-success btn-sm',
            exportOptions: { columns: ':visible' },
            customize: function (xlsx) {
                if (typeof formatExcelExport === 'function') formatExcelExport(xlsx);
            }
        },
        {
            extend: 'print',
            text: '<i class="fas fa-print"></i> طباعة (تقرير مقسم)',
            className: 'btn btn-secondary btn-sm',
            footer: true,
            title: '',
            exportOptions: { columns: ':visible' },
            customize: function (win) {
                try {
                    var $printBody = $(win.document.body);
                    $printBody.css({ 'direction': 'rtl', 'background-color': '#fff', 'padding': '15px' });

                    var $originalTable = $printBody.find('table').first();
                    if ($originalTable.length === 0) return;

                    var $headerCells = $originalTable.find('thead th');
                    var $bodyRows = $originalTable.find('tbody tr');
                    if ($bodyRows.length === 1 && $bodyRows.find('td').first().hasClass('dataTables_empty')) return;

                    // Detection
                    var deptIdx = -1, codeIdx = -1, actionsIdx = -1;
                    $headerCells.each(function (i) {
                        var t = $(this).text().trim().toLowerCase();
                        if (['القسم', 'قسم', 'إدارة'].some(k => t.includes(k))) deptIdx = i;
                        if (['كود', 'الكود', 'رقم'].some(k => t.includes(k))) codeIdx = i;
                        if (t.includes('إجراء') || t.includes('action')) actionsIdx = i;
                    });

                    var sumKeywords = ['الراتب', 'المبلغ', 'القيمة', 'حافز', 'إضافي', 'الخصم', 'الصافي', 'إجمالي', 'مكافأة'];
                    var pageTitle = $('h1').first().text().trim() || $('h2').first().text().trim() || document.title;

                    if (deptIdx !== -1) {
                        var groups = {};
                        $bodyRows.each(function () {
                            var deptName = $(this).find('td').eq(deptIdx).text().trim() || 'بدون قسم';
                            if (!groups[deptName]) groups[deptName] = [];
                            groups[deptName].push($(this));
                        });

                        var $wrapper = $('<div style="width:100%; direction:rtl;">');
                        $wrapper.append('<h2 style="text-align:center; text-decoration:underline; font-weight:bold; margin-bottom:20px;">' + pageTitle + '</h2>');

                        Object.keys(groups).sort().forEach(function (dept) {
                            var rows = groups[dept];
                            if (codeIdx !== -1) {
                                rows.sort((a, b) => (parseInt(a.find('td').eq(codeIdx).text().replace(/\D/g, '')) || 0) - (parseInt(b.find('td').eq(codeIdx).text().replace(/\D/g, '')) || 0));
                            }

                            $wrapper.append('<div style="background:#f4f4f4; border-right:10px solid #1a2a3a; padding:10px; margin:25px 0 10px 0; font-size:1.1em; font-weight:bold;">القسم: ' + dept + '</div>');
                            var $newTable = $('<table class="table table-bordered w-100" style="font-size:10px; border-collapse:collapse; border:1px solid #000;"></table>');
                            var $h = $originalTable.find('thead').clone();
                            $h.find('th').css({ 'background-color': '#eee', 'border': '1px solid #000', 'text-align': 'center' });
                            if (actionsIdx !== -1) $h.find('th').eq(actionsIdx).text('توقيع العامل');
                            $newTable.append($h);

                            var $b = $('<tbody></tbody>');
                            rows.forEach(function ($r) {
                                var $clone = $r.clone();
                                if (actionsIdx !== -1) $clone.find('td').eq(actionsIdx).html('<div style="border-bottom:1px dotted #000; height:15px; width:100%;"></div>');
                                $clone.find('td').css({ 'border': '1px solid #000', 'text-align': 'center', 'padding': '4px' });
                                $b.append($clone);
                            });
                            $newTable.append($b);

                            var $f = $('<tfoot></tfoot>');
                            var $fr = $('<tr style="background:#fafafa; font-weight:bold; border:1px solid #000;">');
                            $headerCells.each(function (idx) {
                                if (idx === 0) { $fr.append('<td style="border:1px solid #000; text-align:center;">العدد: ' + rows.length + '</td>'); return; }
                                if (actionsIdx !== -1 && idx === actionsIdx) { $fr.append('<td style="border:1px solid #000;"></td>'); return; }
                                var isSum = sumKeywords.some(k => $(this).text().includes(k));
                                if (isSum && !$(this).text().includes('تاريخ')) {
                                    var s = 0; rows.forEach($r => s += parseFloat($r.find('td').eq(idx).text().replace(/[^\d.-]/g, '')) || 0);
                                    $fr.append('<td style="border:1px solid #000; text-align:center;">' + (s ? s.toLocaleString() : '') + '</td>');
                                } else { $fr.append('<td style="border:1px solid #000;"></td>'); }
                            });
                            $newTable.append($f.append($fr));

                            $newTable.css('table-layout', 'fixed');
                            var m = $('<div style="position:absolute; visibility:hidden; white-space:nowrap; font-family:Cairo; font-size:10px;">').appendTo($printBody);
                            $newTable.find('thead th').each(function (ci) {
                                if (ci === actionsIdx) return;
                                var mw = m.text($(this).text().trim()).outerWidth();
                                rows.slice(0, 50).forEach($r => { var cw = m.text($r.find('td').eq(ci).text().trim()).outerWidth(); if (cw > mw) mw = cw; });
                                $(this).css('width', (mw + 20) + 'px');
                            });
                            m.remove();
                            $wrapper.append($newTable);
                        });
                        $printBody.empty().append($wrapper);
                    } else {
                        $printBody.prepend('<h2 style="text-align:center;">' + pageTitle + '</h2>');
                    }
                } catch (e) { console.error("Print Error:", e); }
            }
        },
        { extend: 'colvis', text: '<i class="fas fa-columns"></i> تخصيص', className: 'btn btn-outline-primary btn-sm' }
    ]
};

// Global visibility persistence by NAME
$(document).on('column-visibility.dt', function (e, settings, column, state) {
    const tableId = settings.sTableId;
    const api = new $.fn.dataTable.Api(settings);
    const name = $(api.column(column).header()).text().trim();
    let visMap = getStoredObject('dt_vis_' + tableId, {});
    visMap[name] = state;
    setStoredObject('dt_vis_' + tableId, visMap);

    // Sync with other tables if they have same column name
    $('.datatable').each(function () {
        const otherApi = $(this).DataTable();
        if (this.id !== tableId) {
            otherApi.columns().every(function () {
                if ($(this.header()).text().trim() === name) this.visible(state, false);
            });
        }
    });
});

$(document).ready(function () {
    $('.datatable').each(function () {
        const specificTables = ['employees-table', 'departments-table', 'loans-table', 'penalties-table', 'permissions-table'];
        if (!specificTables.includes(this.id) && !$.fn.DataTable.isDataTable(this)) {
            $(this).DataTable(defaultDataTableConfig);
        }
    });

    function initTopScrollbars() {
        $('.table-responsive').each(function () {
            var $this = $(this);
            var $table = $this.find('table');
            $this.prev('.top-scrollbar-wrapper').remove();
            var $wrapper = $('<div class="top-scrollbar-wrapper d-print-none"><div></div></div>');
            $this.before($wrapper);
            var $inner = $wrapper.find('div');
            function update() {
                var tw = $table.prop('scrollWidth') || $table.outerWidth();
                $inner.width(tw);
                if (tw > $this.width() + 5) { $wrapper.show(); $wrapper.scrollLeft($this.scrollLeft()); } else { $wrapper.hide(); }
            }
            $wrapper.on('scroll', function () { if (!$this.data('scrolling')) { $wrapper.data('scrolling', true); $this.scrollLeft($wrapper.scrollLeft()); setTimeout(() => $wrapper.data('scrolling', false), 10); } });
            $this.on('scroll', function () { if (!$wrapper.data('scrolling')) { $this.data('scrolling', true); $wrapper.scrollLeft($this.scrollLeft()); setTimeout(() => $this.data('scrolling', false), 10); } });
            update();
            $(window).on('resize', update);
            $table.on('draw.dt', update);
            setTimeout(update, 1000);
        });
    }
    initTopScrollbars();

    if ($('#employees-table').length && !$.fn.DataTable.isDataTable('#employees-table')) {
        $('#employees-table').DataTable({
            ...defaultDataTableConfig,
            columns: [
                { width: '8%' },   // Code
                { width: '15%' },  // Name
                { width: '10%' },  // Job
                { width: '10%' },  // Dept
                { width: '10%' },  // Hire Date
                { width: '8%' },   // Insurance
                { width: '10%' },  // Salary
                { width: '8%' },   // Reg Incentive
                { width: '5%' },   // Overtime
                { width: '9%' },   // Salary Date
                { width: '5%' },   // Status
                { width: '10%', orderable: false, visible: true } // Actions
            ],
            order: [[1, 'asc']],
            initComplete: function(settings, json) {
                // Force Actions column to always be visible
                const api = this.api();
                api.column('.col-actions').visible(true);
            }
        });
    }
    ['departments', 'loans', 'penalties', 'permissions'].forEach(t => {
        const id = '#' + t + '-table';
        if ($(id).length && !$.fn.DataTable.isDataTable(id)) {
            $(id).DataTable({ ...defaultDataTableConfig, order: [[0, t === 'departments' ? 'asc' : 'desc']] });
        }
    });
});

// Export function for custom use
function exportTableToExcel(tableId, filename = 'data') {
    const table = $('#' + tableId).DataTable();
    table.button('.buttons-excel').trigger();
}

function exportTableToCSV(tableId, filename = 'data') {
    const table = $('#' + tableId).DataTable();
    table.button('.buttons-csv').trigger();
}
