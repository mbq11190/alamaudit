# -*- coding: utf-8 -*-
"""
P-1: Engagement Setup & Team Assignment
Standards: ISA 210, ISA 220, ISQM-1
Purpose: Establish engagement acceptance, ethical compliance, and audit team structure.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class PlanningP1Engagement(models.Model):
    """P-1: Engagement Setup & Team Assignment (ISA 210, 220, ISQM-1)"""
    _name = 'qaco.planning.p1.engagement'
    _description = 'P-1: Engagement Setup & Team Assignment'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'qaco.planning.tab.mixin']
    _order = 'create_date desc'

    # Common status workflow inherited from mixin
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

    # ===== Engagement Acceptance & Continuance =====
    is_new_engagement = fields.Boolean(
        string='New Engagement',
        default=True,
        tracking=True
    )
    previous_auditor = fields.Char(string='Previous Auditor Name')
    previous_auditor_communication = fields.Html(
        string='Communication with Previous Auditor',
        help='Document communication per ISA 300/ISA 510 for new engagements'
    )
    acceptance_continuance_checklist = fields.Html(
        string='Acceptance/Continuance Checklist',
        help='Document completion of acceptance procedures per ISQM-1'
    )
    acceptance_approved = fields.Boolean(
        string='Acceptance Approved',
        tracking=True
    )
    acceptance_approved_by_id = fields.Many2one(
        'res.users',
        string='Acceptance Approved By',
        tracking=True
    )
    acceptance_date = fields.Date(
        string='Acceptance Date',
        tracking=True
    )

    # ===== Independence & Conflict of Interest =====
    independence_confirmed = fields.Boolean(
        string='Independence Confirmed',
        tracking=True,
        help='Confirm compliance with ICAP Code of Ethics'
    )
    independence_threats_identified = fields.Html(
        string='Independence Threats Identified',
        help='Document any threats to independence and safeguards applied'
    )
    conflict_of_interest_confirmed = fields.Boolean(
        string='No Conflict of Interest',
        tracking=True
    )
    conflict_assessment = fields.Html(
        string='Conflict of Interest Assessment'
    )
    self_review_threat = fields.Boolean(string='Self-Review Threat Exists')
    familiarity_threat = fields.Boolean(string='Familiarity Threat Exists')
    intimidation_threat = fields.Boolean(string='Intimidation Threat Exists')
    advocacy_threat = fields.Boolean(string='Advocacy Threat Exists')
    safeguards_applied = fields.Html(
        string='Safeguards Applied',
        help='Document safeguards to address identified threats'
    )

    # ===== Engagement Letter =====
    engagement_letter_date = fields.Date(
        string='Engagement Letter Date',
        tracking=True
    )
    engagement_letter_signed = fields.Boolean(
        string='Engagement Letter Signed',
        tracking=True
    )
    engagement_letter_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p1_engagement_letter_rel',
        'p1_id',
        'attachment_id',
        string='Signed Engagement Letter'
    )
    engagement_letter_terms = fields.Html(
        string='Key Engagement Terms',
        help='Summarize key terms per ISA 210'
    )

    # ===== Audit Team Assignment =====
    engagement_partner_id = fields.Many2one(
        'res.users',
        string='Engagement Partner',
        tracking=True,
        help='Partner responsible for the engagement per ISA 220'
    )
    engagement_manager_id = fields.Many2one(
        'res.users',
        string='Engagement Manager',
        tracking=True
    )
    senior_auditor_id = fields.Many2one(
        'res.users',
        string='Senior Auditor',
        tracking=True
    )
    it_specialist_id = fields.Many2one(
        'res.users',
        string='IT Specialist',
        tracking=True,
        help='IT audit specialist if required'
    )
    eqcr_id = fields.Many2one(
        'res.users',
        string='Engagement Quality Control Reviewer',
        tracking=True,
        help='EQCR per ISA 220/ISQM-1 if applicable'
    )
    eqcr_required = fields.Boolean(
        string='EQCR Required',
        tracking=True,
        help='Is an Engagement Quality Control Review required?'
    )
    team_member_ids = fields.Many2many(
        'res.users',
        'qaco_p1_team_members_rel',
        'p1_id',
        'user_id',
        string='Other Team Members'
    )
    team_competence_assessment = fields.Html(
        string='Team Competence Assessment',
        help='Document assessment of team competence per ISA 220'
    )

    # ===== Time Budget & Resources =====
    planned_hours_partner = fields.Float(string='Partner Hours')
    planned_hours_manager = fields.Float(string='Manager Hours')
    planned_hours_senior = fields.Float(string='Senior Hours')
    planned_hours_staff = fields.Float(string='Staff Hours')
    planned_hours_total = fields.Float(
        string='Total Planned Hours',
        compute='_compute_total_hours',
        store=True
    )
    budget_amount = fields.Monetary(
        string='Engagement Budget',
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )

    # ===== Quality Objectives (ISQM-1) =====
    quality_objectives = fields.Html(
        string='Quality Objectives',
        help='Document quality objectives per ISQM-1'
    )
    quality_risks_identified = fields.Html(
        string='Quality Risks Identified'
    )
    quality_responses = fields.Html(
        string='Responses to Quality Risks'
    )

    # ===== Key Dates =====
    audit_period_from = fields.Date(
        string='Audit Period From',
        required=True,
        tracking=True
    )
    audit_period_to = fields.Date(
        string='Audit Period To',
        required=True,
        tracking=True
    )
    financial_year_end = fields.Date(
        string='Financial Year End',
        required=True,
        tracking=True
    )
    reporting_deadline = fields.Date(
        string='Reporting Deadline',
        tracking=True
    )
    agm_date = fields.Date(
        string='Expected AGM Date',
        tracking=True
    )

    # ===== Sign-off Fields (from mixin, explicit for clarity) =====
    senior_signed_user_id = fields.Many2one(
        'res.users',
        string='Senior Completed By',
        tracking=True,
        copy=False,
        readonly=True
    )
    senior_signed_on = fields.Datetime(
        string='Senior Completed On',
        tracking=True,
        copy=False,
        readonly=True
    )
    manager_reviewed_user_id = fields.Many2one(
        'res.users',
        string='Manager Reviewed By',
        tracking=True,
        copy=False,
        readonly=True
    )
    manager_reviewed_on = fields.Datetime(
        string='Manager Reviewed On',
        tracking=True,
        copy=False,
        readonly=True
    )
    partner_approved_user_id = fields.Many2one(
        'res.users',
        string='Partner Approved By',
        tracking=True,
        copy=False,
        readonly=True
    )
    partner_approved_on = fields.Datetime(
        string='Partner Approved On',
        tracking=True,
        copy=False,
        readonly=True
    )
    reviewer_notes = fields.Html(string='Reviewer Notes')
    approval_notes = fields.Html(string='Approval Notes')

    _sql_constraints = [
        ('audit_unique', 'UNIQUE(audit_id)', 'Only one P-1 record per Audit Engagement is allowed.')
    ]

    @api.depends('audit_id', 'client_id')
    def _compute_name(self):
        for record in self:
            if record.client_id:
                record.name = f"P1-{record.client_id.name[:15]}"
            else:
                record.name = 'P-1: Engagement Setup'

    @api.depends('planned_hours_partner', 'planned_hours_manager', 'planned_hours_senior', 'planned_hours_staff')
    def _compute_total_hours(self):
        for record in self:
            record.planned_hours_total = (
                record.planned_hours_partner +
                record.planned_hours_manager +
                record.planned_hours_senior +
                record.planned_hours_staff
            )

    def _validate_mandatory_fields(self):
        """Validate mandatory fields before completing P-1."""
        self.ensure_one()
        errors = []
        if not self.engagement_letter_signed:
            errors.append('Engagement letter must be signed')
        if not self.engagement_letter_attachment_ids:
            errors.append('Signed engagement letter must be uploaded')
        if not self.independence_confirmed:
            errors.append('Independence must be confirmed')
        if not self.conflict_of_interest_confirmed:
            errors.append('Conflict of interest assessment must be completed')
        if not self.engagement_partner_id:
            errors.append('Engagement Partner must be assigned')
        if not self.engagement_manager_id:
            errors.append('Engagement Manager must be assigned')
        if not self.acceptance_approved:
            errors.append('Engagement acceptance must be approved')
        if self.eqcr_required and not self.eqcr_id:
            errors.append('EQCR is required but not assigned')
        if errors:
            raise UserError('Cannot complete P-1. Missing requirements:\n• ' + '\n• '.join(errors))

    @api.constrains('audit_period_from', 'audit_period_to')
    def _check_audit_period(self):
        for record in self:
            if record.audit_period_from and record.audit_period_to:
                if record.audit_period_from >= record.audit_period_to:
                    raise ValidationError('Audit period "From" date must be before "To" date.')

    def action_start_work(self):
        """Move tab from Not Started to In Progress."""
        for record in self:
            if record.state != 'not_started':
                raise UserError('Can only start work on tabs that are Not Started.')
            record.state = 'in_progress'

    def action_complete(self):
        """Senior marks work as complete, moves to Completed state."""
        for record in self:
            if record.state != 'in_progress':
                raise UserError('Can only complete tabs that are In Progress.')
            record._validate_mandatory_fields()
            record.senior_signed_user_id = self.env.user
            record.senior_signed_on = fields.Datetime.now()
            record.state = 'completed'

    def action_review(self):
        """Manager reviews and approves, moves to Reviewed state."""
        for record in self:
            if record.state != 'completed':
                raise UserError('Can only review tabs that are Completed.')
            record.manager_reviewed_user_id = self.env.user
            record.manager_reviewed_on = fields.Datetime.now()
            record.state = 'reviewed'

    def action_approve(self):
        """Partner approves, moves to Approved state (locked)."""
        for record in self:
            if record.state != 'reviewed':
                raise UserError('Can only approve tabs that have been Reviewed.')
            record.partner_approved_user_id = self.env.user
            record.partner_approved_on = fields.Datetime.now()
            record.state = 'approved'

    def action_send_back(self):
        """Send back for rework."""
        for record in self:
            if record.state not in ['completed', 'reviewed']:
                raise UserError('Can only send back tabs that are Completed or Reviewed.')
            record.state = 'in_progress'

    def action_unlock(self):
        """Unlock an approved tab."""
        for record in self:
            if record.state != 'approved':
                raise UserError('Can only unlock Approved tabs.')
            record.partner_approved_user_id = False
            record.partner_approved_on = False
            record.state = 'reviewed'
