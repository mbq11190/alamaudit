# Production Testing Guide - Hard Gating System
**Module**: `qaco_planning_phase`  
**Test Date**: December 20, 2025  
**Changes**: Sessions 1+2 Complete (Architecture + Hard Gating)

---

## Pre-flight Checklist ✅

- [x] **Syntax Check**: No Python errors detected in modified files
- [x] **Import Validation**: All `UserError` imports added to P-4, P-5
- [x] **Files Modified**: 12 models (P-2 through P-13)
- [x] **Lines Added**: ~500 (can_open fields + constraints)
- [x] **ISA Citations**: All error messages include ISA 300/220 references

---

## Test Environment Setup

### 1. Database Backup (MANDATORY)
```bash
# Backup production database BEFORE upgrade
pg_dump -U odoo_user -h localhost -d production_db -F c -f backup_pre_gating_$(date +%Y%m%d_%H%M%S).backup

# OR use Odoo backup
# Settings → Database Manager → Backup
```

### 2. Module Upgrade Command
```bash
# Option A: Upgrade on test database first (RECOMMENDED)
cd C:\Users\HP\Documents\GitHub\alamaudit
python odoo-bin -c odoo.conf -d test_db -u qaco_planning_phase --log-level=info

# Option B: Production upgrade (after test passes)
python odoo-bin -c odoo.conf -d production_db -u qaco_planning_phase --log-level=warn
```

### 3. Monitor Upgrade Logs
Watch for:
- ✅ `Module qaco_planning_phase: loading objects`
- ✅ `qaco.planning.p2.entity: model created`
- ✅ `ir.model.constraint: creating constraint qaco_planning_p2_entity_check_sequential_gating`
- ❌ Any `ERROR` or `CRITICAL` messages
- ⚠️ Any `WARNING` about missing fields (acceptable if new fields)

---

## Functional Testing Scenarios

### TEST 1: Sequential Gating Enforcement

**Objective**: Verify P-tabs cannot be accessed out of sequence

#### Test Steps:
1. **Create New Audit**:
   ```
   Audits → Audit Management → Create
   - Client: Test Client Ltd
   - Year: 2025
   - Type: Statutory Audit
   - Save
   ```

2. **Test P-2 Block** (EXPECTED FAIL):
   ```
   Open Planning → Planning Main → [Your Audit]
   → Planning Tabs Smart Button → P-2: Entity Understanding
   → Click "Start Entity Understanding" button
   
   EXPECTED RESULT:
   ❌ UserError raised:
   "ISA 300/220 Violation: Sequential Planning Approach Required.
   
   P-2 (Entity Understanding) cannot be started until P-1 (Engagement Setup) 
   has been Partner-approved.
   
   Reason: Per ISA 300, engagement terms must be agreed before entity 
   understanding begins to ensure proper scope and resource allocation...
   
   Action: Please complete and obtain Partner approval for P-1 first."
   ```

3. **Approve P-1 to Unlock P-2**:
   ```
   Planning Tabs → P-1: Engagement Setup
   → Click "Start Engagement" (if not started)
   → Fill mandatory fields:
     - Engagement Letter attached
     - Team Members added
     - Time Budget lines created
   → Click "Manager Sign-Off"
   → Click "Partner Sign-Off"
   → Verify P-1 state = 'approved'
   ```

4. **Test P-2 Unlock** (EXPECTED SUCCESS):
   ```
   Planning Tabs → P-2: Entity Understanding
   → Click "Start Entity Understanding"
   
   EXPECTED RESULT:
   ✅ P-2 opens successfully, state changes to 'in_progress'
   ```

5. **Test P-3 Block** (EXPECTED FAIL):
   ```
   Planning Tabs → P-3: Internal Controls
   → Click "Start Controls Assessment"
   
   EXPECTED RESULT:
   ❌ UserError raised citing P-2 must be approved first
   ```

6. **Chain Test P-1 → P-13**:
   - Approve each P-tab sequentially
   - Verify next tab unlocks automatically
   - Verify error message quality at each gate

**PASS CRITERIA**:
- ✅ All 12 gates block premature access
- ✅ All error messages display ISA citations
- ✅ Approved tabs unlock next in chain immediately
- ✅ can_open field computes in real-time (no server restart needed)

---

### TEST 2: Edge Cases & State Handling

**Objective**: Verify special state handling for P-6, P-11, P-12, P-13

#### Test Steps:

