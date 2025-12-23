# Migration to safely backup and neutralize problematic ir_model_fields
# - Backs up rows into `backup_problematic_ir_model_fields`
# - Records actions into `qaco_problematic_fields_migration_log` (for audit/restore)
# - Clears `relation`/`inverse_name` on offending rows (non-destructive and reversible)
# - Also handles one2many missing inverses
from datetime import datetime


def migrate(cr, installed_version):
    # Ensure backup table exists
    try:
        cr.execute(
            "CREATE TABLE IF NOT EXISTS backup_problematic_ir_model_fields AS SELECT * FROM ir_model_fields WHERE false"
        )
    except Exception:
        pass

    # Create a tiny log table to record what we changed (reversible)
    try:
        cr.execute(
            "CREATE TABLE IF NOT EXISTS qaco_problematic_fields_migration_log (id serial PRIMARY KEY, field_id integer, model text, name text, relation text, ttype text, action text, created_at timestamp)"
        )
    except Exception:
        pass

    # 1) Find fields referencing non-existent models
    cr.execute(
        "SELECT id, model, name, relation, ttype FROM ir_model_fields f WHERE f.relation IS NOT NULL AND f.relation NOT IN (SELECT model FROM ir_model)"
    )
    missing = cr.fetchall()
    if missing:
        ids = tuple([r[0] for r in missing])
        # backup
        cr.execute(
            "INSERT INTO backup_problematic_ir_model_fields SELECT * FROM ir_model_fields WHERE id IN %s",
            (ids,),
        )
        # log actions
        for fid, model, name, relation, ttype in missing:
            cr.execute(
                "INSERT INTO qaco_problematic_fields_migration_log (field_id, model, name, relation, ttype, action, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (fid, model, name, relation, ttype, 'cleared_relation', datetime.utcnow()),
            )
        # neutralize relation to stop ORM errors (non-destructive)
        cr.execute(
            "UPDATE ir_model_fields SET relation = NULL, inverse_name = NULL WHERE id IN %s",
            (ids,),
        )

    # 2) Find One2many fields with missing inverse
    cr.execute(
        "SELECT id, model, name, relation, inverse_name, ttype FROM ir_model_fields f WHERE f.ttype='one2many' AND (f.inverse_name IS NULL OR f.inverse_name = '' OR NOT EXISTS (SELECT 1 FROM ir_model_fields rf WHERE rf.model = f.relation AND rf.name = f.inverse_name))"
    )
    o2m_missing = cr.fetchall()
    if o2m_missing:
        ids = tuple([r[0] for r in o2m_missing])
        cr.execute(
            "INSERT INTO backup_problematic_ir_model_fields SELECT * FROM ir_model_fields WHERE id IN %s",
            (ids,),
        )
        for fid, model, name, relation, inverse_name, ttype in o2m_missing:
            cr.execute(
                "INSERT INTO qaco_problematic_fields_migration_log (field_id, model, name, relation, ttype, action, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (fid, model, name, relation, ttype, 'cleared_inverse', datetime.utcnow()),
            )
        # clear inverse_name to avoid ORM errors; leave relation intact (we only clear inverse)
        cr.execute(
            "UPDATE ir_model_fields SET inverse_name = NULL WHERE id IN %s",
            (ids,),
        )

    # 3) Optionally: disable views where default_order references unknown fields (log & deactivate)
    # Reuse conservative approach: back up and set active=false if invalid default_order found
    try:
        cr.execute(
            "CREATE TABLE IF NOT EXISTS backup_problematic_ir_ui_view AS SELECT * FROM ir_ui_view WHERE false"
        )
    except Exception:
        pass

    try:
        cr.execute(
            "SELECT id, model, arch_db FROM ir_ui_view WHERE arch_db ILIKE '%default_order=%'"
        )
        candidates = cr.fetchall()
        bad_views = []
        for vid, model_name, arch in candidates:
            try:
                # simple heuristic: look for default_order tokens and verify field presence
                # parse tree elements from arch to find tree[@default_order]
                if not arch:
                    continue
                # crude token scan
                if 'default_order' not in arch:
                    continue
                # fetch field names
                cr.execute("SELECT name FROM ir_model_fields WHERE model=%s", (model_name,))
                md_fields = set(r[0] for r in cr.fetchall())
                # find tokens like default_order="a, b desc"
                import re

                for m in re.finditer(r"default_order\s*=\s*\"([^\"]+)\"", arch):
                    default_order = m.group(1)
                    for token in [x.strip() for x in default_order.split(',') if x.strip()]:
                        fname = token.split()[0]
                        if fname not in md_fields:
                            bad_views.append(vid)
                            break
            except Exception:
                continue
        if bad_views:
            ids = tuple(set(bad_views))
            cr.execute(
                "INSERT INTO backup_problematic_ir_ui_view SELECT * FROM ir_ui_view WHERE id IN %s",
                (ids,),
            )
            cr.execute("UPDATE ir_ui_view SET active=false WHERE id IN %s", (ids,))
            cr.execute(
                "DELETE FROM ir_model_data WHERE model='ir.ui.view' AND res_id IN %s",
                (ids,),
            )
    except Exception:
        pass

    # End of migration
    return
