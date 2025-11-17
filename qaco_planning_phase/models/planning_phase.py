import base64
import json
import logging
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


ENTITY_CLASSES = [
    ("small", "Small Entity"),
    ("medium", "Medium Entity"),
    ("large", "Large Entity"),
    ("public_listed", "Public Listed"),
    ("public_unlisted", "Public Unlisted"),
    ("ngo", "NGO"),
    ("section_42", "Section 42 Company"),
    ("other", "Other"),
]

MATERIALITY_BENCHMARKS = [
    ("profit_before_tax", "Profit Before Tax (5%)"),
    ("revenue", "Revenue (0.5-1%)"),
    ("assets", "Total Assets (1-2%)"),
    ("equity", "Equity (3-5%)"),
    ("custom", "Custom"),
]

IC_CHECKLIST_ANSWERS = [
    ("yes", "Yes"),
    ("no", "No"),
    ("na", "Not Applicable"),
]

IC_RISK_RATINGS = [
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
]

IC_CONTROL_CYCLES = [
    ("revenue", "Revenue"),
    ("purchases", "Purchases / Payables"),
    ("inventory", "Inventory / Production"),
    ("payroll", "Payroll"),
    ("fixed_assets", "Fixed Assets"),
    ("treasury", "Treasury / Cash"),
    ("closing_reporting", "Financial Closing & Reporting"),
    ("other", "Other"),
]

IC_CONTROL_TYPES = [
    ("preventive", "Preventive"),
    ("detective", "Detective"),
]

IC_CONTROL_NATURE = [
    ("manual", "Manual"),
    ("automated", "Automated"),
    ("it_dependent", "IT Dependent"),
]

IC_CONTROL_FREQUENCY = [
    ("daily", "Daily"),
    ("weekly", "Weekly"),
    ("monthly", "Monthly"),
    ("quarterly", "Quarterly"),
    ("adhoc", "Ad-hoc"),
]

IC_IMPLEMENTATION_STATUS = [
    ("implemented", "Implemented"),
    ("not_implemented", "Not Implemented"),
    ("partial", "Partially Implemented"),
]

FS_RISK_LEVELS = [
    ("low", "Low"),
    ("moderate", "Moderate"),
    ("high", "High"),
]

CONTROL_RELIANCE = [
    ("no_reliance", "No Reliance"),
    ("limited", "Limited Reliance"),
    ("significant", "Significant Reliance"),
]

RISK_ACCOUNT_CYCLES = [
    ("revenue", "Revenue"),
    ("receivables", "Receivables"),
    ("inventory", "Inventory"),
    ("ppe", "Property, Plant & Equipment"),
    ("cash", "Cash & Cash Equivalents"),
    ("purchases", "Purchases / Payables"),
    ("payroll", "Payroll"),
    ("tax", "Tax"),
    ("others", "Others"),
]

RISK_TYPES = [
    ("fraud", "Fraud"),
    ("error", "Error"),
    ("compliance", "Compliance"),
    ("presentation", "Presentation / Disclosure"),
]

RISK_CATEGORIES = [
    ("inherent", "Inherent"),
    ("control", "Control"),
    ("detection", "Detection"),
    ("combined", "Combined"),
]

RISK_RATINGS = [
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
]

PLANNED_RESPONSE_TYPES = [
    ("toc", "Tests of Controls"),
    ("substantive", "Substantive Procedures"),
    ("combined", "Combined"),
    ("analytics", "Substantive Analytics"),
]

PLANNED_TIMINGS = [
    ("interim", "Interim"),
    ("year_end", "Year-end"),
    ("both", "Both"),
]

ESTIMATE_UNCERTAINTY_LEVELS = [
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
]

RELATED_PARTY_RISK_LEVELS = [
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
]

GOING_CONCERN_INDICATORS = [
    ("no_significant_doubt", "No Significant Doubt"),
    ("significant_doubt", "Significant Doubt"),
    ("material_uncertainty", "Material Uncertainty"),
]

EXPERT_TYPES = [
    ("valuation", "Valuation"),
    ("actuarial", "Actuarial"),
    ("legal", "Legal"),
    ("tax", "Tax"),
    ("it", "IT"),
    ("other", "Other"),
]

TEAM_LEVELS = [
    ("partner", "Partner"),
    ("manager", "Manager"),
    ("supervisor", "Supervisor"),
    ("semi_senior", "Semi Senior"),
    ("junior", "Junior"),
]

ATTACHMENT_TYPES = [
    ("memo", "Memo"),
    ("minutes", "Minutes"),
    ("excel", "Excel"),
    ("legal_doc", "Legal Document"),
    ("other", "Other"),
]

ASSERTION_CODES = [
    ("existence", "Existence"),
    ("completeness", "Completeness"),
    ("accuracy", "Accuracy"),
    ("valuation", "Valuation"),
    ("rights_obligations", "Rights & Obligations"),
    ("presentation", "Presentation & Disclosure"),
]


_logger = logging.getLogger(__name__)


