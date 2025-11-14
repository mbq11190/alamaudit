# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Pre-migration script to handle firm_name field conversion from Selection to Many2one
    """
    _logger.info("Starting pre-migration for qaco_audit 17.0.0.0.4")
    
    # Check if the old firm_name column exists and is a selection field
    cr.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name='qaco_audit' AND column_name='firm_name'
    """)
    result = cr.fetchone()
    
    if result and result[1] in ('character varying', 'varchar', 'text'):
        _logger.info("Renaming old firm_name selection field to firm_name_old")
        # Rename the old selection field to preserve data
        cr.execute("""
            ALTER TABLE qaco_audit 
            RENAME COLUMN firm_name TO firm_name_old
        """)
        _logger.info("Successfully renamed firm_name to firm_name_old")
    else:
        _logger.info("No firm_name selection field found, skipping rename")