1. **P-6 → P-7 Transition** (Locked State):
   ```
   Approve P-1 through P-5 sequentially
   → Open P-6: Risk Assessment
   → Complete risk register
   → Click "Lock P-6"
   → Verify P-6 state = 'locked' (NOT 'approved')
   
   Open P-7: Fraud Risk
   → Click "Start Fraud Assessment"
   
   EXPECTED RESULT:
   ✅ P-7 unlocks when P-6.state == 'locked'
   
   ERROR MESSAGE SHOULD CITE:
   "P-7 cannot be started until P-6 has been Partner-approved and locked"
   ```

2. **P-11 → P-12 Transition** (Partner/Locked):
   ```
   Approve P-7 through P-10 sequentially
   → Open P-11: Group Audit Considerations
   → Complete group audit fields
   → Click "Partner Sign-Off" (state → 'partner')
   
   Open P-12: Overall Audit Strategy
   → Click "Start Strategy"
   
   EXPECTED RESULT:
   ✅ P-12 unlocks when P-11.state in ('partner', 'locked')
   
   Verify can_open logic:
   p11 = self.env['qaco.planning.p11.group.audit'].search([...], limit=1)
   return p11.state in ('partner', 'locked')
   ```

3. **P-12 → P-13 Transition** (Partner/Locked):
   ```
   Open P-12: Overall Audit Strategy
   → Complete strategy sections
   → Click "Partner Sign-Off" (state → 'partner')
   
   Open P-13: Planning Approval
   → Click "Start Final Approval"
   
   EXPECTED RESULT:
   ✅ P-13 unlocks when P-12.state in ('partner', 'locked')
   ```

**PASS CRITERIA**:
- ✅ P-6 locked state properly gates P-7
- ✅ P-11 partner/locked states properly gate P-12
- ✅ P-12 partner/locked states properly gate P-13
- ✅ Error messages correctly cite state requirements

---

### TEST 3: Data Flow Integration

**Objective**: Verify data flows from P-2, P-3, P-5 to P-6 and P-12

#### Test Steps:

1. **P-2 → P-6 Business Risks**:
   ```
   Open P-2: Entity Understanding
   → Section: Business Risk Identification
   → Add business risk:
     - Risk: "Revenue recognition complexity"
     - Category: Accounting
     - Impact: High
   → Save
   → Verify field: linked_to_p6 = False
   
   Approve P-2, P-3, P-4, P-5
   
   Open P-6: Risk Assessment
   → Check risk_line_ids
   
   EXPECTED RESULT:
   ✅ Business risk from P-2 appears in P-6 risk register
   ✅ P-2 risk now shows linked_to_p6 = True
   ```

2. **P-3 → P-6 Control Deficiencies**:
   ```
   Open P-3: Internal Controls
   → Section: Control Deficiency Assessment
   → Add deficiency:
     - Description: "Lack of segregation of duties"
     - Severity: Significant
     - Type: Design
   → Save
   → Verify field: linked_to_p6 = False
   
   After P-6 creation:
   → Check deficiency_ids in P-6
   
   EXPECTED RESULT:
   ✅ Control deficiency from P-3 linked to P-6
   ✅ P-3 deficiency shows linked_to_p6 = True
   ```

3. **P-5 → P-6 Materiality**:
   ```
   Open P-5: Materiality
   → Set overall_materiality = 1,000,000 PKR
   → Verify performance_materiality auto-calculates (e.g., 750,000)
   → Verify clearly_trivial_threshold auto-calculates (e.g., 50,000)
   → Lock P-5
   
   Open P-6: Risk Assessment
   → Try to create without P-5 locked
   
   EXPECTED RESULT:
   ❌ Constraint prevents P-6 creation if P-5 not locked
   ✅ P-6.sources_materiality = True
   ✅ P-6 uses P-5 thresholds for risk rating
   ```

4. **P-6 → P-12 Risk-Response Mapping**:
   ```
   Open P-6: Risk Assessment
   → Add risk lines (high RMM areas)
   → Lock P-6
   
   Approve P-7 through P-11
   
   Open P-12: Overall Audit Strategy
   → Check risk_response_ids One2many
   
   EXPECTED RESULT:
   ✅ P-12.risk_response_ids populated from P-6 risk register
   ✅ Help text confirms: "Auto-populated from P-6, P-7, P-8, P-9, P-10"
   ✅ rmm_alignment_confirmed field present
   ```

