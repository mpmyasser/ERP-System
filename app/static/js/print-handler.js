/**
 * Professional Print Handler for HR System
 */

const PrintHandler = {
    /**
     * Prints the current page with optional classes
     * @param {string} orientation - 'portrait' or 'landscape'
     */
    printPage: function (orientation = 'portrait') {
        const body = document.body;

        // Add orientation class
        if (orientation === 'landscape') {
            body.classList.add('print-landscape');
        } else {
            body.classList.remove('print-landscape');
        }

        // Trigger browser print
        window.print();

        // Clean up
        body.classList.remove('print-landscape');
    },

    /**
     * Opens a specific element in a printable preview modal or new window
     * @param {string} elementId 
     */
    printElement: function (elementId) {
        const element = document.getElementById(elementId);
        if (!element) return;

        // For simplicity, we'll use window.print() and hide other elements via CSS
        // Developers can add more complex logic here for isolated printing
        this.printPage();
    },

    /**
     * Converts the current view to PDF using browser's built-in capability
     */
    saveAsPDF: function () {
        // Most modern browsers' print dialog allows saving as PDF
        this.printPage();
    }
};

// Global shortcuts
window.printReport = function (orientation) {
    PrintHandler.printPage(orientation);
};
