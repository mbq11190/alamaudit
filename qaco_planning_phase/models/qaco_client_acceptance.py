from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class QacoClientAcceptance(models.Model):
    _name = "qaco.client.acceptance"
    _description = "Client Acceptance & Continuance"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(
        string="Reference",
        readonly=True,
        required=True,
        copy=False,
        default=lambda self: self.env["ir.sequence"].next_by_code("qaco.client.acceptance") or _("New"),
    )
    audit_id = fields.Many2one("qaco.audit", required=True, string="Audit")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, string="Company")
    client_id = fields.Many2one(
        "res.partner",
        string="Client",
        domain="[(\"customer_rank\", '>', 0)]",
    )
    legal_name = fields.Char(string="Legal Name")
    registration_no = fields.Char(string="Registration No.")
    ntn = fields.Char(string="NTN")
    strn = fields.Char(string="STRN")
    legal_form = fields.Selection(
        [
            ("public_listed", "Public Listed"),
            ("public_unlisted", "Public Unlisted"),
            ("private", "Private"),
            ("section_42", "Section 42"),
            ("ngo", "NGO"),
            ("llp", "LLP"),
            ("sole_proprietor", "Sole Proprietor"),
            ("partnership", "Partnership"),
            ("other", "Other"),
        ],
        string="Legal Form",
    )
    industry_sector = fields.Char(string="Industry / Sector")
    regulator_type = fields.Selection(
        [
            ("secp", "SECP"),
            ("psx", "PSX"),
            ("sbp", "SBP"),
            ("insurance", "Insurance"),
            ("other", "Other"),
            ("none", "None"),
        ],
        string="Regulator",
    )
    is_pie = fields.Boolean(string="Public Interest Entity (PIE)")
    financial_year_end = fields.Date(string="Financial Year End")
    engagement_type = fields.Selection(
        [
            ("statutory_audit", "Statutory Audit"),
            ("review", "Review"),
            ("special_purpose", "Special Purpose"),
            ("group_component", "Group Component"),
        ],
        string="Engagement Type",
    )
    reporting_framework = fields.Selection(
        [
            ("ifrs", "IFRS"),
            ("ifrs_smes", "IFRS for SMEs"),
            ("other", "Other"),
        ],
        string="Reporting Framework",
    )
    is_first_year_engagement = fields.Boolean(string="First Year Engagement")
    previous_auditor_id = fields.Many2one(
        "res.partner",
        string="Previous Auditor",
        domain="[(\"is_company\", '=', True), ('supplier_rank', '>=', 0)]",
    )

    lead_source = fields.Selection(
        [
            ("referral", "Referral"),
            ("website", "Website"),
            ("tender", "Tender"),
            ("direct_contact", "Direct Contact"),
            ("other", "Other"),
        ],
        string="Lead Source",
    )
    business_overview = fields.Text(string="Business Overview")
    expected_fee_range = fields.Char(string="Expected Fee Range")
    initial_red_flags = fields.Text(string="Initial Red Flags")
    basic_kyc_obtained = fields.Boolean(string="Basic KYC Obtained")
    services_clearly_defined = fields.Boolean(string="Services Clearly Defined")
    conflict_check_initiated = fields.Boolean(string="Conflict Check Initiated")

    ownership_structure_summary = fields.Text(string="Ownership Structure")
    pep_sanction_check_done = fields.Boolean(string="PEP / Sanction Check Done")
    pep_sanction_findings = fields.Text(string="PEP Findings")
    adverse_media_found = fields.Boolean(string="Adverse Media Found")
    adverse_media_summary = fields.Text(string="Adverse Media Summary")
    regulatory_history_summary = fields.Text(string="Regulatory History")
    aml_risk_level = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        string="AML Risk Level",
        default="medium",
    )
    cdd_completed = fields.Boolean(string="CDD Completed")
    beneficial_owners_verified = fields.Boolean(string="Beneficial Owners Verified")
    suspicious_indicators = fields.Text(string="Suspicious Indicators")
    aml_escalation_required = fields.Boolean(string="AML Escalation Required")

    noclar_indicators_present = fields.Boolean(string="NOCLAR Indicators Present")
    noclar_summary = fields.Text(string="NOCLAR Summary")
    noclar_action_plan = fields.Text(string="NOCLAR Action Plan")

    independence_threat_self_interest = fields.Boolean(string="Self-Interest Threat")
    independence_threat_self_review = fields.Boolean(string="Self-Review Threat")
    independence_threat_advocacy = fields.Boolean(string="Advocacy Threat")
    independence_threat_familiarity = fields.Boolean(string="Familiarity Threat")
    independence_threat_intimidation = fields.Boolean(string="Intimidation Threat")
    non_audit_services_summary = fields.Text(string="Non-audit Services")
    relationships_affecting_independence = fields.Text(string="Relationships Affecting Independence")
    independence_safeguards = fields.Text(string="Safeguards / Mitigations")
    independence_acceptable = fields.Selection(
        [
            ("yes", "Yes"),
            ("no", "No"),
            ("yes_with_safeguards", "Yes with Safeguards"),
        ],
        string="Independence Acceptable",
        default="yes_with_safeguards",
    )
    conflict_of_interest_identified = fields.Boolean(string="Conflict of Interest Identified")
    conflict_details = fields.Text(string="Conflict Details")
    conflict_client_consents = fields.Boolean(string="Client Consents Obtained")

    clearance_letter_sent = fields.Boolean(string="Clearance Letter Sent")
    clearance_letter_date = fields.Date(string="Letter Sent On")
    clearance_letter_mode = fields.Selection(
        [
            ("email", "Email"),
            ("registered_post", "Registered Post"),
            ("portal", "Portal"),
            ("other", "Other"),
        ],
        string="Clearance Letter Mode",
    )
    clearance_response_received = fields.Boolean(string="Clearance Response Received")
    clearance_response_date = fields.Date(string="Response Received On")
    clearance_response_summary = fields.Text(string="Clearance Response Summary")
    no_response_followup = fields.Text(string="Follow-up Notes")

    inherent_client_risk = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        string="Inherent Client Risk",
    )
    control_environment_risk = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        string="Control Environment Risk",
    )
    litigation_regulatory_risk = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        string="Litigation & Regulatory Risk",
    )
    going_concern_indicators = fields.Boolean(string="Going Concern Indicator(s)")
    going_concern_summary = fields.Text(string="Going Concern Notes")
    overall_engagement_risk = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        string="Overall Engagement Risk",
    )
    risk_score = fields.Integer(string="Risk Score")

    engagement_status = fields.Selection(
        [
            ("new", "New"),
            ("continuing", "Continuing"),
            ("reengagement", "Re-engagement"),
        ],
        string="Engagement Status",
    )
    decision = fields.Selection(
        [
            ("accept", "Accept"),
            ("continue", "Continue"),
            ("reject", "Reject"),
            ("withdraw", "Withdraw"),
        ],
        string="Decision",
    )
    decision_reason = fields.Text(string="Decision Reason")
    decision_conditions = fields.Text(string="Decision Conditions")

    engagement_partner_id = fields.Many2one("res.users", string="Engagement Partner")
    engagement_partner_decision_date = fields.Date(string="Partner Decision Date")
    quality_partner_id = fields.Many2one("res.users", string="Quality Partner")
    quality_partner_review_required = fields.Boolean(string="Quality Review Required")
    quality_partner_review_date = fields.Date(string="Quality Review Date")

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("under_review", "Under Review"),
            ("approved", "Partner Approved"),
            ("rejected", "Rejected / Closed"),
        ],
        default="draft",
        tracking=True,
        string="Status",
    )

    @api.onchange("client_id")
    def _onchange_client_id(self):
        for record in self:
            if record.client_id and not record.legal_name:
                record.legal_name = record.client_id.name

    def action_submit_review(self):
        self.write({"state": "under_review"})

    def action_approve(self):
        self.write({"state": "approved"})

    def action_reject(self):
        self.write({"state": "rejected"})

    @api.constrains(
        "state",
        "decision",
        "engagement_partner_id",
        "engagement_partner_decision_date",
        "independence_acceptable",
    )
    def _check_state_constraints(self):
        for record in self:
            if record.state == "approved":
                if record.independence_acceptable == "no":
                    raise ValidationError(
                        _(
                            "Independence is unacceptable, approval is not allowed."
                        )
                    )
                if record.decision not in ("accept", "continue"):
                    raise ValidationError(
                        _(
                            "Partner approval requires a positive decision (Accept or Continue)."
                        )
                    )
                if not record.engagement_partner_id or not record.engagement_partner_decision_date:
                    raise ValidationError(
                        _(
                            "Partner approval requires a partner decision date and partner assignment."
                        )
                    )

