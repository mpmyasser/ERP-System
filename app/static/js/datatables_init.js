console.log("HR System: DataTables Custom Sorting v9 Loaded - Zero Shift Mode");

// Global state to track sorting manually
window.HR_TABLE_ORDERS = window.HR_TABLE_ORDERS || {};

// --- متغير عام لحفظ عروض الأعمدة قبل فتح نافذة الطباعة ---
let _capturedWidths = [];

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

// Custom 3-state sorting logic (Zero Shift / Cumulative by default)
function handleThreeStateSort(api, colIdx) {
    const tableId = api.table().node().id || 'datatable';
    
    // Always work with a cumulative stack
    let currentOrder = window.HR_TABLE_ORDERS[tableId] || api.order() || [];
    let newOrder = [];
    let found = false;

    // Process current stack
    currentOrder.forEach(item => {
        if (item[0] === colIdx) {
            found = true;
            if (item[1] === 'asc') {
                newOrder.push([colIdx, 'desc']); // State 2: Desc
            } else {
                // State 3: Remove from stack (None)
            }
        } else {
            newOrder.push(item);
        }
    });

    if (!found) {
        newOrder.push([colIdx, 'asc']); // State 1: Asc (Additive)
    }

    window.HR_TABLE_ORDERS[tableId] = newOrder;
    console.log("HR System [" + tableId + "] New Order Stack:", JSON.stringify(newOrder));
    
    // Apply order and draw
    api.order(newOrder).draw();
    
    // Sync with stateSave
    if (api.state && typeof api.state.save === 'function') {
        api.state.save();
    }
}

function bindHierarchicalOrderGuard(api) {
    const tableNode = api.table().node();
    const $table = $(tableNode);

    const applyStrictProtection = () => {
        const $headers = $table.find('thead th');
        
        // COMPLETELY block DataTables default sort listeners
        // We unbind everything that DT might have attached
        $headers.off('click.dt mousedown.dt keydown.dt keyup.dt');
        
        // Remove any existing hrSort listeners to avoid double-firing
        $headers.off('click.hrSort').on('click.hrSort', function(e) {
            if ($(this).hasClass('no-sort')) return;
            
            // Kill all propagation and default behavior
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            
            const colIdx = api.column(this).index();
            handleThreeStateSort(api, colIdx);
            return false;
        });
        
        // Disable pointer events on sorting icons if they exist to force click on TH
        $headers.find('.DataTables_sort_icon').css('pointer-events', 'none');
    };

    // Initial apply
    applyStrictProtection();

    // Re-apply on every draw to ensure we stay in control
    $table.on('draw.dt', function() {
        applyStrictProtection();
    });
    
    console.log("HR System: Zero-Shift Protection active for", tableNode.id);
}

// Hierarchical logic disabled per user request
function applyHierarchicalOrderConfig(tableNode, config) {
    const resolvedConfig = $.extend(true, {}, config || {});
    resolvedConfig.orderMulti = true;
    return resolvedConfig;
}

function enforceHierarchicalOrder(api, draw = false) {
    // Disabled
}

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
    const version = 'v2'; // Change this manually if columns structure changes
    return `DataTables_${version}_${tableId}:${window.location.pathname}`;
}

