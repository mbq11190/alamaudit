# -*- coding: utf-8 -*-
"""
P-8: Going Concern (Preliminary Assessment)
Standard: ISA 570
Purpose: Assess entity's ability to continue as a going concern.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError


class PlanningP8GoingConcern(models.Model):
    """P-8: Going Concern - Preliminary Assessment (ISA 570)"""
    _name = 'qaco.planning.p8.going.concern'
    _description = 'P-8: Going Concern Assessment'
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
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )

    # ===== Financial Indicators =====
    financial_indicators_header = fields.Char(
        string='Financial Indicators',
        default='ISA 570.A3 - Financial Indicators',
        readonly=True
    )
    net_liability_position = fields.Boolean(
        string='Net Liability/Negative Working Capital',
        help='Net liability or net current liability position'
    )
    negative_operating_cash = fields.Boolean(
        string='Negative Operating Cash Flows',
        help='Negative operating cash flows indicated by historical or forecast statements'
    )
    loan_defaults = fields.Boolean(
        string='Loan Defaults/Breaches',
        help='Default on loan agreements or inability to pay creditors on due dates'
    )
    inability_pay_dividends = fields.Boolean(
        string='Inability to Pay Dividends',
        help='Arrears or discontinuance of dividends'
    )
    adverse_financial_ratios = fields.Boolean(
        string='Adverse Financial Ratios',
        help='Adverse key financial ratios'
    )
    substantial_losses = fields.Boolean(
        string='Substantial Operating Losses'
    )
    financing_difficulty = fields.Boolean(
        string='Difficulty Obtaining Financing'
    )
    financial_indicators_notes = fields.Html(
        string='Financial Indicators Analysis'
    )

    # ===== Operating Indicators =====
    operating_indicators_header = fields.Char(
        string='Operating Indicators',
        default='ISA 570.A3 - Operating Indicators',
        readonly=True
    )
    management_intent_liquidate = fields.Boolean(
        string='Management Intent to Liquidate/Cease',
        help='Management intentions to liquidate or cease operations'
    )
    loss_key_management = fields.Boolean(
        string='Loss of Key Management',
        help='Loss of key management without replacement'
    )
    loss_major_market = fields.Boolean(
        string='Loss of Major Market/Customer/Supplier',
        help='Loss of major market, customer, franchise, license, or principal supplier'
    )
    labor_difficulties = fields.Boolean(
        string='Labor Difficulties',
        help='Labor difficulties'
    )
    shortage_supplies = fields.Boolean(
        string='Shortage of Important Supplies',
        help='Shortages of important supplies'
    )
    powerful_competitor = fields.Boolean(
        string='Emergence of Powerful Competitor'
    )
    operating_indicators_notes = fields.Html(
        string='Operating Indicators Analysis'
    )

    # ===== Other Indicators =====
    other_indicators_header = fields.Char(
        string='Other Indicators',
        default='ISA 570.A3 - Other Indicators',
        readonly=True
    )
    non_compliance_capital = fields.Boolean(
        string='Non-compliance with Capital Requirements',
        help='Non-compliance with capital or other statutory or regulatory requirements'
    )
    pending_litigation = fields.Boolean(
        string='Pending Litigation/Claims',
        help='Pending legal or regulatory proceedings that may result in claims'
    )
    changes_legislation = fields.Boolean(
        string='Changes in Legislation/Policy',
        help='Changes in law/regulation or government policy expected to adversely affect entity'
    )
    uninsured_catastrophes = fields.Boolean(
        string='Uninsured/Underinsured Catastrophes'
    )
    other_indicators_notes = fields.Html(
        string='Other Indicators Analysis'
    )

    # ===== Management's Plans =====
    management_plans = fields.Html(
        string="Management's Plans",
        help="Document management's plans to address going concern issues"
    )
    plans_feasibility = fields.Html(
        string='Feasibility of Plans',
        help='Assessment of the feasibility of management\'s plans'
    )
    plans_likelihood = fields.Selection([
        ('unlikely', '🔴 Unlikely to be Successful'),
        ('uncertain', '🟡 Uncertain'),
        ('likely', '🟢 Likely to be Successful'),
    ], string='Likelihood of Success')

    # ===== Preliminary Conclusion =====
    gc_risk_identified = fields.Boolean(
        string='Going Concern Risk Identified',
        tracking=True
    )
    preliminary_conclusion = fields.Selection([
        ('no_concern', '🟢 No Significant Going Concern Issues'),
        ('uncertainty_exists', '🟡 Material Uncertainty May Exist'),
        ('inappropriate_basis', '🔴 Going Concern Basis May Be Inappropriate'),
    ], string='Preliminary Conclusion', tracking=True)
    conclusion_rationale = fields.Html(
        string='Conclusion Rationale',
        help='Rationale for the preliminary going concern conclusion'
    )

    # ===== Disclosure Requirements =====
    disclosure_required = fields.Boolean(
        string='Disclosure Required',
        help='Is going concern disclosure required in financial statements?'
    )
    disclosure_assessment = fields.Html(
        string='Disclosure Assessment',
        help='Assessment of adequacy of disclosures'
    )

    # ===== Further Procedures =====
    further_procedures = fields.Html(
        string='Further Procedures Planned',
        help='Additional audit procedures to be performed'
    )
    management_representations = fields.Html(
        string='Management Representations Required',
        help='Specific representations to be obtained from management'
    )

    # ===== Attachments =====
    gc_analysis_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p8_gc_analysis_rel',
        'p8_id',
        'attachment_id',
        string='Going Concern Analysis'
    )
    cash_flow_forecast_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p8_cash_flow_rel',
        'p8_id',
        'attachment_id',
        string='Cash Flow Forecasts'
    )

    # ===== Summary =====
    going_concern_summary = fields.Html(
        string='Going Concern Summary',
        help='Consolidated going concern assessment per ISA 570'
    )
    isa_reference = fields.Char(
        string='ISA Reference',
        default='ISA 570',
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
        ('audit_unique', 'UNIQUE(audit_id)', 'Only one P-8 record per Audit Engagement is allowed.')
    ]

    @api.depends('audit_id', 'client_id')
    def _compute_name(self):
        for record in self:
            if record.client_id:
                record.name = f"P8-{record.client_id.name[:15]}"
            else:
                record.name = 'P-8: Going Concern'

    def _validate_mandatory_fields(self):
        """Validate mandatory fields before completing P-8."""
        self.ensure_one()
        errors = []
        if not self.preliminary_conclusion:
            errors.append('Preliminary going concern conclusion is required')
        if not self.conclusion_rationale:
            errors.append('Conclusion rationale must be documented')
        if self.gc_risk_identified and not self.management_plans:
            errors.append("Management's plans must be documented if GC risk exists")
        if not self.going_concern_summary:
            errors.append('Going concern summary is required')
        if errors:
            raise UserError('Cannot complete P-8. Missing requirements:\n• ' + '\n• '.join(errors))

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
