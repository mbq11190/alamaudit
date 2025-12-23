PR: Fix frontend missing modules (permanent replacements for shim)
===============================================================

Summary
-------
This PR (draft) begins the work to replace the runtime shim with permanent fixes for missing frontend modules. It includes:

- A lightweight shim (already merged) that collects missing module names into `window.__missing_module_definitions`.
- A new explicit placeholder definitions file: `web_responsive/static/src/legacy/js/missing_module_definitions.js`.
  - This file defines placeholder modules listed in `MODULE_NAMES`.
  - Placeholders are temporary and should be replaced by real implementations.
- A small QUnit test: `web_responsive/static/tests/test_missing_module_definitions.js`.
- Updated `web_responsive/__manifest__.py` to bundle the definitions file.

What to do next (mapping & replacement workflow)
------------------------------------------------
1. On staging, load the page and open the browser console; evaluate:
   - `window.__missing_module_definitions` (collected by the shim) and `window.__missing_module_shims` (legacy shim list)
2. For each reported module name (highest frequency first):
   a) Search the repo for existing source corresponding to the module name (files or ESM module that should be defining it). If found, update that file to expose the module name via `odoo.define('module.name', ...)` or add a small wrapper file that imports the ESM and defines the `odoo.define` name.
   b) If no existing source is available, implement the minimal real implementation (or re-implement the missing functionality) rather than a placeholder.
   c) Add the new or updated file to the owning module's `__manifest__['assets']['web.assets_backend']` list.
   d) Add tests (QUnit) that `require()` the module and assert expected behavior.
3. Once all heavy hitters are addressed and tests pass, remove the runtime shim (`missing_module_shim.js`) and keep only the real implementations.

Files changed in this draft
--------------------------
- `web_responsive/static/src/legacy/js/missing_module_shim.js` (added global tracking)
- `web_responsive/static/src/legacy/js/missing_module_definitions.js` (new placeholder definitions)
- `web_responsive/static/tests/test_missing_module_definitions.js` (new test)
- `web_responsive/__manifest__.py` (assets updated to include definitions file)

Notes
-----
- This PR intentionally favors safety: placeholders are inert and easily removable. It does not change business logic.
- After you paste `window.__missing_module_definitions` from staging, I will:
  - Map each module to repo files, prepare exact file-level edits, and generate the final PR diff with replacements (implementations and manifest updates).

Next action for me
------------------
- Once you paste the array `window.__missing_module_definitions`, I will produce an exact patch (diff) changing specific files and adding tests, and open the PR draft for your review.
