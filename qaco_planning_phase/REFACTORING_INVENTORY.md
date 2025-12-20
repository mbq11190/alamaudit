# PLANNING PHASE REFACTORING - CODE INVENTORY
**Date:** December 20, 2025  
**Purpose:** Complete audit of P-1 to P-13 planning tabs for refactoring

---

## 📊 CURRENT STATE ANALYSIS

### CRITICAL ISSUES IDENTIFIED

1. **DUPLICATE P-11 MODELS** (KeyError risk)
   - `planning_p11_group_audit.py` → `qaco.planning.p11.group.audit` ❌
   - `planning_p11_group_audit_complete.py` → `audit.planning.p11.group_audit` ✅
   - **Conflict:** Two models exist for same purpose, different naming convention

2. **DUPLICATE P-12 MODELS** (KeyError risk)
   - `planning_p12_strategy.py` → `qaco.planning.p12.strategy` ❌
   - `planning_p12_audit_strategy_complete.py` → `audit.planning.p12.audit_strategy` ✅
   - **Conflict:** Two models exist, one more comprehensive

3. **INCONSISTENT NAMING CONVENTION**
   - P-1 to P-10, P-13: Use `qaco.planning.pX.*` namespace ✅
   - P-11, P-12 "complete": Use `audit.planning.pX.*` namespace ❌
   - **Problem:** Breaks relational integrity with planning_base.py

4. **BROKEN INVERSE RELATIONSHIPS**
   - `planning_base.py` expects models NOT currently imported
   - `__init__.py` only imports non-"complete" versions
   - Planning main orchestrator references broken models

---

## 📁 FILE-BY-FILE INVENTORY

### MODELS DIRECTORY

#### ✅ CANONICAL MODELS (Keep & Fix)

| P-Tab | File | Model Name | Status | Child Models |
|-------|------|------------|--------|--------------|
| P-1 | `planning_p1_engagement.py` | `qaco.planning.p1.engagement` | ✅ Keep | PlanningP1TeamMember, PlanningP1TimeBudget |
| P-2 | `planning_p2_entity.py` | `qaco.planning.p2.entity` | ✅ Keep | PlanningP2BusinessRisk, PlanningP2Change |
| P-3 | `planning_p3_controls.py` | `qaco.planning.p3.controls` | ✅ Keep | 5 child models |
| P-4 | `planning_p4_analytics.py` | `qaco.planning.p4.analytics` | ✅ Keep | 6 child models |
| P-5 | `planning_p5_materiality.py` | `qaco.planning.p5.materiality` | ✅ Keep | 4 child models |
| P-6 | `planning_p6_risk.py` | `qaco.planning.p6.risk` | ✅ Keep | PlanningP6RiskLine (2 versions - need merge) |
| P-7 | `planning_p7_fraud.py` | `qaco.planning.p7.fraud` | ✅ Keep | PlanningP7FraudLine (2 versions - need merge) |
| P-8 | `planning_p8_going_concern.py` | `qaco.planning.p8.going.concern` | ✅ Keep | 2 child models |
| P-9 | `planning_p9_laws.py` | `qaco.planning.p9.laws` | ✅ Keep | PlanningP9LawLine (2 versions - need merge) |
| P-10 | `planning_p10_related_parties.py` | `qaco.planning.p10.related.parties` | ✅ Keep | Need to verify |
| **P-11** | ❌ `planning_p11_group_audit.py` | `qaco.planning.p11.group.audit` | 🔄 **DELETE** | Incomplete |
| **P-11** | ✅ `planning_p11_group_audit_complete.py` | `audit.planning.p11.group_audit` | 🔄 **RENAME TO qaco.*** | 4 models, ISA 600 compliant |
| **P-12** | ❌ `planning_p12_strategy.py` | `qaco.planning.p12.strategy` | 🔄 **DELETE** | Incomplete |
| **P-12** | ✅ `planning_p12_audit_strategy_complete.py` | `audit.planning.p12.audit_strategy` | 🔄 **RENAME TO qaco.*** | 5 models, ISA 300/330 compliant |
| P-13 | `planning_p13_approval.py` | `qaco.planning.p13.approval` | ✅ Keep | 2 child models |

#### 🔧 SUPPORTING FILES

| File | Models | Status |
|------|--------|--------|
| `planning_base.py` | `qaco.planning.tab.mixin`, `qaco.planning.main` | ✅ Keep - NEEDS RELATIONSHIP FIX |
| `planning_phase.py` | `qaco.planning.phase` | ❓ Legacy? Verify usage |
| `supporting_models.py` | `qaco.planning.checklist` | ✅ Keep |
| `__init__.py` | Import registry | 🔧 **CRITICAL FIX NEEDED** |

