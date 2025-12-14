/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { FormButtonBox } from "@web/views/form/button_box/button_box";

// Increase smart button inline limit so all phase buttons stay visible without "More" dropdown.
const superSetup = FormButtonBox.prototype.setup;
patch(FormButtonBox.prototype, "audit_planning.button_box_limit", {
    setup() {
        this.buttonLimit = 8;
        superSetup.call(this);
    },
});
