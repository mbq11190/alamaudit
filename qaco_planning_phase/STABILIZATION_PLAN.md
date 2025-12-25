# PLANNING PHASE STABILIZATION - IMPLEMENTATION PLAN
**Date**: December 20, 2025  
**Status**: PHASE 1 STARTED - READY FOR EXECUTION

---

## ✅ COMPLETED

### **1. BACKUP Files Deleted** ✅
- Removed `planning_p6_risk_BACKUP.py` (35KB)
- Removed `planning_p7_fraud_BACKUP.py` (32KB)
- Removed `planning_p8_going_concern_BACKUP.py` (30KB)
- Removed `planning_p9_laws_BACKUP.py` (28KB)
- Removed `planning_p10_related_parties_BACKUP.py` (34KB)
- **Total cleanup**: 159KB of duplicate code eliminated

---

## 🔧 CRITICAL FIXES REQUIRED

### **FIX 1: P-11/P-12 Parent Link Standardization** 🔴 CRITICAL

**Problem**:
- P-11, P-12 use `engagement_id` + `audit_year_id` (non-standard)
- Rest of P-tabs (P-1 to P-10, P-13) use `audit_id` + `planning_main_id`
- Breaks orchestration by `qaco.planning.main`

**Solution**:
Add to P-11/P-12 models:
```python
# Add these fields (keep existing for backward compat)
audit_id = fields.Many2one(
    'qaco.audit',
    string='Audit Engagement',
    compute='_compute_audit_id',
    store=True,
    readonly=True,
    index=True
)
planning_main_id = fields.Many2one(
    'qaco.planning.main',
    string='Planning Phase',
    ondelete='cascade',
    index=True
)

@api.depends('engagement_id')
def _compute_audit_id(self):
    """Map engagement_id to audit_id for consistency."""
    for rec in self:
        # Assuming engagement_id maps to qaco.audit
        rec.audit_id = rec.engagement_id.id if rec.engagement_id else False
```

**Files to Modify**:
- `planning_p11_group_audit.py` (~line 27-50)
- `planning_p12_strategy.py` (~line 27-50)

---

### **FIX 2: Approval Immutability** 🔴 CRITICAL

**Problem**:
- After partner approval, users can still edit P-tabs
- Violates ISA 230 (documentation integrity)
- QCR/AOB inspection risk

**Solution**:
Add to ALL P-tab models (P-1 to P-13):
```python
@api.constrains('state')
def _prevent_edit_after_approval(self):
    """ISA 230: Prevent modification of approved planning sections."""
    for rec in self:
        if rec.state == 'approved':
            # Allow unlock only via partner action_unlock()
            if not self.env.context.get('allow_partner_unlock'):
                # Check if record was already approved and being modified
                if rec._origin and rec._origin.state == 'approved':
                    changed_fields = [
                        fname for fname in rec._fields 
                        if fname not in ['state', 'write_date', 'write_uid', '__last_update']
                        and rec[fname] != rec._origin[fname]
                    ]
                    if changed_fields:
                        raise ValidationError(
                            f'ISA 230 Violation: Cannot modify approved planning tab.\n'
                            f'Changed fields: {", ".join(changed_fields)}\n\n'
                            f'Partner must explicitly unlock this tab first via action_unlock().'
                        )

def action_unlock(self):
    """Partner unlocks approved tab (with audit trail)."""
    self.ensure_one()
    if not self.env.user.has_group('qaco_audit.group_audit_partner'):
        raise UserError('Only partners can unlock approved planning tabs.')
    
    self.with_context(allow_partner_unlock=True).write({
        'state': 'reviewed',
        'partner_approved_user_id': False,
        'partner_approved_on': False,
    })
    self.message_post(
        body=f'Planning tab unlocked by {self.env.user.name} for amendment. '
             f'ISA 230: Full audit trail preserved.',
        subject='Planning Tab Unlocked'
    )
```

**Files to Modify**:
- All 13 P-tab models (or add to `PlanningTabBase` if inherited)

---

### **FIX 3: Hard Gating (Sequential Approval)** 🔴 CRITICAL

