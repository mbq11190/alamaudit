# P-11 & P-12 REFACTORING EXECUTION PLAN
**Date:** December 20, 2025  
**Critical Fix:** Resolve model namespace conflicts causing registry KeyError

---

## 🎯 PROBLEM SUMMARY

### Issue 1: P-11 Namespace Conflict
- **File 1 (Incomplete):** `planning_p11_group_audit.py`
  - Model: `qaco.planning.p11.group.audit` ✅ Correct namespace
  - Status: Incomplete ISA 600 implementation
  - Currently imported in `__init__.py`

- **File 2 (Complete):** `planning_p11_group_audit_complete.py`
  - Model: `audit.planning.p11.group_audit` ❌ Wrong namespace
  - Status: Full ISA 600 implementation (1,125 lines, 4 models)
  - NOT imported in `__init__.py`

- **Registry Reference:** `planning_base.py` line 233
  ```python
  p11_group_audit_id = fields.Many2one(
      'qaco.planning.p11.group.audit',  # Expects this
  )
  ```

### Issue 2: P-12 Namespace Conflict
- **File 1 (Incomplete):** `planning_p12_strategy.py`
  - Model: `qaco.planning.p12.strategy` ✅ Correct namespace
  - Status: Incomplete ISA 300 implementation
  - Currently imported in `__init__.py`

- **File 2 (Complete):** `planning_p12_audit_strategy_complete.py`
  - Model: `audit.planning.p12.audit_strategy` ❌ Wrong namespace
  - Status: Full ISA 300/330 implementation (1,800+ lines, 5 models)
  - NOT imported in `__init__.py`

- **Registry Reference:** `planning_base.py` line 240
  ```python
  p12_strategy_id = fields.Many2one(
      'qaco.planning.p12.strategy',  # Expects this
  )
  ```

---

## 🔧 EXECUTION STEPS

### PHASE 1: Backup Current State
```bash
git add .
git commit -m "BACKUP: Before P-11/P-12 namespace refactoring"
```

### PHASE 2: Fix P-11 (4 models)

#### Step 1: Namespace Replacement in Complete File
Replace in `planning_p11_group_audit_complete.py`:
1. `audit.planning.p11.group_audit` → `qaco.planning.p11.group.audit`
2. `audit.planning.p11.component` → `qaco.planning.p11.component`
3. `audit.planning.p11.component_risk` → `qaco.planning.p11.component.risk`
4. `audit.planning.p11.component_auditor` → `qaco.planning.p11.component.auditor`

#### Step 2: Class Name Standardization
Replace class names:
1. `AuditPlanningP11GroupAudit` → `PlanningP11GroupAudit`
2. `AuditPlanningP11Component` → `PlanningP11Component`
3. `AuditPlanningP11ComponentRisk` → `PlanningP11ComponentRisk`
4. `AuditPlanningP11ComponentAuditor` → `PlanningP11ComponentAuditor`

#### Step 3: File Replacement
1. Delete `planning_p11_group_audit.py` (old incomplete version)
2. Rename `planning_p11_group_audit_complete.py` → `planning_p11_group_audit.py`

#### Step 4: Update Imports
No change needed in `__init__.py` - already imports `planning_p11_group_audit`

### PHASE 3: Fix P-12 (5 models)

#### Step 1: Namespace Replacement in Complete File
Replace in `planning_p12_audit_strategy_complete.py`:
1. `audit.planning.p12.audit_strategy` → `qaco.planning.p12.strategy`
2. `audit.planning.p12.risk_response` → `qaco.planning.p12.risk.response`
3. `audit.planning.p12.fs_area_strategy` → `qaco.planning.p12.fs.area.strategy`
4. `audit.planning.p12.audit_program` → `qaco.planning.p12.audit.program`
5. `audit.planning.p12.sampling_plan` → `qaco.planning.p12.sampling.plan`
6. `audit.planning.p12.kam_candidate` → `qaco.planning.p12.kam.candidate`

#### Step 2: Class Name Standardization
Replace class names:
1. `AuditPlanningP12AuditStrategy` → `PlanningP12Strategy`
2. `AuditPlanningP12RiskResponse` → `PlanningP12RiskResponse`
3. `AuditPlanningP12FSAreaStrategy` → `PlanningP12FSAreaStrategy`
4. `AuditPlanningP12AuditProgram` → `PlanningP12AuditProgram`
5. `AuditPlanningP12SamplingPlan` → `PlanningP12SamplingPlan`
6. `AuditPlanningP12KAMCandidate` → `PlanningP12KAMCandidate`

#### Step 3: File Replacement
1. Delete `planning_p12_strategy.py` (old incomplete version)
2. Rename `planning_p12_audit_strategy_complete.py` → `planning_p12_strategy.py`

#### Step 4: Update Imports
No change needed in `__init__.py` - already imports `planning_p12_strategy`

### PHASE 4: Update Views

#### P-11 Views
Replace in `planning_p11_views_complete.xml`:
- All `audit.planning.p11.*` → `qaco.planning.p11.*`
- Update XML IDs to remove "_complete" suffix if present

#### P-12 Views (if they exist)
Replace in any P-12 view files:
- All `audit.planning.p12.*` → `qaco.planning.p12.*`

### PHASE 5: Validation

#### Test Registry Load
```bash
cd alamaudit
odoo-bin -u qaco_planning_phase -d test_db --stop-after-init
```

Expected output: No errors about missing models or inverse fields