class PlanningPhase(models.Model):
    _name = "qaco.planning.phase"
    _description = "Audit Planning Phase (ISA)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    # Basic fields
    name = fields.Char(
        default=lambda self: self.env["ir.sequence"].next_by_code("qaco.planning.phase") or _("New"),
        tracking=True,
        readonly=True,
        string="Planning Reference"
    )
    audit_id = fields.Many2one("qaco.audit", required=True, ondelete="cascade", tracking=True, string="Audit Reference")
    client_id = fields.Many2one(related='audit_id.client_id', string='Client', store=True, readonly=True)
    client_partner_id = fields.Many2one("res.partner", string="Audit Committee Chair")
    reporting_period_start = fields.Date(string="Period Start", tracking=True)
    reporting_period_end = fields.Date(string="Period End", tracking=True)
    legal_form = fields.Selection(
        [
            ("company", "Company"),
            ("partnership", "Partnership"),
            ("ngo", "NGO"),
            ("section_42", "Section 42 Company"),
            ("other", "Other"),
        ],
        default="company",
        tracking=True,
    )
    entity_classification = fields.Selection(ENTITY_CLASSES, string="Entity Classification", default="medium", tracking=True)
    
    acceptance_state = fields.Selection(
        [
            ("draft", "Draft"),
            ("precheck", "Independence Pre-check"),
            ("awaiting_clearance", "Awaiting Ethics Clearance"),
            ("accepted", "Accepted"),
            ("rejected", "Rejected"),
        ],
        default="draft",
        tracking=True,
    )
    acceptance_rationale = fields.Text(string="Acceptance Rationale")
    independence_questionnaire_result = fields.Selection(
        [
            ("clean", "No conflicts"),
            ("review", "Needs QCR review"),
            ("block", "Block engagement"),
        ],
        default="clean",
        tracking=True,
    )
    independence_notes = fields.Text(string="Independence Notes")
    qcr_contact_id = fields.Many2one("res.users", string="Ethics / QCR Contact")
    related_party_register = fields.Text(string="Related Parties Log")
    company_registration_no = fields.Char(string="Company Registration No")
    statutory_filing_obligations = fields.Text(string="Statutory Filing Obligations")
    audit_committee_required = fields.Boolean(compute="_compute_committee_required", store=True)
    secp_reporting_required = fields.Boolean(default=True)
    
    state = fields.Selection([
        ("draft", "Draft"),
        ("in_progress", "In Progress"),
        ("review", "Partner Review"),
        ("approved", "Approved"),
        ("fieldwork", "Fieldwork"),
        ("finalisation", "Finalisation"),
    ], default="draft", tracking=True, string="Status")
    planning_date = fields.Date(string="Planning Date", tracking=True)

    # ISA 300: Overall Audit Strategy
    overall_strategy = fields.Text(
        string="Overall Audit Strategy (ISA 300)",
        tracking=True,
        help="Scope, timing, direction, and areas of emphasis for the audit"
    )
    scope = fields.Text(string="Scope and Components", tracking=True)
    audit_scope = fields.Text(string='Audit Scope & Objectives', tracking=True)
    
    use_of_experts = fields.Boolean(string="Planned Use of Experts (ISA 620)", tracking=True)
    rely_on_internal_audit = fields.Boolean(string="Rely on Internal Audit (ISA 610)", tracking=True)
    significant_components = fields.Text(string="Significant Areas / Components")
    key_risk_areas = fields.Text(string='Key Risk Areas Identified', tracking=True)
    
    audit_approach = fields.Selection([
        ("substantive", "Substantive Approach"),
        ("controls", "Controls Reliance"),
        ("combined", "Combined Approach"),
    ], string="Overall Audit Approach", default="combined", tracking=True)

    # ISA 320 / ISA 450: Materiality & Performance Materiality
    materiality_guidance_html = fields.Html(
        string="Materiality Guidance",
        compute="_compute_materiality_guidance",
        sanitize=False,
        readonly=True,
    )
    materiality_basis = fields.Selection(
        MATERIALITY_BENCHMARKS,
        default="profit_before_tax",
        tracking=True,
        string="Materiality Benchmark (ISA 320)",
    )
    materiality_base = fields.Selection(
        MATERIALITY_BENCHMARKS,
        default="profit_before_tax",
        tracking=True,
        string="Materiality Base (Legacy)",
    )
    materiality_benchmark_source = fields.Selection(
        [
            ("current_year_fs", "Current Year FS / TB"),
            ("prior_year", "Prior Year Audited FS"),
            ("budget_forecast", "Budget / Forecast"),
            ("multi_year_average", "Multi-year Average"),
            ("other", "Other Source"),
        ],
        string="Benchmark Source",
        tracking=True,
        help="Document where the benchmark figure has been sourced from (ISA 320).",
    )
    benchmark_source_other = fields.Char(
        string="Benchmark Source (Other)",
        help="Use when the benchmark source selection is 'Other'.",
    )
    materiality_base_amount = fields.Monetary(
        string="Benchmark Base Amount",
        tracking=True,
        currency_field="currency_id",
        help="Enter the base financial metric used to derive overall materiality",
    )
    materiality_benchmark_rationale = fields.Text(
        string="Benchmark Rationale",
        tracking=True,
        help="Explain why this benchmark is appropriate (ISA 320 / ICAP policy).",
    )
    materiality_percentage = fields.Float(
        string="Overall Materiality Percentage (%)",
        default=5.0,
        tracking=True,
        help="Percentage applied to the benchmark amount (ISA 320).",
    )
    overall_materiality_amount_calc = fields.Monetary(
        string="Overall Materiality (Calculated)",
        currency_field="currency_id",
        compute="_compute_materiality_amounts",
        store=True,
        readonly=True,
        help="Benchmark base amount multiplied by the selected percentage.",
    )
    overall_materiality_override = fields.Boolean(
        string="Override Overall Materiality",
        tracking=True,
        help="Tick if firm policy or engagement partner approved an override to the automated calculation.",
    )
    overall_materiality_amount_override = fields.Monetary(
        string="Override Overall Materiality Amount",
        currency_field="currency_id",
        help="Enter the partner-approved overall materiality where it differs from the calculated amount.",
    )
    overall_materiality_override_reason = fields.Text(
        string="Overall Materiality Override Rationale",
        help="Document the reason for overriding the automated calculation (ISA 320 / ISA 450).",
    )
    overall_materiality_approved_by = fields.Many2one(
        "res.users",
        string="Overall Materiality Approved By",
        tracking=True,
        help="Typically the engagement partner / manager approving the override.",
    )
    overall_materiality_approved_date = fields.Date(
        string="Overall Materiality Approval Date",
        tracking=True,
    )
    materiality_amount = fields.Monetary(
        string="Effective Overall Materiality",
        currency_field="currency_id",
        tracking=True,
        compute="_compute_materiality_amounts",
        store=True,
        readonly=True,
        help="Final overall materiality applied in planning (override if provided).",
    )
    overall_materiality = fields.Monetary(
        string="Overall Materiality (Legacy)",
        currency_field="currency_id",
        tracking=True,
    )
    performance_materiality_percentage = fields.Float(
        string="Performance Materiality Percentage (%)",
        default=70.0,
        tracking=True,
        help="Typically 50-75% of overall materiality, based on control effectiveness and misstatement history.",
    )
    performance_materiality_amount_calc = fields.Monetary(
        string="Performance Materiality (Calculated)",
        currency_field="currency_id",
        compute="_compute_materiality_amounts",
        store=True,
        readonly=True,
    )
    performance_materiality_override = fields.Boolean(
        string="Override Performance Materiality",
        tracking=True,
    )
    performance_materiality_amount_override = fields.Monetary(
        string="Override Performance Materiality Amount",
        currency_field="currency_id",
    )
    performance_materiality_override_reason = fields.Text(
        string="Performance Materiality Override Rationale",
    )
    performance_materiality_approved_by = fields.Many2one(
        "res.users",
        string="Performance Materiality Approved By",
        tracking=True,
    )
    performance_materiality_approved_date = fields.Date(
        string="Performance Materiality Approval Date",
        tracking=True,
    )
    performance_materiality = fields.Monetary(
        string="Effective Performance Materiality",
        currency_field="currency_id",
        tracking=True,
        compute="_compute_materiality_amounts",
        store=True,
        readonly=True,
    )
    trivial_threshold_percentage = fields.Float(
        string="Clearly Trivial Threshold Percentage (%)",
        default=3.0,
        tracking=True,
        help="2-5% of overall materiality communicated to management (ISA 450).",
    )
    trivial_threshold_amount_calc = fields.Monetary(
        string="Clearly Trivial Threshold (Calculated)",
        currency_field="currency_id",
        compute="_compute_materiality_amounts",
        store=True,
        readonly=True,
    )
    trivial_threshold_override = fields.Boolean(
        string="Override Clearly Trivial Threshold",
        tracking=True,
    )
    trivial_threshold_amount_override = fields.Monetary(
        string="Override Clearly Trivial Threshold Amount",
        currency_field="currency_id",
    )
    trivial_threshold_override_reason = fields.Text(
        string="Clearly Trivial Override Rationale",
    )
    trivial_misstatement = fields.Monetary(
        string="Clearly Trivial Threshold (Effective)",
        currency_field="currency_id",
        tracking=True,
        compute="_compute_materiality_amounts",
        store=True,
        readonly=True,
    )
    trivial_threshold = fields.Monetary(
        string="Trivial Threshold (Legacy)",
        currency_field="currency_id",
        tracking=True,
    )
    clearly_trivial_threshold = fields.Monetary(
        string="Clearly Trivial Threshold (Legacy Field)",
        currency_field="currency_id",
        tracking=True,
        help="Legacy field retained for backward compatibility.",
    )
    materiality_notes = fields.Text(string="Materiality Rationale and Key Judgements")
    specific_materiality_ids = fields.One2many(
        "qaco.materiality.specific",
        "planning_id",
        string="Specific Materiality Areas",
    )
    materiality_attachment_ids = fields.Many2many(
        "ir.attachment",
        "qaco_planning_materiality_attachment_rel",
        "planning_id",
        "attachment_id",
        string="Materiality Working Papers",
        help="Attach TB extracts, firm templates, approvals, and ISA 450 misstatements summaries.",
    )
    materiality_template_url = fields.Char(
        string="Materiality Template Link",
        help="Optional reference to the firm's standard materiality calculation template.",
    )
    specific_materiality_template_url = fields.Char(
        string="Specific Materiality Template Link",
    )
    misstatement_summary_template_url = fields.Char(
        string="Misstatements Summary Template (ISA 450)",
    )
    materiality_reassessed = fields.Boolean(
        string="Materiality Reassessed During Audit?",
        tracking=True,
    )
    materiality_reassessment_triggers = fields.Text(
        string="Reassessment Triggers",
        help="Describe triggers such as significant changes in results, scope, or subsequent events.",
    )
    materiality_reassessment_date = fields.Date(
        string="Reassessment Date",
        tracking=True,
    )
    materiality_reassessment_approved_by = fields.Many2one(
        "res.users",
        string="Reassessment Approved By",
        tracking=True,
    )
    revised_overall_materiality = fields.Monetary(
        string="Revised Overall Materiality",
        currency_field="currency_id",
        tracking=True,
    )
    revised_performance_materiality = fields.Monetary(
        string="Revised Performance Materiality",
        currency_field="currency_id",
        tracking=True,
    )
    revised_trivial_threshold = fields.Monetary(
        string="Revised Clearly Trivial Threshold",
        currency_field="currency_id",
        tracking=True,
    )
    chk_users_and_needs_identified = fields.Boolean(
        string="Users of FS and needs identified",
        tracking=True,
    )
    comment_users_and_needs = fields.Text(string="Users & Needs Comments")
    chk_benchmark_selected_and_justified = fields.Boolean(
        string="Benchmark selected & justified",
        tracking=True,
    )
    comment_benchmark_selected = fields.Text(string="Benchmark Selection Comments")
    chk_benchmark_agrees_to_fs = fields.Boolean(
        string="Benchmark agrees to FS / TB",
        tracking=True,
    )
    comment_benchmark_agrees_to_fs = fields.Text(string="Benchmark Tie-out Comments")
    chk_overall_materiality_approved = fields.Boolean(
        string="Overall materiality approved",
        tracking=True,
    )
    comment_overall_materiality_approved = fields.Text(string="Overall Materiality Approval Comments")
    chk_performance_materiality_justified = fields.Boolean(
        string="Performance materiality justified",
        tracking=True,
    )
    comment_performance_materiality_justified = fields.Text(string="Performance Materiality Comments")
    chk_trivial_threshold_set_and_communicated = fields.Boolean(
        string="Clearly trivial threshold set & communicated",
        tracking=True,
    )
    comment_trivial_threshold = fields.Text(string="Clearly Trivial Threshold Comments")
    chk_specific_materiality_considered = fields.Selection(
        IC_CHECKLIST_ANSWERS,
        string="Specific materiality considered",
        tracking=True,
    )
    comment_specific_materiality = fields.Text(string="Specific Materiality Comments")
    chk_materiality_reassessment_considered = fields.Boolean(
        string="Materiality reassessment considered",
        tracking=True,
    )
    comment_materiality_reassessment = fields.Text(string="Materiality Reassessment Comments")
    chk_consistency_prior_year_explained = fields.Boolean(
        string="Consistency with prior year explained",
        tracking=True,
    )
    comment_consistency_prior_year = fields.Text(string="Prior Year Consistency Comments")
    materiality_tab_complete = fields.Boolean(
        string="Materiality Tab Complete",
        compute="_compute_materiality_tab_complete",
        store=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self._get_default_currency(),
    )

    def _compute_materiality_guidance(self):
        guidance = _(
            """
            <div class="alert alert-info">
                <p><strong>Objective:</strong> Set overall materiality, performance materiality, clearly trivial thresholds, and specific materiality for sensitive classes of transactions/disclosures in line with ISA 320 &amp; ISA 450 as practiced under ICAP / AOB expectations.</p>
                <ul>
                    <li>Select an appropriate benchmark (e.g., PBT, revenue, assets, equity, custom) and document the rationale, especially for loss-making entities.</li>
                    <li>Capture the benchmark source (current year, prior year, budgets, averages) and ensure it agrees to the supporting FS / TB.</li>
                    <li>Set overall materiality, calculate performance materiality (50-75%), and define a clearly trivial threshold (typically 2-5%).</li>
                    <li>Consider specific materiality for particular balances/disclosures (e.g., related parties, regulatory capital, donor-funded grants) and document reasoning.</li>
                    <li>Override calculations only with documented approval; the system keeps automated calculations while allowing justified overrides.</li>
                    <li>Reassess materiality when results or scope change and capture approvals per ISA 320/450.</li>
                </ul>
            </div>
            """
        )
        for rec in self:
            rec.materiality_guidance_html = guidance

       # ISA 210/220: Ethics & Compliance
    engagement_letter_obtained = fields.Boolean(
        string="Engagement Letter Obtained (ISA 210)",
        tracking=True
    )
    engagement_letter_signed = fields.Boolean(
        string="Engagement Letter Signed (Legacy)",
        tracking=True
    )
    engagement_letter_date = fields.Date(
        string="Engagement Letter Date",
        tracking=True
    )
    scope_agreement_confirmed = fields.Boolean(
        string="Scope Agreement Confirmed",
        tracking=True
    )
    management_responsibility_ack = fields.Boolean(
        string="Management Responsibilities Acknowledged",
        tracking=True
    )
    preconditions_for_audit_assessed = fields.Boolean(
        string="Preconditions for Audit Assessed",
        tracking=True
    )
    framework_acceptability_assessed = fields.Boolean(
        string="Acceptability of Accounting Framework Assessed",
        tracking=True
    )
    continuing_client_evaluation_completed = fields.Boolean(
        string="Continuing Client Evaluation Completed",
        tracking=True,
        oldname="continuing_client_evaluation_done",
    )
    previous_auditor_communication = fields.Boolean(
        string="Communication with Previous Auditor Completed",
        tracking=True,
        help="Tick once professional clearance / communication with the predecessor auditor has been obtained.",
    )
    acceptance_continuance_reason = fields.Text(string="Reasons for Acceptance / Continuance")

    independence_confirmed = fields.Boolean(
        string="Independence Confirmed (IESBA Code)",
        tracking=True
    )
    independence_confirmation_date = fields.Date(
        string="Independence Confirmation Date",
        tracking=True
    )
    independence_team_confirmed = fields.Boolean(
        string="All Team Members Confirmed Independence",
        tracking=True
    )
    independence_supporting_doc = fields.Binary(
        string="Independence Confirmation Attachment",
        attachment=True
    )
    independence_team_attachment = fields.Binary(
        string="Team Independence Declarations (Attachment)",
        attachment=True
    )
    threat_self_interest = fields.Text(string="Self-Interest Threat")
    threat_self_review = fields.Text(string="Self-Review Threat")
    threat_advocacy = fields.Text(string="Advocacy Threat")
    threat_familiarity = fields.Text(string="Familiarity Threat")
    threat_intimidation = fields.Text(string="Intimidation Threat")
    safeguards_documented = fields.Text(
        string="Safeguards Documented",
        oldname="safeguards_applied",
    )
    eqcr_required = fields.Boolean(
        string="Engagement Quality Control Review (EQCR) Required",
        tracking=True
    )

    def _get_default_currency(self):
        """Return PKR currency if available, otherwise fall back to company currency."""
        return self.env.ref("base.PKR", raise_if_not_found=False) or self.env.user.company_id.currency_id
    eqcr_reviewer_id = fields.Many2one(
        "res.users",
        string="EQCR Reviewer",
        tracking=True
    )
    eqcr_review_completed = fields.Boolean(
        string="EQCR Review Completed",
        tracking=True,
    )
    eqcr_review_date = fields.Date(
        string="EQCR Review Date",
        tracking=True,
    )
    rotation_required = fields.Boolean(
        string="Partner Rotation Required",
        tracking=True
    )
    last_rotation_date = fields.Date(
        string="Last Rotation Date",
        tracking=True
    )
    partner_tenure_years = fields.Integer(
        string="Current Engagement Partner Tenure (Years)",
        tracking=True
    )

    ethical_requirements_met = fields.Boolean(
        string="Ethical Requirements Met (ISA 220)",
        tracking=True
    )
    integrity_confirmed = fields.Boolean(
        string="Integrity Confirmed",
        tracking=True
    )
    objectivity_confirmed = fields.Boolean(
        string="Objectivity Confirmed",
        tracking=True
    )
    professional_competence_due_care = fields.Boolean(
        string="Professional Competence & Due Care Confirmed",
        tracking=True
    )
    confidentiality_compliance = fields.Boolean(
        string="Confidentiality Compliance",
        tracking=True,
        oldname="confidentiality_confirmed",
    )
    professional_behavior_compliance = fields.Boolean(
        string="Professional Behavior Compliance",
        tracking=True,
        oldname="professional_behavior_confirmed",
    )
    noclar_risk_identified = fields.Boolean(
        string="NOCLAR Risk Identified",
        tracking=True
    )
    noclar_actions_necessary = fields.Text(
        string="NOCLAR Actions Necessary",
        oldname="noclar_actions_required",
    )

    conflict_of_interest_identified = fields.Boolean(
        string="Conflict of Interest Identified",
        tracking=True
    )
    conflict_of_interest_nature = fields.Text(string="Nature of Conflict")
    conflict_resolution_applied = fields.Text(
        string="Conflict Resolution Applied",
        oldname="conflict_resolution_action",
    )
    conflict_client_notified = fields.Boolean(
        string="Client Notified of Conflict & Safeguards",
        tracking=True
    )

    engagement_partner_review_form = fields.Boolean(
        string="Engagement Partner Review Form Completed",
        tracking=True,
        oldname="engagement_partner_review_done",
    )
    aob_independence_partner_confirmed = fields.Boolean(
        string="AOB Independence Declaration - Partner",
        tracking=True
    )
    aob_independence_team_confirmed = fields.Boolean(
        string="AOB Independence Declaration - Team",
        tracking=True
    )
    aob_independence_checklist = fields.Binary(
        string="AOB Independence Checklist (Attachment)",
        attachment=True
    )
    qcr_compliance_checklist = fields.Binary(
        string="QCR Compliance Checklist (Attachment)",
        attachment=True
    )
    rotation_cooling_off_consent = fields.Boolean(
        string="Rotation & Cooling-Off Requirements Confirmed",
        tracking=True
    )

    aml_kyc_performed = fields.Boolean(
        string="AML / KYC Performed",
        tracking=True
    )
    beneficial_ownership_obtained = fields.Boolean(
        string="Beneficial Ownership Information Obtained",
        tracking=True
    )
    aml_risk_rating = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
        ],
        string="AML Risk Rating",
        tracking=True
    )
    dnfbp_compliance_check_completed = fields.Boolean(
        string="DNFBP Compliance Check Completed",
        tracking=True,
        oldname="dnfbp_compliance_checked",
    )
    suspicious_transaction_risk = fields.Boolean(
        string="Suspicious Transaction Risk Identified",
        tracking=True
    )
    pep_screening_done = fields.Boolean(
        string="PEP (Politically Exposed Person) Screening Done",
        tracking=True
    )

    companies_act_compliance_verified = fields.Boolean(
        string="Companies Act 2017 Compliance Verified",
        tracking=True,
        oldname="companies_act_compliance",
    )
    secp_rules_applicable = fields.Boolean(
        string="SECP Rules / Regulations Applicable & Considered",
        tracking=True
    )
    tax_laws_compliance_verified = fields.Boolean(
        string="Tax Laws Compliance Verified",
        tracking=True,
        oldname="tax_laws_compliance",
    )
    industry_specific_regulations = fields.Text(
        string="Industry-Specific Regulations",
        oldname="industry_regulation_notes",
    )
    compliance_documentation_complete = fields.Boolean(
        string="Compliance Documentation Completed",
        tracking=True
    )
    final_compliance_signoff = fields.Boolean(
        string="Final Compliance Sign-Off by Engagement Partner",
        tracking=True
    )

    fraud_risk_factors_identified = fields.Boolean(
        string="Fraud Risk Factors Identified",
        tracking=True
    )
    management_attitude_fraud_assessed = fields.Boolean(
        string="Management Attitude Towards Fraud Assessed",
        tracking=True,
    )
    management_attitude_fraud_notes = fields.Text(
        string="Management Attitude Towards Fraud Notes",
        oldname="management_attitude_fraud",
    )
    ethical_concerns_identified = fields.Boolean(
        string="Ethical Concerns Identified",
        tracking=True
    )
    whistleblower_policy_exists = fields.Boolean(
        string="Whistleblower Policy Exists",
        tracking=True
    )

    related_party_list_obtained = fields.Boolean(
        string="Related Party List Obtained",
        tracking=True
    )
    management_related_party_declaration = fields.Boolean(
        string="Management Declaration on Related Parties Obtained",
        tracking=True,
        oldname="management_related_party_decl",
    )
    related_party_conflict_identified = fields.Boolean(
        string="Conflict with Related Parties Identified?",
        tracking=True,
        oldname="conflict_with_related_parties",
    )
    related_party_conflict_notes = fields.Text(string="Related Party Conflict Notes / Safeguards")

    # Client & Industry Information
    industry_sector_id = fields.Many2one(
        'planning.industry.sector', 
        string='Client Industry / Sector', 
        tracking=True
    )
    business_nature = fields.Text(string='Nature of Business', tracking=True)
    key_personnel = fields.Text(string='Key Client Personnel', tracking=True)
    client_year_end = fields.Date(string='Financial Year End', tracking=True)
    client_regulator = fields.Char(string='Primary Regulator / Oversight Body', tracking=True)
    client_listing_exchange = fields.Char(string='Listed Exchange (if any)', tracking=True)
    client_ownership_structure = fields.Text(string='Ownership Structure', tracking=True)
    client_governance_notes = fields.Text(string='Governance Structure / Audit Committee', tracking=True)
    client_objectives_strategies = fields.Text(string='Objectives & Strategies', tracking=True)
    client_measurement_basis = fields.Text(string='Financial Measurement & KPIs', tracking=True)
    client_it_environment = fields.Text(string='IT Environment & Key Systems', tracking=True)
    client_compliance_matters = fields.Text(string='Compliance / Regulatory Matters', tracking=True)
    industry_overview = fields.Text(string="Industry Overview", tracking=True)
    regulatory_factors = fields.Text(string="Regulatory / External Factors", tracking=True)
    business_overview = fields.Text(string="Business Model Overview", tracking=True)
    it_environment_overview = fields.Text(string="IT Environment Overview", tracking=True)
    governance_structure = fields.Text(string="Governance & Oversight", tracking=True)
    going_concern_factors = fields.Text(string="Going Concern Factors", tracking=True)
    
    # Engagement Information
    engagement_type = fields.Selection([
        ('statutory', 'Statutory Audit'),
        ('internal', 'Internal Audit'),
        ('special', 'Special Purpose Audit'),
        ('review', 'Review Engagement'),
        ('agreed_procedures', 'Agreed Upon Procedures'),
    ], string='Engagement Type', tracking=True)
    
    reporting_framework = fields.Selection(
        [
            ("ifrs_pakistan", "IFRS (Pakistan Companies Act 2017)"),
            ("ias_only", "IAS Only / Legacy"),
            ("cash_basis", "Cash / Fund Accounting"),
            ("special_purpose", "Special Purpose Framework"),
            ("ifrs", "IFRS (Legacy)"),
            ("ifrs_sme", "IFRS for SMEs (Legacy)"),
            ("local_gaap", "Local GAAP (Legacy)"),
            ("other", "Other"),
        ],
        string="Reporting Framework",
        tracking=True,
        help="Select the applicable financial reporting framework for the current engagement year.",
    )
    
    # Risk Assessment
    inherent_risk = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Inherent Risk', tracking=True)
    
    control_risk = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Control Risk', tracking=True)
    
    detection_risk = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Detection Risk', tracking=True)
    
    fraud_risk_assessment = fields.Text(string='Fraud Risk Assessment', tracking=True)
    control_environment_notes = fields.Text(string="Control Environment", tracking=True)
    risk_assessment_process_notes = fields.Text(string="Entity Risk Assessment Process", tracking=True)
    information_systems_notes = fields.Text(string="Information Systems & Communication", tracking=True)
    control_activities_notes = fields.Text(string="Control Activities", tracking=True)
    monitoring_controls_notes = fields.Text(string="Monitoring of Controls", tracking=True)

    # Internal Control Assessment / Understanding (ISA 315 & ISA 330 linkage)
    tone_at_the_top = fields.Text(string="Tone at the Top", tracking=True)
    organizational_structure_file = fields.Binary(
        string="Organizational Structure (Attachment)",
        attachment=True,
    )
    organizational_structure_filename = fields.Char(string="Org Structure Filename")
    authority_and_responsibility = fields.Text(string="Authority & Responsibility", tracking=True)
    human_resource_policies = fields.Text(string="Human Resource Policies", tracking=True)
    code_of_conduct_existence = fields.Selection(
        [
            ("yes", "Yes"),
            ("no", "No"),
            ("partial", "Partially Documented"),
        ],
        string="Code of Conduct / Ethics Program",
        tracking=True,
    )
    whistleblowing_policy = fields.Selection(
        [("yes", "Yes"), ("no", "No")],
        string="Whistleblowing Mechanism in Place",
        tracking=True,
    )
    whistleblowing_details = fields.Text(string="Whistleblowing Details", tracking=True)
    has_audit_committee = fields.Boolean(string="Audit Committee in Place", tracking=True)
    audit_committee_composition = fields.Text(string="Audit Committee Composition", tracking=True)
    audit_committee_meeting_freq = fields.Selection(
        [
            ("quarterly", "Quarterly"),
            ("semi_annual", "Semi-Annual"),
            ("annual", "Annual"),
            ("ad_hoc", "Ad-hoc"),
        ],
        string="Audit Committee Meeting Frequency",
        tracking=True,
    )
    audit_committee_effectiveness_assessment = fields.Text(
        string="Audit Committee Effectiveness Assessment",
        tracking=True,
    )
    has_internal_audit_function = fields.Boolean(string="Internal Audit Function Exists", tracking=True)
    internal_audit_reporting_line = fields.Selection(
        [
            ("audit_committee", "Audit Committee"),
            ("board", "Board of Directors"),
            ("ceo", "CEO"),
            ("cfo", "CFO"),
        ],
        string="Internal Audit Reporting Line",
        tracking=True,
    )
    internal_audit_scope_summary = fields.Text(string="Internal Audit Scope Summary", tracking=True)
    last_internal_audit_report_date = fields.Date(string="Last Internal Audit Report Date", tracking=True)
    key_ia_findings_summary = fields.Text(string="Key IA Findings Summary", tracking=True)
    control_env_checklist_ids = fields.One2many(
        "qaco.ic.control.env.line",
        "planning_id",
        string="Control Environment Checklist",
    )
    control_env_attachment_ids = fields.Many2many(
        "ir.attachment",
        "qaco_planning_control_env_attachment_rel",
        "planning_id",
        "attachment_id",
        string="Control Environment Attachments",
    )

    formal_risk_management_framework = fields.Selection(
        [
            ("yes", "Yes - Documented"),
            ("no", "No Formal Framework"),
            ("informal", "Informal / Emerging"),
        ],
        string="Formal Risk Management Framework",
        tracking=True,
    )
    risk_policy_exists = fields.Boolean(string="Risk Policy Exists", tracking=True)
    risk_policy_attachment = fields.Binary(string="Risk Policy Attachment", attachment=True)
    risk_policy_attachment_name = fields.Char(string="Risk Policy Filename")
    has_risk_register = fields.Boolean(string="Risk Register Maintained", tracking=True)
    risk_register_attachment = fields.Binary(string="Risk Register Attachment", attachment=True)
    risk_register_attachment_name = fields.Char(string="Risk Register Filename")
    risk_assessment_frequency = fields.Selection(
        [
            ("annual", "Annual"),
            ("quarterly", "Quarterly"),
            ("ad_hoc", "Ad-hoc"),
            ("none", "None"),
        ],
        string="Risk Assessment Frequency",
        tracking=True,
    )
    responsible_person_for_risk = fields.Many2one(
        "res.partner",
        string="Responsible Person for Risk",
        tracking=True,
    )
    linkage_to_financial_reporting = fields.Text(string="Linkage to Financial Reporting", tracking=True)
    key_business_risks_summary = fields.Text(string="Key Business Risks Summary", tracking=True)
    key_fraud_risks_identified = fields.Text(string="Key Fraud Risks Identified", tracking=True)
    impact_on_audit_strategy = fields.Text(string="Impact on Audit Strategy", tracking=True)
    risk_process_checklist_ids = fields.One2many(
        "qaco.ic.risk.process.line",
        "planning_id",
        string="Risk Assessment Process Checklist",
    )
    risk_process_attachment_ids = fields.Many2many(
        "ir.attachment",
        "qaco_planning_risk_process_attachment_rel",
        "planning_id",
        "attachment_id",
        string="Risk Process Attachments",
    )

    main_erp_or_accounting_system = fields.Char(string="Main ERP / Accounting System", tracking=True)
    other_critical_applications = fields.Text(string="Other Critical Applications", tracking=True)
    it_infrastructure_summary = fields.Text(string="IT Infrastructure Summary", tracking=True)
    outsourced_it_services = fields.Text(string="Outsourced IT Services", tracking=True)
    user_access_management = fields.Text(string="User Access Management", tracking=True)
    password_policies = fields.Text(string="Password Policies", tracking=True)
    change_management_process = fields.Text(string="Change Management Process", tracking=True)
    backup_and_restore_procedures = fields.Text(string="Backup & Restore Procedures", tracking=True)
    incident_management = fields.Text(string="Incident Management", tracking=True)
    business_continuity_and_dr = fields.Text(string="Business Continuity & DRP", tracking=True)
    security_controls = fields.Text(string="Security Controls", tracking=True)
    itgc_reliance_planned = fields.Boolean(string="Plan to Rely on ITGC?", tracking=True)
    needs_it_specialist = fields.Boolean(string="IT Specialist Needed?", tracking=True)
    itgc_checklist_ids = fields.One2many(
        "qaco.ic.itgc.line",
        "planning_id",
        string="ITGC Checklist",
    )
    itgc_attachment_ids = fields.Many2many(
        "ir.attachment",
        "qaco_planning_itgc_attachment_rel",
        "planning_id",
        "attachment_id",
        string="ITGC Attachments",
    )

    control_activity_ids = fields.One2many(
        "qaco.ic.control.activity.line",
        "planning_id",
        string="Control Activities by Cycle",
    )

    monitoring_activities_description = fields.Text(string="Monitoring Activities Description", tracking=True)
    frequency_of_monitoring = fields.Selection(
        [
            ("continuous", "Continuous / Embedded"),
            ("quarterly", "Quarterly"),
            ("annual", "Annual"),
            ("ad_hoc", "Ad-hoc"),
        ],
        string="Frequency of Monitoring",
        tracking=True,
    )
    reporting_of_deficiencies = fields.Text(string="Reporting of Deficiencies", tracking=True)
    follow_up_on_deficiencies = fields.Text(string="Follow-up on Deficiencies", tracking=True)
    monitoring_checklist_ids = fields.One2many(
        "qaco.ic.monitoring.line",
        "planning_id",
        string="Monitoring Checklist",
    )
    monitoring_attachment_ids = fields.Many2many(
        "ir.attachment",
        "qaco_planning_monitoring_attachment_rel",
        "planning_id",
        "attachment_id",
        string="Monitoring Attachments",
    )

    is_listed_company = fields.Boolean(string="Listed Company", tracking=True)
    is_public_sector_company = fields.Boolean(string="Public Sector Company", tracking=True)
    is_regulated_by_sbp_or_secp_specific_regime = fields.Selection(
        [
            ("sbp", "State Bank of Pakistan"),
            ("secp_nbfc", "SECP NBFC Regulations"),
            ("insurance", "Insurance / Takaful Regulations"),
            ("modaraba", "Modaraba Regulations"),
            ("none", "None"),
        ],
        string="Specific Regulator",
        tracking=True,
    )
    cg_regulation_applicable = fields.Selection(
        [
            ("secp_listed", "SECP Listed Co CG Regulations 2019"),
            ("psc_rules", "Public Sector Companies (Corporate Governance) Rules"),
            ("sbp_guidelines", "SBP Governance Guidelines"),
            ("other", "Other / Custom Framework"),
        ],
        string="Applicable CG Regulation",
        tracking=True,
    )
    cg_compliance_status = fields.Selection(
        [
            ("compliant", "Compliant"),
            ("partial", "Partially Compliant"),
            ("non_compliant", "Non-compliant"),
        ],
        string="Corporate Governance Compliance",
        tracking=True,
    )
    cg_compliance_comments = fields.Text(string="CG Compliance Comments", tracking=True)
    board_and_ac_composition_vs_regulations = fields.Text(
        string="Board & AC Composition vs Regulations",
        tracking=True,
    )
    required_committees_in_place = fields.Boolean(string="Required Committees Constituted?", tracking=True)
    required_committees_details = fields.Text(string="Required Committees Details", tracking=True)
    ceocfo_certification_exists = fields.Boolean(string="CEO/CFO Certification Obtained?", tracking=True)
    ceocfo_certification_attachment = fields.Binary(
        string="CEO/CFO Certification",
        attachment=True,
    )
    ceocfo_certification_filename = fields.Char(string="Certification Filename")
    related_party_approval_process = fields.Text(string="Related Party Approval Process", tracking=True)
    cg_attachment_ids = fields.Many2many(
        "ir.attachment",
        "qaco_planning_cg_attachment_rel",
        "planning_id",
        "attachment_id",
        string="Corporate Governance Attachments",
    )

    ic_deficiency_ids = fields.One2many(
        "qaco.ic.deficiency.line",
        "planning_id",
        string="Key IC Deficiencies",
    )
    ic_attachment_index_ids = fields.One2many(
        "qaco.ic.attachment.index.line",
        "planning_id",
        string="IC Attachment Index",
    )

    overall_ic_assessment = fields.Selection(
        [
            ("does_not_exist", "Controls do not exist / no formal internal control system"),
            ("weak", "Weak controls (significant deficiencies; cannot rely on controls)"),
            ("moderate", "Moderate controls (some deficiencies; partial reliance possible)"),
            ("strong", "Strong controls (well designed & implemented; reliance appropriate)"),
        ],
        string="Overall Internal Control Assessment",
        tracking=True,
        help="Summarise the auditor's ISA 315 conclusion on the design & implementation of internal controls relevant to financial reporting.",
    )
    toc_strategy = fields.Selection(
        [
            ("perform_toc", "Perform Tests of Controls during execution and rely on controls (ISA 330)"),
            ("no_toc", "Do not perform Tests of Controls; adopt fully substantive approach"),
        ],
        string="Tests of Controls Strategy",
        tracking=True,
        help="Automatically determined based on the overall internal control assessment to evidence whether ToC will be performed in execution.",
    )
    ic_assessment_conclusion = fields.Text(
        string="Internal Control Assessment Conclusion",
        help="Document rationale for the IC assessment, impact on RoMM and resulting ISA 330 audit approach.",
        tracking=True,
    )
    
    # Planning Checklists (Legacy)
    understanding_entity_obtained = fields.Boolean(
        string='Understanding of Entity Obtained', 
        tracking=True
    )
    internal_controls_documented = fields.Boolean(
        string='Internal Controls Documented', 
        tracking=True
    )
    analytical_procedures_performed = fields.Boolean(
        string='Analytical Procedures Performed', 
        tracking=True
    )

    # Understanding the Entity & Environment (ISA 300 / ISA 315)
    business_model_current_year = fields.Text(
        string="Business Model (Current Year)",
        tracking=True,
        help="Summarize the client business model, key processes, and value drivers for the current audit year.",
    )
    key_products_services = fields.Text(string="Key Products / Services", tracking=True)
    major_customers_current_year = fields.Text(string="Major Customers (Current Year)", tracking=True)
    major_suppliers_current_year = fields.Text(string="Major Suppliers (Current Year)", tracking=True)
    significant_changes_in_business = fields.Text(string="Significant Changes in Business", tracking=True)
    going_concern_indicators = fields.Selection(
        [
            ("no_issues", "No indicators"),
            ("mild_concern", "Mild concern"),
            ("significant_doubt", "Significant doubt"),
        ],
        string="Going Concern Indicators",
        default="no_issues",
        tracking=True,
    )
    going_concern_comments = fields.Text(string="Going Concern Comments", tracking=True)
    bm_prior_year_updated = fields.Boolean(string="Prior Year Business Model Updated?", tracking=True)
    bm_prior_year_updated_comment = fields.Text(string="Prior Year BM Comments", tracking=True)
    bm_major_change = fields.Boolean(string="Major Change in Business Model?", tracking=True)
    bm_major_change_comment = fields.Text(string="Major Change Comment", tracking=True)
    bm_customer_supplier_dependency = fields.Boolean(string="Significant Customer / Supplier Dependency?", tracking=True)
    bm_customer_supplier_dependency_comment = fields.Text(string="Dependency Comment", tracking=True)
    bm_going_concern_uncertainty = fields.Boolean(string="Going Concern Uncertainty Identified?", tracking=True)
    bm_going_concern_uncertainty_comment = fields.Text(string="Going Concern Uncertainty Comment", tracking=True)
    bm_attachment_ids = fields.Many2many(
        "ir.attachment",
        "qaco_planning_bm_attachment_rel",
        "planning_id",
        "attachment_id",
        string="Business Model Attachments",
        help="Attach business profiles, strategy decks, and key customer / supplier agreements.",
    )
    bm_template_notes = fields.Text(
        string="Business Model Questionnaire Notes",
        help="Document whether ISA 315 business model templates were used and any tailoring applied.",
    )

    primary_regulator = fields.Selection(
        [
            ("secp", "SECP"),
            ("sbp", "State Bank of Pakistan"),
            ("other_sector_regulator", "Other Sector Regulator"),
            ("none", "None"),
            ("multiple", "Multiple regulators"),
        ],
        string="Primary Regulator",
        tracking=True,
    )
    tax_regime_summary = fields.Text(string="Income Tax Regime Summary", tracking=True)
    indirect_tax_regime_summary = fields.Text(string="Indirect / Provincial Tax Summary", tracking=True)
    regulatory_changes_current_year = fields.Text(string="Regulatory Changes (Current Year)", tracking=True)
    pending_regulatory_inspections = fields.Text(string="Pending Regulatory Inspections", tracking=True)
    litigation_summary_regulatory = fields.Text(string="Regulatory Litigation Summary", tracking=True)
    reg_secp_filings_done = fields.Boolean(string="SECP Filings Completed?", tracking=True)
    reg_secp_filings_comment = fields.Text(string="SECP Filings Comments", tracking=True)
    reg_pending_notices = fields.Boolean(string="Pending Regulatory Notices?", tracking=True)
    reg_pending_notices_comment = fields.Text(string="Regulatory Notices Comment", tracking=True)
    reg_license_non_compliance = fields.Boolean(string="License Non-Compliance?", tracking=True)
    reg_license_non_compliance_comment = fields.Text(string="License Non-Compliance Comment", tracking=True)
    reg_tax_returns_on_time = fields.Boolean(string="Tax Returns Filed On Time?", tracking=True)
    reg_tax_returns_on_time_comment = fields.Text(string="Tax Filing Timeliness Comment", tracking=True)
    reg_attachment_ids = fields.Many2many(
        "ir.attachment",
        "qaco_planning_reg_attachment_rel",
        "planning_id",
        "attachment_id",
        string="Regulatory Attachments",
        help="Upload SECP filings, regulator licenses, and current tax filings.",
    )

    financial_reporting_schedule_ids = fields.Many2many(
        "qaco.financial.reporting.schedule",
        "qaco_planning_fr_schedule_rel",
        "planning_id",
        "schedule_id",
        string="Financial Reporting Schedules",
        help="Reference applicable Companies Act schedules or sector formats.",
    )
    significant_policies_summary = fields.Text(string="Significant Accounting Policies", tracking=True)
    changes_in_policies_current_year = fields.Text(string="Changes in Policies (Current Year)", tracking=True)
    key_judgements_estimates = fields.Text(string="Key Judgements & Estimates", tracking=True)
    fr_companies_act_compliant = fields.Boolean(string="Companies Act 2017 Compliant?", tracking=True)
    fr_companies_act_comment = fields.Text(string="Companies Act Compliance Comment", tracking=True)
    fr_departures_ifrs = fields.Boolean(string="Departures from IFRS / IAS?", tracking=True)
    fr_departures_ifrs_comment = fields.Text(string="IFRS Departure Details", tracking=True)
    fr_new_ifrs_implemented = fields.Boolean(string="New IFRS Implemented?", tracking=True)
    fr_new_ifrs_implemented_comment = fields.Text(string="New IFRS Commentary", tracking=True)
    fr_policies_consistent = fields.Boolean(string="Policies Applied Consistently?", tracking=True)
    fr_policies_consistent_comment = fields.Text(string="Policy Consistency Comment", tracking=True)
    fr_attachment_ids = fields.Many2many(
        "ir.attachment",
        "qaco_planning_fr_attachment_rel",
        "planning_id",
        "attachment_id",
        string="Financial Reporting Attachments",
        help="Attach prior year FS, draft current FS, and accounting policy manuals.",
    )

    main_erp_system = fields.Char(string="Primary ERP / G/L", tracking=True)
    other_critical_systems = fields.Text(string="Other Critical Systems", tracking=True)
    data_hosting = fields.Selection(
        [("on_premise", "On Premise"), ("cloud", "Cloud"), ("hybrid", "Hybrid")],
        string="Data Hosting",
        tracking=True,
    )
    it_changes_current_year = fields.Text(string="IT Changes (Current Year)", tracking=True)
    extent_of_it_dependence = fields.Selection(
        [("high", "High"), ("medium", "Medium"), ("low", "Low")],
        string="Extent of IT Dependence",
        tracking=True,
    )
    extent_of_it_dependence_comment = fields.Text(string="IT Dependence Commentary", tracking=True)
    planned_it_audit_involvement = fields.Selection(
        [
            ("yes_internal", "Internal IT specialists"),
            ("yes_external_specialist", "External IT specialists"),
            ("no", "No dedicated IT audit"),
        ],
        string="Planned IT Audit Involvement",
        tracking=True,
    )
    it_access_controls_tested = fields.Boolean(string="Access Controls Tested?", tracking=True)
    it_access_controls_comment = fields.Text(string="Access Controls Comment", tracking=True)
    it_incidents_or_breaches = fields.Boolean(string="Security Incidents / Breaches?", tracking=True)
    it_incidents_or_breaches_comment = fields.Text(string="Incident / Breach Commentary", tracking=True)
    it_system_generated_reports_locked = fields.Boolean(string="System Reports Locked?", tracking=True)
    it_system_generated_reports_locked_comment = fields.Text(string="System Reports Comment", tracking=True)
    it_manual_interfaces_used = fields.Boolean(string="Manual Interfaces Used?", tracking=True)
    it_manual_interfaces_used_comment = fields.Text(string="Manual Interface Commentary", tracking=True)
    it_attachment_ids = fields.Many2many(
        "ir.attachment",
        "qaco_planning_it_attachment_rel",
        "planning_id",
        "attachment_id",
        string="IT Environment Attachments",
        help="Upload IT architecture diagrams, sample reports, and IT policy documents.",
    )

    group_structure_current_year = fields.Text(string="Group Structure (Current Year)", tracking=True)
    material_related_party_transactions = fields.Text(string="Material Related Party Transactions", tracking=True)
    changes_in_shareholding_current_year = fields.Text(string="Shareholding Changes (Current Year)", tracking=True)
    management_oversight_of_related_parties = fields.Text(string="Management Oversight of Related Parties", tracking=True)
    rp_group_structure_updated = fields.Boolean(string="Group Structure Updated?", tracking=True)
    rp_group_structure_updated_comment = fields.Text(string="Group Structure Comment", tracking=True)
    rp_policy_exists = fields.Boolean(string="Related Party Policy Exists?", tracking=True)
    rp_policy_exists_comment = fields.Text(string="Related Party Policy Comment", tracking=True)
    rp_non_commercial_terms = fields.Boolean(string="Non-Commercial Terms Identified?", tracking=True)
    rp_non_commercial_terms_comment = fields.Text(string="Non-Commercial Terms Comment", tracking=True)
    rp_undisclosed_parties_identified = fields.Boolean(string="Undisclosed Related Parties?", tracking=True)
    rp_undisclosed_parties_identified_comment = fields.Text(string="Undisclosed RP Comment", tracking=True)
    rp_attachment_ids = fields.Many2many(
        "ir.attachment",
        "qaco_planning_rp_attachment_rel",
        "planning_id",
        "attachment_id",
        string="Related Party Attachments",
        help="Attach group charts, related party registers, and intra-group agreements.",
    )

    fraud_brainstorming_summary = fields.Text(string="Fraud Brainstorming Summary", tracking=True)
    identified_fraud_risks_ids = fields.One2many(
        "qaco.risk.assessment",
        "planning_id",
        string="Identified Fraud Risks",
        help="Filtered view of risk assessments that capture ISA 240 fraud considerations.",
    )
    management_anti_fraud_controls = fields.Text(string="Management Anti-Fraud Controls", tracking=True)
    risk_of_management_override = fields.Selection(
        [("high", "High"), ("medium", "Medium"), ("low", "Low")],
        string="Risk of Management Override",
        tracking=True,
    )
    override_rationale = fields.Text(string="Override Risk Rationale", tracking=True)
    fraud_mgmt_assessment_obtained = fields.Boolean(string="Management Fraud Assessment Obtained?", tracking=True)
    fraud_mgmt_assessment_comment = fields.Text(string="Management Fraud Assessment Comment", tracking=True)
    fraud_independent_oversight = fields.Boolean(string="Independent Oversight Present?", tracking=True)
    fraud_independent_oversight_comment = fields.Text(string="Oversight Comment", tracking=True)
    fraud_known_or_suspected = fields.Boolean(string="Known / Suspected Fraud?", tracking=True)
    fraud_known_or_suspected_comment = fields.Text(string="Known / Suspected Fraud Comment", tracking=True)
    fraud_pressure_opportunity_rationalization = fields.Boolean(string="Pressure / Opportunity / Rationalization Present?", tracking=True)
    fraud_pressure_opportunity_rationalization_comment = fields.Text(string="Fraud Triangle Comment", tracking=True)
    fraud_attachment_ids = fields.Many2many(
        "ir.attachment",
        "qaco_planning_fraud_attachment_rel",
        "planning_id",
        "attachment_id",
        string="Fraud Documentation Attachments",
        help="Attach brainstorming minutes, whistleblowing policies, and investigation reports.",
    )

    # Client permanent information (read-only snapshots)
    client_legal_name = fields.Char(related="client_id.legal_name", string="Legal Name", readonly=True)
    client_trade_name = fields.Char(related="client_id.trade_name", string="Trade Name", readonly=True)
    client_incorporation_no = fields.Char(related="client_id.incorporation_no", string="Incorporation No.", readonly=True)
    client_incorporation_date = fields.Date(related="client_id.incorporation_date", string="Incorporation Date", readonly=True)
    client_legal_form = fields.Selection(
        related="client_id.legal_form",
        string="Legal Form",
        readonly=True,
    )
    client_shareholding_ids = fields.One2many(
        related="client_id.shareholding_structure_ids",
        string="Shareholding Structure",
        readonly=True,
    )
    client_group_structure_permanent = fields.Text(
        related="client_id.group_structure_permanent",
        string="Group Structure (Permanent)",
        readonly=True,
    )
    client_group_structure_attachment_ids = fields.Many2many(
        related="client_id.group_structure_attachment_ids",
        string="Group Attachments",
        readonly=True,
    )
    client_ntn = fields.Char(related="client_id.ntn", string="NTN", readonly=True)
    client_strn = fields.Char(related="client_id.strn", string="STRN", readonly=True)
    client_st_reg_province = fields.Char(related="client_id.st_reg_province", string="Sales Tax Province", readonly=True)
    client_eobi_registration_no = fields.Char(related="client_id.eobi_registration_no", string="EOBI #", readonly=True)
    client_social_security_registration_no = fields.Char(
        related="client_id.social_security_registration_no",
        string="Social Security #",
        readonly=True,
    )
    client_license_ids = fields.One2many(
        related="client_id.license_ids",
        string="Regulatory Licenses",
        readonly=True,
    )
    client_permanent_reporting_framework = fields.Selection(
        related="client_id.permanent_reporting_framework",
        string="Permanent Reporting Framework",
        readonly=True,
    )
    client_year_end_permanent = fields.Date(
        related="client_id.permanent_year_end",
        string="Year End",
        readonly=True,
    )
    client_primary_erp_permanent = fields.Char(
        related="client_id.primary_erp_permanent",
        string="Primary ERP (Permanent)",
        readonly=True,
    )
    client_other_systems_permanent = fields.Text(
        related="client_id.other_systems_permanent",
        string="Other Systems (Permanent)",
        readonly=True,
    )
    client_permanent_business_description = fields.Text(
        related="client_id.permanent_business_description",
        string="Business Description (Permanent)",
        readonly=True,
    )
    client_permanent_revenue_streams = fields.Text(
        related="client_id.permanent_revenue_streams",
        string="Revenue Streams (Permanent)",
        readonly=True,
    )
    client_main_locations = fields.Text(
        related="client_id.main_locations",
        string="Main Locations",
        readonly=True,
    )
    client_permanent_key_processes = fields.Text(
        related="client_id.permanent_key_processes",
        string="Key Processes",
        readonly=True,
    )
    client_permanent_policies_attachment_ids = fields.Many2many(
        related="client_id.permanent_policies_attachment_ids",
        string="Permanent Policy Attachments",
        readonly=True,
    )
    client_law_mapping_ids = fields.One2many(
        related="client_id.client_law_mapping_ids",
        string="Client Law Mapping",
        readonly=False,
    )

    # Team
    partner_id = fields.Many2one("res.users", string="Engagement Partner", tracking=True)
    manager_id = fields.Many2one("res.users", string="Engagement Manager", tracking=True)
    team_ids = fields.Many2many("res.users", string="Engagement Team")

    # Timeline
    planning_start_date = fields.Date(string='Planning Start Date', tracking=True)
    planning_end_date = fields.Date(string='Planning End Date', tracking=True)
    fieldwork_start_date = fields.Date(string='Fieldwork Start Date', tracking=True)
    fieldwork_end_date = fields.Date(string='Fieldwork End Date', tracking=True)
    estimated_hours = fields.Float(string='Estimated Hours', tracking=True)

    # Related records
    materiality_ids = fields.One2many("qaco.materiality", "planning_id", string="Materiality Worksheets")
    risk_ids = fields.One2many("qaco.planning.risk", "planning_id", string="Identified Risks")
    risk_assessment_ids = fields.One2many("qaco.risk.assessment", "planning_id", string="Risk Assessments")
    checklist_ids = fields.One2many("qaco.planning.checklist", "planning_id", string="Planning Checklist")
    pbc_ids = fields.One2many("qaco.planning.pbc", "planning_id", string="Information Requisitions")
    milestone_ids = fields.One2many("qaco.planning.milestone", "planning_id", string="Timeline")
    evidence_log_ids = fields.One2many(
        "qaco.planning.evidence",
        "planning_id",
        string="Evidence Log",
    )

    # Progress tracking
    checklist_total = fields.Integer(compute="_compute_progress", store=True)
    checklist_done = fields.Integer(compute="_compute_progress", store=True)
    progress = fields.Integer(string="Progress %", compute="_compute_progress", store=True)
    materiality_ready = fields.Boolean(string="Materiality Documented", default=False, tracking=True)
    risk_register_ready = fields.Boolean(string="Risk Register Complete", default=False, tracking=True)
    pbc_sent = fields.Boolean(string="Information Requests Sent", default=False, tracking=True)
    staffing_signed_off = fields.Boolean(string="Staffing Signed Off", default=False, tracking=True)
    materiality_count = fields.Integer(compute="_compute_counts", string="Materiality")
    risk_count = fields.Integer(compute="_compute_counts", string="Risk Count")
    risk_assessment_count = fields.Integer(compute="_compute_counts", string="Risk Assessments")
    significant_risk_count = fields.Integer(compute="_compute_counts", string="Significant Risks")
    pbc_count = fields.Integer(compute="_compute_counts", string="Information Requisitions")
    pbc_received_count = fields.Integer(compute="_compute_counts", string="Requests Received")
    milestone_count = fields.Integer(compute="_compute_counts", string="Milestones")
    timeline_count = fields.Integer(compute="_compute_counts", string="Timeline Tasks")
    
    # Documents & Notes
    planning_notes = fields.Html(string='Planning Notes')
    planning_attachments = fields.Many2many(
        'ir.attachment', 
        'planning_phase_attachment_rel',
        'planning_id', 
        'attachment_id',
        string='Planning Documents'
    )
    audit_committee_briefing = fields.Html(string="Audit Committee Briefing Notes")
    secp_export_payload = fields.Binary(string="SECP Export Package", attachment=True, readonly=True)
    
    # UI helpers
    active = fields.Boolean(default=True, tracking=True)
    color = fields.Integer(
        string="Color Index",
        compute="_compute_color_index",
        store=True,
    )

    @api.depends("checklist_ids.done")
    def _compute_progress(self):
        for rec in self:
            total = len(rec.checklist_ids)
            done = sum(1 for c in rec.checklist_ids if c.done)
            rec.checklist_total = total
            rec.checklist_done = done
            rec.progress = int((done / total) * 100) if total else 0

    @api.depends("entity_classification")
    def _compute_committee_required(self):
        for rec in self:
            rec.audit_committee_required = rec.entity_classification in {"public_listed", "public_unlisted"}

    @api.depends(
        "materiality_ids",
        "risk_ids",
        "risk_ids.significant",
        "pbc_ids",
        "pbc_ids.received",
        "milestone_ids",
    )
    def _compute_counts(self):
        for rec in self:
            rec.materiality_count = len(rec.materiality_ids)
            rec.risk_count = len(rec.risk_ids)
            rec.risk_assessment_count = len(rec.risk_assessment_ids)
            rec.significant_risk_count = sum(1 for r in rec.risk_ids if r.significant)
            rec.pbc_count = len(rec.pbc_ids)
            rec.pbc_received_count = sum(1 for p in rec.pbc_ids if p.received)
            rec.milestone_count = len(rec.milestone_ids)
            rec.timeline_count = rec.milestone_count

    @api.depends(
        "materiality_base_amount",
        "materiality_percentage",
        "overall_materiality_override",
        "overall_materiality_amount_override",
        "performance_materiality_percentage",
        "performance_materiality_override",
        "performance_materiality_amount_override",
        "trivial_threshold_percentage",
        "trivial_threshold_override",
        "trivial_threshold_amount_override",
    )
    def _compute_materiality_amounts(self):
        for rec in self:
            base = rec.materiality_base_amount or 0.0
            perc = rec.materiality_percentage or 0.0
            calc_overall = base * perc / 100.0 if base and perc else 0.0
            rec.overall_materiality_amount_calc = calc_overall
            effective_overall = calc_overall
            if rec.overall_materiality_override and rec.overall_materiality_amount_override:
                effective_overall = rec.overall_materiality_amount_override
            rec.materiality_amount = effective_overall

            perf_perc = rec.performance_materiality_percentage or 0.0
            perf_calc = effective_overall * perf_perc / 100.0 if effective_overall and perf_perc else 0.0
            rec.performance_materiality_amount_calc = perf_calc
            effective_perf = perf_calc
            if rec.performance_materiality_override and rec.performance_materiality_amount_override:
                effective_perf = rec.performance_materiality_amount_override
            rec.performance_materiality = effective_perf

            trivial_perc = rec.trivial_threshold_percentage or 0.0
            trivial_calc = effective_overall * trivial_perc / 100.0 if effective_overall and trivial_perc else 0.0
            rec.trivial_threshold_amount_calc = trivial_calc
            effective_trivial = trivial_calc
            if rec.trivial_threshold_override and rec.trivial_threshold_amount_override:
                effective_trivial = rec.trivial_threshold_amount_override
            rec.trivial_misstatement = effective_trivial
            rec.clearly_trivial_threshold = effective_trivial

    @api.depends(
        "materiality_basis",
        "materiality_base_amount",
        "materiality_benchmark_rationale",
        "materiality_amount",
        "performance_materiality",
        "trivial_misstatement",
        "chk_benchmark_selected_and_justified",
        "chk_overall_materiality_approved",
        "chk_trivial_threshold_set_and_communicated",
    )
    def _compute_materiality_tab_complete(self):
        for rec in self:
            rec.materiality_tab_complete = bool(
                rec.materiality_basis
                and rec.materiality_base_amount
                and rec.materiality_benchmark_rationale
                and rec.materiality_amount
                and rec.performance_materiality
                and rec.trivial_misstatement
                and rec.chk_benchmark_selected_and_justified
                and rec.chk_overall_materiality_approved
                and rec.chk_trivial_threshold_set_and_communicated
            )

    @api.constrains(
        'overall_materiality_override',
        'overall_materiality_amount_override',
        'overall_materiality_override_reason',
        'performance_materiality_override',
        'performance_materiality_amount_override',
        'performance_materiality_override_reason',
        'trivial_threshold_override',
        'trivial_threshold_amount_override',
        'trivial_threshold_override_reason',
    )
    def _check_materiality_overrides(self):
        for rec in self:
            if rec.overall_materiality_override and (
                not rec.overall_materiality_amount_override or not rec.overall_materiality_override_reason
            ):
                raise ValidationError(_("Provide both amount and rationale when overriding overall materiality."))
            if rec.performance_materiality_override and (
                not rec.performance_materiality_amount_override or not rec.performance_materiality_override_reason
            ):
                raise ValidationError(_("Provide both amount and rationale when overriding performance materiality."))
            if rec.trivial_threshold_override and (
                not rec.trivial_threshold_amount_override or not rec.trivial_threshold_override_reason
            ):
                raise ValidationError(_("Provide both amount and rationale when overriding the clearly trivial threshold."))

    @api.constrains('materiality_amount', 'performance_materiality', 'trivial_misstatement')
    def _check_materiality_relationships(self):
        for rec in self:
            overall_amt = rec.materiality_amount or 0.0
            perf_amt = rec.performance_materiality or 0.0
            trivial_amt = rec.trivial_misstatement or 0.0
            currency = rec.currency_id or rec.env.company.currency_id
            rounding = currency.rounding if currency else 0.01
            if perf_amt and overall_amt and perf_amt - overall_amt > rounding:
                raise ValidationError(_("Performance materiality cannot exceed overall materiality."))
            if trivial_amt and perf_amt and trivial_amt - perf_amt > rounding:
                raise ValidationError(_("Clearly trivial threshold cannot exceed performance materiality."))

    def _log_evidence(self, name, action_type, note, standard_reference, **kwargs):
        self.ensure_one()
        self.env["qaco.planning.evidence"].log_event(
            name=name,
            planning_id=self.id,
            model_name=self._name,
            res_id=self.id,
            action_type=action_type,
            note=note,
            standard_reference=standard_reference,
            **kwargs,
        )

    @api.constrains('planning_start_date', 'planning_end_date')
    def _check_planning_dates(self):
        """Validate planning dates"""
        for rec in self:
            if rec.planning_start_date and rec.planning_end_date:
                if rec.planning_end_date < rec.planning_start_date:
                    raise ValidationError(_("Planning end date must be after start date."))

    @api.constrains('fieldwork_start_date', 'fieldwork_end_date')
    def _check_fieldwork_dates(self):
        """Validate fieldwork dates"""
        for rec in self:
            if rec.fieldwork_start_date and rec.fieldwork_end_date:
                if rec.fieldwork_end_date < rec.fieldwork_start_date:
                    raise ValidationError(_("Fieldwork end date must be after start date."))

    @api.onchange('materiality_basis')
    def _onchange_materiality_basis(self):
        """Keep legacy materiality_base in sync for backward compatibility."""
        if self.materiality_basis:
            self.materiality_base = self.materiality_basis

    @api.onchange('materiality_basis', 'materiality_base_amount')
    def _onchange_materiality_warning(self):
        if self.materiality_basis == 'profit_before_tax':
            base = self.materiality_base_amount or 0.0
            if base <= 0:
                return {
                    'warning': {
                        'title': _('Benchmark review'),
                        'message': _('Profit before tax is negative or insignificant. Consider using revenue, assets, or another benchmark in line with ISA 320.'),
                    }
                }

    def action_start(self):
        self.write({'state': 'in_progress'})
    
    def action_start_planning(self):
        """Legacy method compatibility"""
        return self.action_start()

    def action_submit_review(self):
        for rec in self:
            if rec.progress < 70:
                raise ValidationError(_("Complete at least 70% of the checklist before submitting for review."))
            if not rec.materiality_ids:
                raise ValidationError(_("Add at least one materiality worksheet before submitting for review."))
            rec.state = "review"

    def action_approve(self):
        for rec in self:
            # Validation checks
            if any(r.significant and not r.response for r in rec.risk_ids):
                raise ValidationError(_("All significant risks must have a planned audit response."))
            if not rec.engagement_letter_obtained and not rec.engagement_letter_signed:
                raise ValidationError(_("Engagement letter must be obtained before approval."))
            if not rec.independence_confirmed:
                raise ValidationError(_("Independence must be confirmed before approval."))
            rec.state = "approved"

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    def action_view_risks(self):
        """Smart button: View all risks"""
        self.ensure_one()
        return {
            'name': _('Identified Risks'),
            'type': 'ir.actions.act_window',
            'res_model': 'qaco.planning.risk',
            'view_mode': 'tree,form',
            'domain': [('planning_id', '=', self.id)],
            'context': {
                'default_planning_id': self.id,
                'search_default_planning_id': self.id,
            },
        }

    def action_view_risk_assessments(self):
        """Smart button: View ISA 315 risk assessments"""
        self.ensure_one()
        return {
            'name': _('Risk Assessments'),
            'type': 'ir.actions.act_window',
            'res_model': 'qaco.risk.assessment',
            'view_mode': 'tree,form',
            'domain': [('planning_id', '=', self.id)],
            'context': {
                'default_planning_id': self.id,
                'search_default_planning_id': self.id,
            },
        }

    def action_view_significant_risks(self):
        """Smart button: View significant risks only"""
        self.ensure_one()
        return {
            'name': _('Significant Risks'),
            'type': 'ir.actions.act_window',
            'res_model': 'qaco.planning.risk',
            'view_mode': 'tree,form',
            'domain': [('planning_id', '=', self.id), ('significant', '=', True)],
            'context': {
                'default_planning_id': self.id,
                'default_significant': True,
                'search_default_significant': 1,
            },
        }

    def action_view_pbc(self):
        """Smart button: View client information requisitions"""
        self.ensure_one()
        return {
            'name': _('Information Requisitions'),
            'type': 'ir.actions.act_window',
            'res_model': 'qaco.planning.pbc',
            'view_mode': 'tree,form',
            'domain': [('planning_id', '=', self.id)],
            'context': {
                'default_planning_id': self.id,
                'search_default_planning_id': self.id,
            },
        }

    def action_view_milestones(self):
        """Smart button: View milestones"""
        self.ensure_one()
        return {
            'name': _('Timeline & Milestones'),
            'type': 'ir.actions.act_window',
            'res_model': 'qaco.planning.milestone',
            'view_mode': 'tree,form',
            'domain': [('planning_id', '=', self.id)],
            'context': {
                'default_planning_id': self.id,
                'search_default_planning_id': self.id,
            },
        }

    def action_view_materiality(self):
        self.ensure_one()
        return {
            'name': _('Materiality Worksheets'),
            'type': 'ir.actions.act_window',
            'res_model': 'qaco.materiality',
            'view_mode': 'tree,form',
            'domain': [('planning_id', '=', self.id)],
            'context': {'default_planning_id': self.id},
        }

    def action_accept_planning(self):
        for rec in self:
            if not rec.independence_confirmed or rec.independence_questionnaire_result == 'block':
                raise ValidationError(_("Independence questionnaire must be clean before acceptance (ISA 300 para 7)."))
            if not rec.engagement_letter_obtained:
                raise ValidationError(_("Mark the engagement letter as obtained before acceptance."))
            rec.acceptance_state = 'accepted'
            rec._bootstrap_planning_pack()
            rec._log_evidence(
                name=_('Engagement accepted'),
                action_type='state',
                note=rec.acceptance_rationale or _('Acceptance rationale captured.'),
                standard_reference='ISA 300 para 7; SECP Guide section 2',
            )

    def _bootstrap_planning_pack(self):
        for rec in self:
            if rec.materiality_ids:
                continue
            config = self.env['qaco.planning.materiality.config'].search(
                ['|', ('entity_classification', '=', rec.entity_classification), ('entity_classification', '=', 'other')],
                limit=1,
            )
            default_basis = config.default_basis if config else 'pbt'
            pct_map = {
                'pbt': config.default_pct_pbt if config else 5.0,
                'revenue': config.default_pct_revenue if config else 1.0,
                'assets': config.default_pct_assets if config else 1.5,
                'equity': config.default_pct_equity if config else 3.0,
            }
            applied_pct = pct_map.get(default_basis, 5.0)
            performance_pct = (config.performance_factor if config else 0.75) * 100.0
            self.env['qaco.materiality'].create(
                {
                    'planning_id': rec.id,
                    'audit_id': rec.audit_id.id if rec.audit_id else False,
                    'benchmark_type': default_basis if default_basis in pct_map else 'pbt',
                    'benchmark_amount': 0.0,
                    'currency_id': rec.currency_id.id,
                    'base_source_type': 'manual',
                    'applied_percent': applied_pct,
                    'performance_percent': performance_pct,
                    'trivial_percent': 5.0,
                    'rationale': _('Default planning pack generated (ISA 320 para 10). Update base figures from TB snapshot.'),
                    'prepared_by': self.env.user.id,
                }
            )
            rec._generate_default_pbc_items()
            rec._generate_default_milestones()

    def _generate_default_pbc_items(self):
        template_model = self.env['qaco.planning.pbc.template']
        for rec in self:
            templates = template_model.search(
                [('entity_classification', '=', rec.entity_classification)],
                order="sequence_ref asc, id asc",
            )
            if not templates:
                templates = template_model.search(
                    [('entity_classification', '=', 'other')],
                    order="sequence_ref asc, id asc",
                )
            client_contact = rec.client_partner_id or rec.client_id
            default_due_date = rec.reporting_period_end or fields.Date.context_today(self)
            for template in templates:
                values = {
                    'planning_id': rec.id,
                    'name': template.name,
                    'description': template.description,
                    'category': template.category,
                    'delivery_status': 'not_requested',
                    'requested_date': fields.Date.context_today(self),
                    'due_date': default_due_date,
                    'client_contact': client_contact.name if client_contact else False,
                    'client_contact_id': client_contact.id if client_contact else False,
                    'priority': template.priority,
                    'expected_format': template.format_expected,
                    'format_detail': template.format_detail,
                    'information_heading': template.information_heading,
                    'sequence_ref': template.sequence_ref,
                    'responsible_role': template.responsible_role,
                    'applicable': True,
                }
                self.env['qaco.planning.pbc'].create(values)

    def _generate_default_milestones(self):
        for rec in self:
            start = rec.reporting_period_start or fields.Date.context_today(self)
            milestones = [
                ('Planning Memorandum', start),
                ('Risk Workshops', start),
                ('Audit Committee Briefing', rec.reporting_period_end or start),
            ]
            for name, milestone_date in milestones:
                self.env['qaco.planning.milestone'].create(
                    {
                        'planning_id': rec.id,
                        'name': name,
                        'date': milestone_date,
                        'owner_id': rec.manager_id.id or rec.partner_id.id,
                    }
                )

    def action_export_planning_memorandum(self):
        self.ensure_one()
        report = self.env.ref('qaco_planning_phase.report_planning_memorandum', raise_if_not_found=False)
        if not report:
            raise ValidationError(_('Planning memorandum report is not configured.'))
        return report.report_action(self)

    def action_export_secp_package(self):
        self.ensure_one()
        payload = {
            'planning': self.name,
            'client': self.client_id.display_name if self.client_id else '',
            'entity_class': self.entity_classification,
            'materiality': [
                {
                    'benchmark': m.benchmark_type,
                    'overall': float(m.materiality_amount or 0.0),
                    'performance': float(m.performance_materiality_amount or 0.0),
                    'trivial': float(m.trivial_amount or 0.0),
                }
                for m in self.materiality_ids
            ],
            'risks': [
                {
                    'name': r.name,
                    'rating': r.risk_score,
                    'response': r.response_detail or r.response,
                }
                for r in self.risk_ids if r.significant
            ],
        }
        attachment = self.env['ir.attachment'].create(
            {
                'name': f'SECP-package-{self.name}.json',
                'datas': base64.b64encode(json.dumps(payload, default=str).encode()).decode(),
                'res_model': self._name,
                'res_id': self.id,
            }
        )
        self.secp_export_payload = attachment.datas
        self._log_evidence(
            name=_('SECP export'),
            action_type='export',
            note=_('SECP / PSX export generated for regulator submission.'),
            standard_reference='SECP Guide section 5; PSX ToR section 8',
        )
        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content/{attachment.id}?download=true",
            'target': 'self',
        }

    def action_mark_ready_for_fieldwork(self):
        for rec in self:
            if not all([rec.materiality_ready, rec.risk_register_ready, rec.pbc_sent, rec.staffing_signed_off]):
                raise ValidationError(_("Materiality, risk register, information requisitions and staffing sign-off must be complete before fieldwork."))
            rec.state = 'fieldwork'
            rec._log_evidence(
                name=_('Planning complete'),
                action_type='state',
                note=_('Planning phase sign-offs completed.'),
                standard_reference='ISA 300 para 13',
            )

    def action_trigger_independence_escalation(self):
        for rec in self:
            if rec.independence_questionnaire_result != 'review':
                continue
            if not rec.qcr_contact_id:
                raise ValidationError(_("Assign a QCR / ethics contact before escalation."))
            rec.acceptance_state = 'awaiting_clearance'
            rec._log_evidence(
                name=_('Independence escalation'),
                action_type='state',
                note=_('Routed to QCR contact per ICAP ethics guidance.'),
                standard_reference='ICAP ethics guidance section 2',
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._sync_materiality_vals(vals)
            self._sync_ic_strategy_vals(vals)
        records = super().create(vals_list)
        # Auto-seed ISA-oriented checklist
        for rec in records:
            if not rec.checklist_ids:
                rec._create_default_checklist()
        return records

    def write(self, vals):
        vals = dict(vals)
        if 'overall_ic_assessment' in vals:
            self._sync_ic_strategy_vals(vals)
        if not self.env.context.get('skip_materiality_autofill'):
            self._sync_materiality_vals(vals)
        return super().write(vals)

    def _sync_materiality_vals(self, vals):
        base = vals.get('materiality_base')
        legacy = vals.get('materiality_basis')
        if base and not legacy:
            vals['materiality_basis'] = base
        elif legacy and not base:
            vals['materiality_base'] = legacy

    def _sync_ic_strategy_vals(self, vals):
        assessment = vals.get('overall_ic_assessment')
        if not assessment or vals.get('toc_strategy'):
            return
        strategy = self._determine_toc_strategy(assessment)
        if strategy:
            vals['toc_strategy'] = strategy

    @staticmethod
    def _determine_toc_strategy(assessment):
        if assessment in ('does_not_exist', 'weak'):
            return 'no_toc'
        if assessment in ('moderate', 'strong'):
            return 'perform_toc'
        return False

    @api.onchange('overall_ic_assessment')
    def _onchange_overall_ic_assessment(self):
        self.toc_strategy = self._determine_toc_strategy(self.overall_ic_assessment)

    @api.constrains('overall_ic_assessment', 'toc_strategy')
    def _check_ic_strategy_alignment(self):
        for rec in self:
            if not rec.overall_ic_assessment or not rec.toc_strategy:
                continue
            expected = rec._determine_toc_strategy(rec.overall_ic_assessment)
            if expected and rec.toc_strategy != expected:
                raise ValidationError(_(
                    "The selected Tests of Controls strategy contradicts the internal control assessment per ISA 330."))

    def _create_default_checklist(self):
        """Create standard ISA-aligned checklist items"""
        self.ensure_one()
        
        checklist_items = [
            # ISA 210/220/IESBA - Acceptance & Ethics
            {
                "section": "acceptance",
                "description": "Obtain and review signed engagement letter with agreed terms",
                "isa_ref": "ISA 210.10",
                "sequence": 10,
            },
            {
                "section": "acceptance",
                "description": "Confirm independence of engagement team members",
                "isa_ref": "IESBA Code",
                "sequence": 20,
            },
            {
                "section": "acceptance",
                "description": "Document compliance with ethical requirements",
                "isa_ref": "ISA 220.11",
                "sequence": 30,
            },
            
            # ISA 300 - Planning
            {
                "section": "strategy",
                "description": "Define overall audit strategy including scope, timing, and direction",
                "isa_ref": "ISA 300.7",
                "sequence": 40,
            },
            {
                "section": "strategy",
                "description": "Determine nature and extent of resources needed for the engagement",
                "isa_ref": "ISA 300.8",
                "sequence": 50,
            },
            {
                "section": "strategy",
                "description": "Assign engagement team roles and plan supervision/review",
                "isa_ref": "ISA 300.8",
                "sequence": 60,
            },
            
            # ISA 315 - Risk Assessment
            {
                "section": "risk",
                "description": "Obtain understanding of entity, its environment, and applicable financial reporting framework",
                "isa_ref": "ISA 315.11",
                "sequence": 70,
            },
            {
                "section": "risk",
                "description": "Understand internal controls relevant to the audit",
                "isa_ref": "ISA 315.12",
                "sequence": 80,
            },
            {
                "section": "risk",
                "description": "Identify and assess risks of material misstatement at financial statement and assertion levels",
                "isa_ref": "ISA 315.25",
                "sequence": 90,
            },
            {
                "section": "risk",
                "description": "Determine significant risks requiring special audit consideration",
                "isa_ref": "ISA 315.27",
                "sequence": 100,
            },
            
            # ISA 320 - Materiality
            {
                "section": "materiality",
                "description": "Determine overall materiality for financial statements as a whole",
                "isa_ref": "ISA 320.10",
                "sequence": 110,
            },
            {
                "section": "materiality",
                "description": "Determine performance materiality",
                "isa_ref": "ISA 320.11",
                "sequence": 120,
            },
            {
                "section": "materiality",
                "description": "Set threshold for trivial misstatements",
                "isa_ref": "ISA 320.14",
                "sequence": 130,
            },
            
            # ISA 240 - Fraud
            {
                "section": "fraud",
                "description": "Conduct engagement team discussion on fraud risks",
                "isa_ref": "ISA 240.15",
                "sequence": 140,
            },
            {
                "section": "fraud",
                "description": "Make inquiries of management regarding fraud risk assessment",
                "isa_ref": "ISA 240.17",
                "sequence": 150,
            },
            {
                "section": "fraud",
                "description": "Identify and assess risks of material misstatement due to fraud",
                "isa_ref": "ISA 240.25",
                "sequence": 160,
            },
            {
                "section": "fraud",
                "description": "Presume risk of fraud in revenue recognition",
                "isa_ref": "ISA 240.26",
                "sequence": 170,
            },
        ]
        
        owner_id = self.partner_id.id or self.env.user.id
        self.checklist_ids = [(0, 0, {**item, "owner_id": owner_id}) for item in checklist_items]


class MaterialitySpecific(models.Model):
    _name = "qaco.materiality.specific"
    _description = "Specific Materiality Consideration"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    planning_id = fields.Many2one(
        "qaco.planning.phase",
        required=True,
        ondelete="cascade",
    )
    specific_area = fields.Char(string="Area / Disclosure", required=True)
    specific_reason = fields.Text(string="Reason / Sensitivity", required=True)
    specific_base_amount = fields.Monetary(
        string="Base Amount",
        currency_field="currency_id",
        help="Amount used to derive the specific materiality (e.g., related party balance).",
    )
    specific_percentage = fields.Float(
        string="Percentage (%)",
        help="Override percentage applied to the base amount.",
    )
    specific_amount_calc = fields.Monetary(
        string="Specific Materiality",
        currency_field="currency_id",
        compute="_compute_specific_amount",
        store=True,
        readonly=True,
    )
    specific_standard_reference = fields.Char(
        string="Standard / Regulation Reference",
        help="Examples: ISA 320, ISA 450, SECP, SBP, donor agreement, etc.",
    )
    supporting_notes = fields.Text(string="Notes / Procedures")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="planning_id.currency_id",
        store=True,
        readonly=True,
    )

    @api.depends('specific_base_amount', 'specific_percentage')
    def _compute_specific_amount(self):
        for rec in self:
            base = rec.specific_base_amount or 0.0
            perc = rec.specific_percentage or 0.0
            rec.specific_amount_calc = (base * perc / 100.0) if base and perc else 0.0


