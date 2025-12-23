Fix for RPC_ERROR: Invalid field 'id' on model '_unknown'

Purpose
-------
Quick, safe SQL to neutralize `ir_model_fields` rows referencing missing comodels (the root cause of the error). The change is non-destructive: it backs up affected rows and logs every action.

Recommended workflow
--------------------
1. Take a full database backup (mandatory).
2. Run the dry-run SQL to list affected rows and counts:
   psql -h <host> -U <user> -d <db> -f scripts/fix_problematic_ir_model_fields_dryrun.sql
3. Inspect the output carefully. If the results look reasonable, run the fix SQL:
   psql -h <host> -U <user> -d <db> -f scripts/fix_problematic_ir_model_fields.sql
4. Run verification queries (or re-run the dry-run SQL) to confirm there are no more missing relations.

Verification
------------
- Confirm there are no more missing relations:
  SELECT f.id, f.model, f.name, f.relation FROM ir_model_fields f WHERE f.relation IS NOT NULL AND f.relation NOT IN (SELECT model FROM ir_model);

- Check backups and migration log:
  SELECT * FROM backup_problematic_ir_model_fields ORDER BY id DESC LIMIT 20;
  SELECT * FROM qaco_problematic_fields_migration_log ORDER BY created_at DESC LIMIT 20;

- Check one2many missing inverses:
  SELECT id, model, name, relation, inverse_name FROM ir_model_fields WHERE ttype='one2many' AND (inverse_name IS NULL OR inverse_name = '' OR NOT EXISTS (SELECT 1 FROM ir_model_fields rf WHERE rf.model = ir_model_fields.relation AND rf.name = ir_model_fields.inverse_name));

Restore
-------
If you need to restore specific fields, use the restore helper:

  python scripts/restore_problematic_fields.py --db <db> --user <user> --host <host> --ids <backup_id[,backup_id2]> [--dry-run] [--force]

Notes
-----
- Run the dry-run first. The fix SQL is idempotent but it's good to inspect candidates manually to avoid unintended removals.
- If you want me to run the dry-run and/or the fix on a staging DB, provide temporary credentials and confirm you have a backup. I'll run dry-run first and show the rows I'll affect before applying the fix.
