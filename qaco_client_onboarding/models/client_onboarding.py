# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

try:
    from odoo.addons.qaco_client_onboarding.models.audit_compliance import (
        ONBOARDING_AREAS,
    )  # type: ignore
except ImportError:  # pragma: no cover - fallback for static analysis or path issues
    from .audit_compliance import ONBOARDING_AREAS  # type: ignore

import re
import base64

_logger = logging.getLogger(__name__)

ENTITY_SELECTION = [
    ("pic", "Public Interest Company (PIC)"),
    ("lsc", "Large-Sized Company (LSC)"),
    ("msc", "Medium-Sized Company (MSC)"),
    ("ssc", "Small-Sized Company (SSC)"),
    ("section_42", "Section 42 Company"),
    ("npo", "Not-for-Profit Organization (NPO)"),
    ("sole", "Sole Proprietorship"),
    ("partnership", "Partnership"),
    ("other", "Other (Specify)"),
]

PRIMARY_REGULATOR_SELECTION = [
    ("secp", "SECP"),
    ("sbp", "SBP"),
    ("pemra", "PEMRA"),
    ("pta", "PTA"),
    ("fbr", "FBR"),
    ("provincial", "Provincial Authority"),
    ("other", "Other (Specify)"),
]

FINANCIAL_FRAMEWORK_SELECTION = [
    ("ifrs", "IFRS as adopted by ICAP"),
    ("ifrs_smes", "IFRS for SMEs"),
    ("companies_act", "Companies Act 2017 Schedules"),
    ("other_framework", "Other (Specify)"),
]

SECTION_STATUS = [
    ("red", "Not Started"),
    ("amber", "In Progress / Attention Required"),
    ("green", "Complete & Compliant"),
]

AML_RATING = [
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
]

MANAGEMENT_INTEGRITY_SELECTION = [
    ("high", "High"),
    ("medium", "Medium"),
    ("low", "Low"),
]

ENGAGEMENT_DECISION_SELECTION = [
    ("accept", "Accept"),
    ("reject", "Reject"),
    ("conditions", "Subject to Conditions"),
]

THREAT_TYPES = [
    ("self_interest", "Self-Interest Threat"),
    ("self_review", "Self-Review Threat"),
    ("advocacy", "Advocacy Threat"),
    ("familiarity", "Familiarity Threat"),
    ("intimidation", "Intimidation Threat"),
]

DOCUMENT_STATES = [
    ("pending", "Pending"),
    ("received", "Received"),
    ("reviewed", "Reviewed"),
]

DOCUMENT_TYPE_SELECTION = [
    ("org_chart", "Organizational Chart"),
    ("legal", "Legal Register"),
    ("pcl", "Professional Clearance Letter"),
    ("other", "Other"),
]

CHECKLIST_ANSWER_SELECTION = [
    ("compliant", "Compliant"),
    ("non_compliant", "Non-Compliant"),
    ("na", "Not Applicable"),
]

ONBOARDING_STATUS = [
    ("draft", "Draft"),
    ("under_review", "Under Review"),
    ("partner_approved", "Partner Approved"),
    ("locked", "Locked"),
]


