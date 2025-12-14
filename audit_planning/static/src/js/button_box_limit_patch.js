/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { FormButtonBox } from "@web/views/form/button_box/button_box";

// Raise smart-button inline limit so buttons render without the "More" dropdown.
const superSetup = FormButtonBox.prototype.setup;
patch(FormButtonBox.prototype, "audit_planning.button_box_limit", {
    setup() {
        superSetup.call(this);
        this.buttonLimit = 20;
    },
});
