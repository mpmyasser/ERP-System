/**
 * Filter Persistence System
 * ========================
 * Automatically saves and restores filter selections across the application
 * Uses centralized SettingsManager (with local fallback) to persist filters.
 */

// Configuration for different pages and their filter elements
const FILTER_CONFIG = {
    'employees': {
        storageKey: 'employees_filters',
        elements: {
            'dept-filter': 'department_ids',
            'status-filter': 'status',
            'search': 'search',
            'date-from': 'date_from',
            'date-to': 'date_to',
            'dept-filter-mode': 'dept_filter_mode',
            'job-title-filter': 'job_title'
        }
    },
    'employees_bulk': {
        storageKey: 'employees_bulk_settings',
        elements: {
            'batchHireDate': 'batch_hire_date',
            'batchDept': 'batch_dept'
        }
    },
    'attendance_daily': {
        storageKey: 'attendance_filters',
        elements: {
            'date-picker': 'date',
            'dept-filter': 'department_ids',
            'dept-filter-mode': 'dept_filter_mode'
        }
    },
    'attendance_bulk': {
        storageKey: 'attendance_bulk_settings',
        elements: {
            'batchDate': 'batch_date',
            'batchCheckIn': 'batch_check_in',
            'batchCheckOut': 'batch_check_out'
        }
    },
    'loans': {
        storageKey: 'loans_filters',
        elements: {
            'date-from': 'date_from',
            'date-to': 'date_to',
            'dept-filter': 'department_ids',
            'dept-filter-mode': 'dept_filter_mode'
        }
    },
    'bonuses': {
        storageKey: 'bonuses_filters',
        elements: {
            'date-from': 'date_from',
            'date-to': 'date_to',
            'dept-filter': 'department_ids',
            'dept-filter-mode': 'dept_filter_mode'
        }
    },
    'penalties': {
        storageKey: 'penalties_filters',
        elements: {
            'date-from': 'date_from',
            'date-to': 'date_to',
            'dept-filter': 'department_ids',
            'dept-filter-mode': 'dept_filter_mode'
        }
    },
    'permissions': {
        storageKey: 'permissions_filters',
        elements: {
            'date-from': 'date_from',
            'date-to': 'date_to',
            'dept-filter': 'department_ids',
            'dept-filter-mode': 'dept_filter_mode'
        }
    }
};

function getSettingsUtil() {
    return window.HRSettingsUtil || null;
}

function readStoredObject(key) {
    const util = getSettingsUtil();
    if (!util) return null;
    return util.getObject(key, null);
}

function writeStoredObject(key, value) {
    const util = getSettingsUtil();
    if (!util) return;
    util.setObject(key, value);
}

function removeStoredObject(key) {
    const util = getSettingsUtil();
    if (!util) return;
    util.remove(key);
}

/**
 * Get the current page name from URL
 */
function getCurrentPage() {
    const path = window.location.pathname;
    const pathParts = path.split('/').filter(p => p);

    if (pathParts.length === 0) return 'dashboard';

    // Handle employees submodule
    if (pathParts[0] === 'employees') {
        if (pathParts.length === 1) return 'employees'; // List
        if (pathParts[1] === 'bulk') return 'employees_bulk';
        return null; // Don't persist on create/edit
    }

    // Handle attendance
    if (pathParts[0] === 'attendance') {
        if (pathParts[1] === 'daily') return 'attendance_daily';
        if (pathParts[1] === 'bulk') return 'attendance_bulk';
    }

    // Handle treasury sub-modules
    if (pathParts[0] === 'treasury' && pathParts.length > 1) {
        return pathParts[1];
    }

    return pathParts[0];
}

/**
 * Save filter values to centralized storage
 */