5. **P-5 → P-12 Sampling Strategy**:
   ```
   Open P-12: Overall Audit Strategy
   → Section E: Sampling Strategy (ISA 530)
   → Check sampling_plan_ids
   
   EXPECTED RESULT:
   ✅ Sampling plans reference P-5 materiality thresholds
   ✅ sampling_methodology selection field present
   ```

**PASS CRITERIA**:
- ✅ All `linked_to_p6` flags set correctly
- ✅ P-5 materiality flows to P-6 constraints
- ✅ P-6 risk register feeds P-12 strategy
- ✅ No manual data re-entry required

---

### TEST 4: Approval Immutability (Session 1)

**Objective**: Verify Session 1 immutability still works post-upgrade

#### Test Steps:

1. **Test Approved Tab Edit Block**:
   ```
   Approve P-1 (state = 'approved')
   → Try to edit engagement letter field
   
   EXPECTED RESULT:
   ❌ Write operation blocked by ApprovalImmutabilityBase
   ✅ Only Partner can unlock via special action
   ```

2. **Test P-13 → Execution Unlock** (Session 1):
   ```
   Complete all P-1 through P-12
   → Open P-13: Planning Approval
   → Click "Partner Approval for Planning"
   → Verify P-13.state = 'partner_approved'
   
   Check Audit:
   → audit_id.execution_unlocked = True
   → Execution phase menu/buttons now enabled
   
   EXPECTED RESULT:
   ✅ Execution phase unlocks automatically
   ✅ Per ISA 300: planning must complete before execution starts
   ```

**PASS CRITERIA**:
- ✅ Immutability preserved after upgrade
- ✅ P-13 approval triggers execution unlock
- ✅ Audit trail remains intact

---

### TEST 5: User Experience & Error Quality

**Objective**: Verify error messages are regulator-defensible

#### Evaluation Criteria:

For each of the 12 gated P-tabs, verify error messages contain:

1. **ISA Citation**: "ISA 300/220 Violation: Sequential Planning Approach Required"
2. **Context**: Which tab is blocked and why
3. **Reason**: Audit methodology justification (ISA paragraph if applicable)
4. **Action**: Clear instruction on what to do next

**Example Perfect Error** (P-5):
```
ISA 300/220 Violation: Sequential Planning Approach Required.

P-5 (Materiality) cannot be started until P-4 (Analytics) has been Partner-approved.

Reason: Per ISA 320, materiality must be determined based on understanding of the 
entity and its environment (P-2), controls (P-3), and analytical procedures (P-4). 
Premature materiality assessment risks incorrect thresholds.

Action: Please complete and obtain Partner approval for P-4 first.
```

**PASS CRITERIA**:
- ✅ All 12 error messages are professionally worded
- ✅ No generic "Access denied" messages
- ✅ Messages would satisfy QCR/AOB review
- ✅ Users understand exactly what to do next

---

## Regression Testing

### Verify No Breakage of Existing Features:

1. **Smart Buttons**:
   - Client Onboarding button still works
   - Planning Main → Planning Tabs navigation intact
   - All 13 P-tab buttons visible and clickable

2. **Stage Progression** (qaco_audit):
   - Audit stage moves still work
   - Followers still auto-subscribe
   - Chatter messages still post

3. **Existing Constraints**:
   - P-5 percentage validation still works (0-100%)
   - P-6 risk rating computation still accurate
   - P-12 sampling plan constraints still enforced

4. **Reports & Views**:
   - Planning summary report renders
   - All form views display correctly
   - Tree views show all columns

**PASS CRITERIA**:
- ✅ No features broken by gating implementation
- ✅ All existing workflows still functional
- ✅ No performance degradation (can_open computes quickly)

---

## Performance Testing

### can_open Field Performance:

1. **Computation Speed**:
   ```python
   # Test with 100 audit records
   # Each P-tab should compute can_open in < 100ms
   
   import time
   p2_records = env['qaco.planning.p2.entity'].search([])
   start = time.time()
   for rec in p2_records:
       _ = rec.can_open  # Trigger computation
   elapsed = time.time() - start
   
   EXPECTED: elapsed < 10 seconds for 100 records (< 100ms each)
   ```

2. **Database Impact**:
   - No new tables created (computed field, store=False)
   - No indexes required (searches use existing audit_id index)
   - Constraint validation adds negligible overhead (runs only on state change)

