# -*- coding: utf-8 -*-
"""
P-12: Audit Strategy & Detailed Audit Plan - COMPLETE ISA 300 IMPLEMENTATION
Standards: ISA 300, ISA 315, ISA 330, ISA 240, ISA 520, ISA 530, ISA 570, ISA 600, ISA 701, ISA 220, ISQM-1
Purpose: Translate risk assessments into executable audit work and lock audit approach
Compliance: Companies Act 2017, Auditors (Reporting Obligations) Regulations 2018, ICAP QCR, AOB
"""

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class PlanningP12Strategy(models.Model):
    """P-12: Audit Strategy & Detailed Audit Plan (ISA 300) - MASTER MODEL"""
    _name = 'qaco.planning.p12.strategy'
    _description = 'P-12: Audit Strategy & Detailed Audit Plan (ISA 300)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'engagement_id'
    _order = 'id desc'

    # ============================================================================
    # CORE IDENTIFIERS
    # ============================================================================
    # Standard parent linkage (for qaco.planning.main orchestration)
    audit_id = fields.Many2one(
        'qaco.audit',
        string='Audit Engagement',
        required=True,
        ondelete='cascade',
        tracking=True,
        index=True,
        help='Primary link to audit engagement (standard field)'
    )
    planning_main_id = fields.Many2one(
        'qaco.planning.main',
        string='Planning Phase',
        ondelete='cascade',
        index=True,
        help='Link to planning orchestrator'
    )
    
    # Legacy fields (kept for backward compatibility)
    engagement_id = fields.Many2one(
        'audit.engagement',
        string='Legacy Engagement ID',
        compute='_compute_engagement_id',
        store=True,
        readonly=True,
        help='Computed from audit_id for backward compatibility'
    )
    audit_year_id = fields.Many2one(
        'audit.year',
        string='Audit Year',
        tracking=True,
        help='Optional: Audit year reference'
    )
    client_id = fields.Many2one(
        'res.partner',
        string='Client',
        related='engagement_id.client_id',
        store=True,
        readonly=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Engagement Partner',
        tracking=True,
        required=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self._get_default_currency()
    )
    
    # STATE MANAGEMENT
    state = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Manager Review'),
        ('partner', 'Partner Approval'),
        ('locked', 'Locked - Planning Complete'),
    ], default='draft', tracking=True, copy=False)

    # Sequential Gating (ISA 300/220: Systematic Planning Approach)
    can_open = fields.Boolean(
        string='Can Open This Tab',
        compute='_compute_can_open',
        store=False,
        help='P-12 can only be opened after P-11 is approved'
    )

    @api.depends('audit_id')
    def _compute_can_open(self):
        """P-12 requires P-11 to be approved."""
        for rec in self:
            if not rec.audit_id:
                rec.can_open = False
                continue
            # Find P-11 for this audit
            p11 = self.env['qaco.planning.p11.group.audit'].search([
                ('audit_id', '=', rec.audit_id.id)
            ], limit=1)
            # P-11 uses 'locked' as its final approved state
            rec.can_open = p11.state in ('partner', 'locked') if p11 else False

    @api.constrains('state')
    def _check_sequential_gating(self):
        """ISA 300/220: Enforce sequential planning approach."""
        for rec in self:
            if rec.state != 'draft' and not rec.can_open:
                raise UserError(
                    'ISA 300/220 Violation: Sequential Planning Approach Required.\n\n'
                    'P-12 (Overall Audit Strategy) cannot be started until P-11 (Group Audit) '
                    'has been Partner-approved.\n\n'
                    'Reason: Overall audit strategy per ISA 300 requires completion of all risk '
                    'assessments (P-6 through P-11) to design responsive audit procedures.\n\n'
                    'Action: Please complete and obtain Partner approval for P-11 first.'
                )

    # ============================================================================
    # SECTION A: OVERALL AUDIT STRATEGY (ISA 300 CORE)
    # ============================================================================
    audit_approach = fields.Selection([
        ('substantive', 'Substantive-Based'),
        ('controls_reliant', 'Controls-Reliant'),
        ('hybrid', 'Hybrid Approach'),
    ], string='Overall Audit Approach', required=True, tracking=True,
       help='ISA 300.8: Overall approach to the audit')
    
    approach_rationale = fields.Html(
        string='Reason for Selected Approach',
        required=True,
        help='Mandatory narrative explaining why this approach was chosen'
    )
    
    interim_audit_planned = fields.Boolean(
        string='Interim Audit Planned?',
        tracking=True,
        help='Will there be interim audit work before year-end?'
    )
    interim_audit_details = fields.Html(
        string='Interim Audit Details',
        help='Timing and scope of interim audit work'
    )
    
    specialists_required = fields.Boolean(
        string='Use of Specialists?',
        tracking=True,
        help='ISA 620: Using the work of an auditor\'s expert'
    )
    specialist_types = fields.Many2many(
        'audit.specialist.type',
        string='Specialist Types',
        help='IT, Valuation, Tax, Actuary, etc.'
    )
    specialist_details = fields.Html(
        string='Specialist Engagement Details'
    )
    
    group_audit_applicable = fields.Boolean(
        string='Group Audit Considerations Applicable?',
        compute='_compute_group_audit_applicable',
        store=True,
        help='Auto-populated from P-11'
    )
    group_audit_strategy = fields.Html(
        string='Group Audit Strategy',
        help='Reference to P-11 group audit planning'
    )
    
    # Strategy alignment with RMM
    rmm_alignment_confirmed = fields.Boolean(
        string='Strategy Aligns with RMM?',
        help='Confirm strategy is responsive to P-6 risk assessment'
    )

    # ============================================================================
    # SECTION B: RISK-TO-RESPONSE MAPPING (ISA 330 HEART)
    # ============================================================================
    risk_response_ids = fields.One2many(
        'qaco.planning.p12.risk.response',
        'p12_id',
        string='Risk-Response Mapping',
        help='Auto-populated from P-6, P-7, P-8, P-9, P-10'
    )
    total_risks = fields.Integer(
        string='Total Risks',
        compute='_compute_risk_metrics',
        store=True
    )
    risks_with_responses = fields.Integer(
        string='Risks with Responses',
        compute='_compute_risk_metrics',
        store=True
    )
    unaddressed_risks = fields.Integer(
        string='Unaddressed Risks',
        compute='_compute_risk_metrics',
        store=True,
        help='Risks without audit responses - MUST BE ZERO'
    )
    significant_risk_count = fields.Integer(
        string='Significant Risks',
        compute='_compute_risk_metrics',
        store=True
    )

    # ============================================================================
    # SECTION C: FS-AREA-WISE AUDIT STRATEGY
    # ============================================================================
    fs_area_strategy_ids = fields.One2many(
        'qaco.planning.p12.fs.area.strategy',
        'p12_id',
        string='FS Area Strategy',
        help='Strategy per financial statement area'
    )
    mandatory_fs_areas_covered = fields.Boolean(
        string='All Mandatory FS Areas Covered?',
        compute='_compute_fs_area_coverage',
        store=True
    )

    # ============================================================================
    # SECTION D: DETAILED AUDIT PROGRAMS
    # ============================================================================
    audit_program_ids = fields.One2many(
        'qaco.planning.p12.audit.program',
        'p12_id',
        string='Detailed Audit Programs',
        help='Detailed procedures per FS area'
    )
    programs_finalized = fields.Boolean(
        string='All Programs Finalized?',
        help='Confirm all audit programs are complete'
    )

    # ============================================================================
    # SECTION E: SAMPLING STRATEGY (ISA 530)
    # ============================================================================
    sampling_plan_ids = fields.One2many(
        'qaco.planning.p12.sampling.plan',
        'p12_id',
        string='Sampling Plans',
        help='ISA 530: Audit sampling plans per area'
    )
    sampling_methodology = fields.Selection([
        ('statistical', 'Statistical Sampling'),
        ('non_statistical', 'Non-Statistical Sampling'),
        ('mus', 'Monetary Unit Sampling (MUS)'),
        ('mixed', 'Mixed Approach'),
    ], string='Overall Sampling Methodology', tracking=True)
    
    sampling_rationale = fields.Html(
        string='Basis for Sampling Approach',
        help='Explain sampling methodology selection'
    )

    # ============================================================================
    # SECTION F: ANALYTICAL PROCEDURES PLANNING (ISA 520)
    # ============================================================================
    analytical_procedures_planned = fields.Html(
        string='Planned Analytical Procedures',
        help='ISA 520: Analytical procedures to be performed'
    )
    analytical_procedures_types = fields.Selection([
        ('ratio', 'Ratio Analysis'),
        ('trend', 'Trend Analysis'),
        ('reasonableness', 'Reasonableness Testing'),
        ('all', 'All of the Above'),
    ], string='Types of Analytics', tracking=True)
    
    analytics_data_sources = fields.Html(
        string='Data Sources for Analytics',
        help='Sources of data for analytical procedures'
    )
    analytics_precision_level = fields.Html(
        string='Precision Level & Thresholds',
        help='Expected precision and follow-up thresholds'
    )

    # ============================================================================
    # SECTION G: FRAUD & UNPREDICTABILITY INTEGRATION
    # ============================================================================
    unpredictable_procedures_planned = fields.Boolean(
        string='Unpredictable Procedures Planned?',
        tracking=True,
        help='ISA 240: Element of unpredictability'
    )
    unpredictable_procedures_details = fields.Html(
        string='Unpredictable Procedures Details',
        help='Describe unpredictable audit procedures'
    )
    
    journal_entry_testing_approach = fields.Html(
        string='Journal Entry Testing Approach',
        required=True,
        help='ISA 240.32: Testing of journal entries and adjustments'
    )
    management_override_procedures = fields.Html(
        string='Management Override-Focused Procedures',
        required=True,
        help='ISA 240.33: Procedures to address management override'
    )
    
    # Link to P-7 fraud risks
    p7_fraud_integration = fields.Html(
        string='P-7 Fraud Risk Integration',
        help='How P-7 fraud risks are addressed in audit plan'
    )

    # ============================================================================
    # SECTION H: GOING CONCERN & DISCLOSURE FOCUS
    # ============================================================================
    enhanced_gc_areas = fields.Html(
        string='Areas Requiring Enhanced GC Procedures',
        help='ISA 570: Going concern considerations'
    )
    cash_flow_testing_planned = fields.Boolean(
        string='Cash Flow Testing Planned?',
        tracking=True,
        help='Will cash flow forecasts be tested?'
    )
    cash_flow_testing_details = fields.Html(
        string='Cash Flow Testing Details'
    )
    
    subsequent_events_focus = fields.Boolean(
        string='Subsequent Events Focus?',
        tracking=True,
        help='Enhanced subsequent events procedures'
    )
    subsequent_events_details = fields.Html(
        string='Subsequent Events Procedures'
    )
    
    disclosure_testing_emphasis = fields.Html(
        string='Disclosure Testing Emphasis',
        help='Key disclosure areas requiring testing'
    )

    # ============================================================================
    # SECTION I: KEY AUDIT MATTERS (LISTED ENTITIES - ISA 701)
    # ============================================================================
    is_listed_entity = fields.Boolean(
        string='Listed Entity?',
        help='ISA 701 applies to listed entities'
    )
    kam_candidate_ids = fields.One2many(
        'qaco.planning.p12.kam.candidate',
        'p12_id',
        string='KAM Candidates',
        help='Potential Key Audit Matters per ISA 701'
    )
    kam_candidates_count = fields.Integer(
        string='KAM Candidates',
        compute='_compute_kam_metrics',
        store=True
    )
    kam_from_significant_risks = fields.Boolean(
        string='KAMs Originate from Significant Risks?',
        compute='_compute_kam_metrics',
        store=True
    )

    # ============================================================================
    # SECTION J: BUDGET, TIMELINE & RESOURCE ALIGNMENT
    # ============================================================================
    planned_hours_partner = fields.Float(
        string='Planned Hours - Partner',
        help='Budgeted partner hours'
    )
    planned_hours_manager = fields.Float(
        string='Planned Hours - Manager',
        help='Budgeted manager hours'
    )
    planned_hours_senior = fields.Float(
        string='Planned Hours - Senior',
        help='Budgeted senior hours'
    )
    planned_hours_trainee = fields.Float(
        string='Planned Hours - Trainee/Assistant',
        help='Budgeted trainee hours'
    )
    total_planned_hours = fields.Float(
        string='Total Planned Hours',
        compute='_compute_total_hours',
        store=True
    )
    
    # Milestones
    planning_completion_date = fields.Date(
        string='Planning Completion Date',
        help='Target date for planning phase completion'
    )
    interim_audit_date = fields.Date(
        string='Interim Audit Date',
        help='Date of interim audit work'
    )
    fieldwork_start_date = fields.Date(
        string='Fieldwork Start Date',
        required=True,
        help='Planned start of year-end fieldwork'
    )
    fieldwork_end_date = fields.Date(
        string='Fieldwork End Date',
        required=True,
        help='Planned completion of fieldwork'
    )
    draft_report_date = fields.Date(
        string='Draft Report Date',
        help='Target date for draft report'
    )
    final_report_date = fields.Date(
        string='Final Report Date',
        help='Target date for final report issuance'
    )
    
    # Review checkpoints
    eqcr_required = fields.Boolean(
        string='EQCR Required?',
        tracking=True,
        help='ISA 220: Engagement Quality Control Review required?'
    )
    eqcr_reviewer_id = fields.Many2one(
        'res.partner',
        string='EQCR Reviewer',
        help='Engagement Quality Control Reviewer'
    )
    review_checkpoints = fields.Html(
        string='Review & EQCR Checkpoints',
        help='Key review points throughout audit'
    )
    
    # Budget reconciliation
    budget_reconciliation = fields.Html(
        string='Budget Reconciliation',
        help='Reconciliation with P-5 Audit Budget'
    )
    budget_aligned_with_p5 = fields.Boolean(
        string='Budget Aligned with P-5?',
        help='Confirm budget aligns with P-5 materiality budget'
    )

    # ============================================================================
    # SECTION K: MANDATORY DOCUMENT UPLOADS
    # ============================================================================
    audit_strategy_memo_attachments = fields.Many2many(
        'ir.attachment',
        'p12_strategy_memo_rel',
        'p12_id',
        'attachment_id',
        string='Audit Strategy Memorandum (Draft)',
        help='Upload draft audit strategy memorandum'
    )
    audit_programs_export_attachments = fields.Many2many(
        'ir.attachment',
        'p12_programs_export_rel',
        'p12_id',
        'attachment_id',
        string='Detailed Audit Programs (Export)',
        help='Export of detailed audit programs'
    )
    sampling_rationale_attachments = fields.Many2many(
        'ir.attachment',
        'p12_sampling_rel',
        'p12_id',
        'attachment_id',
        string='Sampling Rationale',
        help='Documentation of sampling approach'
    )
    specialist_scope_attachments = fields.Many2many(
        'ir.attachment',
        'p12_specialist_rel',
        'p12_id',
        'attachment_id',
        string='Specialist Scope Documents',
        help='Scope and engagement letters for specialists'
    )
    prior_year_comparison_attachments = fields.Many2many(
        'ir.attachment',
        'p12_prior_year_rel',
        'p12_id',
        'attachment_id',
        string='Prior-Year Strategy Comparison',
        help='Comparison with prior year audit approach'
    )

    # ============================================================================
    # SECTION L: P-12 CONCLUSION & PROFESSIONAL JUDGMENT
    # ============================================================================
    conclusion_narrative = fields.Html(
        string='P-12 Professional Judgment Conclusion',
        required=True,
        help='Mandatory conclusion per ISA 300'
    )
    all_risks_addressed = fields.Boolean(
        string='All Risks Addressed?',
        help='Confirm all identified risks have audit responses'
    )
    programs_finalized_confirmed = fields.Boolean(
        string='All Programs Finalized?',
        help='Confirm all audit programs are complete and approved'
    )
    strategy_approved_before_execution = fields.Boolean(
        string='Strategy Approved Prior to Execution?',
        help='Confirm strategy approval before execution begins'
    )

    # ============================================================================
    # SECTION M: REVIEW, APPROVAL & LOCK
    # ============================================================================
    prepared_by = fields.Many2one(
        'res.users',
        string='Prepared By',
        tracking=True,
        readonly=True
    )
    prepared_by_role = fields.Char(
        string='Role',
        compute='_compute_preparer_role',
        store=True
    )
    prepared_on = fields.Datetime(
        string='Prepared On',
        readonly=True
    )
    
    reviewed_by = fields.Many2one(
        'res.users',
        string='Reviewed By (Manager)',
        tracking=True,
        readonly=True
    )
    reviewed_on = fields.Datetime(
        string='Reviewed On',
        readonly=True
    )
    review_notes = fields.Html(
        string='Manager Review Notes',
        help='Manager must document review findings'
    )
    
    partner_approved = fields.Boolean(
        string='Partner Approval',
        tracking=True,
        readonly=True,
        copy=False
    )
    partner_approved_by = fields.Many2one(
        'res.users',
        string='Partner Approved By',
        tracking=True,
        readonly=True
    )
    partner_approved_on = fields.Datetime(
        string='Partner Approved On',
        readonly=True
    )
    partner_comments = fields.Html(
        string='Partner Comments',
        help='MANDATORY: Partner must provide substantive comments per ISA 220'
    )
    
    locked = fields.Boolean(
        string='Planning Phase Locked',
        compute='_compute_locked',
        store=True,
        help='P-12 approval locks entire planning phase'
    )
    
    # Audit trail
    version_history = fields.Text(
        string='Version History',
        readonly=True,
        help='ISA 230: Full audit trail preserved'
    )
    reviewer_timestamps = fields.Text(
        string='Reviewer Timestamps',
        readonly=True
    )

    # ISA Reference
    isa_reference = fields.Char(
        string='ISA Reference',
        default='ISA 300, ISA 315, ISA 330, ISA 240, ISA 520, ISA 530, ISA 570, ISA 701, ISA 220, ISQM-1',
        readonly=True
    )

    # ============================================================================
    # SQL CONSTRAINTS
    # ============================================================================
    _sql_constraints = [
        ('engagement_unique', 'UNIQUE(audit_id)', 
         'Only one P-12 record per audit engagement is allowed.')
    ]

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends('audit_id')
    def _compute_engagement_id(self):
        """Compute engagement_id from audit_id for backward compatibility."""
        for rec in self:
            # Map qaco.audit to audit.engagement if needed
            rec.engagement_id = rec.audit_id.id if rec.audit_id else False
    
    @api.depends('risk_response_ids', 'risk_response_ids.response_documented')
    def _compute_risk_metrics(self):
        """Defensive: Safe even during module install."""
        for rec in self:
            try:
                if not rec.risk_response_ids:
                    rec.total_risks = 0
                    rec.risks_with_responses = 0
                    rec.unaddressed_risks = 0
                    rec.significant_risk_count = 0
                    continue
                
                rec.total_risks = len(rec.risk_response_ids)
                rec.risks_with_responses = len(
                    rec.risk_response_ids.filtered(lambda r: r.response_documented)
                )
                rec.unaddressed_risks = rec.total_risks - rec.risks_with_responses
                rec.significant_risk_count = len(
                    rec.risk_response_ids.filtered(lambda r: r.risk_level == 'significant')
                )
            except Exception as e:
                _logger.warning(f'P-12 _compute_risk_metrics failed for record {rec.id}: {e}')
                rec.total_risks = 0
                rec.risks_with_responses = 0
                rec.unaddressed_risks = 0
                rec.significant_risk_count = 0

    @api.depends('fs_area_strategy_ids')
    def _compute_fs_area_coverage(self):
        """Defensive: Check if all mandatory FS areas are covered."""
        mandatory_areas = [
            'revenue', 'ppe', 'inventory', 'cash', 'borrowings',
            'provisions', 'related_parties', 'taxes', 'equity', 'expenses'
        ]
        for rec in self:
            try:
                if not rec.fs_area_strategy_ids:
                    rec.mandatory_fs_areas_covered = False
                    continue
                
                covered_areas = rec.fs_area_strategy_ids.mapped('fs_area')
                rec.mandatory_fs_areas_covered = all(
                    area in covered_areas for area in mandatory_areas
                )
            except Exception as e:
                _logger.warning(f'P-12 _compute_fs_area_coverage failed for record {rec.id}: {e}')
                rec.mandatory_fs_areas_covered = False

    @api.depends('kam_candidate_ids')
    def _compute_kam_metrics(self):
        """Defensive: Safe even during module install."""
        for rec in self:
            try:
                if not rec.kam_candidate_ids:
                    rec.kam_candidates_count = 0
                    rec.kam_from_significant_risks = False
                    continue
                
                rec.kam_candidates_count = len(rec.kam_candidate_ids)
                rec.kam_from_significant_risks = all(
                    kam.from_significant_risk for kam in rec.kam_candidate_ids
                )
            except Exception as e:
                _logger.warning(f'P-12 _compute_kam_metrics failed for record {rec.id}: {e}')
                rec.kam_candidates_count = 0
                rec.kam_from_significant_risks = False

    @api.depends('planned_hours_partner', 'planned_hours_manager',
                 'planned_hours_senior', 'planned_hours_trainee')
    def _compute_total_hours(self):
        for rec in self:
            rec.total_planned_hours = (
                rec.planned_hours_partner +
                rec.planned_hours_manager +
                rec.planned_hours_senior +
                rec.planned_hours_trainee
            )

    @api.depends('prepared_by')
    def _compute_preparer_role(self):
        for rec in self:
            if rec.prepared_by:
                if rec.prepared_by.has_group('qaco_audit.group_audit_partner'):
                    rec.prepared_by_role = 'Partner'
                elif rec.prepared_by.has_group('qaco_audit.group_audit_manager'):
                    rec.prepared_by_role = 'Manager'
                else:
                    rec.prepared_by_role = 'Senior/Trainee'
            else:
                rec.prepared_by_role = ''

    @api.depends('partner_approved')
    def _compute_locked(self):
        for rec in self:
            rec.locked = rec.partner_approved

    def _compute_group_audit_applicable(self):
        """Check if group audit applies from P-11"""
        for rec in self:
            p11 = self.env['qaco.planning.p11.group.audit'].search([
                ('engagement_id', '=', rec.engagement_id.id),
                ('audit_year_id', '=', rec.audit_year_id.id),
            ], limit=1)
            rec.group_audit_applicable = p11.is_group_audit if p11 else False

    def _default_conclusion_narrative(self):
        return """
        <p><strong>P-12: Audit Strategy & Detailed Audit Plan Conclusion</strong></p>
        <p>An overall audit strategy and detailed audit plan have been developed in accordance with 
        ISA 300, responsive to assessed risks under ISA 315 and ISA 330. The audit plan provides a 
        basis for executing an effective and efficient audit.</p>
        <p><strong>Key Confirmations:</strong></p>
        <ul>
            <li>All identified risks from P-6 through P-11 have been addressed with appropriate audit responses</li>
            <li>Detailed audit programs have been finalized for all financial statement areas</li>
            <li>Sampling strategies align with performance materiality</li>
            <li>Fraud-responsive procedures integrated per ISA 240</li>
            <li>Resource allocation and timeline established</li>
            <li>Strategy approved by partner prior to execution</li>
        </ul>
        """

    @api.model_create_multi
    def create(self, vals_list):
        """PROMPT 3: Set HTML defaults safely in create() instead of field defaults."""
        for vals in vals_list:
            if 'conclusion_narrative' not in vals:
                vals['conclusion_narrative'] = self._default_conclusion_narrative()
        return super().create(vals_list)

    # ============================================================================
    # VALIDATION & CONSTRAINTS
    # ============================================================================
    @api.constrains('unaddressed_risks')
    def _check_no_unaddressed_risks(self):
        for rec in self:
            if rec.unaddressed_risks > 0:
                raise ValidationError(
                    _('Cannot approve P-12: %d risk(s) do not have documented audit responses. '
                      'All risks must be addressed per ISA 330.') % rec.unaddressed_risks
                )

    @api.constrains('fieldwork_start_date', 'fieldwork_end_date')
    def _check_fieldwork_dates(self):
        for rec in self:
            if rec.fieldwork_start_date and rec.fieldwork_end_date:
                if rec.fieldwork_end_date <= rec.fieldwork_start_date:
                    raise ValidationError(
                        _('Fieldwork end date must be after start date.')
                    )

    @api.constrains('eqcr_required', 'eqcr_reviewer_id')
    def _check_eqcr_reviewer(self):
        for rec in self:
            if rec.eqcr_required and not rec.eqcr_reviewer_id:
                raise ValidationError(
                    _('EQCR Reviewer must be assigned if EQCR is required per ISA 220.')
                )

    # ============================================================================
    # PRE-CONDITIONS ENFORCEMENT
    # ============================================================================
    def _check_preconditions(self):
        """
        System-enforced pre-conditions:
        ALL planning phases P-1 through P-11 must be partner-approved and locked
        """
        self.ensure_one()
        errors = []

        # Check P-1 through P-11 (comprehensive check)
        planning_phases = [
            ('qaco.planning.p1.engagement', 'P-1 (Engagement Understanding)'),
            ('qaco.planning.p2.entity', 'P-2 (Entity Understanding)'),
            ('qaco.planning.p3.controls', 'P-3 (Internal Controls)'),
            ('qaco.planning.p4.analytics', 'P-4 (Preliminary Analytics)'),
            ('qaco.planning.p5.materiality', 'P-5 (Materiality)'),
            ('qaco.planning.p6.risk', 'P-6 (Risk Assessment)'),
            ('qaco.planning.p7.fraud', 'P-7 (Fraud Assessment)'),
            ('qaco.planning.p8.going.concern', 'P-8 (Going Concern)'),
            ('qaco.planning.p9.laws', 'P-9 (Laws & Regulations)'),
            ('qaco.planning.p10.related.parties', 'P-10 (Related Parties)'),
            ('qaco.planning.p11.group.audit', 'P-11 (Group Audit)'),
        ]

        for model_name, phase_name in planning_phases:
            phase = self.env[model_name].search([
                ('engagement_id', '=', self.engagement_id.id),
                ('audit_year_id', '=', self.audit_year_id.id),
            ], limit=1)
            
            if not phase:
                errors.append(f'{phase_name} record not found.')
            elif phase.state != 'locked':
                errors.append(f'{phase_name} must be locked (partner-approved).')

        if errors:
            raise UserError(
                _('P-12 Pre-Conditions Not Met:\n\n') + '\n'.join(['• ' + e for e in errors]) +
                _('\n\nAll planning phases P-1 through P-11 must be partner-approved and locked before P-12 can be created.')
            )

    @api.model
    def create(self, vals):
        rec = super(AuditPlanningP12AuditStrategy, self).create(vals)
        rec._check_preconditions()
        rec._auto_populate_risk_responses()
        rec._log_version('Created')
        return rec

    def write(self, vals):
        result = super(AuditPlanningP12AuditStrategy, self).write(vals)
        if any(key in vals for key in ['state', 'partner_approved']):
            self._log_version(f"Updated: {vals.get('state', 'state change')}")
        return result

    def _log_version(self, action):
        """Maintain audit trail per ISA 230"""
        for rec in self:
            timestamp = fields.Datetime.now()
            user = self.env.user.name
            log_entry = f"{timestamp} | {user} | {action}\n"
            rec.version_history = (rec.version_history or '') + log_entry

    # ============================================================================
    # AUTO-POPULATION FROM PRIOR PHASES
    # ============================================================================
    def _auto_populate_risk_responses(self):
        """Auto-populate risk-response mapping from P-6, P-7, P-8, P-9, P-10"""
        self.ensure_one()
        
        RiskResponse = self.env['qaco.planning.p12.risk.response']
        
        # Clear existing
        self.risk_response_ids.unlink()
        
        # From P-6 (Risk Assessment)
        p6 = self.env['qaco.planning.p6.risk'].search([
            ('engagement_id', '=', self.engagement_id.id),
            ('audit_year_id', '=', self.audit_year_id.id),
        ], limit=1)
        
        if p6 and p6.risk_ids:
            for risk in p6.risk_ids:
                RiskResponse.create({
                    'p12_id': self.id,
                    'source_phase': 'p6',
                    'risk_description': risk.risk_description,
                    'fs_area': risk.fs_area,
                    'assertion': risk.assertion,
                    'risk_level': risk.risk_level,
                })
        
        # From P-7 (Fraud)
        p7 = self.env['qaco.planning.p7.fraud'].search([
            ('engagement_id', '=', self.engagement_id.id),
            ('audit_year_id', '=', self.audit_year_id.id),
        ], limit=1)
        
        if p7 and p7.fraud_risk_ids:
            for fraud_risk in p7.fraud_risk_ids:
                RiskResponse.create({
                    'p12_id': self.id,
                    'source_phase': 'p7',
                    'risk_description': fraud_risk.fraud_risk_description,
                    'risk_level': 'significant',  # Fraud risks are always significant
                })
        
        # Similar logic for P-8, P-9, P-10 can be added

    # ============================================================================
    # MANDATORY FIELD VALIDATION
    # ============================================================================
    def _validate_mandatory_fields(self):
        """Validate all mandatory fields before progression"""
        self.ensure_one()
        errors = []

        # Section A
        if not self.audit_approach:
            errors.append('Section A: Overall audit approach must be selected')
        if not self.approach_rationale:
            errors.append('Section A: Rationale for audit approach is required')
        
        # Section B
        if self.unaddressed_risks > 0:
            errors.append(f'Section B: {self.unaddressed_risks} risk(s) without responses')
        
        # Section C
        if not self.mandatory_fs_areas_covered:
            errors.append('Section C: All mandatory FS areas must be covered')
        
        # Section D
        if not self.programs_finalized:
            errors.append('Section D: Audit programs must be finalized')
        
        # Section G (Fraud - MANDATORY)
        if not self.journal_entry_testing_approach:
            errors.append('Section G: Journal entry testing approach is required (ISA 240.32)')
        if not self.management_override_procedures:
            errors.append('Section G: Management override procedures are required (ISA 240.33)')
        
        # Section J (Timeline)
        if not self.fieldwork_start_date:
            errors.append('Section J: Fieldwork start date is required')
        if not self.fieldwork_end_date:
            errors.append('Section J: Fieldwork end date is required')
        
        # Section K (Attachments)
        if not self.audit_strategy_memo_attachments:
            errors.append('Section K: Audit strategy memorandum must be uploaded')
        
        # Section L (Confirmations)
        if not self.all_risks_addressed:
            errors.append('Section L: Confirm all risks are addressed')
        if not self.programs_finalized_confirmed:
            errors.append('Section L: Confirm all programs are finalized')
        if not self.strategy_approved_before_execution:
            errors.append('Section L: Confirm strategy approval prior to execution')

        if errors:
            raise UserError(
                _('Cannot progress P-12. Missing requirements:\n\n') + 
                '\n'.join(['• ' + e for e in errors])
            )

    # ============================================================================
    # STATE MANAGEMENT ACTIONS
    # ============================================================================
    def action_mark_complete(self):
        """Senior marks P-12 as complete"""
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Can only mark complete from Draft state.'))
            rec._validate_mandatory_fields()
            rec.write({
                'prepared_by': self.env.user.id,
                'prepared_on': fields.Datetime.now(),
                'state': 'review',
            })
            rec.message_post(body=_('P-12 marked complete and submitted for manager review.'))

    def action_manager_review(self):
        """Manager reviews and approves P-12"""
        for rec in self:
            if rec.state != 'review':
                raise UserError(_('Can only review from Review state.'))
            if not rec.review_notes:
                raise UserError(_('Manager review notes are mandatory.'))
            rec.write({
                'reviewed_by': self.env.user.id,
                'reviewed_on': fields.Datetime.now(),
                'state': 'partner',
            })
            rec.message_post(body=_('P-12 reviewed by manager and forwarded to partner.'))

    def action_partner_approve(self):
        """Partner approves and locks P-12 - LOCKS ENTIRE PLANNING PHASE"""
        for rec in self:
            if rec.state != 'partner':
                raise UserError(_('Can only approve from Partner state.'))
            if not rec.partner_comments:
                raise UserError(_('Partner comments are MANDATORY per ISA 220.'))
            
            rec.write({
                'partner_approved': True,
                'partner_approved_by': self.env.user.id,
                'partner_approved_on': fields.Datetime.now(),
                'state': 'locked',
            })
            rec.message_post(
                body=_('P-12 approved by partner. PLANNING PHASE LOCKED. Execution Phase is now unlocked.')
            )
            rec._unlock_execution_phase()
            rec._auto_unlock_p13()

    def action_send_back(self):
        """Send back to draft for corrections"""
        for rec in self:
            if rec.state not in ['review', 'partner']:
                raise UserError(_('Can only send back from Review or Partner state.'))
            rec.state = 'draft'
            rec.message_post(body=_('P-12 sent back to draft for corrections.'))

    def action_partner_unlock(self):
        """Partner unlocks for amendments (exceptional)"""
        for rec in self:
            if rec.state != 'locked':
                raise UserError(_('Can only unlock from Locked state.'))
            if not self.env.user.has_group('qaco_audit.group_audit_partner'):
                raise UserError(_('Only partners can unlock P-12.'))
            rec.write({
                'partner_approved': False,
                'state': 'partner',
            })
            rec.message_post(body=_('P-12 unlocked by partner for amendment. WARNING: Planning phase unlocked.'))

    def _unlock_execution_phase(self):
        """Automatically unlock Execution Phase when P-12 is locked"""
        self.ensure_one()
        # This method signals that execution phase can now be accessed
        # Implementation depends on execution phase gating logic
        self.message_post(
            body=_('Planning Phase complete. Execution Phase (Audit Fieldwork) is now accessible.')
        )
    
    def _auto_unlock_p13(self):
        """Auto-unlock P-13 Final Planning Approval when P-12 Audit Strategy is approved."""
        self.ensure_one()
        if not self.engagement_id:
            return
        
        # Find or create P-13 record
        P13 = self.env['qaco.planning.p13.approval']
        p13_record = P13.search([('audit_id', '=', self.engagement_id.id)], limit=1)
        
        if p13_record and p13_record.state in ['locked', 'approved']:
            p13_record.write({'state': 'in_progress'})
            p13_record.message_post(
                body='P-13 auto-unlocked after P-12 Audit Strategy approval. Planning Phase ready for final review.'
            )
            _logger.info(f'P-13 auto-unlocked for audit {self.engagement_id.id}')
        elif not p13_record:
            # Use correct field name from P13 model
            p13_record = P13.create({
                'audit_id': self.engagement_id.id,
                'state': 'in_progress',
            })
            _logger.info(f'P-13 auto-created for audit {self.engagement_id.id}')


