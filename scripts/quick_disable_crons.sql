-- Quick cron disable suggestions (COMMENTED by default)
-- Review the cron IDs and models before applying. These statements are safe to enable after verification.

-- Disable crons by name pattern (example):
-- UPDATE ir_cron SET active = false WHERE name ILIKE '%Unallocate Employees%';
-- UPDATE ir_cron SET active = false WHERE name ILIKE '%Pending Transfers%';
-- UPDATE ir_cron SET active = false WHERE name ILIKE '%Employee Transfer%';

-- Disable crons by model referencing missing models (example):
-- UPDATE ir_cron SET active = false WHERE model IN ('hr.employee.transfer', 'unallocated.employee.recipient');

-- UNDO (to re-enable):
-- UPDATE ir_cron SET active = true WHERE name ILIKE '%Unallocate Employees%';
-- UPDATE ir_cron SET active = true WHERE model IN ('hr.employee.transfer', 'unallocated.employee.recipient');
