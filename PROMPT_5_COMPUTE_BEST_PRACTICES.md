# 🔴 PROMPT 5: Odoo 17 Best Practice Compute Pattern (MANDATORY)

## Objective
Standardize all computed fields in `qaco_planning_phase` to follow Odoo 17 best practices and prevent future registry/cron crashes.

## ✅ Canonical Pattern (Mandatory for All Compute Methods)

### GOLD STANDARD (Already Applied to P-2 Entity):

```python
@api.depends('audit_id')  # ✅ ONLY real fields, NO '.id' anywhere
def _compute_can_open(self):
    """Defensive: Safe even during module install/upgrade."""
    for rec in self:
        try:
            # ✅ ALWAYS null-guard first
            if not rec.audit_id:
                rec.can_open = False
                continue
            
            # ✅ Check model exists (for module dependencies)
            if 'qaco.planning.p1.engagement' not in self.env:
                rec.can_open = False
                continue
            
            # ✅ Safe search with limit (performance)
            p1 = self.env['qaco.planning.p1.engagement'].search([
                ('audit_id', '=', rec.audit_id.id)  # ✅ Using .id INSIDE method is VALID
            ], limit=1)
            
            # ✅ Assign value inside loop
            rec.can_open = (p1 and p1.state == 'approved') if p1 else False
            
        except Exception as e:
            # ✅ Never crash - log and set safe default
            _logger.warning(f'P-2 _compute_can_open failed for record {rec.id}: {e}')
            rec.can_open = False
```

## ❌ Anti-Patterns (Violations Found in Codebase)

### 1. **`.id` in @api.depends** (FIXED in PROMPT 1)
```python
# ❌ FORBIDDEN - Causes registry crash
@api.depends('audit_id', 'audit_id.id')  
def _compute_xxx(self):
    ...

# ✅ CORRECT
@api.depends('audit_id')  # Just the field, not .id
def _compute_xxx(self):
    for rec in self:
        if not rec.audit_id:
            rec.xxx = False
            continue
        # Using .id here is FINE
        search_result = self.env['...'].search([('audit_id', '=', rec.audit_id.id)])
```

### 2. **No Null Guards**
```python
# ❌ WILL CRASH if business_risk_ids is None/uninitialized
@api.depends('business_risk_ids')
def _compute_risk_counts(self):
    for rec in self:
        rec.total_risks = len(rec.business_risk_ids)  # AttributeError if None

# ✅ CORRECT
@api.depends('business_risk_ids')
def _compute_risk_counts(self):
    for rec in self:
        try:
            if not rec.business_risk_ids:
                rec.total_risks = 0
                continue
            rec.total_risks = len(rec.business_risk_ids)
        except Exception as e:
            _logger.warning(f'Risk count compute failed: {e}')
            rec.total_risks = 0
```

### 3. **Missing `for rec in self:`**
```python
# ❌ WRONG - Compute must loop over recordset
@api.depends('state')
def _compute_is_locked(self):
    self.is_locked = self.state == 'approved'  # Only works for single record!

# ✅ CORRECT
@api.depends('state')
def _compute_is_locked(self):
    for rec in self:
        try:
            rec.is_locked = rec.state in ('approved', 'locked') if rec.state else False
        except Exception as e:
            _logger.warning(f'Compute failed: {e}')
            rec.is_locked = False
```

### 4. **Side Effects in Compute**
```python
# ❌ FORBIDDEN - Compute should ONLY compute, never modify other records
@api.depends('approval_status')
def _compute_next_tab_ready(self):
    for rec in self:
        rec.next_tab_ready = rec.approval_status == 'approved'
        # ❌ NEVER do this in compute:
        rec.write({'some_other_field': 'value'})  
        self.env['other.model'].create({...})
        rec.send_email()

# ✅ CORRECT - Side effects belong in buttons/crons, not compute
@api.depends('approval_status')
def _compute_next_tab_ready(self):
    for rec in self:
        rec.next_tab_ready = rec.approval_status == 'approved'

def action_approve(self):  # ✅ Side effects here
    self.state = 'approved'
    self._send_notifications()  # OK in action method
```

