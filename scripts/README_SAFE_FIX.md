Safe Odoo Fix workflow
======================

Purpose
-------
Provide a safe, review-first workflow for diagnosing and preparing DB fixes for missing models, crons, and server actions. The workflow emphasizes backups, diagnostics, and a dry-run SQL that must be reviewed before any destructive action.

Files
-----
- `safe_odoo_fix.sh` - Orchestrator that creates DB dump, runs diagnostics, and generates a DRY-RUN SQL file (non-destructive by default).
- `generate_dryrun_sql.py` - Generates the commented DRY-RUN SQL and a human-readable report.
- `dryrun_suggestions.sql` - Output path (default `scripts/dryrun_suggestions.sql`) containing suggested SQL changes (commented).

Usage
-----
1. Generate DRY-RUN (no DB):
   - `./scripts/safe_odoo_fix.sh`
2. Generate DRY-RUN with DB evidence (recommended):
   - `./scripts/safe_odoo_fix.sh --db <dbname>`
3. To apply after careful review (not recommended without approval):
   - `./scripts/safe_odoo_fix.sh --db <dbname> --apply`

Notes
-----
- The scripts purposefully avoid destructive `DELETE` operations. For candidates that need removal, the scripts suggest archiving or inserting review records for manual assessment.

Quick helper SQL files have been added for conservative, commented actions:
- `scripts/quick_disable_crons.sql` — suggested `UPDATE` statements to disable crons referencing missing models (commented by default)
- `scripts/quick_disable_server_actions.sql` — suggested `UPDATE` statements to set server actions to inert `code` or disable them (commented by default)
- `scripts/disable_problematic_jobs.sql` — **precise**, audited and commented disable script that contains only the necessary UPDATE statements (commented by default) and UNDO guidance; run verification queries in the header before uncommenting any statements.

Use these only after reviewing `scripts/dryrun_suggestions.sql` and `scripts/candidate_patch.sql`.

For DB optimization and quick disable workflow, see `scripts/README_DB_OPTIMIZE.md` and `scripts/db_optimize.sh`.

- Always ensure you have a DB dump and tested rollback plan before applying anything to production.
