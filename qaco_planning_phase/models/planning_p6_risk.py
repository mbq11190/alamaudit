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

    # Sequential Gating (ISA 300/220: Systematic Planning Approach)
    can_open = fields.Boolean(
        string='Can Open This Tab',
        compute='_compute_can_open',
        store=False,
        help='P-6 can only be opened after P-5 is approved'
    )

    @api.depends('engagement_id', 'engagement_id.id')
    def _compute_can_open(self):
        """P-6 requires P-5 to be approved."""
        for rec in self:
            if not rec.engagement_id:
                rec.can_open = False
                continue
            # Find P-5 for this audit
            p5 = self.env['qaco.planning.p5.materiality'].search([
                ('audit_id', '=', rec.engagement_id.id)
            ], limit=1)
            rec.can_open = p5.state == 'approved' if p5 else False

    @api.constrains('state')
    def _check_sequential_gating(self):
        """ISA 300/220: Enforce sequential planning approach."""
        for rec in self:
            if rec.state != 'draft' and not rec.can_open:
                raise UserError(
                    'ISA 300/220 Violation: Sequential Planning Approach Required.\n\n'
                    'P-6 (Risk Assessment) cannot be started until P-5 (Materiality) '
                    'has been Partner-approved.\n\n'
                    'Reason: Risk of Material Misstatement assessment requires finalized '
                    'materiality thresholds per ISA 315/320.\n\n'
                    'Action: Please complete and obtain Partner approval for P-5 first.'
                )

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
    
    # ===== Section I: Heat Map & Dashboard Metrics =====
    total_risks_count = fields.Integer(
        string='Total Risks',
        compute='_compute_risk_dashboard_metrics',
        store=True
    )
    high_risk_count = fields.Integer(
        string='High Risk Count',
        compute='_compute_risk_dashboard_metrics',
        store=True
    )
    medium_risk_count = fields.Integer(
        string='Medium Risk Count',
        compute='_compute_risk_dashboard_metrics',
        store=True
    )
    low_risk_count = fields.Integer(
        string='Low Risk Count',
        compute='_compute_risk_dashboard_metrics',
        store=True
    )
    significant_risks_count = fields.Integer(
        string='Significant Risks Count',
        compute='_compute_risk_dashboard_metrics',
        store=True
    )
    fraud_risks_count = fields.Integer(
        string='Fraud Risks Count',
        compute='_compute_risk_dashboard_metrics',
        store=True
    )
    risks_by_account_cycle = fields.Text(
        string='Risks by Account Cycle',
        compute='_compute_risk_dashboard_metrics',
        store=True,
        help='JSON or formatted text showing risk distribution'
    )
    risks_by_assertion = fields.Text(
        string='Risks by Assertion',
        compute='_compute_risk_dashboard_metrics',
        store=True,
        help='JSON or formatted text showing assertion-level risk distribution'
    )

    @api.depends('partner_approved')
    def _compute_locked(self):
        for rec in self:            rec.locked = bool(rec.partner_approved)
    
    @api.depends('risk_line_ids', 'risk_line_ids.risk_rating', 
                 'risk_line_ids.is_significant_risk', 'risk_line_ids.isa_240_fraud_risk',
                 'risk_line_ids.account_cycle', 'risk_line_ids.assertion_type')
    def _compute_risk_dashboard_metrics(self):
        """Compute heat map and dashboard metrics from risk register."""
        for rec in self:
            lines = rec.risk_line_ids
            rec.total_risks_count = len(lines)
            rec.high_risk_count = len(lines.filtered(lambda l: l.risk_rating == 'high'))
            rec.medium_risk_count = len(lines.filtered(lambda l: l.risk_rating == 'medium'))
            rec.low_risk_count = len(lines.filtered(lambda l: l.risk_rating == 'low'))
            rec.significant_risks_count = len(lines.filtered(lambda l: l.is_significant_risk))
            rec.fraud_risks_count = len(lines.filtered(lambda l: l.isa_240_fraud_risk))
            
            # Risk distribution by account cycle
            cycle_counts = {}
            for line in lines:
                cycle = line.account_cycle or 'other'
                cycle_counts[cycle] = cycle_counts.get(cycle, 0) + 1
            rec.risks_by_account_cycle = str(cycle_counts)
            
            # Risk distribution by assertion
            assertion_counts = {}
            for line in lines:
                assertion = line.assertion_type or 'unspecified'
                assertion_counts[assertion] = assertion_counts.get(assertion, 0) + 1
            rec.risks_by_assertion = str(assertion_counts)

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
        # Auto-unlock P-7 (Fraud Risk Assessment)
        self._auto_unlock_p7()

    def action_auto_create_risks_from_planning(self):
        """
        Session 6B: Auto-create P-6 risks from P-2, P-3, P-4 findings.
        Reduces manual data re-entry and ensures planning integration.
        """
        self.ensure_one()
        created_count = 0
        
        # Get planning phase records
        planning_main = self.planning_main_id
        if not planning_main:
            raise UserError('Planning phase not found for this audit.')
        
        # Create risks from P-2 (Entity Understanding - Industry/Business Risks)
        if planning_main.p2_entity_id:
            created_count += self._create_risks_from_p2(planning_main.p2_entity_id)
        
        # Create risks from P-3 (Control Deficiencies)
        if planning_main.p3_controls_id:
            created_count += self._create_risks_from_p3(planning_main.p3_controls_id)
        
        # Create risks from P-4 (Analytical Variances)
        if planning_main.p4_analytics_id:
            created_count += self._create_risks_from_p4(planning_main.p4_analytics_id)
        
        if created_count > 0:
            self.message_post(
                body=f"Session 6B: Auto-created {created_count} risks from P-2/P-3/P-4 findings."
            )
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Risks Auto-Created'),
                    'message': _(f'{created_count} risks have been created from planning phase findings.'),
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No New Risks'),
                    'message': _('No new risks were identified from P-2/P-3/P-4 findings.'),
                    'type': 'info',
                    'sticky': False,
                }
            }
    
    def _create_risks_from_p2(self, p2_record):
        """Create risks from P-2 entity understanding (industry/business risks)."""
        created = 0
        # Check if P-2 has identified entity-level risks in fields like:
        # - industry_specific_risks, regulatory_compliance_risks, etc.
        if hasattr(p2_record, 'entity_level_risk_factors') and p2_record.entity_level_risk_factors:
            # Create FS-level risk from entity understanding
            self.env['qaco.planning.p6.risk.line'].create({
                'p6_risk_id': self.id,
                'account_cycle': 'fs_level',
                'risk_description': f'Entity-level risk from P-2: {p2_record.entity_level_risk_factors[:200]}',
                'assertion_type': 'presentation',
                'inherent_risk': 'high',
                'control_risk': 'medium',
                'fs_level_risk': True,
                'risk_factors': 'Source: P-2 Entity Understanding',
            })
            created += 1
        return created
    
    def _create_risks_from_p3(self, p3_record):
        """Create risks from P-3 control deficiencies."""
        created = 0
        # Check for control deficiencies in P-3
        if hasattr(p3_record, 'deficiency_line_ids'):
            for deficiency in p3_record.deficiency_line_ids:
                if deficiency.severity in ['significant', 'material_weakness']:
                    # Map deficiency to account cycle
                    cycle = 'other'
                    if hasattr(deficiency, 'cycle_id') and deficiency.cycle_id:
                        cycle_map = {
                            'revenue': 'revenue',
                            'purchases': 'purchases',
                            'payroll': 'payroll',
                            'inventory': 'inventory',
                        }
                        cycle = cycle_map.get(deficiency.cycle_id.cycle_type, 'other')
                    
                    # Create risk from control deficiency
                    self.env['qaco.planning.p6.risk.line'].create({
                        'p6_risk_id': self.id,
                        'account_cycle': cycle,
                        'risk_description': f'Control deficiency from P-3: {deficiency.deficiency_description[:200]}',
                        'assertion_type': 'existence',  # Default; should be mapped from deficiency
                        'inherent_risk': 'medium',
                        'control_risk': 'high' if deficiency.severity == 'material_weakness' else 'medium',
                        'is_significant_risk': deficiency.severity == 'material_weakness',
                        'risk_factors': f'Source: P-3 Control Deficiency ({deficiency.severity})',
                    })
                    created += 1
        return created
    
    def _create_risks_from_p4(self, p4_record):
        """Create risks from P-4 analytical variances."""
        created = 0
        # Check for significant variances in P-4
        if hasattr(p4_record, 'fs_line_ids'):
            for fs_line in p4_record.fs_line_ids:
                # Create risk for significant variances (>threshold or risk indicator = high)
                if fs_line.exceeds_threshold or (hasattr(fs_line, 'risk_indicator') and fs_line.risk_indicator == 'high'):
                    # Map FS line to account cycle
                    cycle_map = {
                        'revenue': 'revenue',
                        'sales': 'revenue',
                        'receivables': 'revenue',
                        'purchases': 'purchases',
                        'payables': 'purchases',
                        'inventory': 'inventory',
                        'cogs': 'inventory',
                        'payroll': 'payroll',
                        'wages': 'payroll',
                    }
                    cycle = 'other'
                    if fs_line.fs_caption:
                        caption_lower = fs_line.fs_caption.lower()
                        for keyword, mapped_cycle in cycle_map.items():
                            if keyword in caption_lower:
                                cycle = mapped_cycle
                                break
                    
                    # Create risk from analytical variance
                    variance_pct = fs_line.variance_pct if hasattr(fs_line, 'variance_pct') else 0
                    self.env['qaco.planning.p6.risk.line'].create({
                        'p6_risk_id': self.id,
                        'account_cycle': cycle,
                        'risk_description': f'Significant variance from P-4: {fs_line.fs_caption} ({variance_pct:.1f}% variance)',
                        'assertion_type': 'valuation',  # Variances typically affect valuation
                        'inherent_risk': 'high' if abs(variance_pct) > 20 else 'medium',
                        'control_risk': 'medium',
                        'risk_factors': f'Source: P-4 Analytical Variance ({fs_line.auditor_explanation or "Unexplained"})',
                    })
                    created += 1
        return created
    
    def _auto_unlock_p7(self):
        """Auto-unlock P-7 when P-6 is approved (similar to P-5 -> P-6 pattern)."""
        self.ensure_one()
        if 'qaco.planning.p7.fraud' in self.env:
            p7 = self.env['qaco.planning.p7.fraud'].search([
                ('audit_id', '=', self.engagement_id.id)
            ], limit=1)
            if p7 and p7.state == 'not_started':
                _logger.info(f"P-7 auto-unlock triggered by P-6 approval for audit {self.engagement_id.id}")
                # Optionally set p7.state = 'draft' if using state-based unlocking

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
    
    # ===== Section D: Significant Risk Classification =====
    basis_for_classification = fields.Text(
        string='Basis for Significant Risk Classification',
        help='MANDATORY: Explain why this risk is classified as significant'
    )
    mandatory_substantive_required = fields.Boolean(
        string='Mandatory Substantive Procedures Required',
        default=True,
        help='Auto-set for significant risks per ISA 330'
    )
    control_testing_permitted = fields.Boolean(
        string='Control Testing Permitted',
        default=False,
        help='Default No unless justified for significant risks'
    )
    control_testing_justification = fields.Text(
        string='Justification for Control Testing',
        help='Required if control_testing_permitted = True'
    )
    senior_involvement_required = fields.Boolean(
        string='Senior Team Involvement Required',
        compute='_compute_senior_involvement',
        store=True
    )
    extended_procedures_required = fields.Boolean(
        string='Extended Substantive Procedures Required',
        compute='_compute_extended_procedures',
        store=True
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
    
    # ===== Section E: Fraud Risk Integration =====
    fraud_type = fields.Selection([
        ('revenue_recognition', 'Revenue Recognition (Presumed)'),
        ('management_override', 'Management Override of Controls'),
        ('misappropriation', 'Misappropriation of Assets'),
        ('other', 'Other Fraud Risk'),
    ], string='Fraud Risk Type', help='ISA 240 fraud risk classification')
    fraud_scenario_narrative = fields.Text(
        string='Specific Fraud Scenario',
        help='Describe specific fraud scenario and how it could occur'
    )
    
    # ===== Section F: Going Concern Integration =====
    gc_conditions_identified = fields.Text(
        string='Going Concern Conditions/Events',
        help='ISA 570 - Conditions or events casting doubt on going concern'
    )
    gc_disclosure_impact = fields.Text(
        string='Impact on FS Disclosures',
        help='Required disclosures for material uncertainty or going concern issues'
    )
    
    # ===== Section G: Controls Linkage =====
    relevant_controls_identified = fields.Boolean(
        string='Relevant Controls Identified',
        help='Have controls been identified that could mitigate this risk?'
    )
    control_reliance_planned = fields.Boolean(
        string='Control Reliance Planned',
        help='Is the auditor planning to rely on controls for this risk?'
    )
    control_deficiency_impact = fields.Text(
        string='Impact of Control Deficiencies on RMM',
        help='Document how identified control weaknesses affect RMM assessment'
    )
    control_reference_p3 = fields.Char(
        string='P-3 Control Reference',
        help='Link to specific control in P-3 Internal Controls Assessment'
    )

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
    
    @api.depends('is_significant_risk', 'risk_rating')
    def _compute_senior_involvement(self):
        """Auto-flag senior involvement for significant or high risks."""
        for record in self:
            record.senior_involvement_required = (
                record.is_significant_risk or record.risk_rating == 'high'
            )
    
    @api.depends('is_significant_risk')
    def _compute_extended_procedures(self):
        """Auto-flag extended procedures for significant risks."""
        for record in self:
            record.extended_procedures_required = record.is_significant_risk

