# Migration Guide: Firm Name Field Conversion

## Overview
This migration converts the `firm_name` field from a hardcoded Selection field to a dynamic Many2one field linked to `audit.firm.name` configuration.

## ⚠️ IMPORTANT - Error Fix Required

If you're seeing this error:
```
AttributeError: 'str' object has no attribute 'get'
```

You MUST run the manual fix **BEFORE** upgrading the module.

## Quick Fix Steps

### Option 1: Using the bash script (Easiest)

```bash
cd /var/odoo/alamaudit.thinkoptimise.com/extra-addons/alamaudit.git-*/qaco_audit/migrations/17.0.0.0.4
chmod +x apply_fix.sh
./apply_fix.sh
# Enter your database name when prompted
```

### Option 2: Using SQL directly

```bash
# Replace 'your_database_name' with your actual database name
sudo -u postgres psql -d your_database_name -f fix_firm_name.sql
```

### Option 3: Manual psql commands

```bash
sudo -u postgres psql -d your_database_name
```

Then run:
```sql
-- Rename the column
ALTER TABLE qaco_audit RENAME COLUMN firm_name TO firm_name_old;

-- Delete field metadata
DELETE FROM ir_model_fields WHERE model='qaco.audit' AND name='firm_name';

-- Commit
COMMIT;
\q
```

## After Running the Fix

1. **Restart Odoo:**
   ```bash
   sudo systemctl restart odoo
   ```

2. **Upgrade the module** from the Odoo UI (Apps → QACO Audit → Upgrade)

3. The migration scripts will now run automatically and convert the data

## Migration Process

### Option 1: Automatic Migration (Recommended)

1. **Pull latest code** from repository
2. **Restart Odoo service**
3. **Upgrade module** from Apps menu
4. Migration scripts will run automatically:
   - `pre-migrate.py`: Renames old column and cleans metadata
   - Module upgrade creates new field and data
   - `post-migrate.py`: Migrates old data to new format
   - `end-migrate.py`: Final cleanup

### Option 2: Manual Fix (If automatic migration fails)

If you encounter errors during upgrade:

1. **Run manual fix script** via Odoo shell:
   ```bash
   cd /var/odoo/alamaudit.thinkoptimise.com
   ./odoo-bin shell -d your_database_name -c odoo.conf
   ```

2. **In the Odoo shell**, run:
   ```python
   exec(open('/path/to/extra-addons/qaco_audit/migrations/17.0.0.0.4/manual_fix.py').read())
   ```

3. **Exit shell** and upgrade module from UI

## Data Mapping

Old Selection values are mapped to new firm records:

| Old Value        | New Record XML ID                    |
|-----------------|--------------------------------------|
| Alam Aulakh     | qaco_audit.firm_name_alam_aulakh    |
| QACO            | qaco_audit.firm_name_qaco           |
| Baker Tilly     | qaco_audit.firm_name_baker_tilly    |
| 3rd party Firm  | qaco_audit.firm_name_3rd_party      |

## Verification

After migration, verify:

1. All audit records have correct firm names
2. No `firm_name_old` column exists: 
   ```sql
   SELECT column_name FROM information_schema.columns 
   WHERE table_name='qaco_audit' AND column_name='firm_name_old';
   ```
3. Firm Names configuration menu is accessible
4. Can add new firm names via Configuration menu

## Rollback

If issues occur and you need to rollback:

1. Restore database backup
2. Revert code to version 17.0.0.0.3
3. Restart Odoo

## Support

If migration fails, check logs at:
- `/var/log/odoo/odoo.log`

Look for lines containing:
- "Starting pre-migration for qaco_audit 17.0.0.0.4"
- "Starting post-migration for qaco_audit 17.0.0.0.4"