**PASS CRITERIA**:
- ✅ can_open computes in < 100ms per record
- ✅ No database bloat
- ✅ No slow queries in PostgreSQL logs

---

## Rollback Plan (If Issues Found)

### Emergency Rollback Steps:

1. **Stop Odoo Server**:
   ```bash
   # Linux
   sudo systemctl stop odoo
   
   # Windows
   # Stop Odoo service in Services.msc
   ```

2. **Restore Database Backup**:
   ```bash
   # Drop current database
   dropdb -U odoo_user production_db
   
   # Restore pre-upgrade backup
   pg_restore -U odoo_user -h localhost -d production_db backup_pre_gating_*.backup
   ```

3. **Revert Code Changes** (if needed):
   ```bash
   cd C:\Users\HP\Documents\GitHub\alamaudit
   git log --oneline  # Find commit before Session 2
   git checkout <commit-hash>  # Revert to pre-gating state
   ```

4. **Restart Odoo**:
   ```bash
   python odoo-bin -c odoo.conf -d production_db
   ```

---

## Success Criteria Summary

### Must Pass (Critical):
- ✅ Module upgrades without errors
- ✅ All 12 sequential gates block premature access
- ✅ All 12 error messages display ISA citations
- ✅ Approved tabs unlock next in chain automatically
- ✅ No existing features broken

### Should Pass (High Priority):
- ✅ P-6, P-11, P-12 state handling correct
- ✅ Data flows (P-2→P-6, P-3→P-6, P-5→P-6) work
- ✅ Approval immutability still enforced
- ✅ P-13 execution unlock still works
- ✅ can_open computes in < 100ms

### Nice to Have (Enhancement):
- ✅ Error messages are user-friendly
- ✅ No performance degradation
- ✅ Logs are clean (no warnings)

---

## Test Completion Report Template

```
PRODUCTION TEST REPORT
Date: _________________
Tester: _______________
Database: _____________

PRE-FLIGHT:
[ ] Database backed up
[ ] Module upgraded successfully
[ ] No errors in Odoo logs

TEST 1 - SEQUENTIAL GATING:
[ ] P-2 blocks without P-1 approval
[ ] P-1 approval unlocks P-2
[ ] All 12 gates tested and working
[ ] Error messages display correctly

TEST 2 - EDGE CASES:
[ ] P-6 locked state gates P-7
[ ] P-11 partner/locked gates P-12
[ ] P-12 partner/locked gates P-13

TEST 3 - DATA FLOWS:
[ ] P-2 business risks → P-6
[ ] P-3 control deficiencies → P-6
[ ] P-5 materiality → P-6
[ ] P-6 risks → P-12 strategy

TEST 4 - IMMUTABILITY:
[ ] Approved tabs cannot be edited
[ ] P-13 approval unlocks execution

TEST 5 - ERROR QUALITY:
[ ] All error messages cite ISA 300/220
[ ] Messages are actionable and clear

REGRESSION:
[ ] Smart buttons work
[ ] Existing constraints work
[ ] Reports render correctly

PERFORMANCE:
[ ] can_open computes quickly
[ ] No slow queries observed

ISSUES FOUND:
______________________________
______________________________

OVERALL RESULT: [ ] PASS  [ ] FAIL
```

---

## Next Steps After Testing

### If All Tests PASS:
1. ✅ Deploy to production
2. ✅ Train users on new sequential workflow
3. ✅ Update user documentation
4. ✅ Monitor first real audit for issues
5. ✅ Proceed with **Session 3**: XML-Model validation scan

### If Tests FAIL:
1. ❌ Document failure details
2. ❌ Execute rollback plan
3. ❌ Fix identified issues in dev environment
4. ❌ Re-test on test database
5. ❌ Retry production deployment when stable

---

## Contact & Support

**Repository**: `c:\Users\HP\Documents\GitHub\alamaudit`  
**Module**: `qaco_planning_phase`  
**Session 2 Completion**: December 20, 2025  
**Files Modified**: 12 models (P-2 through P-13)  
**Lines Added**: ~500 (can_open fields + constraints)

**Audit Trail**:
- Session 1: Architecture fixes (BACKUP deletion, P-11/P-12 links, immutability, P-13 unlock)
- Session 2: Hard gating (can_open fields, state constraints, ISA 300/220 errors)
- Session 3: TBD (XML validation, full integration testing)

---

**END OF PRODUCTION TEST GUIDE**