// Default DataTable configuration
const defaultDataTableConfig = {
    language: arabicLanguage,
    responsive: true,
    autoWidth: false,
    orderMulti: true,
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
        data._columnsCount = settings.aoColumns.length;
    },
    stateLoadParams: function (settings, data) {
        if (data && data._columnsCount !== settings.aoColumns.length) {
            console.warn('DataTables state rejected due to column mismatch.');
            return false;
        }
    },
    drawCallback: function(settings) {
        // استعادة تحديدات checkboxes بعد كل رسم
        const tableId = settings.sTableId;
        const storageKey = `dt_checkboxes_${tableId}`;
        const selectedIds = JSON.parse(localStorage.getItem(storageKey) || '[]');
        
        $(this.api().table().node()).find('input[type="checkbox"].row-checkbox').each(function() {
            const row = $(this).closest('tr');
            const id = row.data('id') || row.attr('data-id');
            if (id && selectedIds.includes(String(id))) {
                this.checked = true;
            }
        });
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
        
        // حفظ تحديدات checkboxes عند التغيير
        const $table = $(api.table().node());
        $table.on('change', 'input[type="checkbox"].row-checkbox', function() {
            const storageKey = `dt_checkboxes_${tableId}`;
            const selectedIds = JSON.parse(localStorage.getItem(storageKey) || '[]');
            const row = $(this).closest('tr');
            const id = String(row.data('id') || row.attr('data-id'));
            
            if (this.checked) {
                if (!selectedIds.includes(id)) selectedIds.push(id);
            } else {
                const index = selectedIds.indexOf(id);
                if (index > -1) selectedIds.splice(index, 1);
            }
            
            localStorage.setItem(storageKey, JSON.stringify(selectedIds));
        });
    },
    dom: '<"row d-print-none"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>' +
        '<"row d-print-none mb-2"<"col-sm-12 col-md-6"B><"col-sm-12 col-md-6"p>>' +
        '<"hr-print-settings-wrapper d-print-none"> ' + 
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
            action: function(e, dt, node, config) {
                // قراءة عروض الأعمدة من الجدول الحي قبل فتح نافذة الطباعة
                _capturedWidths = [];
                $(dt.table().node()).find('thead th:visible').each(function() {
                    _capturedWidths.push(Math.round($(this).outerWidth()));
                });
                // استدعاء دالة الطباعة الافتراضية
                $.fn.dataTable.ext.buttons.print.action.call(this, e, dt, node, config);
            },
            customize: function (win) {
                try {
                    const settings = JSON.parse(localStorage.getItem('hr_print_settings') || '{}');
                    const $printBody = $(win.document.body);
                    const marginTop = settings.marginTop !== undefined ? settings.marginTop : 1;
                    const marginBottom = settings.marginBottom !== undefined ? settings.marginBottom : 1;
                    const orientation = settings.orientation || 'portrait';

                    $printBody.css({ 'direction': 'rtl', 'padding': '15px', 'background-color': '#fff' });

                    const pageStyle = `@page {
                        size: A4 ${orientation};
                        margin-top: ${marginTop}cm;
                        margin-bottom: ${marginBottom}cm;
                    }`;
                    $(win.document.head).append(`<style>${pageStyle} .print-footer-wrapper { position: fixed; bottom: 0; }</style>`);

                    const $originalTable = $printBody.find('table').first();
                    if ($originalTable.length === 0) return;

                    const $headerCells = $originalTable.find('thead th');
                    const $bodyRows = $originalTable.find('tbody tr');
                    if ($bodyRows.length === 0 || ($bodyRows.length === 1 && $bodyRows.find('td').first().hasClass('dataTables_empty'))) return;

                    const buildPrintWidthPlan = function(widths, availableWidth) {
                        const minPrintWidth = 30;
                        const numericWidths = widths.map(width => parseInt(width, 10) || 0);
                        const totalWidth = numericWidths.reduce((sum, width) => sum + width, 0);
                        const safeAvailableWidth = Math.max(320, Math.floor(availableWidth || 0));

                        if (!totalWidth || totalWidth <= safeAvailableWidth) {
                            return { widths: numericWidths, scaled: false };
                        }

                        const scaledWidths = numericWidths.map(width =>
                            Math.max(minPrintWidth, Math.round((width / totalWidth) * safeAvailableWidth))
                        );

                        let diff = safeAvailableWidth - scaledWidths.reduce((sum, width) => sum + width, 0);
                        while (diff !== 0) {
                            const direction = diff > 0 ? 1 : -1;
                            let adjusted = false;

                            for (let index = 0; index < scaledWidths.length && diff !== 0; index++) {
                                const targetIndex = direction > 0 ? index : (scaledWidths.length - 1 - index);
                                if (direction < 0 && scaledWidths[targetIndex] <= minPrintWidth) continue;
                                scaledWidths[targetIndex] += direction;
                                diff -= direction;
                                adjusted = true;
                            }

                            if (!adjusted) break;
                        }

                        return { widths: scaledWidths, scaled: true };
                    };

                    const applyPrintWidthsToCells = function($cells, widths, extraStyles) {
                        $cells.each(function(index) {
                            const width = widths[index];
                            if (!width) return;
                            $(this).css(Object.assign({
                                'width': width + 'px',
                                'min-width': width + 'px',
                                'max-width': width + 'px'
                            }, extraStyles || {}));
                        });
                    };

                    const availablePrintWidth = Math.max(800, ($printBody.get(0)?.clientWidth || win.innerWidth || 1100) - 40);
                    const printWidthPlan = buildPrintWidthPlan(_capturedWidths, availablePrintWidth);
                    const printColumnWidths = printWidthPlan.widths;
                    const useScaledPrintWidths = printWidthPlan.scaled;

                    // Smart detection logic - Two-pass priority search
                    let groupIdx = -1;
                    // Pass 1: High-priority (department-level) keywords
                    const groupKeywordsHigh = ['القسم', 'قسم', 'إدارة', 'الفرع', 'الموقع'];
                    // Pass 2: Low-priority (category-level) fallback
                    const groupKeywordsLow = ['النوع', 'الفئة', 'تصنيف'];
                    const sumKeywords = ['الراتب', 'المبلغ', 'القيمة', 'حافز', 'إضافي', 'الخصم', 'الصافي', 'إجمالي', 'مكافأة', 'سلفة', 'جزاء', 'بدل', 'العدد', 'الكمية', 'صافي'];
                    
                    const colInfo = [];
                    $headerCells.each(function(i) {
                        const txt = $(this).text().trim();
                        const isSum = sumKeywords.some(k => txt.includes(k)) && !['تاريخ', 'ميلاد', 'تعيين'].some(k => txt.includes(k));
                        colInfo.push({ index: i, text: txt, isSum: isSum });
                    });

                    // Pass 1: find high-priority group column
                    for (let i = 0; i < colInfo.length; i++) {
                        if (groupKeywordsHigh.some(k => colInfo[i].text.includes(k))) { groupIdx = i; break; }
                    }
                    // Pass 2: fallback to low-priority if nothing found
                    if (groupIdx === -1) {
                        for (let i = 0; i < colInfo.length; i++) {
                            if (groupKeywordsLow.some(k => colInfo[i].text.includes(k))) { groupIdx = i; break; }
                        }
                    }

                    let actionsIdx = -1;
                    $headerCells.each(function(i) { 
                        const txt = $(this).text().trim();
                        if (txt.includes('إجراء') || txt.includes('Action') || txt.includes('عمليات')) actionsIdx = i; 
                    });

                    const pageTitle = $('h1').first().text().trim() || $('h2').first().text().trim() || document.title;
                    const $wrapper = $('<div style="width:100%; direction:rtl; font-family:Cairo, sans-serif;">');

                    // 1. Header (Logo, Text, Date)
                    const $headerRow = $('<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; border-bottom:2px solid #333; padding-bottom:10px;"></div>');
                    const $hRight = $('<div></div>');
                    if (settings.showLogo && settings.logoData) $hRight.append('<img src="' + settings.logoData + '" style="height:60px; margin-bottom:10px; display:block;">');
                    if (settings.showHeader && settings.headerText) $hRight.append('<h4 style="margin:0; font-weight:bold;">' + settings.headerText + '</h4>');
                    $hRight.append('<h2 style="margin:5px 0; font-weight:bold; text-decoration:underline;">' + pageTitle + '</h2>');
                    $headerRow.append($hRight);

                    if (settings.showDate) {
                        const now = new Date();
                        const dateStr = now.toLocaleDateString('ar-EG', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
                        const timeStr = now.toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' });
                        $headerRow.append('<div style="text-align:left; font-size:0.9em;">' + dateStr + '<br>' + timeStr + '</div>');
                    }
                    $wrapper.append($headerRow);

                    // 2. Data Grouping
                    const groups = {};
                    const globalSums = {};
                    let globalCount = 0;

                    $bodyRows.each(function() {
                        const $row = $(this);
                        if ($row.find('td').length < 2) return; // Skip empty/loading rows
                        const gVal = (groupIdx !== -1) ? ($row.find('td').eq(groupIdx).text().trim() || 'غير مصنف') : 'تقرير عام';
                        if (!groups[gVal]) groups[gVal] = [];
                        groups[gVal].push($row);
                    });

                    let groupCount = 0;
                    Object.keys(groups).sort().forEach(function(gName) {
                        const rows = groups[gName];
                        globalCount += rows.length;
                        groupCount++;

                        // Paper-saving wrapping with break protection
                        const groupTitle = groupIdx !== -1 && colInfo[groupIdx] ? colInfo[groupIdx].text + ': ' : '';
                        const $groupWrapper = $('<div style="page-break-inside: auto; margin-bottom: 20px;"></div>');
                        $groupWrapper.append('<div style="background:#f4f4f4; border-right:10px solid #1a2a3a; padding:10px; margin:10px 0 5px 0; font-size:1.1em; font-weight:bold; border-bottom:1px solid #ccc; page-break-after: avoid;">' + groupTitle + gName + '</div>');
                        
                        const tableStyle = useScaledPrintWidths
                            ? 'font-size:10px; border-collapse:collapse; border:1px solid #000; table-layout:fixed; width:100%;'
                            : 'font-size:10px; border-collapse:collapse; border:1px solid #000; table-layout:auto;';
                        const $table = $('<table class="table table-bordered w-100" style="' + tableStyle + '"></table>');
                        const $hCloned = $originalTable.find('thead').clone();
                        $hCloned.find('th').each(function(i) {
                            const baseStyle = {
                                'background-color': '#eee',
                                'border': '1px solid #000',
                                'text-align': 'center',
                                'padding': '5px'
                            };
                            if (printColumnWidths[i]) {
                                baseStyle['width'] = printColumnWidths[i] + 'px';
                                baseStyle['min-width'] = printColumnWidths[i] + 'px';
                                baseStyle['max-width'] = printColumnWidths[i] + 'px';
                            }
                            $(this).css(baseStyle);
                        });
                        if (actionsIdx !== -1) $hCloned.find('th').eq(actionsIdx).text('توقيع العامل');
                        $table.append($hCloned);

                        const $tbody = $('<tbody></tbody>');
                        rows.forEach($r => {
                            const $rCloned = $r.clone();
                            if (actionsIdx !== -1) $rCloned.find('td').eq(actionsIdx).html('<div style="border-bottom:1px dotted #000; height:15px; width:100%;"></div>');
                            applyPrintWidthsToCells($rCloned.find('td'), printColumnWidths, {
                                'border': '1px solid #000',
                                'text-align': 'center',
                                'padding': '4px'
                            });
                            $tbody.append($rCloned);
                        });
                        $table.append($tbody);

                        // Group Totals
                        const $tfoot = $('<tfoot></tfoot>');
                        const $trFoot = $('<tr style="background:#fafafa; font-weight:bold; border:1px solid #000;">');
                        colInfo.forEach((col, idx) => {
                            const w = printColumnWidths[idx] ? printColumnWidths[idx] + 'px' : 'auto';
                            const tdBaseStyle = {
                                'border': '1px solid #000',
                                'text-align': 'center',
                                'padding': '5px',
                                'width': w,
                                'min-width': w,
                                'max-width': w
                            };
                            const tdStyleString = Object.entries(tdBaseStyle).map(([k, v]) => `${k}:${v};`).join(' ');
                            
                            if (col.index === 0) { $trFoot.append('<td style="' + tdStyleString + '">العدد: ' + rows.length + '</td>'); return; }
                            if (col.index === actionsIdx) { $trFoot.append('<td style="' + tdStyleString + '"></td>'); return; }
                            if (col.isSum) {
                                let s = 0;
                                rows.forEach($r => {
                                    const raw = $r.find('td').eq(col.index).text().trim();
                                    const val = parseFloat(raw.replace(/[^\d.-]/g, '')) || 0;
                                    s += val;
                                });
                                globalSums[col.index] = (globalSums[col.index] || 0) + s;
                                $trFoot.append('<td style="' + tdStyleString + '">' + (s ? s.toLocaleString(undefined, {minimumFractionDigits:0, maximumFractionDigits:2}) : '-') + '</td>');
                            } else {
                                $trFoot.append('<td style="' + tdStyleString + '"></td>');
                            }
                        });
                        $table.append($tfoot.append($trFoot));
                        $groupWrapper.append($table);
                        $wrapper.append($groupWrapper);
                    });

                    // 3. Grand Total Section
                    $wrapper.append('<div style="background:#1a2a3a; color:#fff; padding:10px; margin:38px 0 10px 0; font-size:1.2em; font-weight:bold; text-align:center; border-radius:5px;">إجمالي عام للشركة</div>');
                    const grandTableStyle = useScaledPrintWidths
                        ? 'font-size:11px; border-collapse:collapse; border:2px solid #000; background:#f9f9f9; table-layout:fixed; width:100%;'
                        : 'font-size:11px; border-collapse:collapse; border:2px solid #000; background:#f9f9f9;';
                    const $grandTable = $('<table class="table table-bordered w-100" style="' + grandTableStyle + '"></table>');
                    const $gh = $originalTable.find('thead').clone();
                    $gh.find('th').each(function(i) {
                        const baseStyle = {
                            'background-color': '#343a40',
                            'color': '#fff',
                            'border': '1px solid #000',
                            'text-align': 'center'
                        };
                        if (printColumnWidths[i]) {
                            baseStyle['width'] = printColumnWidths[i] + 'px';
                            baseStyle['min-width'] = printColumnWidths[i] + 'px';
                            baseStyle['max-width'] = printColumnWidths[i] + 'px';
                        }
                        $(this).css(baseStyle);
                    });
                    if (actionsIdx !== -1) $gh.find('th').eq(actionsIdx).text('');
                    $grandTable.append($gh);

                    const $gf = $('<tfoot></tfoot>');
                    const $gfr = $('<tr style="font-weight:bold; border:2px solid #000;">');
                    colInfo.forEach((col, idx) => {
                        const w = printColumnWidths[idx] ? printColumnWidths[idx] + 'px' : 'auto';
                        const tdBaseStyle = {
                            'border': '1px solid #000',
                            'text-align': 'center',
                            'padding': '5px',
                            'background': '#eee',
                            'width': w,
                            'min-width': w,
                            'max-width': w
                        };
                        const tdStyleString = Object.entries(tdBaseStyle).map(([k, v]) => `${k}:${v};`).join(' ');
                        
                        if (col.index === 0) { $gfr.append('<td style="' + tdStyleString + '">العدد الكلي: ' + globalCount + '</td>'); return; }
                        if (col.index === actionsIdx) { $gfr.append('<td style="' + tdStyleString + '"></td>'); return; }
                        const s = globalSums[col.index];
                        if (col.isSum && s !== undefined) {
                            $gfr.append('<td style="' + tdStyleString + '">' + s.toLocaleString(undefined, {minimumFractionDigits:0, maximumFractionDigits:2}) + '</td>');
                        } else {
                            $gfr.append('<td style="' + tdStyleString + '"></td>');
                        }
                    });
                    $grandTable.append($gf.append($gfr));
                    $wrapper.append($grandTable);

                    // 4. Footer
                    if (settings.showPageNumbers || (settings.showFooter && settings.footerText)) {
                        const $footer = $('<div class="print-footer-wrapper" style="position:fixed; bottom:0; width:100%; border-top:1px solid #000; padding:5px 0; font-size:8pt; background:#fff; display:flex; justify-content:space-between;"></div>');
                        if (settings.showFooter && settings.footerText) $footer.append('<div style="margin-right:15px;">' + settings.footerText + '</div>');
                        if (settings.showPageNumbers) $footer.append('<div style="margin-left:15px; direction:ltr;">Page <span class="pageNumber"></span></div>');
                        $wrapper.append($footer);
                    }

                    $printBody.empty().append($wrapper);

                } catch (e) { console.error("Smart Print Error:", e); }
            }
        },
        {
            text: '<i class="fas fa-cog"></i> خيارات الطباعة',
            className: 'btn btn-outline-secondary btn-sm',
            action: function(e, dt, node, config) {
                togglePrintSettings(dt);
            }
        },
        { extend: 'colvis', text: '<i class="fas fa-columns"></i> تخصيص', className: 'btn btn-outline-primary btn-sm' }
    ]
};

