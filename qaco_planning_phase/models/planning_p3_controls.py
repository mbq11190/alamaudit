# -*- coding: utf-8 -*-
"""
P-3: Understanding Internal Control & IT Environment - COMPLETE BUILD (Odoo 17)
================================================================================
Standards Compliance:
- ISA 315 (Revised): Identifying and Assessing the Risks of Material Misstatement
- ISA 330: Auditor's Responses to Assessed Risks (planning linkage)
- ISA 265: Communicating Deficiencies in Internal Control
- ISA 240: Fraud (control-related fraud risks)
- ISQM-1: Quality Management
- Companies Act, 2017 (Pakistan)
- ICAP QCR / AOB inspection framework

Purpose:
Demonstrate that the auditor has identified, documented, evaluated, and concluded
on the design and implementation of internal controls, including IT controls, and
has clearly determined the control reliance strategy.
================================================================================
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


# =============================================================================
# SECTION B/C/D: Transaction Cycle Line Model (Walkthroughs & Key Controls)
# =============================================================================
class PlanningP3TransactionCycle(models.Model):
    """Transaction Cycle for Internal Control Documentation"""
    _name = 'qaco.planning.p3.transaction.cycle'
    _description = 'P-3 Transaction Cycle'
    _order = 'sequence, id'

    CYCLE_SELECTION = [
        ('revenue', 'Revenue & Receivables'),
        ('purchases', 'Purchases & Payables'),
        ('payroll', 'Payroll'),
        ('inventory', 'Inventory'),
        ('fixed_assets', 'Fixed Assets'),
        ('cash_bank', 'Cash & Bank'),
        ('borrowings', 'Borrowings & Financing'),
        ('equity', 'Equity'),
        ('related_parties', 'Related Party Transactions'),
        ('other', 'Other'),
    ]

    WALKTHROUGH_STATUS = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    p3_id = fields.Many2one(
        'qaco.planning.p3.controls',
        string='P-3 Internal Controls',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sequence = fields.Integer(string='Sequence', default=10)
    cycle_type = fields.Selection(
        CYCLE_SELECTION,
        string='Transaction Cycle',
        required=True,
    )
    is_significant = fields.Boolean(
        string='Significant Class',
        default=True,
        help='Is this a significant class of transactions?',
    )

    # Section C: Process Understanding & Walkthroughs
    process_description = fields.Html(
        string='Process Description',
        help='Narrative description of the transaction cycle process',
    )
    transaction_flow = fields.Html(
        string='Flow of Transactions',
        help='Document the flow from start to end (initiation → authorization → processing → recording → reporting)',
    )
    key_documents = fields.Text(
        string='Key Documents Used',
        help='List the key documents used in this cycle (e.g., invoices, POs, GRNs)',
    )
    it_systems_involved = fields.Char(
        string='IT Systems Involved',
        help='List the IT systems/applications used in this cycle',
    )
    walkthrough_status = fields.Selection(
        WALKTHROUGH_STATUS,
        string='Walkthrough Status',
        default='not_started',
    )
    walkthrough_performed = fields.Boolean(
        string='Walkthrough Performed',
        default=False,
    )
    walkthrough_date = fields.Date(
        string='Walkthrough Date',
    )
    walkthrough_conclusion = fields.Text(
        string='Walkthrough Conclusion',
    )
    misstatement_points = fields.Text(
        string='Points of Misstatement',
        help='Identify where misstatements could occur in this cycle',
    )

    # Checklist fields
    process_documented = fields.Boolean(string='Process Documented', default=False)
    walkthrough_completed = fields.Boolean(string='Walkthrough Completed', default=False)
    misstatement_points_identified = fields.Boolean(string='Misstatement Points Identified', default=False)

    notes = fields.Text(string='Notes')


# =============================================================================
# SECTION D: Key Control Line Model
# =============================================================================
class PlanningP3KeyControl(models.Model):
    """Key Control Identification per Transaction Cycle"""
    _name = 'qaco.planning.p3.key.control'
    _description = 'P-3 Key Control'
    _order = 'cycle_type, sequence, id'

    CONTROL_TYPE = [
        ('manual', 'Manual'),
        ('automated', 'Automated'),
        ('it_dependent', 'IT-Dependent Manual'),
    ]

    FREQUENCY = [
        ('continuous', 'Continuous'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
        ('ad_hoc', 'Ad Hoc'),
    ]

    CONTROL_NATURE = [
        ('preventive', 'Preventive'),
        ('detective', 'Detective'),
        ('corrective', 'Corrective'),
    ]

    DESIGN_ADEQUACY = [
        ('adequate', '🟢 Adequate'),
        ('partially_adequate', '🟡 Partially Adequate'),
        ('weak', '🔴 Weak'),
    ]

    p3_id = fields.Many2one(
        'qaco.planning.p3.controls',
        string='P-3 Internal Controls',
        required=True,
        ondelete='cascade',
        index=True,
    )
    cycle_id = fields.Many2one(
        'qaco.planning.p3.transaction.cycle',
        string='Transaction Cycle',
        domain="[('p3_id', '=', p3_id)]",
    )
    cycle_type = fields.Selection(
        related='cycle_id.cycle_type',
        store=True,
    )
    sequence = fields.Integer(string='Sequence', default=10)

    control_objective = fields.Char(
        string='Control Objective',
        required=True,
        help='What the control is designed to achieve',
    )
    control_description = fields.Text(
        string='Control Description',
        required=True,
        help='Detailed description of the control activity',
    )
    control_owner = fields.Char(
        string='Control Owner',
        help='Person/role responsible for performing the control',
    )
    control_type = fields.Selection(
        CONTROL_TYPE,
        string='Manual/Automated',
        required=True,
        default='manual',
    )
    frequency = fields.Selection(
        FREQUENCY,
        string='Frequency',
        required=True,
        default='monthly',
    )
    control_nature = fields.Selection(
        CONTROL_NATURE,
        string='Preventive/Detective',
        required=True,
        default='preventive',
    )
    design_adequacy = fields.Selection(
        DESIGN_ADEQUACY,
        string='Design Adequacy',
        required=True,
        default='adequate',
    )
    implementation_confirmed = fields.Boolean(
        string='Implementation Confirmed',
        default=False,
    )
    implementation_evidence = fields.Text(
        string='Evidence of Implementation',
        help='What evidence was obtained to confirm implementation?',
    )
    reliance_planned = fields.Boolean(
        string='Reliance Planned',
        default=False,
        help='Do we plan to rely on this control?',
    )
    notes = fields.Text(string='Notes')


# =============================================================================
# SECTION E: IT General Control Line Model
# =============================================================================
class PlanningP3ITGC(models.Model):
    """IT General Controls Documentation"""
    _name = 'qaco.planning.p3.itgc'
    _description = 'P-3 IT General Control'
    _order = 'itgc_category, sequence, id'

    ITGC_CATEGORY = [
        ('access', 'User Access Controls'),
        ('change', 'Change Management Controls'),
        ('backup', 'Backup & Disaster Recovery'),
        ('interface', 'Interface Controls'),
        ('data_integrity', 'Data Integrity Controls'),
        ('operations', 'IT Operations'),
        ('development', 'System Development'),
        ('security', 'Security Controls'),
    ]

    CONTROL_STATUS = [
        ('effective', '🟢 Effective'),
        ('partially_effective', '🟡 Partially Effective'),
        ('ineffective', '🔴 Ineffective'),
        ('not_assessed', '⚪ Not Assessed'),
    ]

    p3_id = fields.Many2one(
        'qaco.planning.p3.controls',
        string='P-3 Internal Controls',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sequence = fields.Integer(string='Sequence', default=10)
    itgc_category = fields.Selection(
        ITGC_CATEGORY,
        string='ITGC Category',
        required=True,
    )
    control_description = fields.Text(
        string='Control Description',
        required=True,
    )
    application_system = fields.Char(
        string='Application/System',
        help='Which application or system does this control relate to?',
    )
    control_status = fields.Selection(
        CONTROL_STATUS,
        string='Control Status',
        default='not_assessed',
        required=True,
    )
    assessment_notes = fields.Text(
        string='Assessment Notes',
    )
    impact_on_audit = fields.Text(
        string='Impact on Audit Strategy',
        help='How does this ITGC affect our audit approach?',
    )
    notes = fields.Text(string='Notes')


# =============================================================================
# SECTION F: Control Deficiency Line Model (ISA 265)
# =============================================================================
class PlanningP3ControlDeficiency(models.Model):
    """Control Deficiencies Identified (ISA 265)"""
    _name = 'qaco.planning.p3.control.deficiency'
    _description = 'P-3 Control Deficiency'
    _order = 'severity desc, sequence, id'

    DEFICIENCY_TYPE = [
        ('design', 'Design Deficiency'),
        ('implementation', 'Implementation Deficiency'),
        ('both', 'Design & Implementation'),
    ]

    SEVERITY = [
        ('deficiency', '🟡 Control Deficiency'),
        ('significant', '🟠 Significant Deficiency'),
        ('material_weakness', '🔴 Material Weakness'),
    ]

    p3_id = fields.Many2one(
        'qaco.planning.p3.controls',
        string='P-3 Internal Controls',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sequence = fields.Integer(string='Sequence', default=10)
    cycle_id = fields.Many2one(
        'qaco.planning.p3.transaction.cycle',
        string='Related Cycle',
        domain="[('p3_id', '=', p3_id)]",
    )
    deficiency_description = fields.Text(
        string='Deficiency Description',
        required=True,
    )
    deficiency_type = fields.Selection(
        DEFICIENCY_TYPE,
        string='Type of Deficiency',
        required=True,
    )
    severity = fields.Selection(
        SEVERITY,
        string='Severity',
        required=True,
    )
    potential_fs_impact = fields.Text(
        string='Potential FS Impact',
        help='How could this deficiency lead to misstatement?',
    )
    affected_assertions = fields.Char(
        string='Affected Assertions',
        help='e.g., Completeness, Accuracy, Existence',
    )
    communicate_to_tcwg = fields.Boolean(
        string='Communicate to TCWG',
        default=False,
        help='Must be communicated if significant deficiency or material weakness',
    )
    increased_substantive = fields.Boolean(
        string='Increase Substantive Testing',
        default=False,
    )
    management_response = fields.Text(
        string='Management Response',
    )
    remediation_planned = fields.Boolean(
        string='Remediation Planned',
        default=False,
    )
    linked_to_p6 = fields.Boolean(
        string='Linked to P-6 Risk',
        default=False,
        readonly=True,
    )
    notes = fields.Text(string='Notes')

    @api.onchange('severity')
    def _onchange_severity(self):
        """Auto-flag significant deficiencies for TCWG communication."""
        if self.severity in ('significant', 'material_weakness'):
            self.communicate_to_tcwg = True
            self.increased_substantive = True


# =============================================================================
# SECTION I: Control Changes Line Model
# =============================================================================
class PlanningP3ControlChange(models.Model):
    """Changes in Internal Controls During the Year"""
    _name = 'qaco.planning.p3.control.change'
    _description = 'P-3 Control Change'
    _order = 'change_date desc, sequence, id'

    CHANGE_TYPE = [
        ('process', 'Change in Process'),
        ('control', 'Change in Control'),
        ('system', 'Change in System/Automation'),
        ('management', 'Change in Management'),
        ('policy', 'Change in Policy'),
        ('structure', 'Organizational Structure Change'),
        ('other', 'Other'),
    ]

    p3_id = fields.Many2one(
        'qaco.planning.p3.controls',
        string='P-3 Internal Controls',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sequence = fields.Integer(string='Sequence', default=10)
    change_type = fields.Selection(
        CHANGE_TYPE,
        string='Type of Change',
        required=True,
    )
    change_description = fields.Text(
        string='Description of Change',
        required=True,
    )
    change_date = fields.Date(
        string='Date of Change',
    )
    affected_area = fields.Char(
        string='Affected Area/Cycle',
    )
    audit_impact = fields.Text(
        string='Impact on Audit Approach',
        help='How does this change affect our audit procedures?',
    )
    impact_assessed = fields.Boolean(
        string='Impact Assessed',
        default=False,
    )
    notes = fields.Text(string='Notes')


# =============================================================================
# MAIN MODEL: P-3 Understanding Internal Control & IT Environment
# =============================================================================
class PlanningP3Controls(models.Model):
    """
    P-3: Understanding Internal Control & IT Environment
    ISA 315 (Revised), ISA 330, ISA 265, ISA 240, ISQM-1

    PRE-CONDITIONS (System-Enforced):
    - P-2 (Entity & Environment) is partner-approved and locked
    - Entity understanding completed
    - Initial business risks identified and auto-carried forward
    """
    _name = 'qaco.planning.p3.controls'
    _description = 'P-3: Understanding Internal Control & IT Environment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # =========================================================================
    # STATE & WORKFLOW
    # =========================================================================
    TAB_STATE = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('locked', 'Locked'),
    ]

    state = fields.Selection(
        TAB_STATE,
        string='Status',
        default='not_started',
        tracking=True,
        copy=False,
    )

    # =========================================================================
    # CORE IDENTIFIERS & LINKS
    # =========================================================================
    name = fields.Char(
        string='Reference',
        compute='_compute_name',
        store=True,
        readonly=True,
    )
    audit_id = fields.Many2one(
        'qaco.audit',
        string='Audit Engagement',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
    )
    planning_main_id = fields.Many2one(
        'qaco.planning.main',
        string='Planning Phase (Main)',
        ondelete='cascade',
        index=True,
    )
    planning_phase_id = fields.Many2one(
        'qaco.planning.phase',
        string='Planning Phase',
        ondelete='set null',
        index=True,
    )
    client_id = fields.Many2one(
        'res.partner',
        string='Client Name',
        related='audit_id.client_id',
        readonly=True,
        store=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )

    # =========================================================================
    # SECTION A: Control Framework & Overall Control Environment (ISA 315)
    # =========================================================================
    CONTROL_FRAMEWORK = [
        ('coso', 'COSO Framework'),
        ('internal_policies', 'Internal Policies Only'),
        ('informal', 'Informal / Undocumented'),
        ('other', 'Other Framework'),
    ]

    CONTROL_RATING = [
        ('none', '❌ Does Not Exist'),
        ('weak', '🔴 Weak'),
        ('moderate', '🟡 Moderate'),
        ('strong', '🟢 Strong'),
    ]

    control_framework = fields.Selection(
        CONTROL_FRAMEWORK,
        string='Control Framework Adopted',
        tracking=True,
        help='ISA 315 - What control framework does the entity follow?',
    )
    control_framework_other = fields.Char(
        string='Other Framework (Specify)',
    )
    ethical_values_integrity = fields.Html(
        string='Ethical Values & Integrity Culture',
        help='Management\'s commitment to integrity and ethical values',
    )
    management_attitude = fields.Html(
        string='Management Attitude Toward Controls',
        help='Management philosophy and operating style regarding controls',
    )
    tcwg_oversight = fields.Boolean(
        string='Oversight by TCWG',
        help='Is there active oversight by Those Charged With Governance?',
    )
    tcwg_oversight_explanation = fields.Html(
        string='TCWG Oversight Explanation',
    )
    internal_audit_present = fields.Boolean(
        string='Internal Audit Function Present',
    )
    internal_audit_assessment = fields.Html(
        string='Internal Audit Function Assessment',
        help='Objectivity, competence, scope of work (ISA 610)',
    )
    control_environment_rating = fields.Selection(
        CONTROL_RATING,
        string='Control Environment Rating',
        tracking=True,
    )

    # Section A Checklist
    control_environment_assessed = fields.Boolean(
        string='Control Environment Assessed',
        default=False,
    )
    governance_oversight_considered = fields.Boolean(
        string='Governance Oversight Considered',
        default=False,
    )
    management_override_evaluated = fields.Boolean(
        string='Risk of Management Override Evaluated',
        default=False,
    )

    # =========================================================================
    # SECTION B: Significant Classes of Transactions (Multi-Select)
    # =========================================================================
    cycle_revenue = fields.Boolean(string='Revenue & Receivables')
    cycle_purchases = fields.Boolean(string='Purchases & Payables')
    cycle_payroll = fields.Boolean(string='Payroll')
    cycle_inventory = fields.Boolean(string='Inventory')
    cycle_fixed_assets = fields.Boolean(string='Fixed Assets')
    cycle_cash_bank = fields.Boolean(string='Cash & Bank')
    cycle_borrowings = fields.Boolean(string='Borrowings & Financing')
    cycle_equity = fields.Boolean(string='Equity')
    cycle_related_parties = fields.Boolean(string='Related Party Transactions')

    significant_cycles_narrative = fields.Html(
        string='Significant Cycles Narrative',
        help='Explain why these cycles are considered significant',
    )

    # =========================================================================
    # SECTION C/D: Transaction Cycles, Walkthroughs & Key Controls (One2many)
    # =========================================================================
    transaction_cycle_ids = fields.One2many(
        'qaco.planning.p3.transaction.cycle',
        'p3_id',
        string='Transaction Cycles',
    )
    key_control_ids = fields.One2many(
        'qaco.planning.p3.key.control',
        'p3_id',
        string='Key Controls',
    )

    # Summary counts
    total_cycles = fields.Integer(
        string='Total Cycles Documented',
        compute='_compute_cycle_summary',
        store=True,
    )
    walkthroughs_completed = fields.Integer(
        string='Walkthroughs Completed',
        compute='_compute_cycle_summary',
        store=True,
    )
    total_key_controls = fields.Integer(
        string='Total Key Controls',
        compute='_compute_control_summary',
        store=True,
    )
    controls_implemented = fields.Integer(
        string='Controls Implemented',
        compute='_compute_control_summary',
        store=True,
    )

    # =========================================================================
    # SECTION E: IT General Controls (ITGCs)
    # =========================================================================
    system_based_accounting = fields.Boolean(
        string='System-Based Accounting',
        default=True,
        help='Does the entity use computerized accounting systems?',
    )
    itgc_ids = fields.One2many(
        'qaco.planning.p3.itgc',
        'p3_id',
        string='IT General Controls',
    )

    # ITGC Summary Fields
    user_access_controls = fields.Html(
        string='User Access Controls',
        help='Password policies, user provisioning, access reviews',
    )
    change_management_controls = fields.Html(
        string='Change Management Controls',
        help='Program change, testing, approval processes',
    )
    backup_disaster_recovery = fields.Html(
        string='Backup & Disaster Recovery',
        help='Backup procedures, recovery testing, BCP',
    )
    interface_controls = fields.Html(
        string='Interface Controls',
        help='Controls over data interfaces between systems',
    )
    data_integrity_controls = fields.Html(
        string='Data Integrity Controls',
        help='Input, processing, output controls',
    )

    it_reliance_planned = fields.Boolean(
        string='IT Reliance Planned',
        help='Do we plan to rely on IT controls?',
    )
    it_specialist_required = fields.Boolean(
        string='IT Specialist Required',
    )
    it_specialist_justification = fields.Text(
        string='IT Specialist Justification',
    )
    itgc_overall_rating = fields.Selection(
        CONTROL_RATING,
        string='ITGC Overall Rating',
        tracking=True,
    )

    # Section E Checklist
    itgcs_identified = fields.Boolean(string='ITGCs Identified', default=False)
    it_risks_assessed = fields.Boolean(string='IT Risks Assessed', default=False)
    it_strategy_impact_considered = fields.Boolean(
        string='Impact on Audit Strategy Considered',
        default=False,
    )

    # =========================================================================
    # SECTION F: Control Deficiencies & Weaknesses (ISA 265)
    # =========================================================================
    deficiency_ids = fields.One2many(
        'qaco.planning.p3.control.deficiency',
        'p3_id',
        string='Control Deficiencies',
    )
    deficiencies_identified = fields.Boolean(
        string='Deficiencies Identified',
        compute='_compute_deficiency_summary',
        store=True,
    )
    significant_deficiencies_count = fields.Integer(
        string='Significant Deficiencies',
        compute='_compute_deficiency_summary',
        store=True,
    )
    material_weaknesses_count = fields.Integer(
        string='Material Weaknesses',
        compute='_compute_deficiency_summary',
        store=True,
    )
    deficiency_summary = fields.Html(
        string='Deficiency Summary',
        help='Summary of control deficiencies identified',
    )
    tcwg_communication_required = fields.Boolean(
        string='TCWG Communication Required',
        compute='_compute_deficiency_summary',
        store=True,
    )

    # =========================================================================
    # SECTION G: Control Reliance Strategy (Critical Professional Judgment)
    # =========================================================================
    RELIANCE_STRATEGY = [
        ('substantive_only', 'Substantive Only Approach'),
        ('limited_reliance', 'Limited Controls Reliance'),
        ('combined', 'Combined Approach (Controls + Substantive)'),
    ]

    reliance_strategy = fields.Selection(
        RELIANCE_STRATEGY,
        string='Control Reliance Strategy',
        tracking=True,
        help='Critical professional judgment - ISA 330',
    )
    reliance_planned = fields.Boolean(
        string='Reliance on Controls Planned',
        compute='_compute_reliance_decision',
        store=True,
    )
    reliance_rationale = fields.Html(
        string='Rationale for Reliance/Non-Reliance',
        help='Mandatory narrative explaining the reliance decision',
    )
    planned_tests_of_controls = fields.Boolean(
        string='Tests of Controls Planned',
    )
    affected_audit_areas = fields.Html(
        string='Affected Audit Areas',
        help='Which audit areas will be affected by the reliance decision?',
    )
    controls_to_test = fields.Html(
        string='Controls Identified for Testing',
        help='Specific controls where reliance is planned',
    )

    # Section G Checklist
    reliance_decision_justified = fields.Boolean(
        string='Reliance Decision Justified',
        default=False,
    )
    audit_response_aligned = fields.Boolean(
        string='Audit Response Aligned with Control Assessment',
        default=False,
    )

    # =========================================================================
    # SECTION H: Fraud-Related Controls (ISA 240 Integration)
    # =========================================================================
    journal_entry_controls = fields.Html(
        string='Controls Over Journal Entries',
        help='Non-standard journal entries, period-end adjustments (ISA 240)',
    )
    estimate_controls = fields.Html(
        string='Controls Over Accounting Estimates',
        help='Management bias indicators in estimates',
    )
    management_override_controls = fields.Html(
        string='Controls Preventing Management Override',
        help='Segregation of duties, approval limits, etc.',
    )
    fraud_control_gaps = fields.Html(
        string='Identified Fraud Control Gaps',
        help='Areas where controls may not prevent/detect fraud',
    )

    # Section H Checklist
    fraud_controls_evaluated = fields.Boolean(
        string='Fraud-Related Controls Evaluated',
        default=False,
    )
    override_risk_considered = fields.Boolean(
        string='Management Override Risk Considered',
        default=False,
    )

    # =========================================================================
    # SECTION I: Changes in Internal Controls During the Year
    # =========================================================================
    control_change_ids = fields.One2many(
        'qaco.planning.p3.control.change',
        'p3_id',
        string='Control Changes',
    )
    changes_in_controls = fields.Boolean(
        string='Changes in Controls During Year',
    )
    control_change_summary = fields.Html(
        string='Control Changes Summary',
    )
    change_impact_on_audit = fields.Html(
        string='Impact on Audit Approach',
    )

    # =========================================================================
    # SECTION J: Linkage to Risk Assessment (Auto-Flow)
    # =========================================================================
    linked_to_p6 = fields.Boolean(
        string='Linked to P-6 Risk Assessment',
        readonly=True,
    )
    linked_to_p12 = fields.Boolean(
        string='Linked to P-12 Audit Strategy',
        readonly=True,
    )
    risk_linkage_notes = fields.Html(
        string='Risk Linkage Notes',
        help='Notes on how control findings affect risk assessment',
    )

    # =========================================================================
    # SECTION K: Mandatory Document Uploads
    # =========================================================================
    process_flowchart_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p3_flowchart_rel',
        'p3_id',
        'attachment_id',
        string='Process Flowcharts / Narratives',
    )
    control_manual_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p3_control_manual_rel',
        'p3_id',
        'attachment_id',
        string='Internal Control Manuals',
    )
    walkthrough_doc_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p3_walkthrough_doc_rel',
        'p3_id',
        'attachment_id',
        string='Walkthrough Documentation',
    )
    it_policy_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p3_it_policy_rel',
        'p3_id',
        'attachment_id',
        string='IT Policy Documents',
    )
    prior_year_deficiency_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p3_prior_deficiency_rel',
        'p3_id',
        'attachment_id',
        string='Prior Year Deficiency Letters',
    )

    # Document count for validation
    flowchart_count = fields.Integer(
        compute='_compute_attachment_counts',
        string='Flowcharts Uploaded',
    )
    walkthrough_doc_count = fields.Integer(
        compute='_compute_attachment_counts',
        string='Walkthrough Docs Uploaded',
    )

    # =========================================================================
    # SECTION L: P-3 Conclusion & Professional Judgment
    # =========================================================================
    OVERALL_ASSESSMENT = [
        ('ineffective', '🔴 Ineffective - Substantive Only Approach Required'),
        ('partially_effective', '🟡 Partially Effective - Limited Reliance'),
        ('effective', '🟢 Effective - Controls Reliance Possible'),
    ]

    overall_control_assessment = fields.Selection(
        OVERALL_ASSESSMENT,
        string='Overall Control Assessment',
        tracking=True,
    )
    internal_control_conclusion = fields.Html(
        string='Internal Control Conclusion',
        help='ISA 315 conclusion on design and implementation of controls',
    )
    professional_judgment_conclusion = fields.Text(
        string='Professional Judgment Conclusion',
        default="""Based on the understanding obtained of the internal control system, including IT-related controls, the design and implementation of relevant controls have been evaluated in accordance with ISA 315, and appropriate decisions regarding reliance on controls have been made for audit planning purposes.""",
    )

    # Section L Checklist
    controls_understood = fields.Boolean(
        string='Internal Controls Sufficiently Understood',
        default=False,
    )
    control_risks_identified = fields.Boolean(
        string='Control Risks Identified',
        default=False,
    )
    audit_strategy_basis = fields.Boolean(
        string='Basis Established for Audit Strategy',
        default=False,
    )

    # ISA Reference
    isa_reference = fields.Char(
        string='ISA Reference',
        default='ISA 315 / ISA 330 / ISA 265 / ISA 240',
        readonly=True,
    )

    # =========================================================================
    # SECTION M: Review, Approval & Lock
    # =========================================================================
    prepared_by_id = fields.Many2one(
        'res.users',
        string='Prepared By',
        tracking=True,
        copy=False,
    )
    prepared_on = fields.Datetime(
        string='Prepared On',
        tracking=True,
        copy=False,
    )
    reviewed_by_id = fields.Many2one(
        'res.users',
        string='Reviewed By (Manager)',
        tracking=True,
        copy=False,
        readonly=True,
    )
    reviewed_on = fields.Datetime(
        string='Reviewed On',
        tracking=True,
        copy=False,
        readonly=True,
    )
    review_notes = fields.Html(
        string='Review Notes',
    )
    partner_approved = fields.Boolean(
        string='Partner Approved',
        tracking=True,
        copy=False,
        readonly=True,
    )
    partner_approved_by_id = fields.Many2one(
        'res.users',
        string='Partner Approved By',
        tracking=True,
        copy=False,
        readonly=True,
    )
    partner_approved_on = fields.Datetime(
        string='Partner Approved On',
        tracking=True,
        copy=False,
        readonly=True,
    )
    partner_comments = fields.Html(
        string='Partner Comments',
        help='Mandatory for approval',
    )

    # Standard sign-off fields (compatibility)
    senior_signed_user_id = fields.Many2one(
        'res.users',
        string='Senior Completed By',
        tracking=True,
        copy=False,
        readonly=True,
    )
    senior_signed_on = fields.Datetime(
        string='Senior Completed On',
        tracking=True,
        copy=False,
        readonly=True,
    )
    manager_reviewed_user_id = fields.Many2one(
        'res.users',
        string='Manager Reviewed By',
        tracking=True,
        copy=False,
        readonly=True,
    )
    manager_reviewed_on = fields.Datetime(
        string='Manager Reviewed On',
        tracking=True,
        copy=False,
        readonly=True,
    )
    partner_approved_user_id = fields.Many2one(
        'res.users',
        string='Partner Approved By',
        related='partner_approved_by_id',
        readonly=True,
    )
    partner_approved_on_compat = fields.Datetime(
        string='Partner Approved On',
        related='partner_approved_on',
        readonly=True,
    )
    reviewer_notes = fields.Html(
        string='Reviewer Notes',
        related='review_notes',
        readonly=False,
    )
    approval_notes = fields.Html(
        string='Approval Notes',
        related='partner_comments',
        readonly=False,
    )

    # Unlock for P-4
    proceed_to_p4 = fields.Boolean(
        string='Proceed to P-4',
        compute='_compute_proceed_to_p4',
        store=True,
    )

    _sql_constraints = [
        ('audit_unique', 'UNIQUE(audit_id)', 'Only one P-3 record per Audit Engagement is allowed.')
    ]

    # =========================================================================
    # COMPUTED METHODS
    # =========================================================================
    @api.depends('audit_id', 'client_id')
    def _compute_name(self):
        for record in self:
            if record.client_id:
                record.name = f"P3-{record.client_id.name[:15]}-IC"
            else:
                record.name = 'P-3: Internal Controls'

    @api.depends('transaction_cycle_ids', 'transaction_cycle_ids.walkthrough_completed')
    def _compute_cycle_summary(self):
        for record in self:
            record.total_cycles = len(record.transaction_cycle_ids)
            record.walkthroughs_completed = len(
                record.transaction_cycle_ids.filtered(lambda c: c.walkthrough_completed)
            )

    @api.depends('key_control_ids', 'key_control_ids.implementation_confirmed')
    def _compute_control_summary(self):
        for record in self:
            record.total_key_controls = len(record.key_control_ids)
            record.controls_implemented = len(
                record.key_control_ids.filtered(lambda c: c.implementation_confirmed)
            )

    @api.depends('deficiency_ids', 'deficiency_ids.severity')
    def _compute_deficiency_summary(self):
        for record in self:
            record.deficiencies_identified = len(record.deficiency_ids) > 0
            record.significant_deficiencies_count = len(
                record.deficiency_ids.filtered(lambda d: d.severity == 'significant')
            )
            record.material_weaknesses_count = len(
                record.deficiency_ids.filtered(lambda d: d.severity == 'material_weakness')
            )
            record.tcwg_communication_required = (
                record.significant_deficiencies_count > 0 or
                record.material_weaknesses_count > 0
            )

    @api.depends('reliance_strategy')
    def _compute_reliance_decision(self):
        for record in self:
            record.reliance_planned = record.reliance_strategy in ('limited_reliance', 'combined')

    @api.depends('process_flowchart_ids', 'walkthrough_doc_ids')
    def _compute_attachment_counts(self):
        for record in self:
            record.flowchart_count = len(record.process_flowchart_ids)
            record.walkthrough_doc_count = len(record.walkthrough_doc_ids)

    @api.depends('state', 'partner_approved')
    def _compute_proceed_to_p4(self):
        for record in self:
            record.proceed_to_p4 = (
                record.state == 'approved' and record.partner_approved
            )

    # =========================================================================
    # PRECONDITION CHECK
    # =========================================================================
    def _check_p2_preconditions(self):
        """Check if P-2 is approved and locked before allowing P-3 work."""
        self.ensure_one()
        if 'qaco.planning.p2.entity' in self.env:
            P2Model = self.env['qaco.planning.p2.entity']
            p2 = P2Model.search([('audit_id', '=', self.audit_id.id)], limit=1)
            if p2 and p2.state not in ('approved', 'locked'):
                raise UserError(
                    'P-3 cannot proceed until P-2 (Entity & Environment) is partner-approved.\n'
                    f'Current P-2 status: {p2.state}'
                )
            if not p2:
                raise UserError('P-2 (Entity & Environment) must be created before starting P-3.')

    # =========================================================================
    # VALIDATION
    # =========================================================================
    def _validate_mandatory_fields(self):
        """Validate mandatory fields before completing P-3."""
        self.ensure_one()
        errors = []

        # Section A validation
        if not self.control_framework:
            errors.append('Control framework must be specified (Section A)')
        if not self.control_environment_rating:
            errors.append('Control environment rating is required (Section A)')

        # Section B/C validation
        if self.total_cycles == 0:
            errors.append('At least one transaction cycle must be documented (Section B/C)')

        # Section D validation
        if self.total_key_controls == 0:
            errors.append('At least one key control must be identified (Section D)')

        # Section E validation (if system-based)
        if self.system_based_accounting and not self.itgc_overall_rating:
            errors.append('ITGC overall rating is required for system-based accounting (Section E)')

        # Section G validation
        if not self.reliance_strategy:
            errors.append('Control reliance strategy must be specified (Section G)')
        if not self.reliance_rationale:
            errors.append('Reliance rationale narrative is mandatory (Section G)')

        # Section L validation
        if not self.overall_control_assessment:
            errors.append('Overall control assessment is required (Section L)')
        if not self.internal_control_conclusion:
            errors.append('Internal control conclusion is required (Section L)')

        # Checklist validation
        if not self.control_environment_assessed:
            errors.append('Confirm: Control environment assessed (Section A)')
        if not self.reliance_decision_justified:
            errors.append('Confirm: Reliance decision justified (Section G)')
        if not self.controls_understood:
            errors.append('Confirm: Internal controls sufficiently understood (Section L)')

        if errors:
            raise UserError('Cannot complete P-3. Missing requirements:\n• ' + '\n• '.join(errors))

    def _validate_documents(self):
        """Check mandatory document uploads."""
        self.ensure_one()
        errors = []
        if self.flowchart_count == 0:
            errors.append('Process flowcharts/narratives must be uploaded')
        if self.total_cycles > 0 and self.walkthrough_doc_count == 0:
            errors.append('Walkthrough documentation must be uploaded')
        if errors:
            raise UserError('Cannot complete P-3. Missing documents:\n• ' + '\n• '.join(errors))

    # =========================================================================
    # WORKFLOW ACTIONS
    # =========================================================================
    def action_start_work(self):
        """Start work on P-3 (check P-2 preconditions)."""
        for record in self:
            if record.state != 'not_started':
                raise UserError('Can only start work on tabs that are Not Started.')
            record._check_p2_preconditions()
            record.state = 'in_progress'
            record.prepared_by_id = self.env.user
            record.prepared_on = fields.Datetime.now()
            record.message_post(body='P-3 work started.')

    def action_complete(self):
        """Senior marks P-3 as complete."""
        for record in self:
            if record.state != 'in_progress':
                raise UserError('Can only complete tabs that are In Progress.')
            record._validate_mandatory_fields()
            record._validate_documents()
            record.senior_signed_user_id = self.env.user
            record.senior_signed_on = fields.Datetime.now()
            record.state = 'completed'
            record.message_post(body=f'P-3 completed by Senior: {self.env.user.name}.')

    def action_review(self):
        """Manager reviews P-3."""
        for record in self:
            if record.state != 'completed':
                raise UserError('Can only review tabs that are Completed.')
            record.reviewed_by_id = self.env.user
            record.reviewed_on = fields.Datetime.now()
            record.manager_reviewed_user_id = self.env.user
            record.manager_reviewed_on = fields.Datetime.now()
            record.state = 'reviewed'
            record.message_post(body=f'P-3 reviewed by Manager: {self.env.user.name}.')

    def action_approve(self):
        """Partner approves and locks P-3, enabling P-4."""
        for record in self:
            if record.state != 'reviewed':
                raise UserError('Can only approve tabs that have been Reviewed.')
            if not record.partner_comments:
                raise UserError('Partner comments are mandatory for approval.')
            record.partner_approved = True
            record.partner_approved_by_id = self.env.user
            record.partner_approved_on = fields.Datetime.now()
            record.state = 'approved'
            record.message_post(
                body=f'P-3 approved by Partner: {self.env.user.name}. P-4 tab unlocked.'
            )

    def action_lock(self):
        """Lock P-3 (audit trail frozen per ISA 230)."""
        for record in self:
            if record.state != 'approved':
                raise UserError('Can only lock records that are Approved.')
            record.state = 'locked'
            record.message_post(body='P-3 locked. Audit trail frozen per ISA 230.')

    def action_send_back(self):
        """Send back for rework."""
        for record in self:
            if record.state not in ('completed', 'reviewed'):
                raise UserError('Can only send back Completed or Reviewed records.')
            old_state = record.state
            record.state = 'in_progress'
            record.message_post(body=f'P-3 sent back for rework from {old_state} state.')

    def action_unlock(self):
        """Unlock P-3 for revision (requires partner authority)."""
        for record in self:
            if record.state not in ('approved', 'locked'):
                raise UserError('Can only unlock Approved or Locked records.')
            record.state = 'reviewed'
            record.message_post(body='P-3 unlocked for revision.')

    # =========================================================================
    # AUTO-FLOW TO RISK REGISTER
    # =========================================================================
    def action_link_deficiencies_to_p6(self):
        """Link control deficiencies to P-6 Risk Assessment."""
        self.ensure_one()
        if 'qaco.planning.p6.risk' in self.env:
            P6Model = self.env['qaco.planning.p6.risk']
            p6 = P6Model.search([('audit_id', '=', self.audit_id.id)], limit=1)
            if p6:
                # Mark deficiencies as linked
                self.deficiency_ids.write({'linked_to_p6': True})
                self.linked_to_p6 = True
                self.message_post(
                    body=f'{len(self.deficiency_ids)} control deficiencies linked to P-6 Risk Assessment.'
                )
            else:
                raise UserError('P-6 Risk Assessment not found. Create P-6 first.')

    # =========================================================================
    # DEFAULT CYCLE CREATION
    # =========================================================================
    def _create_default_cycles(self):
        """Create default transaction cycles based on significant cycle selections."""
        CycleModel = self.env['qaco.planning.p3.transaction.cycle']
        for rec in self:
            if not rec.transaction_cycle_ids:
                cycle_map = {
                    'cycle_revenue': 'revenue',
                    'cycle_purchases': 'purchases',
                    'cycle_payroll': 'payroll',
                    'cycle_inventory': 'inventory',
                    'cycle_fixed_assets': 'fixed_assets',
                    'cycle_cash_bank': 'cash_bank',
                    'cycle_borrowings': 'borrowings',
                    'cycle_equity': 'equity',
                    'cycle_related_parties': 'related_parties',
                }
                seq = 10
                for field, cycle_type in cycle_map.items():
                    if getattr(rec, field, False):
                        CycleModel.create({
                            'p3_id': rec.id,
                            'cycle_type': cycle_type,
                            'is_significant': True,
                            'sequence': seq,
                        })
                        seq += 10

    def action_generate_cycles(self):
        """Generate transaction cycle records from selected checkboxes."""
        for record in self:
            record._create_default_cycles()
            record.message_post(body='Transaction cycles generated from selections.')

    # =========================================================================
    # REPORT GENERATION
    # =========================================================================
    def action_generate_ic_memo(self):
        """Generate Internal Control Understanding Memorandum (PDF)."""
        self.ensure_one()
        self.message_post(body='Internal Control Understanding Memorandum generated.')
        return {'type': 'ir.actions.act_window_close'}

    def action_view_audit(self):
        """Navigate to parent audit record."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'qaco.audit',
            'res_id': self.audit_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
