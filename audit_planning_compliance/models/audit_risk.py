from __future__ import annotations

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AuditRiskAssessment(models.Model):
    """Risk register aligning with ISA 315 (Revised 2019)."""

    _name = "audit.risk.assessment"
    _description = "Audit Risk Assessment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "risk_rating desc, create_date desc"

    engagement_id = fields.Many2one("audit.engagement", required=True, ondelete="cascade", tracking=True)
    name = fields.Char(required=True, tracking=True)
    business_area = fields.Selection(
        [
            ("revenue", "Revenue"),
            ("cash", "Cash & Equivalents"),
            ("payables", "Payables"),
            ("payroll", "Payroll"),
            ("inventory", "Inventory"),
            ("fixed_assets", "Fixed Assets"),
            ("estimates", "Estimates & Judgments"),
            ("disclosures", "Disclosures"),
        ],
        required=True,
        help="ISA 315 para 25 requires identifying significant classes of transactions and balances.",
    )
    assertion = fields.Selection(
        [
            ("occurrence", "Occurrence"),
            ("completeness", "Completeness"),
            ("accuracy", "Accuracy"),
            ("valuation", "Valuation"),
            ("rights", "Rights & Obligations"),
            ("presentation", "Presentation & Disclosure"),
        ],
        required=True,
    )
    inherent_risk = fields.Integer(string="Inherent Risk (1-5)", required=True, default=3)
    control_risk = fields.Integer(string="Control Risk (1-5)", required=True, default=3)
    detection_risk = fields.Integer(string="Detection Risk", compute="_compute_scores", store=True)
    overall_risk = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("very_high", "Very High"),
        ],
        compute="_compute_scores",
        store=True,
    )
    risk_rating = fields.Float(string="Risk Score", compute="_compute_scores", store=True)
    risk_triggers = fields.Text(string="Risk Triggers", help="Mandatory for high risks (ISA 315 para 31).")
    risk_narrative = fields.Text(string="Risk Narrative", required=True)
    planned_substantive_procedures = fields.Text(string="Planned Substantive Procedures", required=True)
    planned_control_tests = fields.Text(string="Planned Control Tests")
    sign_off_user_id = fields.Many2one("res.users", string="Reviewer")
    sign_off_date = fields.Date()

    @api.depends("inherent_risk", "control_risk")
    def _compute_scores(self) -> None:
        for record in self:
            record.detection_risk = max(1, 6 - min(record.inherent_risk, record.control_risk))
            record.risk_rating = (record.inherent_risk or 0.0) * (record.control_risk or 0.0) * (record.detection_risk or 0.0)
            if record.risk_rating >= 60:
                record.overall_risk = "very_high"
            elif record.risk_rating >= 36:
                record.overall_risk = "high"
            elif record.risk_rating >= 18:
                record.overall_risk = "medium"
            else:
                record.overall_risk = "low"

    @api.constrains("overall_risk", "risk_triggers", "planned_substantive_procedures")
    def _check_high_risk_documentation(self) -> None:
        for record in self:
            if record.overall_risk in ("high", "very_high"):
                if not record.risk_triggers or not record.planned_substantive_procedures:
                    raise ValidationError(
                        _(
                            "High/very high risks require triggers and planned procedures (ISA 315 para 32)."
                        )
                    )

    def action_sign_off(self):
        self.ensure_one()
        if self.env.user not in (self.engagement_id.engagement_partner_id, self.engagement_id.engagement_manager_id):
            raise ValidationError(_("Only partner or manager may sign-off risks."))
        self.sign_off_user_id = self.env.user
        self.sign_off_date = fields.Date.context_today(self)
        high_risks = self.engagement_id.risk_ids.filtered(lambda r: r.overall_risk in ("high", "very_high"))
        self.engagement_id.risk_register_ready = bool(high_risks)
        self.env["audit.evidence.log"].log_event(
            name=_("Risk sign-off"),
            model_name=self._name,
            res_id=self.id,
            action_type="approval",
            note=_("Risk reviewed and response deemed adequate."),
            standard_reference="ISA 315 para 32",
        )
