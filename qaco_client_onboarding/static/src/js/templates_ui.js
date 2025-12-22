/** @odoo-module */

import { patch } from '@web/core/utils/patch';
import { FormController } from '@web/views/form/form_controller';
import rpc from 'web.rpc';
import core from 'web.core';

var _t = core._t;

patch(FormController.prototype, 'qaco_client_onboarding.templates_ui', {
    events: Object.assign({}, FormController.prototype.events, {
        // click anywhere on a list row to toggle the checkbox for easier selection
        'click tr.o_data_row': '_onTemplateRowClick',
        // double-click a template row to attach it directly to this onboarding
        'dblclick tr.o_data_row': '_onTemplateRowDoubleClick',
        // keyboard support for rows
        'keydown tr.o_data_row': '_onTemplateRowKeydown',
    }),

    // Ensure rows are keyboard focusable when clicked / interacted
    _ensureRowFocusable: function (row) {
        if (!row) { return; }
        if (!row.hasAttribute('tabindex')) {
            try { row.setAttribute('tabindex', '0'); } catch (e) { /* ignore */ }
        }
    },

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
        // Make row keyboard-focusable
        this._ensureRowFocusable(row);
        // Fire change event for any listeners
        var changeEvent = new Event('change', { bubbles: true });
        checkbox.dispatchEvent(changeEvent);
    },

    _onTemplateRowDoubleClick: function (ev) {
        var self = this;
        var target = ev.target;
        var row = target.closest('tr.o_data_row');
        if (!row) { return; }
        // ensure we are in the Template Library list (don't trigger from other lists)
        var libField = row.closest('[data-field="template_library_rel_ids"]');
        if (!libField) { return; }

        // get template id from the row's checkbox or data attributes
        var checkbox = row.querySelector('input.o_list_record_selector');
        var tplId = null;
        if (checkbox) {
            tplId = Number(checkbox.dataset.id || checkbox.value || row.dataset.id || row.getAttribute('data-id'));
        } else {
            tplId = Number(row.dataset.id || row.getAttribute('data-id'));
        }
        if (!tplId) { return; }

        // confirm onboarding id
        var recordId = this.model.get(this.handle).data.id;
        if (!recordId) { return; }

        // show busy spinner on row
        row.classList.add('o-row-busy');
        // call server method on the template to attach it to the onboarding using context
        // show a small notification on success/failure
        try {
            rpc.query({
                model: 'qaco.onboarding.template.document',
                method: 'action_attach_to_onboarding',
                args: [[tplId]],
                context: { onboarding_id: recordId },
            }).then(function (action) {
                if (action) {
                    self.trigger_up('do_action', { action: action });
                } else {
                    try {
                        self.displayNotification({ title: _t('Attached'), message: _t('Template attached.'), type: 'success' });
                    } catch (e) {
                        self.env.services.notification.add(_t('Template attached.'), { type: 'success' });
                    }
                }
            }).catch(function (err) {
                console.error(err);
                try {
                    self.displayNotification({ title: _t('Error'), message: _t('Could not attach template.'), type: 'danger' });
                } catch (e) {
                    self.env.services.notification.add(_t('Could not attach template.'), { type: 'danger' });
                }
            }).finally(function () {
                row.classList.remove('o-row-busy');
            });
        } catch (err) {
            console.error(err);
            row.classList.remove('o-row-busy');
        }
    },

    _onTemplateRowKeydown: function (ev) {
        var key = ev.key || ev.keyCode;
        var target = ev.target;
        var row = target.closest && target.closest('tr.o_data_row');
        if (!row) { return; }
        // Space toggles selection
        if (key === ' ' || key === 'Spacebar' || key === 32) {
            ev.preventDefault();
            var checkbox = row.querySelector('input.o_list_record_selector');
            if (!checkbox) { return; }
            checkbox.checked = !checkbox.checked;
            var changeEvent = new Event('change', { bubbles: true });
            checkbox.dispatchEvent(changeEvent);
            this._ensureRowFocusable(row);
            return;
        }
        // Enter triggers attach (same as double-click)
        if (key === 'Enter' || key === 13) {
            ev.preventDefault();
            // reuse double-click handler logic
            this._onTemplateRowDoubleClick({ target: row });
            return;
        }
    },
});