class PlanningRisk(models.Model):
    _name = "qaco.planning.risk"
    _description = "Identified Risk (ISA 315/240)"
    _order = "risk_score desc, id desc"

    planning_id = fields.Many2one("qaco.planning.phase", required=True, ondelete="cascade")
    name = fields.Char(
        required=True,
        string="Risk Description",
        default=lambda self: self._generate_default_name(),
    )
    business_area = fields.Selection([
        ("revenue", "Revenue"),
        ("inventory", "Inventory"),
        ("receivables", "Receivables"),
        ("payables", "Payables"),
        ("cash", "Cash & Equivalents"),
        ("estimates", "Accounting Estimates"),
        ("disclosures", "Disclosures"),
        ("other", "Other"),
    ], string="Business Area")
    
    # Risk classification
    risk_type = fields.Selection([
        ("fraud", "Fraud Risk (ISA 240)"),
        ("significant", "Significant Risk (ISA 315)"),
        ("routine", "Routine Risk"),
    ], default="routine", required=True)
    
    assertion = fields.Selection([
        ("occurrence", "Occurrence"),
        ("existence", "Existence"),
        ("completeness", "Completeness"),
        ("rights", "Rights & Obligations"),
        ("valuation", "Valuation / Allocation"),
        ("presentation", "Presentation & Disclosure"),
        ("cutoff", "Cut-off"),
        ("accuracy", "Accuracy"),
    ], string="Assertion Affected")
    
    account_area = fields.Selection([
        ("revenue", "Revenue"),
        ("inventory", "Inventory"),
        ("receivables", "Receivables"),
        ("payables", "Payables"),
        ("ppe", "Property, Plant & Equipment"),
        ("intangibles", "Intangibles"),
        ("investments", "Investments"),
        ("debt", "Debt & Financing"),
        ("equity", "Equity"),
        ("tax", "Taxation"),
        ("provisions", "Provisions"),
        ("other", "Other"),
    ], string="Account Area")
    
    # Risk assessment
    likelihood = fields.Selection([
        ("1", "Low"),
        ("2", "Medium"),
        ("3", "High"),
    ], default="2", required=True)
    impact = fields.Selection([
        ("1", "Low"),
        ("2", "Medium"),
        ("3", "High"),
    ], default="2", required=True)
    inherent_risk_level = fields.Integer(string="Inherent Risk (1-5)", default=3)
    control_risk_level = fields.Integer(string="Control Risk (1-5)", default=3)
    detection_risk_level = fields.Integer(string="Detection Risk", compute="_compute_score", store=True)
    overall_risk = fields.Selection([
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("very_high", "Very High"),
    ], compute="_compute_score", store=True)
    risk_score = fields.Integer(compute="_compute_score", store=True, string="Risk Rating")
    significant = fields.Boolean(string="Significant Risk")
    
    # Audit response
    response = fields.Selection([
        ("substantive", "Substantive Procedures Only"),
        ("controls", "Tests of Controls"),
        ("combined", "Combined Approach"),
    ], string="Planned Response")
    response_detail = fields.Text(string="Detailed Response")
    planned_substantive_procedures = fields.Text(string="Planned Substantive Procedures")
    planned_control_tests = fields.Text(string="Planned Control Tests")
    risk_triggers = fields.Text(string="Risk Triggers")
    risk_narrative = fields.Text(string="Risk Narrative")
    isa_ref = fields.Char(string="ISA Reference", help="e.g., ISA 315.27, ISA 240.26")
    notes = fields.Text()
    sign_off_user_id = fields.Many2one("res.users", string="Reviewer")
    sign_off_date = fields.Date()

    @api.model
    def _generate_default_name(self):
        seq = self.env["ir.sequence"].sudo().next_by_code("qaco.planning.risk")
        return seq or _("New Risk")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = self._generate_default_name()
        return super().create(vals_list)

    @api.depends("likelihood", "impact", "inherent_risk_level", "control_risk_level")
    def _compute_score(self):
        for rec in self:
            inherent = rec.inherent_risk_level or int(rec.likelihood or "1")
            control = rec.control_risk_level or int(rec.impact or "1")
            rec.detection_risk_level = max(1, 6 - min(inherent, control))
            rec.risk_score = inherent * control * rec.detection_risk_level
            if rec.risk_score >= 60:
                rec.overall_risk = "very_high"
            elif rec.risk_score >= 36:
                rec.overall_risk = "high"
            elif rec.risk_score >= 18:
                rec.overall_risk = "medium"
            else:
                rec.overall_risk = "low"

    @api.onchange('risk_score')
    def _onchange_risk_score(self):
        """Auto-flag as significant if score is high"""
        if self.risk_score >= 36 and not self.significant:
            return {
                'warning': {
                    'title': _('High Risk Score'),
                    'message': _('This risk has a high score (≥6). Consider marking it as Significant Risk.'),
                }
            }

    @api.constrains('overall_risk', 'risk_triggers', 'planned_substantive_procedures')
    def _check_high_risk_documentation(self):
        for rec in self:
            if rec.overall_risk in ('high', 'very_high'):
                if not rec.risk_triggers or not rec.planned_substantive_procedures:
                    raise ValidationError(_("High/very high risks require triggers and planned procedures (ISA 315 para 32)."))

    def action_sign_off(self):
        self.ensure_one()
        if self.env.user not in (self.planning_id.partner_id, self.planning_id.manager_id):
            raise ValidationError(_('Only the engagement partner or manager can sign-off risks.'))
        self.sign_off_user_id = self.env.user
        self.sign_off_date = fields.Date.context_today(self)
        high_risks = self.planning_id.risk_ids.filtered(lambda r: r.overall_risk in ('high', 'very_high'))
        self.planning_id.risk_register_ready = bool(high_risks)
        self.planning_id._log_evidence(
            name=_('Risk sign-off'),
            action_type='approval',
            note=_('Risk reviewed and response deemed adequate.'),
            standard_reference='ISA 315 para 32',
        )


