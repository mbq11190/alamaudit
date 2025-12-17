# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AuditRiskFS(models.Model):
    _name = "audit.risk.fs"
    _description = "Financial Statement Level Risk"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "engagement_id, sequence, id"

    engagement_id = fields.Many2one(
        "audit.engagement",
        string="Engagement",
        required=True,
        ondelete="cascade",
        index=True,
        tracking=True,
    )
    sequence = fields.Integer(default=10)
    name = fields.Char(string="Risk", required=True, tracking=True)
    code = fields.Char(string="Reference")
    isa_reference = fields.Char(string="ISA Reference")
    significant_risk = fields.Boolean(string="Significant Risk", tracking=True)
    fraud_risk = fields.Boolean(string="Fraud Risk", tracking=True)
    presumed_fraud = fields.Boolean(string="Presumed Fraud", help="Preset risks such as revenue recognition or management override.")
    inherent_likelihood = fields.Integer(string="Inherent Likelihood (1-5)", default=1, tracking=True)
    inherent_magnitude = fields.Integer(string="Inherent Magnitude (1-5)", default=1, tracking=True)
    inherent_score = fields.Integer(string="Inherent Risk", compute="_compute_scores", store=True)
    control_risk = fields.Integer(string="Control Risk (1-5)", default=1, tracking=True)
    detection_risk = fields.Integer(string="Detection Risk (1-5)", default=1, tracking=True)
    audit_risk = fields.Integer(string="Audit Risk", compute="_compute_scores", store=True)
    risk_level = fields.Selection(
        [
            ("low", "Low"),
            ("moderate", "Medium"),
            ("high", "High"),
        ],
        string="Risk Band",
        compute="_compute_scores",
        store=True,
    )
    professional_judgment = fields.Text(string="Professional Judgment", required=True)
    planned_response = fields.Text(string="Planned Response", required=True)
    response_owner_id = fields.Many2one("res.users", string="Response Owner")
    assertion_risk_ids = fields.One2many("audit.risk.assertion", "fs_risk_id", string="Assertion Risks")

    @api.depends("inherent_likelihood", "inherent_magnitude", "control_risk", "detection_risk")
    def _compute_scores(self):
        for record in self:
            il = record.inherent_likelihood or 0
            im = record.inherent_magnitude or 0
            record.inherent_score = il * im
            cr = record.control_risk or 0
            dr = record.detection_risk or 0
            record.audit_risk = record.inherent_score * cr * dr
            record.risk_level = record._band_from_score(record.inherent_score)

    def _band_from_score(self, score):
        if score >= 151:
            return "high"
        if score >= 51:
            return "moderate"
        return "low"

    @api.constrains(
        "inherent_likelihood",
        "inherent_magnitude",
        "control_risk",
        "detection_risk",
    )
    def _check_risk_scales(self):
        for record in self:
            record._ensure_scale(record.inherent_likelihood, "Inherent likelihood")
            record._ensure_scale(record.inherent_magnitude, "Inherent magnitude")
            record._ensure_scale(record.control_risk, "Control risk")
            record._ensure_scale(record.detection_risk, "Detection risk")

    def _ensure_scale(self, value, label):
        if value is None:
            raise ValidationError(_("%s must be between 1 and 5.") % label)
        if value < 1 or value > 5:
            raise ValidationError(_("%s must be between 1 and 5.") % label)
