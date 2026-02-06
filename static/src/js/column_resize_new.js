/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";

patch(ListRenderer.prototype, {
    async _renderView() {
        const result = await super._renderView();
        
        setTimeout(() => {
            this._addColumnResizers();
        }, 100);
        
        return result;
    },
    
    _addColumnResizers() {
        const headers = this.el.querySelectorAll('.peepl_weekly_report_list th:not(:last-child)');
        
        headers.forEach((th, index) => {
            if (th.querySelector('.col-resizer')) return;
            
            // Create resizer element
            const resizer = document.createElement('div');
            resizer.className = 'col-resizer';
            th.appendChild(resizer);
            
            let startX;
            let startWidth;
            
            resizer.addEventListener('mousedown', (e) => {
                e.preventDefault();
                
                startX = e.pageX;
                startWidth = th.offsetWidth;
                
                document.addEventListener('mousemove', onMouseMove);
                document.addEventListener('mouseup', onMouseUp);
            });
            
            function onMouseMove(e) {
                const diff = e.pageX - startX;
                const newWidth = Math.max(60, startWidth + diff);
                
                th.style.width = newWidth + 'px';
                th.style.minWidth = newWidth + 'px';
                
                // Apply width to all td in same column
                const table = th.closest('.peepl_weekly_report_list');
                if (table) {
                    table.querySelectorAll(`tr td:nth-child(${index + 1})`).forEach(td => {
                        td.style.width = newWidth + 'px';
                    });
                }
            }
            
            function onMouseUp() {
                document.removeEventListener('mousemove', onMouseMove);
                document.removeEventListener('mouseup', onMouseUp);
            }
        });
    }
});