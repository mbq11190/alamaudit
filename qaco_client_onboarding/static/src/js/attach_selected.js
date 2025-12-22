/** @odoo-module */

import { patch } from '@web/core/utils/patch';
import { FormController } from '@web/views/form/form_controller';
import rpc from 'web.rpc';
import core from 'web.core';

var _t = core._t;

patch(FormController.prototype, 'qaco_client_onboarding.attach_selected', {
    events: Object.assign({}, FormController.prototype.events, {
        'click .o_attach_selected': '_onAttachSelected'
    }),

    _onAttachSelected: function (ev) {
        ev.preventDefault();
        var self = this;
        // find the one2many field container
        var fieldEl = this.el.querySelector('[data-field="template_library_rel_ids"]');
        if (!fieldEl) {
            try {
                this.displayNotification({title: _t('Error'), message: _t('Template list not found.'), type: 'warning'});
            } catch (e) {
                // fallback for newer controller API
                this.env.services.notification.add(_t('Template list not found.'), {type: 'warning'});
            }
            return;
        }
        // collect checked row selectors
        var inputs = fieldEl.querySelectorAll('input.o_list_record_selector:checked');
        var ids = Array.prototype.slice.call(inputs).map(function (i) { return Number(i.dataset.id || i.value); }).filter(Boolean);
        var recordId = this.model.get(this.handle).data.id;
        // If no ids selected, open wizard prefilled with empty selection (user can choose)
        rpc.query({
            model: this.modelName,
            method: 'action_open_attach_wizard_with_templates',
            args: [[recordId], ids]
        }).then(function (action) {
            self.trigger_up('do_action', {action: action});
        }).catch(function (err) {
            try {
                self.displayNotification({title: _t('Error'), message: _t('Could not open attach wizard.'), type: 'danger'});
            } catch (e) {
                self.env.services.notification.add(_t('Could not open attach wizard.'), {type: 'danger'});
            }
        });
    },


});