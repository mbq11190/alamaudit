# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    End-migration script - final cleanup and verification
    """
    _logger.info("Starting end-migration for qaco_audit 17.0.0.0.4")
    
    # Verify migration completed successfully
    cr.execute("""
        SELECT COUNT(*) 
        FROM information_schema.columns 
        WHERE table_name='qaco_audit' AND column_name='firm_name_old'
    """)
    
    old_col_exists = cr.fetchone()[0] > 0
    
    if old_col_exists:
        _logger.warning("Old firm_name_old column still exists - attempting cleanup")
        
        # Try to migrate any remaining data
        cr.execute("""
            SELECT COUNT(*) 
            FROM qaco_audit 
            WHERE firm_name_old IS NOT NULL AND firm_name IS NULL
        """)
        
        unmigrated_count = cr.fetchone()[0]
        
        if unmigrated_count > 0:
            _logger.warning(f"Found {unmigrated_count} records with unmigrated firm_name data")
            
            # Set to NULL for now - admin can fix manually
            cr.execute("""
                UPDATE qaco_audit 
                SET firm_name_old = NULL 
                WHERE firm_name_old IS NOT NULL AND firm_name IS NULL
            """)
        
        # Now safe to drop the column
        cr.execute("ALTER TABLE qaco_audit DROP COLUMN IF EXISTS firm_name_old")
        _logger.info("Dropped old firm_name_old column")
    
    _logger.info("End-migration completed successfully")
