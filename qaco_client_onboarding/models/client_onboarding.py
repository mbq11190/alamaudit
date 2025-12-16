# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

try:
    from odoo.addons.qaco_client_onboarding.models.audit_compliance import ONBOARDING_AREAS  # type: ignore
except ImportError:  # pragma: no cover - fallback for static analysis or path issues
    from .audit_compliance import ONBOARDING_AREAS  # type: ignore
import re

ENTITY_SELECTION = [
    ('pic', 'Public Interest Company (PIC)'),
    ('lsc', 'Large-Sized Company (LSC)'),
    ('msc', 'Medium-Sized Company (MSC)'),
    ('ssc', 'Small-Sized Company (SSC)'),
    ('section_42', 'Section 42 Company'),
    ('npo', 'Not-for-Profit Organization (NPO)'),
    ('sole', 'Sole Proprietorship'),
    ('partnership', 'Partnership'),
    ('other', 'Other (Specify)'),
]

PRIMARY_REGULATOR_SELECTION = [
    ('secp', 'SECP'),
    ('sbp', 'SBP'),
    ('pemra', 'PEMRA'),
    ('pta', 'PTA'),
    ('fbr', 'FBR'),
    ('provincial', 'Provincial Authority'),
    ('other', 'Other (Specify)'),
]

FINANCIAL_FRAMEWORK_SELECTION = [
    ('ifrs', 'IFRS as adopted by ICAP'),
    ('ifrs_smes', 'IFRS for SMEs'),
    ('companies_act', 'Companies Act 2017 Schedules'),
    ('other_framework', 'Other (Specify)'),
]

SECTION_STATUS = [
    ('red', 'Not Started'),
    ('amber', 'In Progress / Attention Required'),
    ('green', 'Complete & Compliant'),
]

AML_RATING = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
]

MANAGEMENT_INTEGRITY_SELECTION = [
    ('high', 'High'),
    ('medium', 'Medium'),
    ('low', 'Low'),
]

ENGAGEMENT_DECISION_SELECTION = [
    ('accept', 'Accept'),
    ('reject', 'Reject'),
    ('conditions', 'Subject to Conditions'),
]

THREAT_TYPES = [
    ('self_interest', 'Self-Interest Threat'),
    ('self_review', 'Self-Review Threat'),
    ('advocacy', 'Advocacy Threat'),
    ('familiarity', 'Familiarity Threat'),
    ('intimidation', 'Intimidation Threat'),
]

DOCUMENT_STATES = [
    ('pending', 'Pending'),
    ('received', 'Received'),
    ('reviewed', 'Reviewed'),
]

DOCUMENT_TYPE_SELECTION = [
    ('org_chart', 'Organizational Chart'),
    ('legal', 'Legal Register'),
    ('pcl', 'Professional Clearance Letter'),
    ('other', 'Other'),
]

CHECKLIST_ANSWER_SELECTION = [
    ('compliant', 'Compliant'),
    ('non_compliant', 'Non-Compliant'),
    ('na', 'Not Applicable'),
]

ONBOARDING_STATUS = [
    ('draft', 'Draft'),
    ('under_review', 'Under Review'),
    ('partner_approved', 'Partner Approved'),
    ('locked', 'Locked'),
]


ENTITY_LABELS = dict(ENTITY_SELECTION)
PRIMARY_REGULATOR_LABELS = dict(PRIMARY_REGULATOR_SELECTION)
FINANCIAL_FRAMEWORK_LABELS = dict(FINANCIAL_FRAMEWORK_SELECTION)
MANAGEMENT_INTEGRITY_LABELS = dict(MANAGEMENT_INTEGRITY_SELECTION)
AML_RATING_LABELS = dict(AML_RATING)
SECTION_STATUS_LABELS = dict(SECTION_STATUS)
ENGAGEMENT_DECISION_LABELS = dict(ENGAGEMENT_DECISION_SELECTION)