class PlanningChecklist(models.Model):
    _name = "qaco.planning.checklist"
    _description = "Planning Checklist Item"
    _order = "sequence, id"

    planning_id = fields.Many2one("qaco.planning.phase", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    
    section = fields.Selection([
        ("acceptance", "Acceptance & Ethics"),
        ("strategy", "Overall Strategy"),
        ("materiality", "Materiality"),
        ("risk", "Risk Assessment"),
        ("fraud", "Fraud Considerations"),
    ], required=True, string="Section")
    
    description = fields.Text(required=True)
    isa_ref = fields.Char(string="ISA Reference")
    done = fields.Boolean(string="Completed")
    owner_id = fields.Many2one("res.users", string="Owner", default=lambda self: self.env.user)
    completion_date = fields.Date(string="Completion Date")
    notes = fields.Text()

    @api.onchange('done')
    def _onchange_done(self):
        """Auto-set completion date when marked as done"""
        if self.done and not self.completion_date:
            self.completion_date = fields.Date.today()
        elif not self.done:
            self.completion_date = False


class FinancialReportingSchedule(models.Model):
    _name = "qaco.financial.reporting.schedule"
    _description = "Companies Act Schedule / Reporting Format"
    _order = "code, name"

    name = fields.Char(required=True, string="Schedule / Format")
    code = fields.Char(required=True, string="Reference Code")
    description = fields.Text(string="Usage Notes")
    active = fields.Boolean(default=True)


class PartnerShareholding(models.Model):
    _name = "qaco.partner.shareholding"
    _description = "Client Shareholding Structure"
    _order = "partner_id, sequence, id"

    partner_id = fields.Many2one("res.partner", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    shareholder_name = fields.Char(required=True, string="Shareholder")
    percentage_holding = fields.Float(string="Holding %")
    resident_status = fields.Selection(
        [("resident", "Resident"), ("non_resident", "Non-resident")],
        string="Resident Status",
    )
    remarks = fields.Char(string="Remarks")


class PartnerLicense(models.Model):
    _name = "qaco.partner.license"
    _description = "Client License / Registration"
    _order = "partner_id, license_type, validity_to desc"

    partner_id = fields.Many2one("res.partner", required=True, ondelete="cascade")
    license_type = fields.Char(required=True, string="License Type")
    license_number = fields.Char(string="Number")
    issuing_authority = fields.Char(string="Issuing Authority")
    validity_from = fields.Date(string="Valid From")
    validity_to = fields.Date(string="Valid To")
    notes = fields.Text(string="Notes")
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "qaco_partner_license_attachment_rel",
        "license_id",
        "attachment_id",
        string="License Attachments",
    )


class ResPartner(models.Model):
    _inherit = "res.partner"

   

    is_qaco_client = fields.Boolean(string="QACO Audit Client", help="Flag to show partner on audit planning forms.")
    legal_name = fields.Char(string="Legal Name")
    trade_name = fields.Char(string="Trade Name / Brand")
    incorporation_no = fields.Char(string="Incorporation / Registration No")
    incorporation_date = fields.Date(string="Incorporation Date")
    legal_form = fields.Selection(
        [
            ("private_ltd", "Private Limited"),
            ("public_listed", "Public Listed"),
            ("public_unlisted", "Public Unlisted"),
            ("section_42", "Section 42 / NGO"),
            ("ngo", "NGO / NPO"),
            ("partnership", "Partnership"),
            ("sole_proprietor", "Sole Proprietor"),
            ("other", "Other"),
        ],
        string="Legal Form",
    )
    shareholding_structure_ids = fields.One2many(
        "qaco.partner.shareholding",
        "partner_id",
        string="Shareholding Structure",
    )
    group_structure_permanent = fields.Text(string="Group Structure (Permanent)")
    group_structure_attachment_ids = fields.Many2many(
        "ir.attachment",
        "qaco_partner_group_attachment_rel",
        "partner_id",
        "attachment_id",
        string="Group Attachments",
    )
    ntn = fields.Char(string="NTN")
    strn = fields.Char(string="STRN")
    st_reg_province = fields.Char(string="Sales Tax Province / Authority")
    eobi_registration_no = fields.Char(string="EOBI Registration No")
    social_security_registration_no = fields.Char(string="Social Security / PESSI / SESSI No")
    license_ids = fields.One2many("qaco.partner.license", "partner_id", string="Licenses & Registrations")
    permanent_reporting_framework = fields.Selection(
        [
            ("ifrs_pakistan", "IFRS (Pakistan Companies Act 2017)"),
            ("ias_only", "IAS Only / Legacy"),
            ("cash_basis", "Cash / Fund Accounting"),
            ("special_purpose", "Special Purpose Framework"),
            ("ifrs", "IFRS (Legacy)"),
            ("ifrs_sme", "IFRS for SMEs (Legacy)"),
            ("local_gaap", "Local GAAP (Legacy)"),
            ("other", "Other"),
        ],
        string="Permanent Reporting Framework",
    )
    permanent_year_end = fields.Date(string="Financial Year End")
    primary_erp_permanent = fields.Char(string="Primary ERP / Core System")
    other_systems_permanent = fields.Text(string="Other Enterprise Systems")
    permanent_policies_attachment_ids = fields.Many2many(
        "ir.attachment",
        "qaco_partner_policy_attachment_rel",
        "partner_id",
        "attachment_id",
        string="Permanent Policy Attachments",
    )
    permanent_business_description = fields.Text(string="Business Description (Permanent)")
    permanent_revenue_streams = fields.Text(string="Revenue Streams (Permanent)")
    main_locations = fields.Text(string="Main Operating Locations")
    permanent_key_processes = fields.Text(string="Key Processes / SOPs")
    client_law_mapping_ids = fields.One2many(
        "qaco.client.law.mapping",
        "client_id",
        string="Laws & Regulations Mapping",
    )


class LawMaster(models.Model):
    _name = "qaco.law.master"
    _description = "Law / Regulation Master"
    _order = "law_category, name"

    name = fields.Char(required=True, string="Law / Regulation")
    law_category = fields.Selection(
        [
            ("company_law", "Companies Act / Corporate"),
            ("direct_tax", "Direct Tax"),
            ("indirect_tax", "Indirect / Sales Tax"),
            ("labour", "Labour & Employment"),
            ("sectoral", "Sector-Specific"),
            ("other", "Other"),
        ],
        string="Category",
        default="company_law",
    )
    section_reference = fields.Text(string="Key Sections / Rules")
    checklist_template_id = fields.Many2one(
        "qaco.law.checklist",
        string="Preferred Checklist",
        help="Reference checklist to seed execution testing in later phases.",
        ondelete="set null",
    )
    note = fields.Text(string="Implementation Notes")
    checklist_ids = fields.One2many("qaco.law.checklist", "law_id", string="Checklist Templates")


class LawChecklist(models.Model):
    _name = "qaco.law.checklist"
    _description = "Law Compliance Checklist"
    _order = "name"

    name = fields.Char(required=True, string="Checklist Name")
    law_id = fields.Many2one("qaco.law.master", string="Law / Regulation", ondelete="cascade")
    line_ids = fields.One2many("qaco.law.checklist.line", "checklist_id", string="Checklist Lines")
    reviewer_notes = fields.Text(string="Usage Notes")


class LawChecklistLine(models.Model):
    _name = "qaco.law.checklist.line"
    _description = "Law Checklist Line"
    _order = "sequence, id"

    checklist_id = fields.Many2one("qaco.law.checklist", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    name = fields.Char(required=True, string="Requirement / Clause")
    control_procedure = fields.Text(string="Audit / Compliance Procedure")
    evidence_reference = fields.Char(string="Evidence Reference")


class ClientLawMapping(models.Model):
    _name = "qaco.client.law.mapping"
    _description = "Client Law & Regulation Mapping"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "law_id, compliance_status"

    client_id = fields.Many2one(
        "res.partner",
        string="Client",
        required=True,
        ondelete="cascade",
        domain="[('is_company','=',True)]",
        tracking=True,
    )
    planning_id = fields.Many2one(
        "qaco.planning.phase",
        string="Planning Reference",
        ondelete="set null",
        help="Optional link to the planning file that initiated this mapping entry.",
    )
    law_id = fields.Many2one("qaco.law.master", string="Law / Regulation", required=True, tracking=True)
    applicable = fields.Boolean(string="Applicable", default=True, tracking=True)
    applicability_scope = fields.Selection(
        [
            ("fully", "Fully applicable"),
            ("partially", "Partially applicable"),
            ("not_applicable_this_year", "Not applicable this year"),
        ],
        string="Applicability Scope",
        default="fully",
        tracking=True,
    )
    compliance_owner_id = fields.Many2one("res.users", string="Compliance Owner")
    last_compliance_review_date = fields.Date(string="Last Review Date")
    next_compliance_review_due = fields.Date(string="Next Review Due")
    compliance_status = fields.Selection(
        [
            ("compliant", "Compliant"),
            ("non_compliant", "Non-compliant"),
            ("under_dispute", "Under dispute"),
            ("not_assessed", "Not assessed"),
        ],
        string="Compliance Status",
        default="not_assessed",
        tracking=True,
    )
    key_risks_summary = fields.Text(string="Key Risks / Issues")
    execution_checklist_id = fields.Many2one(
        "qaco.law.checklist",
        string="Execution Checklist",
        help="Manual linkage to detailed execution checklist for fieldwork phase.",
    )
    law_applicability_reviewed = fields.Boolean(string="Applicability Reviewed?", tracking=True)
    law_applicability_reviewed_comment = fields.Text(string="Applicability Comments")
    law_significant_non_compliances = fields.Boolean(string="Significant Non-compliances?", tracking=True)
    law_significant_non_compliances_comment = fields.Text(string="Non-compliance Commentary")
    law_unrecorded_provisions = fields.Boolean(string="Unrecorded Provisions / Contingencies?", tracking=True)
    law_unrecorded_provisions_comment = fields.Text(string="Provision Commentary")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("in_review", "In Review"),
            ("approved", "Approved"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )
    color = fields.Integer(string="Kanban Color")

    def action_approve(self):
        for rec in self:
            rec.state = "approved"

    def action_request_review(self):
        for rec in self:
            rec.state = "in_review"


class PlanningPBC(models.Model):
    _name = "qaco.planning.pbc"
    _description = "Information Requisition"
    _order = "sequence_ref asc, due_date asc, id desc"

    planning_id = fields.Many2one("qaco.planning.phase", required=True, ondelete="cascade")
    name = fields.Char(string="Information Requested", required=True)
    description = fields.Text(string="Description")
    category = fields.Selection([
        ("financial", "Financial Statements"),
        ("tb", "Trial Balance / Ledgers"),
        ("reconciliation", "Reconciliations"),
        ("contracts", "Contracts / Agreements"),
        ("legal", "Legal Documents"),
        ("tax", "Tax Returns / Filings"),
        ("governance", "Governance / Minutes"),
        ("other", "Other"),
    ], string="Category", default="other")
    
    due_date = fields.Date(string="Due Date")
    requested_date = fields.Date(string="Requested Date")
    delivery_status = fields.Selection([
        ("not_requested", "Not Requested"),
        ("requested", "Requested"),
        ("received", "Received"),
        ("incomplete", "Incomplete"),
    ], default="not_requested", tracking=True)
    received = fields.Boolean(string="Received")
    received_date = fields.Date(string="Received Date")
    client_contact = fields.Char(string="Client Contact")
    client_contact_id = fields.Many2one("res.partner", string="Client Contact")
    
    attachment_ids = fields.Many2many("ir.attachment", string="Attachments")
    notes = fields.Text()
    follow_up_log = fields.Html(string="Follow-up Log")
    reminder_count = fields.Integer(default=0)
    shared_with_portal = fields.Boolean(string="Client Portal Access", default=False)
    escalation_level = fields.Selection([
        ("none", "None"),
        ("first", "Manager"),
        ("second", "Partner"),
    ], default="none")
    reminder_log_ids = fields.One2many("qaco.planning.pbc.reminder", "request_id", string="Reminder History")

    @api.onchange('received')
    def _onchange_received(self):
        """Auto-set received date when marked as received"""
        if self.received and not self.received_date:
            self.received_date = fields.Date.today()
        elif not self.received:
            self.received_date = False

    @api.constrains('due_date')
    def _check_overdue(self):
        """Check for overdue information requisitions"""
        today = fields.Date.today()
        for rec in self:
            if rec.due_date and rec.due_date < today and not rec.received:
                # Just a soft check, no error raised
                pass

    def action_request(self):
        for rec in self:
            rec.delivery_status = 'requested'
            rec.requested_date = fields.Date.context_today(self)
            rec.planning_id.pbc_sent = True
            rec.planning_id._log_evidence(
                name=_('Information requisition issued'),
                action_type='state',
                note=rec.description or rec.name,
                standard_reference='ISA 300 para 13; ICAP APM section 7',
            )

    def action_mark_received(self):
        for rec in self:
            rec.delivery_status = 'received'
            rec.received = True
            rec.received_date = fields.Date.context_today(self)
            if not rec.attachment_ids:
                raise ValidationError(_('Attach evidence before marking received.'))
            rec.planning_id._log_evidence(
                name=_('Information requisition received'),
                action_type='update',
                note=_('Evidence attached for requisition.'),
                standard_reference='ISA 300 para 11',
            )

    def action_send_reminder(self, escalation=False):
        template = self.env.ref('qaco_planning_phase.email_template_pbc_reminder', raise_if_not_found=False)
        for rec in self:
            if template:
                template.send_mail(rec.id, force_send=True)
            rec.reminder_count += 1
            if escalation:
                rec.escalation_level = 'second'
            elif rec.reminder_count >= 2:
                rec.escalation_level = 'first'
            self.env['qaco.planning.pbc.reminder'].create(
                {
                    'request_id': rec.id,
                    'reminder_type': 'email',
                    'note': _('Automated reminder dispatched.'),
                }
            )
            rec.planning_id._log_evidence(
                name=_('Information requisition reminder'),
                action_type='reminder',
                note=_('Reminder sent to client contact.'),
                standard_reference='ICAP APM section 7; SECP Guide section 4',
            )

    @api.model
    def cron_escalate_overdue(self):
        escalation_days = int(self.env['ir.config_parameter'].sudo().get_param('qaco_planning.pbc_escalation_days', 3))
        threshold = fields.Date.to_string(fields.Date.context_today(self) - timedelta(days=escalation_days))
        overdue = self.search([
            ('delivery_status', '!=', 'received'),
            ('due_date', '<=', threshold),
        ])
        overdue.action_send_reminder(escalation=True)


class PlanningPbcTemplate(models.Model):
    _name = "qaco.planning.pbc.template"
    _description = "Information Requisition Template"

    name = fields.Char(required=True)
    entity_classification = fields.Selection(ENTITY_CLASSES, required=True)
    information_heading = fields.Char(string="Information Category", required=True)
    sequence_ref = fields.Integer(string="Reference #")
    description = fields.Text()
    responsible_role = fields.Char(string="Responsible Role")
    category = fields.Selection([
        ("financial", "Financial"),
        ("legal", "Legal"),
        ("tax", "Tax"),
        ("governance", "Governance"),
        ("other", "Other"),
    ], default="financial")
    priority = fields.Selection([("low", "Low"), ("normal", "Normal"), ("high", "High")], default="normal")
    format_expected = fields.Selection(
        [("pdf", "PDF"), ("excel", "Excel"), ("word", "Word"), ("other", "Other")],
        default="excel",
    )
    format_detail = fields.Char(string="Format (Display)")


class PlanningPbcReminder(models.Model):
    _name = "qaco.planning.pbc.reminder"
    _description = "Information Requisition Reminder Log"

    request_id = fields.Many2one("qaco.planning.pbc", required=True, ondelete="cascade")
    reminder_type = fields.Selection([
        ("email", "Email"),
        ("call", "Call"),
        ("portal", "Portal"),
    ], default="email")
    reminder_date = fields.Datetime(default=fields.Datetime.now)
    note = fields.Text()


class PlanningMilestone(models.Model):
    _name = "qaco.planning.milestone"
    _description = "Planning Timeline Milestone"
    _order = "date asc, id desc"

    planning_id = fields.Many2one("qaco.planning.phase", required=True, ondelete="cascade")
    name = fields.Char(required=True, string="Milestone")
    date = fields.Date(required=True)
    
    category = fields.Selection([
        ("kickoff", "Kickoff Meeting"),
        ("pbc_due", "Information Requisition Due"),
        ("planning_complete", "Planning Complete"),
        ("fieldwork_start", "Fieldwork Start"),
        ("fieldwork_end", "Fieldwork End"),
        ("review", "Partner Review"),
        ("report", "Report Issuance"),
    ], default="kickoff", string="Type")
    
    completed = fields.Boolean(string="Completed")
    completion_date = fields.Date(string="Actual Completion")
    owner_id = fields.Many2one("res.users", string="Responsible", default=lambda self: self.env.user)
    notes = fields.Text()

    @api.onchange('completed')
    def _onchange_completed(self):
        """Auto-set completion date when marked as completed"""
        if self.completed and not self.completion_date:
            self.completion_date = fields.Date.today()
        elif not self.completed:
            self.completion_date = False


class PlanningIndustrySector(models.Model):
    _name = "planning.industry.sector"
    _description = "Industry Sector"
    _order = "sequence, name"

    name = fields.Char(string="Sector Name", required=True)
    sequence = fields.Integer(string="Sequence", default=10)
    description = fields.Text(string="Description")
    active = fields.Boolean(default=True)
    
    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Industry sector name must be unique!')
    ]


class PlanningEvidenceLog(models.Model):
    _name = "qaco.planning.evidence"
    _description = "Planning Evidence Log"
    _order = "create_date desc"

    name = fields.Char(string="Reference", required=True)
    planning_id = fields.Many2one("qaco.planning.phase", required=True, ondelete="cascade", index=True)
    model_name = fields.Char(string="Model")
    res_id = fields.Integer(string="Record ID")
    field_name = fields.Char(string="Field")
    action_type = fields.Selection([
        ("create", "Create"),
        ("update", "Update"),
        ("state", "State Change"),
        ("approval", "Approval"),
        ("export", "Export"),
        ("reminder", "Reminder"),
    ], required=True)
    before_value = fields.Text(string="Before Snapshot")
    after_value = fields.Text(string="After Snapshot")
    note = fields.Text(string="Justification / Narrative")
    standard_reference = fields.Char(string="Authority Reference")
    user_id = fields.Many2one("res.users", string="Performed By", default=lambda self: self.env.user)
    exported = fields.Boolean(string="Included in Latest Export", default=False)

    @api.model
    def log_event(
        self,
        name,
        planning_id,
        model_name,
        res_id,
        action_type,
        note,
        standard_reference,
        field_name=None,
        before_value=None,
        after_value=None,
    ):
        return self.sudo().create(
            {
                "name": name,
                "planning_id": planning_id,
                "model_name": model_name,
                "res_id": res_id,
                "action_type": action_type,
                "note": note,
                "standard_reference": standard_reference,
                "field_name": field_name,
                "before_value": before_value,
                "after_value": after_value,
            }
        )

    def export_payload(self):
        self.ensure_one()
        return {
            "reference": self.name,
            "model": self.model_name,
            "res_id": self.res_id,
            "action": self.action_type,
            "note": self.note,
            "standard": self.standard_reference,
            "timestamp": fields.Datetime.to_string(self.create_date),
            "user": self.user_id.name,
        }


class PlanningMaterialityConfig(models.Model):
    _name = "qaco.planning.materiality.config"
    _description = "Materiality Configuration"

    name = fields.Char(required=True)
    entity_classification = fields.Selection(ENTITY_CLASSES, required=True)
    default_basis = fields.Selection([
        ("pbt", "Profit before tax"),
        ("revenue", "Revenue"),
        ("assets", "Total assets"),
        ("equity", "Equity"),
    ], default="pbt")
    default_pct_pbt = fields.Float(default=5.0)
    default_pct_revenue = fields.Float(default=1.0)
    default_pct_assets = fields.Float(default=1.5)
    default_pct_equity = fields.Float(default=3.0)
    performance_factor = fields.Float(default=0.75)
    tolerable_factor = fields.Float(default=0.5)




class PlanningMaterialityWizard(models.TransientModel):
    _name = "qaco.planning.materiality.wizard"
    _description = "Materiality Wizard"

    planning_id = fields.Many2one("qaco.planning.phase", required=True)
    benchmark_type = fields.Selection(
        [
            ("pbt", "Profit before tax"),
            ("revenue", "Revenue"),
            ("assets", "Total assets"),
            ("equity", "Equity"),
            ("other", "Other"),
        ],
        required=True,
        default="pbt",
    )
    benchmark_amount = fields.Float(required=True)
    source_type = fields.Selection(
        [
            ("tb_snapshot", "Trial balance snapshot"),
            ("account_move", "Accounting module"),
            ("manual", "Manual entry"),
        ],
        default="manual",
    )
    source_reference = fields.Char()
    applied_percent = fields.Float()
    rationale = fields.Text(required=True)

    def action_apply(self):
        self.ensure_one()
        config = self.env['qaco.planning.materiality.config'].search(
            ['|', ('entity_classification', '=', self.planning_id.entity_classification), ('entity_classification', '=', 'other')],
            limit=1,
        )
        default_pct = 5.0
        if config:
            default_pct = getattr(config, f"default_pct_{self.benchmark_type}", default_pct)
        applied_pct = self.applied_percent or default_pct
        performance_pct = (config.performance_factor if config else 0.75) * 100.0
        materiality = self.env['qaco.materiality'].create(
            {
                'planning_id': self.planning_id.id,
                'audit_id': self.planning_id.audit_id.id if self.planning_id.audit_id else False,
                'benchmark_type': self.benchmark_type,
                'benchmark_amount': self.benchmark_amount,
                'base_source_type': self.source_type,
                'base_source_reference': self.source_reference,
                'currency_id': self.planning_id.currency_id.id,
                'applied_percent': applied_pct,
                'performance_percent': performance_pct,
                'trivial_percent': 5.0,
                'rationale': self.rationale,
                'prepared_by': self.env.user.id,
            }
        )
        if self.env.user == self.planning_id.partner_id:
            materiality.button_approve()
        return materiality


class PlanningSettings(models.TransientModel):
    _inherit = "res.config.settings"

    materiality_performance_factor = fields.Float(
        string="Performance Factor",
        config_parameter="qaco_planning.performance_factor",
        default=0.75,
    )
    pbc_escalation_days = fields.Integer(
        string="Information Requisition Escalation Days",
        config_parameter="qaco_planning.pbc_escalation_days",
        default=3,
    )


class QacoClientProfile(models.Model):
    _name = "qaco.client_profile"
    _description = "Client Profile / KYC"
    _order = "id desc"

    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        required=True,
        ondelete="cascade",
        help="Linked partner",
    )
    legal_name = fields.Char(string="Legal / Registered Name")
    registration_no = fields.Char(string="Registration / Incorporation No.")
    incorporation_date = fields.Date(string="Incorporation Date")
    company_type = fields.Selection(
        [
            ("private", "Private Limited"),
            ("public", "Public Limited"),
            ("partnership", "Partnership"),
            ("ngo", "NGO"),
            ("other", "Other"),
        ],
        string="Company Type",
    )
    sector = fields.Many2one("planning.industry.sector", string="Sector")
    registered_address = fields.Text(string="Registered Address")
    principal_activity = fields.Text(string="Principal Activity")
    risk_rating = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        default="medium",
        string="Client Risk Rating",
    )
    kyc_status = fields.Selection(
        [
            ("not_started", "Not Started"),
            ("in_progress", "In Progress"),
            ("complete", "Complete"),
        ],
        default="not_started",
    )
    kyc_documents = fields.Many2many("ir.attachment", string="KYC Documents")
    beneficial_owner_ids = fields.One2many(
        "qaco.client_beneficial_owner",
        "client_profile_id",
        string="Beneficial Owners",
    )
    notes = fields.Text(string="CDD / KYC Notes")


