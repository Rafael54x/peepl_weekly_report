/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";
import { onMounted } from "@odoo/owl";

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        
        if (this.props.resModel === "peepl.weekly.report") {
            onMounted(() => {
                const saveButton = document.querySelector('.o_form_button_save');
                if (saveButton) {
                    saveButton.style.display = 'none';
                }
                
                // Move cancel button next to action menu only when creating new record
                if (!this.props.resId) {
                    const cancelButton = document.querySelector('.o_form_button_cancel');
                    const actionMenu = document.querySelector('.o_cp_action_menus');
                    if (cancelButton && actionMenu) {
                        actionMenu.parentNode.insertBefore(cancelButton, actionMenu.nextSibling);
                    }
                }
            });
        }
    },
});
