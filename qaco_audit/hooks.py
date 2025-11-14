# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def pre_init_hook(cr):
    """
    Pre-init hook to handle firm_name field conversion
    This runs BEFORE the module is loaded, so it can fix the database schema
    """
    from odoo import sql_db
    
    _logger.info("="*70)
    _logger.info("Running pre-init hook for qaco_audit")
    _logger.info("="*70)
    
    try:
        # Disable triggers temporarily
        cr.execute("SET CONSTRAINTS ALL DEFERRED")
        
        # Check if firm_name column exists and is varchar (Selection field)
        cr.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name='qaco_audit' AND column_name='firm_name'
        """)
        result = cr.fetchone()
        
        if result and result[1] in ('character varying', 'varchar', 'text'):
            _logger.info("Found old firm_name Selection field - fixing...")
            
            # Rename the column
            cr.execute("""
                ALTER TABLE qaco_audit 
                RENAME COLUMN firm_name TO firm_name_old
            """)
            _logger.info("✓ Renamed firm_name to firm_name_old")
            
            # Delete field metadata - this is critical
            cr.execute("""
                DELETE FROM ir_model_fields 
                WHERE model='qaco.audit' AND name='firm_name'
            """)
            deleted_fields = cr.rowcount
            _logger.info("✓ Deleted old field metadata (%s records)", deleted_fields)
            
            # Delete any constraints on the field
            cr.execute("""
                DELETE FROM ir_model_constraint
                WHERE model IN (
                    SELECT id FROM ir_model WHERE model='qaco.audit'
                )
            """)
            
            # Delete selection values
            cr.execute("""
                DELETE FROM ir_model_fields_selection 
                WHERE field_id IN (
                    SELECT id FROM ir_model_fields 
                    WHERE model='qaco.audit' AND name='firm_name'
                )
            """)
            deleted_selections = cr.rowcount
            _logger.info("✓ Deleted selection values (%s records)", deleted_selections)
            
            # Force commit to ensure changes are persisted
            cr.commit()
            
            _logger.info("="*70)
            _logger.info("✓ Pre-init hook completed successfully")
            _logger.info("="*70)
        else:
            _logger.info("No firm_name Selection field found - skipping")
            
    except Exception as e:
        _logger.error("Error in pre-init hook: %s", str(e), exc_info=True)
        # Try to rollback and continue
        try:
            cr.rollback()
        except:
            pass
        raise
