/**
 * Excel Export Formatting Utility
 * ================================
 * General formatting for all Excel exports across the application
 * Handles both DataTables (JSZip) and server-side (openpyxl) exports
 */

// دالة عامة لتنسيق ملفات Excel المُصدَّرة من DataTables
function formatExcelExport(xlsx) {
    try {
        // Check if this is a JSZip object (from DataTables)
        if (!xlsx || typeof xlsx !== 'object') {
            console.warn('Invalid xlsx object');
            return;
        }

        // Check if xlsx.folder exists (JSZip method)
        if (typeof xlsx.folder !== 'function' || typeof xlsx.file !== 'function') {
            console.warn('Not a JSZip object - may be server-side export');
            return;
        }

        var worksheetFiles = [];
        
        // Find all worksheet files - use try/catch for safety
        try {
            var worksheetsFolder = xlsx.folder('xl/worksheets');
            if (worksheetsFolder) {
                worksheetsFolder.forEach(function(file) {
                    if (file && file.name && file.name.match(/sheet\d+\.xml$/)) {
                        worksheetFiles.push(file.name);
                    }
                });
            }
        } catch (e) {
            console.warn('Could not access worksheets folder:', e);
            return;
        }

        // Process each worksheet
        worksheetFiles.forEach(function(sheetFile) {
            try {
                var sheetContent = xlsx.file(sheetFile).asText();
                var parser = new DOMParser();
                var xmlDoc = parser.parseFromString(sheetContent, 'text/xml');
                
                // Check for parse errors
                if (xmlDoc.getElementsByTagName('parsererror').length > 0) {
                    console.error('XML parsing error in sheet:', sheetFile);
                    return;
                }
                
                var rows = xmlDoc.getElementsByTagName('row');
                
                for (var rowIndex = 0; rowIndex < rows.length; rowIndex++) {
                    var cells = rows[rowIndex].getElementsByTagName('c');
                    
                    for (var cellIndex = 0; cellIndex < cells.length; cellIndex++) {
                        var cell = cells[cellIndex];
                        var vElement = cell.getElementsByTagName('v')[0];
                        
                        if (!vElement) continue;
                        
                        var cellValue = vElement.textContent;
                        
                        // Skip header row (row 1, index 0)
                        if (rowIndex === 0) {
                            // Don't modify header
                            continue;
                        }
                        
                        if (cellValue && cellValue.trim()) {
                            // 1. Remove currency symbols and text
                            var cleanValue = cellValue
                                .replace(/\s*جنيه\s*$/i, '')  // Remove 'جنيه'
                                .replace(/\s*EGP\s*$/i, '')    // Remove 'EGP'
                                .replace(/\s*ج\.م\.ع\s*$/i, '') // Remove 'ج.م.ع'
                                .replace(/\s*\$\s*$/i, '')      // Remove '$'
                                .replace(/\s*€\s*$/i, '')       // Remove '€'
                                .replace(/\s*£\s*$/i, '')       // Remove '£'
                                .trim();
                            
                            // 2. Try to parse as number
                            // Remove commas if present
                            var numValue = parseFloat(cleanValue.replace(/,/g, ''));
                            
                            if (!isNaN(numValue) && cleanValue !== '' && cleanValue !== '-') {
                                // Update cell value with formatted number
                                vElement.textContent = numValue.toFixed(2);
                                
                                // Set cell type to number
                                cell.setAttribute('t', 'n');
                            }
                        }
                    }
                }
                
                // Write modified XML back to zip
                var serializer = new XMLSerializer();
                var modifiedXml = serializer.serializeToString(xmlDoc);
                xlsx.file(sheetFile, modifiedXml);
                
            } catch (sheetError) {
                console.error('Error processing sheet:', sheetFile, sheetError);
            }
        });
        
    } catch (error) {
        console.error('Error formatting Excel export:', error);
    }
}

