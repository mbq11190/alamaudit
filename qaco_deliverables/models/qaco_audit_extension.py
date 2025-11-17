# -*- coding: utf-8 -*-
from odoo import models, fields, api


class QacoAudit(models.Model):
    _inherit = 'qaco.audit'

    # Deliverables
    deliverables_id = fields.Many2one(
        'qaco.deliverables',
        string='Deliverables',
        compute='_compute_deliverables_id'
    )
    deliverables_state = fields.Selection(
        related='deliverables_id.state',
        string='Deliverables Status'
    )
    deliverables_count = fields.Integer(
        string='Deliverables Count',
        compute='_compute_deliverables_count'
    )

    def _compute_deliverables_id(self):
        for record in self:
            deliverables = self.env['qaco.deliverables'].search(
                [('audit_id', '=', record.id)], limit=1
            )
            record.deliverables_id = deliverables.id if deliverables else False

    def _compute_deliverables_count(self):
        for record in self:
            record.deliverables_count = self.env['qaco.deliverables'].search_count(
                [('audit_id', '=', record.id)]
            )

    def action_open_deliverables(self):
        self.ensure_one()
        
        existing_deliverables = self.env['qaco.deliverables'].search(
            [('audit_id', '=', self.id)], limit=1
        )
        
        if existing_deliverables:
            return {
                'name': 'Audit Deliverables',
                'type': 'ir.actions.act_window',
                'res_model': 'qaco.deliverables',
                'view_mode': 'form',
                'res_id': existing_deliverables.id,
                'target': 'current',
                'context': {'default_audit_id': self.id}
            }
        else:
            return {
                'name': 'Audit Deliverables',
                'type': 'ir.actions.act_window',
                'res_model': 'qaco.deliverables',
                'view_mode': 'form',
                'target': 'current',
                'context': {'default_audit_id': self.id}
            }