---

## 🔴 CRITICAL RELATIONSHIP ISSUES

### Issue 1: `planning_base.py` Expects Wrong Models

**Current Code (BROKEN):**
```python
# Line 233 in planning_base.py
p11_group_audit_id = fields.Many2one(
    'qaco.planning.p11.group.audit',  # ❌ Model doesn't exist in __init__.py
    string='P-11: Audit Strategy & Audit Plan',
)
```

**Actual Imported Model:**
```python
# In __init__.py
from . import planning_p11_group_audit  
# Creates: qaco.planning.p11.group.audit ✅

# NOT imported:
from . import planning_p11_group_audit_complete  
# Would create: audit.planning.p11.group_audit ❌ (wrong namespace)
```

### Issue 2: Inverse Fields Missing

**Example from P-11 Complete:**
```python
# planning_p11_group_audit_complete.py creates:
# - audit.planning.p11.group_audit (parent)
# - audit.planning.p11.component (child)
# - audit.planning.p11.component_risk
# - audit.planning.p11.component_auditor

# These are NEVER imported in __init__.py
# So planning_base.py can't reference them
```

### Issue 3: Duplicate Class Names

**P-6, P-7, P-9 have TWO classes with same purpose:**
```python
# In planning_p6_risk.py
class AuditPlanningP6RiskAssessment(models.Model):  # Legacy?
    _name = 'audit.planning.p6.risk'

class PlanningP6RiskLine(models.Model):  # Current?
    _name = 'qaco.planning.p6.risk.line'
```

---

## 🎯 CANONICAL MODEL MAP (ENFORCED)

| Tab | Canonical Model Name | Class Name | File |
|-----|----------------------|------------|------|
| P-1 | `qaco.planning.p1.engagement` | `PlanningP1Engagement` | planning_p1_engagement.py |
| P-2 | `qaco.planning.p2.entity` | `PlanningP2Entity` | planning_p2_entity.py |
| P-3 | `qaco.planning.p3.controls` | `PlanningP3Controls` | planning_p3_controls.py |
| P-4 | `qaco.planning.p4.analytics` | `PlanningP4Analytics` | planning_p4_analytics.py |
| P-5 | `qaco.planning.p5.materiality` | `PlanningP5Materiality` | planning_p5_materiality.py |
| P-6 | `qaco.planning.p6.risk` | `PlanningP6Risk` | planning_p6_risk.py |
| P-7 | `qaco.planning.p7.fraud` | `PlanningP7Fraud` | planning_p7_fraud.py |
| P-8 | `qaco.planning.p8.going.concern` | `PlanningP8GoingConcern` | planning_p8_going_concern.py |
| P-9 | `qaco.planning.p9.laws` | `PlanningP9Laws` | planning_p9_laws.py |
| P-10 | `qaco.planning.p10.related.parties` | `PlanningP10RelatedParties` | planning_p10_related_parties.py |
| **P-11** | `qaco.planning.p11.group.audit` | `PlanningP11GroupAudit` | 🔄 **Merge from complete** |
| **P-12** | `qaco.planning.p12.strategy` | `PlanningP12Strategy` | 🔄 **Merge from complete** |
| P-13 | `qaco.planning.p13.approval` | `PlanningP13Approval` | planning_p13_approval.py |

---

## 🚨 MODELS TO DELETE / MERGE

### DELETE IMMEDIATELY (Duplicates)
❌ `planning_p11_group_audit.py` → Incomplete, replaced by complete version  
❌ `planning_p12_strategy.py` → Incomplete, replaced by complete version

### RENAME & MERGE
🔄 `planning_p11_group_audit_complete.py`:
- Change all `audit.planning.p11.*` → `qaco.planning.p11.*`
- Rename file to `planning_p11_group_audit.py`
- Merge any unique fields from old file

🔄 `planning_p12_audit_strategy_complete.py`:
- Change all `audit.planning.p12.*` → `qaco.planning.p12.*`
- Rename file to `planning_p12_strategy.py`
- Merge any unique fields from old file

### CONSOLIDATE DUPLICATE CLASSES
Within existing files, merge duplicate classes:

**P-6:** Merge `AuditPlanningP6RiskAssessment` → `PlanningP6Risk`  
**P-7:** Merge `AuditPlanningP7Fraud` → `PlanningP7Fraud`  
**P-8:** Merge `AuditPlanningP8GoingConcern` → `PlanningP8GoingConcern`  
**P-9:** Merge `AuditPlanningP9LawsRegulations` → `PlanningP9Laws`

