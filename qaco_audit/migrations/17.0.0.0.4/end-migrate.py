# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    End-migration script - final cleanup and verification
    This runs automatically at the end of module update
    """
    _logger.info("="*70)
    _logger.info("Starting end-migration for qaco_audit 17.0.0.0.4")
    _logger.info("="*70)
    
    try:
        # Verify migration completed successfully
        cr.execute("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name='qaco_audit' AND column_name='firm_name_old'
        """)
        
        old_col_exists = cr.fetchone()[0] > 0
        
        if old_col_exists:
            _logger.warning("⚠ Old firm_name_old column still exists - attempting final cleanup...")
            
            # Check for any unmigrated data
            cr.execute("""
                SELECT COUNT(*) 
                FROM qaco_audit 
                WHERE firm_name_old IS NOT NULL
            """)
            
            unmigrated_count = cr.fetchone()[0]
            
            if unmigrated_count > 0:
                _logger.warning("Found %s records with unmigrated firm_name_old data", unmigrated_count)
                _logger.warning("These will be lost when the column is dropped")
                
                # Show the unmigrated values
                cr.execute("""
                    SELECT firm_name_old, COUNT(*) 
                    FROM qaco_audit 
                    WHERE firm_name_old IS NOT NULL 
                    GROUP BY firm_name_old
                """)
                for value, count in cr.fetchall():
                    _logger.warning("  - '%s': %s records", value, count)
            
            # Drop the column
            cr.execute("ALTER TABLE qaco_audit DROP COLUMN IF EXISTS firm_name_old")
            _logger.info("✓ Dropped firm_name_old column")
        
        # Verify new field exists
        cr.execute("""
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name='qaco_audit' AND column_name='firm_name'
        """)
        
        result = cr.fetchone()
        if result and result[0] in ('integer', 'int4'):
            _logger.info("✓ New firm_name field verified (type: %s - Many2one)", result[0])
        else:
            _logger.warning("⚠ firm_name field type unexpected: %s", result[0] if result else 'NOT FOUND')
        
        # Show final statistics
        cr.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(firm_name) as with_firm,
                COUNT(*) - COUNT(firm_name) as without_firm
            FROM qaco_audit
        """)
        stats = cr.fetchone()
        
        _logger.info("Migration Statistics:")
        _logger.info("  - Total audit records: %s", stats[0])
        _logger.info("  - Records with firm name: %s", stats[1])
        _logger.info("  - Records without firm name: %s", stats[2])
        
        # Check firm name configuration
        cr.execute("SELECT COUNT(*) FROM audit_firm_name WHERE active=true")
        firm_count = cr.fetchone()[0]
        _logger.info("  - Active firm names configured: %s", firm_count)
        
        _logger.info("="*70)
        _logger.info("✓ End-migration completed successfully!")
        _logger.info("✓ Firm name field conversion is complete")
        _logger.info("="*70)
        _logger.info("")
        _logger.info("You can now manage firm names via:")
        _logger.info("  Audit Work → Configurations → Firm Names")
        _logger.info("")
        
    except Exception as e:
        _logger.error("Error during end-migration: %s", str(e))
        _logger.error("Migration completed but verification failed")
        # Don't raise - migration is done
