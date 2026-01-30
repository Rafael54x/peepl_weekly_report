/** @odoo-module **/

import { registry } from "@web/core/registry";
import { FormController } from "@web/views/form/form_controller";
import { ListController } from "@web/views/list/list_controller";
import { patch } from "@web/core/utils/patch";

patch(FormController.prototype, {
    async saveRecord() {
        const result = await super.saveRecord(...arguments);
        
        // Auto-refresh after saving field template
        if (this.props.resModel === 'peepl.field.template') {
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        }
        
        return result;
    }
});

patch(ListController.prototype, {
    async deleteRecords(records) {
        const result = await super.deleteRecords(...arguments);
        
        // Auto-refresh after deleting field template
        if (this.props.resModel === 'peepl.field.template') {
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        }
        
        return result;
    }
});