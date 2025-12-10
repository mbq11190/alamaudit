from odoo import _, api, fields, models
from odoo.exceptions import UserError

try:
    import openai
except ImportError:  # pragma: no cover - optional dependency
    openai = None


class AuditAIHelperMixin(models.AbstractModel):
    _name = 'audit.ai.helper.mixin'
    _description = 'AI Helper Mixin'

    def _call_openai(self, prompt, temperature=None, model=None):
        self.ensure_one()
        settings = self.env['audit.ai.settings'].sudo().get_active_settings()
        if not settings or not settings.openai_api_key:
            raise UserError(_('Configure an OpenAI API key in the AI settings panel before using automation.'))
        if openai is None:
            raise UserError(_('The python-openai library is not installed on this server.'))
        model_name = model or settings.model_version or 'gpt-5.1-codex-max-preview'
        temperature = temperature if temperature is not None else settings.temperature
        openai.api_key = settings.openai_api_key
        response = openai.ChatCompletion.create(
            model=model_name,
            messages=[{'role': 'user', 'content': prompt}],
            temperature=temperature,
        )
        return response['choices'][0]['message']['content']


class AuditCollaborationMixin(models.AbstractModel):
    _name = 'audit.collaboration.mixin'
    _description = 'Audit Collaboration Mixin'

    def schedule_review_activity(self, summary, activity_type_xmlid='mail.mail_activity_data_todo'):
        for record in self:
            users = getattr(record, 'assigned_user_ids', False)
            for user in users or []:
                record.activity_schedule(
                    activity_type_xmlid,
                    summary=summary,
                    user_id=user.id,
                )
        return True