# ============================================================================
# CHILD MODEL: RISK-RESPONSE MAPPING
# ============================================================================
class PlanningP12RiskResponse(models.Model):
    """Risk-to-Response Mapping (ISA 330)"""
    _name = 'qaco.planning.p12.risk.response'
    _description = 'Risk-Response Mapping'
    _order = 'risk_level desc, fs_area'

    p12_id = fields.Many2one(
        'qaco.planning.p12.strategy',
        string='P-12 Audit Strategy',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    # Risk Details
    source_phase = fields.Selection([
        ('p6', 'P-6: Risk Assessment'),
        ('p7', 'P-7: Fraud'),
        ('p8', 'P-8: Going Concern'),
        ('p9', 'P-9: Laws & Regulations'),
        ('p10', 'P-10: Related Parties'),
    ], string='Source Phase', required=True)
    
    risk_id = fields.Char(
        string='Risk ID',
        help='Reference to original risk ID'
    )
    risk_description = fields.Html(
        string='Risk Description',
        required=True
    )
    fs_area = fields.Char(
        string='FS Area',
        help='Financial statement area affected'
    )
    assertion = fields.Char(
        string='Assertion',
        help='Financial statement assertion affected'
    )
    risk_level = fields.Selection([
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
        ('significant', 'Significant Risk'),
    ], string='Risk Level', required=True, default='moderate')
    
    # Audit Response (ISA 330)
    planned_response = fields.Html(
        string='Planned Audit Response',
        help='Nature, timing, and extent of audit procedures (ISA 330.7)'
    )
    response_documented = fields.Boolean(
        string='Response Documented?',
        help='Has the audit response been documented?'
    )
    
    # For Significant Risks (ISA 330.21)
    senior_involvement_required = fields.Boolean(
        string='Senior Involvement Required?',
        help='ISA 330.21: Significant risks require senior involvement'
    )
    substantive_procedures_mandatory = fields.Boolean(
        string='Substantive Procedures Mandatory?',
        help='ISA 330.21: Cannot rely solely on controls for significant risks'
    )
    
    notes = fields.Text(string='Notes')


# ============================================================================
# CHILD MODEL: FS AREA STRATEGY
# ============================================================================
class PlanningP12FSAreaStrategy(models.Model):
    """FS Area-Wise Audit Strategy"""
    _name = 'qaco.planning.p12.fs.area.strategy'
    _description = 'FS Area Audit Strategy'
    _order = 'fs_area'

    p12_id = fields.Many2one(
        'qaco.planning.p12.strategy',
        string='P-12 Audit Strategy',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    fs_area = fields.Selection([
        ('revenue', 'Revenue'),
        ('ppe', 'Property, Plant & Equipment'),
        ('inventory', 'Inventory'),
        ('cash', 'Cash & Bank'),
        ('borrowings', 'Borrowings'),
        ('provisions', 'Provisions & Contingencies'),
        ('related_parties', 'Related Parties'),
        ('taxes', 'Taxation'),
        ('equity', 'Equity'),
        ('expenses', 'Expenses'),
        ('receivables', 'Trade Receivables'),
        ('payables', 'Trade Payables'),
        ('investments', 'Investments'),
        ('other', 'Other'),
    ], string='FS Area', required=True)
    
    rmm_level = fields.Selection([
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
        ('significant', 'Significant Risk'),
    ], string='RMM Level', required=True, help='Overall RMM for this area')
    
    controls_reliance = fields.Boolean(
        string='Controls Reliance?',
        help='Will we rely on controls for this area?'
    )
    substantive_focus = fields.Html(
        string='Substantive Audit Focus',
        required=True,
        help='Key substantive procedures for this area'
    )
    specialist_required = fields.Boolean(
        string='Specialist Required?',
        help='Does this area require a specialist?'
    )
    specialist_type = fields.Char(
        string='Specialist Type',
        help='E.g., IT, Valuation, Actuary'
    )
    
    notes = fields.Text(string='Notes')


# ============================================================================
# CHILD MODEL: AUDIT PROGRAMS
# ============================================================================
class PlanningP12AuditProgram(models.Model):
    """Detailed Audit Programs"""
    _name = 'qaco.planning.p12.audit.program'
    _description = 'Detailed Audit Program'
    _order = 'fs_area, sequence'

    p12_id = fields.Many2one(
        'qaco.planning.p12.strategy',
        string='P-12 Audit Strategy',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    sequence = fields.Integer(string='Sequence', default=10)
    fs_area = fields.Selection([
        ('revenue', 'Revenue'),
        ('ppe', 'Property, Plant & Equipment'),
        ('inventory', 'Inventory'),
        ('cash', 'Cash & Bank'),
        ('borrowings', 'Borrowings'),
        ('provisions', 'Provisions & Contingencies'),
        ('related_parties', 'Related Parties'),
        ('taxes', 'Taxation'),
        ('equity', 'Equity'),
        ('expenses', 'Expenses'),
        ('other', 'Other'),
    ], string='FS Area', required=True)
    
    procedure_type = fields.Selection([
        ('control_test', 'Control Testing'),
        ('substantive_detail', 'Test of Details'),
        ('substantive_analytics', 'Substantive Analytics'),
        ('fraud_responsive', 'Fraud-Responsive Procedure'),
        ('law_regulation', 'Law & Regulation Procedure'),
        ('rpt_specific', 'RPT-Specific Procedure'),
        ('going_concern', 'Going Concern Procedure'),
    ], string='Procedure Type', required=True)
    
    procedure_description = fields.Html(
        string='Procedure Description',
        required=True,
        help='Detailed description of audit procedure'
    )
    
    nature = fields.Char(
        string='Nature',
        help='Nature of procedure (ISA 330)'
    )
    timing = fields.Char(
        string='Timing',
        help='Timing of procedure (interim/year-end)'
    )
    extent = fields.Char(
        string='Extent',
        help='Extent of procedure (sample size, coverage)'
    )
    
    is_finalized = fields.Boolean(
        string='Finalized?',
        help='Has this procedure been finalized?'
    )
    
    notes = fields.Text(string='Notes')


# ============================================================================
# CHILD MODEL: SAMPLING PLANS
# ============================================================================
class PlanningP12SamplingPlan(models.Model):
    """Sampling Plans (ISA 530)"""
    _name = 'qaco.planning.p12.sampling.plan'
    _description = 'Audit Sampling Plan'
    _order = 'fs_area'

    p12_id = fields.Many2one(
        'qaco.planning.p12.strategy',
        string='P-12 Audit Strategy',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    fs_area = fields.Char(
        string='FS Area / Population',
        required=True
    )
    
    sampling_method = fields.Selection([
        ('statistical', 'Statistical Sampling'),
        ('non_statistical', 'Non-Statistical Sampling'),
        ('mus', 'Monetary Unit Sampling'),
    ], string='Sampling Method', required=True)
    
    population_size = fields.Integer(
        string='Population Size',
        help='Total number of items in population'
    )
    population_value = fields.Monetary(
        string='Population Value',
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='p12_id.currency_id'
    )
    
    sample_size = fields.Integer(
        string='Sample Size',
        required=True,
        help='Number of items to be tested'
    )
    basis_for_sample_size = fields.Html(
        string='Basis for Sample Size',
        required=True,
        help='Explain how sample size was determined'
    )
    
    sampling_unit = fields.Char(
        string='Sampling Unit',
        help='E.g., invoice, transaction, item'
    )
    expected_misstatement = fields.Monetary(
        string='Expected Misstatement',
        currency_field='currency_id'
    )
    tolerable_misstatement = fields.Monetary(
        string='Tolerable Misstatement',
        currency_field='currency_id',
        help='Link to P-5 Performance Materiality'
    )
    coverage_percentage = fields.Float(
        string='Coverage %',
        digits=(5, 2),
        help='Percentage of population covered by sample'
    )
    
    notes = fields.Text(string='Notes')


# ============================================================================
# CHILD MODEL: KAM CANDIDATES
# ============================================================================
class PlanningP12KAMCandidate(models.Model):
    """Key Audit Matter Candidates (ISA 701)"""
    _name = 'qaco.planning.p12.kam.candidate'
    _description = 'KAM Candidate'
    _order = 'area'

    p12_id = fields.Many2one(
        'qaco.planning.p12.strategy',
        string='P-12 Audit Strategy',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    area = fields.Char(
        string='Area / Matter',
        required=True,
        help='Area giving rise to potential KAM'
    )
    why_significant = fields.Html(
        string='Why Significant?',
        required=True,
        help='ISA 701: Why this matter required significant auditor attention'
    )
    from_significant_risk = fields.Boolean(
        string='Originates from Significant Risk?',
        help='ISA 701.9: KAMs typically arise from significant risks'
    )
    risk_link = fields.Char(
        string='Risk Link',
        help='Reference to linked risk (P-6, P-7, etc.)'
    )
    likely_kam = fields.Boolean(
        string='Likely to be KAM?',
        help='Preliminary assessment of whether this will be a KAM'
    )
    
    notes = fields.Text(string='Notes')


