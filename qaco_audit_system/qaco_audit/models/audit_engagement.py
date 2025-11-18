from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class QacoAuditEngagement(models.Model):
    _name = 'qaco.audit.engagement'
    _description = 'Audit Engagement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(
        string='Engagement Reference',
        required=True,
        copy=False,
        default=lambda self: self.env['ir.sequence'].next_by_code('qaco.audit.engagement') or '/',
        tracking=True,
    )
    client_id = fields.Many2one('res.partner', string='Client', required=True, tracking=True)
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('onboarding', 'Onboarding'),
            ('planning', 'Planning'),
            ('execution', 'Execution'),
            ('finalisation', 'Finalisation'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        tracking=True,
    )
    engagement_decision = fields.Selection(
        [
            ('draft', 'Draft decision'),
            ('accept', 'Accept'),
            ('reject', 'Reject'),
            ('continue_conditions', 'Continue with conditions'),
        ],
        string='Engagement Decision',
        default='draft',
        tracking=True,
    )

    # Onboarding section
    legal_name = fields.Char(string='Legal Name')
    trade_name = fields.Char(string='Trade Name')
    date_incorporation = fields.Date(string='Date of Incorporation')
    ntn = fields.Char(string='NTN', size=15)
    strn = fields.Char(string='STRN', size=13)
    entity_classification = fields.Selection(
        [
            ('msc', 'Medium Sized Company'),
            ('ssc', 'Small Sized Company'),
            ('pic', 'Public Interest Company'),
            ('lsc', 'Listed/Supervised Company'),
            ('section_42', 'Section 42 Company'),
            ('npo', 'Non-Profit Organization'),
            ('sole_proprietor', 'Sole Proprietor'),
            ('partnership', 'Partnership'),
            ('other', 'Other'),
        ],
        string='Entity Classification',
    )
    regulatory_body = fields.Selection(
        [
            ('secp', 'SECP'),
            ('sbp', 'SBP'),
            ('pemra', 'PEMRA'),
            ('pta', 'PTA'),
            ('ogra', 'OGRA'),
            ('drap', 'DRAP'),
            ('psx', 'PSX'),
            ('other', 'Other'),
        ],
        string='Regulatory Body',
    )
    industry_id = fields.Many2one('qaco.industry', string='Industry')
    registered_address = fields.Text(string='Registered Address')
    branch_office_ids = fields.One2many('qaco.branch.office', 'engagement_id', string='Branch Offices')
    ubo_ids = fields.One2many('qaco.ubo', 'engagement_id', string='Ultimate Beneficial Owners')

    # Regulatory profile
    reporting_framework = fields.Selection(
        [
            ('ifrs', 'IFRS'),
            ('ifrs_sme', 'IFRS for SMEs'),
            ('companies_act', 'Companies Act'),
            ('npo', 'NPO Reporting'),
            ('special_purpose', 'Special Purpose'),
        ],
        string='Reporting Framework',
    )
    secp_status = fields.Selection([('listed', 'Listed'), ('unlisted', 'Unlisted'), ('licensed', 'Licensed')], string='SECP Status')
    stock_exchange = fields.Selection([('psx', 'PSX'), ('none', 'None')], string='Stock Exchange')
    last_annual_return = fields.Date(string='Last Annual Return')
    tax_compliance_rating = fields.Selection([('a', 'A'), ('b', 'B'), ('c', 'C'), ('not_rated', 'Not Rated')], string='Tax Compliance Rating')
    withholding_tax_status = fields.Selection([('compliant', 'Compliant'), ('non_compliant', 'Non-Compliant'), ('not_applicable', 'Not Applicable')], string='Withholding Tax Status')
    regulatory_inspection_ids = fields.One2many('qaco.regulatory.inspection', 'engagement_id', string='Regulatory Inspections')

    # Ownership & governance
    shareholding_pattern = fields.Text(string='Shareholding Pattern')
    board_composition = fields.Text(string='Board Composition')
    ceo_name = fields.Char(string='CEO Name')
    ceo_cnic = fields.Char(string='CEO CNIC')
    cfo_name = fields.Char(string='CFO Name')
    cfo_cnic = fields.Char(string='CFO CNIC')
    company_secretary = fields.Char(string='Company Secretary')
    company_secretary_membership = fields.Char(string='Company Secretary Membership')
    fit_proper_status = fields.Selection([('compliant', 'Compliant'), ('review_required', 'Review Required'), ('non_compliant', 'Non-Compliant')], string='Fit & Proper Status')
    pep_ids = fields.One2many('qaco.pep', 'engagement_id', string='PEP Records')

    # Risk assessment
    management_integrity_rating = fields.Selection([('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')], string='Management Integrity Rating')
    reputation_assessment = fields.Text(string='Reputation Assessment')
    litigation_summary = fields.Text(string='Litigation Summary')
    fraud_history = fields.Boolean(string='Fraud History')
    fraud_history_details = fields.Text(string='Fraud History Details')
    regulatory_penalties = fields.Boolean(string='Regulatory Penalties')
    regulatory_penalties_details = fields.Text(string='Regulatory Penalties Details')
    aml_ctf_risk = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], string='AML / CTF Risk')
    business_risk_factors = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('very_high', 'Very High')], string='Business Risk Factors')

    # Independence & ethics
    independence_threats = fields.Selection(
        [
            ('none', 'None'),
            ('self_interest', 'Self-Interest'),
            ('self_review', 'Self-Review'),
            ('advocacy', 'Advocacy'),
            ('familiarity', 'Familiarity'),
            ('intimidation', 'Intimidation'),
            ('multiple', 'Multiple Threats'),
        ],
        string='Independence Threats',
    )
    safeguards_applied = fields.Text(string='Safeguards Applied')
    team_independence_confirmed = fields.Boolean(string='Team Independence Confirmed')
    prohibited_services_evaluated = fields.Boolean(string='Prohibited Services Evaluated')
    fee_dependency_percentage = fields.Float(string='Fee Dependency (%)')
    fee_dependency_acceptable = fields.Boolean(string='Fee Dependency Acceptable', compute='_compute_fee_dependency_acceptable', store=True)

    # Previous auditor
    previous_auditor_id = fields.Many2one('res.partner', string='Previous Auditor')
    professional_clearance_request_date = fields.Date(string='Clearance Requested')
    professional_clearance_response_date = fields.Date(string='Clearance Response')
    outstanding_fees = fields.Float(string='Outstanding Fees')
    professional_disagreements = fields.Text(string='Professional Disagreements')
    fraud_knowledge_previous = fields.Boolean(string='Fraud Knowledge Previously')
    fraud_knowledge_details = fields.Text(string='Fraud Knowledge Details')
    material_misstatements_previous = fields.Text(string='Material Misstatements from Previous Auditor')

    # Engagement authorization
    preconditions_met = fields.Boolean(string='Pre-conditions Met')
    management_responsibilities_acknowledged = fields.Boolean(string='Management Responsibilities Acknowledged')
    engagement_terms_understood = fields.Boolean(string='Engagement Terms Understood')
    eqcr_required = fields.Boolean(string='EQCR Required', compute='_compute_eqcr_required', store=True)
    eqcr_approved = fields.Boolean(string='EQCR Approved')
    eqcr_approval_date = fields.Date(string='EQCR Approval Date')
    risk_rating = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('very_high', 'Very High')], string='Risk Rating', compute='_compute_risk_rating', store=True)

    # Documents checklist
    doc_certificate_incorporation = fields.Boolean(string='Certificate of Incorporation')
    doc_moa_aoa = fields.Boolean(string='MOA/AOA')
    doc_audited_fs_3years = fields.Boolean(string='Audited FS - 3 Years')
    doc_prior_management_letters = fields.Boolean(string='Prior Management Letters')
    doc_legal_cases = fields.Boolean(string='Legal Cases')
    doc_aml_kyc = fields.Boolean(string='AML KYC')
    doc_independence_confirmations = fields.Boolean(string='Independence Confirmations')
    doc_professional_clearance = fields.Boolean(string='Professional Clearance')
    doc_engagement_letter_signed = fields.Boolean(string='Engagement Letter Signed')
    doc_conflict_declarations = fields.Boolean(string='Conflict Declarations')

    @api.depends('fee_dependency_percentage')
    def _compute_fee_dependency_acceptable(self):
        for record in self:
            record.fee_dependency_acceptable = bool(record.fee_dependency_percentage <= 15)

    @api.depends('aml_ctf_risk', 'business_risk_factors', 'management_integrity_rating')
    def _compute_risk_rating(self):
        risk_map = {'low': 1, 'medium': 2, 'high': 3, 'very_high': 4}
        integrity_map = {'1': 1, '2': 2, '3': 3, '4': 4, '5': 5}
        for record in self:
            total = 0
            total += integrity_map.get(record.management_integrity_rating or '1', 1)
            total += risk_map.get(record.aml_ctf_risk or 'low', 1)
            total += risk_map.get(record.business_risk_factors or 'low', 1)
            if total <= 4:
                record.risk_rating = 'low'
            elif total <= 6:
                record.risk_rating = 'medium'
            elif total <= 9:
                record.risk_rating = 'high'
            else:
                record.risk_rating = 'very_high'

    @api.depends('aml_ctf_risk', 'entity_classification')
    def _compute_eqcr_required(self):
        for record in self:
            high_aml = record.aml_ctf_risk == 'high'
            pic_lsc = record.entity_classification in ['pic', 'lsc']
            record.eqcr_required = high_aml or pic_lsc

    @api.constrains('ntn')
    def _check_ntn(self):
        for record in self:
            if record.ntn and (not record.ntn.isdigit() or len(record.ntn) != 15):
                raise ValidationError(_('NTN must be a 15-digit number.'))

    @api.constrains('strn')
    def _check_strn(self):
        for record in self:
            if record.strn and (not record.strn.isdigit() or len(record.strn) != 13):
                raise ValidationError(_('STRN must be a 13-digit number.'))

    def action_accept_engagement(self):
        for record in self:
            if not record.preconditions_met or not record.management_responsibilities_acknowledged:
                raise UserError(_('Preconditions and management responsibilities must be acknowledged before accepting.'))
            record.state = 'onboarding'
            record.engagement_decision = 'accept'

    def action_reject_engagement(self):
        for record in self:
            record.state = 'cancelled'
            record.engagement_decision = 'reject'

    def action_send_professional_clearance(self):
        template = self.env.ref('qaco_audit.email_template_professional_clearance', raise_if_not_found=False)
        if template:
            for record in self:
                template.send_mail(record.id, force_send=True)
        else:
            raise UserError(_('Professional clearance template is missing.'))

    def action_request_eqcr(self):
        for record in self:
            if record.eqcr_required and not record.eqcr_approved:
                record.activity_schedule('mail.mail_activity_data_todo', user_id=self.env.ref('base.user_root').id, note=_('EQCR review required.'))