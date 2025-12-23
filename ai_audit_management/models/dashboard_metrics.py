from odoo import api, fields, models


class AuditDashboardMetrics(models.Model):
    _name = "audit.dashboard.metrics"
    _description = "Audit Dashboard Metrics"
    _inherit = ["mail.thread"]

    name = fields.Char(default="Audit KPIs", required=True)
    high_risk_clients = fields.Integer(tracking=True)
    materiality_benchmark = fields.Float(tracking=True)
    control_deficiency_heat = fields.Integer(
        string="Control Deficiency Heat", tracking=True
    )
    substantive_exceptions = fields.Integer(tracking=True)
    risk_distribution = fields.Json(string="Risk Distribution JSON")
    progress_timeline = fields.Json(string="Audit Progress Timeline JSON")
    ai_insights = fields.Text(string="AI Insights")

    @api.model
    def update_from_ai(self):
        record = self.search([], limit=1)
        if not record:
            record = self.create({})
        prompt = (
            "Generate concise KPI insights for audit portfolio: high risk clients, control issues, exceptions, forecast."
            " Return bullets only."
        )
        record.ai_insights = record.env["audit.ai.helper.mixin"]._call_openai(prompt)
        return record
