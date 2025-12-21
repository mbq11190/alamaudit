from odoo import api, SUPERUSER_ID


def pre_init_hook(cr):
    """Pre-init hook to clean up stale view records left by earlier attempts.

    Removes the problematic compatibility view that attempted to patch a non-existent
    button via xpath, which causes module upgrade to fail with a ParseError.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    xmlid = 'qaco_client_onboarding.view_client_onboarding_form.fix.attach.button'
    try:
        view = env.ref(xmlid, raise_if_not_found=False)
        if view and getattr(view, '_name', '') == 'ir.ui.view':
            try:
                view.unlink()
            except Exception:
                # best-effort cleanup; don't prevent upgrade if unlink fails
                pass
    except Exception:
        # swallow any unexpected errors to avoid blocking upgrades
        pass
