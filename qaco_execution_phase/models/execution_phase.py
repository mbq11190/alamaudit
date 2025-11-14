from odoo import models, fields, api
from datetime import datetime


class QacoExecutionPhase(models.Model):
    _name = 'qaco.execution.phase'
    _description = 'Audit Execution Phase'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Basic Information
    audit_id = fields.Many2one('qaco.audit', string='Audit', required=True, ondelete='cascade',
                               tracking=True)
    client_name = fields.Char(related='audit_id.client_id.name', string='Client', readonly=True)
    audit_year = fields.Many2many(related='audit_id.audit_year', string='Audit Year', readonly=True)
    
    # Fieldwork Details
    fieldwork_start_date = fields.Date(string='Fieldwork Start Date', tracking=True)
    fieldwork_end_date = fields.Date(string='Fieldwork End Date', tracking=True)
    fieldwork_location = fields.Selection([
        ('client_office', 'Client Office'),
        ('our_office', 'Our Office'),
        ('remote', 'Remote'),
        ('hybrid', 'Hybrid')
    ], string='Fieldwork Location', default='client_office', tracking=True)
    fieldwork_address = fields.Text(string='Fieldwork Address')
    
    # Team Assignment
    execution_lead = fields.Many2one('hr.employee', string='Execution Lead', 
                                     domain="[('designation_id.name', '=', 'Manager')]",
                                     tracking=True)
    senior_auditors = fields.Many2many('hr.employee', 'execution_senior_rel', 
                                       string='Senior Auditors',
                                       domain="[('designation_id.name', 'in', ['Senior', 'Assistant Manager'])]")
    audit_assistants = fields.Many2many('hr.employee', 'execution_assistant_rel',
                                        string='Audit Assistants',
                                        domain="[('designation_id.name', 'in', ['Junior', 'Article'])]")
    
    # Testing Categories and Procedures
    testing_category = fields.Many2one('execution.testing.category', string='Primary Testing Category')
    testing_procedures = fields.Html(string='Testing Procedures')
    substantive_tests_completed = fields.Boolean(string='Substantive Tests Completed', tracking=True)
    control_tests_completed = fields.Boolean(string='Control Tests Completed', tracking=True)
    analytical_procedures_completed = fields.Boolean(string='Analytical Procedures Completed', tracking=True)
    
    # Testing Checklist
    test_cash_bank = fields.Boolean(string='Cash & Bank')
    test_receivables = fields.Boolean(string='Accounts Receivable')
    test_inventory = fields.Boolean(string='Inventory')
    test_fixed_assets = fields.Boolean(string='Fixed Assets')
    test_payables = fields.Boolean(string='Accounts Payable')
    test_revenue = fields.Boolean(string='Revenue')
    test_expenses = fields.Boolean(string='Expenses')
    test_payroll = fields.Boolean(string='Payroll')
    test_tax = fields.Boolean(string='Taxation')
    test_equity = fields.Boolean(string='Equity')
    test_other = fields.Boolean(string='Other Areas')
    test_other_description = fields.Char(string='Other Areas Description')
    
    # Sample Selection
    sample_size = fields.Integer(string='Sample Size')
    sample_selection_method = fields.Selection([
        ('random', 'Random Sampling'),
        ('systematic', 'Systematic Sampling'),
        ('stratified', 'Stratified Sampling'),
        ('judgmental', 'Judgmental Sampling'),
        ('monetary_unit', 'Monetary Unit Sampling')
    ], string='Sample Selection Method')
    sample_notes = fields.Text(string='Sample Selection Notes')
    
    # Evidence Collection
    evidence_obtained = fields.Integer(string='Evidence Documents Obtained', compute='_compute_evidence_count')
    evidence_quality = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('satisfactory', 'Satisfactory'),
        ('needs_improvement', 'Needs Improvement')
    ], string='Evidence Quality Rating')
    evidence_notes = fields.Html(string='Evidence Collection Notes')
    
    # Findings and Observations
    findings_count = fields.Integer(string='Number of Findings', compute='_compute_findings_count')
    significant_findings = fields.Html(string='Significant Findings')
    control_deficiencies = fields.Html(string='Control Deficiencies')
    misstatements_identified = fields.Boolean(string='Misstatements Identified', tracking=True)
    misstatement_amount = fields.Monetary(string='Total Misstatement Amount', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                  default=lambda self: self.env.company.currency_id)
    
    # Working Papers
    working_papers_complete = fields.Boolean(string='Working Papers Complete', tracking=True)
    working_papers_reviewed = fields.Boolean(string='Working Papers Reviewed', tracking=True)
    reviewer_id = fields.Many2one('hr.employee', string='Reviewed By',
                                  domain="[('designation_id.name', 'in', ['Manager', 'Partner'])]")
    review_date = fields.Date(string='Review Date')
    review_notes = fields.Html(string='Review Notes')
    
    # Time Tracking
    budgeted_hours = fields.Float(string='Budgeted Hours')
    actual_hours = fields.Float(string='Actual Hours Spent')
    hours_variance = fields.Float(string='Hours Variance', compute='_compute_hours_variance', store=True)
    hours_variance_percentage = fields.Float(string='Variance %', compute='_compute_hours_variance', store=True)
    
    # Client Interaction
    client_contact_person = fields.Char(string='Client Contact Person')
    client_cooperation_level = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('satisfactory', 'Satisfactory'),
        ('poor', 'Poor')
    ], string='Client Cooperation Level')
    access_issues = fields.Boolean(string='Access Issues Encountered')
    access_issues_description = fields.Text(string='Access Issues Description')
    
    # Progress Tracking
    completion_percentage = fields.Float(string='Completion %', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('fieldwork', 'Fieldwork in Progress'),
        ('testing', 'Testing in Progress'),
        ('review', 'Under Review'),
        ('completed', 'Completed')
    ], string='Status', default='draft', tracking=True)
    
    # Documentation
    execution_notes = fields.Html(string='Execution Notes')
    execution_attachments = fields.Many2many('ir.attachment', 'execution_attachment_rel',
                                            string='Attachments (Working Papers, Evidence, etc.)')
    
    # Audit Trail
    create_date = fields.Datetime(string='Created On', readonly=True)
    create_uid = fields.Many2one('res.users', string='Created By', readonly=True)
    write_date = fields.Datetime(string='Last Updated', readonly=True)
    write_uid = fields.Many2one('res.users', string='Last Updated By', readonly=True)

    @api.depends('budgeted_hours', 'actual_hours')
    def _compute_hours_variance(self):
        for record in self:
            if record.budgeted_hours:
                record.hours_variance = record.actual_hours - record.budgeted_hours
                record.hours_variance_percentage = (record.hours_variance / record.budgeted_hours) * 100
            else:
                record.hours_variance = 0
                record.hours_variance_percentage = 0

    def _compute_evidence_count(self):
        for record in self:
            record.evidence_obtained = len(record.execution_attachments)

    def _compute_findings_count(self):
        for record in self:
            # Count based on HTML content presence
            count = 0
            if record.significant_findings and record.significant_findings.strip():
                count += 1
            if record.control_deficiencies and record.control_deficiencies.strip():
                count += 1
            record.findings_count = count

    def action_start_fieldwork(self):
        """Start fieldwork phase"""
        self.ensure_one()
        self.write({
            'state': 'fieldwork',
            'fieldwork_start_date': fields.Date.today()
        })

    def action_start_testing(self):
        """Move to testing phase"""
        self.ensure_one()
        self.state = 'testing'

    def action_submit_review(self):
        """Submit for review"""
        self.ensure_one()
        self.state = 'review'

    def action_complete(self):
        """Mark execution as complete"""
        self.ensure_one()
        self.write({
            'state': 'completed',
            'completion_percentage': 100.0
        })

    def action_back_to_draft(self):
        """Back to draft"""
        self.ensure_one()
        self.state = 'draft'


class ExecutionTestingCategory(models.Model):
    _name = 'execution.testing.category'
    _description = 'Testing Category'
    _order = 'sequence, name'

    name = fields.Char(string='Category Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