class ClientOnboarding(models.Model):
    _name = 'qaco.client.onboarding'
    _description = 'Client Onboarding'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Onboarding Title', compute='_compute_name', store=True)
    audit_id = fields.Many2one('qaco.audit', string='Audit', required=True, ondelete='cascade')
    client_id = fields.Many2one('res.partner', string='Client', related='audit_id.client_id', readonly=True, store=True)

    # Section 0: Gateway fields
    entity_type = fields.Selection(ENTITY_SELECTION, string='Entity Type', tracking=True)
    other_entity_description = fields.Char(string='Specify Other Entity Type')
    entity_type_guidance = fields.Char(string='Entity Gateway Guidance', default='Select the entity classification that dictates mandatory thresholds, regulatory obligations, and risk profiles.')
    state = fields.Selection(ONBOARDING_STATUS, string='Approval Status', default='draft', tracking=True)
    overall_status = fields.Selection(SECTION_STATUS, string='Onboarding Status', compute='_compute_overall_status', store=True, tracking=True, default='red')
    progress_percentage = fields.Float(string='Completion Progress', compute='_compute_progress', store=True)
    section1_status = fields.Selection(SECTION_STATUS, string='Section 1 Status', compute='_compute_section_status', store=True)
    section2_status = fields.Selection(SECTION_STATUS, string='Section 2 Status', compute='_compute_section_status', store=True)
    section3_status = fields.Selection(SECTION_STATUS, string='Section 3 Status', compute='_compute_section_status', store=True)
    section4_status = fields.Selection(SECTION_STATUS, string='Section 4 Status', compute='_compute_section_status', store=True)
    section5_status = fields.Selection(SECTION_STATUS, string='Section 5 Status', compute='_compute_section_status', store=True)
    section6_status = fields.Selection(SECTION_STATUS, string='Section 6 Status', compute='_compute_section_status', store=True)
    section7_status = fields.Selection(SECTION_STATUS, string='Section 7 Status', compute='_compute_section_status', store=True)
    section8_status = fields.Selection(SECTION_STATUS, string='Section 8 Status', compute='_compute_section_status', store=True)
    section9_status = fields.Selection(SECTION_STATUS, string='Section 9 Status', compute='_compute_section_status', store=True)
    section10_status = fields.Selection(SECTION_STATUS, string='Section 10 Status', compute='_compute_section_status', store=True)
    entity_type_label = fields.Char(string='Entity Type Label', compute='_compute_selection_labels')
    primary_regulator_label = fields.Char(string='Primary Regulator Label', compute='_compute_selection_labels')
    financial_framework_label = fields.Char(string='Financial Framework Label', compute='_compute_selection_labels')
    management_integrity_label = fields.Char(string='Management Integrity Label', compute='_compute_selection_labels')
    aml_risk_label = fields.Char(string='AML Risk Label', compute='_compute_selection_labels')
    overall_status_label = fields.Char(string='Overall Status Label', compute='_compute_selection_labels')
    engagement_decision_label = fields.Char(string='Engagement Decision Label', compute='_compute_selection_labels')
    audit_standard_ids = fields.Many2many('audit.standard.library', string='Auditing Standards & References', tracking=True)
    audit_standard_overview = fields.Html(string='Selected Standards Overview', compute='_compute_audit_standard_overview', sanitize=False)
    regulator_checklist_line_ids = fields.One2many('audit.onboarding.checklist', 'onboarding_id', string='Regulator Onboarding Checklist')
    high_risk_onboarding = fields.Boolean(string='High-Risk Onboarding', compute='_compute_high_risk', store=True)
    regulator_checklist_completion = fields.Float(string='Mandatory Checklist Completion %', compute='_compute_regulator_checklist_completion', store=True)
    regulator_checklist_overview = fields.Html(string='Checklist Summary', compute='_compute_regulator_checklist_overview', sanitize=False)

    # Section 1: Legal Identity
    legal_name = fields.Char(string='Legal Name')
    trading_name = fields.Char(string='Trading Name')
    principal_business_address = fields.Char(string='Principal Business Address')
    branch_location_ids = fields.One2many('qaco.onboarding.branch.location', 'onboarding_id', string='Branch and Office Locations')
    ntn = fields.Char(string='NTN', help='Enter in format 1234567-1')
    strn = fields.Char(string='STRN', help='State the Sales Tax Registration Number if applicable')
    business_registration_number = fields.Char(string='Business Registration Number')
    industry_id = fields.Many2one('qaco.onboarding.industry', string='Industry / Sector')
    primary_regulator = fields.Selection(PRIMARY_REGULATOR_SELECTION, string='Primary Regulator')
    regulator_other = fields.Char(string='Other Regulator Details')
    org_chart_attachment = fields.Binary(string='Group Structure / Org Chart')
    org_chart_name = fields.Char(string='Org Chart File Name')
    ubo_ids = fields.One2many('qaco.onboarding.ubo', 'onboarding_id', string='Ultimate Beneficial Owners')

    # Section 2: Compliance History
    financial_framework = fields.Selection(FINANCIAL_FRAMEWORK_SELECTION, string='Applicable Framework')
    financial_framework_other = fields.Char(string='Other Framework Details')
    annual_return_last_filed = fields.Date(string='Annual Return Last Filed')
    annual_return_overdue = fields.Boolean(string='Return Overdue', default=False)
    fbr_compliance_rating = fields.Selection([('atl', 'ATL'), ('btl', 'BTL'), ('provisional', 'Provisional')], string='FBR Compliance Rating')
    tax_assessment_history = fields.Text(string='Tax Assessment / Litigation History')
    regulatory_inspection_notes = fields.Text(string='Regulatory Inspection Summary')
    regulatory_inspection_attachment = fields.Binary(string='Inspection Documents')

    # Section 3: Ownership & Governance
    shareholder_ids = fields.One2many('qaco.onboarding.shareholder', 'onboarding_id', string='Shareholding Pattern')
    board_member_ids = fields.One2many('qaco.onboarding.board.member', 'onboarding_id', string='Board & Key Personnel')
    fit_proper_confirmed = fields.Boolean(string='Fit & Proper Checks Completed')
    fit_proper_document = fields.Binary(string='Fit & Proper Evidence')
    has_pep = fields.Boolean(string='Politically Exposed Person Identified', compute='_compute_pep_flag', store=True)
    enhanced_due_diligence_required = fields.Boolean(string='Enhanced Due Diligence Required', compute='_compute_pep_flag', store=True)
    enhanced_due_diligence_details = fields.Text(string='Enhanced Due Diligence Notes')
    enhanced_due_diligence_attachment = fields.Binary(string='Enhanced Due Diligence Documentation')

    # Section 4: Pre-Acceptance Risk
    management_integrity_rating = fields.Selection(MANAGEMENT_INTEGRITY_SELECTION, string='Management Integrity Rating')
    management_integrity_comment = fields.Text(string='Management Integrity Justification')
    litigation_history = fields.Text(string='Litigation History')
    fraud_history = fields.Selection([('no', 'No'), ('yes', 'Yes')], string='History of Fraud or Penalties', default='no')
    fraud_explanation = fields.Text(string='Fraud or Penalty Details')
    aml_risk_rating = fields.Selection(AML_RATING, string='AML/CTF Risk Rating', compute='_compute_aml_risk_rating', store=True)
    business_risk_profile = fields.Text(string='Business Risk Profile')
    risk_mitigation_plan = fields.Text(string='Risk Mitigation Plan')
    eqcr_required = fields.Boolean(string='EQCR Required', compute='_compute_eqcr_required', store=True)
    managing_partner_escalation = fields.Boolean(string='Managing Partner Escalation', compute='_compute_eqcr_required', store=True)

    # Section 5: Independence & Ethics
    independence_threat_ids = fields.One2many('qaco.onboarding.independence.threat', 'onboarding_id', string='Independence Threat Checklist')
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, default=lambda self: self.env.company.currency_id)
    non_audit_services_confirmed = fields.Boolean(string='Non-Audit Services Evaluation Completed')
    non_audit_services_attachment = fields.Binary(string='Non-Audit Services Supporting Document')
    proposed_audit_fee = fields.Monetary(currency_field='currency_id', string='Proposed Audit Fee')
    total_fee_income = fields.Monetary(currency_field='currency_id', string='Total Firm Fee Income')
    fee_dependency_percent = fields.Float(string='Fee Dependency (%)', compute='_compute_fee_dependency', store=True)
    fee_dependency_flag = fields.Boolean(string='Fee Dependency Flag', compute='_compute_fee_dependency', store=True)
    independence_declaration_ids = fields.One2many('qaco.onboarding.independence.declaration', 'onboarding_id', string='Team Independence Declarations')
    independence_status_feedback = fields.Text(string='Independence Declaration Status Summary', compute='_compute_independence_status')

    # Section 6: Predecessor Auditor Communication
    predecessor_auditor_name = fields.Char(string='Predecessor Auditor Name')
    predecessor_contact = fields.Char(string='Predecessor Contact Details')
    pcl_requested = fields.Date(string='PCL Date Requested')
    pcl_received = fields.Date(string='PCL Date Received')
    pcl_document = fields.Binary(string='Professional Clearance Letter')
    pcl_document_name = fields.Char(string='PCL File Name')
    pcl_no_outstanding_fees = fields.Boolean(string='PCL confirms no outstanding fees')
    pcl_no_disputes = fields.Boolean(string='PCL confirms no disputes')
    pcl_no_ethics_issues = fields.Boolean(string='PCL raises no ethical issues')

    # Section 7: Final Authorization
    precondition_line_ids = fields.One2many('qaco.onboarding.precondition.line', 'onboarding_id', string='ISA 210 Preconditions')
    engagement_summary = fields.Text(string='Engagement Summary', compute='_compute_engagement_summary', store=True)
    engagement_decision = fields.Selection(ENGAGEMENT_DECISION_SELECTION, string='Engagement Decision')
    engagement_justification = fields.Text(string='Decision Justification')
    engagement_partner_id = fields.Many2one('res.users', string='Engagement Partner')
    engagement_partner_signature = fields.Binary(string='Engagement Partner Digital Signature')
    eqcr_partner_id = fields.Many2one('res.users', string='EQCR Partner')
    eqcr_partner_signature = fields.Binary(string='EQCR Partner Signature')
    managing_partner_id = fields.Many2one('res.users', string='Managing Partner')
    managing_partner_signature = fields.Binary(string='Managing Partner Signature')

    document_ids = fields.One2many('qaco.onboarding.document', 'onboarding_id', string='Document Vault')
    checklist_line_ids = fields.One2many('qaco.onboarding.checklist.line', 'onboarding_id', string='Engagement Partner Decision')
    audit_trail_ids = fields.One2many('qaco.onboarding.audit.trail', 'onboarding_id', string='Audit Trail', readonly=True)

    @api.depends('client_id')
    def _compute_name(self):
        for record in self:
            record.name = f"Onboarding - {record.client_id.name or 'New Client'}"

    @api.constrains('ntn')
    def _check_ntn_format(self):
        pattern = r'^\d{7}-\d$'
        for record in self.filtered('ntn'):
            if not re.match(pattern, record.ntn):
                raise ValidationError(_('NTN must follow the format NNNNNNN-N.'))

    @api.constrains('strn')
    def _check_strn(self):
        for record in self.filtered('strn'):
            if not re.match(r'^[0-9A-Za-z-]+$', record.strn):
                raise ValidationError(_('STRN must only contain alphanumeric characters and hyphens.'))

    @api.constrains('entity_type', 'other_entity_description')
    def _check_entity_type_other(self):
        for record in self:
            if record.entity_type == 'other' and not record.other_entity_description:
                raise ValidationError(_('When selecting Other entity type, specify the classification.'))

    @api.constrains('financial_framework', 'financial_framework_other')
    def _check_financial_framework_other(self):
        for record in self:
            if record.financial_framework == 'other_framework' and not record.financial_framework_other:
                raise ValidationError(_('Provide details for the other financial reporting framework.'))

    @api.constrains('fraud_history', 'fraud_explanation')
    def _require_fraud_explanation(self):
        for record in self:
            if record.fraud_history == 'yes' and not record.fraud_explanation:
                raise ValidationError(_('Provide a detailed explanation when fraud or penalties exist.'))

    @api.constrains('eqcr_required', 'risk_mitigation_plan')
    def _require_risk_mitigation(self):
        for record in self:
            if record.eqcr_required and not record.risk_mitigation_plan:
                raise ValidationError(_('EQCR triggers require a risk mitigation plan to be documented.'))

    @api.depends('section1_status', 'section2_status', 'section3_status', 'section4_status', 'section5_status', 'section6_status', 'section7_status')
    def _compute_overall_status(self):
        for record in self:
            statuses = [getattr(record, f'section{i}_status') or 'red' for i in range(1, 8)]
            if all(status == 'green' for status in statuses):
                record.overall_status = 'green'
            elif any(status == 'amber' for status in statuses):
                record.overall_status = 'amber'
            else:
                record.overall_status = 'red'

    @api.depends('section1_status', 'section2_status', 'section3_status', 'section4_status', 'section5_status', 'section6_status', 'section7_status')
    def _compute_progress(self):
        for record in self:
            statuses = [getattr(record, f'section{i}_status') or 'red' for i in range(1, 8)]
            weights = {'red': 0, 'amber': 0.5, 'green': 1}
            if any(status not in weights for status in statuses):
                record.progress_percentage = 0.0
            else:
                record.progress_percentage = sum(weights[status] for status in statuses) / 7.0 * 100

    @api.depends('entity_type', 'primary_regulator', 'financial_framework', 'management_integrity_rating', 'aml_risk_rating', 'overall_status', 'engagement_decision')
    def _compute_selection_labels(self):
        for record in self:
            record.entity_type_label = ENTITY_LABELS.get(record.entity_type, '')
            record.primary_regulator_label = PRIMARY_REGULATOR_LABELS.get(record.primary_regulator, '')
            record.financial_framework_label = FINANCIAL_FRAMEWORK_LABELS.get(record.financial_framework, '')
            record.management_integrity_label = MANAGEMENT_INTEGRITY_LABELS.get(record.management_integrity_rating, '')
            record.aml_risk_label = AML_RATING_LABELS.get(record.aml_risk_rating, '')
            record.overall_status_label = SECTION_STATUS_LABELS.get(record.overall_status, '')
            record.engagement_decision_label = ENGAGEMENT_DECISION_LABELS.get(record.engagement_decision, '')

    @api.depends('audit_standard_ids')
    def _compute_audit_standard_overview(self):
        for record in self:
            if not record.audit_standard_ids:
                record.audit_standard_overview = _('<p>No standards selected.</p>')
                continue
            lines = []
            for standard in record.audit_standard_ids:
                regulator_label = dict(standard._fields['regulator_reference'].selection).get(standard.regulator_reference, '')
                parts = [f"<strong>{standard.code}</strong> – {standard.title}"]
                if regulator_label:
                    parts.append(f"({regulator_label})")
                applicability = standard.applicability or ''
                lines.append(f"<p>{' '.join(parts)}<br/>{applicability}</p>")
            record.audit_standard_overview = ''.join(lines)

    @api.depends('aml_risk_rating', 'eqcr_required', 'management_integrity_rating', 'fee_dependency_flag')
    def _compute_high_risk(self):
        for record in self:
            record.high_risk_onboarding = bool(
                record.aml_risk_rating == 'high'
                or record.eqcr_required
                or record.management_integrity_rating == 'low'
                or record.fee_dependency_flag
            )

    @api.depends('regulator_checklist_line_ids.completed', 'regulator_checklist_line_ids.mandatory')
    def _compute_regulator_checklist_completion(self):
        for record in self:
            mandatory = [line for line in record.regulator_checklist_line_ids if line.mandatory]
            total_mandatory = len(mandatory)
            if not total_mandatory:
                record.regulator_checklist_completion = 0.0
                continue
            completed_mandatory = sum(1 for line in mandatory if line.completed)
            record.regulator_checklist_completion = round(completed_mandatory / total_mandatory * 100.0, 2)

    @api.depends('regulator_checklist_line_ids.completed', 'regulator_checklist_line_ids.mandatory', 'regulator_checklist_line_ids.standard_ids')
    def _compute_regulator_checklist_overview(self):
        for record in self:
            mandatory_lines = [line for line in record.regulator_checklist_line_ids if line.mandatory]
            if not mandatory_lines:
                record.regulator_checklist_overview = _('<p>No checklist summary available.</p>')
                continue

            lines_by_area = {}
            for line in mandatory_lines:
                lines_by_area.setdefault(line.onboarding_area, []).append(line)

            summary_html = []
            for area_key, area_label in ONBOARDING_AREAS:
                area_lines = lines_by_area.get(area_key)
                if not area_lines:
                    continue
                completed_count = sum(1 for line in area_lines if line.completed)
                standards = set()
                for line in area_lines:
                    for standard in line.standard_ids:
                        if standard.code:
                            standards.add(standard.code)
                codes_text = ', '.join(sorted(standards)) if standards else _('No standards linked')
                summary_html.append(
                    _('<p><strong>%s</strong>: %s/%s mandatory completed | Standards: %s</p>') % (
                        area_label,
                        completed_count,
                        len(area_lines),
                        codes_text,
                    )
                )

            record.regulator_checklist_overview = ''.join(summary_html) if summary_html else _('<p>No checklist summary available.</p>')

    @api.depends(
        'entity_type',
        'legal_name', 'principal_business_address', 'business_registration_number', 'industry_id', 'primary_regulator',
        'financial_framework',
        'shareholder_ids', 'board_member_ids', 'has_pep',
        'management_integrity_rating', 'management_integrity_comment', 'aml_risk_rating', 'eqcr_required',
        'independence_threat_ids', 'independence_declaration_ids', 'fee_dependency_flag',
        'pcl_document', 'pcl_no_outstanding_fees', 'pcl_no_disputes', 'pcl_no_ethics_issues',
        'engagement_decision', 'engagement_partner_signature',
        'document_ids',
        'checklist_line_ids.answer', 'checklist_line_ids.critical',
    )
    def _compute_section_status(self):
        for record in self:
            record.section1_status = 'green' if all([
                record.entity_type,
                record.legal_name,
                record.principal_business_address,
                record.business_registration_number,
                record.industry_id,
                record.primary_regulator,
            ]) else 'red'
            record.section2_status = 'green' if record.financial_framework else 'red'
            if not (record.shareholder_ids and record.board_member_ids):
                record.section3_status = 'red'
            else:
                record.section3_status = 'amber' if record.has_pep else 'green'

            base_section4_green = bool(
                record.management_integrity_rating
                and record.management_integrity_comment
                and record.aml_risk_rating in ['low', 'medium']
            )
            if not record.management_integrity_rating:
                record.section4_status = 'red'
            elif base_section4_green and record.eqcr_required:
                record.section4_status = 'amber'
            elif base_section4_green:
                record.section4_status = 'green'
            else:
                record.section4_status = 'amber'

            if not (record.independence_threat_ids and record.independence_declaration_ids):
                record.section5_status = 'red'
            else:
                record.section5_status = 'amber' if record.fee_dependency_flag else 'green'
            record.section6_status = 'green' if record.pcl_document and record.pcl_no_outstanding_fees and record.pcl_no_disputes and record.pcl_no_ethics_issues else 'red'
            record.section7_status = 'green' if record.engagement_decision == 'accept' and record.engagement_partner_signature else 'red'

            # Sections 8-10: no mandatory fields enforced for navigation; mark as complete by default.
            record.section8_status = 'green'
            record.section9_status = 'green'
            record.section10_status = 'green'

    def _get_onboarding_section_status(self, section_number: int) -> str:
        field_name = f'section{section_number}_status'
        if field_name not in self._fields:
            return 'red'
        return getattr(self, field_name) or 'red'

    def _validate_onboarding_section(self, section_number: int):
        self.ensure_one()
        if section_number in (8, 9, 10):
            return
        status = self._get_onboarding_section_status(section_number)
        if status != 'green':
            raise UserError(
                _('Please complete all required fields in section %s before continuing.')
                % f'1.{section_number}'
            )

    def _action_reopen_onboarding(self, target_section: int):
        self.ensure_one()
        ctx = dict(self.env.context)
        ctx['onboarding_active_section'] = target_section
        return {
            'type': 'ir.actions.act_window',
            'name': _('Client Onboarding'),
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
            'context': ctx,
        }

    def action_onboarding_back(self):
        self.ensure_one()
        current = int(self.env.context.get('onboarding_current_section') or 1)
        target = max(1, current - 1)
        return self._action_reopen_onboarding(target)

    def action_onboarding_save_next(self):
        self.ensure_one()
        current = int(self.env.context.get('onboarding_current_section') or 1)
        self._validate_onboarding_section(current)
        target = min(10, current + 1)
        return self._action_reopen_onboarding(target)

    @api.depends('board_member_ids.is_pep')
    def _compute_pep_flag(self):
        for record in self:
            has_pep = any(member.is_pep for member in record.board_member_ids)
            record.has_pep = has_pep
            record.enhanced_due_diligence_required = has_pep

    @api.depends('management_integrity_rating', 'aml_risk_rating')
    def _compute_eqcr_required(self):
        for record in self:
            low_integrity = record.management_integrity_rating == 'low'
            high_aml = record.aml_risk_rating == 'high'
            record.eqcr_required = low_integrity or high_aml
            record.managing_partner_escalation = record.eqcr_required

    @api.depends('industry_id.risk_category', 'primary_regulator', 'has_pep')
    def _compute_aml_risk_rating(self):
        for record in self:
            risk_score = 0
            if record.industry_id and record.industry_id.risk_category == 'high':
                risk_score += 2
            if record.primary_regulator in ['fbr', 'secp']:
                risk_score += 1
            if record.has_pep:
                risk_score += 2
            rating = 'low'
            if risk_score >= 3:
                rating = 'high'
            elif risk_score == 2:
                rating = 'medium'
            record.aml_risk_rating = rating

    @api.depends('proposed_audit_fee', 'total_fee_income', 'entity_type')
    def _compute_fee_dependency(self):
        for record in self:
            threshold = 15 if record.entity_type in ['pic', 'lsc'] else 20
            if record.proposed_audit_fee and record.total_fee_income:
                record.fee_dependency_percent = round((record.proposed_audit_fee / record.total_fee_income) * 100.0, 2)
            else:
                record.fee_dependency_percent = 0.0
            record.fee_dependency_flag = record.fee_dependency_percent > threshold

    @api.depends('independence_declaration_ids.state')
    def _compute_independence_status(self):
        for record in self:
            if not record.independence_declaration_ids:
                record.independence_status_feedback = _('Awaiting declarations from the engagement team.')
                continue
            total = len(record.independence_declaration_ids)
            confirmed = sum(1 for line in record.independence_declaration_ids if line.state == 'confirmed')
            percent = (confirmed / total) * 100 if total else 0
            record.independence_status_feedback = _('%d%% of team members completed declarations.') % percent

    @api.depends('client_id', 'aml_risk_rating', 'eqcr_required', 'engagement_decision')
    def _compute_engagement_summary(self):
        for record in self:
            summary = [
                _('Client: %s') % (record.client_id.name or '—'),
                _('Risk: %s') % (record.aml_risk_label or '—'),
                _('EQCR Required: %s') % ('Yes' if record.eqcr_required else 'No'),
            ]
            if record.engagement_decision:
                summary.append(_('Decision: %s') % (record.engagement_decision_label or '—'))
            record.engagement_summary = '\n'.join(summary)

    @api.model
    def create(self, vals):
        vals = self._with_minimum_defaults(vals)
        onboarding = super().create(vals)
        onboarding._populate_checklist_from_templates()
        onboarding._populate_preconditions()
        onboarding._populate_regulator_checklist()
        onboarding._log_action('Created onboarding record')
        return onboarding

    def _with_minimum_defaults(self, vals):
        """Ensure required gateway fields are populated when launched from audit smart button."""
        # Only apply when creating a single record via dict input.
        if isinstance(vals, dict):
            audit = None
            if vals.get('audit_id'):
                audit = self.env['qaco.audit'].browse(vals['audit_id'])
            partner = audit.client_id if audit else None

            vals.setdefault('entity_type', 'pic')
            if vals.get('entity_type') == 'other':
                vals.setdefault('other_entity_description', _('Pending classification'))
            vals.setdefault('legal_name', partner.name if partner else _('Pending Legal Name'))
            vals.setdefault('principal_business_address', (partner.contact_address if partner else None) or _('Pending Address'))
            vals.setdefault('business_registration_number', vals.get('business_registration_number') or _('TBD'))
            vals.setdefault('primary_regulator', 'secp')
            vals.setdefault('financial_framework', 'ifrs')
            vals.setdefault('management_integrity_rating', 'medium')
            vals.setdefault('management_integrity_comment', vals.get('management_integrity_comment') or _('Pending assessment'))
        return vals

    def write(self, vals):
        res = super().write(vals)
        changed_fields = ', '.join(map(str, vals.keys())) if vals else ''
        self._log_action('Updated onboarding', notes=changed_fields)
        return res

    def _populate_checklist_from_templates(self):
        template_obj = self.env['qaco.onboarding.checklist.template']
        templates = template_obj.search([])
        if not templates:
            return
        for record in self:
            self.env['qaco.onboarding.checklist.line'].create([
                {
                    'onboarding_id': record.id,
                    'template_id': template.id,
                    'question': template.question,
                    'category': template.category,
                    'critical': template.critical,
                }
                for template in templates
            ])

    def _populate_preconditions(self):
        template_obj = self.env['qaco.onboarding.precondition.template']
        templates = template_obj.search([])
        if not templates:
            return
        for record in self:
            self.env['qaco.onboarding.precondition.line'].create([
                {
                    'onboarding_id': record.id,
                    'template_id': template.id,
                    'description': template.description,
                }
                for template in templates
            ])

    def _populate_regulator_checklist(self):
        template_obj = self.env['audit.onboarding.checklist.template']
        templates = template_obj.search([])
        if not templates:
            return
        for record in self:
            if record.regulator_checklist_line_ids:
                continue
            self.env['audit.onboarding.checklist'].create([
                {
                    'onboarding_id': record.id,
                    'template_id': template.id,
                    'code': template.code,
                    'name': template.name,
                    'onboarding_area': template.onboarding_area,
                    'standard_ids': [(6, 0, template.standard_ids.ids)],
                    'mandatory': template.mandatory,
                    'sequence': template.sequence,
                    'notes': template.guidance,
                }
                for template in templates
            ])

    def _log_action(self, action, notes=None):
        trail = self.env['qaco.onboarding.audit.trail']
        for record in self:
            trail.create({
                'onboarding_id': record.id,
                'action': action,
                'notes': notes or '',
            })

    def _validate_mandatory_checklist_completion(self):
        for record in self:
            if not record.regulator_checklist_line_ids:
                record._populate_regulator_checklist()
            if not record.regulator_checklist_line_ids:
                raise ValidationError(_('Mandatory onboarding checklist items are missing for this record. Please reload or contact an administrator.'))
            pending = record.regulator_checklist_line_ids.filtered(lambda line: line.mandatory and not line.completed)
            if pending:
                pending_names = ', '.join(pending.mapped('name'))
                raise ValidationError(_(
                    'All mandatory onboarding checklist items must be completed before final authorization. Pending: %s'
                ) % pending_names)

    def action_submit_review(self):
        for record in self:
            if record.state != 'draft':
                continue
            record.write({'state': 'under_review'})
            record._log_action('Submitted for review')

    def action_partner_approve(self):
        for record in self:
            if record.state != 'under_review':
                raise ValidationError(_('Submit the onboarding for review before partner approval.'))
            record._validate_mandatory_checklist_completion()
            if record.high_risk_onboarding and not record.engagement_partner_id:
                raise ValidationError(_('High-risk onboardings require an Engagement Partner before approval.'))
            record.write({'state': 'partner_approved'})
            record._log_action('Partner approved onboarding', notes=_('High risk: %s') % ('Yes' if record.high_risk_onboarding else 'No'))

    def action_generate_acceptance_report(self):
        report = self.env.ref('qaco_client_onboarding.report_client_onboarding_pdf', raise_if_not_found=False)
        if report:
            return report.report_action(self)
        return {'type': 'ir.actions.act_window_close'}

    def action_lock_onboarding(self):
        for record in self:
            record._validate_mandatory_checklist_completion()
            if record.overall_status != 'green':
                raise ValidationError(_('Finalize all sections before locking the onboarding.'))
            if record.state != 'partner_approved':
                raise ValidationError(_('Partner approval is required before locking the onboarding.'))
            if record.high_risk_onboarding and record.state != 'partner_approved':
                raise ValidationError(_('High-risk onboarding must be partner approved before locking.'))
            record.write({'state': 'locked'})
            record._log_action('Locked onboarding for final authorization')


