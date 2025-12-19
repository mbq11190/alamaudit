# -*- coding: utf-8 -*-
"""
P-10: Related Parties Planning
Standard: ISA 550
Purpose: Identify and assess related party risks.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError


class PlanningP10RelatedParties(models.Model):
    """P-10: Related Parties Planning (ISA 550)"""
    _name = 'qaco.planning.p10.related.parties'
    _description = 'P-10: Related Parties Planning'
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

    # ===== Related Party Listing =====
    related_party_line_ids = fields.One2many(
        'qaco.planning.p10.related.party.line',
        'p10_related_parties_id',
        string='Related Parties'
    )
    # XML view compatible alias
    related_party_ids = fields.One2many(
        'qaco.related.party.line',
        'p10_related_parties_id',
        string='Related Parties Register'
    )

    # ===== Related Party Transactions =====
    rpt_line_ids = fields.One2many(
        'qaco.rpt.transaction.line',
        'p10_related_parties_id',
        string='Related Party Transactions'
    )

    # ===== Overall Assessment (XML compatible) =====
    rpt_risk_level = fields.Selection([
        ('low', '🟢 Low'),
        ('medium', '🟡 Medium'),
        ('high', '🔴 High'),
    ], string='RPT Risk Level', tracking=True)
    significant_rpt_identified = fields.Boolean(
        string='Significant RPT Identified',
        tracking=True
    )

    # ===== Understanding Requirements =====
    understanding_obtained = fields.Boolean(
        string='Understanding Obtained',
        help='Understanding of related parties and transactions obtained per ISA 550.13'
    )
    understanding_source = fields.Html(
        string='Sources of Information',
        help='Sources used to identify related parties'
    )
    # XML view compatible alias
    understanding_related_parties = fields.Html(
        string='Understanding Entity\'s Related Parties',
        related='understanding_source',
        readonly=False
    )
    management_representations = fields.Html(
        string='Management Representations',
        help='Representations obtained from management regarding RP'
    )

    # ===== Nature of Relationships =====
    ownership_relationships = fields.Html(
        string='Ownership Relationships',
        help='Parent, subsidiaries, associates, joint ventures'
    )
    management_relationships = fields.Html(
        string='Management Relationships',
        help='Common directors, key management personnel'
    )
    family_relationships = fields.Html(
        string='Family Relationships',
        help='Close family members of key management'
    )
    other_relationships = fields.Html(
        string='Other Related Relationships',
        help='Other relationships meeting IAS 24 definition'
    )

    # ===== Transaction Types =====
    transaction_types = fields.Html(
        string='Transaction Types',
        help='Types of transactions with related parties'
    )
    sales_purchases = fields.Boolean(string='Sales/Purchases of Goods')
    services_rendered = fields.Boolean(string='Services Rendered/Received')
    leasing_arrangements = fields.Boolean(string='Leasing Arrangements')
    financing_arrangements = fields.Boolean(string='Financing/Loans')
    guarantees = fields.Boolean(string='Guarantees Given/Received')
    transfer_rd = fields.Boolean(string='Transfer of R&D/IP')
    management_contracts = fields.Boolean(string='Management Contracts')
    other_transactions = fields.Boolean(string='Other Transactions')
    other_transactions_details = fields.Html(string='Other Transaction Details')

    # ===== Risk Assessment =====
    rp_risk_assessment = fields.Html(
        string='Related Party Risk Assessment',
        help='Assessment of risks arising from related party relationships'
    )
    # XML view compatible alias
    rpt_risk_assessment = fields.Html(
        string='RPT Risk Assessment',
        related='rp_risk_assessment',
        readonly=False
    )
    rpt_fraud_indicators = fields.Html(
        string='Fraud Risk Indicators',
        help='Indicators of fraud risk related to related parties'
    )
    significant_rp_transactions = fields.Html(
        string='Significant RP Transactions',
        help='Transactions requiring specific audit attention'
    )
    # XML view compatible alias
    significant_rpt_risks = fields.Html(
        string='Significant RPT Risks',
        related='significant_rp_transactions',
        readonly=False
    )
    arms_length_concerns = fields.Html(
        string="Arm's Length Concerns",
        help='Transactions that may not be at arm\'s length'
    )
    undisclosed_rp_risk = fields.Boolean(
        string='Risk of Undisclosed RPs',
        help='Is there a risk of undisclosed related parties?'
    )
    undisclosed_rp_procedures = fields.Html(
        string='Procedures for Undisclosed RPs',
        help='Procedures to identify undisclosed related parties'
    )
    # XML view compatible alias
    unidentified_rpt_procedures = fields.Html(
        string='Procedures for Previously Unidentified RPT',
        related='undisclosed_rp_procedures',
        readonly=False
    )

    # ===== Audit Procedures (XML compatible) =====
    risk_assessment_procedures = fields.Html(
        string='Risk Assessment Procedures',
        help='Procedures for assessing RPT risks'
    )
    identification_procedures = fields.Html(
        string='Identification Procedures',
        help='Procedures for identifying related parties'
    )
    substantive_procedures = fields.Html(
        string='Substantive Procedures',
        help='Substantive audit procedures for RPT'
    )

    # ===== Authorization (XML compatible) =====
    authorization_assessment = fields.Html(
        string='Authorization Assessment',
        help='Assessment of authorization processes for RPT'
    )
    board_approval = fields.Html(
        string='Board/Shareholder Approval',
        help='Documentation of board/shareholder approvals'
    )
    arms_length_assessment = fields.Html(
        string='Arm\'s Length Basis Assessment',
        help='Assessment of whether transactions are at arm\'s length'
    )

    # ===== Disclosure (XML compatible) =====
    disclosure_requirements = fields.Html(
        string='Disclosure Requirements',
        help='Applicable disclosure requirements'
    )
    disclosure_adequacy = fields.Html(
        string='Disclosure Adequacy Assessment',
        help='Assessment of adequacy of disclosures'
    )
    ias24_compliance = fields.Html(
        string='IAS 24 Compliance',
        help='Assessment of IAS 24 compliance'
    )

    # ===== Representations (XML compatible) =====
    written_representations = fields.Html(
        string='Written Representations Required',
        help='Written representations required from management'
    )
    representations_obtained = fields.Html(
        string='Representations Obtained',
        help='Details of representations obtained'
    )

    # ===== Communication (XML compatible) =====
    management_communication = fields.Html(
        string='Communication to Management',
        help='Matters to communicate to management'
    )
    tcwg_communication = fields.Html(
        string='Communication to TCWG',
        help='Matters to communicate to those charged with governance'
    )

    # ===== Disclosure Risks =====
    disclosure_framework = fields.Char(
        string='Disclosure Framework',
        default='IAS 24',
        help='Applicable accounting standard for RP disclosures'
    )
    disclosure_risks = fields.Html(
        string='Disclosure Risks',
        help='Risks of inadequate or inaccurate RP disclosures'
    )
    disclosure_assessment = fields.Selection([
        ('adequate', '🟢 Likely Adequate'),
        ('concerns', '🟡 Some Concerns'),
        ('inadequate', '🔴 Likely Inadequate'),
        ('not_assessed', '⚪ Not Yet Assessed'),
    ], string='Disclosure Assessment')

    # ===== Planned Audit Procedures =====
    planned_procedures = fields.Html(
        string='Planned Audit Procedures',
        help='Specific procedures for related party audit'
    )
    authorization_review = fields.Boolean(
        string='Review Authorization of RP Transactions'
    )
    terms_review = fields.Boolean(
        string='Review Terms & Conditions'
    )
    pricing_review = fields.Boolean(
        string='Review Pricing/Valuation'
    )
    disclosure_testing = fields.Boolean(
        string='Test Disclosure Completeness'
    )

    # ===== Attachments =====
    rp_schedule_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p10_rp_schedule_rel',
        'p10_id',
        'attachment_id',
        string='Related Party Schedules'
    )
    supporting_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p10_supporting_rel',
        'p10_id',
        'attachment_id',
        string='Supporting Documents'
    )
    # XML view compatible aliases
    rpt_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p10_rpt_attachment_rel',
        'p10_id',
        'attachment_id',
        string='Related Party Documentation'
    )
    approval_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p10_approval_rel',
        'p10_id',
        'attachment_id',
        string='Board Minutes/Approvals'
    )

    # ===== Summary =====
    rp_risk_summary = fields.Html(
        string='Related Party Risk Memo',
        help='Consolidated related party assessment per ISA 550'
    )
    # XML view compatible alias
    rpt_conclusion = fields.Html(
        string='Related Parties Conclusion',
        related='rp_risk_summary',
        readonly=False
    )
    isa_reference = fields.Char(
        string='ISA Reference',
        default='ISA 550',
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
        ('audit_unique', 'UNIQUE(audit_id)', 'Only one P-10 record per Audit Engagement is allowed.')
    ]

    @api.depends('audit_id', 'client_id')
    def _compute_name(self):
        for record in self:
            if record.client_id:
                record.name = f"P10-{record.client_id.name[:15]}"
            else:
                record.name = 'P-10: Related Parties'

    def _validate_mandatory_fields(self):
        """Validate mandatory fields before completing P-10."""
        self.ensure_one()
        errors = []
        if not self.understanding_obtained:
            errors.append('Understanding of related parties must be obtained')
        if not self.rp_risk_summary:
            errors.append('Related party risk memo is required')
        if errors:
            raise UserError('Cannot complete P-10. Missing requirements:\n• ' + '\n• '.join(errors))

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


class PlanningP10RelatedPartyLine(models.Model):
    """Related Party Line Item."""
    _name = 'qaco.planning.p10.related.party.line'
    _description = 'Related Party'
    _order = 'relationship_type, name'

    p10_related_parties_id = fields.Many2one(
        'qaco.planning.p10.related.parties',
        string='P-10 Related Parties',
        required=True,
        ondelete='cascade'
    )
    name = fields.Char(
        string='Related Party Name',
        required=True
    )
    relationship_type = fields.Selection([
        ('parent', 'Parent Company'),
        ('subsidiary', 'Subsidiary'),
        ('associate', 'Associate'),
        ('joint_venture', 'Joint Venture'),
        ('director', 'Director/Officer'),
        ('key_management', 'Key Management Personnel'),
        ('family_member', 'Close Family Member'),
        ('entity_controlled', 'Entity Controlled by KMP'),
        ('pension_fund', 'Post-Employment Benefit Plan'),
        ('other', 'Other Related Party'),
    ], string='Relationship Type', required=True)
    relationship_details = fields.Text(
        string='Relationship Details'
    )
    transaction_types = fields.Char(
        string='Types of Transactions'
    )
    transaction_volume = fields.Monetary(
        string='Estimated Transaction Volume',
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='p10_related_parties_id.currency_id'
    )
    outstanding_balances = fields.Monetary(
        string='Outstanding Balances',
        currency_field='currency_id'
    )
    risk_level = fields.Selection([
        ('low', '🟢 Low'),
        ('medium', '🟡 Medium'),
        ('high', '🔴 High'),
    ], string='Risk Level')
    arms_length = fields.Boolean(
        string="At Arm's Length",
        help='Are transactions at arm\'s length?'
    )
    notes = fields.Text(string='Notes')


class RelatedPartyLine(models.Model):
    """Related Party Line for XML view compatibility."""
    _name = 'qaco.related.party.line'
    _description = 'Related Party'
    _order = 'relationship_type, party_name'

    p10_related_parties_id = fields.Many2one(
        'qaco.planning.p10.related.parties',
        string='P-10 Related Parties',
        required=True,
        ondelete='cascade'
    )
    party_name = fields.Char(
        string='Party Name',
        required=True
    )
    relationship_type = fields.Selection([
        ('parent', 'Parent Company'),
        ('subsidiary', 'Subsidiary'),
        ('associate', 'Associate'),
        ('joint_venture', 'Joint Venture'),
        ('director', 'Director/Officer'),
        ('key_management', 'Key Management Personnel'),
        ('family_member', 'Close Family Member'),
        ('entity_controlled', 'Entity Controlled by KMP'),
        ('pension_fund', 'Post-Employment Benefit Plan'),
        ('other', 'Other Related Party'),
    ], string='Relationship Type', required=True)
    relationship_nature = fields.Char(
        string='Nature of Relationship'
    )
    ownership_percentage = fields.Float(
        string='Ownership %'
    )
    identification_source = fields.Selection([
        ('management', 'Management Inquiry'),
        ('register', 'Company Register'),
        ('minutes', 'Board Minutes'),
        ('prior_audit', 'Prior Year Audit'),
        ('public', 'Public Information'),
        ('other', 'Other'),
    ], string='Identification Source')
    notes = fields.Text(string='Notes')


class RptTransactionLine(models.Model):
    """RPT Transaction Line for XML view compatibility."""
    _name = 'qaco.rpt.transaction.line'
    _description = 'RPT Transaction'
    _order = 'transaction_amount desc'

    p10_related_parties_id = fields.Many2one(
        'qaco.planning.p10.related.parties',
        string='P-10 Related Parties',
        required=True,
        ondelete='cascade'
    )
    related_party_id = fields.Many2one(
        'qaco.related.party.line',
        string='Related Party',
        domain="[('p10_related_parties_id', '=', p10_related_parties_id)]"
    )
    transaction_type = fields.Selection([
        ('sales', 'Sales'),
        ('purchases', 'Purchases'),
        ('services_provided', 'Services Provided'),
        ('services_received', 'Services Received'),
        ('loan_given', 'Loan Given'),
        ('loan_received', 'Loan Received'),
        ('guarantee', 'Guarantee'),
        ('lease', 'Lease'),
        ('royalty', 'Royalty/License'),
        ('management_fee', 'Management Fee'),
        ('other', 'Other'),
    ], string='Transaction Type')
    transaction_description = fields.Char(
        string='Description'
    )
    transaction_amount = fields.Monetary(
        string='Amount',
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='p10_related_parties_id.currency_id'
    )
    terms_conditions = fields.Text(
        string='Terms & Conditions'
    )
    business_rationale = fields.Text(
        string='Business Rationale'
    )
    arms_length = fields.Boolean(
        string='At Arm\'s Length'
    )
    disclosure_risk = fields.Selection([
        ('low', '🟢 Low'),
        ('medium', '🟡 Medium'),
        ('high', '🔴 High'),
    ], string='Disclosure Risk')
