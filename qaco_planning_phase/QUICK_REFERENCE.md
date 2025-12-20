# QACO Planning Phase - Quick Reference Guide

**Last Updated**: 2025 (Post Error Elimination)  
**Status**: ✅ Production-Ready

---

## 📋 Model Namespace Reference

### Canonical Model Names (USE THESE)

```python
# P-1 through P-5 (not modified in this phase)
'qaco.planning.p1.engagement'
'qaco.planning.p2.entity'
'qaco.planning.p3.control'
'qaco.planning.p4.analytics'
'qaco.planning.p5.materiality'

# P-6: Risk Assessment
'qaco.planning.p6.risk'                    # Main model
'qaco.planning.p6.risk.line'               # Child model

# P-7: Fraud Risk Assessment
'qaco.planning.p7.fraud'                   # Main model
'qaco.planning.p7.fraud.line'              # Child model

# P-8: Going Concern
'qaco.planning.p8.going.concern'           # Main model only (no child)

# P-9: Laws & Regulations
'qaco.planning.p9.laws'                    # Main model
'qaco.planning.p9.law.line'                # Child model (compliance)
'qaco.law.line'                            # Standalone law reference
'qaco.non.compliance.line'                 # Non-compliance tracking

# P-10: Related Parties
'qaco.planning.p10.related.parties'        # Main model
'qaco.planning.p10.related.party.line'     # Related party details
'qaco.related.party.line'                  # Standalone RP reference
'qaco.rpt.transaction.line'                # RPT transaction tracking

# P-11: Group Audit (ISA 600)
'qaco.planning.p11.group.audit'            # Main model
'qaco.planning.p11.component'              # Component identification
'qaco.planning.p11.component.risk'         # Component risk assessment
'qaco.planning.p11.component.auditor'      # Component auditor evaluation

# P-12: Audit Strategy & Detailed Plan
'qaco.planning.p12.strategy'               # Main model
'qaco.planning.p12.risk.response'          # Risk response design
'qaco.planning.p12.fs.area.strategy'       # FS area strategies
'qaco.planning.p12.audit.program'          # Detailed audit programs
'qaco.planning.p12.sampling.plan'          # Sampling methodology
'qaco.planning.p12.kam.candidate'          # KAM identification

# P-13: Planning Completion & Sign-Off
'qaco.planning.p13.approval'               # Main model
'qaco.planning.p13.checklist.line'         # Completion checklist
'qaco.planning.p13.change.log'             # Planning changes log
```

---

## 🚫 DEPRECATED Model Names (DO NOT USE)

These models were deleted during error elimination:

```python
# P-6 LEGACY (DELETED)
'audit.planning.p6.risk_assessment'        # ❌ Use qaco.planning.p6.risk
'audit.planning.p6.risk_line'              # ❌ Use qaco.planning.p6.risk.line

# P-7 LEGACY (DELETED)
'audit.planning.p7.fraud'                  # ❌ Use qaco.planning.p7.fraud (same name, different namespace!)
'audit.planning.p7.fraud_risk_line'        # ❌ Use qaco.planning.p7.fraud.line

# P-8 LEGACY (DELETED)
'audit.planning.p8.going_concern'          # ❌ Use qaco.planning.p8.going.concern (note dot)
'audit.planning.p8.gc_indicator_line'      # ❌ REMOVED (canonical model has no child)

# P-9 LEGACY (DELETED)
'audit.planning.p9.laws_regulations'       # ❌ Use qaco.planning.p9.laws
'audit.planning.p9.compliance_line'        # ❌ Use qaco.planning.p9.law.line

# P-10 LEGACY (DELETED - 6 models removed!)
'audit.planning.p10.related_parties'       # ❌ Use qaco.planning.p10.related.parties
'audit.planning.p10.related_party'         # ❌ Use qaco.planning.p10.related.party.line
'audit.planning.p10.rpt_transaction'       # ❌ Use qaco.rpt.transaction.line
'audit.planning.p10.rpt_risk_line'         # ❌ REMOVED (no canonical equivalent)
'audit.p10.completeness.procedure'         # ❌ REMOVED (no canonical equivalent)
'audit.p10.audit_procedure'                # ❌ REMOVED (no canonical equivalent)

# P-11/P-12 LEGACY (DELETED in previous phase)
'audit.planning.p11.*'                     # ❌ Use qaco.planning.p11.*
'audit.planning.p12.*'                     # ❌ Use qaco.planning.p12.*
```