class OnboardingBranchLocation(models.Model):
    _name = 'qaco.onboarding.branch.location'
    _description = 'Onboarding Branch / Office Location'

    onboarding_id = fields.Many2one('qaco.client.onboarding', required=True, ondelete='cascade')
    name = fields.Char(string='Location', required=True)
    address = fields.Char(string='Address', required=True)
    country_id = fields.Many2one('res.country', string='Country')


class OnboardingUBO(models.Model):
    _name = 'qaco.onboarding.ubo'
    _description = 'Ultimate Beneficial Owner'

    onboarding_id = fields.Many2one('qaco.client.onboarding', required=True, ondelete='cascade')
    name = fields.Char(string='UBO Name', required=True)
    cnic_passport = fields.Char(string='CNIC / Passport Number', required=True)
    nationality = fields.Char(string='Nationality')
    ownership_percent = fields.Float(string='Ownership %', digits=(5, 2))


class OnboardingShareholder(models.Model):
    _name = 'qaco.onboarding.shareholder'
    _description = 'Shareholder Pattern'

    onboarding_id = fields.Many2one('qaco.client.onboarding', required=True, ondelete='cascade')
    name = fields.Char(string='Shareholder Name', required=True)
    share_class = fields.Char(string='Class of Shares')
    percentage = fields.Float(string='Percentage', digits=(5, 2))
    voting_rights = fields.Char(string='Voting Rights Structure')


