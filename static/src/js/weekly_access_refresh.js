/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(FormController.prototype, {
    async _onFieldChanged(ev) {
        await super._onFieldChanged(ev);
        
        // Check if the changed field is weekly_report_access
        if (ev.detail && ev.detail.changes && ev.detail.changes.weekly_report_access !== undefined) {
            // Show confirmation dialog
            const result = confirm(_t("Apply changes to Extra Rights? This will refresh the page."));
            
            if (result) {
                // User clicked "OK" - force hard refresh
                setTimeout(() => {
                    window.location.reload(true);
                }, 100);
            }
        }
    }
});