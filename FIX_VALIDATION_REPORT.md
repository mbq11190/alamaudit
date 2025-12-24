# Registry Failure Fix - Validation Report

**Date:** 2025-12-23  
**Instance:** auditwise.thinkoptimise.com (Odoo 17)  
**Module:** qaco_client_onboarding  
**Version:** 17.0.1.7.0 → 17.0.1.7.1  

---

## 1. ROOT CAUSE ANALYSIS

### Problem Statement
System failed to initialize database because the Odoo registry could not load during `setup_models()`.

### Stacktrace Signature
```
File .../odoo/fields.py", line 4440, in setup_nonrelated
    invf = comodel._fields[self.inverse_name]
KeyError: 'onboarding_id'
```

This cascaded into:
- `KeyError: 'auditwise.thinkoptimise.com'` in `odoo.tools.lru.__getitem__` (registry cache miss)
- HTTP requests failing with RPC_ERROR
- Cron jobs crashing with registry load failures

### Root Cause Identified

**Broken Relationship:**
```python
# Model: qaco.onboarding.conflict (IndependenceConflict)
# File: qaco_client_onboarding/models/onboarding_independence.py:139
threat_ids = fields.One2many('qaco.onboarding.independence.threat', 'onboarding_id', ...)
                                                                      ^^^^^^^^^^^^^^
                                                                      WRONG INVERSE!
```

**The Problem:**
- `qaco.onboarding.conflict.threat_ids` declares `inverse_name='onboarding_id'`
- `qaco.onboarding.independence.threat.onboarding_id` is a Many2one pointing to `qaco.client.onboarding` (NOT to `qaco.onboarding.conflict`)
- This violates the One2many ↔ Many2one pairing rule
- Registry setup crashes when trying to find the inverse field

**Why It Happened:**
The data model has TWO legitimate uses of `onboarding_id` in the threat model:
1. **Direct threats**: Attached directly to main onboarding (`qaco.client.onboarding`)
2. **Conflict-related threats**: Attached to a conflict of interest record (`qaco.onboarding.conflict`)

The conflict model incorrectly tried to reuse the `onboarding_id` field for its relationship instead of defining a separate foreign key.

---

## 2. FIX IMPLEMENTATION

### Option Applied: **Option A - Add Missing Inverse Field**

### Files Modified

#### File 1: `qaco_client_onboarding/models/onboarding_independence.py`

**Change 1 - Add `conflict_id` field to IndependenceThreat model (Line ~93):**
```python
class IndependenceThreat(models.Model):
    _name = 'qaco.onboarding.independence.threat'
    _description = 'Independence Threat Record'

    onboarding_id = fields.Many2one('qaco.client.onboarding', required=True, ondelete='cascade', index=True)
+   conflict_id = fields.Many2one('qaco.onboarding.conflict', string='Related Conflict', ondelete='cascade', index=True)
    category = fields.Selection(THREAT_CATEGORIES, string='Threat category')
    # ... rest of fields
```

**Change 2 - Fix inverse_name in IndependenceConflict model (Line ~140):**
```python
class IndependenceConflict(models.Model):
    _name = 'qaco.onboarding.conflict'
    _description = 'Conflict of Interest Register'

    onboarding_id = fields.Many2one('qaco.client.onboarding', required=True, ondelete='cascade', index=True)
    conflict_type = fields.Char(string='Conflict type')
    parties_involved = fields.Char(string='Parties involved')
    description = fields.Text(string='Description')
-   threat_ids = fields.One2many('qaco.onboarding.independence.threat', 'onboarding_id', string='Threats')
+   threat_ids = fields.One2many('qaco.onboarding.independence.threat', 'conflict_id', string='Threats')
    proposed_resolution = fields.Text(string='Proposed resolution and safeguards')
    # ... rest of fields
```

#### File 2: `qaco_client_onboarding/__manifest__.py`

**Change 3 - Version bump:**
```python
- 'version': '17.0.1.7.0',
+ 'version': '17.0.1.7.1',
```

### Why No Migration Script Is Needed

Odoo 17 ORM automatically handles:
1. **Column creation**: The `conflict_id` field will be auto-created as `INTEGER` with index
2. **Nullable by default**: Existing threat records remain valid (conflict_id will be NULL)
3. **No data loss**: All existing `onboarding_id` values preserved
4. **Relationship integrity**: Both direct threats and conflict-specific threats now work correctly

---

## 3. UPGRADE INSTRUCTIONS

### Prerequisites
- Database backup completed
- Odoo service stopped (or use --stop-after-init)
- PostgreSQL access available for validation

### Upgrade Command

**Single module upgrade (recommended):**
```bash
./odoo-bin -d auditwise.thinkoptimise.com \
  -u qaco_client_onboarding \
  --stop-after-init \
  --log-level=info
```

**Alternative (if dependencies involved):**
```bash
./odoo-bin -d auditwise.thinkoptimise.com \
  -u all \
  --stop-after-init \
  --log-level=info
```

