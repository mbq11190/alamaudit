# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Post-migration script to convert firm_name data from old Selection values to Many2one references
    """
    _logger.info("Starting post-migration for qaco_audit 17.0.0.0.4")
    
    # Check if the old firm_name_old column exists
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='qaco_audit' AND column_name='firm_name_old'
    """)
    
    if not cr.fetchone():
        _logger.info("No firm_name_old column found, migration already completed or not needed")
        return
    
    _logger.info("Migrating firm_name data from Selection to Many2one")
    
    # Mapping of old selection values to firm name records
    firm_mapping = {
        'Alam Aulakh': 'qaco_audit.firm_name_alam_aulakh',
        'QACO': 'qaco_audit.firm_name_qaco',
        'Baker Tilly': 'qaco_audit.firm_name_baker_tilly',
        '3rd party Firm': 'qaco_audit.firm_name_3rd_party',
    }
    
    # Update each record based on old value
    for old_value, xml_id in firm_mapping.items():
        _logger.info(f"Migrating records with firm_name_old='{old_value}'")
        
        cr.execute("""
            UPDATE qaco_audit
            SET firm_name = (
                SELECT res_id 
                FROM ir_model_data 
                WHERE module='qaco_audit' AND name=%s
                LIMIT 1
            )
            WHERE firm_name_old = %s
        """, (xml_id.split('.')[1], old_value))
        
        _logger.info(f"Updated {cr.rowcount} records")
    
    # Drop the old column
    _logger.info("Dropping old firm_name_old column")
    cr.execute("ALTER TABLE qaco_audit DROP COLUMN firm_name_old")
    
    _logger.info("Post-migration completed successfully")
