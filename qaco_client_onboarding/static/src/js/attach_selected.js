odoo.define('qaco_client_onboarding.attach_selected', function (require) {
    'use strict';

    const FormController = require('web.FormController');
    const rpc = require('web.rpc');
    const core = require('web.core');
    const _t = core._t;

    FormController.include({
        events: Object.assign({}, FormController.prototype.events, {
            'click .o_attach_selected': '_onAttachSelected',
            'input .o_template_search': '_onTemplateSearch',
        }),

        async _onAttachSelected(ev) {
            ev.preventDefault();
            // find the one2many field container
            const fieldEl = this.el.querySelector('[data-field="template_library_rel_ids"]');
            if (!fieldEl) {
                this.displayNotification({title: _t('Error'), message: _t('Template list not found.'), type: 'warning'});
                return;
            }
            // collect checked row selectors
            const inputs = fieldEl.querySelectorAll('input.o_list_record_selector:checked');
            const ids = Array.from(inputs).map((i) => (i.dataset.id || i.value)).map(Number).filter(Boolean);
            try {
                const recordId = this.model.get(this.handle).data.id;
                // If no ids selected, open wizard prefilled with empty selection (user can choose)
                const action = await this._rpc({
                    model: this.modelName,
                    method: 'action_open_attach_wizard_with_templates',
                    args: [recordId, ids],
                });
                this.trigger_up('do_action', {action: action});
            } catch (err) {
                console.error(err);
                this.displayNotification({title: _t('Error'), message: _t('Could not open attach wizard.'), type: 'danger'});
            }
        },

        _onTemplateSearch(ev) {
            const q = (ev.target.value || '').trim().toLowerCase();
            const fieldEl = this.el.querySelector('[data-field="template_library_rel_ids"]');
            if (!fieldEl) { return; }
            // find rows (one2many list rows)
            const rows = fieldEl.querySelectorAll('tr.o_data_row, tr.o_list_record_row');
            rows.forEach((row) => {
                let nameCell = row.querySelector('td[data-field="name"]');
                if (!nameCell) {
                    // fallback: first cell
                    nameCell = row.querySelector('td');
                }
                const text = nameCell ? nameCell.textContent.trim().toLowerCase() : '';
                row.style.display = q && text.indexOf(q) === -1 ? 'none' : '';
            });
        },
        },
    });
});