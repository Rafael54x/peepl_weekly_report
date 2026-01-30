/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";

patch(ListRenderer.prototype, {
    async _renderView() {
        const result = await super._renderView();
        
        // Force add resize handles after DOM is ready
        this._forceAddResizeHandles();
        
        return result;
    },
    
    _forceAddResizeHandles() {
        const headers = this.el.querySelectorAll('thead th');
        
        headers.forEach((th, index) => {
            // Skip last column (actions) and already processed
            if (index === headers.length - 1 || th.querySelector('.o_resize')) return;
            
            // Add position relative
            th.classList.add('position-relative');
            
            // Create and add resize handle
            const resizeSpan = document.createElement('span');
            resizeSpan.className = 'o_resize position-absolute top-0 end-0 bottom-0 ps-1 bg-black-25 opacity-0 opacity-50-hover z-1';
            resizeSpan.style.width = '4px';
            resizeSpan.style.cursor = 'col-resize';
            
            th.appendChild(resizeSpan);
        });
    }
});