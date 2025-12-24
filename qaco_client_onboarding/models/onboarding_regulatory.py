# -*- coding: utf-8 -*-

import logging
from datetime import date, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

LICENSE_RENEWAL_STATUS = [
    ("not_due", "Not due"),
    ("due_soon", "Due soon"),
    ("submitted", "Submitted"),
    ("approved", "Approved"),
    ("expired", "Expired"),
]

NON_RENEWAL_IMPACT = [
    ("operational_stop", "Operational stop"),
    ("penalty", "Penalty"),
    ("reporting_risk", "Reporting risk"),
]

FILING_STATUS = [
    ("due", "Due"),
    ("filed", "Filed"),
    ("overdue", "Overdue"),
    ("disputed", "Disputed"),
]

MATTER_TYPES = [
    ("tax", "Tax"),
    ("regulatory", "Regulatory"),
    ("civil", "Civil"),
    ("criminal", "Criminal"),
    ("labour", "Labour"),
    ("commercial", "Commercial"),
]

MANAGEMENT_ASSESSMENT = [
    ("probable", "Probable"),
    ("possible", "Possible"),
    ("remote", "Remote"),
]

VERIFICATION_METHODS = [
    ("portal", "Portal"),
    ("doc_inspection", "Document Inspection"),
    ("legal_letter", "Legal Letter"),
    ("third_party", "Third Party"),
]


class OnboardingRegulator(models.Model):
    """Master list of common regulators for multi-selection."""

    _name = "qaco.onboarding.regulator"
    _description = "Regulator (Master List)"
    _order = "id"

    name = fields.Char(string="Regulator Name", required=True)
    code = fields.Char(string="Code")


class OnboardingRegulatorContact(models.Model):
    _name = "qaco.onboarding.regulator.contact"
    _description = "Regulator Contact"
    _order = "id"

    onboarding_id = fields.Many2one(
        "qaco.client.onboarding", required=True, ondelete="cascade", index=True
    )
    name = fields.Char(string="Contact Name", required=True)
    designation = fields.Char(string="Designation")
    email = fields.Char(string="Email")
    phone = fields.Char(string="Phone")
    regulator_id = fields.Many2one("qaco.onboarding.regulator", string="Regulator")


class OnboardingLicense(models.Model):
    _name = "qaco.onboarding.license"
    _description = "License / Approval"
    _order = "id"

    onboarding_id = fields.Many2one(
        "qaco.client.onboarding", required=True, ondelete="cascade", index=True
    )
    license_type = fields.Char(string="License Type", required=True)
    issuing_authority = fields.Char(string="Issuing Authority")
    license_no = fields.Char(string="License No.")
    scope = fields.Text(string="Scope / Coverage")
    issue_date = fields.Date(string="Issue Date")
    expiry_date = fields.Date(string="Expiry Date")
    renewal_due_date = fields.Date(string="Renewal Due Date")
    renewal_status = fields.Selection(LICENSE_RENEWAL_STATUS, string="Renewal Status")
    non_renewal_impact = fields.Selection(
        NON_RENEWAL_IMPACT, string="Non-renewal Impact"
    )
    owner_responsible = fields.Char(string="Client Owner")
    auditor_followup_user_id = fields.Many2one(
        "res.users", string="Auditor Follow-up Owner"
    )
    required = fields.Boolean(string="Required", default=False)

    @api.constrains("required", "expiry_date", "renewal_status")
    def _check_required_has_expiry_and_status(self):
        for rec in self:
            if rec.required:
                if not rec.expiry_date:
                    raise ValidationError(
                        _("Expiry date must be set for required licenses.")
                    )
                if not rec.renewal_status:
                    raise ValidationError(
                        _("Renewal status must be set for required licenses.")
                    )

    @api.depends("expiry_date")
    def _compute_needs_renewal_soon(self):
        # helper compute not stored; used by compute in onboarding
        today = date.today()
        soon = today + timedelta(days=90)
        for rec in self:
            rec.needs_renewal_soon = bool(
                rec.expiry_date and rec.expiry_date <= soon and rec.expiry_date >= today
            )

    needs_renewal_soon = fields.Boolean(
        string="Due within 90 days", compute="_compute_needs_renewal_soon"
    )


