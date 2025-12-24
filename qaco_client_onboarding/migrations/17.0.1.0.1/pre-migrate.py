# -*- coding: utf-8 -*-
"""
Pre-migration script to remove incompatible inherited view records
that extend the client_onboarding_form with xpath queries.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Remove the template section inherited view that's incompatible with the simplified form.
    This view tries to find elements that don't exist in the minimal form structure.
    """
    _logger.info("Removing incompatible inherited view: view_client_onboarding_form_templates_section")
    
    # Delete the inherited view record by XML ID
    cr.execute("""
        DELETE FROM ir_ui_view 
        WHERE id IN (
            SELECT res_id 
            FROM ir_model_data 
            WHERE module = 'qaco_client_onboarding' 
            AND name = 'view_client_onboarding_form_templates_section'
        )
    """)
    
    # Also delete the ir_model_data record
    cr.execute("""
        DELETE FROM ir_model_data 
        WHERE module = 'qaco_client_onboarding' 
        AND name = 'view_client_onboarding_form_templates_section'
    """)
    
    _logger.info("Successfully removed incompatible inherited view")
