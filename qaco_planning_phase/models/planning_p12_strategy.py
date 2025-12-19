# -*- coding: utf-8 -*-
"""
P-12: Audit Strategy & Audit Plan
Standard: ISA 300
Purpose: Consolidate planning outputs into execution strategy.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError


class PlanningP12Strategy(models.Model):
    """P-12: Audit Strategy & Audit Plan (ISA 300)"""
    _name = 'qaco.planning.p12.strategy'
    _description = 'P-12: Audit Strategy & Audit Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    TAB_STATE = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
    ]

    state = fields.Selection(
        TAB_STATE,
        string='Status',
        default='not_started',
        tracking=True,
        copy=False,
    )

    name = fields.Char(
        string='Reference',
        compute='_compute_name',
        store=True,
        readonly=True
    )
    audit_id = fields.Many2one(
        'qaco.audit',
        string='Audit Engagement',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    planning_main_id = fields.Many2one(
        'qaco.planning.main',
        string='Planning Phase',
        ondelete='cascade'
    )
    client_id = fields.Many2one(
        'res.partner',
        string='Client Name',
        related='audit_id.client_id',
        readonly=True,
        store=True
    )

    # ===== Overall Audit Strategy (ISA 300.7) =====
    overall_strategy = fields.Html(
        string='Overall Audit Strategy',
        help='The scope, timing and direction of the audit per ISA 300.7'
    )
    scope_of_audit = fields.Html(
        string='Scope of Audit',
        help='Define the scope of the audit engagement'
    )
    timing_of_audit = fields.Html(
        string='Timing of Audit',
        help='Key dates and timing considerations'
    )
    direction_of_audit = fields.Html(
        string='Direction of Audit',
        help='Key areas of audit focus and approach'
    )

    # ===== Planned Reliance on Controls =====
    controls_reliance = fields.Selection([
        ('substantive_only', 'Substantive Only - No Controls Reliance'),
        ('limited_reliance', 'Limited Reliance on Controls'),
        ('significant_reliance', 'Significant Reliance on Controls'),
    ], string='Planned Controls Reliance', tracking=True)
    controls_reliance_rationale = fields.Html(
        string='Controls Reliance Rationale'
    )
    controls_to_test = fields.Html(
        string='Controls Identified for Testing',
        help='Key controls where reliance is planned'
    )

    # ===== Nature, Timing & Extent of Procedures (ISA 330) =====
    nature_of_procedures = fields.Html(
        string='Nature of Procedures',
        help='Type of audit procedures to be performed'
    )
    timing_of_procedures = fields.Html(
        string='Timing of Procedures',
        help='When procedures will be performed (interim vs year-end)'
    )
    extent_of_procedures = fields.Html(
        string='Extent of Procedures',
        help='Sample sizes and coverage'
    )

    # ===== Sampling Approach =====
    sampling_approach = fields.Html(
        string='Sampling Approach',
        help='Overall approach to audit sampling per ISA 530'
    )
    statistical_sampling = fields.Boolean(
        string='Statistical Sampling Planned'
    )
    sampling_methodology = fields.Html(
        string='Sampling Methodology'
    )
    sample_size_factors = fields.Html(
        string='Sample Size Factors'
    )

    # ===== Use of Experts (ISA 620) =====
    experts_required = fields.Boolean(
        string='Experts Required',
        tracking=True
    )
    expert_line_ids = fields.One2many(
        'qaco.planning.p12.expert.line',
        'p12_strategy_id',
        string='Experts to Use'
    )
    experts_scope = fields.Html(
        string='Scope of Expert Work',
        help='Scope of work for auditor\'s experts per ISA 620'
    )

    # ===== Internal Audit Reliance (ISA 610) =====
    internal_audit_reliance = fields.Boolean(
        string='Reliance on Internal Audit Planned',
        tracking=True
    )
    internal_audit_assessment = fields.Html(
        string='Internal Audit Assessment',
        help='Assessment of objectivity and competence per ISA 610'
    )
    internal_audit_areas = fields.Html(
        string='Areas for Internal Audit Reliance'
    )

    # ===== CAATs / Data Analytics =====
    caats_planned = fields.Boolean(
        string='CAATs/Data Analytics Planned',
        tracking=True
    )
    caats_scope = fields.Html(
        string='CAATs Scope',
        help='Planned computer-assisted audit techniques'
    )
    data_analytics_procedures = fields.Html(
        string='Data Analytics Procedures'
    )

    # ===== Key Audit Areas =====
    key_audit_areas = fields.Html(
        string='Key Audit Areas',
        help='Areas requiring significant audit attention'
    )
    significant_risks_response = fields.Html(
        string='Response to Significant Risks',
        help='Specific responses to identified significant risks per ISA 330.21'
    )

    # ===== Audit Team & Resources =====
    staffing_plan = fields.Html(
        string='Staffing Plan',
        help='Team composition and responsibilities'
    )
    supervision_approach = fields.Html(
        string='Supervision Approach',
        help='How team will be directed and supervised per ISA 220'
    )
    specialist_resources = fields.Html(
        string='Specialist Resources Required'
    )

    # ===== Audit Timeline =====
    planning_completion_date = fields.Date(
        string='Planning Completion Date'
    )
    interim_fieldwork_start = fields.Date(
        string='Interim Fieldwork Start'
    )
    interim_fieldwork_end = fields.Date(
        string='Interim Fieldwork End'
    )
    final_fieldwork_start = fields.Date(
        string='Final Fieldwork Start'
    )
    final_fieldwork_end = fields.Date(
        string='Final Fieldwork End'
    )
    reporting_deadline = fields.Date(
        string='Reporting Deadline'
    )
    detailed_timeline = fields.Html(
        string='Detailed Audit Timeline'
    )

    # ===== Budget =====
    budget_hours = fields.Float(
        string='Total Budget Hours'
    )
    budget_amount = fields.Monetary(
        string='Budget Amount',
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    budget_breakdown = fields.Html(
        string='Budget Breakdown',
        help='Hours/costs by area or team member'
    )

    # ===== Communication =====
    management_communication = fields.Html(
        string='Planned Management Communication'
    )
    tcwg_communication = fields.Html(
        string='Planned TCWG Communication',
        help='Matters to be communicated per ISA 260'
    )

    # ===== Attachments =====
    audit_strategy_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p12_audit_strategy_rel',
        'p12_id',
        'attachment_id',
        string='Audit Strategy Document'
    )
    audit_plan_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p12_audit_plan_rel',
        'p12_id',
        'attachment_id',
        string='Audit Plan'
    )
    timeline_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p12_timeline_rel',
        'p12_id',
        'attachment_id',
        string='Timeline/Gantt Chart'
    )

    # ===== Summary =====
    strategy_summary = fields.Html(
        string='Audit Strategy Summary',
        help='Consolidated audit strategy per ISA 300'
    )
    isa_reference = fields.Char(
        string='ISA Reference',
        default='ISA 300/330',
        readonly=True
    )

    # ===== Sign-off Fields =====
    senior_signed_user_id = fields.Many2one('res.users', string='Senior Completed By', tracking=True, copy=False, readonly=True)
    senior_signed_on = fields.Datetime(string='Senior Completed On', tracking=True, copy=False, readonly=True)
    manager_reviewed_user_id = fields.Many2one('res.users', string='Manager Reviewed By', tracking=True, copy=False, readonly=True)
    manager_reviewed_on = fields.Datetime(string='Manager Reviewed On', tracking=True, copy=False, readonly=True)
    partner_approved_user_id = fields.Many2one('res.users', string='Partner Approved By', tracking=True, copy=False, readonly=True)
    partner_approved_on = fields.Datetime(string='Partner Approved On', tracking=True, copy=False, readonly=True)
    reviewer_notes = fields.Html(string='Reviewer Notes')
    approval_notes = fields.Html(string='Approval Notes')

    _sql_constraints = [
        ('audit_unique', 'UNIQUE(audit_id)', 'Only one P-12 record per Audit Engagement is allowed.')
    ]

    @api.depends('audit_id', 'client_id')
    def _compute_name(self):
        for record in self:
            if record.client_id:
                record.name = f"P12-{record.client_id.name[:15]}"
            else:
                record.name = 'P-12: Audit Strategy'

    def _validate_mandatory_fields(self):
        """Validate mandatory fields before completing P-12."""
        self.ensure_one()
        errors = []
        if not self.overall_strategy:
            errors.append('Overall audit strategy must be documented')
        if not self.controls_reliance:
            errors.append('Controls reliance approach must be selected')
        if not self.key_audit_areas:
            errors.append('Key audit areas must be documented')
        if not self.strategy_summary:
            errors.append('Strategy summary is required')
        if errors:
            raise UserError('Cannot complete P-12. Missing requirements:\n• ' + '\n• '.join(errors))

    def action_start_work(self):
        for record in self:
            if record.state != 'not_started':
                raise UserError('Can only start work on tabs that are Not Started.')
            record.state = 'in_progress'

    def action_complete(self):
        for record in self:
            if record.state != 'in_progress':
                raise UserError('Can only complete tabs that are In Progress.')
            record._validate_mandatory_fields()
            record.senior_signed_user_id = self.env.user
            record.senior_signed_on = fields.Datetime.now()
            record.state = 'completed'

    def action_review(self):
        for record in self:
            if record.state != 'completed':
                raise UserError('Can only review tabs that are Completed.')
            record.manager_reviewed_user_id = self.env.user
            record.manager_reviewed_on = fields.Datetime.now()
            record.state = 'reviewed'

    def action_approve(self):
        for record in self:
            if record.state != 'reviewed':
                raise UserError('Can only approve tabs that have been Reviewed.')
            record.partner_approved_user_id = self.env.user
            record.partner_approved_on = fields.Datetime.now()
            record.state = 'approved'

    def action_send_back(self):
        for record in self:
            if record.state not in ['completed', 'reviewed']:
                raise UserError('Can only send back tabs that are Completed or Reviewed.')
            record.state = 'in_progress'

    def action_unlock(self):
        for record in self:
            if record.state != 'approved':
                raise UserError('Can only unlock Approved tabs.')
            record.partner_approved_user_id = False
            record.partner_approved_on = False
            record.state = 'reviewed'


class PlanningP12ExpertLine(models.Model):
    """Expert Line Item for Audit Strategy."""
    _name = 'qaco.planning.p12.expert.line'
    _description = 'Auditor Expert'
    _order = 'sequence, name'

    p12_strategy_id = fields.Many2one(
        'qaco.planning.p12.strategy',
        string='P-12 Strategy',
        required=True,
        ondelete='cascade'
    )
    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(
        string='Expert Name/Firm',
        required=True
    )
    expertise_area = fields.Selection([
        ('valuation', 'Valuation'),
        ('actuarial', 'Actuarial'),
        ('it', 'IT/Cybersecurity'),
        ('tax', 'Tax'),
        ('legal', 'Legal'),
        ('environmental', 'Environmental'),
        ('engineering', 'Engineering'),
        ('other', 'Other'),
    ], string='Area of Expertise', required=True)
    scope_of_work = fields.Text(
        string='Scope of Work'
    )
    competence_assessment = fields.Text(
        string='Competence Assessment',
        help='Assessment of expert\'s competence, capabilities, and objectivity per ISA 620'
    )
    auditor_or_management = fields.Selection([
        ('auditor', "Auditor's Expert"),
        ('management', "Management's Expert"),
    ], string='Expert Type', required=True)
    related_audit_area = fields.Char(
        string='Related Audit Area'
    )
    notes = fields.Text(string='Notes')