#### Verify Models Registered
```bash
# In Odoo shell
env['qaco.planning.p11.group.audit'].search([])  # Should not error
env['qaco.planning.p12.strategy'].search([])  # Should not error
```

---

## 📝 DETAILED SEARCH-REPLACE OPERATIONS

### P-11 File: planning_p11_group_audit_complete.py

| Find | Replace | Count |
|------|---------|-------|
| `_name = 'audit.planning.p11.group_audit'` | `_name = 'qaco.planning.p11.group.audit'` | 1 |
| `_name = 'audit.planning.p11.component'` | `_name = 'qaco.planning.p11.component'` | 1 |
| `_name = 'audit.planning.p11.component_risk'` | `_name = 'qaco.planning.p11.component.risk'` | 1 |
| `_name = 'audit.planning.p11.component_auditor'` | `_name = 'qaco.planning.p11.component.auditor'` | 1 |
| `'audit.planning.p11.group_audit'` | `'qaco.planning.p11.group.audit'` | ~10-15 |
| `'audit.planning.p11.component'` | `'qaco.planning.p11.component'` | ~5-10 |
| `'audit.planning.p11.component_risk'` | `'qaco.planning.p11.component.risk'` | ~3-5 |
| `'audit.planning.p11.component_auditor'` | `'qaco.planning.p11.component.auditor'` | ~3-5 |
| `class AuditPlanningP11GroupAudit` | `class PlanningP11GroupAudit` | 1 |
| `class AuditPlanningP11Component` | `class PlanningP11Component` | 1 |
| `class AuditPlanningP11ComponentRisk` | `class PlanningP11ComponentRisk` | 1 |
| `class AuditPlanningP11ComponentAuditor` | `class PlanningP11ComponentAuditor` | 1 |

### P-12 File: planning_p12_audit_strategy_complete.py

| Find | Replace | Count |
|------|---------|-------|
| `_name = 'audit.planning.p12.audit_strategy'` | `_name = 'qaco.planning.p12.strategy'` | 1 |
| `_name = 'audit.planning.p12.risk_response'` | `_name = 'qaco.planning.p12.risk.response'` | 1 |
| `_name = 'audit.planning.p12.fs_area_strategy'` | `_name = 'qaco.planning.p12.fs.area.strategy'` | 1 |
| `_name = 'audit.planning.p12.audit_program'` | `_name = 'qaco.planning.p12.audit.program'` | 1 |
| `_name = 'audit.planning.p12.sampling_plan'` | `_name = 'qaco.planning.p12.sampling.plan'` | 1 |
| `_name = 'audit.planning.p12.kam_candidate'` | `_name = 'qaco.planning.p12.kam.candidate'` | 1 |
| `'audit.planning.p12.audit_strategy'` | `'qaco.planning.p12.strategy'` | ~20-30 |
| `'audit.planning.p12.risk_response'` | `'qaco.planning.p12.risk.response'` | ~5-10 |
| `'audit.planning.p12.fs_area_strategy'` | `'qaco.planning.p12.fs.area.strategy'` | ~5-10 |
| `'audit.planning.p12.audit_program'` | `'qaco.planning.p12.audit.program'` | ~3-5 |
| `'audit.planning.p12.sampling_plan'` | `'qaco.planning.p12.sampling.plan'` | ~3-5 |
| `'audit.planning.p12.kam_candidate'` | `'qaco.planning.p12.kam.candidate'` | ~3-5 |
| `class AuditPlanningP12AuditStrategy` | `class PlanningP12Strategy` | 1 |
| `class AuditPlanningP12RiskResponse` | `class PlanningP12RiskResponse` | 1 |
| `class AuditPlanningP12FSAreaStrategy` | `class PlanningP12FSAreaStrategy` | 1 |
| `class AuditPlanningP12AuditProgram` | `class PlanningP12AuditProgram` | 1 |
| `class AuditPlanningP12SamplingPlan` | `class PlanningP12SamplingPlan` | 1 |
| `class AuditPlanningP12KAMCandidate` | `class PlanningP12KAMCandidate` | 1 |

---

## ⚠️ CRITICAL CONSIDERATIONS

### 1. Foreign Key References
After renaming, any existing data records will have broken foreign keys. This is a **BREAKING CHANGE** for existing databases.

**Migration Required:**
- Need to create a migration script to update existing `ir_model_data` records
- Update any existing audit records' foreign key values

### 2. View Dependencies
- All XML views referencing old model names will break
- Must update views before or simultaneously with model changes

### 3. Security Rules
- Access control rules (CSV) must reference correct model names
- Check `security/ir.model.access.csv` for P-11/P-12 entries

### 4. Report Templates
- Any QWeb reports referencing these models need updates

---

## ✅ POST-REFACTORING CHECKLIST

- [ ] P-11 models use `qaco.planning.p11.*` namespace
- [ ] P-12 models use `qaco.planning.p12.*` namespace
- [ ] Old incomplete files deleted
- [ ] __init__.py imports correct (no changes needed)
- [ ] planning_base.py references match (already correct)
- [ ] Views updated to new namespaces
- [ ] Server starts without registry errors
- [ ] Can create new planning phase record
- [ ] Can open P-11 form view
- [ ] Can open P-12 form view
- [ ] Child tables load correctly
- [ ] Workflow buttons functional

---

**Status:** Ready to Execute  
**Risk Level:** HIGH - Breaking change for existing data  
**Recommendation:** Execute on clean test database first  
**Estimated Time:** 45-60 minutes for complete refactoring + testing

