
# -*- coding: utf-8 -*-
"""
P-10: Related Parties Planning (ISA 550)
=========================================
Standards Compliance:
- ISA 550: Related Parties
- ISA 315: Identifying and Assessing the Risks of Material Misstatement
- Companies Act, 2017 (Pakistan) - Section 36: Fraud and Error

Purpose:
Systematic identification and assessment of related party relationships
and transactions that may affect financial statement assertions.
=========================================
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


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

    # Sequential Gating (ISA 300/220: Systematic Planning Approach)
    can_open = fields.Boolean(
        string='Can Open This Tab',
        compute='_compute_can_open',
        store=False,
        help='P-10 can only be opened after P-9 is approved'
    )

    @api.depends('audit_id')
    def _compute_can_open(self):
        """P-10 requires P-9 to be approved."""
        for rec in self:
            if not rec.audit_id:
                rec.can_open = False
                continue
            # Find P-9 for this audit
            p9 = self.env['qaco.planning.p9.laws'].search([
                ('audit_id', '=', rec.audit_id.id)
            ], limit=1)
            rec.can_open = p9.state == 'approved' if p9 else False

    @api.constrains('state')
    def _check_sequential_gating(self):
        """ISA 300/220: Enforce sequential planning approach."""
        for rec in self:
            if rec.state != 'not_started' and not rec.can_open:
                raise UserError(
                    'ISA 300/220 & ISA 550 Violation: Sequential Planning Approach Required.\n\n'
                    'P-10 (Related Parties) cannot be started until P-9 (Laws & Regulations) '
                    'has been Partner-approved.\n\n'
                    'Reason: Related party identification per ISA 550 requires understanding of '
                    'compliance context and regulatory requirements from P-9.\n\n'
                    'Action: Please complete and obtain Partner approval for P-9 first.'
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
        default=lambda self: self._get_default_currency()
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

    # Section A: Confirmations (ISA 550.13)
    confirm_all_rp_identified = fields.Boolean(
        string='☐ All known related parties identified',
        help='Confirm all related parties have been identified per ISA 550.13',
        tracking=True
    )
    confirm_changes_captured = fields.Boolean(
        string='☐ Changes during the year captured',
        help='Confirm changes in related parties during the year have been documented',
        tracking=True
    )

    # ===== Section B: Completeness Procedures (ISA 550.13) =====
    # Structured Completeness Procedure Checkboxes
    completeness_inquiry_mgmt = fields.Boolean(
        string='☐ Inquiry of management & TCWG',
        help='ISA 550.13(a) - Inquire of management and TCWG regarding RP identification'
    )
    completeness_board_minutes = fields.Boolean(
        string='☐ Review of board minutes',
        help='ISA 550.13(b) - Review board and audit committee minutes'
    )
    completeness_declarations = fields.Boolean(
        string='☐ Review of declarations of interest',
        help='ISA 550.13(c) - Review declarations of interest from directors/KMP'
    )
    completeness_shareholder_records = fields.Boolean(
        string='☐ Review of shareholder records',
        help='ISA 550.13(d) - Review shareholder registers and ownership structure'
    )
    completeness_prior_year = fields.Boolean(
        string='☐ Review of prior-year working papers',
        help='ISA 550.13(e) - Review prior-year audit working papers for RP'
    )
    completeness_results = fields.Html(
        string='Results of Completeness Procedures (MANDATORY)',
        help='Document results of procedures performed per ISA 550.13 - REQUIRED',
    )
    completeness_procedures_count = fields.Integer(
        string='Procedures Performed Count',
        compute='_compute_completeness_count',
        store=True,
        help='System rule: Minimum 2 procedures required'
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
        help='Assessment of risks arising from related party relationships per ISA 550.16'
    )
    # XML view compatible alias
    rpt_risk_assessment = fields.Html(
        string='RPT Risk Assessment',
        related='rp_risk_assessment',
        readonly=False
    )

    # Section D: Business Purpose & Fraud Risk Assessment
    rpt_business_purpose_assessed = fields.Boolean(
        string='Business Purpose Assessed',
        help='ISA 550.16 - Business rationale for significant RPTs assessed'
    )
    rpt_business_purpose_narrative = fields.Html(
        string='Business Purpose Assessment',
        help='Document business rationale for significant related party transactions'
    )
    rpt_fraud_risk_identified = fields.Boolean(
        string='Fraud Risk Identified in RPTs',
        tracking=True,
        help='ISA 240 linkage - Have fraud risk indicators been identified in RPTs?'
    )

    rpt_fraud_indicators = fields.Html(
        string='Fraud Risk Indicators',
        help='Indicators of fraud risk related to related parties (ISA 240/550 linkage)'
    )
    significant_rp_transactions = fields.Html(
        string='Significant RP Transactions',
        help='Transactions requiring specific audit attention per ISA 550.17'
    )
    # XML view compatible alias
    significant_rpt_risks = fields.Html(
        string='Significant RPT Risks',
        related='significant_rp_transactions',
        readonly=False
    )

    # Section D: System Rule - Auto-Flag Significant RPTs
    unusual_rpt_flagged = fields.Boolean(
        string='Unusual RPTs Flagged as Significant Risk',
        compute='_compute_significant_rpt_flags',
        store=True,
        help='Auto-flagged if non-routine or unusual RPTs identified (system rule per ISA 550.17)'
    )
    arms_length_concerns = fields.Html(
        string="Arm's Length Concerns",
        help='Transactions that may not be at arm\'s length per ISA 550.18'
    )

    # Section E: Fraud & Concealment Considerations (ISA 240 Linkage)
    undisclosed_rp_risk = fields.Boolean(
        string='Risk of Undisclosed RPs',
        tracking=True,
        help='ISA 550.14 - Is there a risk of undisclosed related parties?'
    )
    management_dominance_indicators = fields.Boolean(
        string='Management Dominance or Override Indicators?',
        tracking=True,
        help='ISA 240.24 - Indicators of management override in RP context'
    )
    circular_transactions_identified = fields.Boolean(
        string='Circular Transactions Identified?',
        tracking=True,
        help='ISA 550.21 - Circular transactions or unusual patterns identified'
    )
    fraud_concealment_assessment = fields.Html(
        string='Auditor Assessment - Fraud & Concealment Risk',
        help='Assessment of fraud/concealment risks in RPT context per ISA 240/550'
    )

    # Section E: System Rule - Auto-Link to P-7 Fraud & P-6 RMM
    fraud_linkage_p7_required = fields.Boolean(
        string='P-7 Fraud Linkage Required',
        compute='_compute_fraud_gc_linkages',
        store=True,
        help='Auto-flagged if fraud indicators require P-7 update'
    )
    rmm_escalation_p6_required = fields.Boolean(
        string='P-6 RMM Escalation Required',
        compute='_compute_fraud_gc_linkages',
        store=True,
        help='Auto-flagged if RPT fraud risks require P-6 RMM escalation'
    )

    undisclosed_rp_procedures = fields.Html(
        string='Procedures for Undisclosed RPs',
        help='Procedures to identify undisclosed related parties per ISA 550.14'
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
        help='Applicable accounting standard for RP disclosures (IAS 24 / IFRS for SMEs)'
    )
    disclosure_risks = fields.Html(
        string='Disclosure Risks',
        help='Risks of inadequate or inaccurate RP disclosures per ISA 550.24'
    )
    disclosure_assessment = fields.Selection([
        ('adequate', '🟢 Likely Adequate'),
        ('concerns', '🟡 Some Concerns'),
        ('inadequate', '🔴 Likely Inadequate'),
        ('not_assessed', '⚪ Not Yet Assessed'),
    ], string='Disclosure Assessment')

    # Section F: Enhanced Disclosure Assessment
    risk_incomplete_disclosure = fields.Boolean(
        string='Risk of Incomplete Disclosure?',
        tracking=True,
        help='ISA 550.24 - Risk that RP disclosures may be incomplete'
    )
    enhanced_disclosure_areas = fields.Text(
        string='Areas Requiring Enhanced Disclosure',
        help='Specific areas where enhanced disclosure may be required'
    )

    # ===== Planned Audit Procedures =====
    planned_procedures = fields.Html(
        string='Planned Audit Procedures',
        help='Specific procedures for related party audit per ISA 550.19-23'
    )

    # Section G: Audit Responses to RPT Risks (ISA 330 / ISA 550.19)
    authorization_review = fields.Boolean(
        string='☐ Review Authorization of RP Transactions',
        help='ISA 550.20 - Review authorization and approval of RPTs'
    )
    terms_review = fields.Boolean(
        string='☐ Review Terms & Conditions',
        help='ISA 550.21 - Review terms and conditions of RPTs'
    )
    pricing_review = fields.Boolean(
        string='☐ Review Pricing/Valuation',
        help='ISA 550.18 - Review pricing/valuation for arm\'s length assessment'
    )
    procedure_confirmation = fields.Boolean(
        string='☐ Confirmation with Related Parties',
        help='ISA 505 - Obtain confirmations from related parties'
    )
    procedure_benchmarking = fields.Boolean(
        string='☐ Benchmarking Terms',
        help='ISA 550.18 - Benchmark RPT terms against market rates/third-party transactions'
    )
    disclosure_testing = fields.Boolean(
        string='☐ Test Disclosure Completeness',
        help='ISA 550.24 - Test completeness and accuracy of RP disclosures'
    )
    senior_team_involvement_required = fields.Boolean(
        string='Senior Team Involvement Required?',
        tracking=True,
        help='ISA 550.22 - Partner or senior team member involvement required for significant RPTs'
    )

    # Section G: System Rule - Auto-Flow to P-12
    responses_linked_to_p12 = fields.Boolean(
        string='Responses Linked to P-12 (Audit Strategy)',
        help='Indicate if RPT audit responses have been incorporated into P-12 Audit Strategy',
        tracking=True
    )

    # ===== Section H: Going Concern & Support Arrangements (ISA 570 Linkage) =====
    rpt_critical_to_liquidity = fields.Boolean(
        string='RPTs Critical to Liquidity/Going Concern?',
        tracking=True,
        help='ISA 570.16 - Are RPTs critical to entity\'s liquidity or support arrangements?'
    )
    gc_support_nature = fields.Text(
        string='Nature of Support (Loans, Guarantees, Waivers)',
        help='Describe nature of going concern support from related parties'
    )
    enforceability_assessed = fields.Boolean(
        string='Enforceability Assessed?',
        tracking=True,
        help='ISA 570.16 - Has enforceability of related party support been assessed?'
    )
    gc_disclosure_impact = fields.Boolean(
        string='Going Concern Disclosure Impact Assessed?',
        tracking=True,
        help='ISA 570.19 - Disclosure impact of RP support on going concern assessed'
    )
    gc_support_assessment = fields.Html(
        string='Going Concern Support Assessment',
        help='Detailed assessment of related party support arrangements per ISA 570'
    )

    # Section H: System Rule - Auto-Link to P-8 Going Concern
    gc_linkage_p8_required = fields.Boolean(
        string='P-8 Going Concern Linkage Required',
        compute='_compute_fraud_gc_linkages',
        store=True,
        help='Auto-flagged if RPT support impacts P-8 going concern assessment'
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

    # ===== Section J: P-10 Conclusion & Professional Judgment =====
    rp_risk_summary = fields.Html(
        string='Related Party Risk Memo (MANDATORY)',
        help='Consolidated related party assessment per ISA 550'
    )
    # XML view compatible alias
    rpt_conclusion = fields.Html(
        string='Related Parties Conclusion',
        related='rp_risk_summary',
        readonly=False
    )

    # Section J: Final Confirmations (Mandatory Before Approval)
    confirm_rp_complete = fields.Boolean(
        string='☐ Related parties complete',
        help='Confirm all related parties have been identified and assessed per ISA 550',
        tracking=True
    )
    confirm_rpt_risks_assessed = fields.Boolean(
        string='☐ RPT risks assessed and linked',
        help='Confirm RPT risks assessed and linked to P-6 (RMM), P-7 (Fraud), P-8 (GC)',
        tracking=True
    )
    confirm_audit_responses_established = fields.Boolean(
        string='☐ Basis established for audit responses',
        help='Confirm basis established for audit responses per ISA 550.19',
        tracking=True
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

    # ============================================================================
    # PROMPT 3: Safe HTML Default Template (Set in create, not field default)
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Set HTML defaults safely in create() to avoid registry crashes."""  
        rp_risk_template = '''
<p><strong>P-10: Related Parties Planning (ISA 550)</strong></p>
<p>Related parties and related party transactions have been identified, assessed for completeness, and evaluated for risk in accordance with ISA 550. Appropriate audit responses and disclosure considerations have been determined.</p>
<ol>
<li><strong>Related Parties Identified:</strong> [Summarize key related parties by category]</li>
<li><strong>Completeness Assessment:</strong> [Summarize procedures performed per ISA 550.13]</li>
<li><strong>Significant RPTs:</strong> [List significant related party transactions]</li>
<li><strong>Risk Assessment:</strong> [Overall RPT risk level and key risks identified]</li>
<li><strong>Fraud & Concealment Considerations:</strong> [ISA 240/550 linkage]</li>
<li><strong>Disclosure Assessment:</strong> [IAS 24 compliance and disclosure risks]</li>
<li><strong>Audit Responses:</strong> [Planned procedures per ISA 550.19-23]</li>
<li><strong>Going Concern Implications:</strong> [If applicable - ISA 570 linkage]</li>
</ol>
<p><strong>Conclusion:</strong> [State overall conclusion on RPT risks and audit strategy implications]</p>
'''
        for vals in vals_list:
            if 'rp_risk_summary' not in vals:
                vals['rp_risk_summary'] = rp_risk_template
        return super().create(vals_list)

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
        
        # Section B: Completeness procedures (minimum 2 required per system rule)
        if self.completeness_procedures_count < 2:
            errors.append('Section B: At least 2 completeness procedures must be performed per ISA 550.13')
        if not self.completeness_results:
            errors.append('Section B: Results of completeness procedures must be documented (MANDATORY)')
        
        # Basic understanding
        if not self.understanding_obtained:
            errors.append('Understanding of related parties must be obtained')
        
        # Section J: Mandatory document uploads
        if not self.declarations_attachment_ids:
            errors.append('Section I: Management declarations of interest must be uploaded (MANDATORY)')
        if not self.board_minutes_attachment_ids:
            errors.append('Section I: Board/audit committee minutes must be uploaded (MANDATORY)')
        if not self.rpt_contracts_attachment_ids:
            errors.append('Section I: RPT agreements/contracts must be uploaded (MANDATORY)')
        if not self.prior_year_rpt_attachment_ids:
            errors.append('Section I: Prior-year RPT schedules must be uploaded (MANDATORY)')
        
        # Section J: Conclusion and confirmations
        if not self.rp_risk_summary:
            errors.append('Section J: Related party risk memo is required')
        if not self.confirm_rp_complete:
            errors.append('Section J: Confirm related parties complete')
        if not self.confirm_rpt_risks_assessed:
            errors.append('Section J: Confirm RPT risks assessed and linked')
        if not self.confirm_audit_responses_established:
            errors.append('Section J: Confirm basis established for audit responses')
        
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
            record.message_post(body='P-10 Related Parties Planning approved by Partner.')
            # Section K: Auto-unlock P-11 Group Audit Planning
            record._auto_unlock_p11()

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

    def _auto_unlock_p11(self):
        """Section K: Auto-unlock P-11 Group Audit Planning when P-10 is approved."""
        self.ensure_one()
        if not self.audit_id:
            return
        
        # Find or create P-11 record
        P11 = self.env['qaco.planning.p11.group.audit']
        p11_record = P11.search([('audit_id', '=', self.audit_id.id)], limit=1)
        
        if p11_record and p11_record.state == 'locked':
            p11_record.write({'state': 'not_started'})
            p11_record.message_post(
                body='P-11 Group Audit Planning auto-unlocked after P-10 Related Parties approval.'
            )
            _logger.info(f'P-11 auto-unlocked for audit {self.audit_id.name}')
        elif not p11_record:
            # Create new P-11 record if doesn't exist
            p11_record = P11.create({
                'audit_id': self.audit_id.id,
                'state': 'not_started',
            })
            _logger.info(f'P-11 auto-created for audit {self.audit_id.name}')

    # ===== COMPUTE METHODS: System Rules =====

    @api.depends('completeness_inquiry_mgmt', 'completeness_board_minutes', 
                 'completeness_declarations', 'completeness_shareholder_records', 
                 'completeness_prior_year')
    def _compute_completeness_count(self):
        """Section B: Count completeness procedures performed (minimum 2 required per system rule)."""
        for record in self:
            record.completeness_procedures_count = sum([
                record.completeness_inquiry_mgmt,
                record.completeness_board_minutes,
                record.completeness_declarations,
                record.completeness_shareholder_records,
                record.completeness_prior_year,
            ])

    @api.depends('significant_rpt_identified', 'rpt_fraud_risk_identified')
    def _compute_significant_rpt_flags(self):
        """Section D: Auto-flag if non-routine or unusual RPTs identified as significant risk."""
        for record in self:
            # Auto-flag if significant RPTs identified or fraud risk in RPTs
            record.unusual_rpt_flagged = (
                record.significant_rpt_identified or 
                record.rpt_fraud_risk_identified
            )

    @api.depends('rpt_fraud_risk_identified', 'management_dominance_indicators', 
                 'circular_transactions_identified', 'rpt_critical_to_liquidity')
    def _compute_fraud_gc_linkages(self):
        """Section E & H: Auto-flag if fraud/GC linkages required to P-6, P-7, P-8."""
        for record in self:
            # Section E: Fraud linkage to P-7 if fraud indicators in RPTs
            record.fraud_linkage_p7_required = any([
                record.rpt_fraud_risk_identified,
                record.management_dominance_indicators,
                record.circular_transactions_identified
            ])
            
            # Section E: RMM escalation to P-6 if fraud risks material
            record.rmm_escalation_p6_required = (
                record.fraud_linkage_p7_required and record.significant_rpt_identified
            )
            
            # Section H: GC linkage to P-8 if RPT support critical
            record.gc_linkage_p8_required = record.rpt_critical_to_liquidity


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
    country_jurisdiction = fields.Char(
        string='Country / Jurisdiction',
        help='Country or jurisdiction where related party is located'
    )
    changes_during_year = fields.Boolean(
        string='Changes During Year?',
        help='Has this relationship changed during the year?'
    )
    change_details = fields.Text(
        string='Change Details',
        help='Details of changes in relationship during the year'
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
    period = fields.Selection([
        ('q1', 'Q1'),
        ('q2', 'Q2'),
        ('q3', 'Q3'),
        ('q4', 'Q4'),
        ('annual', 'Annual'),
    ], string='Period', help='Period when transaction occurred')
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
    tcwg_approved = fields.Boolean(
        string='Approved by TCWG?',
        help='Has this transaction been approved by those charged with governance?'
    )
    disclosure_risk = fields.Selection([
        ('low', '🟢 Low'),
        ('medium', '🟡 Medium'),
        ('high', '🔴 High'),
    ], string='Disclosure Risk')
