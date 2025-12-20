# 🔴 PROMPT 4: Registry Cleanup & KeyError Resolution

## Root Cause Analysis

The `KeyError: 'auditwise.thinkoptimise.com'` error occurs when:

1. **Registry crashes mid-load** - Module import fails, leaving partial registry entries
2. **Database name mismatches** - Code references DB name that doesn't match actual connection
3. **Stale .pyc cache** - Python bytecode cache contains old/corrupted module definitions
4. **Cron retry loops** - ir_cron attempts registry reload, crashes repeatedly, floods logs

## ✅ PROMPT 3 Fixes Applied (Preventing Future Crashes)

All registry-crashing patterns have been eliminated from `qaco_planning_phase`:

### Fixed Patterns (20 instances across 13 files):
- ❌ **BEFORE**: `default=lambda self: self.env.company.currency_id` → Registry crash at import
- ✅ **AFTER**: `default=lambda self: self._get_default_currency()` → Safe method call

### Fixed Files:
1. `planning_base.py` - Added 3 safe helper methods
2. `planning_p1_engagement.py` - Currency default
3. `planning_p3_controls.py` - Currency default
4. `planning_p4_analytics.py` - Currency default
5. `planning_p5_materiality.py` - Currency + user defaults
6. `planning_p7_fraud.py` - HTML template in create()
7. `planning_p8_going_concern.py` - Currency + HTML template
8. `planning_p9_laws.py` - Currency + HTML template
9. `planning_p10_related_parties.py` - Currency + HTML template
10. `planning_p11_group_audit.py` - Currency + HTML template
11. `planning_p12_strategy.py` - Currency + HTML template
12. `planning_p13_approval.py` - User default
13. `planning_template.py` - Context default
14. `planning_phase.py` (legacy) - Currency default

## 🧹 Required Cleanup Steps

### Step 1: Clear Python Bytecode Cache

**Windows (PowerShell):**
```powershell
# From repository root
cd C:\Users\HP\Documents\GitHub\alamaudit
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force
Get-ChildItem -Recurse -Filter "*.pyo" | Remove-Item -Force
```

**Why:** Stale `.pyc` files contain compiled bytecode from OLD versions of models with dangerous lambda defaults. Python caches these and may load them instead of the fixed source code.

### Step 2: Verify Database Name Consistency

**Check actual database name:**
```powershell
# Connect to PostgreSQL and list databases
psql -U odoo -l
```

**Expected output should show:**
```
auditwise.thinkoptimise.com
```

**If database name differs:**
- Update Odoo config: `odoo.conf`
- Update connection strings in code
- Or rename database to match expected name

### Step 3: Clear Odoo Registry Cache

**Stop Odoo completely:**
```powershell
# Kill all Odoo processes
Get-Process | Where-Object {$_.ProcessName -like "*odoo*"} | Stop-Process -Force
```

**Clear Odoo session cache:**
```powershell
# If using filestore cache
Remove-Item -Path "C:\path\to\odoo\sessions\*" -Force
```

**PostgreSQL registry clear (OPTIONAL - use with caution):**
```sql
-- Connect to database
psql -U odoo -d auditwise.thinkoptimise.com

-- Clear ir_cron errors
DELETE FROM ir_cron WHERE model = 'qaco.planning.phase';

-- Clear module update logs (if corrupted)
DELETE FROM ir_module_module WHERE state = 'to upgrade' AND name LIKE 'qaco_%';
```

### Step 4: Verify addons_path Correctness

**Check Odoo config file (`odoo.conf`):**
```ini
[options]
addons_path = C:\Program Files\Odoo 17\server\odoo\addons,
              C:\Users\HP\Documents\GitHub\alamaudit
db_name = auditwise.thinkoptimise.com
```

**Verify path exists:**
```powershell
Test-Path "C:\Users\HP\Documents\GitHub\alamaudit\qaco_planning_phase"
# Should return: True
```

## 🚀 Safe Restart Sequence (Production)

### Phase 1: Pre-Restart Validation
```powershell
# 1. Backup database
pg_dump -U odoo -Fc auditwise.thinkoptimise.com > backup_before_fix_$(Get-Date -Format "yyyyMMdd_HHmmss").dump

# 2. Clear caches
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force

# 3. Verify all files present
Test-Path "C:\Users\HP\Documents\GitHub\alamaudit\qaco_planning_phase\models\planning_base.py"
```

