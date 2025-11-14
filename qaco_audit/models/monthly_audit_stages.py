from odoo import models, fields


class MonthlyAuditStages(models.Model):
    _name = 'monthly.audit.stages'
    _description = 'Monthly Audit Stages'
    _order = 'sequence'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=1)
    is_folded_in_kanban = fields.Boolean(string='Folded in Kanban')