---

## 📋 VIEWS INVENTORY

### DUPLICATE VIEWS IDENTIFIED

| P-Tab | Files Found | Action Required |
|-------|-------------|-----------------|
| P-11 | `planning_p11_views.xml`, `planning_p11_views_complete.xml` | ✅ Use complete, delete old |
| P-10 | `planning_p10_views.xml`, `planning_p10_related_parties_views.xml` | ❓ Verify which is canonical |
| All | Multiple form views per tab in some cases | 🔧 Consolidate to ONE form + ONE tree |

### REQUIRED VIEW STRUCTURE (Standard)
```xml
<!-- ONE form view per P-tab -->
<record id="view_planning_pX_form" model="ir.ui.view">
  <field name="model">qaco.planning.pX.*</field>
  <field name="arch" type="xml">
    <form>
      <header><!-- State workflow buttons --></header>
      <sheet>
        <notebook>
          <page string="Overview"/>
          <page string="Details"/>
          <page string="Attachments"/>
          <page string="Review & Sign-off"/>
        </notebook>
      </sheet>
      <div class="oe_chatter"><!-- Mail thread --></div>
    </form>
  </field>
</record>

<!-- ONE tree view per P-tab -->
<record id="view_planning_pX_tree" model="ir.ui.view">
  ...
</record>
```

---

## 🔗 RELATIONSHIP DEPENDENCY GRAPH

### Forward Dependencies (P-tab → Child Tables)

```
P-1 Engagement
├── PlanningP1TeamMember (One2many)
└── PlanningP1TimeBudget (One2many)

P-2 Entity
├── PlanningP2BusinessRisk (One2many)
└── PlanningP2Change (One2many)

P-3 Controls
├── PlanningP3TransactionCycle
├── PlanningP3KeyControl
├── PlanningP3ITGC
├── PlanningP3ControlDeficiency
└── PlanningP3ControlChange

P-11 Group Audit (COMPLETE VERSION)
├── AuditPlanningP11Component ← NEED TO RENAME
├── AuditPlanningP11ComponentRisk ← NEED TO RENAME
└── AuditPlanningP11ComponentAuditor ← NEED TO RENAME

P-12 Strategy (COMPLETE VERSION)
├── AuditPlanningP12RiskResponse ← NEED TO RENAME
├── AuditPlanningP12FSAreaStrategy ← NEED TO RENAME
├── AuditPlanningP12AuditProgram ← NEED TO RENAME
├── AuditPlanningP12SamplingPlan ← NEED TO RENAME
└── AuditPlanningP12KAMCandidate ← NEED TO RENAME

P-13 Approval
├── PlanningChecklistLine (One2many)
└── PlanningChangeLog (One2many)
```

### Backward Dependencies (Child → Parent)

**CRITICAL:** Every child table MUST have inverse field to parent:
```python
# Child model
p1_engagement_id = fields.Many2one('qaco.planning.p1.engagement', inverse_name='team_member_ids')

# Parent model MUST have
team_member_ids = fields.One2many('qaco.planning.p1.team.member', 'p1_engagement_id')
```

**Missing Inverses Cause KeyError at Registry Load!**

---

## 🛠️ REFACTORING ACTION PLAN

### Phase 1: Model Consolidation (PRIORITY 1)

1. ✅ **Backup Current Code** (git commit before changes)

2. 🔧 **Fix P-11:**
   - [ ] Copy `planning_p11_group_audit_complete.py` → rename to temp
   - [ ] Replace all `audit.planning.p11` → `qaco.planning.p11`
   - [ ] Replace all class names `AuditPlanningP11*` → `PlanningP11*`
   - [ ] Delete old `planning_p11_group_audit.py`
   - [ ] Move temp file to `planning_p11_group_audit.py`
   - [ ] Update `__init__.py` import

3. 🔧 **Fix P-12:**
   - [ ] Copy `planning_p12_audit_strategy_complete.py` → rename to temp
   - [ ] Replace all `audit.planning.p12` → `qaco.planning.p12`
   - [ ] Replace all class names `AuditPlanningP12*` → `PlanningP12*`
   - [ ] Delete old `planning_p12_strategy.py`
   - [ ] Move temp file to `planning_p12_strategy.py`
   - [ ] Update `__init__.py` import

4. 🔧 **Merge Duplicate Classes in P-6, P-7, P-8, P-9:**
   - [ ] Identify canonical class per file
   - [ ] Move fields/methods from legacy class to canonical
   - [ ] Update all inverse references
   - [ ] Delete legacy class
   - [ ] Test registry load

