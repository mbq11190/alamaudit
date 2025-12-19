    # -*- coding: utf-8 -*-
    """
    P-7: Fraud Risk Assessment (ISA 240, 315, 330, 570, 220, ISQM-1, Companies Act 2017, ICAP QCR/AOB)
    Court-defensible, fully integrated with planning workflow.
    """
    
    from odoo import api, fields, models
    from odoo.exceptions import UserError, ValidationError
    import logging
    _logger = logging.getLogger(__name__)
    
    # =============================
    # Parent Model: Fraud Risk Assessment
    # =============================
    class AuditPlanningP7Fraud(models.Model):
        _name = 'audit.planning.p7.fraud'
        _description = 'P-7: Fraud Risk Assessment'
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
        fraud_risk_line_ids = fields.One2many('audit.planning.p7.fraud_risk_line', 'fraud_id', string='Fraud Risk Register', required=True)
        # Section A: Brainstorming
        brainstorming_done = fields.Boolean(string='Brainstorming Session Conducted?')
        brainstorming_date = fields.Date(string='Date of Session')
        brainstorming_participants = fields.Char(string='Participants (Auto-list)', readonly=True)
        brainstorming_mode = fields.Selection([
            ('in_person', 'In-person'),
            ('virtual', 'Virtual'),
        ], string='Mode')
        brainstorming_summary = fields.Text(string='Summary of Discussion')
        brainstorming_susceptibility = fields.Boolean(string='Susceptibility of FS to fraud discussed?')
        brainstorming_override = fields.Boolean(string='Management override risk discussed?')
        brainstorming_revenue = fields.Boolean(string='Revenue recognition risks discussed?')
        brainstorming_unpredictability = fields.Boolean(string='Unpredictability incorporated?')
        # Section B: Management & TCWG Inquiries
        mgmt_inquiries_done = fields.Boolean(string='Management inquiries performed?')
        mgmt_assessment = fields.Text(string="Management's assessment of fraud risk")
        mgmt_knowledge_fraud = fields.Boolean(string='Knowledge of actual/suspected fraud disclosed?')
        tcwg_inquiries_done = fields.Boolean(string='Inquiries of TCWG performed?')
        tcwg_results = fields.Text(string='Results of TCWG inquiries')
        inquiries_documented = fields.Boolean(string='Inquiries documented?')
        responses_consistent = fields.Boolean(string='Responses evaluated for consistency?')
        # Section C: Fraud Risk Factors (ISA 240 Triangle)
        factor_incentives = fields.Boolean(string='Incentives/Pressures Identified?')
        factor_incentives_desc = fields.Text(string='Incentives/Pressures Description')
        factor_opportunities = fields.Boolean(string='Opportunities Identified?')
        factor_opportunities_desc = fields.Text(string='Opportunities Description')
        factor_attitudes = fields.Boolean(string='Attitudes/Rationalization Identified?')
        factor_attitudes_desc = fields.Text(string='Attitudes/Rationalization Description')
        # Section E: Presumed Fraud Risks
        presumed_revenue = fields.Boolean(string='Improper revenue recognition (Presumed)', default=True, readonly=True)
        presumed_override = fields.Boolean(string='Management override of controls (Presumed)', default=True, readonly=True)
        presumed_rebutted = fields.Boolean(string='Are presumed risks rebutted?')
        presumed_rebuttal_justification = fields.Text(string='Rebuttal Justification')
        presumed_partner_approval = fields.Boolean(string='Partner Approval for Rebuttal?')
        # Section F: Management Override of Controls
        planned_journal_entry = fields.Boolean(string='Planned journal entry testing?', default=True, readonly=True)
        planned_estimate_review = fields.Boolean(string='Planned review of accounting estimates?', default=True, readonly=True)
        planned_unusual_txn = fields.Boolean(string='Planned evaluation of significant unusual transactions?', default=True, readonly=True)
        planned_unpredictability = fields.Text(string='Additional unpredictability procedures planned')
        # Section G: Fraud-Related Controls Assessment
        antifraud_controls_identified = fields.Boolean(string='Anti-fraud controls identified?')
        antifraud_controls_effectiveness = fields.Selection([
            ('effective', 'Effective'),
            ('weak', 'Weak'),
            ('none', 'Not present'),
        ], string='Effectiveness of fraud controls')
        antifraud_control_gaps = fields.Text(string='Control gaps increasing fraud risk')
        # Section H: Linkage to Audit Responses
        response_nature = fields.Selection([
            ('expanded', 'Expanded substantive'),
            ('forensic', 'Forensic-style'),
            ('unpredictable', 'Unpredictable'),
        ], string='Nature of response')
        response_timing = fields.Selection([
            ('interim', 'Interim'),
            ('year_end', 'Year-end'),
            ('surprise', 'Surprise'),
        ], string='Timing adjustments')
        response_extent = fields.Selection([
            ('sample_increase', 'Sample size increase'),
            ('full', '100% testing areas'),
        ], string='Extent')
        response_senior_involvement = fields.Boolean(string='Senior team involvement required?')
        # Section I: Going-Concern & Fraud Interplay
        fraud_linked_going_concern = fields.Boolean(string='Fraud indicators linked to going concern?')
        fraud_impact_cashflow = fields.Text(string='Impact on cash flows / liquidity')
        fraud_disclosure_risk = fields.Boolean(string='Disclosure risk identified?')
        # Section J: Mandatory Document Uploads
        attachment_ids = fields.Many2many('ir.attachment', 'audit_p7_fraud_attachment_rel', 'fraud_id', 'attachment_id', string='Required Attachments', help='Fraud brainstorming minutes, management/TCWG inquiry docs, fraud risk register')
        mandatory_upload_check = fields.Boolean(string='Mandatory uploads present?')
        # Section K: Conclusion & Professional Judgment
        conclusion_narrative = fields.Text(string='Conclusion Narrative', required=True, default="Fraud risks, including presumed risks relating to revenue recognition and management override of controls, have been identified and assessed in accordance with ISA 240. Appropriate audit responses have been designed and linked to the overall audit strategy.")
        fraud_risks_confirmed = fields.Boolean(string='Fraud risks fully identified?')
        mandatory_responses_planned = fields.Boolean(string='Mandatory responses planned?')
        linkage_to_strategy_confirmed = fields.Boolean(string='Linkage to audit strategy confirmed?')
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
        fraud_memo_pdf = fields.Binary(string='Fraud Risk Assessment Memorandum (PDF)')
        fraud_register_export = fields.Binary(string='Fraud Risk Register Export')
        fraud_procedures_checklist = fields.Binary(string='Mandatory Fraud Procedures Checklist')
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
            self.message_post(body="P-7 prepared.")
        
        def action_review(self):
            self.state = 'reviewed'
            self.reviewed_by = self.env.user.id
            self.message_post(body="P-7 reviewed.")
        
        def action_partner_approve(self):
            if not self.partner_comments:
                raise ValidationError("Partner comments are mandatory for approval.")
            self.state = 'locked'
            self.partner_approved = True
            self.message_post(body="P-7 partner approved and locked.")
        
        @api.constrains('attachment_ids')
        def _check_mandatory_uploads(self):
            for rec in self:
                if not rec.attachment_ids:
                    raise ValidationError("Mandatory fraud assessment documents must be uploaded.")
        
        @api.constrains('fraud_risk_line_ids')
        def _check_fraud_risk_lines(self):
            for rec in self:
                if not rec.fraud_risk_line_ids:
                    raise ValidationError("At least one fraud risk line must be entered.")
        
        # Pre-conditions enforcement
        @api.model
        def create(self, vals):
            # Enforce P-6 locked, P-5 finalized, P-3/P-4 available
            planning = self.env['qaco.planning.main'].browse(vals.get('planning_main_id'))
            if not planning or not planning.p6_partner_locked:
                raise UserError("P-7 cannot be started until P-6 is partner-approved and locked.")
            if not planning.p5_finalized or not planning.p3_outputs_ready or not planning.p4_outputs_ready:
                raise UserError("P-7 requires finalized P-5, and outputs from P-3 and P-4.")
            return super().create(vals)
        
    # =============================
    # Child Model: Fraud Risk Line
    # =============================
    class AuditPlanningP7FraudRiskLine(models.Model):
        _name = 'audit.planning.p7.fraud_risk_line'
        _description = 'P-7: Fraud Risk Register Line'
        _order = 'id desc'
        
        fraud_id = fields.Many2one('audit.planning.p7.fraud', string='Fraud Assessment', required=True, ondelete='cascade', index=True)
        engagement_id = fields.Many2one('qaco.audit', string='Audit Engagement', required=True, ondelete='cascade', index=True)
        audit_year = fields.Many2one('qaco.audit.year', string='Audit Year', required=True, ondelete='cascade', index=True)
        fs_area = fields.Char(string='FS Area', required=True)
        assertion = fields.Selection([
            ('existence', 'Existence/Occurrence'),
            ('completeness', 'Completeness'),
            ('accuracy', 'Accuracy'),
            ('valuation', 'Valuation'),
            ('rights_obligations', 'Rights & Obligations'),
            ('presentation', 'Presentation & Disclosure'),
        ], string='Assertion', required=True)
        fraud_scenario = fields.Text(string='Fraud Scenario', required=True)
        risk_source = fields.Selection([
            ('p2', 'P-2 Entity'),
            ('p3', 'P-3 Controls'),
            ('p4', 'P-4 Analytics'),
            ('p6', 'P-6 RMM'),
            ('other', 'Other'),
        ], string='Source', required=True)
        likelihood = fields.Selection([
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
        ], string='Likelihood', required=True)
        impact = fields.Selection([
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
        ], string='Impact', required=True)
        fraud_risk_level = fields.Selection([
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
        ], string='Fraud Risk Level', compute='_compute_fraud_risk_level', store=True)
        significant_risk = fields.Boolean(string='Significant Risk? (auto-link to P-6)', default=True, readonly=True)
        # Audit trail
        change_log = fields.Text(string='Change Log')
        version_history = fields.Text(string='Version History')
        reviewer_timestamps = fields.Text(string='Reviewer Timestamps')
        
        @api.depends('likelihood', 'impact')
        def _compute_fraud_risk_level(self):
            for rec in self:
                if rec.likelihood == 'high' or rec.impact == 'high':
                    rec.fraud_risk_level = 'high'
                elif rec.likelihood == 'medium' or rec.impact == 'medium':
                    rec.fraud_risk_level = 'medium'
                else:
                    rec.fraud_risk_level = 'low'
        
        # Audit trail logic
        def write(self, vals):
            self.message_post(body=f"Fraud risk line updated: {vals}")
            return super().write(vals)
        
        def unlink(self):
            self.message_post(body="Fraud risk line deleted.")
            return super().unlink()

