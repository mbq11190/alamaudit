# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ExecutionPhase(models.Model):
    _name = 'qaco.execution.phase'
    _description = 'Execution Phase'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    audit_id = fields.Many2one('qaco.audit', string='Audit', required=True, ondelete='cascade')
    client_id = fields.Many2one('res.partner', string='Client Name', related='audit_id.client_id', readonly=True, store=True)

    @api.depends('audit_id', 'client_id')
    def _compute_name(self):
        for record in self:
            if record.client_id:
                record.name = f"Execution - {record.client_id.name}"
            else:
                record.name = "Execution Phase"
