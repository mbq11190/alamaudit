from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class QacoIndustry(models.Model):
    _name = 'qaco.industry'
    _description = 'Audit Industry Master Data'

    name = fields.Char(string='Industry Name', required=True)
    code = fields.Char(string='Industry Code', required=True)


class QacoBranchOffice(models.Model):
    _name = 'qaco.branch.office'
    _description = 'Branch Office Details'

    name = fields.Char(string='Branch Name', required=True)
    location = fields.Char(string='Location')
    city = fields.Char(string='City')
    province = fields.Char(string='Province')
    country = fields.Char(string='Country', default='Pakistan')
    phone = fields.Char(string='Phone')
    engagement_id = fields.Many2one('qaco.audit.engagement', string='Engagement', ondelete='cascade')


class QacoUBO(models.Model):
    _name = 'qaco.ubo'
    _description = 'Ultimate Beneficial Owner'

    name = fields.Char(string='Name', required=True)
    relation = fields.Char(string='Relation')
    ownership_percentage = fields.Float(string='Ownership Percentage')
    cnic = fields.Char(string='CNIC')
    engagement_id = fields.Many2one('qaco.audit.engagement', string='Engagement', ondelete='cascade')

    @api.constrains('cnic')
    def _check_cnic(self):
        for record in self:
            if record.cnic and (not record.cnic.isdigit() or len(record.cnic) != 13):
                raise ValidationError(_('CNIC for UBO must be 13 digits.'))


class QacoRegulatoryInspection(models.Model):
    _name = 'qaco.regulatory.inspection'
    _description = 'Regulatory Inspection History'

    name = fields.Char(string='Inspection Name', required=True)
    authority = fields.Char(string='Regulatory Authority')
    inspection_date = fields.Date(string='Inspection Date')
    findings = fields.Text(string='Findings')
    engagement_id = fields.Many2one('qaco.audit.engagement', string='Engagement', ondelete='cascade')


class QacoPep(models.Model):
    _name = 'qaco.pep'
    _description = 'Politically Exposed Person'

    name = fields.Char(string='Name', required=True)
    designation = fields.Char(string='Designation')
    country = fields.Char(string='Country', default='Pakistan')
    cnic = fields.Char(string='CNIC')
    engagement_id = fields.Many2one('qaco.audit.engagement', string='Engagement', ondelete='cascade')

    @api.constrains('cnic')
    def _check_cnic_pep(self):
        for record in self:
            if record.cnic and (not record.cnic.isdigit() or len(record.cnic) != 13):
                raise ValidationError(_('CNIC for PEP must be 13 digits.'))


