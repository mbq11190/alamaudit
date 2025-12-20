"""
P-6: Risk Assessment (RMM)
ISA 315/330/240/570/220/ISQM-1/Companies Act 2017/ICAP QCR/AOB
Court-defensible, fully integrated with planning workflow.
"""
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)

# =============================
# Parent Model: Risk Assessment
# =============================
class PlanningP6Risk(models.Model):
    _name = 'qaco.planning.p6.risk'
    _description = 'P-6: Risk Assessment (RMM)'
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
    risk_line_ids = fields.One2many('qaco.planning.p6.risk.line', 'p6_risk_id', string='Risk Register', required=True)
    fs_level_risk_desc = fields.Text(string='FS-Level Risk Description')
    fs_level_risk_nature = fields.Selection([
        ('fraud', 'Fraud'),
        ('error', 'Error'),
    ], string='Nature of Risk')
    fs_level_pervasive = fields.Boolean(string='Pervasive Impact?')
    fs_level_severity = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Risk Severity')
    fs_level_areas = fields.Char(string='Affected FS Areas')
    fs_level_checklist = fields.Boolean(string='FS-level risks identified?')
    fs_level_impact_checklist = fields.Boolean(string='Impact on audit approach considered?')
    # Section A: Risk Identification Sources (auto-display)
    sources_entity = fields.Boolean(string='Entity/Industry (P-2)', default=True, readonly=True)
    sources_controls = fields.Boolean(string='Internal Controls (P-3)', default=True, readonly=True)
    sources_analytics = fields.Boolean(string='Analytics (P-4)', default=True, readonly=True)
    sources_materiality = fields.Boolean(string='Materiality (P-5)', default=True, readonly=True)
    sources_prior_year = fields.Boolean(string='Prior-Year Issues', default=True, readonly=True)
    sources_fraud_brainstorm = fields.Boolean(string='Fraud Brainstorming', default=True, readonly=True)
    sources_checklist = fields.Boolean(string='All planning sources considered?')
    sources_no_isolation = fields.Boolean(string='No risk identified in isolation?')
    # Section J: Mandatory Document Uploads
    attachment_ids = fields.Many2many('ir.attachment', 'audit_p6_risk_attachment_rel', 'risk_id', 'attachment_id', string='Required Attachments', help='Risk register export, prior-year, management risk assessment')
    mandatory_upload_check = fields.Boolean(string='Mandatory uploads present?')
    # Section K: Conclusion & Professional Judgment
    conclusion_narrative = fields.Text(string='Conclusion Narrative', required=True, default="Risks of material misstatement at the financial-statement and assertion levels have been identified and assessed in accordance with ISA 315, considering inherent risk, control risk, fraud risks, and other relevant factors. The assessed risks provide an appropriate basis for designing further audit procedures.")
    significant_risks_confirmed = fields.Boolean(string='All significant risks identified?')
    rmm_assessed_confirmed = fields.Boolean(string='RMM appropriately assessed?')
    audit_response_basis_confirmed = fields.Boolean(string='Basis established for audit responses?')
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
    risk_memo_pdf = fields.Binary(string='Risk Assessment Memorandum (PDF)')
    risk_heat_map = fields.Binary(string='Risk Heat Map')
    risk_register_export = fields.Binary(string='Risk Register Export')
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
        self.message_post(body="P-6 prepared.")

    def action_review(self):
        self.state = 'reviewed'
        self.reviewed_by = self.env.user.id
        self.message_post(body="P-6 reviewed.")

    def action_partner_approve(self):
        if not self.partner_comments:
            raise ValidationError("Partner comments are mandatory for approval.")
        self.state = 'locked'
        self.partner_approved = True
        self.message_post(body="P-6 partner approved and locked.")

    @api.constrains('attachment_ids')
    def _check_mandatory_uploads(self):
        for rec in self:
            if not rec.attachment_ids:
                raise ValidationError("Mandatory risk assessment documents must be uploaded.")

    @api.constrains('risk_line_ids')
    def _check_risk_lines(self):
        for rec in self:
            if not rec.risk_line_ids:
                raise ValidationError("At least one risk line must be entered.")

    # Pre-conditions enforcement
    @api.model
    def create(self, vals):
        # Enforce P-5 locked, P-2/P-3/P-4 outputs present, materiality finalized
        audit = self.env['qaco.audit'].browse(vals.get('engagement_id'))
        planning = self.env['qaco.planning.main'].browse(vals.get('planning_main_id'))
        if not planning or not planning.p5_partner_locked:
            raise UserError("P-6 cannot be started until P-5 is partner-approved and locked.")
        # Add checks for P-2, P-3, P-4 outputs
        if not planning.p2_outputs_ready or not planning.p3_outputs_ready or not planning.p4_outputs_ready:
            raise UserError("P-6 requires outputs from P-2, P-3, and P-4.")
        return super().create(vals)

# =============================
# Child Model: Risk Line
# =============================
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
    # XML view compatible alias
    account_area = fields.Selection(
        ACCOUNT_CYCLES,
        string='Account Area',
        related='account_cycle',
        readonly=False
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
    # XML view compatible alias
    assertion = fields.Selection(
        string='Assertion',
        related='assertion_type',
        readonly=False
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
    # XML view compatible alias
    combined_rmm = fields.Selection(
        string='Combined RMM',
        related='risk_rating',
        store=True
    )
    is_significant_risk = fields.Boolean(
        string='Significant Risk',
        tracking=True
    )
    # XML view compatible alias
    significant_risk = fields.Boolean(
        string='Significant Risk',
        related='is_significant_risk',
        readonly=False
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
    # XML view compatible alias
    planned_response = fields.Text(
        string='Planned Response',
        related='planned_procedures',
        readonly=False
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

