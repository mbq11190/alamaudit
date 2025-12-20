# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime

class AuditPlanningP10RelatedParties(models.Model):
    _name = 'audit.planning.p10.related_parties'
    _description = 'P-10: Related Parties Planning'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'engagement_id'
    _order = 'id desc'

    engagement_id = fields.Many2one('audit.engagement', required=True, ondelete='cascade', tracking=True)
    audit_year_id = fields.Many2one('audit.year', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Manager Review'),
        ('partner', 'Partner Approval'),
        ('locked', 'Locked'),
    ], default='draft', tracking=True)

    # SECTION A: Related Parties Listing
    related_party_ids = fields.One2many('audit.planning.p10.related_party', 'related_parties_id', string='Related Parties', tracking=True)
    related_parties_complete = fields.Boolean('All known related parties identified?', tracking=True)
    changes_captured = fields.Boolean('Changes during the year captured?', tracking=True)

    # SECTION B: Completeness Procedures
    completeness_procedures = fields.Selection([
        ('inquiry', 'Inquiry of management & TCWG'),
        ('minutes', 'Review of board minutes'),
        ('declarations', 'Review of declarations of interest'),
        ('shareholder', 'Review of shareholder records'),
        ('prior', 'Review of prior-year working papers'),
    ], string='Procedures Performed', required=False, tracking=True)
    completeness_procedures_multi = fields.Many2many('audit.p10.completeness.procedure', string='Procedures Performed (multi)', tracking=True)
    completeness_results = fields.Text('Results of Procedures', required=True, tracking=True)

    # SECTION C: RPT Listing
    rpt_transaction_ids = fields.One2many('audit.planning.p10.rpt_transaction', 'related_parties_id', string='RPT Transactions', tracking=True)
    rpt_all_captured = fields.Boolean('All RPTs captured?', tracking=True)
    rpt_non_routine_highlighted = fields.Boolean('Non-routine transactions highlighted?', tracking=True)

    # SECTION D: RPT Risk Assessment
    rpt_risk_line_ids = fields.One2many('audit.planning.p10.rpt_risk_line', 'related_parties_id', string='RPT Risk Lines', tracking=True)

    # SECTION E: Fraud & Concealment
    risk_undisclosed_rpt = fields.Boolean('Risk of undisclosed RPTs?')
    mgmt_override_indicators = fields.Boolean('Management dominance or override indicators?')
    circular_transactions = fields.Boolean('Circular transactions identified?')
    fraud_assessment = fields.Text("Auditor’s assessment (Fraud & Concealment)")

    # SECTION F: Disclosure Requirements
    disclosure_framework = fields.Selection([
        ('ifrs', 'IFRS'),
        ('ifrs_sme', 'IFRS for SMEs'),
    ], string='Applicable Disclosure Framework', tracking=True)
    disclosures_identified = fields.Boolean('Required disclosures identified?', tracking=True)
    risk_incomplete_disclosure = fields.Boolean('Risk of incomplete disclosure?', tracking=True)
    enhanced_disclosure_areas = fields.Text('Areas requiring enhanced disclosure', tracking=True)

    # SECTION G: Audit Responses
    planned_procedures = fields.Many2many('audit.p10.audit_procedure', string='Planned Procedures', tracking=True)
    response_nature_timing_extent = fields.Text('Nature, timing, extent', tracking=True)
    senior_team_involvement = fields.Boolean('Senior team involvement required?', tracking=True)

    # SECTION H: Going Concern & Support
    rpt_critical_liquidity = fields.Boolean('RPTs critical to liquidity/support?')
    support_nature = fields.Text('Nature of support (loans, guarantees, waivers)')
    enforceability_assessed = fields.Boolean('Enforceability assessed?')
    disclosure_impact_assessed = fields.Boolean('Disclosure impact assessed?')

    # SECTION I: Attachments
    attachment_ids = fields.Many2many('ir.attachment', 'audit_p10_attachment_rel', 'related_parties_id', 'attachment_id', string='Attachments', help='Upload all required documents for P-10')

    # SECTION J: Conclusion
    conclusion_narrative = fields.Text('Conclusion & Professional Judgment', default="Related parties and related party transactions have been identified, assessed for completeness, and evaluated for risk in accordance with ISA 550. Appropriate audit responses and disclosure considerations have been determined.", required=True)
    related_parties_complete_final = fields.Boolean('Related parties complete (final)?')
    rpt_risks_assessed_linked = fields.Boolean('RPT risks assessed and linked?')
    basis_established = fields.Boolean('Basis established for audit responses?')

    # SECTION K: Review & Approval
    prepared_by = fields.Many2one('res.users', string='Prepared By', tracking=True)
    prepared_by_role = fields.Char('Prepared By Role')
    prepared_by_date = fields.Datetime('Prepared By Date')
    reviewed_by = fields.Many2one('res.users', string='Reviewed By (Manager)', tracking=True)
    review_notes = fields.Text('Review Notes')
    partner_approval = fields.Boolean('Partner Approval', tracking=True)
    partner_comments = fields.Text('Partner Comments (Mandatory)')
    locked = fields.Boolean('Locked', compute='_compute_locked', store=True)

    # Audit trail fields
    version_history = fields.Text('Version History')
    reviewer_timestamps = fields.Text('Reviewer Timestamps')

    # Pre-condition enforcement (to be implemented in create/write/onchange)

    @api.model
    def create(self, vals):
        # Enforce pre-conditions: P-9 locked, P-2, P-6, P-7 available
        engagement_id = vals.get('engagement_id')
        audit_year_id = vals.get('audit_year_id')
        if engagement_id and audit_year_id:
            # Check P-9 (Laws & Regulations) is locked
            p9 = self.env['audit.planning.p9.laws'].search([
                ('engagement_id', '=', engagement_id),
                ('audit_year_id', '=', audit_year_id),
                ('locked', '=', True)
            ], limit=1)
            if not p9:
                raise UserError(_('Cannot open P-10: P-9 (Laws & Regulations) must be partner-approved and locked.'))
            # Check P-2, P-6, P-7 exist
            for model, label in [
                ('audit.planning.p2.entity', 'P-2 (Entity Understanding)'),
                ('audit.planning.p6.risk', 'P-6 (Risk Assessment)'),
                ('audit.planning.p7.fraud', 'P-7 (Fraud Assessment)')
            ]:
                exists = self.env[model].search([
                    ('engagement_id', '=', engagement_id),
                    ('audit_year_id', '=', audit_year_id)
                ], limit=1)
                if not exists:
                    raise UserError(_(f'Cannot open P-10: {label} must be available.'))
        return super().create(vals)

    def write(self, vals):
        # Enforce completeness and mandatory uploads before locking
        if 'state' in vals and vals['state'] == 'locked':
            for rec in self:
                # At least two completeness procedures
                if not rec.completeness_procedures_multi or len(rec.completeness_procedures_multi) < 2:
                    raise UserError(_('At least two completeness procedures must be documented.'))
                # Mandatory attachments
                if not rec.attachment_ids or len(rec.attachment_ids) < 3:
                    raise UserError(_('All mandatory document uploads must be attached before locking.'))
        return super().write(vals)

    @api.constrains('completeness_procedures_multi')
    def _check_completeness_procedures(self):
        for rec in self:
            if rec.state == 'locked' and (not rec.completeness_procedures_multi or len(rec.completeness_procedures_multi) < 2):
                raise ValidationError(_('At least two completeness procedures must be documented.'))

    @api.constrains('attachment_ids')
    def _check_attachments(self):
        for rec in self:
            if rec.state == 'locked' and (not rec.attachment_ids or len(rec.attachment_ids) < 3):
                raise ValidationError(_('All mandatory document uploads must be attached before locking.'))

    # TODO: Implement auto-import of related parties from onboarding/prior year, auto-linking to P-6, P-7, P-8, P-12 as per system rules.

    @api.depends('partner_approval')
    def _compute_locked(self):
        for rec in self:
            rec.locked = bool(rec.partner_approval)

    def action_lock(self):
        for rec in self:
            if not rec.partner_approval:
                raise UserError('Partner approval required to lock P-10.')
            rec.write({'locked': True, 'state': 'locked'})

    # TODO: Add methods for auto-import, auto-linking, audit trail, and system rules


