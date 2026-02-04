/** @odoo-module **/

function updateProgressBarColors() {
    // Wait a bit for DOM to be fully rendered
    setTimeout(() => {
        const progressBars = document.querySelectorAll('.o_field_widget[name="progress"]');
        
        progressBars.forEach(function(progressBar) {
            const percentageElement = progressBar.querySelector('.o_progressbar_value');
            if (percentageElement) {
                const percentage = parseInt(percentageElement.textContent) || 0;
                console.log('Found progress:', percentage); // Debug log
                
                // Remove existing data attributes
                progressBar.removeAttribute('data-progress-low');
                progressBar.removeAttribute('data-progress-medium');
                progressBar.removeAttribute('data-progress-high');
                
                // Add appropriate data attribute based on percentage
                if (percentage >= 0 && percentage <= 29) {
                    progressBar.setAttribute('data-progress-low', '');
                    console.log('Set low for', percentage);
                } else if (percentage >= 30 && percentage <= 89) {
                    progressBar.setAttribute('data-progress-medium', '');
                    console.log('Set medium for', percentage);
                } else if (percentage >= 90) {
                    progressBar.setAttribute('data-progress-high', '');
                    console.log('Set high for', percentage);
                }
            }
        });
    }, 100);
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', updateProgressBarColors);
} else {
    updateProgressBarColors();
}

// Update when content changes
if (typeof MutationObserver !== 'undefined' && document.body) {
    const observer = new MutationObserver(function(mutations) {
        updateProgressBarColors();
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}