class QacoClientBeneficialOwner(models.Model):
    _name = "qaco.client_beneficial_owner"
    _description = "Beneficial Owner (KYC)"

    client_profile_id = fields.Many2one("qaco.client_profile", required=True, ondelete="cascade")
    name = fields.Char(required=True, string="Owner Name")
    nationality = fields.Char()
    percentage = fields.Float()
    id_document = fields.Many2one("ir.attachment", string="ID Document")
    notes = fields.Text()


class QacoClientAcceptance(models.Model):
    _name = "qaco.client_acceptance"
    _description = "Client Acceptance / Continuance (ISA / Firm Policy)"
    _rec_name = "audit_id"

    audit_id = fields.Many2one("qaco.audit", required=True, ondelete="cascade")
    decision = fields.Selection(
        [("accept", "Accept"), ("decline", "Decline"), ("pending", "Pending")],
        default="pending",
    )
    background_checks = fields.Text(string="Background Checks")
    conflicts_detected = fields.Text(string="Conflicts / Issues")
    sanctions_checked = fields.Boolean(string="Sanctions Checked")
    acceptance_date = fields.Date(string="Decision Date")
    accepted_by = fields.Many2one("res.users", string="Decision By")
    notes = fields.Text()

    @api.model
    def create(self, vals):
        record = super().create(vals)
        audit = record.audit_id
        planning = getattr(audit, "planning_phase_id", None)
        if audit and planning:
            try:
                planning._log_evidence(
                    name=_("Client acceptance recorded"),
                    action_type="create",
                    note=f"Decision: {record.decision}",
                    standard_reference="ISA 210; Firm policy",
                )
            except Exception:  # pragma: no cover - logging guard
                _logger.exception("Failed to log client acceptance evidence")
        return record


