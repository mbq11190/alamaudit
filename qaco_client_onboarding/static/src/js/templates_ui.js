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

    willStart: function () {
        var self = this;
        // call parent willStart if present
        if (FormController.prototype.willStart) {
            var maybe = FormController.prototype.willStart.apply(this, arguments);
            if (maybe && maybe.then) {
                return maybe.then(function () { self._setupTemplateListObserver(); });
            }
        }
        this._setupTemplateListObserver();
    },

    _setupTemplateListObserver: function () {
        var self = this;
        // find the template list container and the placeholder block
        var fieldEl = this.el.querySelector('[data-field="template_library_rel_ids"]');
        var placeholder = this.el.querySelector('.empty-placeholder-container');
        if (!placeholder) { return; }
        // toggle based on presence of data rows initially
        var rows = fieldEl && fieldEl.querySelectorAll('tr.o_data_row, tr.o_list_record_row');
        placeholder.style.display = rows && rows.length ? 'none' : 'block';

        // Setup search and quick filter handlers
        var search = this.el.querySelector('.o_template_search');
        if (search) {
            search.addEventListener('input', function (ev) { self._filterTemplateRows(fieldEl, ev.target.value); });
        }
        var legal = this.el.querySelector('.o_quick_filter_legal');
        if (legal) {
            legal.addEventListener('change', function (ev) { self._applyQuickLegalFilter(fieldEl, ev.target.checked); });
        }

        // observe the fieldEl for changes and toggle placeholder accordingly
        if (!fieldEl || typeof MutationObserver === 'undefined') { return; }
        var tbody = fieldEl.querySelector('tbody');
        if (!tbody) { return; }
        var mo = new MutationObserver(function (mutations) {
            var rows = tbody.querySelectorAll('tr.o_data_row, tr.o_list_record_row');
            placeholder.style.display = rows && rows.length ? 'none' : 'block';
        });
        try {
            mo.observe(tbody, { childList: true, subtree: false });
        } catch (e) {
            // ignore if observation fails
            console.warn('Template list observer setup failed', e);
        }
    },

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

        // also show loading in preview
        var prev = this.el.querySelector('.preview-card');
        if (prev) { prev.classList.add('o-preview-busy'); }

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
                if (prev) { prev.classList.remove('o-preview-busy'); }
            });
        } catch (err) {
            console.error(err);
            row.classList.remove('o-row-busy');
            if (prev) { prev.classList.remove('o-preview-busy'); }
        }
    },

    _filterTemplateRows: function (fieldEl, q) {
        if (!fieldEl) { return; }
        q = (q || '').trim().toLowerCase();
        var rows = fieldEl.querySelectorAll('tr.o_data_row, tr.o_list_record_row');
        for (var i = 0; i < rows.length; i++) {
            var row = rows[i];
            var nameCell = row.querySelector('td[data-field="name"]');
            var text = nameCell ? nameCell.textContent.trim().toLowerCase() : '';
            row.style.display = q && text.indexOf(q) === -1 ? 'none' : '';
        }
    },

    _applyQuickLegalFilter: function (fieldEl, enabled) {
        if (!fieldEl) { return; }
        var rows = fieldEl.querySelectorAll('tr.o_data_row, tr.o_list_record_row');
        for (var i = 0; i < rows.length; i++) {
            var row = rows[i];
            var nameCell = row.querySelector('td[data-field="name"]');
            var text = nameCell ? nameCell.textContent.trim().toLowerCase() : '';
            var match = (text.indexOf('kyc') !== -1) || (text.indexOf('kyb') !== -1) || (text.indexOf('legal') !== -1);
            row.style.display = enabled && !match ? 'none' : '';
        }
    },

    _updatePreviewForSelection: function () {
        var fieldEl = this.el.querySelector('[data-field="template_library_rel_ids"]');
        if (!fieldEl) { return; }
        var selected = fieldEl.querySelectorAll('input.o_list_record_selector:checked');
        var preview = this.el.querySelector('.preview-card');
        var content = this.el.querySelector('.preview-content');
        var empty = this.el.querySelector('.preview-empty');
        if (!preview || !content || !empty) { return; }
        if (!selected || !selected.length) {
            content.style.display = 'none';
            empty.style.display = 'block';
            return;
        }
        var id = Number(selected[0].dataset.id || selected[0].value);
        if (!id) { content.style.display = 'none'; empty.style.display = 'block'; return; }
        // fetch metadata via rpc
        rpc.query({ model: 'qaco.onboarding.template.document', method: 'read', args: [[id], ['name','category_id','file_type','template_filename','write_date','file_size','create_uid']] })
            .then(function (res) {
                if (!res || !res.length) { content.style.display = 'none'; empty.style.display = 'block'; return; }
                var tpl = res[0];
                empty.style.display = 'none';
                content.style.display = 'block';
                var nameEl = document.querySelector('.tpl-name');
                var metaEl = document.querySelector('.tpl-meta');
                var sizeEl = document.querySelector('.tpl-size');
                var dl = document.querySelector('.tpl-download');
                if (nameEl) { nameEl.textContent = tpl.name || ''; }
                if (metaEl) { metaEl.textContent = (tpl.category_id && tpl.category_id[1] ? tpl.category_id[1] + ' | ' : '') + (tpl.file_type || '').toUpperCase() + (tpl.create_uid && tpl.create_uid[1] ? ' | Author: ' + tpl.create_uid[1] : ''); }
                if (sizeEl) { sizeEl.textContent = tpl.file_size ? (tpl.file_size + ' bytes') : '—'; }
                if (dl) { dl.setAttribute('href', '/web/content/qaco.onboarding.template.document/' + id + '/template_file/' + (tpl.template_filename || 'file') + '?download=true'); }
            }).catch(function (err) { console.error(err); });
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
