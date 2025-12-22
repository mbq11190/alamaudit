# Migration script to cleanup broken IR metadata that prevents registry loading
from lxml import etree

def migrate(cr, installed_version):
    # Backup and remove ir.model.fields whose relation points at non-existent models
    try:
        cr.execute("CREATE TABLE IF NOT EXISTS backup_problematic_ir_model_fields AS SELECT * FROM ir_model_fields WHERE false")
    except Exception:
        pass
    cr.execute("SELECT id FROM ir_model_fields f WHERE f.relation IS NOT NULL AND f.relation NOT IN (SELECT model FROM ir_model)")
    missing_fields = [r[0] for r in cr.fetchall()]
    if missing_fields:
        cr.execute("INSERT INTO backup_problematic_ir_model_fields SELECT * FROM ir_model_fields WHERE id IN %s", (tuple(missing_fields),))
        cr.execute("DELETE FROM ir_model_fields WHERE id IN %s", (tuple(missing_fields),))

    # Backup and remove One2many fields with missing inverse
    try:
        cr.execute("SELECT id FROM ir_model_fields f WHERE f.ttype='one2many' AND (f.inverse_name IS NULL OR f.inverse_name = '' OR NOT EXISTS (SELECT 1 FROM ir_model_fields rf WHERE rf.model = f.relation AND rf.name = f.inverse_name))")
        rows = [r[0] for r in cr.fetchall()]
        if rows:
            cr.execute("INSERT INTO backup_problematic_ir_model_fields SELECT * FROM ir_model_fields WHERE id IN %s", (tuple(rows),))
            cr.execute("DELETE FROM ir_model_fields WHERE id IN %s", (tuple(rows),))
    except Exception:
        pass

    # Backup and deactivate views whose default_order references unknown fields
    try:
        cr.execute("CREATE TABLE IF NOT EXISTS backup_problematic_ir_ui_view AS SELECT * FROM ir_ui_view WHERE false")
    except Exception:
        pass
    try:
        cr.execute("SELECT id, model, arch_db FROM ir_ui_view WHERE arch_db ILIKE '%default_order=%'")
        bad_views = []
        for vid, model_name, arch in cr.fetchall():
            try:
                root = etree.fromstring(arch.encode('utf-8'))
            except Exception:
                continue
            trees = root.xpath(".//tree[@default_order]")
            if not trees:
                continue
            # collect model fields
            cr.execute("SELECT name FROM ir_model_fields WHERE model=%s", (model_name,))
            md_fields = set(r[0] for r in cr.fetchall())
            invalid = False
            for t in trees:
                default_order = t.get('default_order')
                for token in [x.strip() for x in default_order.split(',') if x.strip()]:
                    fname = token.split()[0]
                    if fname not in md_fields:
                        invalid = True
            if invalid:
                bad_views.append(vid)
        if bad_views:
            cr.execute("INSERT INTO backup_problematic_ir_ui_view SELECT * FROM ir_ui_view WHERE id IN %s", (tuple(bad_views),))
            cr.execute("UPDATE ir_ui_view SET active=false WHERE id IN %s", (tuple(bad_views),))
            cr.execute("DELETE FROM ir_model_data WHERE model='ir.ui.view' AND res_id IN %s", (tuple(bad_views),))
    except Exception:
        pass