## 📊 Compute Methods Audit (82 Total)

### ✅ Already Compliant (P-2 Entity - PROMPT 2):
- `_compute_is_locked()` - Line 189
- `_compute_can_open()` - Line 207
- `_compute_risk_counts()` - Line 652
- `_compute_doc_status()` - Line 722
- `_compute_name()` - Line 824

### 🟡 Needs Review (Remaining 77 Methods):

**P-1 Engagement (7 methods):**
- `_compute_total_hours()` - Line 140
- `_compute_is_locked()` - Line 194
- `_compute_team_summary()` - Line 407
- `_compute_budget_totals()` - Line 499
- `_compute_name()` - Line 698

**P-3 Controls (7 methods):**
- `_compute_can_open()` - Line 480
- `_compute_name()` - Line 1084
- `_compute_cycle_summary()` - Line 1092
- `_compute_control_summary()` - Line 1100
- `_compute_deficiency_summary()` - Line 1108
- `_compute_reliance_decision()` - Line 1123
- `_compute_attachment_counts()` - Line 1128
- `_compute_proceed_to_p4()` - Line 1134

**P-4 Analytics (7 methods):**
- `_compute_variance()` - Line 108
- `_compute_movement()` - Line 161
- `_compute_budget_variance()` - Line 207
- `_compute_change()` - Line 295
- `_compute_can_open()` - Line 436
- `_compute_name()` - Line 1022
- `_compute_risk_linkage()` - Line 1030

**P-5 Materiality (5 methods):**
- `_compute_as_pct()` - Line 83
- `_compute_can_open()` - Line 306
- `_compute_name()` - Line 922
- `_compute_materiality()` - Line 933
- `_compute_om_change()` - Line 951
- `_compute_outside_threshold()` - Line 959

**P-6 Risk (6 methods):**
- `_compute_can_open()` - Line 40
- `_compute_locked()` - Line 160
- `_compute_risk_dashboard_metrics()` - Line 166
- `_compute_risk_rating()` - Line 634
- `_compute_senior_involvement()` - Line 652
- `_compute_extended_procedures()` - Line 660

**P-7 Fraud (3 methods):**
- `_compute_can_open()` - Line 35
- `_compute_name()` - Line 644
- `_compute_fraud_risks_identified()` - Line 652

**P-8 Going Concern (4 methods):**
- `_compute_can_open()` - Line 47
- `_compute_name()` - Line 751
- `_compute_disclosure_risk()` - Line 760
- `_compute_unsupported_plans()` - Line 770

**P-9 Laws (6 methods):**
- `_compute_can_open()` - Line 47
- `_compute_name()` - Line 666
- `_compute_noncompliance_flags()` - Line 778
- `_compute_compliance_risk_escalation()` - Line 793
- `_compute_fraud_linkage()` - Line 799
- `_compute_gc_linkage()` - Line 809

**P-10 Related Parties (5 methods):**
- `_compute_can_open()` - Line 35
- `_compute_name()` - Line 597
- `_compute_completeness_count()` - Line 719
- `_compute_significant_rpt_flags()` - Line 731
- `_compute_fraud_gc_linkages()` - Line 742

**P-11 Group Audit (8 methods):**
- `_compute_can_open()` - Line 96
- `_compute_engagement_id()` - Line 553
- `_compute_component_metrics()` - Line 560
- `_compute_component_auditor_involvement()` - Line 568
- `_compute_auditor_confirmations()` - Line 574
- `_compute_preparer_role()` - Line 594
- `_compute_locked()` - Line 608
- `_compute_financial_significance()` - Line 1034
- `_compute_escalation_flag()` - Line 1200

**P-12 Strategy (9 methods):**
- `_compute_can_open()` - Line 97
- `_compute_engagement_id()` - Line 605
- `_compute_risk_metrics()` - Line 612
- `_compute_fs_area_coverage()` - Line 624
- `_compute_kam_metrics()` - Line 637
- `_compute_total_hours()` - Line 649
- `_compute_preparer_role()` - Line 659
- `_compute_locked()` - Line 672
- `_compute_group_audit_applicable()` - Line 676

