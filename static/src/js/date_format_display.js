/** @odoo-module **/

const PEEPL_MODELS = ['peepl.weekly.report', 'peepl.pic.overview', 'peepl.user.assignment', 'peepl.field.template', 'peepl.weekly.report.bod', 'peepl.division'];

function isPeeplListView(element) {
    const listView = element.closest('.o_list_view');
    const kanbanView = element.closest('.o_kanban_view');
    const view = listView || kanbanView;
    if (!view) return false;
    const modelAttr = view.getAttribute('data-resModel') || view.querySelector('[data-resModel]')?.getAttribute('data-resModel');
    return modelAttr && PEEPL_MODELS.includes(modelAttr);
}

// Format all date inputs to dd-mm-yyyy display
function formatDateInputs() {
    // Format all date field containers
    const dateFields = document.querySelectorAll('.o_field_date');
    
    dateFields.forEach(field => {
        if (!isPeeplListView(field)) return;
        
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
