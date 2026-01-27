/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";

patch(FormController.prototype, {
    async saveButtonClicked(params = {}) {
        const resModel = this.props.resModel;
        await super.saveButtonClicked(...arguments);
        if (resModel === 'peepl.field.template') {
            window.location.reload();
        }
    }
});