// Print Settings Inline Panel Handler
function togglePrintSettings(dt) {
    const $container = $(dt.table().container()).find('.hr-print-settings-wrapper');
    if ($container.find('.hr-inline-settings').length) {
        $container.toggle();
        return;
    }

    const saved = JSON.parse(localStorage.getItem('hr_print_settings') || '{}');
    const panelHtml = `
        <div class="hr-inline-settings p-3 border rounded bg-light mb-3 mt-2 shadow-sm" style="direction: rtl; font-size: 0.9em;">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <h6 class="mb-0 fw-bold"><i class="fas fa-print me-1 text-primary"></i> خيارات جودة الطباعة المتقدمة</h6>
                <button type="button" class="btn-close btn-sm" onclick="$(this).closest('.hr-print-settings-wrapper').hide()"></button>
            </div>
            <div class="row g-3">
                <div class="col-md-4">
                    <label class="form-label fw-bold small text-muted">شعار الشركة (Logo)</label>
                    <div class="d-flex gap-2 align-items-center">
                        <div class="logo-preview border rounded d-flex align-items-center justify-content-center bg-white" style="width:40px; height:40px; overflow:hidden;">
                            ${saved.logoData ? `<img src="${saved.logoData}" style="max-width:100%; max-height:100%;">` : '<i class="fas fa-image text-muted"></i>'}
                        </div>
                        <input type="file" class="form-control form-control-sm logo-input" accept="image/*" style="width:120px;">
                        <div class="form-check form-switch pt-1">
                            <input class="form-check-input show-logo" type="checkbox" ${saved.showLogo !== false ? 'checked' : ''}>
                            <label class="form-check-label small">تفعيل</label>
                        </div>
                    </div>
                </div>
                <div class="col-md-4 border-start">
                    <div class="form-check form-switch mb-1">
                        <input class="form-check-input show-header" type="checkbox" ${saved.showHeader !== false ? 'checked' : ''}>
                        <label class="form-check-label fw-bold small">رأس الصفحة (Header)</label>
                    </div>
                    <input type="text" class="form-control form-control-sm header-text" placeholder="اسم الشركة أو نص الهيدر" value="${saved.headerText || ''}">
                    <div class="mt-2">
                        <div class="form-check form-switch mb-1">
                            <input class="form-check-input show-footer" type="checkbox" ${saved.showFooter !== false ? 'checked' : ''}>
                            <label class="form-check-label fw-bold small">تذييل الصفحة (Footer)</label>
                        </div>
                        <input type="text" class="form-control form-control-sm footer-text" placeholder="نص مخصص للتذييل" value="${saved.footerText || ''}">
                    </div>
                </div>
                <div class="col-md-4 border-start">
                    <div class="d-flex gap-3 mb-2">
                        <div class="form-check form-switch">
                            <input class="form-check-input show-date" type="checkbox" ${saved.showDate !== false ? 'checked' : ''}>
                            <label class="form-check-label small">عرض التاريخ</label>
                        </div>
                        <div class="form-check form-switch">
                            <input class="form-check-input show-page-numbers" type="checkbox" ${saved.showPageNumbers !== false ? 'checked' : ''}>
                            <label class="form-check-label small">ترقيم الصفحات</label>
                        </div>
                    </div>
                    <div class="d-flex gap-3 align-items-end">
                        <div>
                            <label class="form-label fw-bold small text-muted mb-1"><i class="fas fa-arrows-alt-v text-secondary me-1"></i>الهوامش (سم)</label>
                            <div class="d-flex gap-2">
                                <input type="number" class="form-control form-control-sm margin-top-input" title="علوي" min="0" max="10" step="0.5" style="width:60px;" value="${saved.marginTop !== undefined ? saved.marginTop : 1}">
                                <input type="number" class="form-control form-control-sm margin-bottom-input" title="سفلي" min="0" max="10" step="0.5" style="width:60px;" value="${saved.marginBottom !== undefined ? saved.marginBottom : 1}">
                            </div>
                        </div>
                        <div>
                            <label class="form-label fw-bold small text-muted mb-1"><i class="fas fa-file-alt text-secondary me-1"></i>الوضعية</label>
                            <select class="form-select form-select-sm orientation-select" style="width:90px;">
                                <option value="portrait" ${saved.orientation === 'portrait' ? 'selected' : ''}>طولي</option>
                                <option value="landscape" ${saved.orientation === 'landscape' ? 'selected' : ''}>عرضي</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>
            <div class="mt-2 text-end">
                <small class="text-muted italic">* يتم حفظ الإعدادات تلقائياً لكل مرة طباعة قادمة.</small>
            </div>
        </div>
    `;

    $container.html(panelHtml).show();

    // Event Bindings
    $container.find('input, select').on('change input', function() {
        const settings = {
            showLogo: $container.find('.show-logo').is(':checked'),
            logoData: $container.find('.logo-preview img').attr('src') || '',
            showHeader: $container.find('.show-header').is(':checked'),
            headerText: $container.find('.header-text').val(),
            showDate: $container.find('.show-date').is(':checked'),
            showPageNumbers: $container.find('.show-page-numbers').is(':checked'),
            showFooter: $container.find('.show-footer').is(':checked'),
            footerText: $container.find('.footer-text').val(),
            marginTop: parseFloat($container.find('.margin-top-input').val()) || 1,
            marginBottom: parseFloat($container.find('.margin-bottom-input').val()) || 1,
            orientation: $container.find('.orientation-select').val() || 'portrait'
        };
        localStorage.setItem('hr_print_settings', JSON.stringify(settings));
    });

    $container.find('.logo-input').on('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(event) {
                const base64 = event.target.result;
                $container.find('.logo-preview').html(`<img src="${base64}" style="max-width:100%; max-height:100%;">`);
                $container.find('.show-logo').trigger('change');
            };
            reader.readAsDataURL(file);
        }
    });
}

