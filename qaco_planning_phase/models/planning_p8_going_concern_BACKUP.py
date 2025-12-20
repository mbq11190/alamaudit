# -*- coding: utf-8 -*-
"""
P-8: Going Concern (Preliminary Assessment)
ISA 570/315/330/240/220/ISQM-1/Companies Act 2017/ICAP QCR/AOB
Court-defensible, fully integrated with planning workflow.
"""
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)

# =============================
# Parent Model: Going Concern Assessment
# =============================
class AuditPlanningP8GoingConcern(models.Model):
    _name = 'audit.planning.p8.going_concern'
    _description = 'P-8: Going Concern (Preliminary Assessment)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    engagement_id = fields.Many2one('qaco.audit', string='Audit Engagement', required=True, ondelete='cascade', index=True, tracking=True)
    audit_year = fields.Many2one('qaco.audit.year', string='Audit Year', required=True, ondelete='cascade', index=True)
    partner_id = fields.Many2one('res.users', string='Engagement Partner', required=True)
    planning_main_id = fields.Many2one('qaco.planning.main', string='Planning Phase', ondelete='cascade', index=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('prepared', 'Prepared'),
        ('reviewed', 'Reviewed'),
        ('locked', 'Locked'),
    ], string='Status', default='draft', tracking=True, copy=False)
    gc_indicator_line_ids = fields.One2many('audit.planning.p8.gc_indicator_line', 'going_concern_id', string='GC Indicators', required=True)
    # Section A: Basis of Assessment & Period Covered
    assessment_period = fields.Char(string='Assessment Period (≥ 12 months)')
    fs_basis = fields.Selection([
        ('going_concern', 'Going Concern'),
        ('other', 'Other'),
    ], string='Financial Statements Basis')
    assessment_timing = fields.Char(string="Auditor's Assessment Timing")
    sources_management_accounts = fields.Boolean(string='Management Accounts')
    sources_cashflow_forecasts = fields.Boolean(string='Cash-flow Forecasts')
    sources_financing_agreements = fields.Boolean(string='Financing Agreements')
    sources_budgets = fields.Boolean(string='Budgets / Business Plans')
    period_adequate = fields.Boolean(string='Period adequate per ISA 570?')
    sources_appropriate = fields.Boolean(string='Sources identified and appropriate?')
    # Section D: Financing & Liquidity Indicators
    financing_facilities = fields.Char(string='Availability of Financing Facilities')
    reliance_short_term = fields.Boolean(string='Reliance on Short-term Borrowings?')
    ability_refinance = fields.Boolean(string='Ability to Refinance Debt?')
    shareholder_support = fields.Boolean(string='Dependence on Shareholder Support?')
    donor_funding = fields.Boolean(string='Government/Donor Funding Reliance?')
    financing_sources_assessed = fields.Boolean(string='Financing sources assessed?')
    liquidity_stress_evaluated = fields.Boolean(string='Liquidity stress evaluated?')
    # Section E: Legal, Regulatory & External Indicators
    pending_litigation = fields.Boolean(string='Pending Litigation with Material Impact?')
    regulatory_actions = fields.Boolean(string='Regulatory Actions / Penalties?')
    adverse_market = fields.Boolean(string='Adverse Market/Economic Conditions?')
    political_uncertainty = fields.Boolean(string='Political/Policy Uncertainty?')
    disclosure_risk_flag = fields.Boolean(string='Disclosure Risk Flagged?')
    # Section F: Management’s Going-Concern Assessment
    mgmt_gc_assessment_done = fields.Boolean(string='Management GC Assessment Performed?')
    mgmt_basis = fields.Char(string="Basis of Management's Assessment")
    mgmt_key_assumptions = fields.Text(string='Key Assumptions Used')
    mgmt_period_covered = fields.Char(string='Period Covered by Management Assessment')
    mgmt_consistency = fields.Boolean(string="Consistency with Auditor's Understanding?")
    mgmt_assessment_obtained = fields.Boolean(string='Management assessment obtained?')
    mgmt_assumptions_evaluated = fields.Boolean(string='Assumptions evaluated for reasonableness?')
    # Section G: Management Plans to Mitigate Risks
    mgmt_planned_actions = fields.Text(string='Planned Actions')
    mgmt_plan_status = fields.Selection([
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('implemented', 'Implemented'),
    ], string='Status')
    mgmt_plan_feasibility = fields.Text(string='Feasibility Assessment (Auditor)')
    mgmt_plan_third_party = fields.Boolean(string='Dependency on Third-party Support?')
    unsupported_plans_flag = fields.Boolean(string='Unsupported plans increase GC risk?')
    # Section H: Preliminary Going-Concern Conclusion
    material_uncertainty = fields.Boolean(string='Material Uncertainty Identified?')
    significant_doubt = fields.Boolean(string='Significant Doubt Exists?')
    gc_conclusion_basis = fields.Text(string='Basis for Conclusion')
    gc_disclosure_implications = fields.Boolean(string='Disclosure Implications Identified?')
    # Section J: Mandatory Document Uploads
    attachment_ids = fields.Many2many('ir.attachment', 'audit_p8_gc_attachment_rel', 'gc_id', 'attachment_id', string='Required Attachments', help='Cash-flow forecasts, financing agreements, management GC assessment, support letters, correspondence')
    mandatory_upload_check = fields.Boolean(string='Mandatory uploads present?')
    # Section K: Conclusion & Professional Judgment
    conclusion_narrative = fields.Text(string='Conclusion Narrative', required=True, default="Based on the preliminary assessment performed in accordance with ISA 570 (Revised), indicators of going-concern risk have been identified and evaluated. Management’s assessment and plans have been considered, and appropriate implications for audit strategy and reporting have been determined.")
    gc_assessment_completed = fields.Boolean(string='GC assessment completed?')
    risks_classified = fields.Boolean(string='Risks appropriately classified?')
    strategy_implications_identified = fields.Boolean(string='Audit strategy implications identified?')
    # Section L: Review, Approval & Lock
    prepared_by = fields.Many2one('res.users', string='Prepared By')
    prepared_by_role = fields.Char(string='Prepared By Role')
    prepared_date = fields.Datetime(string='Prepared Date')
    reviewed_by = fields.Many2one('res.users', string='Reviewed By')
    review_notes = fields.Text(string='Review Notes')
    partner_approved = fields.Boolean(string='Partner Approved?')
    partner_comments = fields.Text(string='Partner Comments (Mandatory)')
    locked = fields.Boolean(string='Locked', compute='_compute_locked', store=True)
    # Outputs
    gc_memo_pdf = fields.Binary(string='GC Assessment Memorandum (PDF)')
    gc_risk_summary = fields.Binary(string='GC Risk Summary')
    # Audit trail
    version_history = fields.Text(string='Version History')
    reviewer_timestamps = fields.Text(string='Reviewer Timestamps')

    @api.depends('partner_approved')
    def _compute_locked(self):
        for rec in self:
            rec.locked = bool(rec.partner_approved)

    def action_prepare(self):
        self.state = 'prepared'
        self.prepared_by = self.env.user.id
        self.prepared_by_role = self.env.user.groups_id.mapped('name')
        self.prepared_date = fields.Datetime.now()
        self.message_post(body="P-8 prepared.")

    def action_review(self):
        self.state = 'reviewed'
        self.reviewed_by = self.env.user.id
        self.message_post(body="P-8 reviewed.")

    def action_partner_approve(self):
        if not self.partner_comments:
            raise ValidationError("Partner comments are mandatory for approval.")
        self.state = 'locked'
        self.partner_approved = True
        self.message_post(body="P-8 partner approved and locked.")

    @api.constrains('attachment_ids')
    def _check_mandatory_uploads(self):
        for rec in self:
            if not rec.attachment_ids:
                raise ValidationError("Mandatory GC assessment documents must be uploaded.")

    @api.constrains('gc_indicator_line_ids')
    def _check_gc_indicator_lines(self):
        for rec in self:
            if not rec.gc_indicator_line_ids:
                raise ValidationError("At least one GC indicator line must be entered.")

    # Pre-conditions enforcement
    @api.model
    def create(self, vals):
        planning = self.env['qaco.planning.main'].browse(vals.get('planning_main_id'))
        if not planning or not planning.p7_partner_locked:
            raise UserError("P-8 cannot be started until P-7 is partner-approved and locked.")
        if not planning.p6_finalized or not planning.p4_outputs_ready or not planning.p5_finalized:
            raise UserError("P-8 requires finalized P-6, and outputs from P-4 and P-5.")
        return super().create(vals)

