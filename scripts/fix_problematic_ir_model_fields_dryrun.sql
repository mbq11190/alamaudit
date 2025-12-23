-- Dry-run SQL: lists problematic ir_model_fields and views without making changes
-- Run this first to inspect what would be affected

-- 1) Fields referencing non-existent comodels
SELECT f.id, f.model, f.name, f.ttype, f.relation
FROM ir_model_fields f
WHERE f.relation IS NOT NULL
  AND f.relation NOT IN (SELECT model FROM ir_model)
ORDER BY f.id;

-- 2) One2many fields with missing inverse
SELECT f.id, f.model, f.name, f.ttype, f.relation, f.inverse_name
FROM ir_model_fields f
WHERE f.ttype = 'one2many'
  AND (
    f.inverse_name IS NULL
    OR f.inverse_name = ''
    OR NOT EXISTS (
      SELECT 1 FROM ir_model_fields rf
      WHERE rf.model = f.relation AND rf.name = f.inverse_name
    )
  )
ORDER BY f.id;

-- 3) Views where tree[@default_order] references unknown fields (may cause upgrade parse errors)
-- This is a heuristic scan; review results before acting
SELECT v.id, v.model, v.name
FROM ir_ui_view v
WHERE v.arch_db ILIKE '%default_order=%'
ORDER BY v.id;

-- 4) Counts for quick summary
SELECT
  (SELECT COUNT(*) FROM ir_model_fields f WHERE f.relation IS NOT NULL AND f.relation NOT IN (SELECT model FROM ir_model)) AS missing_relation_count,
  (SELECT COUNT(*) FROM ir_model_fields f WHERE f.ttype='one2many' AND (f.inverse_name IS NULL OR f.inverse_name = '' OR NOT EXISTS (SELECT 1 FROM ir_model_fields rf WHERE rf.model = f.relation AND rf.name = f.inverse_name))) AS missing_o2m_inverse_count,
  (SELECT COUNT(*) FROM ir_ui_view v WHERE v.arch_db ILIKE '%default_order=%') AS views_with_default_order_count;
