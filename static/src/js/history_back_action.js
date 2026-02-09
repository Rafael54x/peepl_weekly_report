/** @odoo-module **/

import { registry } from "@web/core/registry";

registry.category("actions").add("history_back", async () => {
    window.history.back();
});