# =============================
# Child Model: GC Indicator Line
# =============================
class AuditPlanningP8GCIndicatorLine(models.Model):
    _name = 'audit.planning.p8.gc_indicator_line'
    _description = 'P-8: GC Indicator Line'
    _order = 'id desc'

    going_concern_id = fields.Many2one('audit.planning.p8.going_concern', string='Going Concern Assessment', required=True, ondelete='cascade', index=True)
    indicator_type = fields.Selection([
        ('financial', 'Financial'),
        ('operating', 'Operating'),
        ('liquidity', 'Financing/Liquidity'),
        ('legal', 'Legal/Regulatory/External'),
    ], string='Indicator Type', required=True)
    indicator = fields.Char(string='Indicator', required=True)
    present = fields.Boolean(string='Present?')
    details = fields.Text(string='Details')
    risk_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Risk Level')
    # Audit trail
    change_log = fields.Text(string='Change Log')
    version_history = fields.Text(string='Version History')
    reviewer_timestamps = fields.Text(string='Reviewer Timestamps')

    def write(self, vals):
        self.message_post(body=f"GC indicator line updated: {vals}")
        return super().write(vals)

    def unlink(self):
        self.message_post(body="GC indicator line deleted.")
        return super().unlink()
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
    _description = 'P-8: Preliminary Analytical Procedures'
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
        index=True,
        tracking=True
    )
    planning_main_id = fields.Many2one(
        'qaco.planning.main',
        string='Planning Phase',
        ondelete='cascade',
        index=True
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
    # XML view compatible narrative field
    financial_indicators = fields.Html(
        string='Financial Indicators',
        help='Narrative assessment of financial indicators'
    )
    net_liability_position = fields.Boolean(
        string='Net Liability/Negative Working Capital',
        help='Net liability or net current liability position'
    )
    negative_operating_cash = fields.Boolean(
        string='Negative Operating Cash Flows',
        help='Negative operating cash flows indicated by historical or forecast statements'
    )
    # XML view compatible alias
    negative_operating_cash_flow = fields.Boolean(
        string='Negative Operating Cash Flow',
        related='negative_operating_cash',
        readonly=False
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
    # XML view compatible alias
    adverse_key_ratios = fields.Boolean(
        string='Adverse Key Ratios',
        related='adverse_financial_ratios',
        readonly=False
    )
    substantial_losses = fields.Boolean(
        string='Substantial Operating Losses'
    )
    # XML view compatible alias
    substantial_operating_losses = fields.Boolean(
        string='Substantial Operating Losses',
        related='substantial_losses',
        readonly=False
    )
    financing_difficulty = fields.Boolean(
        string='Difficulty Obtaining Financing'
    )
    # XML view compatible aliases
    inability_to_pay_creditors = fields.Boolean(
        string='Inability to Pay Creditors',
        related='loan_defaults',
        readonly=False
    )
    inability_to_obtain_financing = fields.Boolean(
        string='Inability to Obtain Financing',
        related='financing_difficulty',
        readonly=False
    )
    financial_indicators_notes = fields.Html(
        string='Financial Indicators Analysis'
    )
    # XML view compatible alias
    financial_indicator_assessment = fields.Html(
        string='Financial Indicator Assessment',
        related='financial_indicators_notes',
        readonly=False
    )

    # ===== Operating Indicators =====
    operating_indicators_header = fields.Char(
        string='Operating Indicators',
        default='ISA 570.A3 - Operating Indicators',
        readonly=True
    )
    # XML view compatible narrative field
    operating_indicators = fields.Html(
        string='Operating Indicators',
        help='Narrative assessment of operating indicators'
    )
    management_intent_liquidate = fields.Boolean(
        string='Management Intent to Liquidate/Cease',
        help='Management intentions to liquidate or cease operations'
    )
    # XML view compatible alias
    management_intentions = fields.Boolean(
        string='Management Intentions',
        related='management_intent_liquidate',
        readonly=False
    )
    loss_key_management = fields.Boolean(
        string='Loss of Key Management',
        help='Loss of key management without replacement'
    )
    # XML view compatible alias
    loss_of_key_management = fields.Boolean(
        string='Loss of Key Management',
        related='loss_key_management',
        readonly=False
    )
    loss_major_market = fields.Boolean(
        string='Loss of Major Market/Customer/Supplier',
        help='Loss of major market, customer, franchise, license, or principal supplier'
    )
    # XML view compatible alias
    loss_of_major_market = fields.Boolean(
        string='Loss of Major Market',
        related='loss_major_market',
        readonly=False
    )
    labor_difficulties = fields.Boolean(
        string='Labor Difficulties',
        help='Labor difficulties'
    )
    shortage_supplies = fields.Boolean(
        string='Shortage of Important Supplies',
        help='Shortages of important supplies'
    )
    # XML view compatible alias
    shortage_of_supplies = fields.Boolean(
        string='Shortage of Supplies',
        related='shortage_supplies',
        readonly=False
    )
    powerful_competitor = fields.Boolean(
        string='Emergence of Powerful Competitor'
    )
    # XML view compatible alias
    emergence_of_competitor = fields.Boolean(
        string='Emergence of Competitor',
        related='powerful_competitor',
        readonly=False
    )
    operating_indicators_notes = fields.Html(
        string='Operating Indicators Analysis'
    )
    # XML view compatible alias
    operating_indicator_assessment = fields.Html(
        string='Operating Indicator Assessment',
        related='operating_indicators_notes',
        readonly=False
    )

    # ===== Other Indicators (includes Legal/Regulatory) =====
    other_indicators_header = fields.Char(
        string='Other Indicators',
        default='ISA 570.A3 - Other Indicators',
        readonly=True
    )
    # XML view compatible narrative fields
    legal_indicators = fields.Html(
        string='Legal/Regulatory Indicators',
        help='Assessment of legal and regulatory indicators'
    )
    other_indicators = fields.Html(
        string='Other Indicators',
        help='Assessment of other going concern indicators'
    )
    non_compliance_capital = fields.Boolean(
        string='Non-compliance with Capital Requirements',
        help='Non-compliance with capital or other statutory or regulatory requirements'
    )
    pending_litigation = fields.Boolean(
        string='Pending Litigation/Claims',
        help='Pending legal or regulatory proceedings that may result in claims'
    )
    # XML view compatible alias
    pending_legal_proceedings = fields.Boolean(
        string='Pending Legal Proceedings',
        related='pending_litigation',
        readonly=False
    )
    changes_legislation = fields.Boolean(
        string='Changes in Legislation/Policy',
        help='Changes in law/regulation or government policy expected to adversely affect entity'
    )
    # XML view compatible alias
    changes_in_law = fields.Boolean(
        string='Changes in Law',
        related='changes_legislation',
        readonly=False
    )
    license_revocation = fields.Boolean(
        string='License Revocation Risk',
        help='Risk of license or permit revocation'
    )
    uninsured_catastrophes = fields.Boolean(
        string='Uninsured/Underinsured Catastrophes'
    )
    other_indicators_notes = fields.Html(
        string='Other Indicators Analysis'
    )
    # XML view compatible alias
    legal_indicator_assessment = fields.Html(
        string='Legal Indicator Assessment',
        related='other_indicators_notes',
        readonly=False
    )
    industry_economic_factors = fields.Html(
        string='Industry/Economic Factors',
        help='Industry and economic factors affecting going concern'
    )
    pandemic_impact = fields.Html(
        string='Pandemic Impact',
        help='Assessment of pandemic (COVID-19) impact on operations'
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
    plans_supporting_docs = fields.Html(
        string='Supporting Documentation',
        help='Documentation supporting management\'s plans'
    )
    plans_audit_procedures = fields.Html(
        string='Audit Procedures on Management Plans',
        help='Audit procedures performed on management\'s plans'
    )
    plans_likelihood = fields.Selection([
        ('unlikely', '🔴 Unlikely to be Successful'),
        ('uncertain', '🟡 Uncertain'),
        ('likely', '🟢 Likely to be Successful'),
    ], string='Likelihood of Success')

    # ===== Period of Assessment =====
    assessment_period_months = fields.Integer(
        string='Assessment Period (Months)',
        default=12,
        help='Period covered by management\'s assessment'
    )
    assessment_date = fields.Date(
        string='Assessment Date',
        help='Date of going concern assessment'
    )
    assessment_period_adequacy = fields.Html(
        string='Assessment Period Adequacy',
        help='Assessment of whether management\'s period is adequate'
    )
    events_beyond_period = fields.Html(
        string='Events Beyond Assessment Period',
        help='Consideration of events beyond the assessment period'
    )

    # ===== Inquiries & Procedures =====
    management_inquiries = fields.Html(
        string='Management Inquiries',
        help='Inquiries of management regarding going concern'
    )
    audit_procedures_performed = fields.Html(
        string='Audit Procedures Performed',
        help='Audit procedures performed for going concern assessment'
    )
    written_representations = fields.Html(
        string='Written Representations',
        help='Written representations obtained from management'
    )

    # ===== Preliminary Conclusion =====
    gc_risk_identified = fields.Boolean(
        string='Going Concern Risk Identified',
        tracking=True
    )
    # XML view compatible alias
    material_uncertainty_exists = fields.Boolean(
        string='Material Uncertainty Exists',
        related='gc_risk_identified',
        readonly=False
    )
    preliminary_conclusion = fields.Selection([
        ('no_concern', '🟢 No Significant Going Concern Issues'),
        ('uncertainty_exists', '🟡 Material Uncertainty May Exist'),
        ('inappropriate_basis', '🔴 Going Concern Basis May Be Inappropriate'),
    ], string='Preliminary Conclusion', tracking=True)
    # XML view compatible alias
    going_concern_conclusion = fields.Selection(
        string='Going Concern Conclusion',
        related='preliminary_conclusion',
        readonly=False)
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
    material_uncertainty_disclosure = fields.Html(
        string='Material Uncertainty Disclosure',
        help='Assessment of material uncertainty disclosure'
    )
    reporting_implications = fields.Html(
        string='Reporting Implications',
        help='Implications for auditor\'s report'
    )
    report_modification = fields.Boolean(
        string='Report Modification Required',
        help='Is modification of audit report required?'
    )
    emphasis_of_matter = fields.Boolean(
        string='Emphasis of Matter Required',
        help='Is emphasis of matter paragraph required?'
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
    # XML view compatible alias
    going_concern_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p8_gc_attachment_rel',
        'p8_id',
        'attachment_id',
        string='Going Concern Documentation'
    )
    cash_flow_forecast_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p8_cash_flow_rel',
        'p8_id',
        'attachment_id',
        string='Cash Flow Forecasts'
    )
    representation_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p8_representation_rel',
        'p8_id',
        'attachment_id',
        string='Management Representations'
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
