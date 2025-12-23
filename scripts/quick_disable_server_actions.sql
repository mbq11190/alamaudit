-- Quick server action disable suggestions (COMMENTED by default)
-- Find server actions referencing missing models and disable them or set them to inert code.

-- Example: disable by ID
-- UPDATE ir_actions_server SET state = 'code', code = 'raise Warning(\'Temporarily disabled: missing model\')' WHERE id = 446;
-- UNDO: restore previous state/code from backup (not stored here); consider exporting original code before change.

-- Example: disable by model
-- UPDATE ir_actions_server SET state = 'code', code = 'raise Warning(\'Temporarily disabled: missing model\')' WHERE model IN ('hr.employee.transfer');

-- Suggested workflow:
-- 1) Run SELECT id, name, model FROM ir_actions_server WHERE model IN ('hr.employee.transfer');
-- 2) For each result, review and then execute the UPDATE above with the specific id.