### Expected Output
```
INFO auditwise.thinkoptimise.com odoo.modules.loading: loading 1 modules...
INFO auditwise.thinkoptimise.com odoo.modules.loading: 1 modules loaded in X.XXs, 0 queries
INFO auditwise.thinkoptimise.com odoo.modules.registry: Registry loaded on db auditwise.thinkoptimise.com
```

---

## 4. VALIDATION CHECKLIST

### A. Upgrade Success
- [ ] **Command exits cleanly**: No Python exceptions in console
- [ ] **Log confirms registry load**: Search for "Registry loaded on db auditwise.thinkoptimise.com"
- [ ] **Module version updated**: Check `ir_module_module` table shows version `17.0.1.7.1`

### B. Database Schema Validation

**Connect to PostgreSQL:**
```bash
psql -U odoo -d auditwise.thinkoptimise.com
```

**Verify column created:**
```sql
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'qaco_onboarding_independence_threat' 
  AND column_name = 'conflict_id';
```

**Expected result:**
```
 column_name | data_type | is_nullable | column_default 
-------------+-----------+-------------+----------------
 conflict_id | integer   | YES         | NULL
```

**Verify index created:**
```sql
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'qaco_onboarding_independence_threat' 
  AND indexname LIKE '%conflict_id%';
```

**Verify existing data intact:**
```sql
SELECT 
    COUNT(*) as total_threats,
    COUNT(onboarding_id) as threats_with_onboarding,
    COUNT(conflict_id) as threats_with_conflict
FROM qaco_onboarding_independence_threat;
```

### C. Application Validation

**1. Service Restart:**
```bash
sudo systemctl restart odoo
# OR
sudo service odoo restart
```

**2. Web Interface Loads:**
- [ ] Navigate to: `https://auditwise.thinkoptimise.com/web`
- [ ] Login page displays without error
- [ ] Successful login to dashboard
- [ ] No JavaScript console errors

**3. Onboarding Module Functions:**
- [ ] Open any existing Client Onboarding record
- [ ] Navigate to "Independence & Ethics" section
- [ ] Verify "Conflicts of Interest" tab loads
- [ ] Verify threat records display correctly
- [ ] Create new conflict record (should work)
- [ ] Create new threat record (should work)

**4. Error Log Validation:**
```bash
# Check logs for the specific error (should be GONE)
sudo grep -i "KeyError.*onboarding_id" /var/log/odoo/odoo.log
sudo grep -i "KeyError.*auditwise.thinkoptimise.com" /var/log/odoo/odoo.log

# Should return: No matches
```

**5. Cron Jobs Execute:**
```bash
# Monitor logs for at least 2-3 cron cycles (wait ~5 minutes)
sudo tail -f /var/log/odoo/odoo.log | grep -i "cron\|scheduled"
```

Expected output (example):
```
INFO auditwise.thinkoptimise.com odoo.addons.base.models.ir_cron: Starting job `Autovacuum Job`.
INFO auditwise.thinkoptimise.com odoo.addons.base.models.ir_cron: Job `Autovacuum Job` done.
```

No registry crashes or KeyError exceptions should appear.

### D. Model Metadata Validation

**Odoo Shell (optional deep dive):**
```bash
./odoo-bin shell -d auditwise.thinkoptimise.com
```

```python
>>> env = api.Environment(cr, uid, {})
>>> Threat = env['qaco.onboarding.independence.threat']
>>> print('onboarding_id' in Threat._fields)  # Should be True
>>> print('conflict_id' in Threat._fields)     # Should be True
>>> print(Threat._fields['conflict_id'].comodel_name)  # Should be 'qaco.onboarding.conflict'
>>> 
>>> Conflict = env['qaco.onboarding.conflict']
>>> print('threat_ids' in Conflict._fields)    # Should be True
>>> print(Conflict._fields['threat_ids'].inverse_name)  # Should be 'conflict_id'
```

---

## 5. ROLLBACK PROCEDURE (If Needed)

**If the upgrade fails or causes issues:**

### Step 1: Restore Database Backup
```bash
# Stop Odoo
sudo systemctl stop odoo

# Restore PostgreSQL backup
pg_restore -U odoo -d auditwise.thinkoptimise.com /path/to/backup.dump

# OR if using SQL backup:
psql -U odoo -d auditwise.thinkoptimise.com < /path/to/backup.sql
```

### Step 2: Revert Code Changes
```bash
cd /path/to/odoo/custom_addons/qaco_client_onboarding
git checkout HEAD -- models/onboarding_independence.py __manifest__.py
```

### Step 3: Restart Odoo
```bash
sudo systemctl start odoo
```

---

## 6. TECHNICAL DETAILS

### Data Model Relationships

**Before Fix (BROKEN):**
```
qaco.client.onboarding (1)
    ├── independence_threat_ids (M) ──> qaco.onboarding.independence.threat.onboarding_id
    └── conflict_ids (M) ──> qaco.onboarding.conflict.onboarding_id
                                 └── threat_ids (M) ──> qaco.onboarding.independence.threat.onboarding_id
                                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                                         CONFLICT! Same inverse used for 2 different parents
```