class QacoIndependenceCheck(models.Model):
    _name = "qaco.independence_check"
    _description = "Independence Check / Declaration"

    audit_id = fields.Many2one("qaco.audit", required=True, ondelete="cascade")
    declaration_signed = fields.Boolean(string="Declaration Signed")
    declaration_attachment = fields.Many2one(
        "ir.attachment",
        string="Declaration Attachment",
        help="Partner/Manager signed declaration",
    )
    threats_identified = fields.Text(string="Threats Identified")
    safeguards = fields.Text(string="Safeguards Proposed")
    independence_status = fields.Selection(
        [("ok", "OK"), ("needs_action", "Needs Action"), ("blocked", "Blocked")],
        default="ok",
    )
    checked_on = fields.Date(default=fields.Date.context_today)
    checked_by = fields.Many2one("res.users", default=lambda self: self.env.user)

    @api.constrains("independence_status")
    def _constrain_independence(self):
        for record in self:
            if record.independence_status == "ok" and not record.declaration_signed:
                raise ValidationError(_("Independence cannot be marked OK unless declaration is signed."))


class QacoLetterTemplate(models.Model):
    _name = "qaco.letter.template"
    _description = "Engagement Letter Template"

    name = fields.Char(required=True)
    version = fields.Char(string="Version")
    scope_text = fields.Text(string="Scope Text")
    fees = fields.Text(string="Fees / Fee Basis")
    deliverable_list = fields.Text(string="Deliverables / Outputs")
    notes = fields.Text(string="Legal Notes & Disclaimers")
    active = fields.Boolean(default=True)