# SECTION A: Related Party (child)
class AuditPlanningP10RelatedParty(models.Model):
    _name = 'audit.planning.p10.related_party'
    _description = 'P-10: Related Party'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    related_parties_id = fields.Many2one('audit.planning.p10.related_parties', required=True, ondelete='cascade')
    name = fields.Char('Related Party Name', required=True)
    party_type = fields.Selection([
        ('parent', 'Parent'),
        ('subsidiary', 'Subsidiary'),
        ('associate', 'Associate / JV'),
        ('director', 'Director / KMP'),
        ('family', 'Close family member'),
        ('common_control', 'Entity under common control'),
    ], string='Party Type', required=True)
    relationship_nature = fields.Char('Relationship Nature & Basis', required=True)
    country = fields.Char('Country / Jurisdiction')
    changes_during_year = fields.Boolean('Changes during year?')
    changes_details = fields.Text('Details of changes (if any)')
    # Checklist fields
    known_identified = fields.Boolean('Known related party identified?')
    changes_captured = fields.Boolean('Changes during year captured?')


# SECTION C: RPT Transaction (child)
class AuditPlanningP10RPTTransaction(models.Model):
    _name = 'audit.planning.p10.rpt_transaction'
    _description = 'P-10: Related Party Transaction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    related_parties_id = fields.Many2one('audit.planning.p10.related_parties', required=True, ondelete='cascade')
    related_party_id = fields.Many2one('audit.planning.p10.related_party', string='Related Party', required=True)
    nature_of_transaction = fields.Char('Nature of Transaction', required=True)
    period = fields.Char('Period')
    amount = fields.Float('Amount')
    terms_arms_length = fields.Boolean('Terms (Arms’ length?)')
    approved_by_tcw = fields.Boolean('Approved by TCWG?')
    non_routine = fields.Boolean('Non-routine transaction?')


