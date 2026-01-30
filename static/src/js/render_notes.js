/** @odoo-module **/

import { Component, onMounted } from "@odoo/owl";

export class NotesRenderer extends Component {
    setup() {
        onMounted(() => {
            this.renderNotesFields();
        });
    }
    
    renderNotesFields() {
        const notesCells = document.querySelectorAll('td[data-notes] .js-notes-content');
        notesCells.forEach(container => {
            const td = container.closest('td[data-notes]');
            const notes = td.getAttribute('data-notes');
            if (notes) {
                container.innerHTML = notes;
            }
        });
    }
}