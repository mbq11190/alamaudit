from odoo import api, fields, models


class AuditAISettings(models.Model):
    _name = "audit.ai.settings"
    _description = "AI Configuration"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(default="Default AI Configuration", tracking=True)
    openai_api_key = fields.Char(string="OpenAI API Key", tracking=True)
    temperature = fields.Float(
        default=0.2,
        help="Default creativity level for generated content.",
        tracking=True,
    )
    model_version = fields.Selection(
        [
            ("gpt-5.1-codex-max-preview", "GPT-5.1-Codex-Max (Preview)"),
            ("gpt-4o", "GPT-4o"),
            ("gpt-4o-mini", "GPT-4o Mini"),
            ("gpt-4.1-mini", "GPT-4.1 Mini"),
        ],
        default="gpt-5.1-codex-max-preview",
        tracking=True,
    )
    active = fields.Boolean(default=True)

    @api.model
    def get_active_settings(self):
        settings = self.search([("active", "=", True)], limit=1)
        if not settings:
            settings = self.search([], limit=1)
        if not settings:
            settings = self.create({})
        return settings

    @api.model
    def get_key(self):
        return self.get_active_settings().openai_api_key
