Migration 17.0.1.8 — Safe backup and neutralization of problematic ir_model_fields

What this migration does:
- Creates/uses `backup_problematic_ir_model_fields` to store problematic rows before changes.
- Creates `qaco_problematic_fields_migration_log` to record which fields were processed and the actions taken.
- Clears `relation` and `inverse_name` on ir_model_fields rows that point to non-existent models (action = `cleared_relation`).
- Clears `inverse_name` for One2many fields whose inverse does not exist (action = `cleared_inverse`).
- Backups and deactivates `ir_ui_view` records whose tree `default_order` references missing fields.

Why this is safe:
- All changes are non-destructive: original rows are copied to backup table and actions are logged with timestamps.
- Clearing `relation`/`inverse_name` prevents ORM errors while preserving the original metadata in backups for restoration.

Restore steps:
1. Identify the field(s) to restore from `backup_problematic_ir_model_fields`:
   SELECT * FROM backup_problematic_ir_model_fields WHERE id = <field_id>;
2. To fully restore, re-insert the row into `ir_model_fields` (carefully) or use the backup as a source to reconstruct the field via ORM.
3. Remove or annotate the corresponding `qaco_problematic_fields_migration_log` entry to indicate restoration.

Note: If you prefer a full-automatic restore helper script, I can add one (separate patch).