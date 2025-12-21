from odoo import api, SUPERUSER_ID


def pre_init_hook(cr):
    """Pre-init hook to clean up stale view records left by earlier attempts.

    This hook performs a best-effort cleanup of any previously-created compatibility
    view that targeted a now-removed element (the 'Attach selected' button). Such a
    stale view causes an XPath parse error during module update; removing the view
    and its ir.model.data entry prevents the upgrade from failing.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    try:
        # 1) Remove by known xmlid if present
        xmlid = 'qaco_client_onboarding.view_client_onboarding_form.fix.attach.button'
        view = env.ref(xmlid, raise_if_not_found=False)
        if view and getattr(view, '_name', '') == 'ir.ui.view':
            try:
                # Remove any related ir.model.data first
                model_data = env['ir.model.data'].search([('module', '=', 'qaco_client_onboarding'), ('res_id', '=', view.id)])
                if model_data:
                    model_data.unlink()
            except Exception:
                pass
            try:
                view.unlink()
            except Exception:
                pass

        # 2) Broad cleanup: remove any ir.ui.view that references the old class or template field in its arch
        bad_views = env['ir.ui.view'].search([('arch_db', 'ilike', 'o_attach_selected')])
        bad_views += env['ir.ui.view'].search([('arch_db', 'ilike', 'template_library_rel_ids')])
        for bv in bad_views:
            try:
                # Also remove any ir.model.data pointing to it
                md = env['ir.model.data'].search([('module', '=', bv.module), ('res_id', '=', bv.id)])
                if md:
                    md.unlink()
            except Exception:
                pass
            try:
                bv.unlink()
            except Exception:
                pass

        # 3) Defensive remove by name pattern if any remaining model data entries exist
        stale_md = env['ir.model.data'].search([('module', '=', 'qaco_client_onboarding'), ('name', 'ilike', 'fix%attach%')])
        for md in stale_md:
            try:
                # try to unlink referenced record first
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
        # swallow all errors: best-effort cleanup should not block upgrades
        pass
