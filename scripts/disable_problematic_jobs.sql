-- Disable problematic crons & server actions (COMMENTED by default)
-- File: scripts/disable_problematic_jobs.sql
-- Purpose: Provide minimal, targeted UPDATE statements to temporarily disable jobs
--           that reference models missing from the registry. All statements are
--           commented out by default and include UNDO guidance.
-- Safety: 1) Create a DB backup before applying. 2) Apply during a maintenance window.
--         3) Verify the SELECT queries below to confirm the IDs or models before
--            uncommenting any UPDATE statements.

-- ========================================================================
-- Step 0: Verify candidate crons and server actions (run these first)
-- ========================================================================
-- SELECT id, name, model FROM ir_cron WHERE model IS NOT NULL AND model IN (
--     'hr.employee.transfer', 'unallocated.employee.recipient', 'leave.condonation',
--     'audit.firm.name', 'qaco.note.tag', 'execution.phase', 'qaco.execution.phase',
--     'qaco.finalisation.phase'
-- ) ORDER BY id;

-- SELECT id, name, model FROM ir_actions_server WHERE model IS NOT NULL AND model IN (
--     'hr.employee.transfer', 'unallocated.employee.recipient', 'leave.condonation',
--     'audit.firm.name', 'qaco.note.tag', 'execution.phase', 'qaco.execution.phase'
-- ) ORDER BY id;

-- ========================================================================
-- SECTION A: Disable crons by model name (UNCOMMENT to apply)
-- ========================================================================
-- Note: These disable statements are conservative and affect any cron referencing
-- the named model(s). Confirm the affected cron IDs first using the verification
-- queries above.

-- UPDATE ir_cron SET active = false WHERE model IN (
--     'hr.employee.transfer',
--     'unallocated.employee.recipient',
--     'leave.condonation',
--     'audit.firm.name',
--     'qaco.note.tag',
--     'execution.phase',
--     'qaco.execution.phase',
--     'qaco.finalisation.phase'
-- );

-- UNDO: To re-enable the crons
-- UPDATE ir_cron SET active = true WHERE model IN (
--     'hr.employee.transfer',
--     'unallocated.employee.recipient',
--     'leave.condonation',
--     'audit.firm.name',
--     'qaco.note.tag',
--     'execution.phase',
--     'qaco.execution.phase',
--     'qaco.finalisation.phase'
-- );

-- ========================================================================
-- SECTION B: Disable server actions by model name (UNCOMMENT to apply)
-- ========================================================================
-- These will set the server action to inert code (safe placeholder). Restore
-- original code from backups if you need to revert behavior other than disabling.

-- UPDATE ir_actions_server SET state = 'code',
--     code = 'raise Warning("Temporarily disabled: missing model")'
-- WHERE model IN (
--     'hr.employee.transfer',
--     'unallocated.employee.recipient',
--     'leave.condonation',
--     'audit.firm.name',
--     'qaco.note.tag',
--     'execution.phase',
--     'qaco.execution.phase'
-- );

-- UNDO: There is no automatic restore in this file. Best practice:
-- 1) Export original `ir_actions_server` rows before applying (use psql COPY TO or pg_dump of the table filtered by id).
-- 2) Re-import original rows to restore previous state.

-- ========================================================================
-- SECTION C: Disable by explicit IDs (precise & reversible)
-- ========================================================================
-- If you already have the exact IDs (from the verification queries), prefer
-- disabling by ID. Replace <ID> with the numeric id and then uncomment.

-- Example (cron by ID):
-- UPDATE ir_cron SET active = false WHERE id = <cron_id>;
-- -- UNDO: UPDATE ir_cron SET active = true WHERE id = <cron_id>;

-- Example (server action by ID):
-- UPDATE ir_actions_server SET state = 'code', code = 'raise Warning("Disabled pending model")' WHERE id = <action_id>;
-- -- UNDO: restore original state/code from backup export

-- ========================================================================
-- SECTION D: Apply checklist
-- ========================================================================
-- 1) Ensure you have a recent DB dump: sudo -u postgres pg_dump <db> | gzip > /tmp/db_backup.sql.gz
-- 2) Run verification queries at top of this file and confirm the rows you will affect
-- 3) Run the SQL in a single transaction where possible and monitor logs
-- 4) After apply, watch Odoo logs for errors and verify that the previously failing crons/action invocations no longer produce KeyErrors
-- 5) To revert, follow the UNDO steps or re-import the exported ir_actions_server rows

-- ========================================================================
-- End of file