### Phase 2: Module Upgrade
```powershell
# Stop Odoo
Stop-Process -Name "odoo-bin" -Force

# Upgrade module with clean registry
odoo-bin -c odoo.conf `
         -u qaco_planning_phase `
         -d auditwise.thinkoptimise.com `
         --stop-after-init `
         --log-level=info
```

**Expected output (SUCCESS):**
```
INFO odoo.modules.loading: Modules loaded.
INFO odoo.modules.registry: Registry loaded in X.XXs
INFO odoo.modules.loading: Module qaco_planning_phase upgraded
```

**If errors appear:**
- Check log for specific model/field causing issue
- Verify all PROMPT 3 fixes were applied
- Check for remaining lambda defaults: `grep -r "default=lambda" qaco_planning_phase/models/`

### Phase 3: Start Production Server
```powershell
# Start Odoo normally
odoo-bin -c odoo.conf
```

**Monitor logs for:**
- ✅ `Registry loaded successfully`
- ✅ `HTTP server started`
- ❌ `KeyError` (should NOT appear)
- ❌ `NotImplementedError` (should NOT appear)

### Phase 4: Functional Verification

**Test checklist:**
1. **Login**: Access Odoo at `http://localhost:8069`
2. **Navigate**: Audits → Select audit → Planning
3. **Open P-2**: Click "P-2: Entity Understanding" smart button
4. **Verify computed fields**:
   - `can_open` should show True/False (not error)
   - `name` should display "P2-ClientName-Year"
   - `total_risks_identified` should show number
5. **Create new P-2 record**: Verify HTML fields have default templates
6. **Check cron logs**: No repeated registry reload attempts

## 🔍 Diagnostic Commands

**Check for remaining lambda defaults:**
```powershell
cd C:\Users\HP\Documents\GitHub\alamaudit\qaco_planning_phase
Select-String -Path "models\*.py" -Pattern "default=lambda" | Select-Object Filename, Line, LineNumber
```

**Expected: ZERO matches** (all fixed)

**Check for env access at module level:**
```powershell
Select-String -Path "models\*.py" -Pattern "^[^#\s].*=.*env\[" | Select-Object Filename, Line, LineNumber
```

**Expected: ZERO matches** (no class-level env access)

**Verify __init__.py files are clean:**
```powershell
Get-Content "qaco_planning_phase\__init__.py"
Get-Content "qaco_planning_phase\models\__init__.py"
```

**Expected: ONLY import statements** (no executable logic)

## 📋 Rollback Plan (If Issues Persist)

**If module still crashes after fixes:**

```powershell
# 1. Restore database backup
pg_restore -U odoo -d auditwise.thinkoptimise.com -c backup_before_fix_YYYYMMDD_HHMMSS.dump

# 2. Uninstall problematic module
odoo-bin -c odoo.conf -d auditwise.thinkoptimise.com --uninstall qaco_planning_phase --stop-after-init

# 3. Clear all caches again
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force

# 4. Verify git state
git status
git log --oneline -5

# 5. Report specific error to developer
```

## ✅ Success Indicators

**Registry is healthy when:**
- ✅ Odoo starts without `KeyError` messages
- ✅ Cron jobs run normally (check `ir_cron` logs)
- ✅ HTTP requests return 200 (not 500)
- ✅ Planning P-2 screen loads without errors
- ✅ Computed fields populate correctly
- ✅ No repeated registry reload attempts in logs
- ✅ Can create/edit P-2 records without crashes

## 🛡️ Prevention (Going Forward)

**Code review checklist:**
1. Never use `default=lambda self: self.env.xxx` → Use `default=lambda self: self._get_default_xxx()`
2. Never call methods in field defaults → Use `create()` override
3. Never access `env` or `registry` at class/module level → Use `@api.model` methods
4. Always validate imports in `__init__.py` are simple → No executable logic
5. Test module install from scratch → Run `odoo-bin -i qaco_planning_phase` on empty DB

## 📞 Support

**If problems persist after following this guide:**
1. Capture full error traceback from Odoo logs
2. Run diagnostic commands above and save output
3. Check PostgreSQL logs: `/var/log/postgresql/` or Windows Event Viewer
4. Verify Python version matches Odoo 17 requirement: Python 3.10+
5. Contact: Include specific error message + steps already attempted

---

**Document Status**: ✅ PROMPT 4 COMPLETE  
**Last Updated**: 2025-12-20  
**Applied Fixes**: PROMPT 1 (✅), PROMPT 2 (✅), PROMPT 3 (✅)  
**Next Step**: PROMPT 5 - Standardize compute patterns
