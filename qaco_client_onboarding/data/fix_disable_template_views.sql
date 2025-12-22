-- Safe reversible SQL to back up and deactivate problematic template views
-- Run this *after* taking a DB backup. This will create backup tables and deactivate
-- any views that reference patterns known to cause XPath/Parse errors during module upgrades.

BEGIN;

-- create backup tables if they do not exist
CREATE TABLE IF NOT EXISTS backup_problematic_ir_ui_view AS
    SELECT * FROM ir_ui_view WHERE false;

CREATE TABLE IF NOT EXISTS backup_problematic_ir_model_data AS
    SELECT * FROM ir_model_data WHERE false;

-- copy problematic views (matches several patterns)
INSERT INTO backup_problematic_ir_ui_view
SELECT v.* FROM ir_ui_view v
WHERE v.arch_db ILIKE '%o_attach_selected%'
   OR v.arch_db ILIKE '%template_library_rel_ids%'
   OR v.arch_db ILIKE '%Attach selected%'
   OR v.arch_db ILIKE '%Open Template Library%'
   OR v.arch_db ILIKE '%template_library%'
   OR v.arch_db ILIKE '%o_tpl_download%'
   OR v.arch_db ILIKE '%o_tpl_attach%'
   OR v.arch_db ILIKE '%o_open_template_library%';

-- copy related ir.model.data rows
INSERT INTO backup_problematic_ir_model_data
SELECT md.* FROM ir_model_data md
WHERE md.model = 'ir.ui.view'
  AND md.res_id IN (SELECT id FROM backup_problematic_ir_ui_view);

-- Deactivate the problematic views
UPDATE ir_ui_view
SET active = false
WHERE id IN (SELECT id FROM backup_problematic_ir_ui_view);

-- Remove the model data entries so module upgrades don't reapply the broken views
DELETE FROM ir_model_data
WHERE model = 'ir.ui.view' AND res_id IN (SELECT id FROM backup_problematic_ir_ui_view);

COMMIT;

-- Verification: run these after the script
-- SELECT count(*) FROM backup_problematic_ir_ui_view;
-- SELECT count(*) FROM backup_problematic_ir_model_data;
-- SELECT id, name, active FROM ir_ui_view WHERE arch_db ILIKE '%o_attach_selected%';
