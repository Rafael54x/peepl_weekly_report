/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";

patch(FormController.prototype, {
    async saveButtonClicked(params = {}) {
        const record = this.model.root;
        const oldAccess = record.data.weekly_report_access;
        
        const result = await super.saveButtonClicked(params);
        
        // Check if we're on res.users form and weekly_report_access changed
        if (record.resModel === 'res.users' && oldAccess !== record.data.weekly_report_access) {
            // Reload the form to show updated checkboxes
            await this.model.root.load();
        }
        
        return result;
    },
});