---

## 🔗 One2many/Many2one Relationships

### P-6: Risk Assessment
```python
# Parent model: qaco.planning.p6.risk
risk_line_ids = fields.One2many(
    'qaco.planning.p6.risk.line',
    'p6_risk_id',                          # Inverse field name
    string='Risk Register'
)

# Child model: qaco.planning.p6.risk.line
p6_risk_id = fields.Many2one(
    'qaco.planning.p6.risk',
    required=True,
    ondelete='cascade'
)
```

### P-7: Fraud Risk Assessment
```python
# Parent: qaco.planning.p7.fraud
fraud_risk_line_ids = fields.One2many(
    'qaco.planning.p7.fraud.line',
    'p7_fraud_id',                         # Inverse field name
    string='Fraud Risk Register'
)

# Child: qaco.planning.p7.fraud.line
p7_fraud_id = fields.Many2one(
    'qaco.planning.p7.fraud',
    required=True
)
```

### P-9: Laws & Regulations
```python
# Parent: qaco.planning.p9.laws
law_line_ids = fields.One2many(
    'qaco.planning.p9.law.line',
    'p9_laws_id',                          # Inverse field name
    string='Laws & Regulations'
)

# Child: qaco.planning.p9.law.line
p9_laws_id = fields.Many2one(
    'qaco.planning.p9.laws',
    required=True
)
```

### P-11: Group Audit
```python
# Parent: qaco.planning.p11.group.audit
component_ids = fields.One2many(
    'qaco.planning.p11.component',
    'p11_id',                              # Inverse field name
    string='Components'
)

# Child: qaco.planning.p11.component
p11_id = fields.Many2one(
    'qaco.planning.p11.group.audit',
    required=True
)
```

**Pattern**: All child models use `p{N}_id` or `p{N}_{main_model}_id` as inverse field name

---

## 📂 File Locations

### Python Models
```
qaco_planning_phase/models/
├── planning_base.py              # Main orchestrator (qaco.planning.main)
├── planning_p1_engagement.py     # P-1: Engagement (unmodified)
├── planning_p2_entity.py         # P-2: Entity Understanding (unmodified)
├── planning_p3_control.py        # P-3: Internal Control (unmodified)
├── planning_p4_analytics.py      # P-4: Preliminary Analytics (unmodified)
├── planning_p5_materiality.py    # P-5: Materiality (unmodified)
├── planning_p6_risk.py           # P-6: Risk Assessment (✅ REFACTORED)
├── planning_p7_fraud.py          # P-7: Fraud Assessment (✅ REFACTORED)
├── planning_p8_going_concern.py  # P-8: Going Concern (✅ REFACTORED)
├── planning_p9_laws.py           # P-9: Laws & Regulations (✅ REFACTORED)
├── planning_p10_related_parties.py  # P-10: Related Parties (✅ REFACTORED)
├── planning_p11_group_audit.py   # P-11: Group Audit (✅ REFACTORED PHASE 1)
├── planning_p12_strategy.py      # P-12: Audit Strategy (✅ REFACTORED PHASE 1)
└── planning_p13_approval.py      # P-13: Planning Completion (unmodified)
```

### XML Views
```
qaco_planning_phase/views/
├── planning_p6_views.xml
├── planning_p7_views.xml
├── planning_p8_views.xml
├── planning_p9_views.xml
├── planning_p10_views.xml
├── planning_p10_related_parties_views.xml  # ✅ UPDATED (audit.* → qaco.*)
├── planning_p11_views_complete.xml         # ✅ UPDATED (audit.* → qaco.*)
├── planning_p12_views.xml
└── planning_p13_views.xml
```

### Security Rules
```
qaco_planning_phase/security/
├── ir.model.access.csv           # ✅ UPDATED (24 rules refactored)
└── security_groups.xml
```

---

## 🛠️ Common Maintenance Tasks

### Adding a New One2many Field

1. **In Parent Model:**
   ```python
   new_child_ids = fields.One2many(
       'qaco.planning.pX.child.model',
       'pX_parent_id',                    # ⚠️ Must match child field name!
       string='Child Records'
   )
   ```

2. **In Child Model:**
   ```python
   pX_parent_id = fields.Many2one(       # ⚠️ Must match parent inverse!
       'qaco.planning.pX.parent.model',
       required=True,
       ondelete='cascade'
   )
   ```

