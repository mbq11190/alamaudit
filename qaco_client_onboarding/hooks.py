# -*- coding: utf-8 -*-
import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    """Populate existing onboarding records with active templates on module install/upgrade.

    This ensures the stored many2many `template_library_rel_ids` is populated and
    avoids runtime RPC errors caused by missing virtual/computed relations.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    try:
        onboarding = env['qaco.client.onboarding'].search([])
        if onboarding:
            onboarding.populate_template_library()
            _logger.info('Populated template_library_rel_ids for %s onboarding records.', len(onboarding))
        else:
            _logger.info('No onboarding records to populate.')
    except Exception as e:
        _logger.exception('Failed to populate template library on post-init: %s', e)
