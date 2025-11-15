from __future__ import annotations

from typing import Optional

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from .audit_engagement import ENTITY_CLASSES


class AuditMaterialityConfig(models.Model):
    """Default percentages per entity class (ISA 320 para 10-14)."""

    _name = "audit.materiality.config"
    _description = "Materiality Configuration"

    name = fields.Char(required=True)
    entity_classification = fields.Selection(ENTITY_CLASSES, required=True)
    default_basis = fields.Selection(
        [
            ("pbt", "Profit before tax"),
            ("revenue", "Revenue"),
            ("assets", "Total assets"),
            ("equity", "Equity"),
        ],
        default="pbt",
    )
    default_pct_pbt = fields.Float(default=5.0)
    default_pct_revenue = fields.Float(default=1.0)
    default_pct_assets = fields.Float(default=1.5)
    default_pct_equity = fields.Float(default=3.0)
    performance_factor = fields.Float(default=0.75)
    tolerable_factor = fields.Float(default=0.5)


class AuditMateriality(models.Model):
    """Stores individual materiality computations (ISA 320)."""

    _name = "audit.materiality"
    _description = "Materiality Worksheet"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(default=lambda self: _("Materiality"), required=True)
    engagement_id = fields.Many2one("audit.engagement", required=True, ondelete="cascade")
    basis = fields.Selection(
        [
            ("pbt", "Profit before tax"),
            ("revenue", "Revenue"),
            ("assets", "Total assets"),
            ("equity", "Equity"),
        ],
        required=True,
        tracking=True,
        help="(ISA 320 para 10) Document the benchmark used for overall materiality.",
    )
    base_value = fields.Monetary(string="Benchmark Amount", tracking=True)
    base_source_type = fields.Selection(
        [
            ("tb_snapshot", "Trial balance snapshot"),
            ("account_move", "Accounting module"),
            ("manual", "Manual entry"),
        ],
        default="manual",
        tracking=True,
        help="Record the source of the benchmark (ISA 320 para 14).",
    )
    base_source_reference = fields.Char(string="Source Reference")
    default_percentage = fields.Float(string="Default %", readonly=True)
    applied_percentage = fields.Float(string="Applied %", required=True)
    overall_materiality = fields.Monetary(string="Overall Materiality", compute="_compute_amounts", store=True)
    performance_factor = fields.Float(string="Performance Factor", default=0.75)
    performance_materiality = fields.Monetary(string="Performance Materiality", compute="_compute_amounts", store=True)
    tolerable_factor = fields.Float(string="Tolerable Factor", default=0.5)
    tolerable_misstatement = fields.Monetary(string="Tolerable Misstatement", compute="_compute_amounts", store=True)
    currency_id = fields.Many2one(related="engagement_id.currency_id", store=True)
    justification_text = fields.Text(
        string="Justification",
        required=True,
        help="Explain any deviation from default benchmark (ISA 320 para 12).",
    )
    evidence_attachment_id = fields.Many2one("ir.attachment", string="Evidence Attachment")
    computed_by = fields.Many2one("res.users", default=lambda self: self.env.user)
    computed_on = fields.Datetime(default=fields.Datetime.now)
    approved = fields.Boolean(string="Partner Approved", default=False)

    @api.depends("base_value", "applied_percentage", "performance_factor", "tolerable_factor")
    def _compute_amounts(self) -> None:
        for record in self:
            record.overall_materiality = (record.base_value or 0.0) * (record.applied_percentage or 0.0) / 100.0
            record.performance_materiality = record.overall_materiality * (record.performance_factor or 0.0)
            record.tolerable_misstatement = record.overall_materiality * (record.tolerable_factor or 0.0)

    @api.constrains("applied_percentage", "default_percentage")
    def _check_justification(self) -> None:
        for record in self:
            if record.default_percentage and abs(record.applied_percentage - record.default_percentage) > 0.01 and not record.justification_text:
                raise ValidationError(
                    _("Provide justification when overriding default percentage (ISA 320 para 12).")
                )

    def action_partner_approve(self):
        self.ensure_one()
        if self.env.user not in (self.engagement_id.engagement_partner_id,):
            raise ValidationError(_("Only the engagement partner can approve materiality."))
        self.approved = True
        self.engagement_id.materiality_ready = True
        self.env["audit.evidence.log"].log_event(
            name=_("Materiality approved"),
            model_name=self._name,
            res_id=self.id,
            action_type="approval",
            note=self.justification_text,
            standard_reference="ISA 320 para 14; ICAP APM section 5",
        )


class AuditMaterialityWizard(models.TransientModel):
    """Wizard used to capture benchmark quickly."""

    _name = "audit.materiality.wizard"
    _description = "Materiality Wizard"

    engagement_id = fields.Many2one("audit.engagement", required=True)
    basis = fields.Selection(selection=AuditMateriality._fields["basis"].selection, required=True)
    base_value = fields.Float(required=True)
    base_source_type = fields.Selection(selection=AuditMateriality._fields["base_source_type"].selection, default="manual")
    base_source_reference = fields.Char()
    applied_percentage = fields.Float()
    justification_text = fields.Text(required=True)

    def action_apply(self):
        self.ensure_one()
        config = self.env["audit.materiality.config"].search(
            ["|", ("entity_classification", "=", self.engagement_id.entity_classification), ("entity_classification", "=", "other")],
            limit=1,
        )
        default_pct = 5.0
        if config:
            default_pct = getattr(config, f"default_pct_{self.basis}", default_pct)
        applied_pct = self.applied_percentage or default_pct
        materiality = self.env["audit.materiality"].create(
            {
                "engagement_id": self.engagement_id.id,
                "basis": self.basis,
                "base_value": self.base_value,
                "base_source_type": self.base_source_type,
                "base_source_reference": self.base_source_reference,
                "default_percentage": default_pct,
                "applied_percentage": applied_pct,
                "performance_factor": config.performance_factor if config else 0.75,
                "tolerable_factor": config.tolerable_factor if config else 0.5,
                "justification_text": self.justification_text,
            }
        )
        return materiality.action_partner_approve()


class AuditPlanningSettings(models.TransientModel):
    _inherit = "res.config.settings"

    materiality_performance_factor = fields.Float(string="Performance Factor", config_parameter="audit_planning.performance_factor", default=0.75)
    pbc_escalation_days = fields.Integer(string="PBC Escalation Days", config_parameter="audit_planning.pbc_escalation_days", default=3)

    def set_values(self):
        res = super().set_values()
        return res
