#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manual database fix script for firm_name field migration
Run this script using Odoo shell BEFORE upgrading the module:

odoo-bin shell -d your_database --config=/path/to/odoo.conf

Then in the shell, run:
exec(open('/path/to/this/script.py').read())
"""

import logging

_logger = logging.getLogger(__name__)

def fix_firm_name_field():
    """Fix firm_name field before module upgrade"""
    cr = env.cr
    
    _logger.info("=" * 60)
    _logger.info("Starting manual firm_name field fix")
    _logger.info("=" * 60)
    
    # Step 1: Check current state
    cr.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name='qaco_audit' AND column_name='firm_name'
    """)
    result = cr.fetchone()
    
    if not result:
        print("✓ No firm_name column found - nothing to fix")
        return
    
    print(f"Found firm_name column: type={result[1]}")
    
    if result[1] not in ('character varying', 'varchar', 'text'):
        print("✓ firm_name is already Many2one - nothing to fix")
        return
    
    # Step 2: Rename the column
    print("Step 1: Renaming firm_name to firm_name_old...")
    cr.execute("""
        ALTER TABLE qaco_audit 
        RENAME COLUMN firm_name TO firm_name_old
    """)
    print("✓ Column renamed")
    
    # Step 3: Clean up field metadata
    print("Step 2: Removing old field metadata...")
    cr.execute("""
        DELETE FROM ir_model_fields 
        WHERE model='qaco.audit' AND name='firm_name'
    """)
    deleted = cr.rowcount
    print(f"✓ Deleted {deleted} field metadata records")
    
    # Step 4: Clean up selection values if they exist
    print("Step 3: Cleaning up selection values...")
    cr.execute("""
        DELETE FROM ir_model_fields_selection 
        WHERE field_id IN (
            SELECT id FROM ir_model_fields 
            WHERE model='qaco.audit' AND name='firm_name'
        )
    """)
    deleted = cr.rowcount
    print(f"✓ Deleted {deleted} selection value records")
    
    # Step 5: Commit changes
    cr.commit()
    print("✓ Changes committed")
    
    # Step 6: Show summary
    cr.execute("""
        SELECT firm_name_old, COUNT(*) 
        FROM qaco_audit 
        WHERE firm_name_old IS NOT NULL 
        GROUP BY firm_name_old
    """)
    
    print("\nData to be migrated:")
    for row in cr.fetchall():
        print(f"  - {row[0]}: {row[1]} records")
    
    print("\n" + "=" * 60)
    print("✓ Manual fix completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Exit the Odoo shell")
    print("2. Upgrade the qaco_audit module from the UI")
    print("3. The post-migration script will convert the data")
    print("=" * 60)

# Run the fix
if __name__ == '__main__' or 'env' in dir():
    fix_firm_name_field()
