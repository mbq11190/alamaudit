# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

TIME_PRESSURE = [
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
]

ENGAGEMENT_TYPES = [
    ("statutory", "Statutory"),
    ("group", "Group"),
    ("special", "Special"),
    ("pie", "PIE"),
    ("listed", "Listed"),
    ("grant", "Grant audit"),
    ("other", "Other"),
]

AML_CONCLUSIONS = [
    ("clear", "Clear"),
    ("edd", "Needs Enhanced Due Diligence"),
    ("block", "Not acceptable"),
]

SANCTIONS_MATCH_LEVEL = [
    ("exact", "Exact"),
    ("partial", "Partial"),
    ("false_positive", "False positive"),
]

RISK_RATING = [
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
]


class OnboardingAdverseMedia(models.Model):
    _name = "qaco.onboarding.adverse.media"
    _description = "Adverse media / reputation evidence"

    onboarding_id = fields.Many2one(
        "qaco.client.onboarding", required=True, ondelete="cascade", index=True
    )
    source = fields.Char(string="Source")
    summary = fields.Text(string="Summary")
    evidence = fields.Binary(string="Evidence (screenshot/pdf)", attachment=True)
    evidence_filename = fields.Char(string="Filename")


class OnboardingSanctionsScreen(models.Model):
    _name = "qaco.onboarding.sanctions.screen"
    _description = "Sanctions / PEP Screening Record"

    onboarding_id = fields.Many2one(
        "qaco.client.onboarding", required=True, ondelete="cascade", index=True
    )
    screening_performed = fields.Boolean(string="Screening performed")
    screening_scope = fields.Char(string="Screening scope")
    screening_method = fields.Selection(
        [("manual", "Manual"), ("tool", "Tool"), ("third_party", "Third party")],
        string="Screening method",
    )
    sanctions_hit = fields.Boolean(string="Sanctions hit")
    pep_identified = fields.Boolean(string="PEP identified")
    adverse_media_hit = fields.Boolean(string="Adverse media hit")
    match_level = fields.Selection(SANCTIONS_MATCH_LEVEL, string="Match level")
    resolution_notes = fields.Text(string="Resolution notes")
    screening_conclusion = fields.Selection(
        [("clear", "Clear"), ("escalate", "Escalate"), ("block", "Block")],
        string="Screening conclusion",
    )

    @api.constrains("screening_conclusion", "sanctions_hit")
    def _check_sanctions_block(self):
        for rec in self:
            if rec.screening_conclusion == "block" and not rec.resolution_notes:
                raise ValidationError(
                    _("When screening conclusion is Block, provide resolution notes.")
                )


class OnboardingFeeTerms(models.Model):
    _name = "qaco.onboarding.fee.terms"
    _description = "Fee & Collection Terms"

    onboarding_id = fields.Many2one(
        "qaco.client.onboarding", required=True, ondelete="cascade", index=True
    )
    total_fee = fields.Monetary(
        string="Total fee (budget)", currency_field="currency_id"
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        readonly=True,
        default=lambda self: self.env.company.currency_id,
    )
    retainer_amount = fields.Monetary(string="Retainer / advance")
    retainer_due_date = fields.Date(string="Retainer due date")
    billing_milestones = fields.Text(string="Milestones (planning/interim/completion)")
    billing_frequency = fields.Selection(
        [("monthly", "Monthly"), ("phase", "Phase-wise"), ("other", "Other")],
        string="Billing frequency",
    )
    out_of_scope_rate_card = fields.Text(string="Out of scope rate card")
    prior_payment_history = fields.Text(string="Prior payment history")
    credit_assessment = fields.Text(string="Credit assessment summary")
    outstanding_fees_prior_auditor = fields.Monetary(
        string="Outstanding fees (prior auditor)", currency_field="currency_id"
    )
    dispute_probability = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        string="Dispute probability",
    )
    collection_risk_rating = fields.Selection(
        RISK_RATING, string="Collection risk rating"
    )
    collection_controls = fields.Text(string="Collection controls")


class OnboardingConditionalAcceptance(models.Model):
    _name = "qaco.onboarding.conditional.acceptance"
    _description = "Conditional Acceptance Tracker"

    onboarding_id = fields.Many2one(
        "qaco.client.onboarding", required=True, ondelete="cascade", index=True
    )
    description = fields.Text(string="Condition description", required=True)
    required_by = fields.Char(string="Required by")
    due_date = fields.Date(string="Target date")
    status = fields.Selection(
        [("open", "Open"), ("in_progress", "In progress"), ("closed", "Closed")],
        string="Status",
        default="open",
    )
    evidence = fields.Binary(string="Evidence (PDF)", attachment=True)
    evidence_filename = fields.Char(string="Evidence Filename")


