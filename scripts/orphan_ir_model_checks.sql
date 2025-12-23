-- Run the following queries in your DB (psql -d <db>) to find candidate orphan metadata.
-- WARNING: These are SELECT-only checks. Do not DELETE without verification.

-- 1) Show ir.model entries with models that are not defined in code (manual review required)
SELECT id, model, name, state
FROM ir_model
ORDER BY model;

-- 2) Show ir.model.fields where the model is missing or the field likely missing
SELECT f.id, f.model_id, m.model AS model_name, f.name AS field_name, f.ttype
FROM ir_model_fields f
LEFT JOIN ir_model m ON f.model_id = m.id
WHERE m.model IS NULL OR NOT EXISTS (
    SELECT 1 FROM ir_model WHERE model = m.model
)
ORDER BY m.model, f.name;

-- 3) Show server actions referencing missing models
SELECT id, name, model_id, model, state, code
FROM ir_actions_server
ORDER BY model;

-- 4) Show crons whose model is missing
SELECT c.id, c.name, c.model, c.user_id, c.active
FROM ir_cron c
ORDER BY c.model;

-- 5) List views referencing models that may not exist (by checking XML records)
SELECT id, name, model
FROM ir_ui_view
ORDER BY model;

-- After reviewing the SELECT results, to remove an orphan safely, consider disabling or archiving
-- the record (set active = False) rather than deleting immediately. Review dependencies and backups first.
