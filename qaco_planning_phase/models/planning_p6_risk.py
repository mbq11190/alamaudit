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
class AuditPlanningP6RiskAssessment(models.Model):
    _name = 'audit.planning.p6.risk_assessment'
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
    risk_line_ids = fields.One2many('audit.planning.p6.risk_line', 'risk_assessment_id', string='Risk Register', required=True)
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
class AuditPlanningP6RiskLine(models.Model):
    _name = 'audit.planning.p6.risk_line'
    _description = 'P-6: Risk Register Line'
    _order = 'id desc'

    risk_assessment_id = fields.Many2one('audit.planning.p6.risk_assessment', string='Risk Assessment', required=True, ondelete='cascade', index=True)
    engagement_id = fields.Many2one('qaco.audit', string='Audit Engagement', required=True, ondelete='cascade', index=True)
    audit_year = fields.Many2one('qaco.audit.year', string='Audit Year', required=True, ondelete='cascade', index=True)
    fs_caption = fields.Char(string='FS Area', required=True)
    assertion = fields.Selection([
        ('existence', 'Existence/Occurrence'),
        ('completeness', 'Completeness'),
        ('accuracy', 'Accuracy'),
        ('valuation', 'Valuation'),
        ('rights_obligations', 'Rights & Obligations'),
        ('presentation', 'Presentation & Disclosure'),
    ], string='Assertion', required=True)
    risk_description = fields.Text(string='Risk Description', required=True)
    risk_source = fields.Selection([
        ('p2', 'P-2 Entity'),
        ('p3', 'P-3 Controls'),
        ('p4', 'P-4 Analytics'),
        ('p7', 'P-7 Fraud'),
        ('other', 'Other'),
    ], string='Source', required=True)
    inherent_risk = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Inherent Risk', required=True)
    control_risk = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Control Risk', required=True)
    rmm_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='RMM Level', compute='_compute_rmm_level', store=True)
    rmm_override = fields.Boolean(string='Override RMM?')
    rmm_override_justification = fields.Text(string='Override Justification')
    significant_risk = fields.Boolean(string='Significant Risk?')
    significant_basis = fields.Text(string='Basis for Significant Risk')
    substantive_required = fields.Boolean(string='Mandatory Substantive Procedures?')
    control_testing_permitted = fields.Boolean(string='Control Testing Permitted?', default=False)
    fraud_risk_present = fields.Boolean(string='Fraud Risk Present?')
    fraud_type = fields.Selection([
        ('revenue', 'Revenue Recognition'),
        ('override', 'Management Override'),
        ('misappropriation', 'Misappropriation of Assets'),
    ], string='Fraud Type')
    fraud_scenario = fields.Text(string='Specific Fraud Scenario')
    fraud_impacted_assertions = fields.Char(string='Impacted Assertions')
    going_concern_risk = fields.Boolean(string='Going Concern Risk?')
    going_concern_conditions = fields.Text(string='Conditions/Events')
    going_concern_fs_areas = fields.Char(string='Affected FS Areas')
    going_concern_disclosure_impact = fields.Text(string='Impact on Disclosures')
    controls_identified = fields.Boolean(string='Relevant Controls Identified?')
    control_reliance_planned = fields.Boolean(string='Control Reliance Planned?')
    control_deficiency_impact = fields.Text(string='Impact of Control Deficiencies')
    planned_response = fields.Selection([
        ('controls', 'Test of Controls'),
        ('substantive', 'Substantive Procedures Only'),
        ('combined', 'Combined Approach'),
    ], string='Planned Response')
    response_nature = fields.Text(string='Nature (What)')
    response_timing = fields.Char(string='Timing (When)')
    response_extent = fields.Char(string='Extent (How Much)')
    response_materiality_link = fields.Char(string='Link to Materiality Thresholds')
    heat_map_ir = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Heat Map IR')
    heat_map_cr = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Heat Map CR')
    heat_map_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Heat Map Level', compute='_compute_heat_map_level', store=True)
    # Audit trail
    change_log = fields.Text(string='Change Log')
    version_history = fields.Text(string='Version History')
    reviewer_timestamps = fields.Text(string='Reviewer Timestamps')

    @api.depends('inherent_risk', 'control_risk', 'rmm_override', 'rmm_override_justification')
    def _compute_rmm_level(self):
        for rec in self:
            if rec.rmm_override and rec.rmm_override_justification:
                # Partner override
                rec.rmm_level = self._override_rmm(rec.inherent_risk, rec.control_risk, rec.rmm_override_justification)
            else:
                # IR × CR logic
                rec.rmm_level = self._derive_rmm(rec.inherent_risk, rec.control_risk)

    def _derive_rmm(self, ir, cr):
        # Simple matrix logic for demonstration
        if ir == 'high' or cr == 'high':
            return 'high'
        elif ir == 'medium' or cr == 'medium':
            return 'medium'
        else:
            return 'low'

    def _override_rmm(self, ir, cr, justification):
        # Partner override logic
        if justification:
            return 'high' if ir == 'high' or cr == 'high' else 'medium'
        return self._derive_rmm(ir, cr)

    @api.depends('heat_map_ir', 'heat_map_cr')
    def _compute_heat_map_level(self):
        for rec in self:
            if rec.heat_map_ir == 'high' or rec.heat_map_cr == 'high':
                rec.heat_map_level = 'high'
            elif rec.heat_map_ir == 'medium' or rec.heat_map_cr == 'medium':
                rec.heat_map_level = 'medium'
            else:
                rec.heat_map_level = 'low'

    # Audit trail logic
    def write(self, vals):
        # Log changes for ICAP QCR/AOB
        self.message_post(body=f"Risk line updated: {vals}")
        return super().write(vals)

    def unlink(self):
        self.message_post(body="Risk line deleted.")
        return super().unlink()
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

    # ===== Overall Risk Assessment (ISA 315 Summary) =====
    overall_risk_level = fields.Selection([
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
    ], string='Overall Risk Level', tracking=True,
       help='Overall assessed risk of material misstatement')
    
    significant_risks_count = fields.Integer(
        string='Significant Risks Count',
        compute='_compute_significant_risks_count',
        store=True,
        help='Number of significant risks identified'
    )

    # ===== Financial Statement Level Risks =====
    fs_level_risks = fields.Html(
        string='Financial Statement Level Risks',
        help='Pervasive risks affecting multiple assertions across the FS'
    )
    pervasive_control_weaknesses = fields.Html(
        string='Pervasive Control Weaknesses',
        help='Control weaknesses affecting multiple areas'
    )
    entity_wide_risks = fields.Html(
        string='Entity-Wide Risks',
        help='Risks affecting the entity as a whole'
    )
    fs_level_risk_factors = fields.Html(
        string='FS-Level Risk Factors',
        help='Factors giving rise to FS-level risks'
    )
    fs_level_risk_response = fields.Html(
        string='Overall Response to FS-Level Risks',
        help='Planned overall response per ISA 330'
    )
    # XML view compatible alias
    fs_risk_responses = fields.Html(
        string='FS Risk Responses',
        related='fs_level_risk_response',
        readonly=False
    )

    # ===== Risk Register (Assertion-Level) =====
    risk_register_line_ids = fields.One2many(
        'qaco.planning.p6.risk.line',
        'p6_risk_id',
        string='Risk Register - Assertion Level'
    )
    # XML view compatible alias
    risk_register_ids = fields.One2many(
        'qaco.planning.p6.risk.line',
        'p6_risk_id',
        string='Risk Register'
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
    control_risk_factors = fields.Html(
        string='Control Risk Factors',
        help='Factors contributing to control risk'
    )
    controls_reliance_planned = fields.Boolean(
        string='Controls Reliance Planned',
        help='Do we plan to rely on controls for any assertion?'
    )
    controls_to_test = fields.Html(
        string='Controls Identified for Testing'
    )

    # ===== Industry & Economic Factors =====
    industry_risks = fields.Html(
        string='Industry-Specific Risks',
        help='Risks specific to the client industry'
    )
    economic_factors = fields.Html(
        string='Economic/Environmental Factors',
        help='Economic and environmental factors affecting risk'
    )

    # ===== Risk Heat Map =====
    high_risk_count = fields.Integer(
        string='High Risk Items',
        compute='_compute_risk_counts',
        store=True
    )
    # XML view compatible alias
    high_risk_areas = fields.Integer(
        string='High Risk Areas',
        related='high_risk_count',
        store=True
    )
    medium_risk_count = fields.Integer(
        string='Medium Risk Items',
        compute='_compute_risk_counts',
        store=True
    )
    # XML view compatible alias
    medium_risk_areas = fields.Integer(
        string='Medium Risk Areas',
        related='medium_risk_count',
        store=True
    )
    low_risk_count = fields.Integer(
        string='Low Risk Items',
        compute='_compute_risk_counts',
        store=True
    )
    # XML view compatible alias
    low_risk_areas = fields.Integer(
        string='Low Risk Areas',
        related='low_risk_count',
        store=True
    )
    significant_risk_count = fields.Integer(
        string='Significant Risks',
        compute='_compute_risk_counts',
        store=True
    )
    heat_map_narrative = fields.Html(
        string='Heat Map Narrative',
        help='Visualization and narrative for risk heat map'
    )

    # ===== Significant Risks =====
    significant_risks_summary = fields.Html(
        string='Significant Risks Summary',
        help='Summary of all identified significant risks per ISA 315'
    )
    # XML view compatible alias
    significant_risks = fields.Html(
        string='Significant Risks',
        related='significant_risks_summary',
        readonly=False
    )
    revenue_recognition_significant = fields.Boolean(
        string='Revenue Recognition - Significant Risk',
        default=True,
        help='ISA 240 presumption that revenue recognition is a significant risk'
    )
    # XML view compatible alias
    revenue_recognition_risk = fields.Boolean(
        string='Revenue Recognition Risk',
        related='revenue_recognition_significant',
        readonly=False
    )
    revenue_risk_description = fields.Html(
        string='Revenue Risk Description',
        help='Description of revenue recognition risk factors'
    )
    management_override_significant = fields.Boolean(
        string='Management Override - Significant Risk',
        default=True,
        help='ISA 240 presumption of risk of management override of controls'
    )
    # XML view compatible alias
    management_override_risk = fields.Boolean(
        string='Management Override Risk',
        related='management_override_significant',
        readonly=False
    )
    override_risk_description = fields.Html(
        string='Override Risk Description',
        help='Description of management override risk'
    )
    other_significant_risks = fields.Html(
        string='Other Significant Risks',
        help='Other significant risks identified'
    )

    # ===== Audit Response =====
    overall_audit_response = fields.Html(
        string='Overall Audit Response',
        help='Overall audit response to identified risks'
    )
    significant_risk_responses = fields.Html(
        string='Significant Risk Responses',
        help='Specific responses to significant risks'
    )
    substantive_procedures = fields.Html(
        string='Substantive Procedures Planned',
        help='Planned substantive procedures'
    )
    control_testing_planned = fields.Html(
        string='Control Testing Planned',
        help='Planned tests of controls'
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
    # XML view compatible alias
    link_to_programs = fields.Html(
        string='Link to Programs',
        related='link_to_audit_programs',
        readonly=False
    )

    # ===== Linkage Section =====
    link_to_materiality = fields.Html(
        string='Link to Materiality',
        help='How risks link to materiality (P-5)'
    )
    link_to_controls = fields.Html(
        string='Link to Internal Controls',
        help='How risks link to internal controls (P-3)'
    )
    link_to_fraud = fields.Html(
        string='Link to Fraud Risk',
        help='How risks link to fraud risk (P-7)'
    )

    # ===== Attachments =====
    risk_register_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p6_risk_register_rel',
        'p6_id',
        'attachment_id',
        string='Risk Register Files'
    )
    # XML view compatible alias
    risk_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p6_risk_attach_rel',
        'p6_id',
        'attachment_id',
        string='Risk Assessment Documentation'
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
    # XML view compatible alias
    risk_assessment_conclusion = fields.Html(
        string='Risk Assessment Conclusion',
        related='risk_assessment_summary',
        readonly=False
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

    @api.depends('risk_register_line_ids', 'risk_register_line_ids.is_significant_risk')
    def _compute_significant_risks_count(self):
        """Compute the count of significant risks for XML view field."""
        for record in self:
            record.significant_risks_count = len(
                record.risk_register_line_ids.filtered(lambda r: r.is_significant_risk)
            )

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