class OnboardingRiskScoreDriver(models.Model):
    _name = "qaco.onboarding.risk.driver"
    _description = "Engagement Risk Driver (scoring)"

    onboarding_id = fields.Many2one(
        "qaco.client.onboarding", required=True, ondelete="cascade", index=True
    )
    driver = fields.Char(string="Driver")
    weight = fields.Float(string="Weight", default=1.0)
    score = fields.Integer(string="Score (0-100)", default=0)


# Extend existing onboarding record with pre-acceptance fields
class ClientOnboardingPreAcceptance(models.Model):
    _inherit = "qaco.client.onboarding"

    engagement_type = fields.Selection(ENGAGEMENT_TYPES, string="Engagement Type")
    reporting_framework = fields.Char(string="Reporting framework")
    auditing_standards = fields.Char(string="Auditing standards")
    period_from = fields.Date(string="Period start")
    period_to = fields.Date(string="Period end")
    first_year = fields.Boolean(string="First year audit")
    reason_for_appointment = fields.Char(string="Reason for appointment / change")
    deadline_constraints = fields.Text(string="Deadline constraints")

    # Integrity & background
    integrity_history_noncompliance = fields.Boolean(
        string="History of non-compliance / late filings"
    )
    integrity_aggressive_accounting = fields.Boolean(
        string="Aggressive accounting positions / restatements"
    )
    integrity_scope_limitations = fields.Boolean(
        string="Management unwilling to provide information / scope limitations expected"
    )
    integrity_prior_auditor_disagreements = fields.Boolean(
        string="Prior auditor disagreements / resignation / qualifications"
    )
    integrity_litigation_patterns = fields.Boolean(
        string="Litigation / fraud / whistleblowing"
    )
    integrity_adverse_media = fields.Boolean(
        string="Adverse media / reputational issues"
    )
    prior_auditor_issues = fields.Text(string="Prior auditor issues description")
    outstanding_disputes = fields.Text(
        string="Outstanding disputes with auditors/consultants"
    )
    management_attitude = fields.Text(
        string="Management attitude to internal control and governance"
    )

    # AML / KYC
    aml_applicable = fields.Boolean(string="AML / KYC applicable")
    client_identity_verified = fields.Boolean(string="Client identity verified")
    ubo_verified = fields.Boolean(string="UBO verification completed")
    source_of_funds = fields.Text(string="Primary funding sources")
    unusual_funding_patterns = fields.Boolean(string="Unusual funding patterns")
    unusual_funding_details = fields.Text(string="Unusual funding explanation")
    aml_high_risk_indicators = fields.Text(string="High risk AML indicators")
    aml_conclusion = fields.Selection(AML_CONCLUSIONS, string="AML / KYC conclusion")

    # Sanctions / PEP
    sanctions_screen_performed = fields.Boolean(
        string="Sanctions / PEP screening performed"
    )
    sanctions_screen_ids = fields.One2many(
        "qaco.onboarding.sanctions.screen",
        "onboarding_id",
        string="Sanctions / PEP screenings",
    )
    adverse_media_ids = fields.One2many(
        "qaco.onboarding.adverse.media",
        "onboarding_id",
        string="Adverse media evidence",
    )

    # Engagement risk factors
    complexity_estimates = fields.Boolean(string="Complex estimates / valuations")
    complexity_revenue = fields.Boolean(string="Revenue complexity / multiple streams")
    complexity_going_concern = fields.Boolean(string="Going concern stress indicators")
    complexity_related_party = fields.Boolean(
        string="Significant related parties / unusual transactions"
    )
    complexity_group = fields.Boolean(
        string="Group structure / component work expected"
    )
    complexity_regulatory = fields.Boolean(
        string="Regulatory scrutiny / investigations"
    )
    complexity_it = fields.Boolean(string="Significant IT reliance / ERP change")
    complexity_judgments = fields.Boolean(
        string="Significant judgments / first time adoption"
    )

    capability_available = fields.Boolean(string="Do we have capability")
    specialists_required = fields.Boolean(string="Specialists required")
    specialists_plan = fields.Text(string="Specialists plan")
    time_pressure_risk = fields.Selection(TIME_PRESSURE, string="Time pressure risk")

    # Scoring
    engagement_risk_rating = fields.Selection(
        RISK_RATING, string="Engagement risk rating"
    )
    engagement_score = fields.Integer(
        string="Score (0-100)", compute="_compute_engagement_score", store=True
    )
    score_driver_ids = fields.One2many(
        "qaco.onboarding.risk.driver", "onboarding_id", string="Score drivers"
    )
    score_override = fields.Boolean(string="Score override")
    score_override_reason = fields.Text(string="Override rationale")
    score_override_partner_id = fields.Many2one(
        "res.users", string="Partner approving override"
    )

    # Fee & collection
    fee_terms_id = fields.Many2one("qaco.onboarding.fee.terms", string="Fee terms")
    fee_terms_rel = fields.One2many(
        "qaco.onboarding.fee.terms", "onboarding_id", string="Fee terms history"
    )

    # Acceptance decision & safeguards
    engagement_decision = fields.Selection(
        [("accept", "Accept"), ("reject", "Decline"), ("conditions", "Conditional")],
        string="Decision",
    )
    decision_conditions = fields.Text(string="Conditions if conditional")
    eqcr_required = fields.Boolean(
        string="EQCR required", compute="_compute_eqcr_required", store=True
    )
    eqcr_rationale = fields.Text(string="EQCR rationale")
    safeguards_required = fields.Text(string="Required safeguards")
    prepared_by = fields.Many2one("res.users", string="Prepared by")
    reviewed_by = fields.Many2one("res.users", string="Reviewed by")
    partner_approved_by = fields.Many2one("res.users", string="Partner approved by")
    approval_date = fields.Date(string="Approval date")

    conditional_line_ids = fields.One2many(
        "qaco.onboarding.conditional.acceptance",
        "onboarding_id",
        string="Conditional Acceptance Tracker",
    )
    fee_term_ids = fields.One2many(
        "qaco.onboarding.fee.terms", "onboarding_id", string="Fee & Collection Terms"
    )

    @api.depends(
        "complexity_estimates",
        "complexity_revenue",
        "complexity_going_concern",
        "complexity_related_party",
        "complexity_group",
        "complexity_regulatory",
        "complexity_it",
        "complexity_judgments",
    )
    def _compute_engagement_score(self):
        """Simple weighted score: sum of trigger flags * 10 (capped 100)"""
        for rec in self:
            score = 0
            flags = [
                rec.complexity_estimates,
                rec.complexity_revenue,
                rec.complexity_going_concern,
                rec.complexity_related_party,
                rec.complexity_group,
                rec.complexity_regulatory,
                rec.complexity_it,
                rec.complexity_judgments,
            ]
            score += sum(10 for f in flags if f)
            # add time pressure influence
            if rec.time_pressure_risk == "medium":
                score += 5
            elif rec.time_pressure_risk == "high":
                score += 10
            if score > 100:
                score = 100
            rec.engagement_score = int(score)
            # derive rating
            if score >= 70:
                rec.engagement_risk_rating = "high"
            elif score >= 40:
                rec.engagement_risk_rating = "medium"
            else:
                rec.engagement_risk_rating = "low"

    @api.depends("engagement_decision", "engagement_score")
    def _compute_eqcr_required(self):
        for rec in self:
            rec.eqcr_required = (
                rec.engagement_risk_rating == "high"
                or rec.engagement_decision == "conditions"
                or bool(rec.first_year)
            )

    @api.constrains("engagement_risk_rating")
    def _check_risk_and_screening_before_approval(self):
        """Prevent partner approval / finalization if essential checks are incomplete or sanctions block."""
        for rec in self:
            if rec.state in ("partner_approved", "locked"):
                # ensure engagement risk rating is finalized
                if not rec.engagement_risk_rating:
                    raise ValidationError(
                        _("Engagement risk rating must be set before partner approval.")
                    )
                # AML obligations
                if rec.aml_applicable and (
                    not rec.client_identity_verified or not rec.ubo_verified
                ):
                    raise ValidationError(
                        _(
                            "AML/KYC applicable but identity/UBO verification incomplete."
                        )
                    )
                # sanctions check: if any screening exists and conclusion is block, prevent approval
                for s in rec.sanctions_screen_ids:
                    if s.screening_conclusion == "block" or s.sanctions_hit:
                        raise ValidationError(
                            _(
                                "Sanctions / PEP screening blocked approval until resolved (see screening records)."
                            )
                        )
                # fee retainer / collection control check when collection risk high
                ft = rec.fee_terms_id or (rec.fee_term_ids and rec.fee_term_ids[0])
                if (
                    ft
                    and ft.collection_risk_rating == "high"
                    and not ft.retainer_amount
                ):
                    raise ValidationError(
                        _(
                            "High collection risk requires a retainer; set retainer before approval."
                        )
                    )
