/** @odoo-module */
/* global QUnit */

import { makeTestEnv } from "@web/../tests/helpers/mock_env";
import { getFixture } from "@web/../tests/helpers/utils";
import { FormController } from "@web/views/form/form_controller";
// Ensure the templates UI patch is loaded
import "qaco_client_onboarding/static/src/js/templates_ui.js";

QUnit.module("qaco_client_onboarding Templates UI", {
    async beforeEach() {
        this.target = getFixture();
        this.env = await makeTestEnv({});
    },
});

QUnit.test("placeholder toggles based on rows", async (assert) => {
    const el = document.createElement('div');
    el.innerHTML = `
        <div class="empty-placeholder-container" style="display:block">No templates</div>
        <div data-field="template_library_rel_ids"><table><tbody></tbody></table></div>
    `;
    this.target.appendChild(el);

    const controller = {
        el: el,
        env: this.env,
        model: { get: () => ({ data: { id: 1 } }) },
        handle: 'root'
    };

    // no rows => placeholder visible
    FormController.prototype._setupTemplateListObserver.call(controller);
    assert.strictEqual(el.querySelector('.empty-placeholder-container').style.display, 'block', 'placeholder visible when no rows');

    // add a row and re-run observer
    const tbody = el.querySelector('tbody');
    const tr = document.createElement('tr');
    tr.className = 'o_data_row';
    const td = document.createElement('td');
    td.setAttribute('data-field','name');
    td.textContent = 'KYC Document';
    const td2 = document.createElement('td');
    const cb = document.createElement('input'); cb.className = 'o_list_record_selector'; cb.dataset.id = '42';
    td2.appendChild(cb);
    tr.appendChild(td);
    tr.appendChild(td2);
    tbody.appendChild(tr);

    FormController.prototype._setupTemplateListObserver.call(controller);
    assert.strictEqual(el.querySelector('.empty-placeholder-container').style.display, 'none', 'placeholder hidden when rows exist');
});

QUnit.test("filter and quick legal filter work", async (assert) => {
    const el = document.createElement('div');
    el.innerHTML = `
        <div class="empty-placeholder-container" style="display:none"></div>
        <div data-field="template_library_rel_ids"><table><tbody></tbody></table></div>
    `;
    this.target.appendChild(el);
    const tbody = el.querySelector('tbody');

    function addRow(name){
        const tr = document.createElement('tr');
        tr.className = 'o_data_row';
        const td = document.createElement('td');
        td.setAttribute('data-field','name');
        td.textContent = name;
        tr.appendChild(td);
        tbody.appendChild(tr);
        return tr;
    }

    addRow('KYC Checklist');
    addRow('Engagement Letter');

    const controller = {
        el: el,
        env: this.env,
        model: { get: () => ({ data: { id: 1 } }) },
        handle: 'root'
    };

    FormController.prototype._filterTemplateRows.call(controller, el.querySelector('[data-field="template_library_rel_ids"]'), 'kyc');
    let rows = Array.from(tbody.querySelectorAll('tr'));
    assert.strictEqual(rows.filter(r => r.style.display === '').length, 1, 'one row visible for kyc');

    // quick legal filter (should keep KYC only)
    FormController.prototype._applyQuickLegalFilter.call(controller, el.querySelector('[data-field="template_library_rel_ids"]'), true);
    rows = Array.from(tbody.querySelectorAll('tr'));
    assert.strictEqual(rows.filter(r => r.style.display === '').length, 1, 'only legal-like row remains when quick filter enabled');
});

QUnit.test("clicking a row toggles checkbox selection", async (assert) => {
    const el = document.createElement('div');
    el.innerHTML = `
        <div class="empty-placeholder-container" style="display:none"></div>
        <div data-field="template_library_rel_ids"><table><tbody>
            <tr class="o_data_row"><td data-field="name">Doc</td><td><input class="o_list_record_selector" data-id="1" type="checkbox"/></td></tr>
        </tbody></table></div>
    `;
    this.target.appendChild(el);

    const controller = {
        el: el,
        env: this.env,
        model: { get: () => ({ data: { id: 1 } }) },
        handle: 'root'
    };

    const td = el.querySelector('td[data-field="name"]');
    FormController.prototype._onTemplateRowClick.call(controller, { target: td });
    const checkbox = el.querySelector('input.o_list_record_selector');
    assert.ok(checkbox.checked, 'checkbox toggled on click');
});