class QacoAuditChecklist(models.Model):
    _name = 'qaco.audit.checklist'
    _description = 'Engagement Onboarding Checklist'

    engagement_id = fields.Many2one('qaco.audit.engagement', string='Engagement', required=True, ondelete='cascade')
    checklist_type = fields.Selection([
        ('acceptance', 'Acceptance & Continuance'),
        ('independence', 'Independence & Ethics'),
        ('isqm', 'ISQM Firm Risk Assessment')
    ], string='Checklist Type', required=True)
    question = fields.Char(string='Checklist Question', required=True)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('done', 'Done'),
        ('not_applicable', 'Not Applicable')
    ], default='pending', string='Status')
    note = fields.Text(string='Notes')


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
        tracking=True
    )
    client_id = fields.Many2one('res.partner', string='Client', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('onboarding', 'Onboarding'),
        ('planning', 'Planning'),
        ('execution', 'Execution'),
        ('finalisation', 'Finalisation'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    engagement_decision = fields.Selection([
        ('draft', 'Draft decision'),
        ('accept', 'Accept'),
        ('reject', 'Reject'),
        ('continue_conditions', 'Continue with conditions')
    ], string='Engagement Decision', default='draft', tracking=True)

    legal_name = fields.Char(string='Legal Name')
    trade_name = fields.Char(string='Trade Name')
    date_incorporation = fields.Date(string='Date of Incorporation')
    ntn = fields.Char(string='NTN', size=15)
    strn = fields.Char(string='STRN', size=13)
    entity_classification = fields.Selection([
        ('msc', 'Medium Sized Company'),
        ('ssc', 'Small Sized Company'),
        ('pic', 'Public Interest Company'),
        ('lsc', 'Listed/Supervised Company'),
        ('section_42', 'Section 42 Company'),
        ('npo', 'Non-Profit Organization'),
        ('sole_proprietor', 'Sole Proprietor'),
        ('partnership', 'Partnership'),
        ('other', 'Other')
    ], string='Entity Classification')
    regulatory_body = fields.Selection([
        ('secp', 'SECP'),
        ('sbp', 'SBP'),
        ('pemra', 'PEMRA'),
        ('pta', 'PTA'),
        ('ogra', 'OGRA'),
        ('drap', 'DRAP'),
        ('psx', 'PSX'),
        ('other', 'Other')
    ], string='Regulatory Body')
    industry_id = fields.Many2one('qaco.industry', string='Industry')
    registered_address = fields.Text(string='Registered Address')
    branch_office_ids = fields.One2many('qaco.branch.office', 'engagement_id', string='Branch Offices')
    ubo_ids = fields.One2many('qaco.ubo', 'engagement_id', string='Ultimate Beneficial Owners')

    reporting_framework = fields.Selection([
        ('ifrs', 'IFRS'),
        ('ifrs_sme', 'IFRS for SMEs'),
        ('companies_act', 'Companies Act'),
        ('npo', 'NPO Reporting'),
        ('special_purpose', 'Special Purpose')
    ], string='Reporting Framework')
    secp_status = fields.Selection([
        ('listed', 'Listed'),
        ('unlisted', 'Unlisted'),
        ('licensed', 'Licensed')
    ], string='SECP Status')
    stock_exchange = fields.Selection([
        ('psx', 'PSX'),
        ('none', 'None')
    ], string='Stock Exchange')
    last_annual_return = fields.Date(string='Last Annual Return')
    tax_compliance_rating = fields.Selection([
        ('a', 'A'),
        ('b', 'B'),
        ('c', 'C'),
        ('not_rated', 'Not Rated')
    ], string='Tax Compliance Rating')
    withholding_tax_status = fields.Selection([
        ('compliant', 'Compliant'),
        ('non_compliant', 'Non-Compliant'),
        ('not_applicable', 'Not Applicable')
    ], string='Withholding Tax Status')
    regulatory_inspection_ids = fields.One2many('qaco.regulatory.inspection', 'engagement_id', string='Regulatory Inspections')

    shareholding_pattern = fields.Text(string='Shareholding Pattern')
    board_composition = fields.Text(string='Board Composition')
    ceo_name = fields.Char(string='CEO Name')
    ceo_cnic = fields.Char(string='CEO CNIC')
    cfo_name = fields.Char(string='CFO Name')
    cfo_cnic = fields.Char(string='CFO CNIC')
    company_secretary = fields.Char(string='Company Secretary')
    company_secretary_membership = fields.Char(string='Company Secretary Membership')
    fit_proper_status = fields.Selection([
        ('compliant', 'Compliant'),
        ('review_required', 'Review Required'),
        ('non_compliant', 'Non-Compliant')
    ], string='Fit & Proper Status')
    pep_ids = fields.One2many('qaco.pep', 'engagement_id', string='PEP Records')

    management_integrity_rating = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5')
    ], string='Management Integrity Rating')
    reputation_assessment = fields.Text(string='Reputation Assessment')
    litigation_summary = fields.Text(string='Litigation Summary')
    fraud_history = fields.Boolean(string='Fraud History')
    fraud_history_details = fields.Text(string='Fraud History Details')
    regulatory_penalties = fields.Boolean(string='Regulatory Penalties')
    regulatory_penalties_details = fields.Text(string='Regulatory Penalties Details')
    aml_ctf_risk = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], string='AML / CTF Risk')
    business_risk_factors = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('very_high', 'Very High')
    ], string='Business Risk Factors')

    independence_threats = fields.Selection([
        ('none', 'None'),
        ('self_interest', 'Self-Interest'),
        ('self_review', 'Self-Review'),
        ('advocacy', 'Advocacy'),
        ('familiarity', 'Familiarity'),
        ('intimidation', 'Intimidation'),
        ('multiple', 'Multiple Threats')
    ], string='Independence Threats')
    safeguards_applied = fields.Text(string='Safeguards Applied')
    team_independence_confirmed = fields.Boolean(string='Team Independence Confirmed')
    prohibited_services_evaluated = fields.Boolean(string='Prohibited Services Evaluated')
    fee_dependency_percentage = fields.Float(string='Fee Dependency (%)')
    fee_dependency_acceptable = fields.Boolean(string='Fee Dependency Acceptable', compute='_compute_fee_dependency_acceptable', store=True)
    safeguards_documentation_required = fields.Boolean(string='Safeguard Documentation Required', compute='_compute_safeguards_required', store=True)
    partner_review_required = fields.Boolean(string='Partner Review Required', compute='_compute_partner_review_required', store=True)
    partner_review_completed = fields.Boolean(string='Partner Review Completed')

    previous_auditor_id = fields.Many2one('res.partner', string='Previous Auditor')
    professional_clearance_request_date = fields.Date(string='Clearance Requested')
    professional_clearance_response_date = fields.Date(string='Clearance Response')
    outstanding_fees = fields.Float(string='Outstanding Fees')
    professional_disagreements = fields.Text(string='Professional Disagreements')
    fraud_knowledge_previous = fields.Boolean(string='Fraud Knowledge Previously')
    fraud_knowledge_details = fields.Text(string='Fraud Knowledge Details')
    material_misstatements_previous = fields.Text(string='Material Misstatements from Previous Auditor')

    preconditions_met = fields.Boolean(string='Pre-conditions Met')
    management_responsibilities_acknowledged = fields.Boolean(string='Management Responsibilities Acknowledged')
    engagement_terms_understood = fields.Boolean(string='Engagement Terms Understood')
    eqcr_required = fields.Boolean(string='EQCR Required', compute='_compute_eqcr_required', store=True)
    eqcr_approved = fields.Boolean(string='EQCR Approved')
    eqcr_approval_date = fields.Date(string='EQCR Approval Date')
    risk_rating = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('very_high', 'Very High')
    ], string='Risk Rating', compute='_compute_risk_rating', store=True)

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

    checklist_ids = fields.One2many('qaco.audit.checklist', 'engagement_id', string='Checklists')
    acceptance_checklist_complete = fields.Boolean(string='Acceptance Checklist Complete', compute='_compute_checklist_completion', store=True)
    independence_checklist_complete = fields.Boolean(string='Independence Checklist Complete', compute='_compute_checklist_completion', store=True)
    isqm_checklist_complete = fields.Boolean(string='ISQM Checklist Complete', compute='_compute_checklist_completion', store=True)

    @api.depends('fee_dependency_percentage')
    def _compute_fee_dependency_acceptable(self):
        for record in self:
            record.fee_dependency_acceptable = bool(record.fee_dependency_percentage <= 15)

    @api.depends('aml_ctf_risk', 'business_risk_factors', 'management_integrity_rating')
    def _compute_risk_rating(self):
        risk_map = {'low': 1, 'medium': 2, 'high': 3, 'very_high': 4}
        integrity_map = {'1': 1, '2': 2, '3': 3, '4': 4, '5': 5}
        for record in self:
            total = integrity_map.get(record.management_integrity_rating or '1', 1)
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
            record.eqcr_required = record.aml_ctf_risk == 'high' or record.entity_classification in ('pic', 'lsc')

    @api.depends('independence_threats', 'fraud_history', 'regulatory_penalties', 'fraud_knowledge_previous', 'material_misstatements_previous', 'outstanding_fees', 'aml_ctf_risk')
    def _compute_partner_review_required(self):
        for record in self:
            issues = any([
                record.fraud_history,
                record.regulatory_penalties,
                record.fraud_knowledge_previous,
                bool(record.material_misstatements_previous),
                bool(record.outstanding_fees and record.outstanding_fees > 0)
            ])
            independence_issue = record.independence_threats and record.independence_threats != 'none'
            record.partner_review_required = bool(issues or independence_issue or record.aml_ctf_risk == 'high' or record.eqcr_required)

    @api.depends('independence_threats')
    def _compute_safeguards_required(self):
        for record in self:
            record.safeguards_documentation_required = bool(record.independence_threats and record.independence_threats != 'none')

    @api.depends('checklist_ids.status', 'checklist_ids.checklist_type')
    def _compute_checklist_completion(self):
        for record in self:
            types = {'acceptance': [], 'independence': [], 'isqm': []}
            for checklist in record.checklist_ids:
                types[checklist.checklist_type].append(checklist)
            record.acceptance_checklist_complete = all(item.status == 'done' for item in types['acceptance']) if types['acceptance'] else False
            record.independence_checklist_complete = all(item.status == 'done' for item in types['independence']) if types['independence'] else False
            record.isqm_checklist_complete = all(item.status == 'done' for item in types['isqm']) if types['isqm'] else False

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
                raise ValidationError(_('Preconditions and management responsibilities must be acknowledged before accepting.'))
            if record.partner_review_required and not record.partner_review_completed:
                raise ValidationError(_('Partner review is required before acceptance.'))
            record.state = 'onboarding'
            record.engagement_decision = 'accept'

    def action_request_partner_review(self):
        for record in self:
            if record.partner_review_required and not record.partner_review_completed:
                record.activity_schedule('mail.mail_activity_data_todo', note=_('Engagement partner review required.'))

    def action_mark_partner_review_complete(self):
        for record in self:
            record.partner_review_completed = True