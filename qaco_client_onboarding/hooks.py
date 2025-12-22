import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def pre_init_hook(cr):
    """Pre-init hook to clean up stale compatibility view records and prevent
    upgrade-time XPath/Parse errors caused by views that target removed UI elements.

    Behavior:
    - Create backup tables (if not present) and copy offending `ir_ui_view` and
      related `ir.model.data` rows into them for safe recovery.
    - Deactivate the offending views (`active = False`) so Odoo won't parse them.
    - Remove the `ir.model.data` entries that would cause the upgrade to reapply
      the broken inheritance.

    The hook is intentionally best-effort and will swallow errors to avoid
    blocking module installation/upgrade when the DB is in an unexpected state.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    try:
        # patterns to look for in view.arch_db which indicate problematic compatibility patches
        patterns = [
            'o_attach_selected',
            'template_library_rel_ids',
            'Attach selected',
            'Open Template Library',
            'template_library',
            'o_tpl_download',
            'o_tpl_attach',
            'o_open_template_library',
        ]

        # Build dynamic SQL WHERE clause from patterns
        like_clauses = " OR ".join([f"arch_db ILIKE '%{p}%'" for p in patterns])

        # Create backup tables if not exist
        try:
            cr.execute("CREATE TABLE IF NOT EXISTS backup_problematic_ir_ui_view AS SELECT * FROM ir_ui_view WHERE false")
            cr.execute("CREATE TABLE IF NOT EXISTS backup_problematic_ir_model_data AS SELECT * FROM ir_model_data WHERE false")
        except Exception:
            _logger.debug('Could not ensure backup tables exist; continuing anyway', exc_info=True)

        # Copy problematic views into backup table (idempotent insert behaviour handled by DB uniqueness if needed)
        try:
            insert_views_sql = (
                "INSERT INTO backup_problematic_ir_ui_view SELECT v.* FROM ir_ui_view v WHERE " + like_clauses
            )
            cr.execute(insert_views_sql)
        except Exception:
            _logger.debug('Failed to copy problematic ir_ui_view rows into backup table', exc_info=True)

        # Find problematic view ids
        try:
            cr.execute("SELECT id FROM ir_ui_view WHERE " + like_clauses)
            view_ids = [r[0] for r in cr.fetchall()]
        except Exception:
            view_ids = []

        # Also ensure explicit cleanup of templates view if present
        try:
            specific_view = env.ref('qaco_client_onboarding.view_client_onboarding_form_templates_section', raise_if_not_found=False)
            if specific_view and getattr(specific_view, 'id', False) and specific_view.id not in view_ids:
                view_ids.append(specific_view.id)
                try:
                    cr.execute("INSERT INTO backup_problematic_ir_ui_view SELECT v.* FROM ir_ui_view v WHERE id=%s", (specific_view.id,))
                except Exception:
                    _logger.debug('Failed to back up specific templates view', exc_info=True)
        except Exception:
            _logger.debug('Error checking for specific templates view', exc_info=True)

        if view_ids:
            _logger.info('Pre-init: found %d problematic views, deactivating and backing up', len(view_ids))

            # Back up any ir.model.data rows referring to these views
            try:
                cr.execute(
                    "INSERT INTO backup_problematic_ir_model_data SELECT md.* FROM ir_model_data md WHERE md.model='ir.ui.view' AND md.res_id IN %s",
                    (tuple(view_ids),),
                )
            except Exception:
                _logger.debug('Failed to copy problematic ir.model.data rows into backup table', exc_info=True)

            # Deactivate views and remove their ir.model.data entries
            try:
                # Deactivate views
                cr.execute("UPDATE ir_ui_view SET active = false WHERE id IN %s", (tuple(view_ids),))
            except Exception:
                _logger.debug('Failed to deactivate problematic views', exc_info=True)

            try:
                # Remove model data entries pointing to the deactivated views so upgrades don't try to reapply them
                cr.execute("DELETE FROM ir_model_data WHERE model='ir.ui.view' AND res_id IN %s", (tuple(view_ids),))
            except Exception:
                _logger.debug('Failed to remove ir.model.data entries for problematic views', exc_info=True)

        # Lastly, remove any stray model-data entries created by earlier fix attempts that match common fix names
        try:
            stale_md = env['ir.model.data'].search([('module', '=', 'qaco_client_onboarding'), ('name', 'ilike', 'fix%attach%')])
            if stale_md:
                _logger.info('Pre-init: removing %d stale ir.model.data records created by earlier fixes', len(stale_md))
                for md in stale_md:
                    try:
                        rec = md.model and env[md.model].browse(md.res_id)
                        if rec:
                            try:
                                rec.unlink()
                            except Exception:
                                pass
                    except Exception:
                        pass
                    try:
                        md.unlink()
                    except Exception:
                        pass
        except Exception:
            _logger.debug('Error while cleaning stale ir.model.data by name', exc_info=True)

        # Defensive cleanup: find ir.model.fields that reference missing models (relation not present in ir.model)
        try:
            cr.execute("CREATE TABLE IF NOT EXISTS backup_problematic_ir_model_fields AS SELECT * FROM ir_model_fields WHERE false")
        except Exception:
            _logger.debug('Could not ensure backup table for ir.model.fields exists; continuing', exc_info=True)
        try:
            cr.execute("SELECT id FROM ir_model_fields f WHERE f.relation IS NOT NULL AND f.relation NOT IN (SELECT model FROM ir_model)")
            missing_fields = [r[0] for r in cr.fetchall()]
            if missing_fields:
                _logger.info('Pre-init: found %d ir.model.fields with missing relation model; backing up and removing', len(missing_fields))
                try:
                    cr.execute("INSERT INTO backup_problematic_ir_model_fields SELECT * FROM ir_model_fields WHERE id IN %s", (tuple(missing_fields),))
                except Exception:
                    _logger.debug('Failed to backup problematic ir.model.fields rows', exc_info=True)
                try:
                    cr.execute("DELETE FROM ir_model_fields WHERE id IN %s", (tuple(missing_fields),))
                except Exception:
                    _logger.debug('Failed to delete problematic ir.model.fields rows', exc_info=True)
        except Exception:
            _logger.exception('Error while checking for problematic ir.model.fields (continuing)')

        # Defensive cleanup: scan views for invalid default_order attributes referencing missing fields
        try:
            cr.execute("SELECT id, model, arch_db FROM ir_ui_view WHERE arch_db ILIKE '%default_order=%'")
            bad_views = []
            for vid, model_name, arch in cr.fetchall():
                try:
                    from lxml import etree
                    root = etree.fromstring(arch.encode('utf-8'))
                    # find all tree nodes with default_order
                    trees = root.xpath(".//tree[@default_order]")
                    if not trees:
                        continue
                    # collect model fields
                    md_fields = set(f.name for f in env['ir.model.fields'].search([('model', '=', model_name)]))
                    invalid = False
                    for t in trees:
                        default_order = t.get('default_order')
                        # split by comma and check each field token (field_name or field_name asc/desc)
                        for token in [x.strip() for x in default_order.split(',') if x.strip()]:
                            fname = token.split()[0]
                            if fname not in md_fields:
                                invalid = True
                                _logger.warning('Pre-init: view %s Default order references unknown field %s on model %s', vid, fname, model_name)
                    if invalid:
                        bad_views.append(vid)
                except Exception:
                    _logger.debug('Failed to parse view arch for view id %s', vid, exc_info=True)
            if bad_views:
                _logger.info('Pre-init: backing up and deactivating %d views due to invalid default_order', len(bad_views))
                try:
                    cr.execute("INSERT INTO backup_problematic_ir_ui_view SELECT v.* FROM ir_ui_view v WHERE id IN %s", (tuple(bad_views),))
                except Exception:
                    _logger.debug('Failed to back up problematic views with invalid default_order', exc_info=True)
                try:
                    cr.execute("UPDATE ir_ui_view SET active = false WHERE id IN %s", (tuple(bad_views),))
                except Exception:
                    _logger.debug('Failed to deactivate problematic views with invalid default_order', exc_info=True)
                try:
                    cr.execute("DELETE FROM ir_model_data WHERE model='ir.ui.view' AND res_id IN %s", (tuple(bad_views),))
                except Exception:
                    _logger.debug('Failed to remove ir.model.data entries for problematic views with invalid default_order', exc_info=True)
        except Exception:
            _logger.exception('Error while scanning views for invalid default_order (continuing)')

        # Defensive cleanup: One2many fields whose inverse_name is missing on the relation model
        try:
            cr.execute("CREATE TABLE IF NOT EXISTS backup_problematic_ir_model_fields AS SELECT * FROM ir_model_fields WHERE false")
            cr.execute("SELECT f.id, f.model, f.name, f.relation, f.inverse_name FROM ir_model_fields f WHERE f.ttype='one2many' AND (f.inverse_name IS NULL OR f.inverse_name = '' OR NOT EXISTS (SELECT 1 FROM ir_model_fields rf WHERE rf.model = f.relation AND rf.name = f.inverse_name))")
            rows = cr.fetchall()
            if rows:
                ids = [r[0] for r in rows]
                _logger.info('Pre-init: found %d One2many fields with missing inverse on relation model; backing up and removing', len(ids))
                try:
                    cr.execute("INSERT INTO backup_problematic_ir_model_fields SELECT * FROM ir_model_fields WHERE id IN %s", (tuple(ids),))
                except Exception:
                    _logger.debug('Failed to backup problematic One2many ir.model.fields', exc_info=True)
                try:
                    cr.execute("DELETE FROM ir_model_fields WHERE id IN %s", (tuple(ids),))
                except Exception:
                    _logger.debug('Failed to delete problematic One2many ir.model.fields', exc_info=True)
        except Exception:
            _logger.exception('Error while checking One2many inverse consistency (continuing)')
    except Exception:
        # swallow any error: the cleanup is best-effort and must not block upgrades
        _logger.exception('Pre-init hook failed during defensive cleanup (continuing)')
