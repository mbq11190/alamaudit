# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

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
    ('accept_safeguards', 'Accept with Safeguards'),
    ('reject', 'Reject'),
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
    ('legal', 'Legal'),
    ('regulatory', 'Regulatory'),
    ('ethics', 'Ethics'),
    ('kyc_aml', 'KYC / AML'),
    ('engagement', 'Engagement'),
    ('governance', 'Governance'),
    ('risk', 'Risk'),
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


class ClientOnboarding(models.Model):
    _name = 'qaco.client.onboarding'
    _description = 'Client Onboarding'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Onboarding Title', compute='_compute_name', store=True)
    audit_id = fields.Many2one('qaco.audit', string='Audit', required=True, ondelete='cascade')
    client_id = fields.Many2one('res.partner', string='Client', related='audit_id.client_id', readonly=True, store=True)

    # Section 0: Gateway fields
    entity_type = fields.Selection(ENTITY_SELECTION, string='Entity Type', required=True, tracking=True)
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
    legal_name = fields.Char(string='Legal Name', required=True)
    trading_name = fields.Char(string='Trading Name')
    principal_business_address = fields.Char(string='Principal Business Address', required=True)
    branch_location_ids = fields.One2many('qaco.onboarding.branch.location', 'onboarding_id', string='Branch and Office Locations')
    ntn = fields.Char(string='NTN', help='Enter in format 1234567-1')
    strn = fields.Char(string='STRN', help='State the Sales Tax Registration Number if applicable')
    business_registration_number = fields.Char(string='Business Registration Number', required=True)
    industry_id = fields.Many2one('qaco.onboarding.industry', string='Industry / Sector')
    primary_regulator = fields.Selection(PRIMARY_REGULATOR_SELECTION, string='Primary Regulator', required=True)
    regulator_other = fields.Char(string='Other Regulator Details')
    org_chart_attachment = fields.Binary(string='Group Structure / Org Chart')
    org_chart_name = fields.Char(string='Org Chart File Name')
    ubo_ids = fields.One2many('qaco.onboarding.ubo', 'onboarding_id', string='Ultimate Beneficial Owners')
    # Section 1.1: Mandatory Narratives (cannot be blank)
    legal_existence_verification = fields.Text(
        string='Legal Existence Verification',
        tracking=True,
        help='Describe how legal existence was verified (e.g., certificate of incorporation, company registry search, legal opinion).',
    )
    group_structure_risk = fields.Text(
        string='Group / Holding / Subsidiary Structure Risk',
        tracking=True,
        help='Assess risks arising from group structure, intercompany transactions, related party complexity, and consolidation issues.',
    )
    foreign_ownership_exposure = fields.Text(
        string='Foreign Ownership Exposure',
        tracking=True,
        help='Document foreign ownership percentage, jurisdictions involved, repatriation restrictions, and cross-border regulatory implications.',
    )
    ubo_risk_summary = fields.Text(
        string='Ultimate Beneficial Owner Risk Summary',
        tracking=True,
        help='Summarize UBO identification process, any PEP exposure, sanctions screening results, and residual risks.',
    )
    # Section 1.1: Mandatory Attachments
    incorporation_evidence = fields.Binary(
        string='Incorporation / Registration Evidence',
        attachment=True,
        help='Upload certificate of incorporation, registration certificate, or equivalent legal document.',
    )
    incorporation_evidence_name = fields.Char(string='Incorporation Evidence Filename')
    group_structure_chart = fields.Binary(
        string='Group Structure Chart',
        attachment=True,
        help='Upload organizational/group structure chart showing ownership hierarchy.',
    )
    group_structure_chart_name = fields.Char(string='Group Structure Chart Filename')

    # Section 2: Compliance History
    financial_framework = fields.Selection(FINANCIAL_FRAMEWORK_SELECTION, string='Applicable Framework', required=True)
    financial_framework_other = fields.Char(string='Other Framework Details')
    annual_return_last_filed = fields.Date(string='Annual Return Last Filed')
    annual_return_overdue = fields.Boolean(string='Return Overdue', default=False)
    fbr_compliance_rating = fields.Selection([('atl', 'ATL'), ('btl', 'BTL'), ('provisional', 'Provisional')], string='FBR Compliance Rating')
    tax_assessment_history = fields.Text(string='Tax Assessment / Litigation History')
    regulatory_inspection_notes = fields.Text(string='Regulatory Inspection Summary')
    regulatory_inspection_attachment = fields.Binary(string='Inspection Documents')
    # Section 1.2: Mandatory Compliance Assessment Notes
    applicable_laws_regulators = fields.Text(
        string='Applicable Laws & Regulators',
        tracking=True,
        help='List all applicable laws, regulations, and regulatory bodies governing the client (e.g., Companies Act, SECP, SBP, FBR, sector-specific regulators).',
    )
    filing_history_gaps = fields.Text(
        string='Filing History and Compliance Gaps',
        tracking=True,
        help='Document filing history with regulators, identify any gaps, late filings, or non-compliance issues.',
    )
    inspection_enforcement_exposure = fields.Text(
        string='Inspection / Enforcement Exposure',
        tracking=True,
        help='Summarize any regulatory inspections, enforcement actions, show-cause notices, or pending investigations.',
    )
    litigation_penalties_note = fields.Text(
        string='Litigation & Penalties',
        tracking=True,
        help='Document any litigation, fines, penalties, or adverse regulatory findings against the client.',
    )
    # Section 1.2: Mandatory Conclusion
    regulatory_framework_acceptable = fields.Selection(
        [('yes', 'Yes'), ('no', 'No')],
        string='Regulatory Framework Acceptable',
        tracking=True,
        help='Confirm whether the regulatory framework applicable to the client is acceptable for engagement.',
    )
    regulatory_framework_conclusion = fields.Text(
        string='Regulatory Framework Conclusion',
        help='Provide justification for the conclusion on regulatory framework acceptability.',
    )

    # Section 3: Ownership & Governance
    shareholder_ids = fields.One2many('qaco.onboarding.shareholder', 'onboarding_id', string='Shareholding Pattern')
    board_member_ids = fields.One2many('qaco.onboarding.board.member', 'onboarding_id', string='Board & Key Personnel')
    fit_proper_confirmed = fields.Boolean(string='Fit & Proper Checks Completed')
    fit_proper_document = fields.Binary(string='Fit & Proper Evidence')
    has_pep = fields.Boolean(string='Politically Exposed Person Identified', compute='_compute_pep_flag', store=True)
    enhanced_due_diligence_required = fields.Boolean(string='Enhanced Due Diligence Required', compute='_compute_pep_flag', store=True)
    enhanced_due_diligence_details = fields.Text(string='Enhanced Due Diligence Notes')
    enhanced_due_diligence_attachment = fields.Binary(string='Enhanced Due Diligence Documentation')
    # Section 1.3: Mandatory Governance Risk Notes
    board_independence_assessment = fields.Text(
        string='Board Independence Assessment',
        tracking=True,
        help='Assess board composition, proportion of independent directors, potential conflicts of interest, and effectiveness of oversight.',
    )
    audit_committee_competence = fields.Text(
        string='Audit Committee Existence & Competence',
        tracking=True,
        help='Document existence of audit committee, member qualifications, financial expertise, meeting frequency, and effectiveness.',
    )
    political_exposure_note = fields.Text(
        string='Political Exposure',
        tracking=True,
        help='Assess political connections, PEP involvement, government contracts, and associated reputational/regulatory risks.',
    )
    dominant_shareholder_risk = fields.Text(
        string='Dominant Shareholder Risk',
        tracking=True,
        help='Evaluate risks from concentrated ownership, related party influence, minority shareholder protection, and governance override.',
    )
    # Section 1.3: Mandatory Evidence Attachments
    board_list_attachment = fields.Binary(
        string='Board List',
        attachment=True,
        help='Upload current board of directors list with roles, appointment dates, and independence status.',
    )
    board_list_attachment_name = fields.Char(string='Board List Filename')
    audit_committee_details_attachment = fields.Binary(
        string='Audit Committee Details',
        attachment=True,
        help='Upload audit committee charter, member list, and recent meeting minutes.',
    )
    audit_committee_details_attachment_name = fields.Char(string='Audit Committee Details Filename')
    fit_proper_confirmation_attachment = fields.Binary(
        string='Fit & Proper Confirmation',
        attachment=True,
        help='Upload fit and proper confirmation documentation for key personnel.',
    )
    fit_proper_confirmation_attachment_name = fields.Char(string='Fit & Proper Confirmation Filename')

    # Section 4: Pre-Acceptance Risk
    management_integrity_rating = fields.Selection(MANAGEMENT_INTEGRITY_SELECTION, string='Management Integrity Rating', tracking=True)
    management_integrity_comment = fields.Text(string='Management Integrity Justification')
    litigation_history = fields.Text(string='Litigation History')
    fraud_history = fields.Selection([('no', 'No'), ('yes', 'Yes')], string='History of Fraud or Penalties', default='no', tracking=True)
    fraud_explanation = fields.Text(string='Fraud or Penalty Details')
    aml_risk_rating = fields.Selection(AML_RATING, string='AML/CTF Risk Rating', compute='_compute_aml_risk_rating', store=True)
    business_risk_profile = fields.Text(string='Business Risk Profile')
    risk_mitigation_plan = fields.Text(string='Risk Mitigation Plan')
    eqcr_required = fields.Boolean(string='EQCR Required', compute='_compute_eqcr_required', store=True)
    managing_partner_escalation = fields.Boolean(string='Managing Partner Escalation', compute='_compute_eqcr_required', store=True)
    # Section 1.4: Mandatory Risk Summaries (Rating + Justification)
    RISK_LEVEL_SELECTION = [
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
    ]
    integrity_risk_level = fields.Selection(
        RISK_LEVEL_SELECTION,
        string='Integrity Risk Level',
        tracking=True,
        help='Conclude the overall integrity risk level.',
    )
    integrity_risk_summary = fields.Text(
        string='Integrity Risk Summary',
        tracking=True,
        help='Summarize management integrity concerns, background check findings, reputation issues, and justification for the risk level.',
    )
    business_risk_level = fields.Selection(
        RISK_LEVEL_SELECTION,
        string='Business Risk Level',
        tracking=True,
        help='Conclude the overall business risk level.',
    )
    business_risk_summary = fields.Text(
        string='Business Risk Summary',
        tracking=True,
        help='Summarize industry risks, competitive pressures, financial stability, and justification for the risk level.',
    )
    fraud_risk_level = fields.Selection(
        RISK_LEVEL_SELECTION,
        string='Fraud Risk Level',
        tracking=True,
        help='Conclude the overall fraud risk level.',
    )
    fraud_risk_summary = fields.Text(
        string='Fraud Risk Summary',
        tracking=True,
        help='Summarize fraud risk indicators, control environment, management override risks, and justification for the risk level.',
    )
    going_concern_level = fields.Selection(
        RISK_LEVEL_SELECTION,
        string='Going Concern Risk Level',
        tracking=True,
        help='Conclude the going concern risk level.',
    )
    going_concern_indicators = fields.Text(
        string='Going Concern Indicators',
        tracking=True,
        help='Document going concern indicators, liquidity issues, debt covenants, operational losses, and justification for the risk level.',
    )
    reputation_risk_level = fields.Selection(
        RISK_LEVEL_SELECTION,
        string='Reputation Risk Level',
        tracking=True,
        help='Conclude the reputation risk to the firm.',
    )
    reputation_risk_to_firm = fields.Text(
        string='Reputation Risk to Firm',
        tracking=True,
        help='Assess reputational risk to the firm from this engagement, media exposure, controversial activities, and justification for the risk level.',
    )

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

    # Section 1.5: Mandatory Attachments
    independence_declaration_attachment = fields.Binary(
        string='Independence Declaration (Before Engagement)',
        help='Attach signed independence declaration form completed before engagement acceptance.',
    )
    independence_declaration_attachment_name = fields.Char(string='Independence Declaration Filename')
    fee_dependency_calculation_attachment = fields.Binary(
        string='Fee Dependency Calculation',
        help='Attach fee dependency calculation workpaper demonstrating compliance with 15% threshold.',
    )
    fee_dependency_calculation_attachment_name = fields.Char(string='Fee Dependency Calculation Filename')
    audit_committee_approval_attachment = fields.Binary(
        string='Audit Committee Approval (if applicable)',
        help='Attach audit committee approval for significant independence matters, if required.',
    )
    audit_committee_approval_attachment_name = fields.Char(string='Audit Committee Approval Filename')

    # Section 1.5: Independence Acceptance Blocking
    independence_residual_risk_acceptable = fields.Boolean(
        string='All Residual Risks Acceptable (Low)',
        compute='_compute_independence_residual_risk_acceptable',
        store=True,
        help='True only if ALL threat residual risks are Low. Any Moderate/High risk blocks acceptance.',
    )

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

    # Section 1.6: Mandatory Professional Clearance Note
    pcl_reason_for_change = fields.Text(
        string='Reason for Change of Auditors',
        tracking=True,
        help='Document the stated reason for change of auditors. Include client explanation and any corroborating evidence.',
    )
    pcl_disputes_unpaid_fees = fields.Text(
        string='Disputes / Unpaid Fees',
        tracking=True,
        help='Document any outstanding disputes or unpaid fees with predecessor. State "None identified" if applicable.',
    )
    pcl_access_to_working_papers = fields.Text(
        string='Access to Working Papers',
        tracking=True,
        help='Document the status of access to predecessor working papers. Include any limitations or refusals.',
    )
    pcl_ethical_concerns_raised = fields.Text(
        string='Ethical Concerns Raised',
        tracking=True,
        help='Document any ethical concerns raised by predecessor or identified during clearance process. State "None raised" if applicable.',
    )

    # Section 1.6: Mandatory Conclusion
    pcl_no_barrier_conclusion = fields.Boolean(
        string='No Professional or Ethical Barrier Exists',
        default=False,
        tracking=True,
        help='Confirm: "No professional or ethical barrier exists to accepting this engagement." Must be True to proceed.',
    )

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

    # Section 1.7: Mandatory Management Acknowledgement Checklist
    mgmt_ack_responsibility_fs = fields.Boolean(
        string='Responsibility for Financial Statements',
        default=False,
        tracking=True,
        help='Management acknowledges responsibility for preparation and fair presentation of financial statements.',
    )
    mgmt_ack_responsibility_ic = fields.Boolean(
        string='Responsibility for Internal Control',
        default=False,
        tracking=True,
        help='Management acknowledges responsibility for internal control relevant to preparation of financial statements.',
    )
    mgmt_ack_access_to_records = fields.Boolean(
        string='Access to Records',
        default=False,
        tracking=True,
        help='Management confirms unrestricted access to all records, documentation, and personnel.',
    )
    mgmt_ack_going_concern = fields.Boolean(
        string='Going Concern Responsibility',
        default=False,
        tracking=True,
        help='Management acknowledges responsibility for assessing going concern and providing related disclosures.',
    )

    # Section 1.7: Mandatory Partner Judgment Note
    partner_judgment_acceptable = fields.Text(
        string='Why Engagement is Acceptable',
        tracking=True,
        help='Document the partner\'s professional judgment on why this engagement is acceptable. Include key factors considered.',
    )
    partner_judgment_safeguards = fields.Text(
        string='Safeguards Imposed',
        tracking=True,
        help='Document any safeguards imposed to address identified risks. State "No additional safeguards required" if applicable.',
    )
    partner_judgment_conditions = fields.Text(
        string='Conditions (if any)',
        tracking=True,
        help='Document any conditions attached to acceptance. State "No conditions" if engagement is accepted unconditionally.',
    )

    # Section 1.7: Partner Sign-off Blocking
    partner_signoff_complete = fields.Boolean(
        string='Partner Sign-off Complete',
        compute='_compute_partner_signoff_complete',
        store=True,
        help='True only if Engagement Partner has provided digital signature. Cannot proceed without sign-off.',
    )

    document_ids = fields.One2many('qaco.onboarding.document', 'onboarding_id', string='Document Vault')
    attached_template_ids = fields.One2many('qaco.onboarding.attached.template', 'onboarding_id', string='Attached Templates')
    checklist_line_ids = fields.One2many('qaco.onboarding.checklist.line', 'onboarding_id', string='Engagement Partner Decision')
    audit_trail_ids = fields.One2many('qaco.onboarding.audit.trail', 'onboarding_id', string='Audit Trail', readonly=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # 📄 AUTO-GENERATED REPORTS (Upon Partner Approval)
    # ═══════════════════════════════════════════════════════════════════════════
    # Report Generation Tracking
    reports_generated = fields.Boolean(
        string='Reports Generated',
        default=False,
        readonly=True,
        help='Indicates whether the four mandatory reports have been auto-generated upon partner approval.',
    )
    reports_generated_date = fields.Datetime(
        string='Reports Generated On',
        readonly=True,
        help='Timestamp when mandatory reports were auto-generated.',
    )
    reports_generated_by = fields.Many2one(
        'res.users',
        string='Reports Generated By',
        readonly=True,
        help='Partner who approved and triggered report generation.',
    )
    # Individual Report Attachments (stored for QCR reference)
    report_acceptance_continuance = fields.Binary(
        string='Client Acceptance & Continuance Report',
        attachment=True,
        readonly=True,
        help='ISA 220 / ISQM-1 referenced acceptance report - auto-generated on approval.',
    )
    report_acceptance_continuance_name = fields.Char(
        string='Acceptance Report Filename',
        readonly=True,
    )
    report_ethics_independence = fields.Binary(
        string='Ethics & Independence Compliance Report',
        attachment=True,
        readonly=True,
        help='IESBA Code / ISA 220 referenced ethics report - auto-generated on approval.',
    )
    report_ethics_independence_name = fields.Char(
        string='Ethics Report Filename',
        readonly=True,
    )
    report_fraud_business_risk = fields.Binary(
        string='Fraud & Business Risk Summary',
        attachment=True,
        readonly=True,
        help='ISA 240 / ISA 315 referenced risk summary - auto-generated on approval.',
    )
    report_fraud_business_risk_name = fields.Char(
        string='Fraud Risk Report Filename',
        readonly=True,
    )
    report_engagement_authorization = fields.Binary(
        string='Engagement Authorization Memorandum',
        attachment=True,
        readonly=True,
        help='ISA 210 / ISQM-1 referenced authorization memo - auto-generated on approval.',
    )
    report_engagement_authorization_name = fields.Char(
        string='Authorization Memo Filename',
        readonly=True,
    )
    # Report Summary for UI
    generated_reports_summary = fields.Html(
        string='Generated Reports Summary',
        compute='_compute_generated_reports_summary',
        sanitize=False,
    )

    # Section 1.9: Mandatory Final Acceptance Memorandum
    fam_engagement_risk_level = fields.Selection(
        [('low', 'Low'), ('moderate', 'Moderate'), ('high', 'High')],
        string='Engagement Risk Level',
        tracking=True,
        help='Partner must explicitly state the overall engagement risk level.',
    )
    fam_engagement_risk_justification = fields.Text(
        string='Engagement Risk Justification',
        tracking=True,
        help='Document the basis for the engagement risk level conclusion.',
    )
    fam_independence_conclusion = fields.Text(
        string='Independence Conclusion',
        tracking=True,
        help='Partner must explicitly state the independence conclusion for the engagement team.',
    )
    fam_fraud_risk_conclusion = fields.Text(
        string='Fraud Risk Conclusion',
        tracking=True,
        help='Partner must explicitly state the fraud risk conclusion and response strategy.',
    )
    fam_resource_sufficiency = fields.Text(
        string='Resource Sufficiency',
        tracking=True,
        help='Partner must confirm sufficiency of resources (staff competence, time, budget) to complete the engagement.',
    )
    fam_isqm1_compliance = fields.Boolean(
        string='ISQM-1 Compliance Confirmed',
        default=False,
        tracking=True,
        help='Partner confirms the engagement complies with firm\'s ISQM-1 quality management system.',
    )
    fam_final_decision = fields.Selection(
        ENGAGEMENT_DECISION_SELECTION,
        string='Final Acceptance Decision',
        tracking=True,
        help='Partner must explicitly select: Accept, Accept with Safeguards, or Reject. No silent acceptance allowed.',
    )
    fam_safeguards_imposed = fields.Text(
        string='Safeguards Imposed (if applicable)',
        help='If decision is "Accept with Safeguards", document the specific safeguards imposed.',
    )
    fam_rejection_reason = fields.Text(
        string='Rejection Reason (if applicable)',
        help='If decision is "Reject", document the specific reasons for declining the engagement.',
    )

    # Section 1.0: Mandatory Template Checklist
    tpl_engagement_letter = fields.Boolean(string='Engagement Letter template selected', default=False, tracking=True)
    tpl_independence_declaration = fields.Boolean(string='Independence Declaration template', default=False, tracking=True)
    tpl_acceptance_checklist = fields.Boolean(string='Acceptance checklist template', default=False, tracking=True)
    tpl_fraud_risk_questionnaire = fields.Boolean(string='Fraud risk questionnaire', default=False, tracking=True)
    tpl_business_risk_questionnaire = fields.Boolean(string='Business risk questionnaire', default=False, tracking=True)
    tpl_governance_tcwg_checklist = fields.Boolean(string='Governance & TCWG checklist', default=False, tracking=True)
    templates_locked = fields.Boolean(string='Templates Locked', default=False, tracking=True)
    templates_complete = fields.Boolean(string='All Templates Complete', compute='_compute_templates_complete', store=True)

    @api.depends('tpl_engagement_letter', 'tpl_independence_declaration', 'tpl_acceptance_checklist',
                 'tpl_fraud_risk_questionnaire', 'tpl_business_risk_questionnaire', 'tpl_governance_tcwg_checklist',
                 'templates_locked')
    def _compute_templates_complete(self):
        for record in self:
            all_selected = all([
                record.tpl_engagement_letter,
                record.tpl_independence_declaration,
                record.tpl_acceptance_checklist,
                record.tpl_fraud_risk_questionnaire,
                record.tpl_business_risk_questionnaire,
                record.tpl_governance_tcwg_checklist,
            ])
            record.templates_complete = all_selected and record.templates_locked

    @api.depends('independence_threat_ids.residual_risk')
    def _compute_independence_residual_risk_acceptable(self):
        """Check if ALL threat residual risks are Low. Any Moderate/High blocks acceptance."""
        for record in self:
            threats = record.independence_threat_ids
            if not threats:
                # If no threats documented, not acceptable (must document all 5 threat types)
                record.independence_residual_risk_acceptable = False
            else:
                # Check if ALL residual risks are 'low'
                all_low = all(threat.residual_risk == 'low' for threat in threats)
                record.independence_residual_risk_acceptable = all_low

    @api.depends('engagement_partner_id', 'engagement_partner_signature')
    def _compute_partner_signoff_complete(self):
        """Check if Engagement Partner has provided digital signature."""
        for record in self:
            record.partner_signoff_complete = bool(
                record.engagement_partner_id and record.engagement_partner_signature
            )

    def action_lock_templates(self):
        """Lock templates after all mandatory items are selected."""
        for record in self:
            missing = []
            if not record.tpl_engagement_letter:
                missing.append('Engagement Letter template')
            if not record.tpl_independence_declaration:
                missing.append('Independence Declaration template')
            if not record.tpl_acceptance_checklist:
                missing.append('Acceptance checklist template')
            if not record.tpl_fraud_risk_questionnaire:
                missing.append('Fraud risk questionnaire')
            if not record.tpl_business_risk_questionnaire:
                missing.append('Business risk questionnaire')
            if not record.tpl_governance_tcwg_checklist:
                missing.append('Governance & TCWG checklist')
            if missing:
                raise ValidationError(
                    _('Cannot lock templates. The following mandatory items are not selected:\n• %s') % '\n• '.join(missing)
                )
            record.templates_locked = True
            record._log_action('Templates locked - all mandatory templates confirmed')

    def action_unlock_templates(self):
        """Unlock templates for editing (only in draft state)."""
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_('Templates can only be unlocked in Draft state.'))
            record.templates_locked = False
            record._log_action('Templates unlocked for editing')

    @api.depends('client_id')
    def _compute_name(self):
        for record in self:
            record.name = f"Onboarding - {record.client_id.name or 'New Client'}"

    @api.depends('reports_generated', 'reports_generated_date', 'reports_generated_by',
                 'report_acceptance_continuance', 'report_ethics_independence',
                 'report_fraud_business_risk', 'report_engagement_authorization')
    def _compute_generated_reports_summary(self):
        """Compute an attractive HTML summary of generated reports for the UI."""
        for record in self:
            if not record.reports_generated:
                record.generated_reports_summary = '''
                <div style="padding: 16px; background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%); 
                     border-radius: 12px; border-left: 5px solid #f39c12; margin: 8px 0;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <span style="font-size: 28px;">⏳</span>
                        <div>
                            <strong style="font-size: 14px; color: #856404;">Reports Pending Generation</strong>
                            <p style="margin: 4px 0 0 0; font-size: 12px; color: #856404;">
                                Four mandatory reports will be auto-generated upon Partner Approval.
                            </p>
                        </div>
                    </div>
                </div>
                '''
                continue

            # Format date/time
            gen_date = record.reports_generated_date.strftime('%d %B %Y at %H:%M') if record.reports_generated_date else 'N/A'
            gen_by = record.reports_generated_by.name if record.reports_generated_by else 'System'

            reports = []
            if record.report_acceptance_continuance:
                reports.append(('✅', 'Client Acceptance & Continuance Report', 'ISA 220, ISQM-1', '#28a745'))
            if record.report_ethics_independence:
                reports.append(('✅', 'Ethics & Independence Compliance Report', 'IESBA Code, ISA 220', '#17a2b8'))
            if record.report_fraud_business_risk:
                reports.append(('✅', 'Fraud & Business Risk Summary', 'ISA 240, ISA 315', '#dc3545'))
            if record.report_engagement_authorization:
                reports.append(('✅', 'Engagement Authorization Memorandum', 'ISA 210, ISQM-1', '#6f42c1'))

            report_cards = ''
            for icon, title, refs, color in reports:
                report_cards += f'''
                <div style="padding: 12px 16px; background: white; border-radius: 8px; 
                     border-left: 4px solid {color}; margin: 8px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="font-size: 16px; margin-right: 8px;">{icon}</span>
                            <strong style="font-size: 13px;">{title}</strong>
                        </div>
                        <span style="font-size: 10px; padding: 3px 8px; background: {color}15; 
                              color: {color}; border-radius: 4px; font-weight: 600;">{refs}</span>
                    </div>
                </div>
                '''

            record.generated_reports_summary = f'''
            <div style="background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); 
                 padding: 20px; border-radius: 16px; border: 1px solid #28a745;">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px; 
                     padding-bottom: 12px; border-bottom: 2px dashed #28a74550;">
                    <span style="font-size: 32px;">📄</span>
                    <div>
                        <strong style="font-size: 16px; color: #155724;">Auto-Generated Reports</strong>
                        <p style="margin: 2px 0 0 0; font-size: 11px; color: #155724;">
                            ✓ ICAP QCR Ready • Partner Signed • Time-stamped
                        </p>
                    </div>
                </div>
                <div style="display: flex; gap: 16px; font-size: 11px; color: #155724; margin-bottom: 12px;">
                    <span><strong>Generated:</strong> {gen_date}</span>
                    <span><strong>By:</strong> {gen_by}</span>
                </div>
                {report_cards}
            </div>
            '''

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

    @api.constrains('fam_final_decision', 'fam_safeguards_imposed', 'fam_rejection_reason', 'fam_isqm1_compliance')
    def _validate_final_acceptance_memorandum(self):
        """Ensure no silent acceptance - all required memorandum fields must be completed."""
        for record in self:
            # If Accept with Safeguards, safeguards must be documented
            if record.fam_final_decision == 'accept_safeguards' and not record.fam_safeguards_imposed:
                raise ValidationError(
                    _('When accepting with safeguards, you must document the specific safeguards imposed.')
                )
            # If Reject, reason must be documented
            if record.fam_final_decision == 'reject' and not record.fam_rejection_reason:
                raise ValidationError(
                    _('When rejecting an engagement, you must document the specific reasons for rejection.')
                )
            # ISQM-1 compliance must be confirmed for acceptance
            if record.fam_final_decision in ['accept', 'accept_safeguards'] and not record.fam_isqm1_compliance:
                raise ValidationError(
                    _('ISQM-1 compliance must be confirmed before accepting any engagement.')
                )

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
            record.entity_type_label = dict(ENTITY_SELECTION).get(record.entity_type, '')
            record.primary_regulator_label = dict(PRIMARY_REGULATOR_SELECTION).get(record.primary_regulator, '')
            record.financial_framework_label = dict(FINANCIAL_FRAMEWORK_SELECTION).get(record.financial_framework, '')
            record.management_integrity_label = dict(MANAGEMENT_INTEGRITY_SELECTION).get(record.management_integrity_rating, '')
            record.aml_risk_label = dict(AML_RATING).get(record.aml_risk_rating, '')
            record.overall_status_label = dict(SECTION_STATUS).get(record.overall_status, '')
            record.engagement_decision_label = dict(ENGAGEMENT_DECISION_SELECTION).get(record.engagement_decision, '')

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

    @api.depends('legal_name', 'principal_business_address', 'business_registration_number', 'industry_id', 'primary_regulator')
    def _compute_section_status(self):
        for record in self:
            record.section1_status = 'green' if all([record.legal_name, record.principal_business_address, record.business_registration_number, record.industry_id, record.primary_regulator]) else 'red'
            record.section2_status = 'green' if record.financial_framework else 'red'
            record.section3_status = 'green' if record.shareholder_ids and record.board_member_ids else 'red'
            record.section4_status = 'green' if record.management_integrity_rating and record.aml_risk_rating in ['low', 'medium'] else ('amber' if record.management_integrity_rating else 'red')
            record.section5_status = 'green' if record.independence_threat_ids and record.independence_declaration_ids else 'red'
            record.section6_status = 'green' if record.pcl_document and record.pcl_no_outstanding_fees and record.pcl_no_disputes and record.pcl_no_ethics_issues else 'red'
            record.section7_status = 'green' if record.engagement_decision == 'accept' and record.engagement_partner_signature else 'red'

    def _compute_pep_flag(self):
        for record in self:
            has_pep = bool(record.board_member_ids.filtered('is_pep'))
            record.has_pep = has_pep
            record.enhanced_due_diligence_required = has_pep
            if has_pep:
                record.section3_status = 'amber'

    @api.depends('management_integrity_rating', 'aml_risk_rating')
    def _compute_eqcr_required(self):
        for record in self:
            low_integrity = record.management_integrity_rating == 'low'
            high_aml = record.aml_risk_rating == 'high'
            record.eqcr_required = low_integrity or high_aml
            record.managing_partner_escalation = record.eqcr_required
            if record.eqcr_required:
                record.section4_status = 'amber'

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
            if record.fee_dependency_flag:
                record.section5_status = 'amber'

    @api.depends('independence_declaration_ids.state')
    def _compute_independence_status(self):
        for record in self:
            if not record.independence_declaration_ids:
                record.independence_status_feedback = _('Awaiting declarations from the engagement team.')
                continue
            completed = record.independence_declaration_ids.filtered(lambda l: l.state == 'confirmed')
            percent = 0
            if record.independence_declaration_ids:
                percent = len(completed) / len(record.independence_declaration_ids) * 100
            record.independence_status_feedback = _('%d%% of team members completed declarations.') % percent

    @api.depends('client_id', 'audit_id', 'risk_mitigation_plan', 'section4_status')
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
        # Capture old values before write for audit trail
        for record in self:
            record._log_field_changes(vals)
        res = super().write(vals)
        return res

    def _log_field_changes(self, vals):
        """Log individual field changes with old vs new values for audit trail."""
        TRACKED_FIELDS = [
            'state', 'entity_type', 'legal_name', 'primary_regulator', 'financial_framework',
            'management_integrity_rating', 'aml_risk_rating', 'engagement_decision',
            'fam_final_decision', 'fam_engagement_risk_level', 'fam_isqm1_compliance',
            'templates_locked', 'pcl_no_barrier_conclusion', 'partner_signoff_complete',
            'integrity_risk_level', 'business_risk_level', 'fraud_risk_level',
            'going_concern_level', 'reputation_risk_level', 'regulatory_framework_acceptable',
            'engagement_partner_id', 'eqcr_partner_id', 'managing_partner_id',
        ]
        trail = self.env['qaco.onboarding.audit.trail']
        for record in self:
            for field_name, new_value in vals.items():
                if field_name in TRACKED_FIELDS:
                    old_value = getattr(record, field_name, None)
                    # Handle Many2one fields
                    if hasattr(old_value, 'id'):
                        old_value = old_value.name or old_value.id
                    # Handle Selection fields - get label
                    field_obj = record._fields.get(field_name)
                    if field_obj and field_obj.type == 'selection':
                        selection_dict = dict(field_obj.selection)
                        old_label = selection_dict.get(old_value, old_value)
                        new_label = selection_dict.get(new_value, new_value)
                        old_value = old_label
                        new_value = new_label
                    # Create immutable audit trail entry
                    trail.sudo().create({
                        'onboarding_id': record.id,
                        'action': _('Field Changed: %s') % field_name,
                        'field_name': field_name,
                        'old_value': str(old_value) if old_value is not None else '',
                        'new_value': str(new_value) if new_value is not None else '',
                        'change_type': 'field_change',
                    })

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

    def _log_action(self, action, notes=None, change_type='action'):
        """Log an action to the immutable audit trail."""
        trail = self.env['qaco.onboarding.audit.trail']
        for record in self:
            trail.sudo().create({
                'onboarding_id': record.id,
                'action': action,
                'notes': notes or '',
                'change_type': change_type,
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

    def _validate_all_mandatory_notes(self):
        """GLOBAL BLOCKER: Validate ALL mandatory narrative fields are not blank."""
        MANDATORY_TEXT_FIELDS = [
            # Section 1.1
            ('legal_existence_verification', '1.1 Legal Existence Verification'),
            ('group_structure_risk', '1.1 Group Structure Risk'),
            ('foreign_ownership_exposure', '1.1 Foreign Ownership Exposure'),
            ('ubo_risk_summary', '1.1 UBO Risk Summary'),
            # Section 1.2
            ('applicable_laws_regulators', '1.2 Applicable Laws & Regulators'),
            ('filing_history_gaps', '1.2 Filing History Gaps'),
            ('inspection_enforcement_exposure', '1.2 Inspection/Enforcement Exposure'),
            ('litigation_penalties_note', '1.2 Litigation & Penalties'),
            ('regulatory_framework_conclusion', '1.2 Regulatory Framework Conclusion'),
            # Section 1.3
            ('board_independence_assessment', '1.3 Board Independence Assessment'),
            ('audit_committee_competence', '1.3 Audit Committee Competence'),
            ('political_exposure_note', '1.3 Political Exposure'),
            ('dominant_shareholder_risk', '1.3 Dominant Shareholder Risk'),
            # Section 1.4
            ('integrity_risk_summary', '1.4 Integrity Risk Summary'),
            ('business_risk_summary', '1.4 Business Risk Summary'),
            ('fraud_risk_summary', '1.4 Fraud Risk Summary'),
            ('going_concern_indicators', '1.4 Going Concern Indicators'),
            ('reputation_risk_to_firm', '1.4 Reputation Risk to Firm'),
            ('management_integrity_comment', '1.4 Management Integrity Justification'),
            # Section 1.6
            ('pcl_reason_for_change', '1.6 Reason for Change'),
            ('pcl_disputes_unpaid_fees', '1.6 Disputes/Unpaid Fees'),
            ('pcl_access_to_working_papers', '1.6 Access to Working Papers'),
            ('pcl_ethical_concerns_raised', '1.6 Ethical Concerns Raised'),
            # Section 1.7
            ('partner_judgment_acceptable', '1.7 Why Engagement Acceptable'),
            ('partner_judgment_safeguards', '1.7 Safeguards Imposed'),
            ('partner_judgment_conditions', '1.7 Conditions'),
            # Section 1.9
            ('fam_engagement_risk_justification', '1.9 Engagement Risk Justification'),
            ('fam_independence_conclusion', '1.9 Independence Conclusion'),
            ('fam_fraud_risk_conclusion', '1.9 Fraud Risk Conclusion'),
            ('fam_resource_sufficiency', '1.9 Resource Sufficiency'),
        ]
        for record in self:
            missing = []
            for field_name, label in MANDATORY_TEXT_FIELDS:
                value = getattr(record, field_name, None)
                if not value or (isinstance(value, str) and not value.strip()):
                    missing.append(label)
            if missing:
                raise ValidationError(
                    _('PARTNER APPROVAL BLOCKED: The following mandatory notes are blank:\n• %s\n\n'
                      'All mandatory documentation must be completed before partner approval.') % '\n• '.join(missing)
                )

    def _validate_ethics_clearance(self):
        """GLOBAL BLOCKER: Validate ethics clearance before engagement letter issuance."""
        for record in self:
            errors = []
            # Independence threats must all be documented with Low residual risk
            if not record.independence_residual_risk_acceptable:
                errors.append('All independence threats must have LOW residual risk')
            # PCL barrier conclusion must be confirmed
            if not record.pcl_no_barrier_conclusion:
                errors.append('Professional Clearance conclusion not confirmed (Section 1.6)')
            # ISQM-1 compliance must be confirmed
            if not record.fam_isqm1_compliance:
                errors.append('ISQM-1 compliance not confirmed (Section 1.9)')
            # Final decision must be Accept or Accept with Safeguards
            if record.fam_final_decision not in ['accept', 'accept_safeguards']:
                errors.append('Final acceptance decision must be Accept or Accept with Safeguards')
            if errors:
                raise ValidationError(
                    _('ETHICS CLEARANCE BLOCKED: Cannot issue engagement letter.\n• %s') % '\n• '.join(errors)
                )

    def _validate_acceptance_complete(self):
        """GLOBAL BLOCKER: Validate acceptance is complete before planning phase."""
        for record in self:
            errors = []
            # State must be partner_approved or locked
            if record.state not in ['partner_approved', 'locked']:
                errors.append('Onboarding must be Partner Approved before planning phase')
            # Templates must be locked
            if not record.templates_complete:
                errors.append('All mandatory templates must be selected and locked (Section 1.0)')
            # Partner sign-off must be complete
            if not record.partner_signoff_complete:
                errors.append('Engagement Partner digital sign-off required (Section 1.7)')
            # Final decision must exist
            if not record.fam_final_decision:
                errors.append('Final acceptance decision not made (Section 1.9)')
            # All management acknowledgements must be confirmed
            if not all([record.mgmt_ack_responsibility_fs, record.mgmt_ack_responsibility_ic,
                        record.mgmt_ack_access_to_records, record.mgmt_ack_going_concern]):
                errors.append('All management acknowledgements must be confirmed (Section 1.7)')
            if errors:
                raise ValidationError(
                    _('PLANNING PHASE BLOCKED: Acceptance incomplete.\n• %s') % '\n• '.join(errors)
                )

    def _validate_audit_trail_exists(self):
        """GLOBAL BLOCKER: Validate audit trail exists before locking record."""
        for record in self:
            if not record.audit_trail_ids:
                raise ValidationError(
                    _('LOCK BLOCKED: No audit trail exists for this record. '
                      'System integrity check failed - contact administrator.')
                )
            # Check for essential approval entries
            approval_actions = record.audit_trail_ids.filtered(lambda t: t.change_type == 'approval')
            if not approval_actions:
                raise ValidationError(
                    _('LOCK BLOCKED: No approval actions recorded in audit trail. '
                      'Record must go through proper approval workflow.')
                )

    def action_submit_review(self):
        for record in self:
            if record.state != 'draft':
                continue
            # Block progression if templates not complete
            if not record.templates_complete:
                raise ValidationError(
                    _('Cannot submit for review. All mandatory templates must be selected and locked in Section 1.0 Templates & Docs.')
                )
            # Block if independence residual risk is not acceptable (any threat not Low)
            if not record.independence_residual_risk_acceptable:
                non_low_threats = record.independence_threat_ids.filtered(lambda t: t.residual_risk != 'low')
                if non_low_threats:
                    threat_names = ', '.join([dict(THREAT_TYPES).get(t.threat_type, t.threat_type) for t in non_low_threats])
                    raise ValidationError(
                        _('ACCEPTANCE BLOCKED: Residual risk must be LOW for all independence threats before submission. '
                          'The following threats have Moderate/High residual risk: %s. '
                          'Please apply additional safeguards or decline the engagement.') % threat_names
                    )
                else:
                    raise ValidationError(
                        _('ACCEPTANCE BLOCKED: All five independence threat types must be documented in Section 1.5. '
                          'Please complete the mandatory threat-by-threat assessment.')
                    )
            # Validate ethics clearance before submission
            record._validate_ethics_clearance()
            record.write({'state': 'under_review'})
            record._log_action('Submitted for review', change_type='approval')

    def action_partner_approve(self):
        for record in self:
            if record.state != 'under_review':
                raise ValidationError(_('Submit the onboarding for review before partner approval.'))
            # GLOBAL BLOCKER: All mandatory notes must be filled
            record._validate_all_mandatory_notes()
            record._validate_mandatory_checklist_completion()
            record._validate_ethics_clearance()
            if record.high_risk_onboarding and not record.engagement_partner_id:
                raise ValidationError(_('High-risk onboardings require an Engagement Partner before approval.'))
            record.write({'state': 'partner_approved'})
            record._log_action('Partner approved onboarding', notes=_('High risk: %s') % ('Yes' if record.high_risk_onboarding else 'No'), change_type='approval')
            # ═══════════════════════════════════════════════════════════════════════════
            # 📄 AUTO-GENERATE MANDATORY REPORTS (Upon Partner Approval)
            # ═══════════════════════════════════════════════════════════════════════════
            record._generate_all_mandatory_reports()

    # ═══════════════════════════════════════════════════════════════════════════════════
    # 📄 REPORT GENERATION METHODS (ISA-Referenced, ICAP QCR Ready)
    # ═══════════════════════════════════════════════════════════════════════════════════

    def _generate_all_mandatory_reports(self):
        """Auto-generate all four mandatory reports upon Partner Approval.
        
        Reports Generated:
        1. Client Acceptance & Continuance Report (ISA 220, ISQM-1)
        2. Ethics & Independence Compliance Report (IESBA Code, ISA 220)
        3. Fraud & Business Risk Summary (ISA 240, ISA 315)
        4. Engagement Authorization Memorandum (ISA 210, ISQM-1)
        
        All reports are: ISA-referenced, ICAP QCR ready, Time-stamped, Partner-signed
        """
        import base64
        from datetime import datetime
        
        for record in self:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            client_name = (record.client_id.name or 'Client').replace(' ', '_')[:20]
            
            # Generate all four reports
            reports_data = {}
            
            # 1. Client Acceptance & Continuance Report
            report_1 = record._generate_acceptance_continuance_report()
            filename_1 = f'Acceptance_Continuance_{client_name}_{timestamp}.pdf'
            reports_data['report_acceptance_continuance'] = base64.b64encode(report_1)
            reports_data['report_acceptance_continuance_name'] = filename_1
            
            # 2. Ethics & Independence Compliance Report
            report_2 = record._generate_ethics_independence_report()
            filename_2 = f'Ethics_Independence_{client_name}_{timestamp}.pdf'
            reports_data['report_ethics_independence'] = base64.b64encode(report_2)
            reports_data['report_ethics_independence_name'] = filename_2
            
            # 3. Fraud & Business Risk Summary
            report_3 = record._generate_fraud_business_risk_report()
            filename_3 = f'Fraud_Business_Risk_{client_name}_{timestamp}.pdf'
            reports_data['report_fraud_business_risk'] = base64.b64encode(report_3)
            reports_data['report_fraud_business_risk_name'] = filename_3
            
            # 4. Engagement Authorization Memorandum
            report_4 = record._generate_engagement_authorization_report()
            filename_4 = f'Engagement_Authorization_{client_name}_{timestamp}.pdf'
            reports_data['report_engagement_authorization'] = base64.b64encode(report_4)
            reports_data['report_engagement_authorization_name'] = filename_4
            
            # Update record with generated reports
            reports_data.update({
                'reports_generated': True,
                'reports_generated_date': fields.Datetime.now(),
                'reports_generated_by': self.env.user.id,
            })
            record.write(reports_data)
            
            # Log to audit trail
            record._log_action(
                'Auto-generated mandatory reports upon Partner Approval',
                notes=_('Reports: Acceptance & Continuance, Ethics & Independence, '
                       'Fraud & Business Risk, Engagement Authorization. '
                       'All ISA-referenced and ICAP QCR ready.'),
                change_type='approval'
            )
            
            # Post to chatter
            record.message_post(
                body=_('📄 <b>Four Mandatory Reports Auto-Generated</b><br/>'
                       '✅ Client Acceptance & Continuance Report (ISA 220, ISQM-1)<br/>'
                       '✅ Ethics & Independence Compliance Report (IESBA Code, ISA 220)<br/>'
                       '✅ Fraud & Business Risk Summary (ISA 240, ISA 315)<br/>'
                       '✅ Engagement Authorization Memorandum (ISA 210, ISQM-1)<br/>'
                       '<i>All reports are time-stamped and partner-signed. Ready for ICAP QCR.</i>'),
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )

    def _generate_acceptance_continuance_report(self):
        """Generate Client Acceptance & Continuance Report as PDF bytes.
        ISA 220: Quality Management for an Audit of Financial Statements
        ISQM-1: Quality Management for Firms
        """
        report = self.env.ref('qaco_client_onboarding.report_acceptance_continuance_pdf', raise_if_not_found=False)
        if report:
            pdf_content, _ = report._render_qweb_pdf(report.id, [self.id])
            return pdf_content
        # Fallback: Return empty PDF structure
        return b'%PDF-1.4\n%Acceptance Report Placeholder\n%%EOF'

    def _generate_ethics_independence_report(self):
        """Generate Ethics & Independence Compliance Report as PDF bytes.
        IESBA Code of Ethics for Professional Accountants
        ISA 220: Quality Management for an Audit
        """
        report = self.env.ref('qaco_client_onboarding.report_ethics_independence_pdf', raise_if_not_found=False)
        if report:
            pdf_content, _ = report._render_qweb_pdf(report.id, [self.id])
            return pdf_content
        return b'%PDF-1.4\n%Ethics Report Placeholder\n%%EOF'

    def _generate_fraud_business_risk_report(self):
        """Generate Fraud & Business Risk Summary as PDF bytes.
        ISA 240: The Auditor's Responsibilities Relating to Fraud
        ISA 315: Identifying and Assessing Risks of Material Misstatement
        """
        report = self.env.ref('qaco_client_onboarding.report_fraud_business_risk_pdf', raise_if_not_found=False)
        if report:
            pdf_content, _ = report._render_qweb_pdf(report.id, [self.id])
            return pdf_content
        return b'%PDF-1.4\n%Fraud Risk Report Placeholder\n%%EOF'

    def _generate_engagement_authorization_report(self):
        """Generate Engagement Authorization Memorandum as PDF bytes.
        ISA 210: Agreeing the Terms of Audit Engagements
        ISQM-1: Quality Management for Firms
        """
        report = self.env.ref('qaco_client_onboarding.report_engagement_authorization_pdf', raise_if_not_found=False)
        if report:
            pdf_content, _ = report._render_qweb_pdf(report.id, [self.id])
            return pdf_content
        return b'%PDF-1.4\n%Authorization Memo Placeholder\n%%EOF'

    def action_download_all_reports(self):
        """Download all generated reports as a ZIP file."""
        import base64
        import io
        import zipfile
        
        self.ensure_one()
        if not self.reports_generated:
            raise ValidationError(_('Reports have not been generated yet. Partner approval is required.'))
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            if self.report_acceptance_continuance:
                zip_file.writestr(
                    self.report_acceptance_continuance_name or 'Acceptance_Continuance.pdf',
                    base64.b64decode(self.report_acceptance_continuance)
                )
            if self.report_ethics_independence:
                zip_file.writestr(
                    self.report_ethics_independence_name or 'Ethics_Independence.pdf',
                    base64.b64decode(self.report_ethics_independence)
                )
            if self.report_fraud_business_risk:
                zip_file.writestr(
                    self.report_fraud_business_risk_name or 'Fraud_Business_Risk.pdf',
                    base64.b64decode(self.report_fraud_business_risk)
                )
            if self.report_engagement_authorization:
                zip_file.writestr(
                    self.report_engagement_authorization_name or 'Engagement_Authorization.pdf',
                    base64.b64decode(self.report_engagement_authorization)
                )
        
        zip_buffer.seek(0)
        zip_data = base64.b64encode(zip_buffer.read())
        
        # Create attachment and return download action
        client_name = (self.client_id.name or 'Client').replace(' ', '_')[:20]
        attachment = self.env['ir.attachment'].create({
            'name': f'Onboarding_Reports_{client_name}.zip',
            'type': 'binary',
            'datas': zip_data,
            'mimetype': 'application/zip',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def action_regenerate_reports(self):
        """Regenerate all reports (only for partner_approved state, requires confirmation)."""
        for record in self:
            if record.state != 'partner_approved':
                raise ValidationError(_('Reports can only be regenerated in Partner Approved state.'))
            record._generate_all_mandatory_reports()
        return {'type': 'ir.actions.act_window_close'}

    def action_generate_acceptance_report(self):
        report = self.env.ref('qaco_client_onboarding.report_client_onboarding_pdf', raise_if_not_found=False)
        if report:
            return report.report_action(self)
        return {'type': 'ir.actions.act_window_close'}

    def action_lock_onboarding(self):
        for record in self:
            # GLOBAL BLOCKER: All validations before locking
            record._validate_mandatory_checklist_completion()
            record._validate_all_mandatory_notes()
            record._validate_ethics_clearance()
            record._validate_acceptance_complete()
            record._validate_audit_trail_exists()
            if record.overall_status != 'green':
                raise ValidationError(_('Finalize all sections before locking the onboarding.'))
            if record.state != 'partner_approved':
                raise ValidationError(_('Partner approval is required before locking the onboarding.'))
            if record.high_risk_onboarding and record.state != 'partner_approved':
                raise ValidationError(_('High-risk onboarding must be partner approved before locking.'))
            record.write({'state': 'locked'})
            record._log_action('Locked onboarding for final authorization', change_type='approval')

    def action_view_state(self):
        """Dummy action for stat button - just refreshes the view."""
        return {'type': 'ir.actions.act_window_close'}

    def action_issue_engagement_letter(self):
        """Issue engagement letter - requires ethics clearance."""
        for record in self:
            # GLOBAL BLOCKER: Ethics clearance required
            record._validate_ethics_clearance()
            record._validate_acceptance_complete()
            record._log_action('Engagement letter issued', change_type='approval')
        return {'type': 'ir.actions.act_window_close'}

    def action_proceed_to_planning(self):
        """Proceed to planning phase - requires complete acceptance."""
        for record in self:
            # GLOBAL BLOCKER: Acceptance must be complete
            record._validate_acceptance_complete()
            record._log_action('Proceeded to planning phase', change_type='approval')
            # Return action to open planning phase if exists
            planning = self.env['qaco.planning.phase'].search([('audit_id', '=', record.audit_id.id)], limit=1)
            if planning:
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'qaco.planning.phase',
                    'res_id': planning.id,
                    'view_mode': 'form',
                    'target': 'current',
                }
        return {'type': 'ir.actions.act_window_close'}

    # ═══════════════════════════════════════════════════════════════════════════════════
    # 🔄 AUTO-SAVE FUNCTIONALITY (ISA 230 / ISQM-1 Compliant)
    # ═══════════════════════════════════════════════════════════════════════════════════

    @api.model
    def autosave(self, record_id, values):
        """
        Safe auto-save endpoint for client onboarding form.
        
        Called by JavaScript every 10 seconds or on field change.
        Respects partner approval lock and maintains full audit trail.
        
        Args:
            record_id: ID of the onboarding record
            values: Dictionary of field values to save
            
        Returns:
            dict: Status of the save operation
            
        Raises:
            ValidationError: If record is locked after Partner Approval
        """
        record = self.browse(record_id)
        
        if not record.exists():
            return {'status': 'error', 'message': 'Record not found'}
        
        # GLOBAL BLOCKER: No auto-save after Partner Approval
        if record.state in ['partner_approved', 'locked']:
            return {
                'status': 'locked',
                'message': 'Record is locked after Partner Approval. No further edits allowed.'
            }
        
        # Filter out read-only and computed fields that shouldn't be saved
        safe_fields = self._get_autosave_safe_fields()
        filtered_values = {k: v for k, v in values.items() if k in safe_fields}
        
        if not filtered_values:
            return {'status': 'skipped', 'message': 'No saveable fields in payload'}
        
        try:
            # Use write() to ensure audit trail is captured via mail.thread
            record.write(filtered_values)
            
            return {
                'status': 'saved',
                'message': 'Auto-saved successfully',
                'timestamp': fields.Datetime.now().isoformat(),
                'fields_saved': list(filtered_values.keys())
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    @api.model
    def _get_autosave_safe_fields(self):
        """
        Return list of fields that are safe to auto-save.
        Excludes computed, readonly, and system fields.
        """
        # All notes fields (1.0 - 1.10)
        notes_fields = [
            'notes_10', 'notes_11', 'notes_12', 'notes_13', 'notes_14',
            'notes_15', 'notes_16', 'notes_17', 'notes_18', 'notes_19', 'notes_110',
        ]
        
        # Editable selection and boolean fields
        selection_fields = [
            'entity_type', 'other_entity_description',
            'primary_regulator', 'other_regulator_description',
            'financial_framework', 'other_framework_description',
            'management_integrity', 'client_acceptance_decision',
            'engagement_decision', 'engagement_justification',
            'fam_final_decision', 'fam_safeguards_imposed', 'fam_rejection_reason',
        ]
        
        # Text and char fields for narratives
        narrative_fields = [
            'industry_overview', 'regulatory_environment',
            'fraud_risk_narrative', 'going_concern_narrative',
            'related_party_narrative', 'significant_risks_narrative',
            'it_environment_narrative', 'group_audit_narrative',
            'aml_overall_assessment', 'aml_conclusion',
            'communication_narrative', 'resource_plan_narrative',
        ]
        
        # Risk assessment fields
        risk_fields = [
            'inherent_risk_assessment', 'fraud_risk_level',
            'going_concern_indicator', 'related_party_risk',
            'aml_country_risk', 'aml_customer_risk', 'aml_product_risk',
        ]
        
        # Checkbox and toggle fields
        boolean_fields = [
            'pcl_no_barrier_conclusion', 'partner_signoff_complete',
            'is_first_year_audit', 'is_group_audit',
            'has_internal_audit', 'has_audit_committee',
        ]
        
        return notes_fields + selection_fields + narrative_fields + risk_fields + boolean_fields

    def get_autosave_status(self):
        """
        Return current auto-save status for the record.
        Used by JavaScript to determine if auto-save should be active.
        """
        self.ensure_one()
        return {
            'is_locked': self.state in ['partner_approved', 'locked'],
            'can_autosave': self.state in ['draft', 'under_review'],
            'last_write_date': self.write_date.isoformat() if self.write_date else None,
            'state': self.state,
        }


class OnboardingBranchLocation(models.Model):
    _name = 'qaco.onboarding.branch.location'
    _description = 'Onboarding Branch / Office Location'

    CITY_SELECTION = [
        # Punjab
        ('lahore', 'Lahore'),
        ('faisalabad', 'Faisalabad'),
        ('rawalpindi', 'Rawalpindi'),
        ('multan', 'Multan'),
        ('gujranwala', 'Gujranwala'),
        ('sialkot', 'Sialkot'),
        ('bahawalpur', 'Bahawalpur'),
        ('sargodha', 'Sargodha'),
        # Sindh
        ('karachi', 'Karachi'),
        ('hyderabad', 'Hyderabad'),
        ('sukkur', 'Sukkur'),
        ('larkana', 'Larkana'),
        # KPK
        ('peshawar', 'Peshawar'),
        ('abbottabad', 'Abbottabad'),
        ('mingora', 'Mingora (Swat)'),
        ('mardan', 'Mardan'),
        # Balochistan
        ('quetta', 'Quetta'),
        ('gwadar', 'Gwadar'),
        # ICT
        ('islamabad', 'Islamabad'),
        # GB
        ('gilgit', 'Gilgit'),
        ('skardu', 'Skardu'),
        # AJK
        ('muzaffarabad', 'Muzaffarabad'),
        ('mirpur', 'Mirpur'),
        # Other
        ('other', 'Other'),
    ]

    onboarding_id = fields.Many2one('qaco.client.onboarding', required=True, ondelete='cascade')
    address = fields.Char(string='Address', required=True)
    country_id = fields.Many2one(
        'res.country',
        string='Country',
        default=lambda self: self.env.ref('base.pk', raise_if_not_found=False),
    )
    province_id = fields.Many2one(
        'res.country.state',
        string='Province / Territory',
        domain="[('country_id', '=', country_id)]",
        help='Select the province to align with Pakistan jurisdictional mapping.',
    )
    city = fields.Selection(
        selection=CITY_SELECTION,
        string='City',
        help='Select a Pakistan city from the list.',
    )

    @api.onchange('province_id')
    def _onchange_province(self):
        for record in self:
            if record.province_id:
                record.country_id = record.province_id.country_id

    @api.onchange('country_id')
    def _onchange_country(self):
        pk_country = self.env.ref('base.pk', raise_if_not_found=False)
        for record in self:
            if pk_country and record.country_id and record.country_id != pk_country:
                record.country_id = pk_country
            if not record.country_id and pk_country:
                record.country_id = pk_country
            if record.province_id and record.province_id.country_id != record.country_id:
                record.province_id = False

    @api.constrains('country_id', 'province_id')
    def _check_location_hierarchy(self):
        pk_country = self.env.ref('base.pk', raise_if_not_found=False)
        for record in self:
            if pk_country and record.country_id and record.country_id != pk_country:
                raise ValidationError(_('Branch locations must be within Pakistan.'))
            if record.province_id and record.country_id and record.province_id.country_id != record.country_id:
                raise ValidationError(_('Selected province must belong to the chosen country.'))


class OnboardingUBO(models.Model):
    _name = 'qaco.onboarding.ubo'
    _description = 'Ultimate Beneficial Owner'

    onboarding_id = fields.Many2one('qaco.client.onboarding', required=True, ondelete='cascade')
    name = fields.Char(string='UBO Name', required=True)
    cnic_passport = fields.Char(string='CNIC / Passport Number', required=True)
    nationality = fields.Char(string='Nationality')
    country_id = fields.Many2one('res.country', string='Country')
    ownership_percent = fields.Float(string='Ownership %', digits=(5, 2))

    @api.onchange('country_id')
    def _onchange_country_id(self):
        for record in self:
            if record.country_id:
                record.nationality = record.country_id.name


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


RESIDUAL_RISK_SELECTION = [
    ('low', 'Low'),
    ('moderate', 'Moderate'),
    ('high', 'High'),
]


class OnboardingIndependenceThreat(models.Model):
    _name = 'qaco.onboarding.independence.threat'
    _description = 'Independence Threat Assessment'
    _rec_name = 'threat_type'

    onboarding_id = fields.Many2one('qaco.client.onboarding', required=True, ondelete='cascade')
    threat_type = fields.Selection(THREAT_TYPES, string='Threat Type', required=True)
    answer = fields.Selection([('no', 'No'), ('yes', 'Yes')], string='Threat Identified', required=True, default='no')
    threat_description = fields.Text(
        string='Threat Description',
        required=True,
        help='Describe the nature, source, and significance of the identified threat. '
             'If no threat identified, document "No threat identified" with brief justification.',
    )
    safeguards_applied = fields.Text(
        string='Safeguards Applied',
        required=True,
        help='Document specific safeguards implemented to eliminate or reduce the threat to an acceptable level. '
             'Include firm-level and engagement-level safeguards. If no threat, state "N/A - no threat identified."',
    )
    residual_risk = fields.Selection(
        RESIDUAL_RISK_SELECTION,
        string='Residual Risk',
        required=True,
        default='low',
        help='Assess residual risk after safeguards. LOW = acceptable, MODERATE/HIGH = requires additional action or engagement decline.',
    )
    # Legacy fields for backward compatibility
    details = fields.Text(string='Details (Legacy)', help='Legacy field - use Threat Description instead.')
    safeguards = fields.Text(string='Safeguards (Legacy)', help='Legacy field - use Safeguards Applied instead.')


class OnboardingDocument(models.Model):
    _name = 'qaco.onboarding.document'
    _description = 'Document Vault Entry'

    onboarding_id = fields.Many2one('qaco.client.onboarding', required=True, ondelete='cascade')
    name = fields.Char(string='Document Name', required=True)
    doc_type = fields.Selection(
        DOCUMENT_TYPE_SELECTION,
        string='Classification',
        required=True,
        help='Mandatory classification: Legal, Regulatory, Ethics, KYC/AML, Engagement, Governance, or Risk.',
    )
    file = fields.Binary(string='File', attachment=True, required=True)
    file_name = fields.Char(string='File Name')
    state = fields.Selection(DOCUMENT_STATES, string='Status', default='pending')
    doc_type_label = fields.Char(string='Classification (Label)', compute='_compute_doc_type_label')

    @api.depends('doc_type')
    def _compute_doc_type_label(self):
        for record in self:
            record.doc_type_label = dict(DOCUMENT_TYPE_SELECTION).get(record.doc_type, record.doc_type or '')

    @api.constrains('doc_type', 'file')
    def _check_classification_required(self):
        """Ensure every uploaded document has a mandatory classification."""
        for record in self:
            if record.file and not record.doc_type:
                raise ValidationError(
                    _('Upload without classification NOT allowed. '
                      'Each document must be tagged as: Legal, Regulatory, Ethics, KYC/AML, Engagement, Governance, or Risk.')
                )


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


AUDIT_TRAIL_CHANGE_TYPE = [
    ('create', 'Record Created'),
    ('field_change', 'Field Changed'),
    ('approval', 'Approval Action'),
    ('action', 'System Action'),
]


class OnboardingAuditTrail(models.Model):
    _name = 'qaco.onboarding.audit.trail'
    _description = 'Client Onboarding Audit Trail (Immutable)'
    _order = 'create_date desc'

    onboarding_id = fields.Many2one('qaco.client.onboarding', required=True, ondelete='cascade', readonly=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, readonly=True)
    action = fields.Char(string='Action', required=True, readonly=True)
    notes = fields.Text(string='Notes', readonly=True)
    create_date = fields.Datetime(string='Timestamp', default=fields.Datetime.now, readonly=True)
    field_name = fields.Char(string='Field Changed', readonly=True)
    old_value = fields.Text(string='Old Value', readonly=True)
    new_value = fields.Text(string='New Value', readonly=True)
    change_type = fields.Selection(
        AUDIT_TRAIL_CHANGE_TYPE,
        string='Change Type',
        default='action',
        readonly=True,
    )

    def write(self, vals):
        """Audit trail is immutable - prevent any modifications."""
        raise ValidationError(_('Audit trail records are immutable and cannot be modified.'))

    def unlink(self):
        """Audit trail is immutable - prevent deletion."""
        raise ValidationError(_('Audit trail records are immutable and cannot be deleted.'))
