// Input Sanitizer: trims whitespace for numeric inputs and normalizes numeric values
(function () {
    function sanitizeNumberInputs(root) {
        root = root || document;
        try {
            const inputs = root.querySelectorAll('input[type="number"]');
            inputs.forEach(i => {
                if (i && typeof i.value === 'string' && (i.value.trim() !== i.value)) {
                    i.value = i.value.trim();
                }
            });
        } catch (e) { console.error('sanitizeNumberInputs error', e); }
    }

    document.addEventListener('DOMContentLoaded', function () {
        sanitizeNumberInputs(document);

        // Observe for dynamically added inputs (e.g., table rows)
        const mo = new MutationObserver(function (mutations) {
            mutations.forEach(m => {
                if (m.addedNodes && m.addedNodes.length > 0) {
                    m.addedNodes.forEach(node => {
                        try {
                            if (node.nodeType !== 1) return;
                            if (node.matches && node.matches('input[type="number"]')) {
                                sanitizeNumberInputs(node.parentNode || document);
                            } else if (node.querySelectorAll) {
                                const found = node.querySelectorAll('input[type="number"]');
                                if (found && found.length) sanitizeNumberInputs(node);
                            }
                        } catch (e) {}
                    });
                }
            });
        });
        mo.observe(document.body, { childList: true, subtree: true });
    });
})();