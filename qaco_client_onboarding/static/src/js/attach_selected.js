odoo.define('qaco_client_onboarding.attach_selected', function (require) {
    'use strict';

    const FormController = require('web.FormController');
    const rpc = require('web.rpc');
    const core = require('web.core');
    const _t = core._t;

    FormController.include({
        events: Object.assign({}, FormController.prototype.events, {
            'click .o_attach_selected': '_onAttachSelected',
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
            if (!ids.length) {
                this.displayNotification({title: _t('No selection'), message: _t('Select one or more templates to attach.'), type: 'warning'});
                return;
            }
            try {
                const recordId = this.model.get(this.handle).data.id;
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
    });
});