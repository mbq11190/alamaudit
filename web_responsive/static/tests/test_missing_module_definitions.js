odoo.define('web_responsive.tests.missing_module_definitions', function (require) {
    'use strict';
    var QUnit = require('qunit');

    QUnit.module('missing_module_definitions', function () {
        QUnit.test('placeholders defined', function (assert) {
            // If MODULE_NAMES is empty, this test is a noop; otherwise it checks each module can be required.
            var names = (window.__missing_module_definitions || []);
            names.forEach(function (name) {
                assert.ok(typeof require(name) !== 'undefined', 'Module ' + name + ' should be defined');
            });
            assert.ok(true, 'missing_module_definitions test ran');
        });
    });
});
