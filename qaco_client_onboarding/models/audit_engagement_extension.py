from odoo import api, fields, models, _


class QacoAuditEngagement(models.Model):
    _inherit = 'qaco.audit.engagement'

    onboarding_ids = fields.One2many('qaco.client.onboarding', 'audit_id', string='Onboarding Records')
    onboarding_state = fields.Selection(
        related='onboarding_ids.state',
        readonly=True,
        string='Onboarding State'
    )
    onboarding_in_progress = fields.Boolean(compute='_compute_onboarding_in_progress', store=True)

    def _compute_onboarding_in_progress(self):
        for record in self:
            record.onboarding_in_progress = bool(record.onboarding_ids.filtered(lambda o: o.state not in ('approved', 'rejected')))

    def action_open_onboarding(self):
        self.ensure_one()
        onboarding = self.onboarding_ids.filtered(lambda o: o.state not in ('approved', 'rejected'))
        if onboarding:
            return {
                'name': _('Client Onboarding'),
                'type': 'ir.actions.act_window',
                'res_model': 'qaco.client.onboarding',
                'view_mode': 'form',
                'res_id': onboarding[0].id,
                'target': 'current',
            }
        return {
            'name': _('Client Onboarding'),
            'type': 'ir.actions.act_window',
            'res_model': 'qaco.client.onboarding',
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_audit_id': self.id},
        }