class OnboardingBoardMember(models.Model):
    _name = 'qaco.onboarding.board.member'
    _description = 'Board Member or Key Personnel'

    onboarding_id = fields.Many2one('qaco.client.onboarding', required=True, ondelete='cascade')
    name = fields.Char(string='Name', required=True)
    cnic = fields.Char(string='CNIC')
    din = fields.Char(string='DIN')
    role = fields.Selection([('ceo', 'CEO'), ('cfo', 'CFO'), ('company_secretary', 'Company Secretary'), ('independent_director', 'Independent Director'), ('other', 'Other')], string='Role')
    is_pep = fields.Boolean(string='Politically Exposed Person')


class OnboardingIndustry(models.Model):
    _name = 'qaco.onboarding.industry'
    _description = 'Industry / Sector Reference'

    name = fields.Char(string='Industry / Sector', required=True)
    risk_category = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], string='Risk Category', default='medium', required=True)


class OnboardingIndependenceThreat(models.Model):
    _name = 'qaco.onboarding.independence.threat'
    _description = 'Independence Threat Checklist'

    onboarding_id = fields.Many2one('qaco.client.onboarding', required=True, ondelete='cascade')
    threat_type = fields.Selection(THREAT_TYPES, string='Threat Type', required=True)
    answer = fields.Selection([('no', 'No'), ('yes', 'Yes')], string='Threat Identified', required=True)
    details = fields.Text(string='Details / Safeguards')
    safeguards = fields.Text(string='Safeguards Applied')