from odoo import api, fields, models
from odoo.exceptions import UserError


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

    # ===== Overall Fraud Risk Summary (ISA 240) =====
    fraud_risks_identified = fields.Integer(
        string='Fraud Risks Identified',
        compute='_compute_fraud_risks_identified',
        store=True,
        help='Number of fraud risks identified'
    )

    # ===== Fraud Brainstorming Documentation =====
    brainstorming_date = fields.Date(
        string='Brainstorming Date',
        tracking=True
    )
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
    brainstorming_documentation = fields.Html(
        string='Brainstorming Documentation',
        help='Document the fraud brainstorming discussion per ISA 240.15'
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

    # ===== Fraud Triangle Assessment =====
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

    # ===== Fraud Risk Factors =====
    fraud_risk_line_ids = fields.One2many(
        'qaco.planning.p7.fraud.line',
        'p7_fraud_id',
        string='Fraud Risk Factors'
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
        help='Document if the presumption is rebutted'
    )
    revenue_rebuttal_justification = fields.Html(
        string='Rebuttal Justification',
        help='Justification for rebutting revenue recognition fraud risk'
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
        help='ISA 240.31 - Risk of management override of controls (cannot be rebutted)'
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

    # ===== Attachments =====
    fraud_risk_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p7_fraud_risk_rel',
        'p7_id',
        'attachment_id',
        string='Fraud Risk Documentation'
    )
    brainstorming_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p7_brainstorming_rel',
        'p7_id',
        'attachment_id',
        string='Brainstorming Notes'
    )
    # XML view compatible alias
    fraud_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p7_fraud_attachment_rel',
        'p7_id',
        'attachment_id',
        string='Fraud Attachments'
    )

    # ===== Summary =====
    fraud_risk_summary = fields.Html(
        string='Fraud Risk Memo',
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
    ], string='Overall Fraud Risk Assessment', tracking=True)
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

    @api.depends('audit_id', 'client_id')
    def _compute_name(self):
        for record in self:
            if record.client_id:
                record.name = f"P7-{record.client_id.name[:15]}"
            else:
                record.name = 'P-7: Fraud Risk'

    @api.depends('fraud_risk_line_ids')
    def _compute_fraud_risks_identified(self):
        """Compute the number of fraud risks identified."""
        for record in self:
            record.fraud_risks_identified = len(record.fraud_risk_line_ids)

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
    risk_level = fields.Selection([
        ('low', '🟢 Low'),
        ('medium', '🟡 Medium'),
        ('high', '🔴 High'),
    ], string='Risk Level', required=True)
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
