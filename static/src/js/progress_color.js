/** @odoo-module **/

function applyProgressColor(root = document) {
    root.querySelectorAll('.o_progressbar_value').forEach(bar => {
        const value = parseInt(bar.textContent || bar.dataset.value || 0, 10);

        bar.classList.remove('is-red', 'is-yellow', 'is-green');

        if (value >= 1 && value <= 29) {
            bar.classList.add('is-red');
        } else if (value >= 30 && value <= 89) {
            bar.classList.add('is-yellow');
        } else if (value >= 90) {
            bar.classList.add('is-green');
        }
    });
}

// Initial run when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => applyProgressColor());
} else {
    applyProgressColor();
}

// Re-apply when Odoo re-renders
if (typeof MutationObserver !== 'undefined' && document.body) {
    const observer = new MutationObserver(() => applyProgressColor());
    observer.observe(document.body, {
        childList: true,
        subtree: true,
    });
}