class QacoEngagementLetter(models.Model):
    _name = "qaco.engagement.letter"
    _description = "Engagement Letter Instance"

    audit_id = fields.Many2one("qaco.audit", required=True, ondelete="cascade")
    template_id = fields.Many2one("qaco.letter.template", string="Template")
    version = fields.Char(string="Template Version")
    scope_text = fields.Text(string="Scope")
    fees = fields.Text(string="Fees")
    deliverable_list = fields.Text(string="Deliverables")
    finalized_pdf = fields.Binary(string="Finalized PDF", attachment=True)
    finalized_fname = fields.Char(string="File Name")
    signed = fields.Boolean(string="Signed")
    signed_date = fields.Date(string="Signed Date")

    def action_generate_pdf(self):
        self.ensure_one()
        audit = self.audit_id
        planning = getattr(audit, "planning_phase_id", None)
        if audit and planning:
            try:
                planning._log_evidence(
                    name=_("Engagement letter generated"),
                    action_type="create",
                    note="Template %s" % (self.template_id.name if self.template_id else ""),
                    standard_reference="ISA 210",
                )
            except Exception:  # pragma: no cover - logging guard
                _logger.exception("Failed to log engagement letter evidence")
        return True


class QacoRiskMatrixFS(models.Model):
    _name = "qaco.risk_matrix.fs"
    _description = "Financial Statement Level Risk Matrix"

    audit_id = fields.Many2one("qaco.audit", required=True, ondelete="cascade")
    name = fields.Char(
        string="Risk Description",
        required=True,
        default=lambda self: self._generate_default_name(),
    )
    likelihood = fields.Selection([("1", "Low"), ("2", "Medium"), ("3", "High")], default="2")
    impact = fields.Selection([("1", "Low"), ("2", "Medium"), ("3", "High")], default="2")
    score = fields.Integer(compute="_compute_score", store=True)
    owner_id = fields.Many2one("res.users", string="Owner")
    linked_checklist_ids = fields.Many2many("qaco.planning.checklist", string="Related Checklist Items")
    notes = fields.Text()

    @api.model
    def _generate_default_name(self):
        seq = self.env["ir.sequence"].sudo().next_by_code("qaco.risk_matrix.fs")
        return seq or _("Financial Statement Risk")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = self._generate_default_name()
        return super().create(vals_list)

    @api.depends("likelihood", "impact")
    def _compute_score(self):
        for record in self:
            try:
                record.score = int(record.likelihood or 1) * int(record.impact or 1)
            except Exception:
                record.score = 0