**P-13 Approval (3 methods):**
- `_compute_can_open()` - Line 47
- `_compute_name()` - Line 427
- `_compute_all_tabs_complete()` - Line 440

**planning_phase.py (Legacy - 6 methods):**
- `_compute_name()` - Line 283
- `_compute_audit_tenure()` - Line 291
- `_compute_reliance_strategy()` - Line 300
- `_compute_significant_risks()` - Line 309
- `_compute_can_finalize()` - Line 325
- `_compute_materiality_values()` - Line 362

## 🛠️ Verification Script

**PowerShell script to check for anti-patterns:**

```powershell
# Save as: check_compute_patterns.ps1
cd C:\Users\HP\Documents\GitHub\alamaudit\qaco_planning_phase\models

Write-Host "🔍 PROMPT 5: Compute Pattern Compliance Check" -ForegroundColor Cyan

# Check 1: Find any remaining '.id' in @api.depends
Write-Host "`n❌ CHECK 1: @api.depends with .id (FORBIDDEN)" -ForegroundColor Red
$forbidden_id = Select-String -Path "*.py" -Pattern "@api\.depends.*\.id['\""']" -Context 0,1
if ($forbidden_id) {
    $forbidden_id | ForEach-Object { Write-Host "  $($_.Filename):$($_.LineNumber): $($_.Line)" }
} else {
    Write-Host "  ✅ PASS: No .id in @api.depends" -ForegroundColor Green
}

# Check 2: Find compute methods without try-except
Write-Host "`n🟡 CHECK 2: Compute methods without try-except (WARNING)" -ForegroundColor Yellow
$no_try = Select-String -Path "*.py" -Pattern "def _compute_" -Context 0,5 | Where-Object {
    $_.Context.PostContext -notmatch "try:"
}
if ($no_try) {
    Write-Host "  Found $($no_try.Count) methods without try-except (may need review)"
} else {
    Write-Host "  ✅ PASS: All compute methods have try-except" -ForegroundColor Green
}

# Check 3: Find compute methods without 'for rec in self:'
Write-Host "`n❌ CHECK 3: Compute methods without 'for rec in self:' (CRITICAL)" -ForegroundColor Red
$no_loop = Select-String -Path "*.py" -Pattern "def _compute_" -Context 0,3 | Where-Object {
    $_.Context.PostContext -notmatch "for rec in self:"
}
if ($no_loop) {
    Write-Host "  ⚠️ WARNING: Found methods that may not loop correctly"
    $no_loop | Select-Object -First 5 | ForEach-Object { 
        Write-Host "  $($_.Filename):$($_.LineNumber)"
    }
} else {
    Write-Host "  ✅ PASS: All compute methods loop over recordset" -ForegroundColor Green
}

# Check 4: Find compute methods with side effects
Write-Host "`n❌ CHECK 4: Compute methods with side effects (FORBIDDEN)" -ForegroundColor Red
$side_effects = Select-String -Path "*.py" -Pattern "def _compute_" -Context 0,20 | Where-Object {
    $_.Context.PostContext -match "\.write\(|\.create\(|\.unlink\(|\.send_"
}
if ($side_effects) {
    Write-Host "  ⚠️ CRITICAL: Found compute methods with side effects!"
    $side_effects | ForEach-Object { Write-Host "  $($_.Filename):$($_.LineNumber)" }
} else {
    Write-Host "  ✅ PASS: No side effects in compute methods" -ForegroundColor Green
}

Write-Host "`n✅ Verification complete" -ForegroundColor Green
```

**Run verification:**
```powershell
.\check_compute_patterns.ps1
```

## 📝 Refactoring Checklist (For Each Compute Method)

### Step 1: Add `for rec in self:` Loop
```python
# ❌ Before
@api.depends('state')
def _compute_is_locked(self):
    self.is_locked = self.state == 'approved'

# ✅ After
@api.depends('state')
def _compute_is_locked(self):
    for rec in self:
        rec.is_locked = rec.state == 'approved'
