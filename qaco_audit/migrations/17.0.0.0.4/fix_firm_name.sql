-- Manual SQL fix for firm_name field migration
-- Run this SQL script directly on the database BEFORE upgrading the module
-- 
-- Usage:
-- psql -U odoo -d your_database_name -f fix_firm_name.sql

BEGIN;

-- Step 1: Check if firm_name column exists and is varchar/text type
DO $$
DECLARE
    col_type text;
BEGIN
    SELECT data_type INTO col_type
    FROM information_schema.columns 
    WHERE table_name='qaco_audit' AND column_name='firm_name';
    
    IF col_type IN ('character varying', 'varchar', 'text') THEN
        RAISE NOTICE 'Found firm_name Selection field - proceeding with fix';
        
        -- Step 2: Rename the column
        RAISE NOTICE 'Renaming firm_name to firm_name_old...';
        ALTER TABLE qaco_audit RENAME COLUMN firm_name TO firm_name_old;
        
        -- Step 3: Delete old field metadata
        RAISE NOTICE 'Deleting old field metadata...';
        DELETE FROM ir_model_fields 
        WHERE model='qaco.audit' AND name='firm_name';
        
        -- Step 4: Delete selection values if they exist
        RAISE NOTICE 'Deleting selection values...';
        DELETE FROM ir_model_fields_selection 
        WHERE field_id IN (
            SELECT id FROM ir_model_fields 
            WHERE model='qaco.audit' AND name='firm_name'
        );
        
        RAISE NOTICE 'Fix completed successfully!';
    ELSE
        RAISE NOTICE 'firm_name field is already Many2one or does not exist - no fix needed';
    END IF;
END $$;

COMMIT;

-- Show what data will be migrated
SELECT 
    firm_name_old as "Old Firm Name Value", 
    COUNT(*) as "Number of Records"
FROM qaco_audit 
WHERE firm_name_old IS NOT NULL 
GROUP BY firm_name_old
ORDER BY COUNT(*) DESC;
