
# -*- coding: utf-8 -*-
"""
P-7: Fraud Risk Assessment (ISA 240)
=====================================
Standards Compliance:
- ISA 240: The Auditor's Responsibilities Relating to Fraud in an Audit of Financial Statements
- ISA 315: Identifying and Assessing the Risks of Material Misstatement
- Companies Act, 2017 (Pakistan) - Section 36: Fraud and Error

Purpose:
Systematic identification, assessment, and documentation of fraud risks
through professional skepticism and risk-based audit procedures.
=====================================
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class PlanningP7Fraud(models.Model):
    """P-7: Fraud Risk Assessment (ISA 240)"""
    _name = 'qaco.planning.p7.fraud'
    _description = 'P-7: Fraud Risk Assessment'
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

    # Sequential Gating (ISA 300/220: Systematic Planning Approach)
    can_open = fields.Boolean(
        string='Can Open This Tab',
        compute='_compute_can_open',
        store=False,
        help='P-7 can only be opened after P-6 is approved'
    )

    @api.depends('audit_id')
    def _compute_can_open(self):
        """P-7 requires P-6 to be approved. Optimized for performance."""
        if not self:
            return

        # Batch fetch all P-6 records for the audits in this recordset
        audit_ids = self.mapped('audit_id.id')
        p6_records = self.env['qaco.planning.p6.risk'].search([
            ('engagement_id', 'in', audit_ids)
        ])

        # Create a mapping for quick lookup
        p6_map = {p6.engagement_id.id: p6.state for p6 in p6_records}

        for rec in self:
            if not rec.audit_id:
                rec.can_open = False
                continue
            # Use the mapping for O(1) lookup instead of O(n) search
            p6_state = p6_map.get(rec.audit_id.id)
            rec.can_open = p6_state == 'locked' if p6_state else False

    @api.constrains('state')
    def _check_sequential_gating(self):
        """ISA 300/220: Enforce sequential planning approach."""
        for rec in self:
            if rec.state != 'not_started' and not rec.can_open:
                raise UserError(
                    'ISA 300/220 & ISA 240 Violation: Sequential Planning Approach Required.\n\n'
                    'P-7 (Fraud Risk Assessment) cannot be started until P-6 (Risk Assessment) '
                    'has been Partner-approved and locked.\n\n'
                    'Reason: Fraud risk assessment per ISA 240 requires completed Risk of '
                    'Material Misstatement assessment from P-6.\n\n'
                    'Action: Please complete and obtain Partner approval for P-6 first.'
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
        store=False
    )

    # ===== Overall Fraud Risk Summary (ISA 240) =====
    fraud_risks_identified = fields.Integer(
        string='Fraud Risks Identified',
        compute='_compute_fraud_risks_identified',
        store=True,
        help='Number of fraud risks identified'
    )

    # ===== Fraud Brainstorming Documentation =====
    # Section A: Mandatory Brainstorming Session
    brainstorming_conducted = fields.Boolean(
        string='Brainstorming Session Conducted',
        default=False,
        tracking=True,
        help='ISA 240.15 - MANDATORY brainstorming session (No blocks progression)'
    )
    brainstorming_date = fields.Date(
        string='Brainstorming Date',
        tracking=True
    )
    brainstorming_mode = fields.Selection([
        ('in_person', 'In-Person'),
        ('virtual', 'Virtual'),
        ('hybrid', 'Hybrid'),
    ], string='Mode of Session')
    brainstorming_participants = fields.Many2many(
        'res.users',
        'qaco_p7_brainstorming_participants_rel',
        'p7_id',
        'user_id',
        string='Brainstorming Participants'
    )
    # XML view compatible alias
    brainstorming_attendees = fields.Many2many(
        'res.users',
        'qaco_p7_brainstorming_attendees_rel',
        'p7_id',
        'user_id',
        string='Brainstorming Attendees'
    )
    brainstorming_summary = fields.Html(
        string='Summary of Discussion (MANDATORY)',
        help='Document the fraud brainstorming discussion summary'
    )
    brainstorming_documentation = fields.Html(
        string='Brainstorming Documentation',
        help='Document the fraud brainstorming discussion per ISA 240.15'
    )
    
    # Section A: Brainstorming Checklists
    brainstorm_fs_susceptibility = fields.Boolean(
        string='☐ Susceptibility of FS to fraud discussed',
        help='ISA 240.15(a)'
    )
    brainstorm_management_override = fields.Boolean(
        string='☐ Management override risk discussed',
        help='ISA 240.31'
    )
    brainstorm_revenue_recognition = fields.Boolean(
        string='☐ Revenue recognition risks discussed',
        help='ISA 240.26'
    )
    brainstorm_unpredictability = fields.Boolean(
        string='☐ Unpredictability incorporated',
        help='ISA 240.30'
    )
    key_fraud_concerns = fields.Html(
        string='Key Fraud Concerns Identified',
        help='Summary of key fraud concerns raised during brainstorming'
    )
    discussion_points = fields.Html(
        string='Discussion Points',
        help='Key points discussed during fraud brainstorming'
    )
    fraud_scenarios = fields.Html(
        string='Fraud Scenarios Considered',
        help='Fraud scenarios discussed during brainstorming'
    )
    discussion_conclusions = fields.Html(
        string='Discussion Conclusions',
        help='Key conclusions from the brainstorming discussion'
    )
    
    # ===== Section B: Management & TCWG Inquiries =====
    management_inquiries_performed = fields.Boolean(
        string='Management Inquiries Performed?',
        default=False,
        tracking=True
    )
    management_fraud_assessment = fields.Html(
        string="Management's Assessment of Fraud Risk",
        help='Document management\'s own assessment of fraud risks'
    )
    actual_suspected_fraud_disclosed = fields.Boolean(
        string='Knowledge of Actual/Suspected Fraud Disclosed?',
        default=False,
        tracking=True,
        help='Did management disclose any actual or suspected fraud?'
    )
    fraud_disclosure_details = fields.Html(
        string='Fraud Disclosure Details',
        help='Details of any actual or suspected fraud disclosed'
    )
    tcwg_inquiries_performed = fields.Boolean(
        string='TCWG Inquiries Performed?',
        default=False,
        tracking=True
    )
    tcwg_inquiry_results = fields.Html(
        string='Results of TCWG Inquiries',
        help='Document responses from those charged with governance'
    )
    
    # Section B: Inquiry Checklists
    inquiry_documented = fields.Boolean(
        string='☐ Inquiries documented',
        help='All fraud inquiries properly documented'
    )
    inquiry_responses_evaluated = fields.Boolean(
        string='☐ Responses evaluated for consistency',
        help='Management and TCWG responses evaluated for consistency'
    )

    # ===== Fraud Triangle Assessment =====
    # Section C: Fraud Risk Factors (ISA 240 Triangle) - MANDATORY checkboxes
    incentives_identified = fields.Boolean(
        string='Incentives/Pressures Identified?',
        default=False,
        tracking=True,
        help='If Yes, specific fraud risks must be logged in Section D'
    )
    opportunities_identified = fields.Boolean(
        string='Opportunities Identified?',
        default=False,
        tracking=True,
        help='If Yes, specific fraud risks must be logged in Section D'
    )
    attitudes_identified = fields.Boolean(
        string='Attitudes/Rationalization Identified?',
        default=False,
        tracking=True,
        help='If Yes, specific fraud risks must be logged in Section D'
    )
    RISK_RATING = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    # Incentives/Pressures
    pressure_rating = fields.Selection(
        RISK_RATING,
        string='Pressure Rating',
        help='Assessment of pressure/incentive factors'
    )
    fraud_incentives = fields.Html(
        string='Incentives/Pressures',
        help='Management or employee incentives or pressures to commit fraud'
    )
    incentive_factors = fields.Html(
        string='Incentive Factors Identified',
        help='Specific factors: profit targets, bonuses, debt covenants, etc.'
    )
    # XML view compatible alias
    pressure_factors = fields.Html(
        string='Pressure Factors',
        related='incentive_factors',
        readonly=False
    )

    # Opportunities
    opportunity_rating = fields.Selection(
        RISK_RATING,
        string='Opportunity Rating',
        help='Assessment of opportunity factors'
    )
    fraud_opportunities = fields.Html(
        string='Opportunities',
        help='Circumstances that provide opportunity to commit fraud'
    )
    opportunity_factors = fields.Html(
        string='Opportunity Factors Identified',
        help='Specific factors: control weaknesses, lack of oversight, etc.'
    )

    # Attitudes/Rationalizations
    rationalization_rating = fields.Selection(
        RISK_RATING,
        string='Rationalization Rating',
        help='Assessment of rationalization/attitude factors'
    )
    fraud_attitudes = fields.Html(
        string='Attitudes/Rationalizations',
        help='Culture or attitudes that enable fraud'
    )
    attitude_factors = fields.Html(
        string='Attitude Factors Identified',
        help='Specific factors: aggressive management, poor tone at top, etc.'
    )
    # XML view compatible alias
    rationalization_factors = fields.Html(
        string='Rationalization Factors',
        related='attitude_factors',
        readonly=False
    )

    # ===== Section D: Fraud Risk Factors =====
    fraud_risk_line_ids = fields.One2many(
        'qaco.planning.p7.fraud.line',
        'p7_fraud_id',
        string='Fraud Risk Factors (Section D)'
    )
    # XML view compatible fields for narrative
    fraud_risk_factors = fields.Html(
        string='Fraud Risk Factors',
        help='Documented fraud risk factors identified'
    )
    industry_fraud_risks = fields.Html(
        string='Industry-Specific Fraud Risks',
        help='Fraud risks specific to the client\'s industry'
    )
    historical_fraud = fields.Html(
        string='Historical Fraud Information',
        help='Information about prior fraud occurrences or allegations'
    )

    # ===== Presumed Fraud Risks (ISA 240) =====
    # Section E: Presumed Risks (MANDATORY - Cannot be removed)
    revenue_recognition_fraud = fields.Boolean(
        string='Revenue Recognition - Presumed Fraud Risk',
        default=True,
        help='ISA 240.26 - Presumption of fraud risk in revenue recognition'
    )
    revenue_recognition_assessment = fields.Html(
        string='Revenue Recognition Fraud Assessment'
    )
    revenue_recognition_rebutted = fields.Boolean(
        string='Revenue Recognition Presumption Rebutted',
        help='Document if the presumption is rebutted (REQUIRES PARTNER APPROVAL)'
    )
    revenue_rebuttal_justification = fields.Html(
        string='Rebuttal Justification (MANDATORY if rebutted)',
        help='Detailed justification for rebutting revenue recognition fraud risk'
    )
    revenue_rebuttal_partner_approved = fields.Boolean(
        string='Rebuttal Approved by Partner',
        default=False,
        help='Partner must approve any rebuttal of presumed fraud risk'
    )
    # XML view compatible aliases for revenue recognition
    revenue_fraud_presumption = fields.Boolean(
        string='Revenue Fraud Presumption',
        related='revenue_recognition_fraud',
        readonly=False
    )
    revenue_presumption_rebutted = fields.Boolean(
        string='Revenue Presumption Rebutted',
        related='revenue_recognition_rebutted',
        readonly=False
    )
    revenue_fraud_assessment = fields.Html(
        string='Revenue Fraud Assessment',
        related='revenue_recognition_assessment',
        readonly=False
    )
    rebuttal_documentation = fields.Html(
        string='Rebuttal Documentation',
        related='revenue_rebuttal_justification',
        readonly=False
    )
    specific_revenue_risks = fields.Html(
        string='Specific Revenue Risks',
        help='Specific revenue recognition fraud risks identified'
    )

    management_override_fraud = fields.Boolean(
        string='Management Override - Presumed Fraud Risk',
        default=True,
        help='ISA 240.31 - Risk of management override of controls (CANNOT be rebutted)'
    )
    management_override_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Management Override Risk Level',
       help='Assessment level for management override risk')
    management_override_assessment = fields.Html(
        string='Management Override Assessment'
    )
    # XML view compatible alias
    override_risk_assessment = fields.Html(
        string='Override Risk Assessment',
        related='management_override_assessment',
        readonly=False
    )
    
    # ===== Section F: Management Override of Controls (MANDATORY RESPONSES) =====
    # These procedures CANNOT be deselected per ISA 240.32
    journal_entry_testing_planned = fields.Boolean(
        string='☑ Journal Entry Testing Planned (MANDATORY)',
        default=True,
        readonly=True,
        help='ISA 240.32(a) - Testing of journal entries (cannot be deselected)'
    )
    estimates_review_planned = fields.Boolean(
        string='☑ Accounting Estimates Review Planned (MANDATORY)',
        default=True,
        readonly=True,
        help='ISA 240.32(b) - Review of estimates for bias (cannot be deselected)'
    )
    unusual_transactions_planned = fields.Boolean(
        string='☑ Significant Unusual Transactions Planned (MANDATORY)',
        default=True,
        readonly=True,
        help='ISA 240.32(c) - Evaluation of unusual transactions (cannot be deselected)'
    )
    unpredictability_procedures = fields.Html(
        string='Additional Unpredictability Procedures',
        help='ISA 240.30 - Planned unpredictable audit procedures'
    )
    
    # ===== Section G: Entity's Anti-Fraud Controls =====
    antifraud_controls_identified = fields.Boolean(
        string='Anti-fraud Controls Identified?',
        default=False,
        tracking=True,
        help='Entity-level controls to prevent/detect fraud'
    )
    fraud_controls_effectiveness = fields.Selection([
        ('effective', 'Effective'),
        ('partially_effective', 'Partially Effective'),
        ('ineffective', 'Ineffective'),
        ('not_assessed', 'Not Assessed'),
    ], string='Control Effectiveness', default='not_assessed')
    fraud_control_gaps = fields.Html(
        string='Fraud Control Gaps Identified',
        help='Identified weaknesses in anti-fraud controls'
    )
    fraud_control_impact_assessment = fields.Html(
        string='Impact on Fraud Risk Assessment',
        help='How control weaknesses impact the fraud risk assessment (If ineffective → auto-increase fraud risk)'
    )
    
    # ===== Section H: Overall Audit Responses (Link to P-12) =====
    overall_fraud_response_nature = fields.Selection([
        ('general', 'General Responses'),
        ('specific', 'Specific Risk-Based'),
        ('both', 'Both General and Specific'),
    ], string='Response Nature', help='ISA 240.29')
    overall_fraud_response_timing = fields.Selection([
        ('interim', 'Interim'),
        ('year_end', 'Year-End'),
        ('both', 'Both'),
    ], string='Response Timing')
    overall_fraud_response_extent = fields.Selection([
        ('standard', 'Standard'),
        ('extended', 'Extended'),
        ('substantive', 'Substantive Only'),
    ], string='Response Extent')
    senior_involvement_required = fields.Boolean(
        string='Senior Personnel Involvement Required',
        help='ISA 240.29(a) - Assignment of more experienced personnel'
    )
    fraud_response_summary = fields.Html(
        string='Overall Fraud Response Summary',
        help='To be linked to P-12: Audit Strategy'
    )
    
    # ===== Section I: Going Concern & Fraud Interplay (Link to P-8) =====
    gc_fraud_linkage_exists = fields.Boolean(
        string='Going Concern Fraud Linkage Exists?',
        default=False,
        help='ISA 570.19 - Fraud indicators impacting GC assessment'
    )
    gc_fraud_impact_cashflows = fields.Boolean(
        string='Fraud Risk Impacts Cash Flows/Liquidity?',
        help='Fraud that may impair going concern'
    )
    gc_fraud_disclosure_risk = fields.Html(
        string='GC Disclosure Fraud Risk',
        help='Risk of fraudulent GC disclosures (link to P-8)'
    )
    gc_fraud_procedures = fields.Html(
        string='GC-Related Fraud Procedures',
        help='Specific procedures for GC fraud scenarios'
    )

    # ===== Fraud Response =====
    fraud_responses = fields.Html(
        string='Planned Fraud Responses',
        help='Audit responses to address identified fraud risks'
    )
    journal_entry_testing = fields.Html(
        string='Journal Entry Testing Plan',
        help='Plan for testing journal entries per ISA 240.32'
    )
    estimates_review = fields.Html(
        string='Accounting Estimates Review',
        help='Plan for reviewing accounting estimates for bias'
    )
    unusual_transactions = fields.Html(
        string='Unusual Transaction Testing',
        help='Plan for testing unusual significant transactions'
    )
    unpredictability_elements = fields.Html(
        string='Elements of Unpredictability',
        help='Planned unpredictable audit procedures'
    )
    # XML view compatible aliases for fraud response
    overall_fraud_response = fields.Html(
        string='Overall Fraud Response',
        related='fraud_responses',
        readonly=False
    )
    specific_fraud_responses = fields.Html(
        string='Specific Fraud Responses',
        help='Specific responses to individual fraud risks'
    )
    professional_skepticism = fields.Html(
        string='Professional Skepticism',
        help='Documentation of professional skepticism considerations'
    )

    # ===== Communication =====
    management_inquiry = fields.Html(
        string='Management Inquiry Documentation',
        help='Documentation of inquiries of management regarding fraud'
    )
    tcwg_inquiry = fields.Html(
        string='TCWG Inquiry Documentation',
        help='Documentation of inquiries of those charged with governance'
    )
    internal_audit_inquiry = fields.Html(
        string='Internal Audit Inquiry',
        help='Inquiries of internal audit regarding fraud'
    )
    other_inquiries = fields.Html(
        string='Other Inquiries',
        help='Other fraud-related inquiries documented'
    )
    # XML view compatible aliases for inquiries
    management_inquiries = fields.Html(
        string='Management Inquiries',
        related='management_inquiry',
        readonly=False
    )
    tcwg_inquiries = fields.Html(
        string='TCWG Inquiries',
        related='tcwg_inquiry',
        readonly=False
    )
    internal_audit_inquiries = fields.Html(
        string='Internal Audit Inquiries',
        related='internal_audit_inquiry',
        readonly=False
    )

    # ===== Section J: Attachments (MANDATORY) =====
    fraud_risk_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p7_fraud_risk_rel',
        'p7_id',
        'attachment_id',
        string='Fraud Risk Documentation (MANDATORY)'
    )
    brainstorming_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p7_brainstorming_rel',
        'p7_id',
        'attachment_id',
        string='Brainstorming Notes (MANDATORY)'
    )
    # XML view compatible alias
    fraud_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p7_fraud_attachment_rel',
        'p7_id',
        'attachment_id',
        string='Fraud Attachments'
    )

    # ===== Section K: Summary & Conclusion =====
    fraud_risk_summary = fields.Html(
        string='Fraud Risk Memo (MANDATORY)',
        help='Consolidated fraud risk assessment summary per ISA 240'
    )
    # XML view compatible alias
    fraud_conclusion = fields.Html(
        string='Fraud Conclusion',
        related='fraud_risk_summary',
        readonly=False
    )
    overall_fraud_risk = fields.Selection([
        ('low', '🟢 Low'),
        ('medium', '🟡 Medium'),
        ('high', '🔴 High'),
        ('very_high', '🔴🔴 Very High'),
    ], string='Overall Fraud Risk Assessment', tracking=True)
    
    # Section K: Mandatory Confirmations
    confirm_fraud_risks_linked = fields.Boolean(
        string='☐ All fraud risks linked to P-6 as significant risks',
        help='System auto-links fraud risks to RMM'
    )
    confirm_responses_documented = fields.Boolean(
        string='☐ All fraud responses documented and linked to P-12',
        help='Responses must flow to audit strategy'
    )
    confirm_partner_reviewed = fields.Boolean(
        string='☐ Partner has reviewed all rebutted presumptions',
        help='Partner approval mandatory for any rebuttal'
    )
    
    isa_reference = fields.Char(
        string='ISA Reference',
        default='ISA 240',
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
        ('audit_unique', 'UNIQUE(audit_id)', 'Only one P-7 record per Audit Engagement is allowed.')
    ]

    # ============================================================================
    # PROMPT 3: Safe HTML Default Template (Set in create, not field default)
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Set HTML defaults safely in create() to avoid registry crashes."""
        fraud_risk_template = '''
<p><strong>Fraud Risk Assessment Summary (ISA 240)</strong></p>
<ol>
<li><strong>Brainstorming Session:</strong> [Summarize key findings from fraud brainstorming]</li>
<li><strong>Fraud Triangle Analysis:</strong> [Summarize incentives, opportunities, attitudes identified]</li>
<li><strong>Presumed Fraud Risks:</strong> [Revenue recognition and management override status]</li>
<li><strong>Specific Fraud Risks:</strong> [List significant fraud risks identified]</li>
<li><strong>Overall Fraud Response:</strong> [Summarize how the audit strategy addresses fraud risks]</li>
</ol>
'''
        for vals in vals_list:
            if 'fraud_risk_summary' not in vals:
                vals['fraud_risk_summary'] = fraud_risk_template
        return super().create(vals_list)

    @api.depends('audit_id', 'client_id')
    def _compute_name(self):
        for record in self:
            if record.client_id:
                record.name = f"P7-{record.client_id.name[:15]}"
            else:
                record.name = 'P-7: Fraud Risk'

    @api.depends('fraud_risk_line_ids')
    def _compute_fraud_risks_identified(self):
        """Optimized: Compute the number of fraud risks identified with batch processing."""
        for record in self:
            try:
                # Use len() which is O(1) for recordsets
                record.fraud_risks_identified = len(record.fraud_risk_line_ids) if record.fraud_risk_line_ids else 0
            except Exception as e:
                _logger.warning(f'P-7 _compute_fraud_risks_identified failed for record {record.id}: {e}')
                record.fraud_risks_identified = 0

    def _validate_mandatory_fields(self):
        """Validate mandatory fields before completing P-7."""
        self.ensure_one()
        errors = []
        if not self.brainstorming_date:
            errors.append('Brainstorming date must be documented')
        if not self.brainstorming_documentation:
            errors.append('Brainstorming discussion must be documented per ISA 240')
        if not self.fraud_incentives:
            errors.append('Fraud incentives/pressures must be assessed')
        if not self.fraud_opportunities:
            errors.append('Fraud opportunities must be assessed')
        if not self.fraud_attitudes:
            errors.append('Fraud attitudes/rationalizations must be assessed')
        if not self.fraud_responses:
            errors.append('Planned fraud responses must be documented')
        if not self.fraud_risk_summary:
            errors.append('Fraud risk memo is required')
        if errors:
            raise UserError('Cannot complete P-7. Missing requirements:\n• ' + '\n• '.join(errors))

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
            record.message_post(body='P-7 Fraud Risk Assessment approved by Partner.')
            # Auto-unlock P-8: Going Concern
            record._auto_unlock_p8()
    
    def _auto_unlock_p8(self):
        """Auto-unlock P-8 Going Concern when P-7 is approved"""
        self.ensure_one()
        if not self.engagement_id:
            return
        
        # Find or create P-8 record
        P8 = self.env['qaco.planning.p8.going_concern']
        p8_record = P8.search([
            ('engagement_id', '=', self.engagement_id.id)
        ], limit=1)
        
        if p8_record and p8_record.state == 'locked':
            p8_record.write({'state': 'not_started'})
            p8_record.message_post(
                body='P-8 Going Concern auto-unlocked after P-7 Fraud Risk Assessment approval.'
            )
            _logger.info(f'P-8 auto-unlocked for engagement {self.engagement_id.name}')
        elif not p8_record:
            # Create new P-8 record if doesn't exist
            p8_record = P8.create({
                'engagement_id': self.engagement_id.id,
                'state': 'not_started',
            })
            _logger.info(f'P-8 auto-created for engagement {self.engagement_id.name}')

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


