# -*- coding: utf-8 -*-
"""
P-5: Materiality & Performance Materiality
Standard: ISA 320
Purpose: Establish quantitative benchmarks for audit.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class PlanningP5Materiality(models.Model):
    """P-5: Materiality & Performance Materiality (ISA 320)"""
    _name = 'qaco.planning.p5.materiality'
    _description = 'P-5: Materiality & Performance Materiality'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    TAB_STATE = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
    ]

    MATERIALITY_BENCHMARKS = [
        ('pbt', 'Profit Before Tax (PBT)'),
        ('revenue', 'Revenue/Turnover'),
        ('assets', 'Total Assets'),
        ('equity', 'Equity'),
        ('expenses', 'Total Expenses'),
        ('custom', 'Custom Benchmark'),
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

    # ===== Materiality Status & Workflow (ISA 320) =====
    materiality_finalized = fields.Boolean(
        string='Materiality Finalized',
        tracking=True,
        help='Indicates whether materiality has been finalized and approved'
    )
    revision_required = fields.Boolean(
        string='Revision Required',
        tracking=True,
        help='Flag raised by reviewer/partner requiring revision of materiality'
    )

    # ===== Benchmark Selection =====
    materiality_benchmark = fields.Selection(
        MATERIALITY_BENCHMARKS,
        string='Materiality Benchmark',
        required=True,
        tracking=True,
        help='Select the appropriate benchmark per ISA 320'
    )
    # XML view compatible alias
    benchmark_type = fields.Selection(
        MATERIALITY_BENCHMARKS,
        string='Benchmark Type',
        related='materiality_benchmark',
        store=True
    )
    benchmark_amount = fields.Monetary(
        string='Benchmark Amount',
        currency_field='currency_id',
        tracking=True,
        help='The amount of the selected benchmark'
    )
    custom_benchmark_description = fields.Char(
        string='Custom Benchmark Description',
        help='Description if using custom benchmark'
    )
    custom_benchmark_value = fields.Monetary(
        string='Custom Benchmark Value',
        currency_field='currency_id'
    )

    # ===== Benchmark Justification =====
    benchmark_selection_justification = fields.Html(
        string='Benchmark Selection Justification',
        required=True,
        help='Document why this benchmark is appropriate for the entity per ISA 320'
    )
    # XML view compatible alias
    benchmark_rationale = fields.Html(
        string='Benchmark Rationale',
        related='benchmark_selection_justification',
        readonly=False
    )
    alternative_benchmarks = fields.Html(
        string='Alternative Benchmarks Considered',
        help='Document alternative benchmarks that were considered'
    )
    user_focus_factors = fields.Html(
        string='User Focus Factors',
        help='Factors indicating what users focus on (key metrics, regulatory requirements)'
    )
    # XML view compatible alias
    user_base_analysis = fields.Html(
        string='User Base Analysis',
        related='user_focus_factors',
        readonly=False
    )

    # ===== Materiality Percentage & Calculation =====
    materiality_percentage = fields.Float(
        string='Materiality Percentage (%)',
        required=True,
        default=5.0,
        tracking=True,
        help='Percentage to apply to benchmark (typically 1-10%)'
    )
    percentage_justification = fields.Html(
        string='Percentage Justification',
        help='Justify the selected percentage within the acceptable range'
    )
    # XML view compatible alias
    percentage_rationale = fields.Html(
        string='Percentage Rationale',
        related='percentage_justification',
        readonly=False
    )

    # ===== Calculated Materiality Values =====
    overall_materiality = fields.Monetary(
        string='Overall Materiality (OM)',
        currency_field='currency_id',
        compute='_compute_materiality_values',
        store=True,
        tracking=True,
        help='Overall materiality for the financial statements as a whole'
    )
    
    performance_materiality_pct = fields.Float(
        string='Performance Materiality %',
        default=75.0,
        help='Percentage of overall materiality (typically 50-75%)'
    )
    performance_materiality = fields.Monetary(
        string='Performance Materiality (PM)',
        currency_field='currency_id',
        compute='_compute_materiality_values',
        store=True,
        tracking=True,
        help='Materiality for individual transactions/balances'
    )
    performance_materiality_justification = fields.Html(
        string='Performance Materiality Justification',
        help='Factors considered in determining PM %'
    )
    # XML view compatible aliases for performance materiality
    pm_factors_considered = fields.Html(
        string='PM Factors Considered',
        help='Factors considered in determining performance materiality'
    )
    pm_justification = fields.Html(
        string='PM Justification',
        related='performance_materiality_justification',
        readonly=False
    )

    trivial_threshold_pct = fields.Float(
        string='Clearly Trivial Threshold %',
        default=5.0,
        help='Percentage of overall materiality (typically 3-5%)'
    )
    clearly_trivial_threshold = fields.Monetary(
        string='Clearly Trivial Threshold',
        currency_field='currency_id',
        compute='_compute_materiality_values',
        store=True,
        tracking=True,
        help='Threshold below which misstatements are clearly trivial'
    )
    # XML view compatible alias
    trivial_threshold = fields.Monetary(
        string='Trivial Threshold',
        related='clearly_trivial_threshold',
        store=True
    )
    sad_threshold = fields.Monetary(
        string='Summary of Audit Differences Threshold',
        currency_field='currency_id',
        help='Threshold for accumulating misstatements'
    )
    threshold_justification = fields.Html(
        string='Threshold Justification',
        help='Justification for trivial and SAD thresholds'
    )

    # ===== Specific Materiality (if applicable) =====
    specific_materiality_required = fields.Boolean(
        string='Specific Materiality Required',
        help='Are there classes/balances requiring lower materiality?'
    )
    specific_materiality_ids = fields.One2many(
        'qaco.planning.p5.specific.materiality',
        'p5_materiality_id',
        string='Specific Materiality Items'
    )
    specific_materiality_narrative = fields.Html(
        string='Specific Materiality Narrative',
        help='Narrative explanation for specific materiality items'
    )

    # ===== Qualitative Factors =====
    qualitative_factors = fields.Html(
        string='Qualitative Factors Considered',
        help='Qualitative factors that may affect materiality judgments'
    )
    regulatory_considerations = fields.Html(
        string='Regulatory Considerations',
        help='Regulatory factors affecting materiality'
    )
    sensitive_items = fields.Html(
        string='Sensitive Items',
        help='Items that are sensitive to users regardless of amount'
    )

    # ===== Materiality Considerations / Prior Year Comparison =====
    prior_year_materiality = fields.Monetary(
        string='Prior Year Materiality',
        currency_field='currency_id'
    )
    materiality_change_pct = fields.Float(
        string='Materiality Change %',
        compute='_compute_materiality_change',
        store=True,
        help='Percentage change from prior year materiality'
    )
    prior_year_comparison = fields.Html(
        string='Prior Year Comparison',
        help='Narrative comparison with prior year materiality'
    )
    materiality_change_explanation = fields.Html(
        string='Materiality Change Explanation',
        help='Explain any significant change from prior year'
    )

    # ===== Revision Log =====
    materiality_revision_ids = fields.One2many(
        'qaco.planning.p5.revision',
        'p5_materiality_id',
        string='Materiality Revisions'
    )
    # XML view compatible alias
    revision_line_ids = fields.One2many(
        'qaco.planning.p5.revision',
        'p5_materiality_id',
        string='Revision Lines'
    )
    revision_notes = fields.Html(
        string='Revision Notes',
        help='Latest revision notes'
    )
    is_revised = fields.Boolean(
        string='Has Been Revised',
        default=False,
        tracking=True
    )
    revision_date = fields.Date(
        string='Last Revision Date',
        tracking=True
    )
    revision_reason = fields.Html(
        string='Revision Reason'
    )

    # ===== Partner Approval =====
    partner_materiality_approved = fields.Boolean(
        string='Partner Approved Materiality',
        tracking=True
    )
    partner_approval_date = fields.Datetime(
        string='Partner Approval Date',
        tracking=True
    )
    partner_approval_user_id = fields.Many2one(
        'res.users',
        string='Partner Who Approved',
        tracking=True
    )

    # ===== Attachments =====
    materiality_worksheet_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p5_materiality_worksheet_rel',
        'p5_id',
        'attachment_id',
        string='Materiality Worksheets'
    )
    supporting_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p5_supporting_rel',
        'p5_id',
        'attachment_id',
        string='Supporting Documents'
    )
    # XML view compatible alias
    materiality_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p5_materiality_attach_rel',
        'p5_id',
        'attachment_id',
        string='Materiality Calculation Workpapers'
    )

    # ===== Summary =====
    materiality_summary = fields.Html(
        string='Materiality Summary',
        help='Consolidated summary of materiality determination'
    )
    isa_reference = fields.Char(
        string='ISA Reference',
        default='ISA 320',
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
        ('audit_unique', 'UNIQUE(audit_id)', 'Only one P-5 record per Audit Engagement is allowed.')
    ]

    @api.depends('audit_id', 'client_id')
    def _compute_name(self):
        for record in self:
            if record.client_id:
                record.name = f"P5-{record.client_id.name[:15]}"
            else:
                record.name = 'P-5: Materiality'

    @api.depends(
        'materiality_benchmark', 'benchmark_amount', 'custom_benchmark_value',
        'materiality_percentage', 'performance_materiality_pct', 'trivial_threshold_pct'
    )
    def _compute_materiality_values(self):
        for record in self:
            # Determine benchmark value
            if record.materiality_benchmark == 'custom':
                base_value = record.custom_benchmark_value or 0
            else:
                base_value = record.benchmark_amount or 0

            # Calculate overall materiality
            if base_value and record.materiality_percentage:
                record.overall_materiality = base_value * (record.materiality_percentage / 100.0)
            else:
                record.overall_materiality = 0

            # Calculate performance materiality
            if record.overall_materiality and record.performance_materiality_pct:
                record.performance_materiality = record.overall_materiality * (record.performance_materiality_pct / 100.0)
            else:
                record.performance_materiality = 0

            # Calculate trivial threshold
            if record.overall_materiality and record.trivial_threshold_pct:
                record.clearly_trivial_threshold = record.overall_materiality * (record.trivial_threshold_pct / 100.0)
            else:
                record.clearly_trivial_threshold = 0

    @api.depends('overall_materiality', 'prior_year_materiality')
    def _compute_materiality_change(self):
        """Compute the percentage change from prior year materiality."""
        for record in self:
            if record.prior_year_materiality and record.prior_year_materiality != 0:
                record.materiality_change_pct = (
                    (record.overall_materiality - record.prior_year_materiality) 
                    / record.prior_year_materiality
                ) * 100
            else:
                record.materiality_change_pct = 0

    def _validate_mandatory_fields(self):
        """Validate mandatory fields before completing P-5."""
        self.ensure_one()
        errors = []
        if not self.materiality_benchmark:
            errors.append('Materiality benchmark must be selected')
        if not self.benchmark_amount and self.materiality_benchmark != 'custom':
            errors.append('Benchmark amount must be specified')
        if self.materiality_benchmark == 'custom' and not self.custom_benchmark_value:
            errors.append('Custom benchmark value is required when using custom benchmark')
        if not self.benchmark_selection_justification:
            errors.append('Benchmark selection justification is mandatory per ISA 320')
        if not self.materiality_percentage or self.materiality_percentage <= 0:
            errors.append('Valid materiality percentage must be specified')
        if not self.partner_materiality_approved:
            errors.append('Partner must approve materiality determination')
        if errors:
            raise UserError('Cannot complete P-5. Missing requirements:\n• ' + '\n• '.join(errors))

    @api.constrains('materiality_percentage')
    def _check_materiality_percentage(self):
        for record in self:
            if record.materiality_percentage and not (0.1 <= record.materiality_percentage <= 20):
                raise ValidationError('Materiality percentage should typically be between 0.1% and 20% as per ISA guidance.')

    @api.constrains('performance_materiality_pct')
    def _check_pm_percentage(self):
        for record in self:
            if record.performance_materiality_pct and not (25 <= record.performance_materiality_pct <= 90):
                raise ValidationError('Performance materiality percentage should typically be between 25% and 90% of overall materiality.')

    def action_partner_approve_materiality(self):
        """Partner approves materiality determination."""
        for record in self:
            record.partner_materiality_approved = True
            record.partner_approval_date = fields.Datetime.now()
            record.partner_approval_user_id = self.env.user

    def action_revise_materiality(self):
        """Revise materiality (creates revision log entry)."""
        self.ensure_one()
        # Create revision log entry
        self.env['qaco.planning.p5.revision'].create({
            'p5_materiality_id': self.id,
            'revision_date': fields.Date.today(),
            'previous_overall_materiality': self.overall_materiality,
            'previous_performance_materiality': self.performance_materiality,
            'revised_by_id': self.env.user.id,
        })
        self.is_revised = True
        self.revision_date = fields.Date.today()
        # Reset partner approval for revised materiality
        self.partner_materiality_approved = False
        self.partner_approval_date = False
        self.partner_approval_user_id = False

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


class PlanningP5SpecificMateriality(models.Model):
    """Specific Materiality for particular classes/balances."""
    _name = 'qaco.planning.p5.specific.materiality'
    _description = 'Specific Materiality Item'
    _order = 'sequence, id'

    p5_materiality_id = fields.Many2one(
        'qaco.planning.p5.materiality',
        string='P-5 Materiality',
        required=True,
        ondelete='cascade'
    )
    sequence = fields.Integer(string='Sequence', default=10)
    class_or_balance = fields.Char(
        string='Class/Balance/Disclosure',
        required=True
    )
    # XML view compatible alias
    account_area = fields.Char(
        string='Account Area',
        related='class_or_balance',
        readonly=False
    )
    specific_materiality_amount = fields.Monetary(
        string='Specific Materiality',
        currency_field='currency_id'
    )
    # XML view compatible alias
    specific_amount = fields.Monetary(
        string='Specific Amount',
        related='specific_materiality_amount',
        readonly=False
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='p5_materiality_id.currency_id'
    )
    justification = fields.Text(
        string='Justification',
        required=True,
        help='Why lower materiality is appropriate for this item'
    )
    # XML view compatible alias
    rationale = fields.Text(
        string='Rationale',
        related='justification',
        readonly=False
    )


class PlanningP5Revision(models.Model):
    """Materiality Revision Log."""
    _name = 'qaco.planning.p5.revision'
    _description = 'Materiality Revision Log'
    _order = 'revision_date desc, id desc'

    p5_materiality_id = fields.Many2one(
        'qaco.planning.p5.materiality',
        string='P-5 Materiality',
        required=True,
        ondelete='cascade'
    )
    revision_date = fields.Date(
        string='Revision Date',
        required=True
    )
    previous_overall_materiality = fields.Monetary(
        string='Previous Overall Materiality',
        currency_field='currency_id'
    )
    # XML view compatible alias
    previous_materiality = fields.Monetary(
        string='Previous Materiality',
        related='previous_overall_materiality',
        readonly=False
    )
    previous_performance_materiality = fields.Monetary(
        string='Previous Performance Materiality',
        currency_field='currency_id'
    )
    new_overall_materiality = fields.Monetary(
        string='Revised Overall Materiality',
        currency_field='currency_id'
    )
    # XML view compatible alias
    revised_materiality = fields.Monetary(
        string='Revised Materiality',
        related='new_overall_materiality',
        readonly=False
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='p5_materiality_id.currency_id'
    )
    revision_reason = fields.Text(
        string='Reason for Revision',
        required=True
    )
    revised_by_id = fields.Many2one(
        'res.users',
        string='Revised By',
        required=True
    )