3. **Update XML View** (if needed):
   ```xml
   <field name="new_child_ids">
       <tree>
           <field name="field1"/>
           <field name="field2"/>
       </tree>
   </field>
   ```

4. **Update Security CSV** (if needed):
   ```csv
   access_qaco_planning_pX_child_model_trainee,qaco.planning.pX.child.model.trainee,model_qaco_planning_pX_child_model,qaco_audit.group_audit_trainee,1,1,1,0
   ```

### Creating a New P-Tab Model

1. **Create Model File**: `qaco_planning_phase/models/planning_pX_new.py`
2. **Use Canonical Namespace**: `_name = 'qaco.planning.pX.new'`
3. **Inherit Tracking**: `_inherit = ['mail.thread', 'mail.activity.mixin']`
4. **Add to planning_base.py**:
   ```python
   pX_new_id = fields.Many2one(
       'qaco.planning.pX.new',
       string='P-X: New Tab',
       readonly=True,
       copy=False
   )
   ```
5. **Update `_create_p_tabs()` method**:
   ```python
   if not self.pX_new_id:
       self.pX_new_id = self.env['qaco.planning.pX.new'].create({
           'audit_id': self.audit_id.id,
           'planning_main_id': self.id,
       })
   ```

---

## 🐛 Troubleshooting

### KeyError: "Model 'audit.planning.pX.*' not found"
**Cause**: Legacy model name used in code  
**Fix**: Search codebase for `audit.planning.pX` and replace with `qaco.planning.pX`
```bash
grep -r "audit.planning.pX" qaco_planning_phase/
```

### KeyError: "Field 'xyz_id' does not exist in model"
**Cause**: One2many inverse mismatch  
**Fix**: Check parent One2many inverse parameter matches child Many2one field name exactly
```python
# Parent
field_ids = fields.One2many('child.model', 'INVERSE_NAME')
# Child must have:
INVERSE_NAME = fields.Many2one('parent.model')
```

### Access Denied for Model
**Cause**: Missing or incorrect security CSV entry  
**Fix**: Add/update entry in `ir.model.access.csv`
```csv
access_model_name_trainee,qaco.planning.pX.model.trainee,model_qaco_planning_pX_model,qaco_audit.group_audit_trainee,1,1,1,0
```

### XML View Error: "Model not found"
**Cause**: XML view references legacy `audit.planning.*` model  
**Fix**: Update `<field name="model">` to use canonical `qaco.planning.*`
```xml
<!-- BEFORE -->
<field name="model">audit.planning.p6.risk_assessment</field>
<!-- AFTER -->
<field name="model">qaco.planning.p6.risk</field>
```

---

## 📊 Validation Checklist

Before deploying changes:

- [ ] Run `grep -r "audit\.planning" models/*.py` → Should return ZERO matches (excluding BACKUP files)
- [ ] Check all XML views have `model="qaco.planning.*"` attributes
- [ ] Verify ir.model.access.csv has entries for all new models
- [ ] Confirm One2many inverse fields match child Many2one field names
- [ ] Test module upgrade: `odoo-bin -u qaco_planning_phase -d test_db --stop-after-init`
- [ ] Test model resolution: `env['qaco.planning.pX.model'].search([])`
- [ ] Test planning phase creation: `env['qaco.planning.main'].create({...})._create_p_tabs()`
- [ ] Verify access rights for trainee/manager/partner users

---

## 📞 Support Resources

**Documentation:**
- `ERROR_ELIMINATION_COMPLETE.md` - Full refactoring summary
- `ERROR_ELIMINATION_PLAN.md` - Detailed methodology
- `P11_P12_REFACTORING_PLAN.md` - Phase 1 documentation
- `REFACTORING_INVENTORY.md` - Comprehensive codebase analysis

**Key Patterns:**
- Model naming: `qaco.planning.p{N}.{descriptor}` (dots for hierarchy)
- Class naming: `PlanningP{N}{DescriptorCamelCase}`
- Inverse field naming: `p{N}_id` or `p{N}_{parent}_id`
- Security ID: `model_qaco_planning_p{N}_{model_name}`

---

**Status**: ✅ **CURRENT** (Post-2025 Error Elimination)  
**Next Review**: After P-13 implementation or major structural changes  

---

*Quick reference guide maintained as part of qaco_planning_phase module*