class PlanningP7FraudLine(models.Model):
    """Fraud Risk Factor Line Items."""
    _name = 'qaco.planning.p7.fraud.line'
    _description = 'Fraud Risk Factor'
    _order = 'risk_level desc, sequence'

    p7_fraud_id = fields.Many2one(
        'qaco.planning.p7.fraud',
        string='P-7 Fraud Assessment',
        required=True,
        ondelete='cascade'
    )
    sequence = fields.Integer(string='Sequence', default=10)
    risk_category = fields.Selection([
        ('incentive', 'Incentive/Pressure'),
        ('opportunity', 'Opportunity'),
        ('attitude', 'Attitude/Rationalization'),
    ], string='Risk Category', required=True)
    risk_description = fields.Text(
        string='Risk Description',
        required=True
    )
    fraud_scenario = fields.Text(
        string='Fraud Scenario',
        help='Specific how/what/when fraud scenario'
    )
    risk_level = fields.Selection([
        ('low', '🟢 Low'),
        ('medium', '🟡 Medium'),
        ('high', '🔴 High'),
    ], string='Risk Level', required=True)
    # Linkage to P-6 RMM
    fs_area = fields.Selection([
        ('revenue', 'Revenue'),
        ('purchases', 'Purchases'),
        ('payroll', 'Payroll'),
        ('inventory', 'Inventory'),
        ('fixed_assets', 'Fixed Assets'),
        ('cash', 'Cash & Bank'),
        ('investments', 'Investments'),
        ('borrowings', 'Borrowings'),
        ('equity', 'Equity'),
        ('other', 'Other'),
    ], string='FS Area/Account Cycle', help='Link to P-6 RMM')
    assertion = fields.Selection([
        ('existence', 'Existence/Occurrence'),
        ('completeness', 'Completeness'),
        ('valuation', 'Valuation/Measurement'),
        ('rights', 'Rights & Obligations'),
        ('presentation', 'Presentation & Disclosure'),
    ], string='Assertion at Risk')
    source = fields.Selection([
        ('p2_client_info', 'P-2: Client Info'),
        ('p3_controls', 'P-3: Controls'),
        ('p4_analytical', 'P-4: Analytical'),
        ('p6_risk_assessment', 'P-6: RMM'),
        ('brainstorming', 'Brainstorming'),
        ('inquiry', 'Management/TCWG Inquiry'),
        ('other', 'Other'),
    ], string='Source of Risk', help='Traceability to prior planning')
    likelihood = fields.Selection([
        ('remote', 'Remote'),
        ('possible', 'Possible'),
        ('probable', 'Probable'),
    ], string='Likelihood')
    impact = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Impact if Occurs')
    affected_area = fields.Char(
        string='Affected Area/Account'
    )
    fraud_type = fields.Selection([
        ('misappropriation', 'Asset Misappropriation'),
        ('fraudulent_reporting', 'Fraudulent Financial Reporting'),
        ('both', 'Both'),
    ], string='Fraud Type')
    planned_response = fields.Text(
        string='Planned Response'
    )
    notes = fields.Text(string='Notes')
