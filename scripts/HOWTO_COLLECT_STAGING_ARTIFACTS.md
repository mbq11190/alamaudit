How to collect staging artifacts for root-cause analysis
=======================================================

These steps are safe and non-destructive. They create a DB backup and produce the key files we need to analyze registry and asset errors.

1) Run the safe orchestrator (recommended)
-----------------------------------------
- From the repository root on the staging host:
  ./scripts/safe_odoo_fix.sh --db <staging_db>

- Artifacts produced (in ./scripts/):
  - first_traceback.txt  (extracted first Python traceback)
  - db_models.txt        (list of models in DB)
  - orphan_report.txt    (DB-side metadata checks)
  - dryrun_suggestions.sql (commented SQL with suggested changes)

2) If you cannot run the orchestrator, run these commands
---------------------------------------------------------
- DB model list:
  sudo -u postgres psql -d <staging_db> -c "COPY (SELECT model FROM ir_model ORDER BY model) TO STDOUT;" > ./scripts/db_models.txt

- Extract first traceback from upgrade log:
  python scripts/find_first_traceback.py /tmp/upgrade-<DB>.log > ./scripts/first_traceback.txt

- Run orphan checks (see scripts/orphan_ir_model_checks.sql):
  sudo -u postgres psql -d <staging_db> -f ./scripts/orphan_ir_model_checks.sql > ./scripts/orphan_report.txt

3) Browser console (frontend missing modules)
--------------------------------------------
- Open the affected page in Chrome/Firefox and open DevTools (F12)
- In Console, run:
  JSON.stringify(window.__missing_module_definitions || window.__missing_module_shims || [], null, 2)
- Copy & paste the output here in the chat (it should be a JSON array of module name strings)

4) Paste the files here for analysis
-----------------------------------
- Attach or paste the contents of these files in the chat:
  - scripts/first_traceback.txt (first traceback block)
  - scripts/db_models.txt (DB model list)
  - scripts/orphan_report.txt (SQL orphan checks output)
  - The browser console JSON array for missing modules

5) What I’ll do with the artifacts
---------------------------------
- Parse first traceback and map to file/module/manifest
- Cross-check DB model list and identify true missing models
- Produce safe, minimal fixes (code or SQL) and an UNDO plan
- Prepare PR(s) with tests and a verification checklist
