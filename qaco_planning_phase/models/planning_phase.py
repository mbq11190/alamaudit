# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class PlanningPhase(models.Model):
    _name = 'qaco.planning.phase'
    _description = 'Planning Phase'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    SUBTAB_STATUS = [
        ('red', 'Incomplete'),
        ('amber', 'In Progress'),
        ('green', 'Complete'),
    ]
    RISK_RATING = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    CONTROL_RATING = [
        ('none', 'Does Not Exist'),
        ('weak', 'Weak'),
        ('moderate', 'Moderate'),
        ('strong', 'Strong'),
    ]
    ASSERTION_TYPES = [
        ('existence', 'Existence'),
        ('completeness', 'Completeness'),
        ('valuation', 'Valuation'),
        ('rights', 'Rights & Obligations'),
        ('presentation', 'Presentation & Disclosure'),
    ]
    MATERIALITY_BENCHMARKS = [
        ('pbt', 'Profit Before Tax'),
        ('revenue', 'Revenue'),
        ('assets', 'Total Assets'),
        ('equity', 'Equity'),
        ('expenses', 'Total Expenses'),
    ]
    _STATUS_FIELDS = (
        'understanding_status',
        'analytics_status',
        'materiality_status',
        'control_status',
        'risk_status',
        'completion_status',
    )
    _MANDATORY_ATTACHMENT_FIELDS = (
        'organogram_attachment_ids',
        'engagement_letter_attachment_ids',
        'board_minutes_attachment_ids',
        'process_flow_attachment_ids',
        'related_party_attachment_ids',
        'materiality_worksheet_attachment_ids',
        'analytical_summary_attachment_ids',
        'risk_register_attachment_ids',
        'audit_strategy_attachment_ids',
    )
    _MANDATORY_CHECKLIST_FIELDS = (
        'checklist_engagement_letter',
        'checklist_entity_understanding',
        'checklist_fraud_brainstormed',
        'checklist_analytics_performed',
        'checklist_materiality_finalized',
        'checklist_controls_assessed',
        'checklist_risks_linked',
        'checklist_strategy_signed',
        'checklist_independence_confirmed',
        'checklist_partner_manager_review',
    )

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    audit_id = fields.Many2one('qaco.audit', string='Audit', required=True, ondelete='cascade')
    client_id = fields.Many2one('res.partner', string='Client Name', related='audit_id.client_id', readonly=True, store=True)
    understanding_status = fields.Selection(SUBTAB_STATUS, default='red', tracking=True)
    analytics_status = fields.Selection(SUBTAB_STATUS, default='red', tracking=True)
    materiality_status = fields.Selection(SUBTAB_STATUS, default='red', tracking=True)
    control_status = fields.Selection(SUBTAB_STATUS, default='red', tracking=True)
    risk_status = fields.Selection(SUBTAB_STATUS, default='red', tracking=True)
    completion_status = fields.Selection(SUBTAB_STATUS, default='red', tracking=True)
    organogram_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_plan_organogram_rel', 'phase_id', 'attachment_id',
        string='Organogram Files', help='Mandatory organogram upload per ISA 315.', tracking=True)
    engagement_letter_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_plan_eng_rel', 'phase_id', 'attachment_id',
        string='Signed Engagement Letters', help='Signed engagement letters for the audit.', tracking=True)
    board_minutes_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_plan_minutes_rel', 'phase_id', 'attachment_id',
        string='BOD/Audit Committee Minutes', help='Key governance minutes with relevant summaries.', tracking=True)
    process_flow_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_plan_flow_rel', 'phase_id', 'attachment_id',
        string='Process Flowcharts', help='Uploaded flowcharts for significant processes.', tracking=True)
    related_party_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_plan_rp_rel', 'phase_id', 'attachment_id',
        string='Related Party Schedules', help='Comprehensive related party listings.', tracking=True)
    checklist_engagement_letter = fields.Boolean(string='Engagement Letter Uploaded', tracking=True)
    checklist_entity_understanding = fields.Boolean(string='Entity Understanding Complete', tracking=True)
    checklist_fraud_brainstormed = fields.Boolean(string='Fraud Brainstorming Documented', tracking=True)
    checklist_analytics_performed = fields.Boolean(string='Analytical Procedures Completed', tracking=True)
    checklist_materiality_finalized = fields.Boolean(string='Materiality Finalized', tracking=True)
    checklist_controls_assessed = fields.Boolean(string='Internal Controls Assessed', tracking=True)
    checklist_risks_linked = fields.Boolean(string='Risks Linked to Audit Programs', tracking=True)
    checklist_strategy_signed = fields.Boolean(string='Audit Strategy Memo Approved', tracking=True)
    checklist_independence_confirmed = fields.Boolean(string='Independence Confirmed', tracking=True)
    checklist_partner_manager_review = fields.Boolean(string='Partner/Manager Review Evidenced', tracking=True)
    manager_signed_user_id = fields.Many2one('res.users', string='Manager Signature', tracking=True, copy=False, readonly=True)
    manager_signed_on = fields.Datetime(string='Manager Signed On', tracking=True, copy=False, readonly=True)
    partner_signed_user_id = fields.Many2one('res.users', string='Partner Signature', tracking=True, copy=False, readonly=True)
    partner_signed_on = fields.Datetime(string='Partner Signed On', tracking=True, copy=False, readonly=True)
    planning_complete = fields.Boolean(string='Planning Complete', default=False, tracking=True, copy=False)
    planning_completed_on = fields.Datetime(string='Planning Completed On', tracking=True, copy=False, readonly=True)
    can_finalize_planning = fields.Boolean(string='Can Finalize Planning', compute='_compute_can_finalize', store=True)
    missing_requirements_note = fields.Char(string='Outstanding Planning Requirements', compute='_compute_can_finalize', store=True)
    industry_id = fields.Many2one('qaco.industry', string='Industry', tracking=True)
    business_model = fields.Text(string='Business Model & Revenue Sources', tracking=True)
    organizational_structure = fields.Text(string='Organizational Structure', tracking=True)
    operational_locations = fields.Text(string='Operational Locations & Branches', tracking=True)
    key_contracts = fields.Text(string='Key Contractual Arrangements', tracking=True)
    applicable_regulators = fields.Many2many(
        'qaco.regulator', 'qaco_plan_phase_reg_rel', 'phase_id', 'regulator_id',
        string='Applicable Regulators', help='SECP, SBP, PEMRA, PRA, DRAP, etc.')
    regulatory_filings_status = fields.Selection([
        ('compliant', 'Fully Compliant'),
        ('pending', 'Some Filings Pending'),
        ('non_compliant', 'Non-Compliant'),
    ], string='Regulatory Filings Status', tracking=True)
    regulatory_penalties = fields.Text(string='Regulatory Penalties/Litigations', tracking=True)
    related_parties_summary = fields.Text(string='Related Parties Summary', tracking=True)
    group_structure = fields.Text(string='Group Structure', tracking=True)
    fraud_incentives = fields.Text(string='Incentives/Pressures for Fraud', tracking=True)
    fraud_opportunities = fields.Text(string='Opportunities for Fraud', tracking=True)
    fraud_attitudes = fields.Text(string='Attitudes/Rationalizations', tracking=True)
    prior_year_fs_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_plan_prior_fs_rel', 'phase_id', 'attachment_id',
        string='Prior Year Financial Statements')
    current_year_tb_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_plan_current_tb_rel', 'phase_id', 'attachment_id',
        string='Current Year Trial Balance')
    significant_fluctuations = fields.Text(string='Significant Fluctuations Analysis', tracking=True)
    ratio_analysis_summary = fields.Text(string='Ratio Analysis Summary', tracking=True)
    going_concern_assessment = fields.Text(string='Going Concern Assessment', tracking=True)
    materiality_benchmark = fields.Selection(MATERIALITY_BENCHMARKS, string='Materiality Benchmark', tracking=True)
    materiality_percentage = fields.Float(string='Materiality Percentage (%)', tracking=True)
    materiality_justification = fields.Text(string='Benchmark Selection Justification', tracking=True)
    overall_materiality = fields.Monetary(string='Overall Materiality', currency_field='company_currency_id')
    performance_materiality = fields.Monetary(string='Performance Materiality', currency_field='company_currency_id')
    clearly_trivial_threshold = fields.Monetary(string='Clearly Trivial Threshold', currency_field='company_currency_id')
    company_currency_id = fields.Many2one(
        'res.currency', string='Company Currency', default=lambda self: self.env.company.currency_id)
    control_environment_rating = fields.Selection(CONTROL_RATING, string='Control Environment', tracking=True)
    entity_level_controls_rating = fields.Selection(CONTROL_RATING, string='Entity-Level Controls', tracking=True)
    risk_assessment_rating = fields.Selection(CONTROL_RATING, string='Risk Assessment Process', tracking=True)
    itgc_rating = fields.Selection(CONTROL_RATING, string='IT General Controls', tracking=True)
    control_activities_rating = fields.Selection(CONTROL_RATING, string='Control Activities', tracking=True)
    monitoring_controls_rating = fields.Selection(CONTROL_RATING, string='Monitoring of Controls', tracking=True)
    reliance_on_controls = fields.Boolean(
        string='Planned Reliance on Controls', compute='_compute_reliance_strategy', store=False, readonly=True)
    control_assessment_summary = fields.Text(string='Control Assessment Summary', tracking=True)
    risk_register_line_ids = fields.One2many('qaco.risk.register.line', 'planning_phase_id', string='Risk Register')
    audit_approach = fields.Text(string='Overall Audit Approach', tracking=True)
    use_of_experts = fields.Boolean(string='Use of Experts Required', tracking=True)
    experts_details = fields.Text(string='Experts Scope & Details', tracking=True)
    use_of_caats = fields.Boolean(string='Use of CAATs/Data Analytics', tracking=True)
    caats_details = fields.Text(string='CAATs/Data Analytics Details', tracking=True)
    component_auditors_involved = fields.Boolean(string='Component Auditors Involved', tracking=True)
    component_auditors_details = fields.Text(string='Component Auditors Details', tracking=True)
    staffing_plan = fields.Text(string='Staffing Plan & Timelines', tracking=True)
    planning_memo_summary = fields.Text(string='Planning Memorandum Summary', tracking=True)
    materiality_worksheet_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_plan_materiality_rel', 'phase_id', 'attachment_id',
        string='Materiality Worksheets', tracking=True)
    analytical_summary_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_plan_analytics_rel', 'phase_id', 'attachment_id',
        string='Analytical Summary Sheets', tracking=True)
    risk_register_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_plan_risk_reg_rel', 'phase_id', 'attachment_id',
        string='Risk Register Files', tracking=True)
    audit_strategy_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_plan_strategy_rel', 'phase_id', 'attachment_id',
        string='Audit Strategy Documentation', tracking=True)
    internal_control_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_plan_control_rel', 'phase_id', 'attachment_id',
        string='Internal Control Documentation', tracking=True)

    @api.depends('audit_id', 'client_id')
    def _compute_name(self):
        for record in self:
            if record.client_id:
                record.name = f"Planning - {record.client_id.name}"
            else:
                record.name = "Planning Phase"

    @api.depends('control_environment_rating', 'control_activities_rating', 'itgc_rating')
    def _compute_reliance_strategy(self):
        for record in self:
            record.reliance_on_controls = (
                record.control_environment_rating in ('moderate', 'strong')
                and record.control_activities_rating in ('moderate', 'strong')
                and record.itgc_rating in ('moderate', 'strong')
            )

    @api.depends(
        'understanding_status', 'analytics_status', 'materiality_status', 'control_status',
        'risk_status', 'completion_status',
        'organogram_attachment_ids', 'engagement_letter_attachment_ids', 'board_minutes_attachment_ids',
        'process_flow_attachment_ids', 'related_party_attachment_ids',
        'checklist_engagement_letter', 'checklist_entity_understanding', 'checklist_fraud_brainstormed',
        'checklist_analytics_performed', 'checklist_materiality_finalized', 'checklist_controls_assessed',
        'checklist_risks_linked', 'checklist_strategy_signed', 'checklist_independence_confirmed',
        'checklist_partner_manager_review', 'manager_signed_user_id', 'partner_signed_user_id',
    )
    def _compute_can_finalize(self):
        for record in self:
            statuses_ready = all(getattr(record, field) == 'green' for field in record._STATUS_FIELDS)
            attachments_ready = all(getattr(record, field) for field in record._MANDATORY_ATTACHMENT_FIELDS)
            checklist_ready = all(getattr(record, field) for field in record._MANDATORY_CHECKLIST_FIELDS)
            signoffs_ready = bool(record.manager_signed_user_id and record.partner_signed_user_id)
            record.can_finalize_planning = statuses_ready and attachments_ready and checklist_ready and signoffs_ready
            pending = []
            if not statuses_ready:
                pending.append('Finalize all sub-tab traffic lights.')
            if not attachments_ready:
                pending.append('Upload every mandatory attachment.')
            if not checklist_ready:
                pending.append('Complete the master planning checklist.')
            if not signoffs_ready:
                pending.append('Obtain manager and partner e-signatures.')
            record.missing_requirements_note = '; '.join(pending) if pending else False

    @api.onchange('materiality_benchmark', 'materiality_percentage')
    def _compute_materiality_values(self):
        for record in self:
            if record.materiality_benchmark and record.materiality_percentage:
                benchmark_value = 0.0  # placeholder until financial data integration
                record.overall_materiality = benchmark_value * (record.materiality_percentage / 100.0)
                record.performance_materiality = record.overall_materiality * 0.75
                record.clearly_trivial_threshold = record.overall_materiality * 0.05

    def _ensure_statuses_green(self):
        self.ensure_one()
        if not all(getattr(self, field) == 'green' for field in self._STATUS_FIELDS):
            raise UserError('All planning sub-tabs must be marked green before sign-off.')

    def _validate_materiality_parameters(self):
        self.ensure_one()
        if not self.materiality_benchmark:
            raise UserError('Materiality benchmark must be selected.')
        if not self.materiality_justification:
            raise UserError('Justification for benchmark selection is mandatory.')
        if not self.materiality_percentage or self.materiality_percentage <= 0:
            raise UserError('Valid materiality percentage must be specified.')

    def action_manager_sign(self):
        self.ensure_one()
        self._ensure_statuses_green()
        self._validate_materiality_parameters()
        self.manager_signed_user_id = self.env.user
        self.manager_signed_on = fields.Datetime.now()

    def action_partner_sign(self):
        self.ensure_one()
        if not self.manager_signed_user_id:
            raise UserError('Manager must sign before the partner can sign.')
        self._ensure_statuses_green()
        self._validate_materiality_parameters()
        self.partner_signed_user_id = self.env.user
        self.partner_signed_on = fields.Datetime.now()

    def action_mark_planning_complete(self):
        self.ensure_one()
        if not self.can_finalize_planning:
            raise UserError(self.missing_requirements_note or 'Planning prerequisites are incomplete.')
        self._validate_materiality_parameters()
        if not self.risk_register_line_ids:
            raise UserError('Risk register must contain at least one identified risk.')
        self.planning_complete = True
        self.planning_completed_on = fields.Datetime.now()
        self.completion_status = 'green'

    def action_generate_planning_memo(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/qaco.planning.phase/{self.id}/planning_memo',
            'target': 'new',
        }

    @api.constrains('materiality_percentage')
    def _check_materiality_percentage(self):
        for record in self:
            if record.materiality_percentage and not (0 < record.materiality_percentage <= 100):
                raise ValidationError('Materiality percentage must be between 0 and 100.')

    @api.constrains('planning_complete')
    def _check_planning_complete_guard(self):
        for record in self:
            if record.planning_complete and not record.can_finalize_planning:
                raise ValidationError('Planning cannot be marked complete until every prerequisite is satisfied.')