class OnboardingFiling(models.Model):
    _name = "qaco.onboarding.filing"
    _description = "Statutory Filing"
    _order = "id"

    onboarding_id = fields.Many2one(
        "qaco.client.onboarding", required=True, ondelete="cascade", index=True
    )
    filing_name = fields.Char(string="Filing Name", required=True)
    authority = fields.Char(string="Authority")
    period_covered = fields.Char(string="Period Covered")
    statutory_due_date = fields.Date(string="Statutory Due Date")
    actual_filing_date = fields.Date(string="Actual Filing Date")
    evidence_file = fields.Binary(string="Evidence (PDF)", attachment=True)
    evidence_filename = fields.Char(string="Evidence Filename")
    status = fields.Selection(FILING_STATUS, string="Status", default="due")

    @api.model_create_multi
    def create(self, vals_list):
        Created = super().create(vals_list)
        for rec in Created:
            # index evidence if uploaded
            if rec.evidence_file:
                try:
                    self.env["qaco.onboarding.document"].create(
                        {
                            "onboarding_id": rec.onboarding_id.id,
                            "name": f"Filing Evidence: {rec.filing_name}",
                            "doc_type": "legal",
                            "file": rec.evidence_file,
                            "file_name": rec.evidence_filename
                            or f"{rec.filing_name}.pdf",
                            "state": "received",
                        }
                    )
                except Exception:
                    _logger.exception(
                        "Failed to index filing evidence for %s (onboarding %s)",
                        rec.filing_name,
                        rec.onboarding_id.id,
                    )
        return Created

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if "evidence_file" in vals and vals.get("evidence_file"):
                try:
                    self.env["qaco.onboarding.document"].create(
                        {
                            "onboarding_id": rec.onboarding_id.id,
                            "name": f"Filing Evidence: {rec.filing_name}",
                            "doc_type": "legal",
                            "file": vals.get("evidence_file"),
                            "file_name": vals.get("evidence_filename")
                            or f"{rec.filing_name}.pdf",
                            "state": "received",
                        }
                    )
                except Exception:
                    _logger.exception(
                        "Failed to index filing evidence for %s (onboarding %s)",
                        rec.filing_name,
                        rec.onboarding_id.id,
                    )
        return res


class OnboardingDispute(models.Model):
    _name = "qaco.onboarding.dispute"
    _description = "Legal matter, litigation or dispute"
    _order = "id"

    onboarding_id = fields.Many2one(
        "qaco.client.onboarding", required=True, ondelete="cascade", index=True
    )
    matter_type = fields.Selection(MATTER_TYPES, string="Matter Type")
    counterparty = fields.Char(string="Counterparty / Authority")
    amount_exposure = fields.Monetary(
        string="Amount Exposure", currency_field="currency_id"
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        readonly=True,
        default=lambda self: self.env.company.currency_id,
    )
    status = fields.Selection(
        [
            ("notice", "Notice"),
            ("appeal", "Appeal"),
            ("court", "Court"),
            ("settled", "Settled"),
        ],
        string="Status",
    )
    counsel_name = fields.Char(string="Counsel")
    management_assessment = fields.Selection(
        MANAGEMENT_ASSESSMENT, string="Management Assessment"
    )
    management_assessment_basis = fields.Text(string="Basis for assessment")


class OnboardingNonCompliance(models.Model):
    _name = "qaco.onboarding.noncompliance"
    _description = "Prior non-compliance & remediation"
    _order = "id"

    onboarding_id = fields.Many2one(
        "qaco.client.onboarding", required=True, ondelete="cascade", index=True
    )
    nature = fields.Text(string="Nature of non-compliance")
    period = fields.Char(string="Period")
    root_cause = fields.Text(string="Root Cause")
    corrective_action = fields.Text(string="Corrective Action Plan")
    target_date = fields.Date(string="Target Date")
    status = fields.Selection(
        [("open", "Open"), ("in_progress", "In progress"), ("closed", "Closed")],
        string="Status",
    )
    evidence = fields.Binary(string="Evidence (PDF)", attachment=True)
    evidence_filename = fields.Char(string="Evidence Filename")

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if "evidence" in vals and vals.get("evidence"):
                try:
                    self.env["qaco.onboarding.document"].create(
                        {
                            "onboarding_id": rec.onboarding_id.id,
                            "name": f"Non-compliance Evidence: {rec.onboarding_id.name}",
                            "doc_type": "legal",
                            "file": vals.get("evidence"),
                            "file_name": vals.get("evidence_filename")
                            or "noncompliance.pdf",
                            "state": "received",
                        }
                    )
                except Exception:
                    _logger.exception(
                        "Failed to index non-compliance evidence (onboarding %s)",
                        rec.onboarding_id.id,
                    )
        return res


