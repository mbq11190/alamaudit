from odoo import fields, models, _


class EngagementDetails(models.Model):
    """Central repository for engagement-level context required by ISA, SECP, and ICAP."""

    _name = "qaco.engagement.details"
    _description = "Engagement Details (ISA / SECP / ICAP)"

    # ===============================
    # A. Engagement Identification
    # ===============================
    name = fields.Char(
        string="Engagement Reference",
        default=lambda self: self.env["ir.sequence"].next_by_code("qaco.engagement.details") or _("New"),
        readonly=True,
    )
    audit_year = fields.Char(string="Audit Year")
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
    )

    engagement_type = fields.Selection(
        [
            ("statutory", "Statutory Audit"),
            ("review", "Review Engagement"),
            ("agreed", "Agreed Upon Procedures"),
            ("special", "Special Purpose Audit"),
        ],
        string="Engagement Type",
    )

    # ===============================
    # B. Engagement Information
    # ===============================
    reporting_framework = fields.Char(string="Reporting Framework")
    applicable_laws = fields.Text(string="Applicable Laws & Regulations")
    period_start = fields.Date(string="Period Start Date")
    period_end = fields.Date(string="Period End Date")
    engagement_purpose = fields.Text(string="Nature & Purpose of Engagement")
    basis_of_accounting = fields.Char(string="Basis of Accounting")
    special_purpose_framework = fields.Char(string="Special Purpose Framework")
    deliverables = fields.Text(string="Engagement Deliverables")

    # ===============================
    # C. Engagement Preconditions (ISA 210)
    # ===============================
    framework_acceptability = fields.Boolean(string="Framework Acceptability Assessed")
    mgmt_responsibility_ack = fields.Boolean(string="Management Responsibilities Acknowledged")
    info_access_agreed = fields.Boolean(string="Agreement on Access to Information")
    preconditions_met = fields.Boolean(string="Preconditions for Audit Met")
    scope_limitation = fields.Text(string="Scope Limitations (If Any)")

    # ===============================
    # D. Engagement Letter
    # ===============================
    engagement_letter_issued = fields.Boolean(string="Engagement Letter Issued")
    engagement_letter_date = fields.Date(string="Engagement Letter Date")
    signed_engagement_letter = fields.Binary(string="Signed Engagement Letter", attachment=True)
    signed_engagement_letter_filename = fields.Char(string="Signed Engagement Letter Filename")

    # ===============================
    # E. Timeline
    # ===============================
    planning_start = fields.Date(string="Planning Start Date")
    planning_end = fields.Date(string="Planning End Date")
    planning_meeting_date = fields.Date(string="Planning Meeting Date")
    fieldwork_start = fields.Date(string="Fieldwork Start Date")
    fieldwork_end = fields.Date(string="Fieldwork End Date")
    expected_completion = fields.Date(string="Expected Completion Date")
    audit_committee_meeting = fields.Date(string="Audit Committee Meeting Date")
    expected_report_date = fields.Date(string="Expected Report Date")
    estimated_hours = fields.Float(string="Estimated Hours")

    # ===============================
    # F. Scope & Objectives
    # ===============================
    audit_scope = fields.Text(string="Audit Scope")
    audit_objectives = fields.Text(string="Audit Objectives")
    inherent_limitations = fields.Text(string="Inherent Limitations")
    specialists_involved = fields.Text(string="Specialists / Experts Involved")

    # ===============================
    # G. Team & Responsibilities
    # ===============================
    engagement_partner = fields.Many2one("res.users", string="Engagement Partner")
    engagement_manager = fields.Many2one("res.users", string="Engagement Manager")
    eqcr_reviewer = fields.Many2one("res.users", string="EQCR Reviewer")
    specialists = fields.Text(string="Specialists")
    independence_confirmed = fields.Boolean(string="Independence Confirmed")
    competence_assessed = fields.Boolean(string="Team Competence Assessed")

    # ===============================
    # H. Materiality Summary
    # ===============================
    overall_materiality = fields.Float(string="Overall Materiality")
    performance_materiality = fields.Float(string="Performance Materiality")
    trivial_threshold = fields.Float(string="Clearly Trivial Threshold")
    materiality_basis = fields.Char(string="Materiality Basis")
    materiality_rationale = fields.Text(string="Materiality Rationale")

    # ===============================
    # I. Risk Summary
    # ===============================
    significant_risks = fields.Text(string="Significant Risks")
    fraud_risks = fields.Text(string="Fraud Risks (ISA 240)")
    fs_level_risks = fields.Text(string="FS-Level Risks")
    assertion_level_risks = fields.Text(string="Assertion-Level Risks")

    # ===============================
    # J. Budget & Resources
    # ===============================
    approved_budget_hours = fields.Float(string="Approved Budget Hours")
    fee_amount = fields.Float(string="Fee Amount")
    staff_allocation = fields.Text(string="Staff Allocation")

    # ===============================
    # K. Regulatory Compliance
    # ===============================
    listed_entity = fields.Boolean(string="Listed Entity")
    pie_status = fields.Boolean(string="Public Interest Entity")
    sepc_aob_requirements = fields.Text(string="SECP / AOB Requirements Applicable")
