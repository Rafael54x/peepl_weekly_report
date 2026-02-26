/** @odoo-module **/

// Format all date inputs to dd-mm-yyyy display
function formatDateInputs() {
    // Format all date field containers
    const dateFields = document.querySelectorAll('.o_field_date');
    
    dateFields.forEach(field => {
        // Format input fields
        const input = field.querySelector('input');
        if (input && input.value && !input.dataset.formatted) {
            const date = new Date(input.value);
            if (!isNaN(date.getTime())) {
                const day = String(date.getDate()).padStart(2, '0');
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const year = date.getFullYear();
                const formatted = `${day}-${month}-${year}`;
                
                input.dataset.formatted = 'true';
                input.dataset.realValue = input.value;
                input.type = 'text';
                input.value = formatted;
                
                input.addEventListener('focus', function(e) {
                    e.stopPropagation();
                    this.type = 'date';
                    this.value = this.dataset.realValue || '';
                }, true);
                
                input.addEventListener('blur', function() {
                    if (this.value) {
                        this.dataset.realValue = this.value;
                        const newDate = new Date(this.value);
                        if (!isNaN(newDate.getTime())) {
                            const day = String(newDate.getDate()).padStart(2, '0');
                            const month = String(newDate.getMonth() + 1).padStart(2, '0');
                            const year = newDate.getFullYear();
                            this.type = 'text';
                            this.value = `${day}-${month}-${year}`;
                        }
                    } else {
                        this.type = 'date';
                        this.dataset.formatted = '';
                    }
                });
            }
        }
        
        // Format readonly display text - always check
        const textNodes = [];
        const walker = document.createTreeWalker(field, NodeFilter.SHOW_TEXT, null, false);
        let node;
        while (node = walker.nextNode()) {
            if (node.nodeValue.trim()) {
                textNodes.push(node);
            }
        }
        
        textNodes.forEach(textNode => {
            const text = textNode.nodeValue.trim();
            if (text.match(/[a-zA-Z]/) && text.length > 3 && text.length < 50) {
                let dateText = text;
                if (!text.match(/\d{4}/)) {
                    dateText = text + ', ' + new Date().getFullYear();
                }
                const date = new Date(dateText);
                if (!isNaN(date.getTime())) {
                    const day = String(date.getDate()).padStart(2, '0');
                    const month = String(date.getMonth() + 1).padStart(2, '0');
                    const year = date.getFullYear();
                    const formatted = `${day}-${month}-${year}`;
                    if (textNode.nodeValue !== formatted) {
                        textNode.nodeValue = formatted;
                    }
                }
            }
        });
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(formatDateInputs, 50);
        setTimeout(formatDateInputs, 100);
        setTimeout(formatDateInputs, 500);
        setTimeout(formatDateInputs, 1000);
        setTimeout(formatDateInputs, 2000);
        setTimeout(formatDateInputs, 3000);
        
        const observer = new MutationObserver(() => {
            formatDateInputs();
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            characterData: true
        });
    });
} else {
    setTimeout(formatDateInputs, 50);
    setTimeout(formatDateInputs, 100);
    setTimeout(formatDateInputs, 500);
    setTimeout(formatDateInputs, 1000);
    setTimeout(formatDateInputs, 2000);
    setTimeout(formatDateInputs, 3000);
    
    const observer = new MutationObserver(() => {
        formatDateInputs();
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true,
        characterData: true
    });
}

// Listen for Odoo field changes
document.addEventListener('click', () => {
    setTimeout(formatDateInputs, 100);
});

document.addEventListener('keyup', (e) => {
    if (e.key === 'z' && (e.ctrlKey || e.metaKey)) {
        setTimeout(formatDateInputs, 50);
        setTimeout(formatDateInputs, 100);
        setTimeout(formatDateInputs, 200);
        setTimeout(formatDateInputs, 500);
        setTimeout(formatDateInputs, 1000);
    }
});