class ClientOnboarding(models.Model):
    _name = "qaco.client.onboarding"
    _description = "Client Onboarding"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Onboarding Title", compute="_compute_name", store=True)
    audit_id = fields.Many2one(
        "qaco.audit", string="Audit", required=True, ondelete="cascade", index=True
    )
    client_id = fields.Many2one(
        "res.partner",
        string="Client",
        related="audit_id.client_id",
        readonly=True,
        store=False,
    )
    firm_name = fields.Many2one(
        "audit.firm.name",
        string="Firm Name",
        related="audit_id.firm_name",
        readonly=True,
        store=False,
    )

    # Section 0: Gateway fields
    entity_type = fields.Selection(
        ENTITY_SELECTION, string="Entity Type", required=True, tracking=True
    )
    other_entity_description = fields.Char(string="Specify Other Entity Type")
    entity_type_guidance = fields.Char(
        string="Entity Gateway Guidance",
        default="Select the entity classification that dictates mandatory thresholds, regulatory obligations, and risk profiles.",
    )
    state = fields.Selection(
        ONBOARDING_STATUS, string="Approval Status", default="draft", tracking=True
    )
    overall_status = fields.Selection(
        SECTION_STATUS,
        string="Onboarding Status",
        compute="_compute_overall_status",
        store=True,
        tracking=True,
        default="red",
    )
    progress_percentage = fields.Float(
        string="Completion Progress", compute="_compute_progress", store=True
    )
    section1_status = fields.Selection(
        SECTION_STATUS,
        string="Section 1 Status",
        compute="_compute_section_status",
        store=True,
    )
    section2_status = fields.Selection(
        SECTION_STATUS,
        string="Section 2 Status",
        compute="_compute_section_status",
        store=True,
    )
    section3_status = fields.Selection(
        SECTION_STATUS,
        string="Section 3 Status",
        compute="_compute_section_status",
        store=True,
    )
    section4_status = fields.Selection(
        SECTION_STATUS,
        string="Section 4 Status",
        compute="_compute_section_status",
        store=True,
    )
    section5_status = fields.Selection(
        SECTION_STATUS,
        string="Section 5 Status",
        compute="_compute_section_status",
        store=True,
    )
    section6_status = fields.Selection(
        SECTION_STATUS,
        string="Section 6 Status",
        compute="_compute_section_status",
        store=True,
    )
    section7_status = fields.Selection(
        SECTION_STATUS,
        string="Section 7 Status",
        compute="_compute_section_status",
        store=True,
    )
    entity_type_label = fields.Char(
        string="Entity Type Label", compute="_compute_selection_labels"
    )
    primary_regulator_label = fields.Char(
        string="Primary Regulator Label", compute="_compute_selection_labels"
    )
    financial_framework_label = fields.Char(
        string="Financial Framework Label", compute="_compute_selection_labels"
    )
    management_integrity_label = fields.Char(
        string="Management Integrity Label", compute="_compute_selection_labels"
    )
    aml_risk_label = fields.Char(
        string="AML Risk Label", compute="_compute_selection_labels"
    )
    overall_status_label = fields.Char(
        string="Overall Status Label", compute="_compute_selection_labels"
    )
    engagement_decision_label = fields.Char(
        string="Engagement Decision Label", compute="_compute_selection_labels"
    )
    audit_standard_ids = fields.Many2many(
        "audit.standard.library",
        string="Auditing Standards & References",
        tracking=True,
    )
    audit_standard_overview = fields.Html(
        string="Selected Standards Overview",
        compute="_compute_audit_standard_overview",
        sanitize=False,
    )
    regulator_checklist_line_ids = fields.One2many(
        "audit.onboarding.checklist",
        "onboarding_id",
        string="Regulator Onboarding Checklist",
    )
    high_risk_onboarding = fields.Boolean(
        string="High-Risk Onboarding", compute="_compute_high_risk", store=True
    )
    regulator_checklist_completion = fields.Float(
        string="Mandatory Checklist Completion %",
        compute="_compute_regulator_checklist_summary",
        store=True,
    )
    regulator_checklist_overview = fields.Html(
        string="Checklist Summary",
        compute="_compute_regulator_checklist_summary",
        store=False,
        sanitize=False,
    )

    attached_template_ids = fields.One2many(
        "qaco.onboarding.attached.template",
        "onboarding_id",
        string="Attached Templates",
    )

    # Stored Template Library: active templates available for quick attach in the onboarding UI
    template_library_rel_ids = fields.Many2many(
        "qaco.onboarding.template.document",
        "qaco_onb_tlib_rel",
        "onboarding_id",
        "template_id",
        string="Template Library",
        readonly=False,
    )

    # Template library population helper
    def populate_template_library(self):
        """Populate `template_library_rel_ids` with active templates for these records."""
        Template = self.env["qaco.onboarding.template.document"]
        active_templates = Template.search([("active", "=", True)])
        if not active_templates:
            return
        for rec in self:
            if not rec.template_library_rel_ids:
                rec.template_library_rel_ids = [(6, 0, active_templates.ids)]

    # Section 1: Legal Identity
    legal_name = fields.Char(string="Legal Name", required=True)
    trading_name = fields.Char(string="Trading Name")
    incorporation_date = fields.Date(string="Incorporation / Registration Date")
    incorporation_authority = fields.Selection(
        [
            ("secp", "SECP"),
            ("registrar_of_firms", "Registrar of Firms"),
            ("trust", "Trust/Deed Authority"),
            ("society", "Societies Registrar"),
            ("other", "Other"),
        ],
        string="Incorporation / Registration Authority",
    )
    incorporation_authority_other = fields.Char(string="Other Authority Details")
    registration_status = fields.Selection(
        [
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("liquidation", "Under liquidation"),
        ],
        string="Status on Register",
    )
    registration_status_verified_on = fields.Date(string="Status Verified On")
    registered_share_capital = fields.Monetary(
        string="Registered Share Capital", currency_field="currency_id"
    )
    financial_year_end = fields.Date(string="Financial Year End")
    principal_activities = fields.Text(string="Principal Activities")
    principal_business_address = fields.Char(
        string="Principal Business Address", required=True
    )
    branch_location_ids = fields.One2many(
        "qaco.onboarding.branch.location",
        "onboarding_id",
        string="Branch and Office Locations",
    )
    ntn = fields.Char(string="NTN", help="Enter in format 1234567-1")
    strn = fields.Char(
        string="STRN", help="State the Sales Tax Registration Number if applicable"
    )
    withholding_agent = fields.Selection(
        [("yes", "Yes"), ("no", "No")], string="Withholding Agent"
    )
    other_statutory_registrations = fields.Char(
        string="Other Statutory Registrations (EOBI/Social Security/etc)"
    )
    business_registration_number = fields.Char(
        string="Business Registration Number", required=True
    )
    industry_id = fields.Many2one(
        "qaco.onboarding.industry", string="Industry / Sector", index=True
    )
    primary_regulator = fields.Selection(
        PRIMARY_REGULATOR_SELECTION, string="Primary Regulator", required=True
    )
    regulator_other = fields.Char(string="Other Regulator Details")
    org_chart_attachment = fields.Binary(string="Group Structure / Org Chart")
    org_chart_name = fields.Char(string="Org Chart File Name")
    ubo_ids = fields.One2many(
        "qaco.onboarding.ubo", "onboarding_id", string="Ultimate Beneficial Owners"
    )
    # Official contacts
    primary_contact_name = fields.Char(string="Primary Contact")
    primary_contact_designation = fields.Char(string="Primary Contact Designation")
    primary_contact_email = fields.Char(string="Primary Contact Email")
    primary_contact_phone = fields.Char(string="Primary Contact Phone")
    finance_head_name = fields.Char(string="Finance Head")
    finance_head_email = fields.Char(string="Finance Head Email")
    finance_head_phone = fields.Char(string="Finance Head Phone")
    company_secretary_name = fields.Char(string="Company Secretary / Legal Focal")
    it_focal_person = fields.Char(string="IT Focal Person")
    # Signatories
    signatory_ids = fields.One2many(
        "qaco.onboarding.signatory", "onboarding_id", string="Authorized Signatories"
    )
    signatory_count = fields.Integer(
        string="Signatory Count", compute="_compute_signatory_count", store=True
    )
    # Verification & Controls
    verification_performed_by = fields.Many2one(
        "res.users", string="Verification Performed By"
    )
    verification_date = fields.Date(string="Verification Date")
    verification_method = fields.Selection(
        [
            ("secp", "SECP Portal"),
            ("doc_inspection", "Document Inspection"),
            ("third_party", "Third Party"),
        ],
        string="Verification Method",
    )
    verification_exception_ids = fields.One2many(
        "qaco.onboarding.verification.exception",
        "onboarding_id",
        string="Verification Exceptions",
    )

    @api.depends("signatory_ids")
    def _compute_signatory_count(self):
        for rec in self:
            rec.signatory_count = len(rec.signatory_ids)

    # Section 2: Compliance History
    financial_framework = fields.Selection(
        FINANCIAL_FRAMEWORK_SELECTION, string="Applicable Framework", required=True
    )
    financial_framework_other = fields.Char(string="Other Framework Details")
    annual_return_last_filed = fields.Date(string="Annual Return Last Filed")
    annual_return_overdue = fields.Boolean(string="Return Overdue", default=False)
    fbr_compliance_rating = fields.Selection(
        [("atl", "ATL"), ("btl", "BTL"), ("provisional", "Provisional")],
        string="FBR Compliance Rating",
    )
    tax_assessment_history = fields.Text(string="Tax Assessment / Litigation History")
    regulatory_inspection_notes = fields.Text(string="Regulatory Inspection Summary")
    regulatory_inspection_attachment = fields.Binary(string="Inspection Documents")

    # Section 3: Ownership & Governance
    shareholder_ids = fields.One2many(
        "qaco.onboarding.shareholder", "onboarding_id", string="Shareholding Pattern"
    )
    shareholding_total = fields.Float(
        string="Shareholding % Total", compute="_compute_shareholding_total", store=True
    )
    shareholding_difference_explanation = fields.Text(
        string="Shareholding difference explanation"
    )
    share_capital_movement_ids = fields.One2many(
        "qaco.onboarding.sharecapital.movement",
        "onboarding_id",
        string="Share Capital Movements",
    )

    # UBOs
    ubo_ids = fields.One2many(
        "qaco.onboarding.ubo", "onboarding_id", string="Ultimate Beneficial Owners"
    )
    ubo_identification_method = fields.Selection(
        [
            ("client_declaration", "Client declaration"),
            ("registry_filings", "Registry filings"),
            ("group_organogram", "Group organogram"),
            ("other", "Other"),
        ],
        string="UBO identification method",
    )
    ubo_section_complete = fields.Boolean(string="UBO section complete")

    # Group & consolidation
    group_status = fields.Selection(
        [
            ("standalone", "Standalone"),
            ("parent", "Parent"),
            ("subsidiary", "Subsidiary"),
            ("associate", "Associate"),
            ("joint_venture", "Joint Venture"),
        ],
        string="Group status",
    )
    group_component_ids = fields.One2many(
        "qaco.onboarding.group.component", "onboarding_id", string="Group Components"
    )
    consolidation_changes = fields.Text(string="Consolidation changes and impact")
    intercompany_expected = fields.Boolean(string="Intercompany transactions expected")
    intercompany_categories = fields.Char(string="Intercompany categories")

    # Governance
    board_member_ids = fields.One2many(
        "qaco.onboarding.board.member", "onboarding_id", string="Board & Key Personnel"
    )
    kmp_ids = fields.One2many(
        "qaco.onboarding.kmp", "onboarding_id", string="Key Management Personnel"
    )
    delegation_of_authority = fields.Text(
        string="Delegation of authority / signing limits"
    )
    internal_audit = fields.Boolean(string="Internal audit function present")
    internal_audit_head = fields.Char(string="Head of internal audit")
    internal_audit_scope = fields.Text(string="Internal audit scope (high-level)")

    # Related parties
    related_party_ids = fields.One2many(
        "qaco.onboarding.related.party",
        "onboarding_id",
        string="Related Parties Master List",
    )
    has_significant_related_parties = fields.Boolean(
        string="Significant related parties present"
    )
    related_parties_procedures = fields.Text(
        string="Planned completeness procedures for related parties"
    )

    # Validation & risk flags
    fit_proper_confirmed = fields.Boolean(string="Fit & Proper Checks Completed")
    fit_proper_document = fields.Binary(string="Fit & Proper Evidence")
    has_pep = fields.Boolean(
        string="Politically Exposed Person Identified",
        compute="_compute_pep_flag",
        store=True,
    )
    enhanced_due_diligence_required = fields.Boolean(
        string="Enhanced Due Diligence Required",
        compute="_compute_pep_flag",
        store=True,
    )
    enhanced_due_diligence_details = fields.Text(string="Enhanced Due Diligence Notes")
    enhanced_due_diligence_attachment = fields.Binary(
        string="Enhanced Due Diligence Documentation"
    )

    ownership_complex_ownership = fields.Boolean(
        string="Complex ownership / nominee shareholders"
    )
    ownership_frequent_director_changes = fields.Boolean(
        string="Frequent director changes / weak oversight"
    )
    ownership_significant_related_party_transactions = fields.Boolean(
        string="Significant related party transactions"
    )
    ownership_cross_border_group = fields.Boolean(
        string="Cross-border group structure / tax complexity"
    )
    ownership_dominant_owner_override_risk = fields.Boolean(
        string="Dominant owner/management override risk"
    )
    ownership_risk_rating = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        string="Ownership / governance risk rating",
    )
    ownership_risk_rationale = fields.Text(string="Ownership risk rationale")

    # Verification for ownership section
    ownership_verified_by = fields.Many2one("res.users", string="Ownership Verified By")
    ownership_verified_on = fields.Date(string="Ownership Verified On")
    ownership_verification_method = fields.Selection(
        [
            ("registry", "Registry filings"),
            ("minutes", "Minutes"),
            ("declaration", "Management declaration"),
            ("other", "Other"),
        ],
        string="Verification method",
    )

    # Section 4: Pre-Acceptance Risk
    management_integrity_rating = fields.Selection(
        MANAGEMENT_INTEGRITY_SELECTION,
        string="Management Integrity Rating",
        required=True,
    )
    management_integrity_comment = fields.Text(
        string="Management Integrity Justification", required=True
    )
    litigation_history = fields.Text(string="Litigation History")
    fraud_history = fields.Selection(
        [("no", "No"), ("yes", "Yes")],
        string="History of Fraud or Penalties",
        required=True,
        default="no",
    )
    fraud_explanation = fields.Text(string="Fraud or Penalty Details")
    aml_risk_rating = fields.Selection(
        AML_RATING,
        string="AML/CTF Risk Rating",
        compute="_compute_aml_risk_rating",
        store=True,
    )
    business_risk_profile = fields.Text(string="Business Risk Profile")
    risk_mitigation_plan = fields.Text(string="Risk Mitigation Plan")
    eqcr_required = fields.Boolean(
        string="EQCR Required", compute="_compute_eqcr_required", store=True
    )
    managing_partner_escalation = fields.Boolean(
        string="Managing Partner Escalation",
        compute="_compute_eqcr_required",
        store=True,
    )

    # Section 5: Independence & Ethics
    independence_threat_ids = fields.One2many(
        "qaco.onboarding.independence.threat",
        "onboarding_id",
        string="Independence Threat Checklist",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        readonly=True,
        default=lambda self: self.env.company.currency_id,
    )
    non_audit_services_confirmed = fields.Boolean(
        string="Non-Audit Services Evaluation Completed"
    )
    non_audit_services_attachment = fields.Binary(
        string="Non-Audit Services Supporting Document"
    )
    proposed_audit_fee = fields.Monetary(
        currency_field="currency_id", string="Proposed Audit Fee"
    )
    total_fee_income = fields.Monetary(
        currency_field="currency_id", string="Total Firm Fee Income"
    )
    fee_dependency_percent = fields.Float(
        string="Fee Dependency (%)", compute="_compute_fee_dependency", store=True
    )
    fee_dependency_flag = fields.Boolean(
        string="Fee Dependency Flag", compute="_compute_fee_dependency", store=True
    )
    independence_declaration_ids = fields.One2many(
        "qaco.onboarding.independence.declaration",
        "onboarding_id",
        string="Team Independence Declarations",
    )
    independence_status_feedback = fields.Text(
        string="Independence Declaration Status Summary",
        compute="_compute_independence_status",
    )

    # Section 6: Predecessor Auditor Communication
    predecessor_auditor_name = fields.Char(string="Predecessor Auditor Name")
    predecessor_contact = fields.Char(string="Predecessor Contact Details")
    predecessor_request_ids = fields.One2many(
        "qaco.onboarding.predecessor.request",
        "onboarding_id",
        string="Predecessor Clearance Requests",
    )
    predecessor_response_ids = fields.One2many(
        "qaco.onboarding.predecessor.response",
        "onboarding_id",
        string="Predecessor Responses",
    )
    predecessor_escalated = fields.Boolean(
        string="Predecessor Issues Escalated",
        help="Indicates if any predecessor issues have been escalated",
    )
    predecessor_locked = fields.Boolean(
        string="Predecessor Section Locked",
        help="Indicates if predecessor section is locked for editing",
    )
    pcl_requested = fields.Date(string="PCL Date Requested")
    pcl_received = fields.Date(string="PCL Date Received")
    pcl_document = fields.Binary(string="Professional Clearance Letter")
    pcl_document_name = fields.Char(string="PCL File Name")
    pcl_no_outstanding_fees = fields.Boolean(string="PCL confirms no outstanding fees")
    pcl_no_disputes = fields.Boolean(string="PCL confirms no disputes")
    pcl_no_ethics_issues = fields.Boolean(string="PCL raises no ethical issues")

    # Section 7: Final Authorization
    precondition_line_ids = fields.One2many(
        "qaco.onboarding.precondition.line",
        "onboarding_id",
        string="ISA 210 Preconditions",
    )
    # Document Vault relationship
    document_ids = fields.One2many(
        "qaco.onboarding.document", "onboarding_id", string="Document Vault"
    )
    document_folder_ids = fields.One2many(
        "qaco.onboarding.document.folder", "onboarding_id", string="Document Folders"
    )
    latest_decision_id = fields.Many2one(
        "qaco.onboarding.decision", string="Latest Decision"
    )

    # Convenience related fields for UI display (read-only)
    latest_decision_rationale = fields.Text(
        string="Latest Decision Rationale", related="latest_decision_id.decision_rationale", readonly=True
    )
    latest_decision_by = fields.Many2one(
        "res.users", string="Latest Decision By", related="latest_decision_id.decision_by", readonly=True
    )
    latest_decision_date = fields.Datetime(
        string="Latest Decision Date", related="latest_decision_id.decision_date", readonly=True
    )

    def _create_default_document_folders(self):
        """Create a copy of the template folder taxonomy for this onboarding."""
        Folder = self.env["qaco.onboarding.document.folder"]
        templates = Folder.search([("onboarding_id", "=", False)])
        created = {}
        roots = templates.filtered(lambda t: not t.parent_id)
        for rec in self:
            # Create root-level folders
            for tmpl in roots:
                new = Folder.create(
                    {
                        "onboarding_id": rec.id,
                        "name": tmpl.name,
                        "code": tmpl.code,
                        "status": "created",
                        "sequence": tmpl.sequence,
                        "description": tmpl.description,
                    }
                )
                created[tmpl.id] = new
            # Create child folders iteratively
            children = templates.filtered(lambda t: t.parent_id)
            pending = children
            while pending:
                for tmpl in list(pending):
                    parent_new = created.get(tmpl.parent_id.id)
                    if parent_new:
                        new = Folder.create(
                            {
                                "onboarding_id": rec.id,
                                "name": tmpl.name,
                                "code": tmpl.code,
                                "parent_id": parent_new.id,
                                "status": "created",
                                "sequence": tmpl.sequence,
                                "description": tmpl.description,
                            }
                        )
                        created[tmpl.id] = new
                        pending = pending - tmpl
                    else:
                        # Wait until parent is created
                        pass
        return True

    def get_folder_by_code(self, code):
        self.ensure_one()
        return self.document_folder_ids.filtered(lambda f: f.code == code)[:1]


    @api.constrains("state")
    def _check_company_required_documents_on_approval(self):
        """Enforce hard validations for company-type entities before partner approval."""
        company_types = set(["pic", "lsc", "msc", "ssc"])
        for rec in self:
            if (
                rec.state in ("partner_approved", "locked")
                and rec.entity_type in company_types
            ):
                # Use in-memory collection where possible to avoid extra DB roundtrips
                # Check for Memorandum & Articles / governing instrument and Incorporation Certificate
                names = " ".join((d.name or "").lower() for d in rec.document_ids)
                has_moa = "memorandum" in names or "moa" in names
                has_incorp = "incorporation" in names or "registration" in names
                if not has_moa:
                    raise ValidationError(
                        _(
                            "Memorandum & Articles (MoA/AoA) must be uploaded for company-type entities before partner approval."
                        )
                    )
                if not has_incorp:
                    raise ValidationError(
                        _(
                            "Incorporation / Registration Certificate must be uploaded for company-type entities before partner approval."
                        )
                    )
            # Ensure signatory authority evidence exists before final authorization (in-memory check)
            signatories_missing = rec.signatory_ids.filtered(
                lambda s: not s.authority_evidence_id
            )
            if signatories_missing:
                raise ValidationError(
                    _(
                        "All authorised signatories must have authority evidence attached before partner approval."
                    )
                )
            # Ensure evidence documents are received/accepted
            for s in rec.signatory_ids:
                if s.authority_evidence_id and s.authority_evidence_id.state not in (
                    "received",
                    "reviewed",
                ):
                    raise ValidationError(
                        _(
                            "Authority evidence for signatory %s must be received/verified before partner approval."
                        )
                        % s.name
                    )
            # Ensure there are no overdue statutory filings or, if present, prevent partner approval until resolved
            overdue = rec.filing_ids.filtered(
                lambda f: f.statutory_due_date
                and f.statutory_due_date < fields.Date.context_today(rec)
                and f.status != "filed"
            )
            if overdue:
                names = ", ".join(overdue.mapped("filing_name"))
                raise ValidationError(
                    _(
                        "Overdue filings detected (%s). Resolve or obtain partner acknowledgement before partner approval."
                    )
                    % names
                )
            # Ensure open investigations have financial reporting impact documented
            open_investigations = rec.dispute_ids.filtered(
                lambda d: d.status in ("notice", "appeal", "court")
            )
            if open_investigations and not rec.financial_reporting_impact:
                raise ValidationError(
                    _(
                        "Open investigation/notice exists; document the financial reporting impact before partner approval."
                    )
                )


    engagement_summary = fields.Text(
        string="Engagement Summary", compute="_compute_engagement_summary", store=True
    )
    engagement_decision = fields.Selection(
        ENGAGEMENT_DECISION_SELECTION, string="Engagement Decision"
    )
    engagement_justification = fields.Text(string="Decision Justification")
    engagement_partner_id = fields.Many2one(
        "res.users", string="Engagement Partner", index=True
    )
    engagement_partner_signature = fields.Binary(
        string="Engagement Partner Digital Signature"
    )
    eqcr_partner_id = fields.Many2one("res.users", string="EQCR Partner", index=True)
    eqcr_partner_signature = fields.Binary(string="EQCR Partner Signature")
    managing_partner_id = fields.Many2one(
        "res.users", string="Managing Partner", index=True
    )
    managing_partner_signature = fields.Binary(string="Managing Partner Signature")

    # Final Authorization attestations & flags
    team_competence_confirmed = fields.Boolean(string="Team competence confirmed")
    resources_timeline_confirmed = fields.Boolean(
        string="Resources & timeline confirmed"
    )
    specialists_required = fields.Boolean(string="Specialists required")
    specialists_notes = fields.Text(string="Specialists notes")
    latest_authorization_id = fields.Many2one(
        "qaco.onboarding.final.authorization", string="Latest Authorization"
    )

    # compute method removed

    def action_open_attach_wizard_with_templates(self, template_ids):
        """Return an action to open the Attach Templates wizard prefilled with selected templates.

        This method is intended for JS to call with selected template ids and return an
        act_window action containing default template_ids and onboarding_id in the context.
        """
        self.ensure_one()
        action = self.env.ref(
            "qaco_client_onboarding.action_attach_templates_wizard",
            raise_if_not_found=False,
        )
        ctx = {}
        if action and getattr(action, "id", False):
            action = action.read()[0]
            ctx = dict(action.get("context") or {})
            ctx.update(
                {
                    "default_template_ids": [(6, 0, template_ids)],
                    "default_onboarding_id": self.id,
                    "onboarding_id": self.id,
                }
            )
            action["context"] = ctx
            return action
        else:
            # Fallback: construct a minimal act_window action that opens the transient wizard form
            return {
                "type": "ir.actions.act_window",
                "name": "Attach Templates",
                "res_model": "qaco.onboarding.attach.templates.wizard",
                "view_mode": "form",
                "target": "new",
                "context": {
                    "default_template_ids": [(6, 0, template_ids)],
                    "default_onboarding_id": self.id,
                    "onboarding_id": self.id,
                },
            }

    def action_open_template_library(self):
        """Open the central Template Library (safe, defensive ref).

        Returns an `act_window` action dict when the xmlid exists, or constructs
        a minimal action as a fallback so the button never fails during upgrades.
        """
        self.ensure_one()
        action = self.env.ref(
            "qaco_client_onboarding.action_template_library", raise_if_not_found=False
        )
        if action and getattr(action, "id", False):
            return action.read()[0]
        return {
            "type": "ir.actions.act_window",
            "name": "Template Library",
            "res_model": "qaco.onboarding.template.document",
            "view_mode": "tree,form",
        }

    def action_open_attach_wizard(self):
        """Open the attach templates wizard with no preselected templates as a fallback."""
        self.ensure_one()
        action = self.env.ref(
            "qaco_client_onboarding.action_attach_templates_wizard",
            raise_if_not_found=False,
        )
        if action and getattr(action, "id", False):
            a = action.read()[0]
            ctx = dict(a.get("context") or {})
            ctx.update({"default_onboarding_id": self.id, "onboarding_id": self.id})
            a["context"] = ctx
            return a
        return {
            "type": "ir.actions.act_window",
            "name": "Attach Templates",
            "res_model": "qaco.onboarding.attach.templates.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_onboarding_id": self.id, "onboarding_id": self.id},
        }

    def upload_and_attach(self, filename, file_b64):
        """Upload a binary file and attach it to this onboarding as an Attached Template.

        Called via RPC with args: ([onboarding_id], filename, file_b64)
        """
        self.ensure_one()
        Attached = self.env["qaco.onboarding.attached.template"]
        vals = {
            "onboarding_id": self.id,
            "attached_filename": filename,
            "attached_file": file_b64,
        }
        Attached.create([vals])
        self.message_post(
            body=_("Template %s uploaded and attached by %s")
            % (filename, self.env.user.name)
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Uploaded"),
                "message": _("Template uploaded and attached."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_attach_selected(self):
        """Server handler for the "Attach selected" button.

        Returns the same attach wizard action but without any preselected templates.
        This ensures the view will parse (button requires a name) and provides a
        graceful server-side fallback if JS is not available.
        """
        self.ensure_one()
        return self.action_open_attach_wizard_with_templates([])

    document_ids = fields.One2many(
        "qaco.onboarding.document", "onboarding_id", string="Document Vault"
    )
    checklist_line_ids = fields.One2many(
        "qaco.onboarding.checklist.line",
        "onboarding_id",
        string="Engagement Partner Decision",
    )
    audit_trail_ids = fields.One2many(
        "qaco.onboarding.audit.trail",
        "onboarding_id",
        string="Audit Trail",
        readonly=True,
    )

    @api.depends("client_id")
    def _compute_name(self):
        for record in self:
            record.name = f"Onboarding - {record.client_id.name or 'New Client'}"

    @api.constrains("ntn")
    def _check_ntn_format(self):
        pattern = r"^\d{7}-\d$"
        for record in self.filtered("ntn"):
            if not re.match(pattern, record.ntn):
                raise ValidationError(_("NTN must follow the format NNNNNNN-N."))

    @api.constrains("strn")
    def _check_strn(self):
        for record in self.filtered("strn"):
            if not re.match(r"^[0-9A-Za-z-]+$", record.strn):
                raise ValidationError(
                    _("STRN must only contain alphanumeric characters and hyphens.")
                )

    @api.constrains("entity_type", "other_entity_description")
    def _check_entity_type_other(self):
        for record in self:
            if record.entity_type == "other" and not record.other_entity_description:
                raise ValidationError(
                    _("When selecting Other entity type, specify the classification.")
                )

    @api.constrains("financial_framework", "financial_framework_other")
    def _check_financial_framework_other(self):
        for record in self:
            if (
                record.financial_framework == "other_framework"
                and not record.financial_framework_other
            ):
                raise ValidationError(
                    _("Provide details for the other financial reporting framework.")
                )

    @api.constrains("fraud_history", "fraud_explanation")
    def _require_fraud_explanation(self):
        for record in self:
            if record.fraud_history == "yes" and not record.fraud_explanation:
                raise ValidationError(
                    _("Provide a detailed explanation when fraud or penalties exist.")
                )

    @api.constrains("eqcr_required", "risk_mitigation_plan")
    def _require_risk_mitigation(self):
        for record in self:
            if record.eqcr_required and not record.risk_mitigation_plan:
                raise ValidationError(
                    _("EQCR triggers require a risk mitigation plan to be documented.")
                )

    @api.depends(
        "section1_status",
        "section2_status",
        "section3_status",
        "section4_status",
        "section5_status",
        "section6_status",
        "section7_status",
    )
    def _compute_overall_status(self):
        for record in self:
            statuses = [
                getattr(record, f"section{i}_status") or "red" for i in range(1, 8)
            ]
            if all(status == "green" for status in statuses):
                record.overall_status = "green"
            elif any(status == "amber" for status in statuses):
                record.overall_status = "amber"
            else:
                record.overall_status = "red"

    @api.depends(
        "section1_status",
        "section2_status",
        "section3_status",
        "section4_status",
        "section5_status",
        "section6_status",
        "section7_status",
    )
    def _compute_progress(self):
        for record in self:
            statuses = [
                getattr(record, f"section{i}_status") or "red" for i in range(1, 8)
            ]
            weights = {"red": 0, "amber": 0.5, "green": 1}
            if any(status not in weights for status in statuses):
                record.progress_percentage = 0.0
            else:
                record.progress_percentage = (
                    sum(weights[status] for status in statuses) / 7.0 * 100
                )

    @api.depends(
        "entity_type",
        "primary_regulator",
        "financial_framework",
        "management_integrity_rating",
        "aml_risk_rating",
        "overall_status",
        "engagement_decision",
    )
    def _compute_selection_labels(self):
        for record in self:
            record.entity_type_label = dict(ENTITY_SELECTION).get(
                record.entity_type, ""
            )
            record.primary_regulator_label = dict(PRIMARY_REGULATOR_SELECTION).get(
                record.primary_regulator, ""
            )
            record.financial_framework_label = dict(FINANCIAL_FRAMEWORK_SELECTION).get(
                record.financial_framework, ""
            )
            record.management_integrity_label = dict(
                MANAGEMENT_INTEGRITY_SELECTION
            ).get(record.management_integrity_rating, "")
            record.aml_risk_label = dict(AML_RATING).get(record.aml_risk_rating, "")
            record.overall_status_label = dict(SECTION_STATUS).get(
                record.overall_status, ""
            )
            record.engagement_decision_label = dict(ENGAGEMENT_DECISION_SELECTION).get(
                record.engagement_decision, ""
            )

    @api.depends("audit_standard_ids")
    def _compute_audit_standard_overview(self):
        for record in self:
            if not record.audit_standard_ids:
                record.audit_standard_overview = _("<p>No standards selected.</p>")
                continue
            lines = []
            for standard in record.audit_standard_ids:
                regulator_label = dict(
                    standard._fields["regulator_reference"].selection
                ).get(standard.regulator_reference, "")
                parts = [f"<strong>{standard.code}</strong> – {standard.title}"]
                if regulator_label:
                    parts.append(f"({regulator_label})")
                applicability = standard.applicability or ""
                lines.append(f"<p>{' '.join(parts)}<br/>{applicability}</p>")
            record.audit_standard_overview = "".join(lines)

    @api.depends(
        "aml_risk_rating",
        "eqcr_required",
        "management_integrity_rating",
        "fee_dependency_flag",
    )
    def _compute_high_risk(self):
        for record in self:
            record.high_risk_onboarding = bool(
                record.aml_risk_rating == "high"
                or record.eqcr_required
                or record.management_integrity_rating == "low"
                or record.fee_dependency_flag
            )

    @api.depends(
        "regulator_checklist_line_ids.completed",
        "regulator_checklist_line_ids.mandatory",
        "regulator_checklist_line_ids.standard_ids",
    )
    def _compute_regulator_checklist_summary(self):
        for record in self:
            lines = record.regulator_checklist_line_ids
            mandatory = lines.filtered("mandatory")
            completed_mandatory = mandatory.filtered("completed")
            total_mandatory = len(mandatory)
            percent = 0.0
            if total_mandatory:
                percent = round(len(completed_mandatory) / total_mandatory * 100.0, 2)
            record.regulator_checklist_completion = percent

            summary_html = []
            for area_key, area_label in ONBOARDING_AREAS:
                area_lines = lines.filtered(
                    lambda line: line.onboarding_area == area_key and line.mandatory
                )
                if not area_lines:
                    continue
                area_completed = area_lines.filtered("completed")
                codes = set()
                for line in area_lines:
                    codes.update(line.standard_ids.mapped("code"))
                codes_text = (
                    ", ".join(sorted(codes)) if codes else _("No standards linked")
                )
                summary_html.append(
                    _(
                        "<p><strong>%s</strong>: %s/%s mandatory completed | Standards: %s</p>"
                    )
                    % (
                        area_label,
                        len(area_completed),
                        len(area_lines),
                        codes_text,
                    )
                )
            if not summary_html:
                summary_html = [_("<p>No checklist summary available.</p>")]
            record.regulator_checklist_overview = "".join(summary_html)

    @api.depends(
        "legal_name",
        "principal_business_address",
        "business_registration_number",
        "industry_id",
        "primary_regulator",
    )
    def _compute_section_status(self):
        for record in self:
            record.section1_status = (
                "green"
                if all(
                    [
                        record.legal_name,
                        record.principal_business_address,
                        record.business_registration_number,
                        record.industry_id,
                        record.primary_regulator,
                    ]
                )
                else "red"
            )
            record.section2_status = "green" if record.financial_framework else "red"
            record.section3_status = (
                "green" if record.shareholder_ids and record.board_member_ids else "red"
            )
            record.section4_status = (
                "green"
                if record.management_integrity_rating
                and record.aml_risk_rating in ["low", "medium"]
                else ("amber" if record.management_integrity_rating else "red")
            )
            record.section5_status = (
                "green"
                if record.independence_threat_ids
                and record.independence_declaration_ids
                else "red"
            )
            record.section6_status = (
                "green"
                if record.pcl_document
                and record.pcl_no_outstanding_fees
                and record.pcl_no_disputes
                and record.pcl_no_ethics_issues
                else "red"
            )
            record.section7_status = (
                "green"
                if record.engagement_decision == "accept"
                and record.engagement_partner_signature
                else "red"
            )

    @api.depends("shareholder_ids.percentage")
    def _compute_shareholding_total(self):
        for rec in self:
            rec.shareholding_total = sum(
                sh.percentage or 0.0 for sh in rec.shareholder_ids
            )

    @api.constrains("shareholder_ids", "shareholding_difference_explanation")
    def _check_shareholding_total(self):
        """Shareholding % total must equal 100% unless an explanation is provided."""
        for rec in self:
            total = sum(sh.percentage or 0.0 for sh in rec.shareholder_ids)
            # allow small rounding tolerance
            if (
                rec.shareholder_ids
                and abs(total - 100.0) > 0.5
                and not rec.shareholding_difference_explanation
            ):
                raise ValidationError(
                    _(
                        "Shareholding percentages must sum to approximately 100%%, or provide an explanation in the Shareholding difference explanation field."
                    )
                )

    @api.constrains("ubo_section_complete")
    def _check_ubo_basis(self):
        for rec in self:
            if rec.ubo_section_complete and rec.ubo_ids:
                missing = rec.ubo_ids.filtered(lambda u: not u.basis_of_control)
                if missing:
                    raise ValidationError(
                        _(
                            "UBO section marked complete but some UBOs are missing a basis of control."
                        )
                    )

    @api.constrains("group_status")
    def _check_group_components(self):
        for rec in self:
            if (
                rec.group_status
                and rec.group_status != "standalone"
                and not rec.group_component_ids
            ):
                raise ValidationError(
                    _(
                        "Group status indicates a group entity; at least one group component must be recorded."
                    )
                )

    @api.constrains("has_significant_related_parties")
    def _check_related_parties_presence(self):
        for rec in self:
            if rec.has_significant_related_parties and (
                not rec.related_party_ids or not rec.related_parties_procedures
            ):
                raise ValidationError(
                    _(
                        "Significant related parties flagged; provide related parties master list and planned completeness procedures."
                    )
                )

    def _compute_pep_flag(self):
        for record in self:
            has_pep = bool(record.board_member_ids.filtered("is_pep"))
            record.has_pep = has_pep
            record.enhanced_due_diligence_required = has_pep
            if has_pep:
                record.section3_status = "amber"

    @api.depends("management_integrity_rating", "aml_risk_rating")
    def _compute_eqcr_required(self):
        for record in self:
            low_integrity = record.management_integrity_rating == "low"
            high_aml = record.aml_risk_rating == "high"
            record.eqcr_required = low_integrity or high_aml
            record.managing_partner_escalation = record.eqcr_required
            if record.eqcr_required:
                record.section4_status = "amber"

    @api.depends("industry_id.risk_category", "primary_regulator", "has_pep")
    def _compute_aml_risk_rating(self):
        for record in self:
            risk_score = 0
            if record.industry_id and record.industry_id.risk_category == "high":
                risk_score += 2
            if record.primary_regulator in ["fbr", "secp"]:
                risk_score += 1
            if record.has_pep:
                risk_score += 2
            rating = "low"
            if risk_score >= 3:
                rating = "high"
            elif risk_score == 2:
                rating = "medium"
            record.aml_risk_rating = rating

    @api.depends("proposed_audit_fee", "total_fee_income", "entity_type")
    def _compute_fee_dependency(self):
        for record in self:
            threshold = 15 if record.entity_type in ["pic", "lsc"] else 20
            if record.proposed_audit_fee and record.total_fee_income:
                record.fee_dependency_percent = round(
                    (record.proposed_audit_fee / record.total_fee_income) * 100.0, 2
                )
            else:
                record.fee_dependency_percent = 0.0
            record.fee_dependency_flag = record.fee_dependency_percent > threshold
            if record.fee_dependency_flag:
                record.section5_status = "amber"

    @api.depends("independence_declaration_ids.status")
    def _compute_independence_status(self):
        for record in self:
            if not record.independence_declaration_ids:
                record.independence_status_feedback = _(
                    "Awaiting declarations from the engagement team."
                )
                continue
            completed = record.independence_declaration_ids.filtered(
                lambda line: line.status == "approved"
            )
            percent = 0
            if record.independence_declaration_ids:
                percent = (
                    len(completed) / len(record.independence_declaration_ids) * 100
                )
            record.independence_status_feedback = (
                _("%d%% of team members completed declarations.") % percent
            )

    @api.depends("client_id", "audit_id", "risk_mitigation_plan", "section4_status")
    def _compute_engagement_summary(self):
        for record in self:
            summary = [
                _("Client: %s") % (record.client_id.name or "—"),
                _("Risk: %s") % (record.aml_risk_label or "—"),
                _("EQCR Required: %s") % ("Yes" if record.eqcr_required else "No"),
            ]
            if record.engagement_decision:
                summary.append(
                    _("Decision: %s") % (record.engagement_decision_label or "—")
                )
            record.engagement_summary = "\n".join(summary)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals = self._with_minimum_defaults(vals)
        onboardings = super().create(vals_list)
        for onboarding in onboardings:
            onboarding._populate_checklist_from_templates()
            onboarding._populate_preconditions()
            onboarding._populate_regulator_checklist()
            # populate regulatory required document rows from regulatory template category
            try:
                onboarding.populate_required_documents_from_templates()
            except Exception:
                # avoid failing create if required documents cannot be populated
                _logger.exception(
                    "Failed to populate regulatory required documents for onboarding %s",
                    onboarding.id,
                )
            # populate ownership required documents (1.3)
            try:
                onboarding.populate_ownership_required_documents_from_templates()
            except Exception:
                _logger.exception(
                    "Failed to populate ownership required documents for onboarding %s",
                    onboarding.id,
                )
            # populate the template library with active templates if empty
            try:
                onboarding.populate_template_library()
            except Exception:
                # avoid failing create if templates cannot be populated
                _logger.exception(
                    "Failed to populate template library for onboarding %s",
                    onboarding.id,
                )
            # create default document folders (if not created)
            try:
                onboarding._create_default_document_folders()
            except Exception:
                _logger.exception(
                    "Failed to create default document folders for onboarding %s",
                    onboarding.id,
                )
                pass
            onboarding._log_action("Created onboarding record")
        return onboardings

    def _with_minimum_defaults(self, vals):
        """Ensure required gateway fields are populated when launched from audit smart button."""
        # Only apply when creating a single record via dict input.
        if isinstance(vals, dict):
            audit = None
            if vals.get("audit_id"):
                audit = self.env["qaco.audit"].browse(vals["audit_id"])
            partner = audit.client_id if audit else None

            vals.setdefault("entity_type", "pic")
            if vals.get("entity_type") == "other":
                vals.setdefault("other_entity_description", _("Pending classification"))
            vals.setdefault(
                "legal_name", partner.name if partner else _("Pending Legal Name")
            )
            vals.setdefault(
                "principal_business_address",
                (partner.contact_address if partner else None) or _("Pending Address"),
            )
            vals.setdefault(
                "business_registration_number",
                vals.get("business_registration_number") or _("TBD"),
            )
            vals.setdefault("primary_regulator", "secp")
            vals.setdefault("financial_framework", "ifrs")
            vals.setdefault("management_integrity_rating", "medium")
            vals.setdefault(
                "management_integrity_comment",
                vals.get("management_integrity_comment") or _("Pending assessment"),
            )
        return vals

    def write(self, vals):
        res = super().write(vals)
        # Index specific uploads into the Document Vault on change.
        binary_map = {
            "org_chart_attachment": "Organizational Chart",
            "regulatory_inspection_attachment": "Regulatory Inspection Document",
            "pcl_document": "Professional Clearance Letter (PCL)",
            "fit_proper_document": "Fit & Proper Evidence",
            "enhanced_due_diligence_attachment": "Enhanced Due Diligence Document",
        }
        for rec in self:
            for field, label in binary_map.items():
                if field in vals and vals.get(field):
                    try:
                        self.env["qaco.onboarding.document"].create(
                            {
                                "onboarding_id": rec.id,
                                "name": label,
                                "doc_type": "legal",
                                "file": vals.get(field),
                                "file_name": f"{label}.pdf",
                                "state": "received",
                            }
                        )
                    except Exception:
                        _logger.exception(
                            'Failed to index binary field "%s" for onboarding %s',
                            field,
                            rec.id,
                        )
        changed_fields = ", ".join(map(str, vals.keys())) if vals else ""
        self._log_action("Updated onboarding", notes=changed_fields)
        return res

    def _populate_checklist_from_templates(self):
        if not self:
            return
        template_obj = self.env["qaco.onboarding.checklist.template"]
        templates = template_obj.search([])
        if not templates:
            return
        lines = []
        for record in self:
            for template in templates:
                lines.append(
                    {
                        "onboarding_id": record.id,
                        "template_id": template.id,
                        "question": template.question,
                        "category": template.category,
                        "critical": template.critical,
                    }
                )
        self.env["qaco.onboarding.checklist.line"].create(lines)

    def _populate_preconditions(self):
        if not self:
            return
        template_obj = self.env["qaco.onboarding.precondition.template"]
        templates = template_obj.search([])
        if not templates:
            return
        lines = []
        for record in self:
            for template in templates:
                lines.append(
                    {
                        "onboarding_id": record.id,
                        "template_id": template.id,
                        "description": template.description,
                    }
                )
        self.env["qaco.onboarding.precondition.line"].create(lines)

    def _populate_regulator_checklist(self):
        if not self:
            return
        template_obj = self.env["audit.onboarding.checklist.template"]
        templates = template_obj.search([])
        if not templates:
            return
        lines = []
        for record in self:
            if record.regulator_checklist_line_ids:
                continue
            for template in templates:
                lines.append(
                    {
                        "onboarding_id": record.id,
                        "template_id": template.id,
                        "code": template.code,
                        "name": template.name,
                        "onboarding_area": template.onboarding_area,
                        "standard_ids": [(6, 0, template.standard_ids.ids)],
                        "mandatory": template.mandatory,
                        "sequence": template.sequence,
                        "notes": template.guidance,
                    }
                )
        self.env["audit.onboarding.checklist"].create(lines)

    def _log_action(
        self,
        action,
        notes=None,
        action_type="activity",
        is_override=False,
        resolution=None,
        related_model=None,
        related_res_id=None,
        user_id=None,
    ):
        """Create a structured audit trail entry for onboarding activity.

        Parameters:
        - action: short action label
        - notes: free-text notes
        - action_type: one of 'activity','override','system','user'
        - is_override: mark if this entry documents an override
        - resolution: optional resolution or follow-up text
        - related_model/related_res_id: optional link to related model record
        - user_id: optional user id to attribute (defaults to current user)
        """
        trail = self.env["qaco.onboarding.audit.trail"]
        for record in self:
            vals = {
                "onboarding_id": record.id,
                "action": action,
                "notes": notes or "",
                "action_type": action_type,
                "is_override": bool(is_override),
                "resolution": resolution or False,
                "related_model": related_model or False,
                "related_res_id": related_res_id or False,
                "user_id": user_id or self.env.uid,
            }
            try:
                trail.create(vals)
            except Exception:
                _logger.exception(
                    "Failed to create audit trail for onboarding %s action %s",
                    record.id,
                    action,
                )

    def _validate_mandatory_checklist_completion(self):
        for record in self:
            if not record.regulator_checklist_line_ids:
                record._populate_regulator_checklist()
            if not record.regulator_checklist_line_ids:
                raise ValidationError(
                    _(
                        "Mandatory onboarding checklist items are missing for this record. Please reload or contact an administrator."
                    )
                )
            pending = record.regulator_checklist_line_ids.filtered(
                lambda line: line.mandatory and not line.completed
            )
            if pending:
                pending_names = ", ".join(pending.mapped("name"))
                raise ValidationError(
                    _(
                        "All mandatory onboarding checklist items must be completed before final authorization. Pending: %s"
                    )
                    % pending_names
                )

    def action_submit_review(self):
        for record in self:
            if record.state != "draft":
                continue
            record.write({"state": "under_review"})
            record._log_action("Submitted for review")

    def action_partner_approve(self):
        for record in self:
            if record.state != "under_review":
                raise ValidationError(
                    _("Submit the onboarding for review before partner approval.")
                )
            record._validate_mandatory_checklist_completion()
            # Independence & Ethics compliance check (1.5)
            record.action_check_independence_before_approval()
            # Predecessor clearance check (1.6)
            record.action_check_predecessor_before_approval()
            if record.high_risk_onboarding and not record.engagement_partner_id:
                raise ValidationError(
                    _(
                        "High-risk onboardings require an Engagement Partner before approval."
                    )
                )
            record.write({"state": "partner_approved"})
            record._log_action(
                "Partner approved onboarding",
                notes=_("High risk: %s")
                % ("Yes" if record.high_risk_onboarding else "No"),
            )

    def action_generate_acceptance_report(self):
        report = self.env.ref(
            "qaco_client_onboarding.report_client_onboarding_pdf",
            raise_if_not_found=False,
        )
        if report:
            return report.report_action(self)
        return {"type": "ir.actions.act_window_close"}

    def _check_final_authorization_preconditions(self):
        """Run the set of system controls that must be complete before final authorization.

        Raises ValidationError with a clear message listing blocking items.
        """
        for rec in self:
            errors = []
            # 1. Profile complete: legal_name, principal_business_address, engagement_type/reporting_period
            if not rec.legal_name or not rec.principal_business_address:
                errors.append(
                    _("Client & engagement profile incomplete (legal name or address).")
                )
            # reporting period / engagement type
            if not rec.reporting_period or not rec.engagement_type:
                errors.append(_("Engagement scope, type or reporting period missing."))
            # 2. AML / Fit & Proper
            if not rec.fit_proper_confirmed:
                errors.append(_("Fit & proper / AML checks are not completed."))
            # 3. Independence status must be compliant
            if (
                hasattr(rec, "independence_status")
                and rec.independence_status != "compliant"
            ):
                errors.append(_("Independence & ethics status is not compliant."))
            # 4. Predecessor check
            try:
                rec.action_check_predecessor_before_approval()
            except ValidationError as e:
                errors.append(str(e))
            # 5. Fee and collection risk - ensure proposed fee present and no PCL outstanding fees flagged
            if not rec.proposed_audit_fee:
                errors.append(_("Proposed audit fee must be recorded."))
            if (
                hasattr(rec, "pcl_no_outstanding_fees")
                and rec.pcl_no_outstanding_fees is False
            ):
                errors.append(
                    _(
                        "Predecessor clearance indicates outstanding fees; resolve before authorization."
                    )
                )
            # 6. Resources & competence - check attestations or presence of partner assignment
            if not rec.team_competence_confirmed:
                errors.append(
                    _("Team competence has not been confirmed (capacity & competence).")
                )
            if not rec.engagement_partner_id:
                errors.append(
                    _("Engagement Partner assignment is required before authorization.")
                )
            # 7. High risk flags resolved or declined recorded
            if (
                rec.high_risk_onboarding
                and rec.engagement_decision != "reject"
                and rec.overall_status != "green"
            ):
                errors.append(
                    _(
                        "High-risk onboarding must be escalated and resolved before authorization."
                    )
                )
            if errors:
                raise ValidationError("\n".join(errors))
        return True

    def action_generate_onboarding_summary_pack(self):
        """Generate a summary pack: merge existing memos and key reports into one bundle.

        Uses the predecessor pack merger approach to merge PDF memos and the client onboarding certificate if present.
        """
        self.ensure_one()
        # Collect candidate attachments: ethics memo, predecessor memo, risk memo, engagement letter (if binary stored)
        candidates = []
        # search attachments linked to this onboarding
        other_attachments = self.env["ir.attachment"].search(
            [("res_model", "=", "qaco.client.onboarding"), ("res_id", "=", self.id)]
        )
        for att in other_attachments:
            if att.mimetype == "application/pdf":
                candidates.append(att)
        # attempt to render the acceptance report/certificate
        report = self.env.ref(
            "qaco_client_onboarding.report_client_onboarding_pdf",
            raise_if_not_found=False,
        )
        try:
            if report:
                pdf = report._render_qweb_pdf([self.id])[0]
            else:
                pdf = None
        except Exception:
            pdf = None
        # Use PdfMerger from predecessor module if available
        import base64
        import io

        from .onboarding_predecessor import PdfMerger

        merger = None
        merged_bytes = None
        if PdfMerger:
            merger = PdfMerger()
            if pdf:
                merger.append(io.BytesIO(pdf))
            for att in candidates:
                try:
                    data = base64.b64decode(att.datas or att.db_datas or "")
                    merger.append(io.BytesIO(data))
                except Exception:
                    _logger.exception("Failed to append %s to summary pack", att.name)
            out = io.BytesIO()
            try:
                merger.write(out)
                merged_bytes = out.getvalue()
            finally:
                try:
                    merger.close()
                except Exception:
                    pass
        else:
            _logger.warning(
                "No PDF merger available; returning base acceptance report if present."
            )
            merged_bytes = pdf
        if merged_bytes:
            att = self.env["ir.attachment"].create(
                {
                    "name": f"onboarding_summary_pack_{self.id}.pdf",
                    "type": "binary",
                    "datas": base64.b64encode(merged_bytes).decode("ascii"),
                    "res_model": "qaco.client.onboarding",
                    "res_id": self.id,
                    "mimetype": "application/pdf",
                }
            )
            try:
                folder = self.get_folder_by_code("08_Final_Authorization")
                if folder:
                    self.env["qaco.onboarding.document"].create(
                        {
                            "onboarding_id": self.id,
                            "name": att.name,
                            "file": att.datas,
                            "file_name": att.name,
                            "state": "final",
                            "folder_id": folder.id,
                        }
                    )
            except Exception:
                _logger.exception(
                    "Failed to index onboarding summary pack into folder for onboarding %s",
                    self.id,
                )
            return att
        return False

    def action_generate_independence_memo(self):
        """Render the independence/ethics report and index it into the Independence folder."""
        self.ensure_one()
        report = self.env.ref(
            "qaco_client_onboarding.report_ethics_independence",
            raise_if_not_found=False,
        )
        if not report:
            _logger.warning("Ethics independence report not found")
            return False
        try:
            pdf = report._render_qweb_pdf([self.id])[0]
            att = self.env["ir.attachment"].create(
                {
                    "name": f"independence_memo_{self.id}.pdf",
                    "type": "binary",
                    "datas": base64.b64encode(pdf).decode("ascii"),
                    "res_model": "qaco.client.onboarding",
                    "res_id": self.id,
                    "mimetype": "application/pdf",
                }
            )
            folder = self.get_folder_by_code("03_Independence")
            if folder:
                self.env["qaco.onboarding.document"].create(
                    {
                        "onboarding_id": self.id,
                        "name": att.name,
                        "file": att.datas,
                        "file_name": att.name,
                        "state": "final",
                        "folder_id": folder.id,
                    }
                )
            return att
        except Exception:
            _logger.exception(
                "Failed to generate independence memo for onboarding %s", self.id
            )
            return False

    def action_lock_onboarding(self):
        for record in self:
            record._validate_mandatory_checklist_completion()
            if record.overall_status != "green":
                raise ValidationError(
                    _("Finalize all sections before locking the onboarding.")
                )
            if record.state != "partner_approved":
                raise ValidationError(
                    _("Partner approval is required before locking the onboarding.")
                )
            if record.high_risk_onboarding and record.state != "partner_approved":
                raise ValidationError(
                    _("High-risk onboarding must be partner approved before locking.")
                )
            record.write({"state": "locked"})
            record._log_action("Locked onboarding for final authorization")

    def action_attach_legal_identity_templates(self):
        """Attach commonly-required legal identity templates (KYC / KYB) to this onboarding record.

        The method searches the template library for documents with names matching KYC or KYB and
        creates `qaco.onboarding.attached.template` records for any templates not already attached.
        """
        Template = self.env["qaco.onboarding.template.document"]
        Attached = self.env["qaco.onboarding.attached.template"]
        # Search for commonly used legal identity templates (expand if needed)
        domain = ["|", ("name", "ilike", "KYC"), ("name", "ilike", "KYB")]
        templates = Template.search(domain)
        if not templates:
            return True
        for record in self:
            existing_ids = record.attached_template_ids.mapped("template_id.id")
            new_templates = templates.filtered(lambda t: t.id not in existing_ids)
            if not new_templates:
                continue
            vals = []
            for t in new_templates:
                vals.append(
                    {
                        "onboarding_id": record.id,
                        "template_id": t.id,
                        "attached_file": t.template_file,
                        "attached_filename": t.template_filename,
                        "attached_by": self.env.uid,
                    }
                )
            if vals:
                Attached.create(vals)
                record._log_action(
                    "Attached legal identity templates",
                    notes=", ".join(new_templates.mapped("name")),
                )
        return True


class OnboardingBranchLocation(models.Model):
    _name = "qaco.onboarding.branch.location"
    _description = "Onboarding Branch / Office Location"

    onboarding_id = fields.Many2one(
        "qaco.client.onboarding", required=True, ondelete="cascade", index=True
    )
    name = fields.Char(string="Location", required=True)
    address = fields.Char(string="Address", required=True)
    function = fields.Char(
        string="Function / Role", help="e.g., Sales Office, HQ, Warehouse"
    )
    headcount = fields.Integer(string="Headcount")
    warehouse_locations = fields.Char(string="Warehouse Locations")
    key_systems = fields.Char(string="Key Systems (ERP / POS / Payroll / Inventory)")
    city_id = fields.Many2one(
        "qaco.onboarding.city",
        string="City",
        help="Select a city to automatically update the province and country fields.",
        ondelete="restrict",
    )
    province_id = fields.Many2one(
        "res.country.state",
        string="Province / Territory",
        domain="[('country_id','=', country_id)]",
    )
    country_id = fields.Many2one("res.country", string="Country")

    @api.onchange("city_id")
    def _onchange_city_id(self):
        for location in self:
            if location.city_id and location.city_id.state_id:
                state = location.city_id.state_id
                location.province_id = state
                location.country_id = state.country_id
            else:
                location.province_id = False
                location.country_id = False

    @api.onchange("province_id")
    def _onchange_province_id(self):
        for location in self:
            if location.province_id:
                location.country_id = location.province_id.country_id
                if (
                    location.city_id
                    and location.city_id.state_id != location.province_id
                ):
                    location.city_id = False

    @api.onchange("country_id")
    def _onchange_country_id(self):
        for location in self:
            if location.country_id:
                if (
                    location.province_id
                    and location.province_id.country_id != location.country_id
                ):
                    location.province_id = False
                if (
                    location.city_id
                    and location.city_id.state_id.country_id != location.country_id
                ):
                    location.city_id = False


class OnboardingCity(models.Model):
    _name = "qaco.onboarding.city"
    _description = "Onboarding City Reference"
    _order = "name"

    name = fields.Char(string="City", required=True)
    state_id = fields.Many2one(
        "res.country.state",
        string="Province / Territory",
        ondelete="cascade",
        required=True,
    )
    country_id = fields.Many2one(
        "res.country",
        string="Country",
        related="state_id.country_id",
        store=False,
        readonly=True,
    )

    _sql_constraints = [
        (
            "name_state_unique",
            "unique(name,state_id)",
            "City must be unique within its province.",
        ),
    ]


class OnboardingUBO(models.Model):
    _name = "qaco.onboarding.ubo"
    _description = "Ultimate Beneficial Owner"

    onboarding_id = fields.Many2one(
        "qaco.client.onboarding", required=True, ondelete="cascade", index=True
    )
    name = fields.Char(string="UBO Name", required=True)
    cnic_passport = fields.Char(string="CNIC / Passport Number")
    is_restricted = fields.Boolean(
        string="Restricted (ID)",
        default=True,
        help="Sensitive identifier - limited access",
    )
    nationality = fields.Char(string="Nationality")
    country_id = fields.Many2one("res.country", string="Country")
    ownership_percent = fields.Float(string="Ownership %", digits=(5, 2))
    basis_of_control = fields.Selection(
        [
            ("shareholding", "Shareholding"),
            ("voting", "Voting rights"),
            ("contract", "Contract/Arrangement"),
            ("other", "Other"),
        ],
        string="Basis of Control",
    )
    effective_interest = fields.Float(
        string="Effective interest (direct+indirect %)", digits=(5, 2)
    )
    pep_screening_result = fields.Selection(
        [
            ("clear", "Clear"),
            ("pep", "PEP"),
            ("sanction_check", "Sanctions hit"),
            ("not_checked", "Not checked"),
        ],
        string="PEP / Sanctions Screening",
    )
    filing_status = fields.Selection(
        [("filed", "Filed"), ("not_filed", "Not filed"), ("overdue", "Overdue")],
        string="Beneficial ownership filing status",
    )
    filing_evidence_file = fields.Binary(string="Filing Evidence", attachment=True)
    filing_evidence_filename = fields.Char(string="Filing Evidence Filename")

    @api.onchange("country_id")
    def _onchange_country_id(self):
        for record in self:
            if record.country_id:
                record.nationality = record.country_id.name

    @api.constrains("ownership_percent", "effective_interest")
    def _check_percentages_non_negative(self):
        for rec in self:
            if rec.ownership_percent and rec.ownership_percent < 0:
                raise ValidationError(_("Ownership percent cannot be negative."))
            if rec.effective_interest and rec.effective_interest < 0:
                raise ValidationError(_("Effective interest cannot be negative."))


class OnboardingSignatory(models.Model):
    _name = "qaco.onboarding.signatory"
    _description = "Authorized Signatory"

    onboarding_id = fields.Many2one(
        "qaco.client.onboarding", required=True, ondelete="cascade", index=True
    )
    name = fields.Char(string="Full Name", required=True)
    id_number = fields.Char(string="CNIC / Passport Number")
    is_restricted = fields.Boolean(string="Restricted (ID)", default=True)
    designation = fields.Char(string="Designation")
    authority_scope = fields.Char(string="Authority Scope")
    effective_date = fields.Date(string="Effective Date")
    expiry_date = fields.Date(string="Expiry Date")
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone")
    specimen_signature = fields.Binary(string="Specimen Signature", attachment=True)
    authority_evidence_id = fields.Many2one(
        "qaco.onboarding.document", string="Authority Evidence"
    )


class OnboardingVerificationException(models.Model):
    _name = "qaco.onboarding.verification.exception"
    _description = "Verification Exception / Mismatch"

    onboarding_id = fields.Many2one(
        "qaco.client.onboarding", required=True, ondelete="cascade", index=True
    )
    area = fields.Selection(
        [
            ("legal_identity", "Legal Identity"),
            ("regulatory", "Regulatory"),
            ("ownership_governance", "Ownership & Governance"),
            ("other", "Other"),
        ],
        string="Area",
        default="other",
    )
    field_name = fields.Char(string="Field")
    expected_value = fields.Char(string="Expected Value")
    observed_value = fields.Char(string="Observed Value")
    impact = fields.Char(string="Impact")
    resolution = fields.Text(string="Resolution")
    approved_by = fields.Many2one("res.users", string="Approved By")
    created_on = fields.Datetime(string="Created On", default=fields.Datetime.now)


class OnboardingShareholder(models.Model):
    _name = "qaco.onboarding.shareholder"
    _description = "Shareholder Pattern"

    onboarding_id = fields.Many2one(
        "qaco.client.onboarding", required=True, ondelete="cascade", index=True
    )
    name = fields.Char(string="Shareholder Name", required=True)
    id_number = fields.Char(string="CNIC / Passport / Reg. No.")
    country_id = fields.Many2one("res.country", string="Country / Residency")
    share_class = fields.Char(string="Class of Shares")
    nature_of_ownership = fields.Selection(
        [
            ("direct", "Direct"),
            ("indirect", "Indirect"),
            ("nominee", "Nominee"),
            ("other", "Other"),
        ],
        string="Nature of ownership",
    )
    percentage = fields.Float(string="Percentage", digits=(5, 2))
    voting_rights = fields.Char(string="Voting Rights Structure")
    beneficial_vs_legal = fields.Selection(
        [("beneficial", "Beneficial"), ("legal", "Legal")], string="Beneficial vs Legal"
    )
    acquisition_date = fields.Date(string="Acquisition Date")
    changes_during_year = fields.Boolean(string="Changes during year")
    changes_details = fields.Text(string="Changes details")
    pledges_charges = fields.Boolean(string="Pledge / Charge on Shares")
    pledges_details = fields.Text(string="Pledge details")


class OnboardingShareCapitalMovement(models.Model):
    _name = "qaco.onboarding.sharecapital.movement"
    _description = "Share Capital Movement"

    onboarding_id = fields.Many2one(
        "qaco.client.onboarding", required=True, ondelete="cascade", index=True
    )
    movement_type = fields.Selection(
        [
            ("issuance", "Issuance"),
            ("transfer", "Transfer"),
            ("buy_back", "Buy-back"),
            ("conversion", "Conversion"),
        ],
        string="Movement Type",
    )
    description = fields.Char(string="Description")
    amount = fields.Monetary(string="Amount", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        readonly=True,
        default=lambda self: self.env.company.currency_id,
    )
    approval_reference = fields.Char(string="Approvals / Reference")
    movement_date = fields.Date(string="Date")


class OnboardingGroupComponent(models.Model):
    _name = "qaco.onboarding.group.component"
    _description = "Group Component / Entity"

    onboarding_id = fields.Many2one(
        "qaco.client.onboarding", required=True, ondelete="cascade", index=True
    )
    entity_name = fields.Char(string="Entity Name", required=True)
    country_id = fields.Many2one("res.country", string="Country")
    relationship_type = fields.Selection(
        [
            ("subsidiary", "Subsidiary"),
            ("associate", "Associate"),
            ("joint_venture", "Joint Venture"),
            ("branch", "Branch"),
            ("other", "Other"),
        ],
        string="Relationship Type",
    )
    percent_ownership = fields.Float(string="% Ownership", digits=(5, 2))
    percent_voting = fields.Float(string="% Voting", digits=(5, 2))
    control_basis = fields.Selection(
        [
            ("ifrs10", "IFRS 10"),
            ("ias28", "IAS 28"),
            ("ifrs11", "IFRS 11"),
            ("other", "Other"),
        ],
        string="Control Basis",
    )
    financial_significance = fields.Char(
        string="Financial significance (assets/revenue/PBT)"
    )
    reporting_framework = fields.Char(string="Reporting Framework")
    year_end_alignment = fields.Selection(
        [("same", "Same"), ("different", "Different")], string="Year-end alignment"
    )
    component_auditor = fields.Char(string="Component auditor")


class OnboardingRelatedParty(models.Model):
    _name = "qaco.onboarding.related.party"
    _description = "Related Party Master List"

    onboarding_id = fields.Many2one(
        "qaco.client.onboarding", required=True, ondelete="cascade", index=True
    )
    name = fields.Char(string="Entity / Person", required=True)
    relationship = fields.Char(string="Relationship Nature")
    control_influence = fields.Char(string="Control / Influence Basis")
    expected_transactions = fields.Char(string="Expected Transactions")
    disclosure_expectations = fields.Char(string="Disclosure Expectations")


class OnboardingKMP(models.Model):
    _name = "qaco.onboarding.kmp"
    _description = "Key Management Personnel"

    onboarding_id = fields.Many2one(
        "qaco.client.onboarding", required=True, ondelete="cascade", index=True
    )
    name = fields.Char(string="Name", required=True)
    role = fields.Char(string="Role")
    contact = fields.Char(string="Contact Details")


class OnboardingBoardMember(models.Model):
    _name = "qaco.onboarding.board.member"
    _description = "Board Member or Key Personnel"

    onboarding_id = fields.Many2one(
        "qaco.client.onboarding", required=True, ondelete="cascade", index=True
    )
    name = fields.Char(string="Name", required=True)
    cnic = fields.Char(string="CNIC")
    din = fields.Char(string="DIN")
    role = fields.Selection(
        [
            ("ceo", "CEO"),
            ("cfo", "CFO"),
            ("company_secretary", "Company Secretary"),
            ("independent_director", "Independent Director"),
            ("other", "Other"),
        ],
        string="Role",
    )
    is_pep = fields.Boolean(string="Politically Exposed Person")


class OnboardingIndustry(models.Model):
    _name = "qaco.onboarding.industry"
    _description = "Industry / Sector Reference"

    name = fields.Char(string="Industry / Sector", required=True)
    risk_category = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        string="Risk Category",
        default="medium",
        required=True,
    )


class OnboardingIndependenceThreat(models.Model):
    _name = "qaco.onboarding.independence.threat"
    _description = "Independence Threat Checklist"

    onboarding_id = fields.Many2one(
        "qaco.client.onboarding", required=True, ondelete="cascade", index=True
    )
    threat_type = fields.Selection(THREAT_TYPES, string="Threat Type", required=True)
    answer = fields.Selection(
        [("no", "No"), ("yes", "Yes")], string="Threat Identified", required=True
    )
    details = fields.Text(string="Details / Safeguards")
    safeguards = fields.Text(string="Safeguards Applied")


class OnboardingDocument(models.Model):
    _name = "qaco.onboarding.document"
    _description = "Document Vault Entry"

    onboarding_id = fields.Many2one(
        "qaco.client.onboarding", required=True, ondelete="cascade", index=True
    )
    name = fields.Char(string="Document Name", required=True)
    doc_type = fields.Selection(
        DOCUMENT_TYPE_SELECTION, string="Document Type", default="other"
    )
    file = fields.Binary(string="File", attachment=True)
    file_name = fields.Char(string="File Name")
    state = fields.Selection(DOCUMENT_STATES, string="Status", default="pending")
    doc_type_label = fields.Char(
        string="Document Type (Label)", compute="_compute_doc_type_label"
    )

    @api.depends("doc_type")
    def _compute_doc_type_label(self):
        for record in self:
            record.doc_type_label = dict(DOCUMENT_TYPE_SELECTION).get(
                record.doc_type, record.doc_type or ""
            )


class OnboardingChecklistTemplate(models.Model):
    _name = "qaco.onboarding.checklist.template"
    _description = "Engagement Partner Decision Template"

    question = fields.Char(string="Checklist Question", required=True)
    category = fields.Char(string="Checklist Category")
    critical = fields.Boolean(string="Critical")


class OnboardingChecklistLine(models.Model):
    _name = "qaco.onboarding.checklist.line"
    _description = "Checklist Answer"

    onboarding_id = fields.Many2one(
        "qaco.client.onboarding", required=True, ondelete="cascade", index=True
    )
    template_id = fields.Many2one(
        "qaco.onboarding.checklist.template", string="Template Reference"
    )
    question = fields.Char(string="Question", required=True)
    category = fields.Char(string="Category")
    answer = fields.Selection(CHECKLIST_ANSWER_SELECTION, string="Answer")
    remarks = fields.Text(string="Remarks")
    critical = fields.Boolean(string="Critical")
    answer_label = fields.Char(string="Answer Label", compute="_compute_answer_label")

    @api.depends("answer")
    def _compute_answer_label(self):
        for record in self:
            record.answer_label = dict(CHECKLIST_ANSWER_SELECTION).get(
                record.answer, record.answer or ""
            )


class OnboardingIndependenceDeclaration(models.Model):
    _name = "qaco.onboarding.independence.declaration"
    _description = "Individual Independence Declaration"

    onboarding_id = fields.Many2one(
        "qaco.client.onboarding", required=True, ondelete="cascade", index=True
    )
    user_id = fields.Many2one("res.users", string="Team Member", required=True)
    state = fields.Selection(
        [("pending", "Pending"), ("confirmed", "Confirmed")],
        string="Declaration Status",
        default="pending",
    )
    confirmation_date = fields.Datetime(string="Confirmed On")
    reminder_sent = fields.Boolean(string="Reminder Sent")


class OnboardingPreconditionTemplate(models.Model):
    _name = "qaco.onboarding.precondition.template"
    _description = "ISA 210 Precondition Template"

    description = fields.Char(string="Precondition", required=True)


class OnboardingPreconditionLine(models.Model):
    _name = "qaco.onboarding.precondition.line"
    _description = "ISA 210 Precondition Confirmation"

    onboarding_id = fields.Many2one(
        "qaco.client.onboarding", required=True, ondelete="cascade", index=True
    )
    template_id = fields.Many2one(
        "qaco.onboarding.precondition.template", string="Template Reference"
    )
    description = fields.Char(string="Precondition", required=True)
    confirmed = fields.Boolean(string="Confirmed", default=False)


class OnboardingAuditTrail(models.Model):
    _name = "qaco.onboarding.audit.trail"
    _description = "Client Onboarding Audit Trail"

    ACTION_TYPES = [
        ("activity", "Activity"),
        ("override", "Override"),
        ("system", "System"),
        ("user", "User"),
    ]

    onboarding_id = fields.Many2one(
        "qaco.client.onboarding", required=True, ondelete="cascade", index=True
    )
    user_id = fields.Many2one(
        "res.users", string="User", default=lambda self: self.env.user.id
    )
    action = fields.Char(string="Action", required=True)
    action_type = fields.Selection(
        ACTION_TYPES, string="Action type", default="activity"
    )
    is_override = fields.Boolean(string="Override", default=False)
    resolution = fields.Text(string="Resolution / Notes")
    related_model = fields.Char(string="Related model")
    related_res_id = fields.Integer(string="Related record id")
    notes = fields.Text(string="Notes")
    create_date = fields.Datetime(string="Timestamp", default=fields.Datetime.now)

    def action_open_resolution_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "qaco.onboarding.audit.resolution.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_audit_id": self.id},
        }
