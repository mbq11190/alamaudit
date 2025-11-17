# -*- coding: utf-8 -*-
from odoo import models, fields, api


class QacoAudit(models.Model):
    _inherit = 'qaco.audit'

    # Client Onboarding
    onboarding_id = fields.Many2one(
        'qaco.client.onboarding',
        string='Client Onboarding',
        compute='_compute_onboarding_id',
        store=True
    )
    onboarding_state = fields.Selection(
        related='onboarding_id.state',
        string='Onboarding Status',
        store=True
    )
    onboarding_count = fields.Integer(
        string='Onboarding Count',
        compute='_compute_onboarding_count'
    )

    @api.depends('id')
    def _compute_onboarding_id(self):
        for record in self:
            onboarding = self.env['qaco.client.onboarding'].search(
                [('audit_id', '=', record.id)], limit=1
            )
            record.onboarding_id = onboarding.id if onboarding else False

    def _compute_onboarding_count(self):
        for record in self:
            record.onboarding_count = self.env['qaco.client.onboarding'].search_count(
                [('audit_id', '=', record.id)]
            )

    def action_open_client_onboarding(self):
        self.ensure_one()
        
        existing_onboarding = self.env['qaco.client.onboarding'].search(
            [('audit_id', '=', self.id)], limit=1
        )
        
        if existing_onboarding:
            return {
                'name': 'Client Onboarding',
                'type': 'ir.actions.act_window',
                'res_model': 'qaco.client.onboarding',
                'view_mode': 'form',
                'res_id': existing_onboarding.id,
                'target': 'current',
                'context': {'default_audit_id': self.id}
            }
        else:
            return {
                'name': 'Client Onboarding',
                'type': 'ir.actions.act_window',
                'res_model': 'qaco.client.onboarding',
                'view_mode': 'form',
                'target': 'current',
                'context': {
                    'default_audit_id': self.id,
                }
            }
