#!/bin/bash
# Quick fix script for firm_name field migration
# Run this on the server before upgrading the module

set -e

echo "=========================================="
echo "Firm Name Field Migration Fix"
echo "=========================================="
echo ""

# Get database name
read -p "Enter database name: " DB_NAME

if [ -z "$DB_NAME" ]; then
    echo "Error: Database name is required"
    exit 1
fi

echo ""
echo "Applying fix to database: $DB_NAME"
echo ""

# Run the SQL fix
sudo -u postgres psql -d "$DB_NAME" << 'EOF'
BEGIN;

DO $$
DECLARE
    col_type text;
    deleted_fields int;
    deleted_selections int;
BEGIN
    SELECT data_type INTO col_type
    FROM information_schema.columns 
    WHERE table_name='qaco_audit' AND column_name='firm_name';
    
    IF col_type IN ('character varying', 'varchar', 'text') THEN
        RAISE NOTICE '✓ Found firm_name Selection field';
        
        -- Rename the column
        RAISE NOTICE 'Renaming firm_name to firm_name_old...';
        ALTER TABLE qaco_audit RENAME COLUMN firm_name TO firm_name_old;
        RAISE NOTICE '✓ Column renamed';
        
        -- Delete old field metadata
        DELETE FROM ir_model_fields 
        WHERE model='qaco.audit' AND name='firm_name';
        GET DIAGNOSTICS deleted_fields = ROW_COUNT;
        RAISE NOTICE '✓ Deleted % field metadata records', deleted_fields;
        
        -- Delete selection values
        DELETE FROM ir_model_fields_selection 
        WHERE field_id IN (
            SELECT id FROM ir_model_fields 
            WHERE model='qaco.audit' AND name='firm_name'
        );
        GET DIAGNOSTICS deleted_selections = ROW_COUNT;
        RAISE NOTICE '✓ Deleted % selection value records', deleted_selections;
        
        RAISE NOTICE '';
        RAISE NOTICE '========================================';
        RAISE NOTICE '✓ Fix completed successfully!';
        RAISE NOTICE '========================================';
    ELSE
        RAISE NOTICE 'ℹ firm_name field is already Many2one or does not exist - no fix needed';
    END IF;
END $$;

-- Show migration summary
SELECT 
    COALESCE(firm_name_old, '(NULL)') as "Old Firm Name", 
    COUNT(*) as "Records"
FROM qaco_audit 
GROUP BY firm_name_old
ORDER BY COUNT(*) DESC;

COMMIT;
EOF

echo ""
echo "=========================================="
echo "Next steps:"
echo "1. Restart Odoo service:"
echo "   sudo systemctl restart odoo"
echo "2. Upgrade the qaco_audit module from UI"
echo "=========================================="
