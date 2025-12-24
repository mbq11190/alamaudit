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
    
    This runs BEFORE any XML loading, so it prevents the xpath parsing error.
    """
    _logger.info("=" * 80)
    _logger.info("MIGRATION: Removing incompatible inherited view records")
    _logger.info("=" * 80)
    
    try:
        # First, find the view ID from ir_model_data
        cr.execute("""
            SELECT res_id 
            FROM ir_model_data 
            WHERE module = 'qaco_client_onboarding' 
            AND name = 'view_client_onboarding_form_templates_section'
            AND model = 'ir.ui.view'
        """)
        result = cr.fetchone()
        
        if result:
            view_id = result[0]
            _logger.info(f"Found problematic view with ID: {view_id}")
            
            # Delete the view record
            cr.execute("DELETE FROM ir_ui_view WHERE id = %s", (view_id,))
            _logger.info(f"Deleted ir_ui_view record ID {view_id}")
            
            # Delete the ir_model_data record
            cr.execute("""
                DELETE FROM ir_model_data 
                WHERE module = 'qaco_client_onboarding' 
                AND name = 'view_client_onboarding_form_templates_section'
            """)
            _logger.info("Deleted ir_model_data record")
            
            _logger.info("Successfully removed incompatible inherited view")
        else:
            _logger.info("No problematic view found - already cleaned up or never existed")
            
    except Exception as e:
        _logger.error(f"Error during migration: {e}", exc_info=True)
        # Don't raise - allow upgrade to continue
    
    _logger.info("=" * 80)