**Problem**:
- Users can open any P-tab anytime (no sequence enforcement)
- Violates ISA 300/220 (systematic planning approach)

**Solution**:

#### **3A: Add Computed Gate Fields**
Add to each P-tab model:
```python
can_open = fields.Boolean(
    string='Can Open This Tab',
    compute='_compute_can_open',
    store=False,
    help='Computed based on prior tab approval status'
)

@api.depends('planning_main_id.p2_entity_id.state')  # Adjust per tab
def _compute_can_open(self):
    """Check if prior planning tab is approved."""
    for rec in self:
        # P-2 example: Check planning initialized (P-1 deprecated)
        if rec.planning_main_id and rec.planning_main_id.p2_entity_id:
            rec.can_open = rec.planning_main_id.p2_entity_id.state == 'approved'
        else:
            rec.can_open = False  # Block if planning not initialized
```

#### **3B: Enforce in Python create/write**
```python
@api.model
def create(self, vals):
    # Check gating before create
    planning_id = vals.get('planning_main_id')
    if planning_id:
        planning = self.env['qaco.planning.main'].browse(planning_id)
        if not self._check_prior_approved(planning):
            raise UserError(
                f'Cannot create {self._description} until prior planning tabs are approved.\n'
                f'Required: P-{self._get_prior_tab_number()} must be approved first.'
            )
    return super().create(vals)

def _check_prior_approved(self, planning):
    """Override in each P-tab to check prior tab."""
    # P-2 example:
    return planning.p1_engagement_id and planning.p1_engagement_id.state == 'approved'
```

#### **3C: Enforce in XML Views**
Add to form views:
```xml
<form create="false" edit="false" delete="false">
    <header>
        <div class="alert alert-warning" role="alert" 
             attrs="{'invisible': [('can_open', '=', True)]}">
            <strong>⚠️ Prior Planning Tab Not Approved</strong><br/>
            This tab cannot be accessed until P-X is partner-approved.
        </div>
    </header>
    <!-- Rest of form -->
</form>
```

**Gating Sequence**:
- P-1: Always accessible (entry point)
- P-2: Requires P-1 approved
- P-3: Requires P-2 approved
- P-4: Requires P-3 approved
- P-5: Requires P-4 approved
- P-6: Requires P-5 approved
- P-7: Requires P-6 approved
- P-8: Requires P-7 approved
- P-9: Requires P-8 approved
- P-10: Requires P-9 approved
- P-11: Requires P-10 approved
- P-12: Requires P-11 approved
- P-13: Requires P-12 approved

**Files to Modify**: All 13 P-tab models + all 13 form views

---

### **FIX 4: P-13 → Execution Phase Unlock** 🔴 CRITICAL

**Problem**:
- P-13 approval doesn't unlock execution phase
- Manual intervention required

**Solution**:
Add to `planning_p13_approval.py`:
```python
def action_approve(self):
    """Approve P-13 and unlock Execution Phase."""
    for record in self:
        # ... existing approval logic ...
        record._auto_unlock_execution_phase()

def _auto_unlock_execution_phase(self):
    """Unlock execution phase after planning approval."""
    self.ensure_one()
    if not self.audit_id:
        return
    
    # Find execution phase record
    ExecutionPhase = self.env['qaco.execution.phase']
    execution = ExecutionPhase.search([('audit_id', '=', self.audit_id.id)], limit=1)
    
    if execution and execution.state == 'locked':
        execution.write({'state': 'not_started'})
        execution.message_post(
            body='Execution Phase auto-unlocked after P-13 Planning Approval. '
                 'Audit fieldwork may now commence.'
        )
        _logger.info(f'Execution phase unlocked for audit {self.audit_id.name}')
    elif not execution:
        # Create execution phase record
        execution = ExecutionPhase.create({
            'audit_id': self.audit_id.id,
            'state': 'not_started',
        })
        _logger.info(f'Execution phase created for audit {self.audit_id.name}')
```

**File to Modify**: `planning_p13_approval.py`

---