class QacoRiskMatrixAssertion(models.Model):
    _name = "qaco.risk_matrix.assertion"
    _description = "Assertion Level Risk Matrix"

    audit_id = fields.Many2one("qaco.audit", required=True, ondelete="cascade")
    account_area = fields.Char(string="Account / Area", required=True)
    assertion = fields.Selection(
        [
            ("occurrence", "Occurrence"),
            ("existence", "Existence"),
            ("completeness", "Completeness"),
            ("rights", "Rights & Obligations"),
            ("valuation", "Valuation / Allocation"),
            ("presentation", "Presentation & Disclosure"),
            ("cutoff", "Cut-off"),
            ("accuracy", "Accuracy"),
        ],
        required=True,
    )
    description = fields.Text()
    likelihood = fields.Selection([("1", "Low"), ("2", "Medium"), ("3", "High")], default="2")
    impact = fields.Selection([("1", "Low"), ("2", "Medium"), ("3", "High")], default="2")
    score = fields.Integer(compute="_compute_score", store=True)
    planned_substantive = fields.Text(string="Planned Substantive Procedures")
    planned_controls = fields.Text(string="Planned Tests of Controls")

    @api.depends("likelihood", "impact")
    def _compute_score(self):
        for record in self:
            try:
                record.score = int(record.likelihood or 1) * int(record.impact or 1)
            except Exception:
                record.score = 0


class QacoICControlEnvLine(models.Model):
    _name = "qaco.ic.control.env.line"
    _description = "Control Environment Checklist Line"
    _order = "ref_no, id"

    planning_id = fields.Many2one("qaco.planning.phase", required=True, ondelete="cascade")
    ref_no = fields.Char(string="Reference")
    question = fields.Text(string="Question", required=True)
    answer = fields.Selection(IC_CHECKLIST_ANSWERS, string="Answer", default="yes")
    risk_rating = fields.Selection(IC_RISK_RATINGS, string="Risk Rating")
    comments = fields.Text(string="Comments")
    evidence_attached = fields.Boolean(string="Evidence Attached")
    wp_ref = fields.Char(string="WP Ref")


class QacoICRiskProcessLine(models.Model):
    _name = "qaco.ic.risk.process.line"
    _description = "Entity Risk Assessment Process Checklist"
    _order = "ref_no, id"

    planning_id = fields.Many2one("qaco.planning.phase", required=True, ondelete="cascade")
    ref_no = fields.Char(string="Reference")
    question = fields.Text(string="Question", required=True)
    answer = fields.Selection(IC_CHECKLIST_ANSWERS, string="Answer", default="yes")
    risk_rating = fields.Selection(IC_RISK_RATINGS, string="Risk Rating")
    comments = fields.Text(string="Comments")
    evidence_attached = fields.Boolean(string="Evidence Attached")
    wp_ref = fields.Char(string="WP Ref")


class QacoICITGCLine(models.Model):
    _name = "qaco.ic.itgc.line"
    _description = "IT General Controls Checklist"
    _order = "ref_no, id"

    planning_id = fields.Many2one("qaco.planning.phase", required=True, ondelete="cascade")
    ref_no = fields.Char(string="Reference")
    question = fields.Text(string="Question", required=True)
    answer = fields.Selection(IC_CHECKLIST_ANSWERS, string="Answer", default="yes")
    risk_rating = fields.Selection(IC_RISK_RATINGS, string="Risk Rating")
    comments = fields.Text(string="Comments")
    evidence_attached = fields.Boolean(string="Evidence Attached")
    wp_ref = fields.Char(string="WP Ref")


class QacoICMonitoringLine(models.Model):
    _name = "qaco.ic.monitoring.line"
    _description = "Monitoring of Controls Checklist"
    _order = "ref_no, id"

    planning_id = fields.Many2one("qaco.planning.phase", required=True, ondelete="cascade")
    ref_no = fields.Char(string="Reference")
    question = fields.Text(string="Question", required=True)
    answer = fields.Selection(IC_CHECKLIST_ANSWERS, string="Answer", default="yes")
    risk_rating = fields.Selection(IC_RISK_RATINGS, string="Risk Rating")
    comments = fields.Text(string="Comments")
    evidence_attached = fields.Boolean(string="Evidence Attached")
    wp_ref = fields.Char(string="WP Ref")


class QacoICControlActivityLine(models.Model):
    _name = "qaco.ic.control.activity.line"
    _description = "Control Activity by Process"
    _order = "cycle, id"

    planning_id = fields.Many2one("qaco.planning.phase", required=True, ondelete="cascade")
    cycle = fields.Selection(IC_CONTROL_CYCLES, string="Process / Cycle", required=True)
    key_controls_description = fields.Text(string="Key Controls Description", required=True)
    control_type = fields.Selection(IC_CONTROL_TYPES, string="Control Type")
    control_nature = fields.Selection(IC_CONTROL_NATURE, string="Control Nature")
    frequency = fields.Selection(IC_CONTROL_FREQUENCY, string="Frequency")
    control_owner = fields.Char(string="Control Owner")
    design_effective = fields.Boolean(string="Design Effective")
    design_effective_note = fields.Text(string="Design Effectiveness Notes")
    implementation_status = fields.Selection(
        IC_IMPLEMENTATION_STATUS,
        string="Implementation Status",
        default="implemented",
    )


class QacoICDeficiencyLine(models.Model):
    _name = "qaco.ic.deficiency.line"
    _description = "Internal Control Deficiency"
    _order = "remediation_timeline desc, id"

    area = fields.Selection(
        [
            ("control_environment", "Control Environment"),
            ("risk_process", "Risk Assessment Process"),
            ("itgc", "IT General Controls"),
            ("cycle_controls", "Cycle / Process Controls"),
            ("monitoring", "Monitoring"),
            ("cg", "Corporate Governance / Regulatory"),
        ],
        string="Area",
        required=True,
    )
    planning_id = fields.Many2one("qaco.planning.phase", required=True, ondelete="cascade")
    description = fields.Text(string="Deficiency Description", required=True)
    likelihood = fields.Selection(IC_RISK_RATINGS, string="Likelihood")
    impact = fields.Selection(IC_RISK_RATINGS, string="Impact")
    potential_effect_on_fs = fields.Text(string="Potential Effect on FS")
    related_assertions = fields.Char(string="Related Assertions")
    planned_audit_response = fields.Text(string="Planned Audit Response")
    management_remediation_plan = fields.Text(string="Management Remediation Plan")
    remediation_timeline = fields.Date(string="Remediation Timeline")
    follow_up_next_audit = fields.Boolean(string="Follow-up Next Audit")


class QacoICAttachmentIndexLine(models.Model):
    _name = "qaco.ic.attachment.index.line"
    _description = "Internal Control Attachment Index"
    _order = "category, template_name"

    planning_id = fields.Many2one("qaco.planning.phase", required=True, ondelete="cascade")
    template_name = fields.Char(string="Template / Document", required=True)
    category = fields.Selection(
        [
            ("control_environment", "Control Environment"),
            ("risk_process", "Risk Assessment Process"),
            ("itgc", "ITGC"),
            ("cycle_controls", "Cycle Controls"),
            ("monitoring", "Monitoring"),
            ("cg", "Corporate Governance"),
        ],
        string="Category",
        required=True,
    )
    doc_type = fields.Selection(
        [
            ("template", "Template"),
            ("policy", "Policy / SOP"),
            ("evidence", "Evidence"),
            ("minutes", "Minutes / Meeting"),
            ("register", "Register / Log"),
            ("other", "Other"),
        ],
        string="Document Type",
        required=True,
    )
    uploaded = fields.Boolean(string="Uploaded?")
    attachment_id = fields.Many2one("ir.attachment", string="Attachment")


class QacoInternalControlAssessment(models.Model):
    _name = "qaco.internal_control_assessment"
    _description = "Internal Control Assessment (ToC Questionnaire)"

    audit_id = fields.Many2one("qaco.audit", required=True, ondelete="cascade")
    process_name = fields.Char(string="Process / Cycle")
    questionnaire_responses = fields.Json(string="Questionnaire Responses (JSON)")
    control_rating = fields.Selection(
        [("weak", "Weak"), ("adequate", "Adequate"), ("strong", "Strong")],
        default="adequate",
    )
    recommended_tests_of_controls = fields.Boolean(string="Recommend Tests of Controls")
    notes = fields.Text()


class QacoAnalyticalReview(models.Model):
    _name = "qaco.analytical_review"
    _description = "Preliminary Analytical Procedures"

    audit_id = fields.Many2one("qaco.audit", required=True, ondelete="cascade")
    bs_commentary = fields.Text(string="Balance Sheet Commentary")
    is_commentary = fields.Text(string="Income Statement Commentary")
    ratio_analysis = fields.Json(string="Ratio Analysis (JSON)")
    anomalies_found = fields.Text(string="Anomalies Found / Flags")
    performed_on = fields.Date(default=fields.Date.context_today)
    performed_by = fields.Many2one("res.users", default=lambda self: self.env.user)


class QacoPlanningPBCExtension(models.Model):
    _inherit = "qaco.planning.pbc"

    information_heading = fields.Char(string="Information Category")
    sequence_ref = fields.Integer(string="Reference #")
    responsible_role = fields.Char(string="Responsible Role")
    format_detail = fields.Char(string="Format (Display)")
    applicable = fields.Boolean(string="Applicable", default=True)
    priority = fields.Selection([("low", "Low"), ("normal", "Normal"), ("high", "High")], default="normal")
    expected_format = fields.Selection(
        [("pdf", "PDF"), ("excel", "Excel"), ("word", "Word"), ("other", "Other")],
        default="pdf",
    )
    sample_items = fields.Text(string="Sample Items (if sampling required)")
    auto_reminder_config = fields.Boolean(string="Auto Reminder Enabled", default=True)
    reminder_days = fields.Char(
        string="Reminder Days (csv)",
        help="Comma separated days before due to remind, e.g. 7,3,1",
    )


class PlanningPBCReminderCron(models.Model):
    _inherit = "qaco.planning.pbc"

    @api.model
    def cron_send_pbc_reminders(self):
        _logger.info("Running qaco cron: send_information_requisition_reminders")
        param = self.env["ir.config_parameter"].sudo()
        default_days = self._parse_days_csv(param.get_param("qaco.pbc.reminder_days", "7,3,1"))
        today = fields.Date.to_date(fields.Date.context_today(self))
        template = self.env.ref("qaco_planning_phase.email_template_pbc_reminder", raise_if_not_found=False)
        activity_type = self.env.ref("mail.mail_activity_data_reminder", raise_if_not_found=False)
        model_ref = self.env["ir.model"]._get(self._name)
        reminders = 0
        for pbc in self.search([("delivery_status", "!=", "received"), ("due_date", "!=", False)]):
            if not pbc.auto_reminder_config:
                continue
            days_list = self._parse_days_csv(pbc.reminder_days) or default_days
            for days in days_list:
                target_date = fields.Date.to_date(pbc.due_date) - timedelta(days=days)
                if target_date != today:
                    continue
                self._create_activity_for_pbc(pbc, activity_type, model_ref, days)
                if template:
                    self._send_template_email(template, pbc)
                reminders += 1
        _logger.info("qaco cron: created %s information requisition reminders", reminders)
        return True

    @staticmethod
    def _parse_days_csv(days_csv):
        try:
            values = {
                int(value.strip())
                for value in (days_csv or "").split(",")
                if value.strip()
            }
            return sorted(values, reverse=True)
        except Exception:
            return []

    def _create_activity_for_pbc(self, pbc, activity_type, model_ref, days):
        if not activity_type or not model_ref:
            return
        user_id = pbc.planning_id.manager_id.id or pbc.planning_id.partner_id.id or self.env.user.id
        vals = {
            "res_id": pbc.id,
            "res_model_id": model_ref.id,
            "activity_type_id": activity_type.id,
            "note": _("Information requisition due in %s days: %s") % (days, pbc.name),
            "user_id": user_id,
            "date_deadline": pbc.due_date,
        }
        try:
            self.env["mail.activity"].create(vals)
        except Exception:  # pragma: no cover - logging guard
            _logger.exception("Failed creating information requisition reminder activity for request %s", pbc.id)

    def _send_template_email(self, template, pbc):
        try:
            template.send_mail(pbc.id, force_send=True)
        except Exception:  # pragma: no cover - logging guard
            _logger.exception("Failed to send information requisition reminder email for %s", pbc.id)

    @api.depends("state", "acceptance_state")
    def _compute_color_index(self):
        state_colors = {
            "draft": 0,            # grey
            "in_progress": 4,      # amber
            "review": 6,           # pink
            "approved": 10,        # green
            "fieldwork": 11,       # teal
            "finalisation": 8,     # purple
        }
        acceptance_colors = {
            "draft": 0,
            "precheck": 2,         # orange
            "awaiting_clearance": 1,  # red
            "accepted": 10,
            "rejected": 1,
        }
        for rec in self:
            rec.color = state_colors.get(
                rec.state,
                acceptance_colors.get(rec.acceptance_state, 0),
            )
