document.addEventListener('DOMContentLoaded', () => {
    // Load ExcelJS Library
    const script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/exceljs/4.3.0/exceljs.min.js';
    document.head.appendChild(script);

    script.onload = () => {
        const tables = document.querySelectorAll('table.table:not(.no-export)');
        tables.forEach(table => {
            // Find a suitable container to prepend the button
            let container = table.closest('.table-responsive');
            if (!container) container = table;
            
            // Prevent adding multiple buttons if script runs again
            if (container.parentNode.querySelector('.excel-export-btn-wrap')) return;

            // Create export button
            const btnWrap = document.createElement('div');
            btnWrap.className = 'd-flex justify-content-end mb-2 excel-export-btn-wrap';
            const btn = document.createElement('button');
            btn.className = 'btn btn-sm btn-success shadow-sm';
            btn.innerHTML = '<i class="fas fa-file-excel me-1"></i> تصدير إكسيل';
            btnWrap.appendChild(btn);
            
            container.parentNode.insertBefore(btnWrap, container);
            
            // On Click
            btn.addEventListener('click', async () => {
                const data = extractTableData(table);
                if (data.length <= 1) {
                    alert('لا يوجد بيانات كافية للتصدير');
                    return;
                }
                
                const workbook = new ExcelJS.Workbook();
                const worksheet = workbook.addWorksheet('البيانات', {
                    views: [{ rightToLeft: true }]
                });
                
                worksheet.addRows(data);
                
                // Styling Header
                const headerRow = worksheet.getRow(1);
                headerRow.height = 30;
                headerRow.eachCell((cell, colNumber) => {
                    cell.fill = {
                        type: 'pattern',
                        pattern: 'solid',
                        fgColor: { argb: 'FF16324F' }
                    };
                    cell.font = { color: { argb: 'FFFFFFFF' }, bold: true, size: 12, name: 'Cairo' };
                    cell.alignment = { vertical: 'middle', horizontal: 'center' };
                    cell.border = {
                        top: { style: 'thin', color: { argb: 'FF000000' } },
                        left: { style: 'thin', color: { argb: 'FF000000' } },
                        bottom: { style: 'thin', color: { argb: 'FF000000' } },
                        right: { style: 'thin', color: { argb: 'FF000000' } }
                    };
                    
                    // Auto width approx based on header text
                    const col = worksheet.getColumn(colNumber);
                    col.width = Math.max(20, (cell.value ? cell.value.toString().length * 1.5 : 20));
                });
                
                // Style Data Cells
                for (let i = 2; i <= data.length; i++) {
                    const row = worksheet.getRow(i);
                    row.height = 25;
                    row.eachCell((cell) => {   
                        cell.font = { name: 'Cairo', size: 11 };
                        cell.alignment = { vertical: 'middle', horizontal: 'center' };
                        cell.border = {
                            top: { style: 'thin', color: { argb: 'FFCCCCCC' } },
                            left: { style: 'thin', color: { argb: 'FFCCCCCC' } },
                            bottom: { style: 'thin', color: { argb: 'FFCCCCCC' } },
                            right: { style: 'thin', color: { argb: 'FFCCCCCC' } }
                        };
                        // Alternate row bg
                        if (i % 2 === 0) {
                            cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFF9FAFB' } };
                        }
                    });
                }
                
                // Download
                const buffer = await workbook.xlsx.writeBuffer();
                const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
                
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                const dateStr = new Date().toISOString().split('T')[0];
                a.download = `تصدير_بيانات_${dateStr}.xlsx`;
                a.click();
                window.URL.revokeObjectURL(url);
            });
        });
    };

    function extractTableData(table) {
        const data = [];
        const rows = table.querySelectorAll('tr');
        
        rows.forEach(tr => {
            // Skip hidden rows or template rows
            if (tr.classList.contains('d-none') || tr.style.display === 'none' || tr.closest('template')) return;
            
            const rowData = [];
            const cells = tr.querySelectorAll('th, td');
            
            let hasContent = false;
            cells.forEach(cell => {
                let val = '';
                const input = cell.querySelector('input:not([type="hidden"]):not([type="button"]):not([type="checkbox"])');
                const select = cell.querySelector('select');
                
                if (input) {
                    val = input.value;
                } else if (select) {
                    val = select.options[select.selectedIndex]?.text || '';
                } else {
                    val = cell.innerText.trim();
                }
                rowData.push(val);
                if (val) hasContent = true;
            });
            
            if (hasContent || tr.querySelector('th')) {
                data.push(rowData);
            }
        });
        
        // Remove columns that are for actions or empty
        if (data.length > 0) {
            const headers = data[0];
            const skipIndices = new Set();
            headers.forEach((h, i) => {
                if (h.includes('الإجراءات') || h === '') {
                    skipIndices.add(i);
                }
            });
            
            return data.map(row => row.filter((_, i) => !skipIndices.has(i)));
        }
        
        return data;
    }
});