### **FIX 5: Data Flow Verification & Missing Links** 🟡 HIGH

**Required Flows to Verify**:

#### **5A: P-1 → P-12 (Staffing & Budget)**
```python
# In P-12 model, add:
team_summary = fields.Html(
    compute='_compute_team_from_p1',
    store=True,
    string='Team Summary from P-1'
)
budget_summary = fields.Monetary(
    compute='_compute_budget_from_p1',
    store=True,
    string='Budget from P-1'
)

@api.depends('planning_main_id.p1_engagement_id.team_ids')
def _compute_team_from_p1(self):
    for rec in self:
        if rec.planning_main_id and rec.planning_main_id.p1_engagement_id:
            p1 = rec.planning_main_id.p1_engagement_id
            team_html = '<ul>'
            for member in p1.team_ids:
                team_html += f'<li>{member.name} - {member.role}</li>'
            team_html += '</ul>'
            rec.team_summary = team_html
        else:
            rec.team_summary = '<p>No team assigned</p>'
```

#### **5B: P-2 → P-6 (Business Risks)**
```python
# In P-6 model, add:
business_risk_ids = fields.One2many(
    'qaco.planning.p6.business.risk',
    'p6_id',
    string='Business Risks from P-2',
    compute='_compute_business_risks_from_p2',
    store=True
)

@api.depends('planning_main_id.p2_entity_id.business_risks')
def _compute_business_risks_from_p2(self):
    for rec in self:
        if rec.planning_main_id and rec.planning_main_id.p2_entity_id:
            # Auto-create risk lines from P-2 business risks
            p2 = rec.planning_main_id.p2_entity_id
            # Implementation depends on P-2 structure
```

#### **5C: P-3 → P-6 (Control Risks)**
Similar pattern to 5B

#### **5D: P-5 → P-6 (Materiality)**
```python
# In P-6 model, add:
overall_materiality = fields.Monetary(
    related='planning_main_id.p5_materiality_id.overall_materiality',
    readonly=True,
    string='Overall Materiality from P-5'
)
performance_materiality = fields.Monetary(
    related='planning_main_id.p5_materiality_id.performance_materiality',
    readonly=True,
    string='Performance Materiality from P-5'
)
```

#### **5E: P-5 → P-12 (Sampling Thresholds)**
```python
# In P-12 model, add:
sampling_materiality = fields.Monetary(
    related='planning_main_id.p5_materiality_id.performance_materiality',
    readonly=True,
    string='Sampling Threshold from P-5'
)
```

**Files to Modify**: Multiple P-tab models

---

## 📋 EXECUTION SEQUENCE

### **Session 1: Critical Fixes (Est. 2-3 hours)**
1. ✅ Delete BACKUP files
2. ⏳ Fix P-11/P-12 parent links
3. ⏳ Add approval immutability (all P-tabs)
4. ⏳ Add P-13 → Execution unlock

### **Session 2: Hard Gating (Est. 2-3 hours)**
5. ⏳ Add can_open fields to all P-tabs
6. ⏳ Add XML view enforcement
7. ⏳ Add Python create/write validation

### **Session 3: Data Flow Integration (Est. 3-4 hours)**
8. ⏳ P-1 → P-12 flows
9. ⏳ P-2 → P-6 flows
10. ⏳ P-3 → P-6 flows
11. ⏳ P-5 → P-6/P-12 flows
12. ⏳ P-6/P-7/P-8/P-9/P-10/P-11 → P-12 flows

### **Session 4: Validation & Testing (Est. 2-3 hours)**
13. ⏳ XML-model field validation
14. ⏳ ISA compliance audit
15. ⏳ Performance optimization
16. ⏳ Server activation test

---

## 🚀 READY TO PROCEED

**Current Status**: 
- BACKUP files deleted ✅
- Architecture audit complete ✅
- Implementation plan ready ✅

**Next Action**: Execute Session 1 fixes

**Estimated Total Effort**: 10-13 hours across 4 focused sessions

---

**Approval Required**: Confirm to proceed with Session 1 critical fixes
