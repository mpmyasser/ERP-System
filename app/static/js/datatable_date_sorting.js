/**
 * DataTables Date Sorting Plugin for Arabic HR System
 * ===================================================
 * ظٹطھط¹ط±ظپ طھظ„ظ‚ط§ط¦ظٹط§ظ‹ ط¹ظ„ظ‰ ط£ط¹ظ…ط¯ط© ط§ظ„طھظˆط§ط±ظٹط® ظˆظٹظپط±ط²ظ‡ط§ ط¨ط´ظƒظ„ طµط­ظٹط­ ط²ظ…ظ†ظٹط§ظ‹ ظˆظ„ظٹط³ ظ†طµظٹط§ظ‹
 * 
 * Supported Formats:
 * - DD/MM/YYYY (Display format for users)
 * - YYYY-MM-DD (Database/API format)
 * - DD-MM-YYYY (Alternative format)
 * - YYYY-MM-DD HH:MM (DateTime format)
 */

(function($) {
    'use strict';

    // ===============================================
    // Date Type Detection
    // ===============================================
    
    /**
     * ظƒط´ظپ ط£ط¹ظ…ط¯ط© ط§ظ„طھظˆط§ط±ظٹط® طھظ„ظ‚ط§ط¦ظٹط§ظ‹
     * ظٹطھظ… طھط´ط؛ظٹظ„ ظ‡ط°ط§ ظ‚ط¨ظ„ DataTables initialization
     */
    $.fn.dataTable.ext.type.detect.unshift(function(data) {
        // طھظ†ط¸ظٹظپ ط§ظ„ط¨ظٹط§ظ†ط§طھ ظ…ظ† HTML tags ظˆط§ظ„ظپط±ط§ط؛ط§طھ
        const cleanData = (data || '').toString().replace(/<[^>]*>/g, '').trim();
        
        if (!cleanData || cleanData === '' || cleanData === '-') {
            return null;
        }
        
        // Pattern 1: DD/MM/YYYY or DD-MM-YYYY
        if (/^\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4}/.test(cleanData)) {
            return 'date-dd-mm-yyyy';
        }
        
        // Pattern 2: YYYY-MM-DD or YYYY/MM/DD
        if (/^\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2}/.test(cleanData)) {
            return 'date-yyyy-mm-dd';
        }
        
        // Pattern 3: YYYY-MM-DD HH:MM or YYYY-MM-DD HH:MM:SS
        if (/^\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2}\s+\d{1,2}:\d{2}/.test(cleanData)) {
            return 'date-yyyy-mm-dd-time';
        }
        
        return null;
    });

    // ===============================================
    // Sorting Functions
    // ===============================================

    /**
     * Pre-processing ظ„ظ„طھظˆط§ط±ظٹط® ط¨طµظٹط؛ط© DD/MM/YYYY
     * ظٹط­ظˆظ„ ط§ظ„طھط§ط±ظٹط® ط¥ظ„ظ‰ timestamp ظ„ظ„ظ…ظ‚ط§ط±ظ†ط©
     */
    $.fn.dataTable.ext.type.order['date-dd-mm-yyyy-pre'] = function(data) {
        const cleanData = (data || '').toString().replace(/<[^>]*>/g, '').trim();
        
        if (!cleanData || cleanData === '' || cleanData === '-') {
            return 0; // ظ‚ظٹظ…ط© ط§ظپطھط±ط§ط¶ظٹط© ظ„ظ„ط¨ظٹط§ظ†ط§طھ ط§ظ„ظپط§ط±ط؛ط©
        }
        
        try {
            // طھظ‚ط³ظٹظ… ط§ظ„طھط§ط±ظٹط®
            const parts = cleanData.split(/[\/\-]/);
            
            if (parts.length !== 3) {
                return 0;
            }
            
            const day = parseInt(parts[0], 10);
            const month = parseInt(parts[1], 10) - 1; // JavaScript months are 0-indexed
            const year = parseInt(parts[2], 10);
            
            // ط§ظ„طھط­ظ‚ظ‚ ظ…ظ† طµط­ط© ط§ظ„ظ‚ظٹظ…
            if (isNaN(day) || isNaN(month) || isNaN(year)) {
                return 0;
            }
            
            if (year < 1900 || year > 2100) {
                return 0;
            }
            
            // ط¥ظ†ط´ط§ط، Date object ظˆط¥ط±ط¬ط§ط¹ timestamp
            const dateObj = new Date(year, month, day);
            return dateObj.getTime();
        } catch (e) {
            console.warn('Error parsing date (DD/MM/YYYY):', cleanData, e);
            return 0;
        }
    };

    /**
     * Pre-processing ظ„ظ„طھظˆط§ط±ظٹط® ط¨طµظٹط؛ط© YYYY-MM-DD
     */
    $.fn.dataTable.ext.type.order['date-yyyy-mm-dd-pre'] = function(data) {
        const cleanData = (data || '').toString().replace(/<[^>]*>/g, '').trim();
        
        if (!cleanData || cleanData === '' || cleanData === '-') {
            return 0;
        }
        
        try {
            // JavaScript Date constructor ظٹط¯ط¹ظ… YYYY-MM-DD ط¨ط´ظƒظ„ ط£طµظ„ظٹ
            const dateObj = new Date(cleanData);
            
            if (isNaN(dateObj.getTime())) {
                return 0;
            }
            
            return dateObj.getTime();
        } catch (e) {
            console.warn('Error parsing date (YYYY-MM-DD):', cleanData, e);
            return 0;
        }
    };

    /**
     * Pre-processing ظ„ظ„طھظˆط§ط±ظٹط® ظ…ط¹ ط§ظ„ظˆظ‚طھ YYYY-MM-DD HH:MM
     */
    $.fn.dataTable.ext.type.order['date-yyyy-mm-dd-time-pre'] = function(data) {
        const cleanData = (data || '').toString().replace(/<[^>]*>/g, '').trim();
        
        if (!cleanData || cleanData === '' || cleanData === '-') {
            return 0;
        }
        
        try {
            // ظپطµظ„ ط§ظ„طھط§ط±ظٹط® ظˆط§ظ„ظˆظ‚طھ
            const parts = cleanData.split(/\s+/);
            const datePart = parts[0];
            const timePart = parts[1] || '00:00:00';
            
            // ط¯ظ…ط¬ ط§ظ„طھط§ط±ظٹط® ظˆط§ظ„ظˆظ‚طھ ظپظٹ طµظٹط؛ط© ISO
            const isoString = datePart + 'T' + timePart;
            const dateObj = new Date(isoString);
            
            if (isNaN(dateObj.getTime())) {
                return 0;
            }
            
            return dateObj.getTime();
        } catch (e) {
            console.warn('Error parsing datetime:', cleanData, e);
            return 0;
        }
    };

    // ===============================================
    // Helper Functions
    // ===============================================

    /**
     * ط¯ط§ظ„ط© ظ…ط³ط§ط¹ط¯ط© ظ„طھط­ظˆظٹظ„ ط§ظ„طھط§ط±ظٹط® ظ…ظ† DD/MM/YYYY ط¥ظ„ظ‰ YYYY-MM-DD
     * ظ„ظ„ط§ط³طھط®ط¯ط§ظ… ط¹ظ†ط¯ ط¥ط±ط³ط§ظ„ ط§ظ„ط¨ظٹط§ظ†ط§طھ ط¥ظ„ظ‰ Backend
     */
    window.convertDateToISO = function(dateString) {
        if (!dateString || dateString === '' || dateString === '-') {
            return null;
        }
        
        const parts = dateString.split(/[\/\-]/);
        
        if (parts.length !== 3) {
            return null;
        }
        
        const day = parts[0].padStart(2, '0');
        const month = parts[1].padStart(2, '0');
        const year = parts[2];
        
        return `${year}-${month}-${day}`;
    };

    /**
     * ط¯ط§ظ„ط© ظ…ط³ط§ط¹ط¯ط© ظ„طھط­ظˆظٹظ„ ط§ظ„طھط§ط±ظٹط® ظ…ظ† YYYY-MM-DD ط¥ظ„ظ‰ DD/MM/YYYY
     * ظ„ظ„ط§ط³طھط®ط¯ط§ظ… ط¹ظ†ط¯ ط¹ط±ط¶ ط§ظ„ط¨ظٹط§ظ†ط§طھ ظ„ظ„ظ…ط³طھط®ط¯ظ…
     */
    window.convertDateToDisplay = function(dateString) {
        if (!dateString || dateString === '' || dateString === '-') {
            return '';
        }
        
        const parts = dateString.split(/[\/\-]/);
        
        if (parts.length !== 3) {
            return dateString;
        }
        
        // ط¥ط°ط§ ظƒط§ظ†طھ ط§ظ„ط³ظ†ط© ظپظٹ ط§ظ„ط¨ط¯ط§ظٹط© (YYYY-MM-DD)
        if (parts[0].length === 4) {
            return `${parts[2]}/${parts[1]}/${parts[0]}`;
        }
        
        // ط¥ط°ط§ ظƒط§ظ†طھ ط¨ط§ظ„ظپط¹ظ„ DD/MM/YYYY
        return dateString;
    };

    /**
     * ط¯ط§ظ„ط© ظ„طھظ‡ظٹط¦ط© ط§ظ„ظپط±ط² ط§ظ„طھظ„ظ‚ط§ط¦ظٹ ظ„ظ„طھظˆط§ط±ظٹط®
     * ظٹظ…ظƒظ† ط§ط³طھط¯ط¹ط§ط¤ظ‡ط§ ط¨ط¹ط¯ طھط­ظ…ظٹظ„ DataTable
     */
    window.initDateColumnSorting = function(tableId) {
        const table = $('#' + tableId);

        if (!table.length || !$.fn.DataTable.isDataTable(table)) {
            return;
        }

        // No manual column type override needed.
        // DataTables auto-detection is already configured above.
    };


})(jQuery);
