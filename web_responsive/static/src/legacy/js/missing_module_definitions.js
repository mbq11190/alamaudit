/*
 * Explicit missing-module definitions (temporary placeholders)
 * -----------------------------------------------------------
 * Add module names (strings) to the MODULE_NAMES array below for each
 * frontend module that is reported missing by `window.__missing_module_shims`.
 *
 * Each entry will be defined as an empty module via odoo.define(name, () => ({}))
 * which satisfies any require(...) calls. Replace each placeholder with the
 * real implementation as you implement permanent fixes.
 */

(function () {
  'use strict';
  var MODULE_NAMES = [
    // Example: 'web_responsive.menu_canonical_searchbar',
    // Add missing module names here (one per line)
  ];

  if (!(window.odoo && window.odoo.define)) {
    // Wait for Odoo loader to be ready
    document.addEventListener('DOMContentLoaded', function () {
      if (window.odoo && window.odoo.define) {
        defineModules();
      }
    });
  } else {
    defineModules();
  }

  function defineModules() {
    MODULE_NAMES.forEach(function (name) {
      try {
        if (!window.odoo._modules || !window.odoo._modules[name]) {
          window.odoo.define(name, function () {
            return {};
          });
          console.info('missing_module_definitions: defined placeholder for', name);
        }
      } catch (e) {
        console.warn('missing_module_definitions: failed to define placeholder for', name, e);
      }
    });
  }
})();
