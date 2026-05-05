/**
 * input_sanitizer.js
 * Sanitizes and trims text inputs on submit to prevent accidental whitespace issues.
 */
(function () {
    'use strict';

    document.addEventListener('submit', function (e) {
        const form = e.target;
        if (!form || form.tagName !== 'FORM') return;

        // Trim all text/search inputs before submit
        const inputs = form.querySelectorAll('input[type="text"], input[type="search"], input:not([type])');
        inputs.forEach(function (input) {
            input.value = input.value.trim();
        });
    }, true); // useCapture = true to fire before other handlers

})();
