from odoo import models, fields, api
from datetime import datetime


class QacoFinalisationPhase(models.Model):
    _name = 'qaco.finalisation.phase'
    _description = 'Audit Finalisation Phase'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Basic Information
    audit_id = fields.Many2one('qaco.audit', string='Audit', required=True, ondelete='cascade',
                               tracking=True)
    client_name = fields.Char(related='audit_id.client_id.name', string='Client', readonly=True)
    audit_year = fields.Many2many(related='audit_id.audit_year', string='Audit Year', readonly=True)
    
    # Report Drafting
    report_type = fields.Many2one('finalisation.report.type', string='Report Type', tracking=True)
    report_opinion = fields.Selection([
        ('unqualified', 'Unqualified/Unmodified'),
        ('qualified', 'Qualified'),
        ('adverse', 'Adverse'),
        ('disclaimer', 'Disclaimer of Opinion')
    ], string='Audit Opinion', tracking=True)
    report_draft_date = fields.Date(string='Draft Report Date')
    report_final_date = fields.Date(string='Final Report Date')
    report_issued_date = fields.Date(string='Report Issued Date', tracking=True)
    
    # Review Process
    draft_prepared_by = fields.Many2one('hr.employee', string='Draft Prepared By',
                                        domain="[('qaco_designation', 'in', ['Senior', 'Assistant Manager'])]")
    first_reviewer = fields.Many2one('hr.employee', string='First Reviewer (Manager)',
                                     domain="[('qaco_designation', '=', 'Manager')]",
                                     tracking=True)
    first_review_date = fields.Date(string='First Review Date')
    first_review_completed = fields.Boolean(string='First Review Complete', tracking=True)
    
    second_reviewer = fields.Many2one('hr.employee', string='Second Reviewer (Partner)',
                                      domain="[('qaco_designation', '=', 'Partner')]",
                                      tracking=True)
    second_review_date = fields.Date(string='Second Review Date')
    second_review_completed = fields.Boolean(string='Second Review Complete', tracking=True)
    
    # Quality Control
    quality_control_reviewer = fields.Many2one('hr.employee', string='Quality Control Reviewer',
                                               domain="[('qaco_designation', 'in', ['Partner', 'Director'])]")
    quality_control_date = fields.Date(string='QC Review Date')
    quality_control_completed = fields.Boolean(string='Quality Control Complete', tracking=True)
    quality_control_notes = fields.Html(string='QC Review Notes')
    
    # Key Matters
    emphasis_of_matter = fields.Boolean(string='Emphasis of Matter', tracking=True)
    emphasis_of_matter_description = fields.Html(string='Emphasis of Matter Description')
    other_matter = fields.Boolean(string='Other Matter', tracking=True)
    other_matter_description = fields.Html(string='Other Matter Description')
    key_audit_matters = fields.Html(string='Key Audit Matters (KAM)')
    
    # Adjustments
    adjustments_proposed = fields.Boolean(string='Adjustments Proposed', tracking=True)
    passed_adjustments = fields.Html(string='Passed Adjustments')
    waived_adjustments = fields.Html(string='Waived Adjustments')
    total_adjustment_amount = fields.Monetary(string='Total Adjustment Amount', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                  default=lambda self: self.env.company.currency_id)
    
    # Client Discussions
    exit_meeting_date = fields.Date(string='Exit Meeting Date', tracking=True)
    exit_meeting_attendees = fields.Text(string='Exit Meeting Attendees')
    client_concerns = fields.Html(string='Client Concerns/Questions')
    client_responses = fields.Html(string='Responses Provided')
    
    # Management Representation
    representation_letter_received = fields.Boolean(string='Representation Letter Received', tracking=True)
    representation_letter_date = fields.Date(string='Representation Letter Date')
    representation_letter_signatory = fields.Char(string='Signatory Name')
    representation_letter_title = fields.Char(string='Signatory Title')
    
    # Subsequent Events
    subsequent_events_review = fields.Boolean(string='Subsequent Events Reviewed', tracking=True)
    subsequent_events_date = fields.Date(string='Review Through Date')
    subsequent_events_notes = fields.Html(string='Subsequent Events Notes')
    
    # Going Concern
    going_concern_assessment = fields.Selection([
        ('no_concern', 'No Going Concern Issues'),
        ('disclosure', 'Disclosure Required'),
        ('substantial_doubt', 'Substantial Doubt')
    ], string='Going Concern Assessment')
    going_concern_notes = fields.Html(string='Going Concern Notes')
    
    # Deliverables
    audit_report_final = fields.Many2many('ir.attachment', 'finalisation_audit_report_rel',
                                         string='Final Audit Report')
    management_letter = fields.Many2many('ir.attachment', 'finalisation_mgmt_letter_rel',
                                        string='Management Letter')
    financial_statements = fields.Many2many('ir.attachment', 'finalisation_fin_stmt_rel',
                                           string='Audited Financial Statements')
    other_deliverables = fields.Many2many('ir.attachment', 'finalisation_other_del_rel',
                                         string='Other Deliverables')
    
    # Sign-off and Approval
    partner_signoff = fields.Boolean(string='Partner Sign-off', tracking=True)
    partner_signoff_date = fields.Date(string='Partner Sign-off Date')
    partner_signoff_name = fields.Many2one('hr.employee', string='Signing Partner',
                                          domain="[('qaco_designation', '=', 'Partner')]")
    
    # File Completion
    audit_file_complete = fields.Boolean(string='Audit File Complete', tracking=True)
    file_assembly_deadline = fields.Date(string='File Assembly Deadline')
    file_completion_date = fields.Date(string='File Completion Date')
    file_archived = fields.Boolean(string='File Archived', tracking=True)
    file_archive_date = fields.Date(string='Archive Date')
    file_archive_location = fields.Char(string='Archive Location')
    
    # Retention
    retention_period_years = fields.Integer(string='Retention Period (Years)', default=7)
    destruction_date = fields.Date(string='Scheduled Destruction Date', compute='_compute_destruction_date', store=True)
    
    # Independence Confirmation
    independence_confirmed = fields.Boolean(string='Independence Confirmed', tracking=True)
    independence_confirmation_date = fields.Date(string='Independence Confirmation Date')
    independence_notes = fields.Text(string='Independence Notes')
    
    # Completion Checklist
    checklist_workpapers_reviewed = fields.Boolean(string='Working Papers Reviewed')
    checklist_conclusions_documented = fields.Boolean(string='Conclusions Documented')
    checklist_differences_resolved = fields.Boolean(string='All Differences Resolved')
    checklist_schedules_complete = fields.Boolean(string='All Schedules Complete')
    checklist_cross_references = fields.Boolean(string='Cross-References Complete')
    checklist_supervision_documented = fields.Boolean(string='Supervision Documented')
    checklist_compliance_verified = fields.Boolean(string='Compliance Verified')
    checklist_all_complete = fields.Boolean(string='All Checklist Items Complete', 
                                           compute='_compute_checklist_complete', store=True)
    
    # Progress Tracking
    completion_percentage = fields.Float(string='Completion %', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('report_drafting', 'Report Drafting'),
        ('review', 'Under Review'),
        ('qc_review', 'QC Review'),
        ('client_discussion', 'Client Discussion'),
        ('signoff', 'Awaiting Sign-off'),
        ('completed', 'Completed'),
        ('archived', 'Archived')
    ], string='Status', default='draft', tracking=True)
    
    # Documentation
    finalisation_notes = fields.Html(string='Finalisation Notes')
    finalisation_attachments = fields.Many2many('ir.attachment', 'finalisation_attachment_rel',
                                               string='Additional Attachments')
    
    # Audit Trail
    create_date = fields.Datetime(string='Created On', readonly=True)
    create_uid = fields.Many2one('res.users', string='Created By', readonly=True)
    write_date = fields.Datetime(string='Last Updated', readonly=True)
    write_uid = fields.Many2one('res.users', string='Last Updated By', readonly=True)

    @api.depends('file_completion_date', 'retention_period_years')
    def _compute_destruction_date(self):
        for record in self:
            if record.file_completion_date and record.retention_period_years:
                from dateutil.relativedelta import relativedelta
                record.destruction_date = record.file_completion_date + relativedelta(years=record.retention_period_years)
            else:
                record.destruction_date = False

    @api.depends('checklist_workpapers_reviewed', 'checklist_conclusions_documented',
                 'checklist_differences_resolved', 'checklist_schedules_complete',
                 'checklist_cross_references', 'checklist_supervision_documented',
                 'checklist_compliance_verified')
    def _compute_checklist_complete(self):
        for record in self:
            record.checklist_all_complete = all([
                record.checklist_workpapers_reviewed,
                record.checklist_conclusions_documented,
                record.checklist_differences_resolved,
                record.checklist_schedules_complete,
                record.checklist_cross_references,
                record.checklist_supervision_documented,
                record.checklist_compliance_verified
            ])

    def action_start_drafting(self):
        """Start report drafting"""
        self.ensure_one()
        self.write({
            'state': 'report_drafting',
            'report_draft_date': fields.Date.today()
        })

    def action_submit_review(self):
        """Submit for review"""
        self.ensure_one()
        self.state = 'review'

    def action_submit_qc(self):
        """Submit for QC review"""
        self.ensure_one()
        self.state = 'qc_review'

    def action_client_discussion(self):
        """Move to client discussion"""
        self.ensure_one()
        self.state = 'client_discussion'

    def action_awaiting_signoff(self):
        """Move to awaiting sign-off"""
        self.ensure_one()
        self.state = 'signoff'

    def action_complete(self):
        """Mark finalisation as complete"""
        self.ensure_one()
        self.write({
            'state': 'completed',
            'completion_percentage': 100.0,
            'report_issued_date': fields.Date.today()
        })

    def action_archive_file(self):
        """Archive the audit file"""
        self.ensure_one()
        self.write({
            'state': 'archived',
            'file_archived': True,
            'file_archive_date': fields.Date.today()
        })

    def action_back_to_draft(self):
        """Back to draft"""
        self.ensure_one()
        self.state = 'draft'


class FinalisationReportType(models.Model):
    _name = 'finalisation.report.type'
    _description = 'Audit Report Type'
    _order = 'sequence, name'

    name = fields.Char(string='Report Type', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