**After Fix (CORRECT):**
```
qaco.client.onboarding (1)
    ├── independence_threat_ids (M) ──> qaco.onboarding.independence.threat.onboarding_id ✓
    └── conflict_ids (M) ──> qaco.onboarding.conflict.onboarding_id
                                 └── threat_ids (M) ──> qaco.onboarding.independence.threat.conflict_id ✓
                                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                                         FIXED! Dedicated inverse field
```

### Field Attributes

| Model | Field | Type | Comodel | Inverse | Required | OnDelete | Index |
|-------|-------|------|---------|---------|----------|----------|-------|
| qaco.onboarding.independence.threat | onboarding_id | Many2one | qaco.client.onboarding | - | Yes | cascade | Yes |
| qaco.onboarding.independence.threat | conflict_id | Many2one | qaco.onboarding.conflict | - | No | cascade | Yes |
| qaco.onboarding.conflict | threat_ids | One2many | qaco.onboarding.independence.threat | conflict_id | - | - | - |

### Security Impact
- **No changes to access rules**: The `qaco.onboarding.conflict` model already has proper ACL entries in `ir.model.access.csv` (line 95)
- **No changes to groups**: Existing groups continue to work
- **No changes to views**: XML views don't explicitly reference the threat relationship within conflicts

### Performance Impact
- **Minimal**: One additional indexed foreign key column
- **Index created automatically**: Odoo ORM handles this during field setup
- **No additional queries**: Relationship queries work as before, just with correct inverse

---

## 7. RELATED WORK

### All One2many Fields Validated

The following One2many relationships with `inverse_name='onboarding_id'` were verified as CORRECT:

| Parent Model | Field | Child Model | Child Inverse Field | Status |
|--------------|-------|-------------|---------------------|--------|
| qaco.client.onboarding | regulator_checklist_line_ids | audit.onboarding.checklist | onboarding_id | ✓ Valid |
| qaco.client.onboarding | attached_template_ids | qaco.onboarding.attached.template | onboarding_id | ✓ Valid |
| qaco.client.onboarding | independence_threat_ids | qaco.onboarding.independence.threat | onboarding_id | ✓ Valid |
| qaco.client.onboarding | independence_declaration_ids | qaco.onboarding.independence.declaration | onboarding_id | ✓ Valid |
| qaco.client.onboarding | conflict_ids | qaco.onboarding.conflict | onboarding_id | ✓ Valid |
| qaco.client.onboarding | non_audit_service_ids | qaco.onboarding.non.audit | onboarding_id | ✓ Valid |
| qaco.client.onboarding | gift_ids | qaco.onboarding.gift | onboarding_id | ✓ Valid |
| qaco.onboarding.conflict | threat_ids | qaco.onboarding.independence.threat | ~~onboarding_id~~ conflict_id | **FIXED** |

All other relationships use correct inverse fields.

---

## 8. SUCCESS CRITERIA

The fix is considered successful when ALL of the following are true:

✅ **Registry builds**: `odoo-bin -u qaco_client_onboarding` completes without errors  
✅ **No KeyError**: Log files contain no "KeyError: 'onboarding_id'" or "KeyError: 'auditwise.thinkoptimise.com'"  
✅ **Web loads**: `https://auditwise.thinkoptimise.com/web` accessible without RPC_ERROR  
✅ **Cron runs**: Scheduled jobs execute without registry crashes  
✅ **Data intact**: All existing onboarding/conflict/threat records remain accessible  
✅ **Schema correct**: PostgreSQL shows `conflict_id` column exists with proper index  
✅ **Functional**: Users can create/edit conflicts and threats without errors  

---

## 9. MAINTENANCE NOTES

### For Future Developers

**When adding new One2many relationships:**
1. Always verify the comodel has a matching Many2one field with the EXACT name specified in `inverse_name`
2. Never reuse an existing foreign key field for a new relationship if that field already points to a different parent
3. Use descriptive inverse field names (e.g., `conflict_id`, `onboarding_id`, `parent_id`) to avoid confusion
4. Test module upgrade in a staging environment before production deployment

**Common Odoo ORM Mistakes:**
- Using `onboarding_id` as inverse when the child model has `onboarding_id` pointing to a DIFFERENT parent
- Forgetting to add the inverse Many2one field to the child model
- Typos in inverse_name (Odoo won't catch this until registry load)

---

## 10. SIGN-OFF

**Fix Implemented By:** Senior Odoo 17 Core Engineer  
**Review Status:** ⏳ Pending Production Validation  
**Deployment Date:** [TO BE FILLED AFTER UPGRADE]  

**Validation Checklist Completed:**
- [ ] Development environment tested
- [ ] Staging environment tested
- [ ] Production backup verified
- [ ] Production upgrade completed
- [ ] All validation checks passed
- [ ] Users notified of system restoration

**Final Sign-off:**
- [ ] Technical Lead: ___________________ Date: ___________
- [ ] System Administrator: ___________________ Date: ___________

---

**END OF REPORT**