# SECTION D: RPT Risk Line (child)
class AuditPlanningP10RPTRiskLine(models.Model):
    _name = 'audit.planning.p10.rpt_risk_line'
    _description = 'P-10: RPT Risk Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    related_parties_id = fields.Many2one('audit.planning.p10.related_parties', required=True, ondelete='cascade')
    rpt_transaction_id = fields.Many2one('audit.planning.p10.rpt_transaction', string='RPT', required=True)
    business_purpose = fields.Char('Business Purpose')
    fraud_risk = fields.Boolean('Fraud Risk?')
    disclosure_risk = fields.Boolean('Disclosure Risk?')
    rpt_risk_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('significant', 'Significant'),
    ], string='RPT Risk Level')
    significant_flag = fields.Boolean('Significant Risk (auto-flag)', compute='_compute_significant_flag', store=True)
    partner_override = fields.Boolean('Partner Override?')

    @api.depends('rpt_transaction_id.non_routine', 'partner_override', 'rpt_risk_level')
    def _compute_significant_flag(self):
        for rec in self:
            rec.significant_flag = rec.rpt_risk_level == 'significant' or (rec.rpt_transaction_id and rec.rpt_transaction_id.non_routine and not rec.partner_override)


# Completeness Procedures (for Many2many)
class AuditP10CompletenessProcedure(models.Model):
    _name = 'audit.p10.completeness.procedure'
    _description = 'P-10: Completeness Procedure Option'
    name = fields.Char('Procedure', required=True)

# Planned Procedures (for Many2many)
class AuditP10AuditProcedure(models.Model):
    _name = 'audit.p10.audit_procedure'
    _description = 'P-10: Audit Procedure Option'
    name = fields.Char('Procedure', required=True)# -*- coding: utf-8 -*-
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
    _description = 'P-10: Related Parties & Group Considerations'
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
