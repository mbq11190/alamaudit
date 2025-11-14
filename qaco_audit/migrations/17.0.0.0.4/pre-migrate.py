# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Pre-migration script to handle firm_name field conversion from Selection to Many2one
    This runs automatically when updating the module - no manual intervention needed!
    """
    _logger.info("="*70)
    _logger.info("Starting pre-migration for qaco_audit 17.0.0.0.4")
    _logger.info("="*70)
    
    try:
        # Check if the old firm_name column exists and is a selection field
        cr.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name='qaco_audit' AND column_name='firm_name'
        """)
        result = cr.fetchone()
        
        if result and result[1] in ('character varying', 'varchar', 'text'):
            _logger.info("Found firm_name Selection field (type: %s)", result[1])
            _logger.info("Converting to Many2one field...")
            
            # Step 1: Rename the old selection field to preserve data
            _logger.info("Step 1: Renaming firm_name to firm_name_old...")
            cr.execute("""
                ALTER TABLE qaco_audit 
                RENAME COLUMN firm_name TO firm_name_old
            """)
            _logger.info("✓ Column renamed successfully")
            
            # Step 2: Remove field metadata to prevent conflicts
            _logger.info("Step 2: Removing old firm_name field metadata...")
            cr.execute("""
                DELETE FROM ir_model_fields 
                WHERE model='qaco.audit' AND name='firm_name'
            """)
            deleted_count = cr.rowcount
            _logger.info("✓ Deleted %s field metadata record(s)", deleted_count)
            
            # Step 3: Remove any selection values
            _logger.info("Step 3: Removing selection values...")
            cr.execute("""
                DELETE FROM ir_model_fields_selection 
                WHERE field_id IN (
                    SELECT id FROM ir_model_fields 
                    WHERE model='qaco.audit' AND name='firm_name'
                )
            """)
            deleted_selections = cr.rowcount
            _logger.info("✓ Deleted %s selection value(s)", deleted_selections)
            
            # Step 4: Show what data will be migrated
            cr.execute("""
                SELECT firm_name_old, COUNT(*) 
                FROM qaco_audit 
                WHERE firm_name_old IS NOT NULL 
                GROUP BY firm_name_old
            """)
            data_summary = cr.fetchall()
            
            if data_summary:
                _logger.info("Data to be migrated in post-migration:")
                for firm, count in data_summary:
                    _logger.info("  - '%s': %s records", firm, count)
            
            _logger.info("="*70)
            _logger.info("✓ Pre-migration completed successfully!")
            _logger.info("="*70)
            
        elif result:
            _logger.info("firm_name field already exists with type %s - skipping migration", result[1])
        else:
            _logger.info("No firm_name field found - this must be a fresh installation")
            
    except Exception as e:
        _logger.error("Error during pre-migration: %s", str(e))
        _logger.error("Migration will continue, but manual intervention may be required")
        # Don't raise - let the migration continue
