# -*- coding: utf-8 -*-
"""
P-6: Risk Assessment (RMM - Risk of Material Misstatement)
Standard: ISA 315
Purpose: Identify and assess risks of material misstatement.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError


class PlanningP6Risk(models.Model):
    """P-6: Risk Assessment - RMM (ISA 315)"""
    _name = 'qaco.planning.p6.risk'
    _description = 'P-6: Risk Assessment (RMM)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    TAB_STATE = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
    ]

    RISK_RATING = [
        ('low', '🟢 Low'),
        ('medium', '🟡 Medium'),
        ('high', '🔴 High'),
    ]

    ASSERTION_TYPES = [
        ('existence', 'Existence/Occurrence'),
        ('completeness', 'Completeness'),
        ('accuracy', 'Accuracy'),
        ('valuation', 'Valuation/Allocation'),
        ('cutoff', 'Cut-off'),
        ('rights', 'Rights & Obligations'),
        ('classification', 'Classification'),
        ('presentation', 'Presentation & Disclosure'),
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

    # ===== Financial Statement Level Risks =====
    fs_level_risks = fields.Html(
        string='Financial Statement Level Risks',
        help='Pervasive risks affecting multiple assertions across the FS'
    )
    fs_level_risk_factors = fields.Html(
        string='FS-Level Risk Factors',
        help='Factors giving rise to FS-level risks'
    )
    fs_level_risk_response = fields.Html(
        string='Overall Response to FS-Level Risks',
        help='Planned overall response per ISA 330'
    )

    # ===== Risk Register (Assertion-Level) =====
    risk_register_line_ids = fields.One2many(
        'qaco.planning.p6.risk.line',
        'p6_risk_id',
        string='Risk Register - Assertion Level'
    )

    # ===== Inherent Risk Assessment =====
    inherent_risk_factors = fields.Html(
        string='Inherent Risk Factors',
        help='Factors affecting inherent risk across the entity'
    )
    complexity_factors = fields.Html(
        string='Complexity Factors',
        help='Transactions/events that are complex or involve significant judgment'
    )
    estimation_uncertainty = fields.Html(
        string='Estimation Uncertainty',
        help='Areas with significant estimation uncertainty'
    )
    subjectivity = fields.Html(
        string='Subjectivity Factors',
        help='Areas requiring significant management judgment'
    )
    change_factors = fields.Html(
        string='Change Factors',
        help='Significant changes in the entity affecting risk'
    )

    # ===== Control Risk Assessment =====
    control_risk_summary = fields.Html(
        string='Control Risk Summary',
        help='Summary of control risk assessment from P-3'
    )
    controls_reliance_planned = fields.Boolean(
        string='Controls Reliance Planned',
        help='Do we plan to rely on controls for any assertion?'
    )
    controls_to_test = fields.Html(
        string='Controls Identified for Testing'
    )

    # ===== Risk Heat Map =====
    high_risk_count = fields.Integer(
        string='High Risk Items',
        compute='_compute_risk_counts',
        store=True
    )
    medium_risk_count = fields.Integer(
        string='Medium Risk Items',
        compute='_compute_risk_counts',
        store=True
    )
    low_risk_count = fields.Integer(
        string='Low Risk Items',
        compute='_compute_risk_counts',
        store=True
    )
    significant_risk_count = fields.Integer(
        string='Significant Risks',
        compute='_compute_risk_counts',
        store=True
    )

    # ===== Significant Risks =====
    significant_risks_summary = fields.Html(
        string='Significant Risks Summary',
        help='Summary of all identified significant risks per ISA 315'
    )
    revenue_recognition_significant = fields.Boolean(
        string='Revenue Recognition - Significant Risk',
        default=True,
        help='ISA 240 presumption that revenue recognition is a significant risk'
    )
    management_override_significant = fields.Boolean(
        string='Management Override - Significant Risk',
        default=True,
        help='ISA 240 presumption of risk of management override of controls'
    )

    # ===== Link to Audit Procedures =====
    risk_response_strategy = fields.Html(
        string='Risk Response Strategy',
        help='How identified RMMs will be addressed in audit procedures'
    )
    link_to_audit_programs = fields.Html(
        string='Link to Audit Programs',
        help='Reference to specific audit programs addressing each risk'
    )

    # ===== Attachments =====
    risk_register_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p6_risk_register_rel',
        'p6_id',
        'attachment_id',
        string='Risk Register Files'
    )
    risk_matrix_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p6_risk_matrix_rel',
        'p6_id',
        'attachment_id',
        string='RMM Matrix'
    )

    # ===== Summary =====
    risk_assessment_summary = fields.Html(
        string='Risk Assessment Summary',
        help='Consolidated risk assessment per ISA 315'
    )
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
        ('audit_unique', 'UNIQUE(audit_id)', 'Only one P-6 record per Audit Engagement is allowed.')
    ]

    @api.depends('audit_id', 'client_id')
    def _compute_name(self):
        for record in self:
            if record.client_id:
                record.name = f"P6-{record.client_id.name[:15]}"
            else:
                record.name = 'P-6: Risk Assessment'

    @api.depends('risk_register_line_ids', 'risk_register_line_ids.risk_rating', 'risk_register_line_ids.is_significant_risk')
    def _compute_risk_counts(self):
        for record in self:
            record.high_risk_count = len(record.risk_register_line_ids.filtered(lambda r: r.risk_rating == 'high'))
            record.medium_risk_count = len(record.risk_register_line_ids.filtered(lambda r: r.risk_rating == 'medium'))
            record.low_risk_count = len(record.risk_register_line_ids.filtered(lambda r: r.risk_rating == 'low'))
            record.significant_risk_count = len(record.risk_register_line_ids.filtered(lambda r: r.is_significant_risk))

    def _validate_mandatory_fields(self):
        """Validate mandatory fields before completing P-6."""
        self.ensure_one()
        errors = []
        if not self.risk_register_line_ids:
            errors.append('Risk register must contain at least one identified risk')
        if not self.significant_risk_count and not self.risk_register_line_ids.filtered(lambda r: r.is_significant_risk):
            errors.append('At least one significant risk must be identified per ISA 315')
        if not self.risk_assessment_summary:
            errors.append('Risk assessment summary is required')
        if errors:
            raise UserError('Cannot complete P-6. Missing requirements:\n• ' + '\n• '.join(errors))

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


class PlanningP6RiskLine(models.Model):
    """Risk Register Line - Assertion Level Risks."""
    _name = 'qaco.planning.p6.risk.line'
    _description = 'Risk Register Line - Assertion Level'
    _order = 'risk_rating desc, sequence'
    _rec_name = 'risk_description'

    RISK_RATING = [
        ('low', '🟢 Low'),
        ('medium', '🟡 Medium'),
        ('high', '🔴 High'),
    ]

    ASSERTION_TYPES = [
        ('existence', 'Existence/Occurrence'),
        ('completeness', 'Completeness'),
        ('accuracy', 'Accuracy'),
        ('valuation', 'Valuation/Allocation'),
        ('cutoff', 'Cut-off'),
        ('rights', 'Rights & Obligations'),
        ('classification', 'Classification'),
        ('presentation', 'Presentation & Disclosure'),
    ]

    ACCOUNT_CYCLES = [
        ('revenue', 'Revenue & Receivables'),
        ('purchases', 'Purchases & Payables'),
        ('inventory', 'Inventory & Cost of Sales'),
        ('payroll', 'Payroll & Human Resources'),
        ('fixed_assets', 'Fixed Assets & Depreciation'),
        ('investments', 'Investments & Securities'),
        ('cash', 'Cash & Bank'),
        ('taxation', 'Taxation'),
        ('provisions', 'Provisions & Contingencies'),
        ('equity', 'Equity & Financing'),
        ('fs_level', 'Financial Statement Level'),
        ('other', 'Other'),
    ]

    p6_risk_id = fields.Many2one(
        'qaco.planning.p6.risk',
        string='P-6 Risk Assessment',
        required=True,
        ondelete='cascade'
    )
    sequence = fields.Integer(string='Sequence', default=10)

    # ===== Risk Identification =====
    account_cycle = fields.Selection(
        ACCOUNT_CYCLES,
        string='Account/Cycle',
        required=True
    )
    risk_description = fields.Text(
        string='Risk Description',
        required=True
    )
    assertion_type = fields.Selection(
        ASSERTION_TYPES,
        string='Assertion',
        required=True
    )
    fs_level_risk = fields.Boolean(
        string='FS-Level Risk',
        help='Is this a financial statement level risk?'
    )

    # ===== Risk Assessment =====
    inherent_risk = fields.Selection(
        RISK_RATING,
        string='Inherent Risk',
        required=True
    )
    control_risk = fields.Selection(
        RISK_RATING,
        string='Control Risk',
        required=True
    )
    risk_rating = fields.Selection(
        RISK_RATING,
        string='Combined RMM',
        compute='_compute_risk_rating',
        store=True
    )
    is_significant_risk = fields.Boolean(
        string='Significant Risk',
        tracking=True
    )

    # ===== Risk Factors =====
    risk_factors = fields.Text(
        string='Risk Factors',
        help='Factors contributing to this risk'
    )
    root_cause = fields.Text(string='Root Cause Analysis')
    impact_on_fs = fields.Text(string='Impact on Financial Statements')

    # ===== Likelihood & Magnitude =====
    likelihood = fields.Selection([
        ('remote', 'Remote'),
        ('possible', 'Possible'),
        ('probable', 'Probable'),
        ('likely', 'Likely'),
    ], string='Likelihood')
    magnitude = fields.Selection([
        ('immaterial', 'Immaterial'),
        ('material', 'Material'),
        ('significant', 'Significant'),
        ('critical', 'Critical'),
    ], string='Magnitude')

    # ===== ISA-Specific Flags =====
    isa_240_fraud_risk = fields.Boolean(string='ISA 240 - Fraud Risk')
    isa_540_estimate_risk = fields.Boolean(string='ISA 540 - Estimate Risk')
    isa_550_rp_risk = fields.Boolean(string='ISA 550 - Related Party Risk')
    isa_570_gc_risk = fields.Boolean(string='ISA 570 - Going Concern Risk')

    # ===== Planned Response =====
    planned_procedures = fields.Text(
        string='Planned Audit Procedures',
        help='Procedures to address this risk'
    )
    nature_of_procedures = fields.Selection([
        ('test_of_controls', 'Test of Controls'),
        ('substantive_analytical', 'Substantive Analytical'),
        ('test_of_details', 'Test of Details'),
        ('combination', 'Combination'),
    ], string='Nature of Procedures')
    timing_of_procedures = fields.Selection([
        ('interim', 'Interim'),
        ('year_end', 'Year-end'),
        ('both', 'Both Interim & Year-end'),
    ], string='Timing of Procedures')
    extent_of_procedures = fields.Text(string='Extent of Procedures')
    link_to_audit_program = fields.Char(string='Audit Program Reference')

    @api.depends('inherent_risk', 'control_risk')
    def _compute_risk_rating(self):
        """Compute combined RMM based on inherent and control risk."""
        risk_matrix = {
            ('high', 'high'): 'high',
            ('high', 'medium'): 'high',
            ('high', 'low'): 'medium',
            ('medium', 'high'): 'high',
            ('medium', 'medium'): 'medium',
            ('medium', 'low'): 'low',
            ('low', 'high'): 'medium',
            ('low', 'medium'): 'low',
            ('low', 'low'): 'low',
        }
        for record in self:
            key = (record.inherent_risk, record.control_risk)
            record.risk_rating = risk_matrix.get(key, 'medium')
