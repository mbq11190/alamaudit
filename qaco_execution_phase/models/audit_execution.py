# -*- coding: utf-8 -*-
"""Standalone audit execution domain models."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AuditExecution(models.Model):
    _name = 'audit.execution'
    _description = 'Comprehensive Audit Execution'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence asc'

    name = fields.Char(
        string='Execution Reference',
        required=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('audit.execution') or 'New',
    )
    sequence = fields.Integer(string='Sequence', default=10)
    client_id = fields.Many2one('res.partner', string='Client', required=True, domain=[('is_company', '=', True)])
    audit_lead_id = fields.Many2one('res.users', string='Audit Lead', default=lambda self: self.env.user)
    date_start = fields.Date(string='Start Date', default=fields.Date.today)
    date_end = fields.Date(string='End Date')
    fiscal_year = fields.Char(string='Fiscal Year', compute='_compute_fiscal_year', store=True)
    account_head_id = fields.Many2one('account.account', string='Head of Account', required=True, domain=[('deprecated', '=', False)])
    account_code = fields.Char(string='Account Code', related='account_head_id.code', store=True)
    nature = fields.Selection([
        ('revenue', 'Revenue'),
        ('expense', 'Expense'),
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
    ], string='Nature', required=True, compute='_compute_nature', store=True)
    assertion_ids = fields.Many2many('audit.assertion', string='Assertions', required=True)
    risk_rating = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('significant', 'Significant'),
    ], string='Risk Rating', required=True, default='medium')
    significant_risk = fields.Boolean(string='Significant Risk', default=False)
    risk_description = fields.Html(string='Risk Description', placeholder='<p>Describe the specific risks associated with this account...</p>')
    relying_on_controls = fields.Boolean(string='Relying on Entity Controls', default=False)
    control_design_effective = fields.Boolean(string='Control Design Effective')
    control_operating_effective = fields.Boolean(string='Control Operating Effective')
    coverage_percentage = fields.Float(string='Coverage %', compute='_compute_coverage_percentage')
    fully_tested = fields.Boolean(string='Fully Tested', compute='_compute_fully_tested', store=True)
    total_population_amount = fields.Float(string='Total Population Amount', digits=(16, 2))
    tested_amount = fields.Float(string='Tested Amount', digits=(16, 2))
    tested_percentage = fields.Float(string='Tested %', compute='_compute_tested_percentage')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('under_review', 'Under Review'),
        ('completed', 'Completed'),
    ], string='Status', default='draft', tracking=True)
    overall_progress = fields.Float(string='Overall Progress', compute='_compute_overall_progress')
    audit_procedure_ids = fields.One2many('audit.procedure.detail', 'execution_id', string='Audit Procedures')
    test_of_controls_ids = fields.One2many('test.of.controls.detail', 'execution_id', string='Test of Controls')
    test_of_details_ids = fields.One2many('test.of.details.detail', 'execution_id', string='Test of Details')
    analytical_procedure_ids = fields.One2many('analytical.procedure.detail', 'execution_id', string='Analytical Procedures')
    evidence_ids = fields.One2many('audit.evidence.detail', 'execution_id', string='Evidences')

    @api.depends('date_start')
    def _compute_fiscal_year(self):
        for record in self:
            if record.date_start:
                date_value = fields.Date.to_date(record.date_start)
                record.fiscal_year = str(date_value.year) if date_value else False
            else:
                record.fiscal_year = False

    @api.depends('account_head_id')
    def _compute_nature(self):
        mapping = {
            'income': 'revenue',
            'expense': 'expense',
            'asset': 'asset',
            'liability': 'liability',
            'equity': 'equity',
        }
        for record in self:
            record.nature = mapping.get(record.account_head_id.user_type_id.type, False) if record.account_head_id else False

    @api.depends('tested_amount', 'total_population_amount')
    def _compute_tested_percentage(self):
        for record in self:
            if record.total_population_amount:
                record.tested_percentage = (record.tested_amount / record.total_population_amount) * 100
            else:
                record.tested_percentage = 0.0

    @api.depends('tested_percentage')
    def _compute_coverage_percentage(self):
        for record in self:
            record.coverage_percentage = record.tested_percentage

    @api.depends('tested_percentage')
    def _compute_fully_tested(self):
        for record in self:
            record.fully_tested = record.tested_percentage >= 95.0

    @api.depends('state', 'audit_procedure_ids', 'audit_procedure_ids.is_completed')
    def _compute_overall_progress(self):
        for record in self:
            if record.state == 'completed':
                record.overall_progress = 100.0
            elif record.state == 'in_progress' and record.audit_procedure_ids:
                total = len(record.audit_procedure_ids)
                completed = len(record.audit_procedure_ids.filtered(lambda proc: proc.is_completed))
                record.overall_progress = (completed / total) * 100 if total else 0.0
            else:
                record.overall_progress = 0.0

    @api.constrains('total_population_amount', 'tested_amount')
    def _check_amounts(self):
        for record in self:
            if record.total_population_amount < 0 or record.tested_amount < 0:
                raise ValidationError('Amounts cannot be negative.')
            if record.total_population_amount and record.tested_amount > record.total_population_amount:
                raise ValidationError('Tested amount cannot exceed total population amount.')

    def action_start_execution(self):
        self.write({'state': 'in_progress'})

    def action_mark_review(self):
        self.write({'state': 'under_review'})

    def action_complete_execution(self):
        self.write({'state': 'completed'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})


class AuditAssertion(models.Model):
    _name = 'audit.assertion'
    _description = 'Audit Assertions'
    _order = 'sequence asc'

    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string='Assertion', required=True)
    code = fields.Char(string='Code', required=True)
    description = fields.Text(string='Description')
    color = fields.Integer(string='Color Index')

    _sql_constraints = [
        ('unique_assertion_code', 'UNIQUE(code)', 'Assertion code must be unique!'),
    ]


class AuditProcedureDetail(models.Model):
    _name = 'audit.procedure.detail'
    _description = 'Detailed Audit Procedure'
    _order = 'sequence asc'

    name = fields.Char(
        string='Reference',
        required=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('audit.procedure.detail') or 'New',
    )
    sequence = fields.Integer(string='Sequence', default=10)
    execution_id = fields.Many2one('audit.execution', string='Audit Execution', required=True, ondelete='cascade')
    procedure_template_id = fields.Many2one('audit.procedure.template', string='Procedure Template', required=True)
    procedure_name = fields.Char(string='Procedure Name', related='procedure_template_id.name', store=True)
    procedure_description = fields.Html(string='Description', related='procedure_template_id.description', store=True)
    procedure_type = fields.Selection(
        string='Procedure Type', related='procedure_template_id.procedure_type', store=True)
    custom_description = fields.Html(string='Custom Description')
    risk_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Risk Level', default='medium')
    is_completed = fields.Boolean(string='Completed')
    performed_by = fields.Many2one('res.users', string='Performed By')
    performed_date = fields.Date(string='Performed Date')
    notes = fields.Html(string='Procedure Notes')
    result = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('unsatisfactory', 'Unsatisfactory'),
        ('not_applicable', 'Not Applicable'),
    ], string='Result')
    findings = fields.Html(string='Findings')


class AuditProcedureTemplate(models.Model):
    _name = 'audit.procedure.template'
    _description = 'Audit Procedure Templates'
    _order = 'sequence asc'

    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string='Procedure Name', required=True)
    code = fields.Char(string='Procedure Code', required=True)
    description = fields.Html(string='Description')
    procedure_type = fields.Selection([
        ('risk_assessment', 'Risk Assessment'),
        ('test_of_controls', 'Test of Controls'),
        ('substantive', 'Substantive Procedure'),
        ('analytical', 'Analytical Procedure'),
    ], string='Procedure Type', required=True)
    nature_applicable = fields.Selection([
        ('revenue', 'Revenue'),
        ('expense', 'Expense'),
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('all', 'All'),
    ], string='Applicable Nature', default='all')
    assertion_ids = fields.Many2many('audit.assertion', string='Applicable Assertions')

    _sql_constraints = [
        ('unique_procedure_code', 'UNIQUE(code)', 'Procedure code must be unique!'),
    ]


class TestOfControlsDetail(models.Model):
    _name = 'test.of.controls.detail'
    _description = 'Detailed Test of Controls'
    _order = 'sequence asc'

    name = fields.Char(
        string='Reference',
        required=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('test.controls.detail') or 'New',
    )
    sequence = fields.Integer(string='Sequence', default=10)
    execution_id = fields.Many2one('audit.execution', string='Audit Execution', required=True, ondelete='cascade')
    control_objective = fields.Char(string='Control Objective', required=True)
    control_activity = fields.Html(string='Control Activity', required=True)
    control_owner = fields.Char(string='Control Owner')
    frequency = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
    ], string='Frequency', required=True)
    sample_size = fields.Integer(string='Sample Size')
    sample_method = fields.Selection([
        ('random', 'Random Sampling'),
        ('systematic', 'Systematic Sampling'),
        ('judgmental', 'Judgmental Sampling'),
    ], string='Sampling Method')
    exceptions_found = fields.Integer(string='Exceptions Found')
    deviation_rate = fields.Float(string='Deviation Rate', compute='_compute_deviation_rate')
    control_effective = fields.Boolean(string='Control Effective')
    test_result = fields.Selection([
        ('effective', 'Effective'),
        ('partially_effective', 'Partially Effective'),
        ('ineffective', 'Ineffective'),
    ], string='Test Result')
    notes = fields.Html(string='Testing Notes')

    @api.depends('sample_size', 'exceptions_found')
    def _compute_deviation_rate(self):
        for record in self:
            if record.sample_size:
                record.deviation_rate = (record.exceptions_found / record.sample_size) * 100
            else:
                record.deviation_rate = 0.0


class TestOfDetailsDetail(models.Model):
    _name = 'test.of.details.detail'
    _description = 'Detailed Test of Details'
    _order = 'sequence asc'

    name = fields.Char(
        string='Reference',
        required=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('test.details.detail') or 'New',
    )
    sequence = fields.Integer(string='Sequence', default=10)
    execution_id = fields.Many2one('audit.execution', string='Audit Execution', required=True, ondelete='cascade')
    test_objective = fields.Char(string='Test Objective', required=True)
    assertion_tested = fields.Many2many('audit.assertion', string='Assertions Tested', required=True)
    population_size = fields.Integer(string='Population Size')
    sample_size = fields.Integer(string='Sample Size')
    sampling_method = fields.Selection([
        ('random', 'Random Sampling'),
        ('systematic', 'Systematic Sampling'),
        ('monetary', 'Monetary Unit Sampling'),
        ('haphazard', 'Haphazard Sampling'),
    ], string='Sampling Method')
    population_amount = fields.Float(string='Population Amount', digits=(16, 2))
    sample_amount = fields.Float(string='Sample Amount', digits=(16, 2))
    coverage_percentage = fields.Float(string='Coverage %', compute='_compute_coverage_percentage')
    exceptions_found = fields.Integer(string='Exceptions Found')
    test_result = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('unsatisfactory', 'Unsatisfactory'),
    ], string='Test Result')
    conclusion = fields.Html(string='Conclusion')

    @api.depends('population_amount', 'sample_amount')
    def _compute_coverage_percentage(self):
        for record in self:
            if record.population_amount:
                record.coverage_percentage = (record.sample_amount / record.population_amount) * 100
            else:
                record.coverage_percentage = 0.0


class AnalyticalProcedureDetail(models.Model):
    _name = 'analytical.procedure.detail'
    _description = 'Detailed Analytical Procedure'
    _order = 'sequence asc'

    name = fields.Char(
        string='Reference',
        required=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('analytical.procedure.detail') or 'New',
    )
    sequence = fields.Integer(string='Sequence', default=10)
    execution_id = fields.Many2one('audit.execution', string='Audit Execution', required=True, ondelete='cascade')
    procedure_description = fields.Html(string='Procedure Description', required=True)
    procedure_type = fields.Selection([
        ('ratio', 'Ratio Analysis'),
        ('trend', 'Trend Analysis'),
        ('comparison', 'Comparison Analysis'),
        ('reasonableness', 'Reasonableness Test'),
    ], string='Procedure Type', required=True)
    current_year_amount = fields.Float(string='Current Year Amount', digits=(16, 2))
    previous_year_amount = fields.Float(string='Previous Year Amount', digits=(16, 2))
    budget_amount = fields.Float(string='Budget Amount', digits=(16, 2))
    industry_average = fields.Float(string='Industry Average', digits=(16, 2))
    variance_cy_py = fields.Float(string='Variance CY vs PY', compute='_compute_variances')
    variance_cy_budget = fields.Float(string='Variance CY vs Budget', compute='_compute_variances')
    variance_percentage = fields.Float(string='Variance %', compute='_compute_variances')
    expectation_met = fields.Boolean(string='Expectation Met')
    unusual_fluctuation = fields.Boolean(string='Unusual Fluctuation')
    investigation_required = fields.Boolean(string='Investigation Required')
    analysis_notes = fields.Html(string='Analysis Notes')
    follow_up_actions = fields.Html(string='Follow-up Actions')

    @api.depends('current_year_amount', 'previous_year_amount', 'budget_amount')
    def _compute_variances(self):
        for record in self:
            record.variance_cy_py = (record.current_year_amount - record.previous_year_amount) if record.previous_year_amount else 0.0
            record.variance_cy_budget = (record.current_year_amount - record.budget_amount) if record.budget_amount else 0.0
            if record.previous_year_amount:
                record.variance_percentage = ((record.current_year_amount - record.previous_year_amount) / record.previous_year_amount) * 100
            else:
                record.variance_percentage = 0.0


class AuditEvidenceDetail(models.Model):
    _name = 'audit.evidence.detail'
    _description = 'Detailed Audit Evidence'
    _order = 'sequence asc'

    sequence = fields.Integer(string='Sequence', default=10)
    execution_id = fields.Many2one('audit.execution', string='Audit Execution', required=True, ondelete='cascade')
    evidence_type = fields.Selection([
        ('physical', 'Physical Examination'),
        ('documentary', 'Documentary Evidence'),
        ('analytical', 'Analytical Evidence'),
        ('oral', 'Oral Evidence'),
        ('electronic', 'Electronic Evidence'),
        ('confirmation', 'External Confirmation'),
    ], string='Evidence Type', required=True)
    description = fields.Html(string='Description', required=True)
    reliability = fields.Selection([
        ('high', 'High Reliability'),
        ('medium', 'Medium Reliability'),
        ('low', 'Low Reliability'),
    ], string='Reliability', required=True)
    collected_by = fields.Many2one('res.users', string='Collected By', default=lambda self: self.env.user)
    collection_date = fields.Date(string='Collection Date', default=fields.Date.today)
    attachment_id = fields.Many2one('ir.attachment', string='Attachment')
    evidence_notes = fields.Html(string='Notes')
