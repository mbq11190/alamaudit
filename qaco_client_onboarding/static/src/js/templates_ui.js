/** @odoo-module */

import { patch } from '@web/core/utils/patch';
import { FormController } from '@web/views/form/form_controller';

patch(FormController.prototype, 'qaco_client_onboarding.templates_ui', {
    events: Object.assign({}, FormController.prototype.events, {
        // click anywhere on a list row to toggle the checkbox for easier selection
        'click tr.o_data_row': '_onTemplateRowClick',
    }),

    _onTemplateRowClick: function (ev) {
        // Avoid toggling if user clicked on a button/link or input
        var target = ev.target;
        if (!target) { return; }
        if (['BUTTON', 'A', 'INPUT', 'LABEL'].indexOf(target.tagName) !== -1) { return; }
        // find nearest row
        var row = target.closest('tr.o_data_row');
        if (!row) { return; }
        var checkbox = row.querySelector('input.o_list_record_selector');
        if (!checkbox) { return; }
        checkbox.checked = !checkbox.checked;
        // Fire change event for any listeners
        var changeEvent = new Event('change', { bubbles: true });
        checkbox.dispatchEvent(changeEvent);
    },
});