class OnboardingDocument(models.Model):
    _name = 'qaco.onboarding.document'
    _description = 'Document Vault Entry'

    onboarding_id = fields.Many2one('qaco.client.onboarding', required=True, ondelete='cascade')
    name = fields.Char(string='Document Name', required=True)
    doc_type = fields.Selection(DOCUMENT_TYPE_SELECTION, string='Document Type', default='other')
    file = fields.Binary(string='File', attachment=True)
    file_name = fields.Char(string='File Name')
    state = fields.Selection(DOCUMENT_STATES, string='Status', default='pending')
    doc_type_label = fields.Char(string='Document Type (Label)', compute='_compute_doc_type_label')

    @api.depends('doc_type')
    def _compute_doc_type_label(self):
        for record in self:
            record.doc_type_label = dict(DOCUMENT_TYPE_SELECTION).get(record.doc_type, record.doc_type or '')


class OnboardingChecklistTemplate(models.Model):
    _name = 'qaco.onboarding.checklist.template'
    _description = 'Engagement Partner Decision Template'

    question = fields.Char(string='Checklist Question', required=True)
    category = fields.Char(string='Checklist Category')
    critical = fields.Boolean(string='Critical')


class OnboardingChecklistLine(models.Model):
    _name = 'qaco.onboarding.checklist.line'
    _description = 'Checklist Answer'

    onboarding_id = fields.Many2one('qaco.client.onboarding', required=True, ondelete='cascade')
    template_id = fields.Many2one('qaco.onboarding.checklist.template', string='Template Reference')
    question = fields.Char(string='Question', required=True)
    category = fields.Char(string='Category')
    answer = fields.Selection(CHECKLIST_ANSWER_SELECTION, string='Answer')
    remarks = fields.Text(string='Remarks')
    critical = fields.Boolean(string='Critical')
    answer_label = fields.Char(string='Answer Label', compute='_compute_answer_label')

    @api.depends('answer')
    def _compute_answer_label(self):
        for record in self:
            record.answer_label = dict(CHECKLIST_ANSWER_SELECTION).get(record.answer, record.answer or '')