class OnboardingRequiredDocument(models.Model):
    _name = "qaco.onboarding.required.document"
    _description = "Required document row for Regulatory & Compliance"
    _order = "id"

    onboarding_id = fields.Many2one(
        "qaco.client.onboarding", required=True, ondelete="cascade", index=True
    )
    template_id = fields.Many2one(
        "qaco.onboarding.template.document", string="Template"
    )
    template_name = fields.Char(related="template_id.name", readonly=True)
    stage = fields.Selection(
        [
            ("pre_onboarding", "Pre Onboarding"),
            ("throughout_onboarding", "Throughout Onboarding"),
        ],
        string="Stage",
    )
    mandatory = fields.Selection(
        [
            ("yes", "Yes"),
            ("conditional", "Conditional"),
            ("as_applicable", "As applicable"),
        ],
        string="Mandatory",
    )
    notes = fields.Text(string="Notes")
    download_url = fields.Char(string="Download URL", compute="_compute_download_url")
    uploaded_file = fields.Binary(string="Upload (PDF)", attachment=True)
    uploaded_filename = fields.Char(string="Upload Filename")
    status = fields.Selection(
        [
            ("not_started", "Not started"),
            ("downloaded", "Downloaded"),
            ("received", "Received"),
            ("verified", "Verified"),
            ("accepted", "Accepted"),
            ("rejected", "Rejected"),
            ("superseded", "Superseded"),
        ],
        string="Status",
        default="not_started",
    )
    restricted = fields.Boolean(string="Restricted", default=False)

    def _compute_download_url(self):
        for rec in self:
            if rec.template_id and rec.template_id.template_file:
                rec.download_url = f"/web/content/{rec.template_id._name}/{rec.template_id.id}/template_file/{rec.template_id.template_filename}?download=true"
            else:
                rec.download_url = False

    @api.model_create_multi
    def create(self, vals_list):
        Created = super().create(vals_list)
        for rec in Created:
            if rec.uploaded_file:
                try:
                    self.env["qaco.onboarding.document"].create(
                        {
                            "onboarding_id": rec.onboarding_id.id,
                            "name": f'Required Doc: {rec.template_name or "Attachment"}',
                            "doc_type": "legal",
                            "file": rec.uploaded_file,
                            "file_name": rec.uploaded_filename
                            or (
                                rec.template_id.template_filename
                                if rec.template_id
                                else "upload.pdf"
                            ),
                            "state": "received",
                        }
                    )
                except Exception:
                    _logger.exception(
                        "Failed to index required document for onboarding %s",
                        rec.onboarding_id.id,
                    )
        return Created

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if "uploaded_file" in vals and vals.get("uploaded_file"):
                try:
                    self.env["qaco.onboarding.document"].create(
                        {
                            "onboarding_id": rec.onboarding_id.id,
                            "name": f'Required Doc: {rec.template_name or "Attachment"}',
                            "doc_type": "legal",
                            "file": vals.get("uploaded_file"),
                            "file_name": vals.get("uploaded_filename")
                            or (
                                rec.template_id.template_filename
                                if rec.template_id
                                else "upload.pdf"
                            ),
                            "state": "received",
                        }
                    )
                except Exception:
                    _logger.exception(
                        "Failed to index required document for onboarding %s",
                        rec.onboarding_id.id,
                    )
        return res