```

### Step 2: Add Null Guards
```python
# ❌ Before
@api.depends('audit_id')
def _compute_can_open(self):
    for rec in self:
        p1 = self.env['...'].search([('audit_id', '=', rec.audit_id.id)])
        rec.can_open = p1.state == 'approved'

# ✅ After
@api.depends('audit_id')
def _compute_can_open(self):
    for rec in self:
        if not rec.audit_id:  # ✅ Null guard
            rec.can_open = False
            continue
        p1 = self.env['...'].search([('audit_id', '=', rec.audit_id.id)], limit=1)
        rec.can_open = p1.state == 'approved' if p1 else False
```

### Step 3: Wrap in try-except
```python
# ❌ Before
@api.depends('business_risk_ids')
def _compute_risk_counts(self):
    for rec in self:
        if not rec.business_risk_ids:
            rec.total_risks = 0
            continue
        rec.total_risks = len(rec.business_risk_ids)

# ✅ After
@api.depends('business_risk_ids')
def _compute_risk_counts(self):
    for rec in self:
        try:
            if not rec.business_risk_ids:
                rec.total_risks = 0
                continue
            rec.total_risks = len(rec.business_risk_ids)
        except Exception as e:
            _logger.warning(f'Risk count compute failed for {rec.id}: {e}')
            rec.total_risks = 0
```

### Step 4: Add Docstring
```python
@api.depends('audit_id')
def _compute_can_open(self):
    """
    Determine if P-2 tab can be opened based on P-1 approval.
    Defensive: Safe even during module install/upgrade when audit_id is NULL.
    """
    for rec in self:
        try:
            if not rec.audit_id:
                rec.can_open = False
                continue
            # ... rest of method
```

## 🚀 Rollout Plan

### Phase 1: Critical `_compute_can_open()` Methods (Priority 1)
All P-tabs have a `_compute_can_open()` that enforces sequential workflow. These MUST be bulletproof.

**Files to fix:**
- `planning_p3_controls.py:480`
- `planning_p4_analytics.py:436`
- `planning_p5_materiality.py:306`
- `planning_p6_risk.py:40`
- `planning_p7_fraud.py:35`
- `planning_p8_going_concern.py:47`
- `planning_p9_laws.py:47`
- `planning_p10_related_parties.py:35`
- `planning_p11_group_audit.py:96`
- `planning_p12_strategy.py:97`
- `planning_p13_approval.py:47`

### Phase 2: Metrics/Counters (Priority 2)
Methods that aggregate counts/metrics - high crash risk if data incomplete.

**Examples:**
- `_compute_risk_counts()`
- `_compute_risk_metrics()`
- `_compute_component_metrics()`
- `_compute_total_hours()`

### Phase 3: Name/Display Fields (Priority 3)
Methods that compute display names - lower risk but should still be defensive.

**Examples:**
- `_compute_name()` (all P-tabs)
- `_compute_cycle_summary()`

### Phase 4: Validation (Final)
Run verification script, test module install, validate production upgrade.

## ✅ Success Criteria

**A compute method is PROMPT 5 compliant when:**
1. ✅ `@api.depends()` has ONLY real field names (no `.id`)
2. ✅ Contains `for rec in self:` loop
3. ✅ Has null guards for all dependent fields (`if not rec.field:`)
4. ✅ Wrapped in `try-except Exception` block
5. ✅ Logs warnings with `_logger.warning()` on error
6. ✅ Assigns safe default value in except block
7. ✅ Has descriptive docstring with "Defensive:" note
8. ✅ No side effects (no `.write()`, `.create()`, `.unlink()`)
9. ✅ Uses `.search(..., limit=1)` for performance
10. ✅ Checks model existence if cross-module dependency

## 📚 Reference Implementation

**See:** `planning_p2_entity.py` lines 189-840 for 5 fully compliant compute methods after PROMPT 2 hardening.

---

**Document Status**: ✅ PROMPT 5 DOCUMENTED  
**Implementation Status**: 🟡 PARTIAL (P-2 complete, remaining 77 methods need review)  
**Priority**: HIGH (Prevents production crashes)  
**Next Step**: Run verification script → Fix critical `_compute_can_open()` methods first