function saveFilters() {
    const currentPage = getCurrentPage();
    if (!currentPage || !FILTER_CONFIG[currentPage]) {
        return; // Page not configured for filter persistence
    }

    const config = FILTER_CONFIG[currentPage];
    const filters = {};

    // Iterate through all configured elements
    for (const [elementId, filterName] of Object.entries(config.elements)) {
        const element = document.getElementById(elementId);
        if (!element) continue;

        // Handle different element types
        if (element.tagName === 'SELECT') {
            if (element.multiple) {
                // Multi-select: save selected values as array
                const selected = Array.from(element.selectedOptions).map(opt => opt.value);
                filters[filterName] = selected;
            } else {
                // Single select: save selected value
                filters[filterName] = element.value;
            }
        } else if (element.tagName === 'INPUT') {
            if (element.type === 'checkbox') {
                filters[filterName] = element.checked;
            } else if (element.type === 'radio') {
                // Only save checked radio
                const checked = document.querySelector(`input[name="${element.name}"]:checked`);
                if (checked) {
                    filters[filterName] = checked.value;
                }
            } else {
                // Text, date, etc.
                filters[filterName] = element.value;
            }
        }
    }

    // Only save if there are non-empty filters
    const hasFilters = Object.values(filters).some(val => {
        if (Array.isArray(val)) return val.length > 0;
        return val && val !== '';
    });

    if (hasFilters) {
        writeStoredObject(config.storageKey, filters);
    } else {
        removeStoredObject(config.storageKey); // Clear if all filters empty
    }
}

/**
 * Restore filter values from centralized storage
 */
function restoreFilters() {
    const currentPage = getCurrentPage();
    if (!currentPage || !FILTER_CONFIG[currentPage]) {
        return; // Page not configured for filter persistence
    }

    const config = FILTER_CONFIG[currentPage];
    const filters = readStoredObject(config.storageKey);

    if (!filters) {
        return; // No saved filters
    }

    try {
        const urlParams = new URLSearchParams(window.location.search);

        // Iterate through all configured elements
        for (const [elementId, filterName] of Object.entries(config.elements)) {
            // Priority to URL parameters: if the parameter is in the URL, don't restore from storage
            if (urlParams.has(filterName)) {
                continue;
            }

            const element = document.getElementById(elementId);
            if (!element || !filters.hasOwnProperty(filterName)) {
                continue;
            }

            const value = filters[filterName];

            // Restore different element types
            if (element.tagName === 'SELECT') {
                if (element.multiple) {
                    // Multi-select: restore array of values
                    const values = Array.isArray(value) ? value : [value];
                    Array.from(element.options).forEach(opt => {
                        opt.selected = values.includes(opt.value);
                    });
                } else {
                    // Single select: restore single value
                    element.value = value;
                }
            } else if (element.tagName === 'INPUT') {
                if (element.type === 'checkbox') {
                    element.checked = value === true || value === 'true';
                } else if (element.type === 'radio') {
                    const radio = document.querySelector(`input[name="${element.name}"][value="${value}"]`);
                    if (radio) {
                        radio.checked = true;
                    }
                } else {
                    // Text, date, etc.
                    element.value = value;
                }
            }
        }
    } catch (error) {
        console.error('Error restoring filters:', error);
    }
}

/**
 * Clear all saved filters for current page
 */
function clearFilters() {
    const currentPage = getCurrentPage();
    if (!currentPage || !FILTER_CONFIG[currentPage]) {
        return;
    }

    const config = FILTER_CONFIG[currentPage];
    removeStoredObject(config.storageKey);
}

/**
 * Initialize filter persistence
 * Call on page load
 */
function initializeFilterPersistence() {
    const currentPage = getCurrentPage();
    if (!currentPage || !FILTER_CONFIG[currentPage]) {
        return; // Page not configured
    }

    // Restore saved filters on page load
    restoreFilters();

    // Set up auto-save on filter changes
    const config = FILTER_CONFIG[currentPage];
    for (const elementId of Object.keys(config.elements)) {
        const element = document.getElementById(elementId);
        if (!element) continue;

        // Add event listeners for different element types
        if (element.tagName === 'SELECT') {
            element.addEventListener('change', saveFilters);
        } else if (element.tagName === 'INPUT') {
            if (element.type === 'checkbox' || element.type === 'radio') {
                element.addEventListener('change', saveFilters);
            } else {
                // For text inputs, save on blur (not on every keystroke)
                element.addEventListener('blur', saveFilters);
                // Or on Enter key for quick save
                element.addEventListener('keypress', function (e) {
                    if (e.key === 'Enter') {
                        saveFilters();
                    }
                });
            }
        }
    }

    // Save filters when page is about to unload (closing tab, etc.)
    window.addEventListener('beforeunload', saveFilters);
}

/**
 * Auto-initialize when DOM is ready
 */
document.addEventListener('DOMContentLoaded', initializeFilterPersistence);

// Also make functions available globally for manual use
window.filterPersistence = {
    save: saveFilters,
    restore: restoreFilters,
    clear: clearFilters,
    initialize: initializeFilterPersistence,
    getCurrentPage: getCurrentPage
};
