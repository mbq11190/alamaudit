from odoo import fields, models, _


class EngagementDetails(models.Model):
    """Central repository for ISA / ICAP / SECP / AOB engagement metadata."""

    _name = "qaco.engagement.details"
    _description = "Engagement Details (ISA / SECP / ICAP)"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # ===============================
    # A. Engagement Identification
    # ===============================
    name = fields.Char(
        string="Engagement Reference",
        default=lambda self: self.env["ir.sequence"].next_by_code("qaco.engagement.details") or _("New"),
        readonly=True,
        tracking=True,
    )
    audit_year = fields.Char(string="Audit Year (FY)", tracking=True)
    entity_class = fields.Selection(
        [
            ("small", "Small Entity"),
            ("medium", "Medium Entity"),
            ("large", "Large Entity"),
            ("public_listed", "Public Listed"),
            ("public_unlisted", "Public Unlisted"),
            ("ngo", "NGO"),
            ("section_42", "Section 42 Company"),
            ("other", "Other"),
        ],
        string="Entity Class",
        tracking=True,
    )
    engagement_type = fields.Selection(
        [
            ("statutory", "Statutory Audit"),
            ("review", "Review Engagement"),
            ("agreed", "Agreed Upon Procedures"),
            ("special", "Special Purpose Audit"),
        ],
        string="Type of Engagement",
        tracking=True,
    )

    # ===============================
    # B. Engagement Information
    # ===============================
    reporting_framework = fields.Selection(
        [
            ("ifrs", "IFRS"),
            ("ias", "IAS"),
            ("ifrs_sme", "IFRS for SMEs"),
            ("government", "Government Framework"),
            ("cash", "Cash-basis"),
            ("other", "Other"),
        ],
        string="Applicable Reporting Framework",
        tracking=True,
    )
    applicable_laws = fields.Text(string="Applicable Laws & Regulations")
    period_start = fields.Date(string="Period Start Date")
    period_end = fields.Date(string="Period End Date")
    engagement_purpose = fields.Text(string="Nature & Purpose of Engagement")
    basis_of_accounting = fields.Selection(
        [
            ("accrual", "Accrual"),
            ("cash", "Cash"),
            ("special", "Special Purpose"),
        ],
        string="Basis of Accounting",
    )
    special_purpose_framework = fields.Char(string="Special Purpose Framework")
    deliverables = fields.Text(string="Deliverables")

    # ===============================
    # C. Engagement Preconditions (ISA 210)
    # ===============================
    framework_acceptability = fields.Boolean(string="Framework Acceptability Assessed", tracking=True)
    mgmt_responsibility_ack = fields.Boolean(string="Management Responsibilities Acknowledged", tracking=True)
    info_access_agreed = fields.Boolean(string="Agreement on Access to Information", tracking=True)
    preconditions_met = fields.Boolean(string="Preconditions for Audit Met", tracking=True)
    scope_limitation = fields.Text(string="Scope Limitation Identified")

    # ===============================
    # D. Engagement Letter
    # ===============================
    engagement_letter_issued = fields.Boolean(string="Engagement Letter Issued", tracking=True)
    engagement_letter_date = fields.Date(string="Engagement Letter Date")
    engagement_letter_reference = fields.Char(string="Engagement Letter Version / Reference")
    signed_engagement_letter = fields.Binary(string="Signed Engagement Letter", attachment=True)
    signed_engagement_letter_filename = fields.Char(string="Signed Engagement Letter Filename")
    client_signed_copy = fields.Binary(string="Client Signed Copy", attachment=True)
    client_signed_copy_filename = fields.Char(string="Client Signed Copy Filename")

    # ===============================
    # E. Timeline
    # ===============================
    planning_start = fields.Date(string="Planning Start Date")
    planning_end = fields.Date(string="Planning End Date")
    planning_meeting_date = fields.Date(string="Planning Meeting Date")
    fieldwork_start = fields.Date(string="Fieldwork Start Date")
    fieldwork_end = fields.Date(string="Fieldwork End Date")
    expected_completion = fields.Date(string="Expected Completion Date")
    final_review_date = fields.Date(string="Final Review Date")
    audit_committee_meeting = fields.Date(string="Audit Committee Meeting Date")
    expected_report_date = fields.Date(string="Expected Date of Auditor's Report")

    # ===============================
    # F. Scope, Objectives & Limitations
    # ===============================
    audit_scope = fields.Text(string="Audit Scope")
    audit_objectives = fields.Text(string="Audit Objectives (ISA 200)")
    inherent_limitations = fields.Text(string="Inherent Limitations Identified")
    specialists_involved = fields.Text(string="Use of Component Auditors / Experts")

    # ===============================
    # G. Team & Responsibilities (ISA 220)
    # ===============================
    engagement_partner = fields.Many2one("res.users", string="Engagement Partner")
    engagement_manager = fields.Many2one("res.users", string="Engagement Manager")
    eqcr_reviewer = fields.Many2one("res.users", string="EQCR Reviewer")
    specialists = fields.Text(string="Specialists Used")
    competence_assessed = fields.Boolean(string="Team Competence Assessed", tracking=True)
    competence_assessment_notes = fields.Text(string="Team Competence Assessment Notes")
    independence_confirmed = fields.Boolean(string="Independence Confirmed", tracking=True)

    # ===============================
    # H. Materiality Summary
    # ===============================
    overall_materiality = fields.Float(string="Overall Materiality")
    performance_materiality = fields.Float(string="Performance Materiality")
    trivial_threshold = fields.Float(string="Trivial Misstatement Threshold")
    materiality_basis = fields.Selection(
        [
            ("pbt", "Profit Before Tax"),
            ("revenue", "Revenue"),
            ("assets", "Total Assets"),
            ("equity", "Equity"),
            ("other", "Other"),
        ],
        string="Materiality Basis",
    )
    materiality_rationale = fields.Text(string="Materiality Rationale")

    # ===============================
    # I. Risk Summary
    # ===============================
    significant_risks = fields.Text(string="Significant Risks Identified")
    fraud_risks = fields.Text(string="Fraud Risk Factors (ISA 240)")
    fs_level_risks = fields.Text(string="Risk of Material Misstatement – FS Level")
    assertion_level_risks = fields.Text(string="Risk of Material Misstatement – Assertion Level")
    management_override_risk = fields.Selection(
        [
            ("low", "Low"),
            ("moderate", "Moderate"),
            ("high", "High"),
        ],
        string="Management Override Risk",
        required=True,
        default="moderate",
    )

    # ===============================
    # J. Engagement Budget & Resources
    # ===============================
    estimated_hours = fields.Float(string="Estimated Hours")
    approved_budget_hours = fields.Float(string="Approved Budget Hours")
    fee_amount = fields.Float(string="Fee Amount")
    staff_allocation = fields.Text(string="Resource Allocation")

    # ===============================
    # K. Reporting Requirements
    # ===============================
    report_type = fields.Selection(
        [
            ("unmodified", "Unmodified"),
            ("qualified", "Qualified"),
            ("adverse", "Adverse"),
            ("disclaimer", "Disclaimer"),
            ("emphasis", "Emphasis of Matter"),
        ],
        string="Type of Audit Report",
    )
    other_reporting_requirements = fields.Text(string="Other Reporting Requirements")
    required_attachments = fields.Text(string="Required Attachments")

    # ===============================
    # L. Regulatory & SECP / AOB Compliance
    # ===============================
    listed_entity = fields.Boolean(string="Listed Entity Requirements", tracking=True)
    pie_status = fields.Boolean(string="PIE Criteria", tracking=True)
    aob_registration_number = fields.Char(string="AOB Registration No.")
    sepc_aob_requirements = fields.Text(string="SECP / AOB Requirements Applicable")
    additional_secp_sros = fields.Text(string="Additional SECP SROs Applicable")