### Phase 2: Relationship Integrity (PRIORITY 1)

1. **Verify All One2many Have Inverse:**
   ```python
   # Scan every One2many field
   # Verify inverse exists in child model
   # Add missing inverse fields
   ```

2. **Update planning_base.py References:**
   - [ ] Ensure all p*_id fields reference correct model names
   - [ ] Verify all referenced models exist in __init__.py

3. **Audit Child Table Inverses:**
   - [ ] P-1 team_member_ids, time_budget_ids
   - [ ] P-2 business_risk_ids, change_ids
   - [ ] P-3 all 5 child table inverses
   - [ ] P-11 component_ids, component_risk_ids, component_auditor_ids
   - [ ] P-12 risk_response_ids, fs_area_strategy_ids, audit_program_ids, sampling_plan_ids, kam_candidate_ids
   - [ ] P-13 checklist_ids, change_log_ids

### Phase 3: View Consolidation (PRIORITY 2)

1. **Delete Duplicate Views:**
   - [ ] Keep `planning_p11_views_complete.xml`, delete `planning_p11_views.xml`
   - [ ] Verify no duplicate XML IDs across all view files

2. **Standardize View Structure:**
   - [ ] ONE form per P-tab
   - [ ] ONE tree per P-tab
   - [ ] Consistent notebook layout (Overview, Details, Attachments, Review)

3. **Update XML Model References:**
   - [ ] Change P-11 views: `audit.planning.p11.*` → `qaco.planning.p11.*`
   - [ ] Change P-12 views: `audit.planning.p12.*` → `qaco.planning.p12.*`

### Phase 4: Workflow Standardization (PRIORITY 2)

1. **Ensure All P-tabs Inherit from `qaco.planning.tab.mixin`:**
   ```python
   _inherit = ['mail.thread', 'mail.activity.mixin', 'qaco.planning.tab.mixin']
   ```

2. **Remove Duplicate Workflow Methods:**
   - [ ] If mixin provides it, don't override unless custom logic needed

3. **Standardize State Field:**
   ```python
   state = fields.Selection(
       [('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved')],
       default='not_started'
   )
   ```

### Phase 5: Security & Data Files (PRIORITY 3)

1. **Consolidate Access Rules:**
   - [ ] One CSV per module section
   - [ ] Remove duplicate rules for same model

2. **Update XML IDs in Data Files:**
   - [ ] Reflect new model names in seed data

### Phase 6: Legacy Cleanup (PRIORITY 3)

1. **Delete Dead Code:**
   - [ ] Remove commented blocks
   - [ ] Remove unused imports
   - [ ] Remove 1.0-7.0 legacy references

2. **Remove Unused Views:**
   - [ ] Grep for XML IDs referenced nowhere
   - [ ] Delete orphan view records

### Phase 7: Registry Validation (PRIORITY 1 - FINAL)

1. **Test Server Startup:**
   ```bash
   ./odoo-bin -u qaco_planning_phase -d test_db --stop-after-init --test-enable
   ```

2. **Verify No Errors:**
   - [ ] No KeyError for missing models
   - [ ] No missing inverse warnings
   - [ ] No duplicate XML ID warnings
   - [ ] No circular dependency errors

3. **Smoke Test Each P-tab:**
   - [ ] Create new planning phase
   - [ ] Open each P-tab form view
   - [ ] Verify child tables load
   - [ ] Verify workflow buttons work

---

## ✅ SUCCESS CRITERIA

- [ ] ZERO duplicate model names
- [ ] ZERO missing inverse fields
- [ ] ZERO registry errors on startup
- [ ] ONE canonical model per P-tab
- [ ] ONE form + ONE tree view per P-tab
- [ ] ALL P-tabs use consistent naming: `qaco.planning.pX.*`
- [ ] ALL relationships bidirectional
- [ ] Planning phase orchestrator fully functional
- [ ] Stable server startup with all modules loaded

---

## 📞 NEXT STEPS

1. **IMMEDIATE:** Fix P-11 and P-12 model namespace issues
2. **IMMEDIATE:** Fix planning_base.py relationship references
3. **IMMEDIATE:** Update __init__.py imports
4. **HIGH:** Audit and fix all One2many inverse fields
5. **MEDIUM:** Consolidate duplicate views
6. **MEDIUM:** Standardize workflows
7. **LOW:** Clean up legacy code

---

**Status:** Inventory Complete - Ready for Systematic Refactoring  
**Estimated Effort:** 8-12 hours for full refactoring  
**Risk Level:** HIGH (Registry crashes if not done correctly)  
**Recommended Approach:** Sequential P-tab refactoring with registry validation after each

