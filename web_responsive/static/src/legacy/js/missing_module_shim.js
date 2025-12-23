/*
  Missing module shim for Odoo frontend
  --------------------------------------
  Purpose: Provide safe, minimal no-op module definitions for any JS modules
  that fail to load due to missing files during asset loading. This is a
  temporary mitigation to prevent module_loader errors until permanent fixes
  (adding the missing files or correcting asset references) are applied.

  Behavior:
   - Wraps global require to catch missing module load errors
   - Automatically defines a noop module for the missing module name and
     retries the require, returning an empty object as the module value
   - Logs the shimmed module names to window.__missing_module_shims for
     diagnostics.

  IMPORTANT: This is a temporary mitigation. Please investigate and add the
  missing module files or correct `__manifest__['assets']` entries for a
  permanent fix.
*/

(function () {
  'use strict';
  try {
    var globalRequire = window.require || (window.odoo && window.odoo.require);
    var globalDefine = window.odoo && window.odoo.define;
    if (!globalRequire || !globalDefine) {
      // If the Odoo loader isn't present yet, try again after DOMContentLoaded
      document.addEventListener('DOMContentLoaded', function () {
        if (window.require && window.odoo && window.odoo.define) {
          installShim(window.require, window.odoo.define);
        }
      });
      return;
    }
    installShim(globalRequire, globalDefine);
  } catch (e) {
    // Fail silently; we don't want to break the UI if shimming fails
    console.warn('missing_module_shim: initialization error', e);
  }

  function installShim(requireFn, defineFn) {
    if (!window.__missing_module_shims) {
      window.__missing_module_shims = [];
    }

    // Wrap require to handle missing modules
    var originalRequire = requireFn;

    function wrappedRequire(name) {
      try {
        return originalRequire(name);
      } catch (err) {
        try {
          // If module not defined, define a noop module and register it
          if (window.odoo && window.odoo.define) {
            if (window.__missing_module_shims.indexOf(name) === -1) {
              window.__missing_module_shims.push(name);
              console.warn('missing_module_shim: defining noop for missing module', name);
              window.odoo.define(name, function (require) {
                // noop stub: return an empty object
                return {};
              });
            }
            // Try require again
            return originalRequire(name);
          }
        } catch (e) {
          console.warn('missing_module_shim: failed to define stub for', name, e);
        }
        // As a last resort, return an empty object
        return {};
      }
    }

    // Try to replace global require if safe to do so
    try {
      if (window.require && window.require !== wrappedRequire) {
        window.require = wrappedRequire;
      }
      if (window.odoo && window.odoo.require && window.odoo.require !== wrappedRequire) {
        window.odoo.require = wrappedRequire;
      }
    } catch (e) {
      // ignore
    }
  }
})();
