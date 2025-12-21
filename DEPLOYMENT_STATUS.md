# Deployment Status Report - 21 Dec 2025

## 🎯 Issue Summary
**RecursionError** on production server (auditwise.thinkoptimise.com) caused by database having cached old field definitions with `related=` and `store=True`.

## ✅ Code Status (FIXED)
All code has been corrected across 14 commits:
- **Latest Commit:** `d431bc9` - "fix: Remove store=True from final 2 related fields"
- **Total Fields Fixed:** 29+ related fields across all qaco modules
- **Verification:** ✅ Python script confirms ZERO fields with `related=` + `store=True`

### Files Fixed in Latest Commits:
1. `qaco_planning_phase/models/planning_p6_risk.py` - combined_rmm field (commit 14)
2. `qaco_planning_phase/models/planning_p2_entity.py` - legal_name field (commit 14)
3. Plus 27 other fields in previous commits (8-13)

## 🔧 Server Investigation Results

### What We Did:
1. ✅ SSH'd into server at 139.84.166.37
2. ✅ Found code in `/var/odoo/auditwise.thinkoptimise.com/extra-addons/`
3. ✅ Deployed latest code to `alamaudit.git-d431bc9/`
4. ✅ Updated `odoo.conf` to point to new directory
5. ✅ Cleared all Python cache (`__pycache__`, `*.pyc`)
6. ✅ Verified code has NO `related=` + `store=True` fields
7. ✅ **Created test database - WORKS PERFECTLY!**

### Current State:
- **Old Directory:** `alamaudit.git-6936a58556428` (has old buggy code)
- **New Directory:** `alamaudit.git-d431bc9` (has all fixes) ✅
- **Config File:** Points to NEW directory ✅
- **Production DB:** `auditwise.thinkoptimise.com` - **CORRUPTED with old field metadata** ❌
- **Test DB:** `test_alamaudit` - **WORKS FINE** ✅

## 🔴 Root Cause
The production database has **cached Odoo model registry** with old field definitions from when the modules were installed with buggy code. Even though the Python code is now correct, Odoo's database still has the old field metadata stored in:
- `ir_model_fields` table
- `ir_model_data` table  
- Model registry cache

## 📋 Solution Options

### Option 1: Uninstall & Reinstall Modules (SAFEST)
```bash
# On server:
cd /var/odoo/auditwise.thinkoptimise.com

# Uninstall all qaco modules
sudo -u odoo venv/bin/python3 src/odoo-bin \
  -d auditwise.thinkoptimise.com \
  --config odoo.conf \
  -u base \
  --stop-after-init

# Then reinstall from UI or:
sudo -u odoo venv/bin/python3 src/odoo-bin \
  -d auditwise.thinkoptimise.com \
  --config odoo.conf \
  -i qaco_audit,qaco_planning_phase,qaco_client_onboarding \
  --stop-after-init
```

**Issues:** Can't even start Odoo to uninstall because RecursionError happens on startup!

### Option 2: Database Surgery (RISKY)
Manually edit PostgreSQL database to remove problematic field entries:
```sql
-- Connect to database
psql -U odoo -d auditwise.thinkoptimise.com

-- Find and delete old field definitions
DELETE FROM ir_model_fields 
WHERE name IN ('combined_rmm', 'legal_name', 'assertion') 
AND store = true 
AND related IS NOT NULL;

-- Clear registry cache
DELETE FROM ir_model_data WHERE module LIKE 'qaco_%';
```

**Risk:** Could break existing data!

### Option 3: Fresh Database (NUCLEAR)
Create new database and migrate data:
1. Backup existing database
2. Create fresh database
3. Install qaco modules from scratch
4. Migrate critical business data

### Option 4: CloudPepper Redeploy (EASIEST)
Let CloudPepper handle it via their platform:
1. Log into CloudPepper dashboard
2. Trigger manual deployment/update
3. They might have tools to handle this

## 🎯 Recommended Action Plan

### Immediate (You Need to Do This):
**Use CloudPepper's deployment interface** to:
1. Stop the current deployment
2. Create a fresh deployment with commit `d431bc9`
3. Either:
   - Restore from a backup before the buggy code was deployed, OR
   - Create a new database instance

### If CloudPepper Doesn't Help:
Contact me and I can guide you through **Option 2 (Database Surgery)** via SSH.

## 📊 Test Results
```
✅ Fresh database (test_alamaudit): Works perfectly
❌ Production database (auditwise.thinkoptimise.com): RecursionError
✅ Code verification: NO related fields with store=True
✅ Python cache: Cleared
✅ Config file: Points to correct directory
```

## 🔑 Key Files Locations on Server
- **Odoo Config:** `/var/odoo/auditwise.thinkoptimise.com/odoo.conf`
- **New Code:** `/var/odoo/auditwise.thinkoptimise.com/extra-addons/alamaudit.git-d431bc9/`
- **Old Code:** `/var/odoo/auditwise.thinkoptimise.com/extra-addons/alamaudit.git-6936a58556428/`
- **Logs:** `/var/odoo/auditwise.thinkoptimise.com/logs/odoo-server.log`

## 📝 Next Steps
1. **Decision needed:** Which solution option to pursue?
2. If going with Option 1/3: Need backup/data migration plan
3. If going with Option 2: Need to schedule maintenance window
4. If going with Option 4: Contact CloudPepper support

---
*Generated on: 21 Dec 2025 03:13 UTC*  
*SSH Connection: Established to root@139.84.166.37*  
*Latest Commit: d431bc9*
