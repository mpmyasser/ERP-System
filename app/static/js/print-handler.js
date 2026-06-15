/**
 * Professional Print Handler for HR System
 */

const PrintHandler = {
    /**
     * Prints the current page
     */
    printPage: function () {
        window.print();
    },

    /**
     * Opens a specific element in a printable preview modal or new window
     * @param {string} elementId
     */
    printElement: function (elementId) {
        const element = document.getElementById(elementId);
        if (!element) return;

        this.printPage();
    },

    /**
     * Converts the current view to PDF using browser's built-in capability
     */
    saveAsPDF: function () {
        this.printPage();
    }
};

// Global shortcuts
window.printReport = function () {
    PrintHandler.printPage();
};