# Add helper compute fields on onboarding itself by extending via inheritance
class ClientOnboardingRegulatory(models.Model):
    _inherit = "qaco.client.onboarding"

    regulator_ids = fields.Many2many(
        "qaco.onboarding.regulator", string="Regulators in Scope"
    )
    regulator_contact_ids = fields.One2many(
        "qaco.onboarding.regulator.contact",
        "onboarding_id",
        string="Regulator Contacts",
    )
    license_ids = fields.One2many(
        "qaco.onboarding.license", "onboarding_id", string="Licenses & Approvals"
    )
    filing_ids = fields.One2many(
        "qaco.onboarding.filing", "onboarding_id", string="Filings Tracker"
    )
    dispute_ids = fields.One2many(
        "qaco.onboarding.dispute", "onboarding_id", string="Legal Matters & Disputes"
    )
    non_compliance_ids = fields.One2many(
        "qaco.onboarding.noncompliance", "onboarding_id", string="Prior Non-Compliances"
    )
    required_document_line_ids = fields.One2many(
        "qaco.onboarding.required.document",
        "onboarding_id",
        string="Required Documents (Regulatory)",
    )

    # Tax & labour high-level
    income_tax_status = fields.Selection(
        [
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("not_registered", "Not registered"),
        ],
        string="Income Tax Filer Status",
    )
    withholding_agent_status = fields.Selection(
        [("yes", "Yes"), ("no", "No")], string="Withholding Agent Status"
    )
    sales_tax_status = fields.Selection(
        [("registered", "Registered"), ("not_registered", "Not registered")],
        string="Sales Tax Status",
    )
    provincial_sales_tax = fields.Char(string="PRA / SRB / Provincial Sales Tax")
    tax_audits_summary = fields.Text(string="Open / Recent Tax Audits")
    tax_arrears_summary = fields.Text(string="Tax Arrears / Disputes Summary")

    eobi_registration = fields.Selection(
        [("yes", "Yes"), ("no", "No")], string="EOBI Registered"
    )
    social_security_registration = fields.Selection(
        [("yes", "Yes"), ("no", "No")], string="Social Security Registered"
    )
    min_wage_overtime_risk = fields.Boolean(
        string="Minimum Wage / Overtime Compliance Risk"
    )
    hr_legal_matters = fields.Text(string="Key HR Legal Matters")

    # Compliance risk assessment
    compliance_history_rating = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        string="Compliance History Rating",
    )
    compliance_risk_drivers = fields.Text(string="Key Compliance Risk Drivers")
    residual_compliance_risk = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        string="Residual Compliance Risk",
    )
    financial_reporting_impact = fields.Selection(
        [
            ("direct", "Direct effect"),
            ("indirect", "Indirect effect"),
            ("disclosure", "Disclosure-only"),
        ],
        string="Financial Reporting Impact",
    )

    # Alerts & counters
    upcoming_renewals_count = fields.Integer(
        string="Upcoming Renewals (90d)",
        compute="_compute_renewal_and_overdues",
        store=True,
    )
    overdue_filings_count = fields.Integer(
        string="Overdue Filings", compute="_compute_renewal_and_overdues", store=True
    )

    @api.depends(
        "license_ids.expiry_date", "filing_ids.statutory_due_date", "filing_ids.status"
    )
    def _compute_renewal_and_overdues(self):
        today = date.today()
        soon = today + timedelta(days=90)
        for rec in self:
            rec.upcoming_renewals_count = len(
                rec.license_ids.filtered(
                    lambda line: line.expiry_date
                    and line.expiry_date <= soon
                    and line.expiry_date >= today
                )
            )
            rec.overdue_filings_count = len(
                rec.filing_ids.filtered(
                    lambda f: f.statutory_due_date
                    and f.statutory_due_date < today
                    and f.status != "filed"
                )
            )

    @api.constrains("filing_ids")
    def _check_overdue_filings_before_approval(self):
        # Enforce partner approval/pre-finalization rules: no overdue filings allowed
        for rec in self:
            if rec.state in ("partner_approved", "locked"):
                overdue = rec.filing_ids.filtered(
                    lambda f: f.statutory_due_date
                    and f.statutory_due_date < date.today()
                    and f.status != "filed"
                )
                if overdue:
                    names = ", ".join(overdue.mapped("filing_name"))
                    raise ValidationError(
                        _(
                            "Overdue filings detected (%s). Resolve or obtain partner acknowledgement before approval."
                        )
                        % names
                    )
            # ensure open investigations have financial impact documented
            open_investigations = rec.dispute_ids.filtered(
                lambda d: d.status in ("notice", "appeal", "court")
            )
            for d in open_investigations:
                if not rec.financial_reporting_impact:
                    raise ValidationError(
                        _(
                            "Open investigation/notice exists; document the financial reporting impact before partner approval."
                        )
                    )

    def populate_required_documents_from_templates(self):
        """Populate `required_document_line_ids` from template library filtered to regulatory category."""
        Template = self.env["qaco.onboarding.template.document"]
        cat = self.env["qaco.onboarding.template.category"].search(
            [("code", "=", "regulatory")], limit=1
        )
        if not cat:
            return
        templates = Template.search([("category_id", "=", cat.id)])
        lines = []
        for rec in self:
            existing = rec.required_document_line_ids.mapped("template_id")
            for tpl in templates:
                if tpl.id in existing:
                    continue
                lines.append(
                    {
                        "onboarding_id": rec.id,
                        "template_id": tpl.id,
                        "stage": tpl.stage,
                        "mandatory": (
                            tpl.mandatory
                            if tpl.mandatory in ("yes", "conditional", "as_applicable")
                            else "conditional"
                        ),
                        "notes": tpl.description,
                    }
                )
        if lines:
            self.env["qaco.onboarding.required.document"].create(lines)

    def populate_ownership_required_documents_from_templates(self):
        """Populate `required_document_line_ids` from template library filtered to ownership category."""
        Template = self.env["qaco.onboarding.template.document"]
        cat = self.env["qaco.onboarding.template.category"].search(
            [("code", "=", "ownership")], limit=1
        )
        if not cat:
            return
        templates = Template.search([("category_id", "=", cat.id)])
        lines = []
        for rec in self:
            existing = rec.required_document_line_ids.mapped("template_id")
            for tpl in templates:
                if tpl.id in existing:
                    continue
                lines.append(
                    {
                        "onboarding_id": rec.id,
                        "template_id": tpl.id,
                        "stage": tpl.stage,
                        "mandatory": (
                            tpl.mandatory
                            if tpl.mandatory in ("yes", "conditional", "as_applicable")
                            else "conditional"
                        ),
                        "notes": tpl.description,
                    }
                )
        if lines:
            self.env["qaco.onboarding.required.document"].create(lines)
