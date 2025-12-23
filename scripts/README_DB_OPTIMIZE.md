DB Optimization & Safe Disable workflow
======================================

Purpose
-------
Provide conservative, reviewed steps to temporarily disable crons and server actions that reference missing models, and to run safe database optimization queries during a maintenance window.

Files
-----
- `scripts/generate_disable_and_optimize.sql` - Commented candidate SQL for disabling crons/server actions and safe optimization queries (VACUUM/ANALYZE, indexes).
- `scripts/db_optimize.sh` - Wrapper to create a backup and show the SQL (DRY-RUN), and apply it with `--apply` after explicit confirmation.

Usage
-----
1. DRY RUN (recommended):
   - `./scripts/db_optimize.sh --db <dbname>`
   - This creates a backup and prints the SQL to stdout for review.

2. APPLY (only after review and backups):
   - `./scripts/db_optimize.sh --db <dbname> --apply`
   - You will be prompted to type `YES` to proceed.

Notes & Safety
--------------
- These scripts intentionally avoid destructive deletes; the SQL is commented and conservative.
- Always ensure a tested backup exists before running `--apply`.
- Monitor Odoo logs and cron behavior after changes. Re-enable anything you disabled if it proves necessary.
