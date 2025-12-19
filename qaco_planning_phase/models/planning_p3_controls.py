# -*- coding: utf-8 -*-
"""
P-3: Internal Control Understanding
Standard: ISA 315
Purpose: Document internal control design and implementation.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError


class PlanningP3Controls(models.Model):
    """P-3: Internal Control Understanding (ISA 315)"""
    _name = 'qaco.planning.p3.controls'
    _description = 'P-3: Understanding Internal Control & IT Environment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    TAB_STATE = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
    ]

    CONTROL_RATING = [
        ('none', '❌ Does Not Exist'),
        ('weak', '🔴 Weak'),
        ('moderate', '🟡 Moderate'),
        ('strong', '🟢 Strong'),
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

    # ===== Control Environment (COSO Component 1) =====
    control_environment_rating = fields.Selection(
        CONTROL_RATING,
        string='Control Environment Rating',
        required=True,
        tracking=True
    )
    control_environment_assessment = fields.Html(
        string='Control Environment Assessment',
        help='Integrity, ethical values, management philosophy, organizational structure'
    )
    tone_at_top = fields.Html(
        string='Tone at the Top',
        help='Management\'s commitment to integrity and ethical values'
    )
    organizational_structure = fields.Html(
        string='Organizational Structure & Authority',
        help='Assignment of authority and responsibility'
    )
    hr_policies = fields.Html(
        string='Human Resource Policies',
        help='Competence, performance evaluation, training'
    )

    # ===== Risk Assessment Process (COSO Component 2) =====
    risk_assessment_process_rating = fields.Selection(
        CONTROL_RATING,
        string='Risk Assessment Process Rating',
        required=True,
        tracking=True
    )
    risk_assessment_process = fields.Html(
        string='Risk Assessment Process',
        help='Entity\'s process for identifying and responding to business risks'
    )
    risk_identification = fields.Html(
        string='Risk Identification Procedures'
    )
    risk_evaluation = fields.Html(
        string='Risk Evaluation & Response'
    )

    # ===== Information System (COSO Component 3) =====
    information_system_rating = fields.Selection(
        CONTROL_RATING,
        string='Information System Rating',
        required=True,
        tracking=True
    )
    information_system_overview = fields.Html(
        string='Information System Overview',
        help='Information systems relevant to financial reporting'
    )
    accounting_system = fields.Html(
        string='Accounting System',
        help='Chart of accounts, general ledger, sub-ledgers'
    )
    transaction_cycles = fields.Html(
        string='Transaction Cycles',
        help='Revenue, purchases, payroll, inventory, etc.'
    )
    journal_entry_process = fields.Html(
        string='Journal Entry Process',
        help='Non-standard journal entries and period-end adjustments'
    )
    financial_reporting = fields.Html(
        string='Financial Reporting Process',
        help='Preparation of financial statements'
    )

    # ===== IT General Controls (ITGCs) =====
    itgc_rating = fields.Selection(
        CONTROL_RATING,
        string='IT General Controls Rating',
        required=True,
        tracking=True
    )
    it_environment = fields.Html(
        string='IT Environment',
        help='Hardware, software, networks, applications'
    )
    access_controls = fields.Html(
        string='Access Controls',
        help='Logical and physical access security'
    )
    program_change_controls = fields.Html(
        string='Program Change Controls',
        help='Application change management'
    )
    it_operations = fields.Html(
        string='IT Operations',
        help='Data backup, recovery, job scheduling'
    )
    system_development = fields.Html(
        string='System Development & Acquisition'
    )
    cybersecurity = fields.Html(
        string='Cybersecurity Controls'
    )

    # ===== Control Activities (COSO Component 4) =====
    control_activities_rating = fields.Selection(
        CONTROL_RATING,
        string='Control Activities Rating',
        required=True,
        tracking=True
    )
    control_activities_assessment = fields.Html(
        string='Control Activities Assessment',
        help='Policies and procedures addressing business and fraud risks'
    )
    authorization_controls = fields.Html(
        string='Authorization Controls'
    )
    segregation_of_duties = fields.Html(
        string='Segregation of Duties'
    )
    reconciliation_controls = fields.Html(
        string='Reconciliation Controls'
    )
    physical_controls = fields.Html(
        string='Physical Controls'
    )

    # ===== Monitoring Controls (COSO Component 5) =====
    monitoring_controls_rating = fields.Selection(
        CONTROL_RATING,
        string='Monitoring Controls Rating',
        required=True,
        tracking=True
    )
    monitoring_assessment = fields.Html(
        string='Monitoring Assessment',
        help='How entity monitors controls on an ongoing basis'
    )
    internal_audit_function = fields.Selection([
        ('none', 'No Internal Audit'),
        ('weak', 'Weak Internal Audit'),
        ('moderate', 'Moderate Internal Audit'),
        ('strong', 'Strong Internal Audit'),
    ], string='Internal Audit Function', tracking=True)
    internal_audit_assessment = fields.Html(
        string='Internal Audit Assessment',
        help='Objectivity, competence, scope of work'
    )
    audit_committee = fields.Html(
        string='Audit Committee Oversight'
    )
    external_communications = fields.Html(
        string='External Communications',
        help='Reports from regulators, external parties'
    )

    # ===== Walkthrough Documentation =====
    walkthroughs_performed = fields.Boolean(
        string='Walkthroughs Performed',
        tracking=True
    )
    revenue_cycle_walkthrough = fields.Html(
        string='Revenue Cycle Walkthrough'
    )
    purchases_cycle_walkthrough = fields.Html(
        string='Purchases Cycle Walkthrough'
    )
    payroll_cycle_walkthrough = fields.Html(
        string='Payroll Cycle Walkthrough'
    )
    other_walkthroughs = fields.Html(
        string='Other Cycle Walkthroughs'
    )

    # ===== Control Reliance =====
    reliance_on_controls = fields.Boolean(
        string='Planned Reliance on Controls',
        compute='_compute_reliance_strategy',
        store=True,
        readonly=True
    )
    controls_to_test = fields.Html(
        string='Controls Identified for Testing',
        help='Controls where we plan to rely on for substantive testing reduction'
    )
    reliance_rationale = fields.Html(
        string='Reliance Rationale'
    )

    # ===== Deficiencies Identified =====
    deficiencies_identified = fields.Html(
        string='Control Deficiencies Identified',
        help='Significant deficiencies and material weaknesses'
    )
    management_communication = fields.Html(
        string='Communication to Management',
        help='Deficiencies to be communicated to management and TCWG'
    )

    # ===== Attachments =====
    internal_control_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p3_internal_control_rel',
        'p3_id',
        'attachment_id',
        string='Internal Control Documentation'
    )
    walkthrough_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p3_walkthrough_rel',
        'p3_id',
        'attachment_id',
        string='Walkthrough Documentation'
    )
    process_flow_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p3_process_flow_rel',
        'p3_id',
        'attachment_id',
        string='Process Flowcharts'
    )

    # ===== Summary Outputs =====
    internal_control_summary = fields.Html(
        string='Internal Control Summary',
        help='Design effectiveness conclusion per ISA 315'
    )
    overall_control_assessment = fields.Selection([
        ('ineffective', '🔴 Ineffective - Substantive Only'),
        ('partially_effective', '🟡 Partially Effective - Limited Reliance'),
        ('effective', '🟢 Effective - Controls Reliance Possible'),
    ], string='Overall Control Assessment', tracking=True)
    isa_reference = fields.Char(
        string='ISA Reference',
        default='ISA 315',
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
        ('audit_unique', 'UNIQUE(audit_id)', 'Only one P-3 record per Audit Engagement is allowed.')
    ]

    @api.depends('audit_id', 'client_id')
    def _compute_name(self):
        for record in self:
            if record.client_id:
                record.name = f"P3-{record.client_id.name[:15]}"
            else:
                record.name = 'P-3: Internal Controls'

    @api.depends('control_environment_rating', 'control_activities_rating', 'itgc_rating')
    def _compute_reliance_strategy(self):
        for record in self:
            record.reliance_on_controls = (
                record.control_environment_rating in ['moderate', 'strong']
                and record.control_activities_rating in ['moderate', 'strong']
                and record.itgc_rating in ['moderate', 'strong']
            )

    def _validate_mandatory_fields(self):
        """Validate mandatory fields before completing P-3."""
        self.ensure_one()
        errors = []
        if not self.control_environment_rating:
            errors.append('Control environment rating is required')
        if not self.itgc_rating:
            errors.append('IT general controls rating is required')
        if not self.control_activities_rating:
            errors.append('Control activities rating is required')
        if not self.overall_control_assessment:
            errors.append('Overall control assessment is required')
        if not self.internal_control_summary:
            errors.append('Internal control summary is required')
        if errors:
            raise UserError('Cannot complete P-3. Missing requirements:\n• ' + '\n• '.join(errors))

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