// Global visibility helper (legacy support)
function showPrintSettingsModal(dt, config) {
    togglePrintSettings(dt);
}

// Global function to initialize DataTable once
function initDataTableOnce(target, config) {
    const $table = typeof target === 'string' ? $(target) : $(target);
    if (!$table.length) return null;
    const node = $table.get(0);
    const selector = node.id ? ('#' + node.id) : null;
    const finalConfig = applyHierarchicalOrderConfig(node, config);

    // Global guard: initialize each table only once.
    if (selector) {
        if (!$.fn.DataTable.isDataTable(selector)) {
            const api = $table.DataTable(finalConfig);
            bindHierarchicalOrderGuard(api);
            enforceHierarchicalOrder(api, true);
            return api;
        }
        const api = new $.fn.dataTable.Api(node);
        bindHierarchicalOrderGuard(api);
        enforceHierarchicalOrder(api, true);
        return api;
    }

    if (!$.fn.DataTable.isDataTable(node)) {
        const api = $table.DataTable(finalConfig);
        bindHierarchicalOrderGuard(api);
        enforceHierarchicalOrder(api, true);
        return api;
    }
    const api = new $.fn.dataTable.Api(node);
    bindHierarchicalOrderGuard(api);
    enforceHierarchicalOrder(api, true);
    return api;
}

