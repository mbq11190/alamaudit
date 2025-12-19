# -*- coding: utf-8 -*-
"""
P-11: Group Audit Planning (If Applicable)
Standard: ISA 600
Purpose: Plan group audit strategy.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError


class PlanningP11GroupAudit(models.Model):
    """P-11: Group Audit Planning (ISA 600)"""
    _name = 'qaco.planning.p11.group.audit'
    _description = 'P-11: Group Audit Planning'
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

    # ===== Applicability =====
    is_group_audit = fields.Boolean(
        string='Is Group Audit',
        tracking=True,
        help='Does this audit involve group audit considerations?'
    )
    not_applicable_reason = fields.Html(
        string='Reason Not Applicable',
        help='Document why group audit is not applicable'
    )
    # XML view compatible alias
    not_applicable_rationale = fields.Html(
        string='Not Applicable Rationale',
        related='not_applicable_reason',
        readonly=False
    )

    # ===== Group Structure =====
    group_structure = fields.Html(
        string='Group Structure',
        help='Document the group structure and components'
    )
    # XML view compatible aliases
    group_structure_overview = fields.Html(
        string='Group Structure Overview',
        related='group_structure',
        readonly=False
    )
    group_chart = fields.Html(
        string='Group Chart',
        help='Visual representation of group structure'
    )
    parent_company = fields.Char(
        string='Parent Company Name'
    )
    consolidation_method = fields.Html(
        string='Consolidation Method',
        help='Method used to consolidate group financial statements'
    )
    # XML view compatible alias
    consolidation_process = fields.Html(
        string='Consolidation Process',
        related='consolidation_method',
        readonly=False
    )

    # ===== Components =====
    component_line_ids = fields.One2many(
        'qaco.planning.p11.component.line',
        'p11_group_audit_id',
        string='Components'
    )
    # XML view compatible alias
    component_ids = fields.One2many(
        'qaco.component.line',
        'p11_group_audit_id',
        string='Component Register'
    )
    significant_component_count = fields.Integer(
        string='Significant Components',
        compute='_compute_component_counts',
        store=True
    )
    total_component_count = fields.Integer(
        string='Total Components',
        compute='_compute_component_counts',
        store=True
    )
    # XML view compatible alias
    component_count = fields.Integer(
        string='Component Count',
        related='total_component_count',
        store=True
    )

    # ===== Significance Assessment (XML compatible) =====
    significance_criteria = fields.Html(
        string='Significance Criteria',
        help='Criteria for determining component significance'
    )
    significant_components = fields.Html(
        string='Significant Components Assessment',
        help='Assessment of significant components'
    )
    non_significant_components = fields.Html(
        string='Non-Significant Components Assessment',
        help='Assessment of non-significant components'
    )
    coverage_assessment = fields.Html(
        string='Coverage Assessment',
        help='Assessment of audit coverage'
    )

    # ===== Component Auditors =====
    component_auditors_involved = fields.Boolean(
        string='Component Auditors Involved',
        tracking=True
    )
    component_auditor_assessment = fields.Html(
        string='Component Auditor Assessment',
        help='Assessment of component auditor competence and independence per ISA 600.19'
    )
    # XML view compatible alias
    auditor_assessment = fields.Html(
        string='Auditor Assessment',
        related='component_auditor_assessment',
        readonly=False
    )
    # XML view compatible - component auditor register
    component_auditor_ids = fields.One2many(
        'qaco.component.auditor.line',
        'p11_group_audit_id',
        string='Component Auditors'
    )
    component_auditor_access = fields.Boolean(
        string='Access to Component Auditor Work',
        help='Do we have unrestricted access to component auditor work papers?'
    )
    access_restrictions = fields.Html(
        string='Access Restrictions',
        help='Document any restrictions on access'
    )

    # ===== Component Materiality =====
    group_materiality = fields.Monetary(
        string='Group Materiality',
        currency_field='currency_id'
    )
    component_materiality_approach = fields.Html(
        string='Component Materiality Approach',
        help='Approach for determining component materiality per ISA 600.21'
    )
    component_pm = fields.Monetary(
        string='Component Performance Materiality',
        currency_field='currency_id'
    )
    # XML view compatible alias
    component_pm_threshold = fields.Monetary(
        string='Component PM Threshold',
        related='component_pm',
        readonly=False
    )
    threshold_for_aggregation = fields.Monetary(
        string='Threshold for Aggregation',
        currency_field='currency_id',
        help='Threshold for misstatements communicated to group team'
    )
    # XML view compatible
    aggregation_risk = fields.Html(
        string='Aggregation Risk',
        help='Assessment of aggregation risk'
    )

    # ===== Instructions to Component Auditors =====
    instructions_issued = fields.Boolean(
        string='Instructions Issued',
        tracking=True
    )
    instructions_date = fields.Date(
        string='Instructions Date'
    )
    instructions_content = fields.Html(
        string='Instructions Content',
        help='Key contents of instructions per ISA 600.40'
    )
    # XML view compatible alias
    group_audit_instructions = fields.Html(
        string='Group Audit Instructions',
        related='instructions_content',
        readonly=False
    )
    reporting_deadlines = fields.Html(
        string='Reporting Deadlines',
        help='Deadlines for component auditor reporting'
    )
    # XML view compatible alias
    reporting_requirements = fields.Html(
        string='Reporting Requirements',
        related='reporting_deadlines',
        readonly=False
    )
    specific_requirements = fields.Html(
        string='Specific Requirements',
        help='Specific work required from component auditors'
    )
    # XML view compatible
    communication_requirements = fields.Html(
        string='Communication Requirements',
        help='Communication requirements for component auditors'
    )

    # ===== Review Strategy =====
    review_strategy = fields.Html(
        string='Review Strategy',
        help='Strategy for reviewing component auditor work'
    )
    # XML view compatible alias
    component_work_review = fields.Html(
        string='Component Work Review',
        related='review_strategy',
        readonly=False
    )
    component_findings = fields.Html(
        string='Component Findings',
        help='Findings from component auditor work'
    )
    evidence_sufficiency = fields.Html(
        string='Evidence Sufficiency',
        help='Assessment of sufficiency of audit evidence'
    )
    site_visits_planned = fields.Boolean(
        string='Site Visits Planned'
    )
    site_visit_details = fields.Html(
        string='Site Visit Details'
    )
    file_reviews_planned = fields.Boolean(
        string='File Reviews Planned'
    )
    file_review_details = fields.Html(
        string='File Review Details'
    )

    # ===== Communication =====
    communication_plan = fields.Html(
        string='Communication Plan',
        help='Plan for communication with component auditors'
    )
    # XML view compatible alias
    component_communication = fields.Html(
        string='Component Communication',
        related='communication_plan',
        readonly=False
    )
    group_management_communication = fields.Html(
        string='Group Management Communication',
        help='Communication with group management'
    )
    tcwg_communication = fields.Html(
        string='Communication to TCWG',
        help='Communication to those charged with governance'
    )
    significant_matters = fields.Html(
        string='Significant Matters to Communicate'
    )

    # ===== Consolidation Procedures =====
    consolidation_procedures = fields.Html(
        string='Consolidation Procedures',
        help='Planned procedures on consolidation process'
    )
    intercompany_elimination = fields.Html(
        string='Intercompany Elimination Review'
    )
    # XML view compatible alias
    intercompany_eliminations = fields.Html(
        string='Intercompany Eliminations',
        related='intercompany_elimination',
        readonly=False
    )
    subsequent_events = fields.Html(
        string='Subsequent Events',
        help='Subsequent events at component level'
    )
    uniform_policies = fields.Html(
        string='Uniform Accounting Policies',
        help='Assessment of uniform accounting policies'
    )

    # ===== Attachments =====
    group_structure_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p11_group_structure_rel',
        'p11_id',
        'attachment_id',
        string='Group Structure Documents'
    )
    instructions_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p11_instructions_rel',
        'p11_id',
        'attachment_id',
        string='Component Auditor Instructions'
    )
    # XML view compatible aliases
    group_audit_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p11_group_audit_rel',
        'p11_id',
        'attachment_id',
        string='Group Audit Documentation'
    )
    component_report_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p11_component_report_rel',
        'p11_id',
        'attachment_id',
        string='Component Reports'
    )

    # ===== Summary =====
    group_audit_summary = fields.Html(
        string='Group Audit Summary',
        help='Consolidated group audit planning summary per ISA 600'
    )
    # XML view compatible alias
    group_audit_conclusion = fields.Html(
        string='Group Audit Conclusion',
        related='group_audit_summary',
        readonly=False
    )
    isa_reference = fields.Char(
        string='ISA Reference',
        default='ISA 600',
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
        ('audit_unique', 'UNIQUE(audit_id)', 'Only one P-11 record per Audit Engagement is allowed.')
    ]

    @api.depends('audit_id', 'client_id')
    def _compute_name(self):
        for record in self:
            if record.client_id:
                record.name = f"P11-{record.client_id.name[:15]}"
            else:
                record.name = 'P-11: Group Audit'

    @api.depends('component_line_ids', 'component_line_ids.is_significant')
    def _compute_component_counts(self):
        for record in self:
            record.total_component_count = len(record.component_line_ids)
            record.significant_component_count = len(record.component_line_ids.filtered(lambda c: c.is_significant))

    def _validate_mandatory_fields(self):
        """Validate mandatory fields before completing P-11."""
        self.ensure_one()
        errors = []
        if self.is_group_audit:
            if not self.group_structure:
                errors.append('Group structure must be documented')
            if not self.component_line_ids:
                errors.append('Components must be identified')
            if self.component_auditors_involved and not self.component_auditor_assessment:
                errors.append('Component auditor assessment is required')
            if not self.group_audit_summary:
                errors.append('Group audit summary is required')
        elif not self.not_applicable_reason:
            errors.append('Reason for non-applicability must be documented')
        if errors:
            raise UserError('Cannot complete P-11. Missing requirements:\n• ' + '\n• '.join(errors))

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


class PlanningP11ComponentLine(models.Model):
    """Component Line Item for Group Audit."""
    _name = 'qaco.planning.p11.component.line'
    _description = 'Group Audit Component'
    _order = 'is_significant desc, name'

    p11_group_audit_id = fields.Many2one(
        'qaco.planning.p11.group.audit',
        string='P-11 Group Audit',
        required=True,
        ondelete='cascade'
    )
    name = fields.Char(
        string='Component Name',
        required=True
    )
    location = fields.Char(
        string='Location/Country'
    )
    consolidation_method = fields.Selection([
        ('full', 'Full Consolidation'),
        ('proportional', 'Proportional Consolidation'),
        ('equity', 'Equity Method'),
        ('not_consolidated', 'Not Consolidated'),
    ], string='Consolidation Method', required=True)
    is_significant = fields.Boolean(
        string='Significant Component',
        help='Is this a significant component per ISA 600.27?'
    )
    significance_reason = fields.Selection([
        ('individual_significance', 'Individual Financial Significance'),
        ('significant_risk', 'Likely to Include Significant Risks'),
        ('both', 'Both'),
    ], string='Reason for Significance')
    component_materiality = fields.Monetary(
        string='Component Materiality',
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='p11_group_audit_id.currency_id'
    )
    work_to_perform = fields.Selection([
        ('full_audit', 'Full Audit'),
        ('specified_procedures', 'Specified Procedures'),
        ('analytical_procedures', 'Analytical Procedures'),
        ('no_work', 'No Work Required'),
    ], string='Work to Perform')
    component_auditor = fields.Char(
        string='Component Auditor Firm'
    )
    component_auditor_independence = fields.Boolean(
        string='Independence Confirmed'
    )
    notes = fields.Text(string='Notes')


class ComponentLine(models.Model):
    """Component Line for XML view compatibility."""
    _name = 'qaco.component.line'
    _description = 'Component'
    _order = 'significance desc, component_name'

    p11_group_audit_id = fields.Many2one(
        'qaco.planning.p11.group.audit',
        string='P-11 Group Audit',
        required=True,
        ondelete='cascade'
    )
    component_name = fields.Char(
        string='Component Name',
        required=True
    )
    location = fields.Char(
        string='Location/Country'
    )
    significance = fields.Selection([
        ('significant', 'Significant'),
        ('non_significant', 'Non-Significant'),
    ], string='Significance', default='non_significant')
    type_of_work = fields.Selection([
        ('full_audit', 'Full Audit'),
        ('specified_procedures', 'Specified Procedures'),
        ('analytical_procedures', 'Analytical Procedures'),
        ('no_work', 'No Work Required'),
    ], string='Type of Work')
    component_auditor = fields.Char(
        string='Component Auditor'
    )
    component_materiality = fields.Monetary(
        string='Component Materiality',
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='p11_group_audit_id.currency_id'
    )
    reporting_deadline = fields.Date(
        string='Reporting Deadline'
    )
    status = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ], string='Status', default='pending')


class ComponentAuditorLine(models.Model):
    """Component Auditor Line for XML view compatibility."""
    _name = 'qaco.component.auditor.line'
    _description = 'Component Auditor'
    _order = 'auditor_name'

    p11_group_audit_id = fields.Many2one(
        'qaco.planning.p11.group.audit',
        string='P-11 Group Audit',
        required=True,
        ondelete='cascade'
    )
    auditor_name = fields.Char(
        string='Auditor Name',
        required=True
    )
    firm_name = fields.Char(
        string='Firm Name'
    )
    network_member = fields.Boolean(
        string='Network Member'
    )
    competence_assessment = fields.Selection([
        ('acceptable', 'Acceptable'),
        ('concerns', 'Concerns Identified'),
        ('not_assessed', 'Not Yet Assessed'),
    ], string='Competence Assessment')
    independence_confirmed = fields.Boolean(
        string='Independence Confirmed'
    )
    access_to_work = fields.Boolean(
        string='Access to Work Granted'
    )
    notes = fields.Text(string='Notes')