class OnboardingIndependenceDeclaration(models.Model):
    _name = 'qaco.onboarding.independence.declaration'
    _description = 'Individual Independence Declaration'

    onboarding_id = fields.Many2one('qaco.client.onboarding', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', string='Team Member', required=True)
    state = fields.Selection([('pending', 'Pending'), ('confirmed', 'Confirmed')], string='Declaration Status', default='pending')
    confirmation_date = fields.Datetime(string='Confirmed On')
    reminder_sent = fields.Boolean(string='Reminder Sent')


class OnboardingPreconditionTemplate(models.Model):
    _name = 'qaco.onboarding.precondition.template'
    _description = 'ISA 210 Precondition Template'

    description = fields.Char(string='Precondition', required=True)


class OnboardingPreconditionLine(models.Model):
    _name = 'qaco.onboarding.precondition.line'
    _description = 'ISA 210 Precondition Confirmation'

    onboarding_id = fields.Many2one('qaco.client.onboarding', required=True, ondelete='cascade')
    template_id = fields.Many2one('qaco.onboarding.precondition.template', string='Template Reference')
    description = fields.Char(string='Precondition', required=True)
    confirmed = fields.Boolean(string='Confirmed', default=False)


class OnboardingAuditTrail(models.Model):
    _name = 'qaco.onboarding.audit.trail'
    _description = 'Client Onboarding Audit Trail'

    onboarding_id = fields.Many2one('qaco.client.onboarding', required=True, ondelete='cascade')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id)
    action = fields.Char(string='Action', required=True)
    notes = fields.Text(string='Notes')
    create_date = fields.Datetime(string='Timestamp', default=fields.Datetime.now)
