/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { patch } from "@web/core/utils/patch";

patch(ListController.prototype, {
    setup() {
        super.setup();
    },
    async createRecord() {
        if (this.props.resModel === "peepl.weekly.report.department") {
            return this.env.services.action.doAction({
                type: "ir.actions.act_window",
                name: "New Department",
                res_model: "hr.department",
                views: [[false, "form"]],
                target: "current",
            });
        }
        return super.createRecord(...arguments);
    }
});

patch(KanbanController.prototype, {
    setup() {
        super.setup();
    },
    async createRecord() {
        if (this.props.resModel === "peepl.weekly.report.department") {
            return this.env.services.action.doAction({
                type: "ir.actions.act_window",
                name: "New Department",
                res_model: "hr.department",
                views: [[false, "form"]],
                target: "current",
            });
        }
        return super.createRecord(...arguments);
    }
});