class RiskRegisterLine(models.Model):
    _name = 'qaco.risk.register.line'
    _description = 'Risk Register Line'
    _order = 'risk_rating desc, sequence'

    planning_phase_id = fields.Many2one('qaco.planning.phase', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    account_cycle = fields.Char(string='Account/Cycle', required=True)
    risk_description = fields.Text(string='Risk Description', required=True)
    fs_level_risk = fields.Boolean(string='Financial Statement Level Risk')
    assertion_type = fields.Selection(PlanningPhase.ASSERTION_TYPES, string='Assertion Level Risk')
    risk_rating = fields.Selection(PlanningPhase.RISK_RATING, string='Risk Rating', required=True)
    is_significant_risk = fields.Boolean(string='Significant Risk')
    root_cause = fields.Text(string='Root Cause')
    impact_on_fs = fields.Text(string='Impact on Financial Statements')
    isa_240_risk = fields.Boolean(string='ISA 240 - Fraud Risk')
    isa_540_risk = fields.Boolean(string='ISA 540 - Accounting Estimates')
    isa_550_risk = fields.Boolean(string='ISA 550 - Related Parties')
    isa_570_risk = fields.Boolean(string='ISA 570 - Going Concern')
    planned_procedures = fields.Text(string='Planned Audit Procedures')
    link_to_audit_program = fields.Char(string='Link to Audit Program')


class Industry(models.Model):
    _name = 'qaco.industry'
    _description = 'Industry Classification'

    name = fields.Char(required=True)
    code = fields.Char(string='Industry Code')
    description = fields.Text(string='Description')
    common_risks = fields.Text(string='Common Industry Risks')


class Regulator(models.Model):
    _name = 'qaco.regulator'
    _description = 'Regulatory Body'

    name = fields.Char(required=True)
    code = fields.Char(string='Regulator Code')
    description = fields.Text(string='Description')
    website = fields.Char(string='Website')
    jurisdiction = fields.Selection([
        ('federal', 'Federal'),
        ('provincial', 'Provincial'),
        ('both', 'Federal & Provincial'),
    ], string='Jurisdiction')
