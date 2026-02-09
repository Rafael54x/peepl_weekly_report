/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { onMounted } from "@odoo/owl";

patch(FormController.prototype, {
    setup() {
        super.setup();
        
        // Hide breadcrumb for weekly report forms - instant
        if (this.props.resModel === 'peepl.weekly.report') {
            onMounted(() => {
                const breadcrumb = document.querySelector('.o_control_panel .breadcrumb');
                if (breadcrumb) {
                    breadcrumb.style.display = 'none';
                }
            });
        }
    }
});
