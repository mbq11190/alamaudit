# -*- coding: utf-8 -*-
"""
P-7: Fraud Risk Assessment
Standard: ISA 240
Purpose: Identify fraud risks and responses.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError


class PlanningP7Fraud(models.Model):
    """P-7: Fraud Risk Assessment (ISA 240)"""
    _name = 'qaco.planning.p7.fraud'
    _description = 'P-7: Fraud Risk Assessment'
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

    # ===== Fraud Brainstorming Documentation =====
    brainstorming_date = fields.Date(
        string='Brainstorming Date',
        tracking=True
    )
    brainstorming_participants = fields.Many2many(
        'res.users',
        'qaco_p7_brainstorming_participants_rel',
        'p7_id',
        'user_id',
        string='Brainstorming Participants'
    )
    brainstorming_documentation = fields.Html(
        string='Brainstorming Documentation',
        help='Document the fraud brainstorming discussion per ISA 240.15'
    )
    key_fraud_concerns = fields.Html(
        string='Key Fraud Concerns Identified',
        help='Summary of key fraud concerns raised during brainstorming'
    )

    # ===== Fraud Triangle Assessment =====
    # Incentives/Pressures
    fraud_incentives = fields.Html(
        string='Incentives/Pressures',
        help='Management or employee incentives or pressures to commit fraud'
    )
    incentive_factors = fields.Html(
        string='Incentive Factors Identified',
        help='Specific factors: profit targets, bonuses, debt covenants, etc.'
    )

    # Opportunities
    fraud_opportunities = fields.Html(
        string='Opportunities',
        help='Circumstances that provide opportunity to commit fraud'
    )
    opportunity_factors = fields.Html(
        string='Opportunity Factors Identified',
        help='Specific factors: control weaknesses, lack of oversight, etc.'
    )

    # Attitudes/Rationalizations
    fraud_attitudes = fields.Html(
        string='Attitudes/Rationalizations',
        help='Culture or attitudes that enable fraud'
    )
    attitude_factors = fields.Html(
        string='Attitude Factors Identified',
        help='Specific factors: aggressive management, poor tone at top, etc.'
    )

    # ===== Fraud Risk Factors =====
    fraud_risk_line_ids = fields.One2many(
        'qaco.planning.p7.fraud.line',
        'p7_fraud_id',
        string='Fraud Risk Factors'
    )

    # ===== Presumed Fraud Risks (ISA 240) =====
    revenue_recognition_fraud = fields.Boolean(
        string='Revenue Recognition - Presumed Fraud Risk',
        default=True,
        help='ISA 240.26 - Presumption of fraud risk in revenue recognition'
    )
    revenue_recognition_assessment = fields.Html(
        string='Revenue Recognition Fraud Assessment'
    )
    revenue_recognition_rebutted = fields.Boolean(
        string='Revenue Recognition Presumption Rebutted',
        help='Document if the presumption is rebutted'
    )
    revenue_rebuttal_justification = fields.Html(
        string='Rebuttal Justification',
        help='Justification for rebutting revenue recognition fraud risk'
    )

    management_override_fraud = fields.Boolean(
        string='Management Override - Presumed Fraud Risk',
        default=True,
        help='ISA 240.31 - Risk of management override of controls (cannot be rebutted)'
    )
    management_override_assessment = fields.Html(
        string='Management Override Assessment'
    )

    # ===== Fraud Response =====
    fraud_responses = fields.Html(
        string='Planned Fraud Responses',
        help='Audit responses to address identified fraud risks'
    )
    journal_entry_testing = fields.Html(
        string='Journal Entry Testing Plan',
        help='Plan for testing journal entries per ISA 240.32'
    )
    estimates_review = fields.Html(
        string='Accounting Estimates Review',
        help='Plan for reviewing accounting estimates for bias'
    )
    unusual_transactions = fields.Html(
        string='Unusual Transaction Testing',
        help='Plan for testing unusual significant transactions'
    )
    unpredictability_elements = fields.Html(
        string='Elements of Unpredictability',
        help='Planned unpredictable audit procedures'
    )

    # ===== Communication =====
    management_inquiry = fields.Html(
        string='Management Inquiry Documentation',
        help='Documentation of inquiries of management regarding fraud'
    )
    tcwg_inquiry = fields.Html(
        string='TCWG Inquiry Documentation',
        help='Documentation of inquiries of those charged with governance'
    )
    internal_audit_inquiry = fields.Html(
        string='Internal Audit Inquiry',
        help='Inquiries of internal audit regarding fraud'
    )

    # ===== Attachments =====
    fraud_risk_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p7_fraud_risk_rel',
        'p7_id',
        'attachment_id',
        string='Fraud Risk Documentation'
    )
    brainstorming_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p7_brainstorming_rel',
        'p7_id',
        'attachment_id',
        string='Brainstorming Notes'
    )

    # ===== Summary =====
    fraud_risk_summary = fields.Html(
        string='Fraud Risk Memo',
        help='Consolidated fraud risk assessment summary per ISA 240'
    )
    overall_fraud_risk = fields.Selection([
        ('low', '🟢 Low'),
        ('medium', '🟡 Medium'),
        ('high', '🔴 High'),
    ], string='Overall Fraud Risk Assessment', tracking=True)
    isa_reference = fields.Char(
        string='ISA Reference',
        default='ISA 240',
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
        ('audit_unique', 'UNIQUE(audit_id)', 'Only one P-7 record per Audit Engagement is allowed.')
    ]

    @api.depends('audit_id', 'client_id')
    def _compute_name(self):
        for record in self:
            if record.client_id:
                record.name = f"P7-{record.client_id.name[:15]}"
            else:
                record.name = 'P-7: Fraud Risk'

    def _validate_mandatory_fields(self):
        """Validate mandatory fields before completing P-7."""
        self.ensure_one()
        errors = []
        if not self.brainstorming_date:
            errors.append('Brainstorming date must be documented')
        if not self.brainstorming_documentation:
            errors.append('Brainstorming discussion must be documented per ISA 240')
        if not self.fraud_incentives:
            errors.append('Fraud incentives/pressures must be assessed')
        if not self.fraud_opportunities:
            errors.append('Fraud opportunities must be assessed')
        if not self.fraud_attitudes:
            errors.append('Fraud attitudes/rationalizations must be assessed')
        if not self.fraud_responses:
            errors.append('Planned fraud responses must be documented')
        if not self.fraud_risk_summary:
            errors.append('Fraud risk memo is required')
        if errors:
            raise UserError('Cannot complete P-7. Missing requirements:\n• ' + '\n• '.join(errors))

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


class PlanningP7FraudLine(models.Model):
    """Fraud Risk Factor Line Items."""
    _name = 'qaco.planning.p7.fraud.line'
    _description = 'Fraud Risk Factor'
    _order = 'risk_level desc, sequence'

    p7_fraud_id = fields.Many2one(
        'qaco.planning.p7.fraud',
        string='P-7 Fraud Assessment',
        required=True,
        ondelete='cascade'
    )
    sequence = fields.Integer(string='Sequence', default=10)
    risk_category = fields.Selection([
        ('incentive', 'Incentive/Pressure'),
        ('opportunity', 'Opportunity'),
        ('attitude', 'Attitude/Rationalization'),
    ], string='Risk Category', required=True)
    risk_description = fields.Text(
        string='Risk Description',
        required=True
    )
    risk_level = fields.Selection([
        ('low', '🟢 Low'),
        ('medium', '🟡 Medium'),
        ('high', '🔴 High'),
    ], string='Risk Level', required=True)
    affected_area = fields.Char(
        string='Affected Area/Account'
    )
    fraud_type = fields.Selection([
        ('misappropriation', 'Asset Misappropriation'),
        ('fraudulent_reporting', 'Fraudulent Financial Reporting'),
        ('both', 'Both'),
    ], string='Fraud Type')
    planned_response = fields.Text(
        string='Planned Response'
    )
    notes = fields.Text(string='Notes')