$(document).ready(function () {
    const specificTables = ['employees-table', 'departments-table', 'loans-table', 'penalties-table', 'permissions-table', 'attendance-table'];

    // ===== Top Scrollbar (deferred to avoid layout shift) =====
    function initTopScrollbars() {
        // Wrap in rAF so DOM insertion happens AFTER first paint — no visible reflow
        requestAnimationFrame(function() {
            $('.table-responsive').each(function () {
                var $this = $(this);
                var $table = $this.find('table');
                $this.prev('.top-scrollbar-wrapper').remove();
                var $wrapper = $('<div class="top-scrollbar-wrapper d-print-none" style="display:none"><div></div></div>');
                $this.before($wrapper);
                var $inner = $wrapper.find('div');
                function update() {
                    var tw = $table.prop('scrollWidth') || $table.outerWidth();
                    $inner.width(tw);
                    if (tw > $this.width() + 5) { $wrapper.show(); $wrapper.scrollLeft($this.scrollLeft()); } else { $wrapper.hide(); }
                }
                $wrapper.on('scroll', function () {
                    if ($this.data('scrolling')) return;
                    $wrapper.data('scrolling', true);
                    $this.scrollLeft($wrapper.scrollLeft());
                    requestAnimationFrame(function () { $wrapper.data('scrolling', false); });
                });
                $this.on('scroll', function () {
                    if ($wrapper.data('scrolling')) return;
                    $this.data('scrolling', true);
                    $wrapper.scrollLeft($this.scrollLeft());
                    requestAnimationFrame(function () { $this.data('scrolling', false); });
                });
                // Defer first size calculation until after layout is stable
                setTimeout(update, 50);
                $(window).on('resize', update);
                $table.on('draw.dt', update);
            });
        });
    }

    // ===== Generic datatable init =====
    $('.datatable').each(function () {
        if (specificTables.includes(this.id)) return;
        initDataTableOnce(this, defaultDataTableConfig);
    });

    // ===== Employees Table =====
    initDataTableOnce('#employees-table', {
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
            { width: '6%' },   // Work Hours
            { width: '5%' },   // Overtime
            { width: '9%' },   // Salary Date
            { width: '5%' },   // Status
            { width: '10%', orderable: false, visible: true } // Actions
        ],
        order: [[1, 'asc']],
        initComplete: function(settings, json) {
            const api = this.api();
            api.column('.col-actions').visible(true);
            // Init scrollbars AFTER this table is fully ready
            initTopScrollbars();
        }
    });

    initDataTableOnce('#attendance-table', $.extend(true, {}, defaultDataTableConfig, {
        language: { url: "//cdn.datatables.net/plug-ins/1.13.7/i18n/ar.json" },
        order: [[0, "asc"]],
        pageLength: 25
    }));

    initDataTableOnce('#departments-table', {
        ...defaultDataTableConfig,
        order: [[0, 'asc']]
    });

    initDataTableOnce('#penalties-table', {
        ...defaultDataTableConfig
    });

    initDataTableOnce('#permissions-table', {
        ...defaultDataTableConfig
    });

    // For pages without employees-table, still init scrollbars after a safe delay
    if (!document.getElementById('employees-table')) {
        setTimeout(initTopScrollbars, 100);
    }
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

// Checkbox helper functions
function getSelectedCheckboxIds(tableId) {
    const storageKey = `dt_checkboxes_${tableId}`;
    return JSON.parse(localStorage.getItem(storageKey) || '[]');
}

function clearSelectedCheckboxes(tableId) {
    const storageKey = `dt_checkboxes_${tableId}`;
    localStorage.removeItem(storageKey);
    $(`#${tableId}`).find('input[type="checkbox"].row-checkbox').prop('checked', false);
}
