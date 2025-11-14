from odoo import models, fields


class QacoAuditExtend(models.Model):
    _inherit = 'qaco.audit'

    planning_phase_ids = fields.One2many('qaco.planning.phase', 'audit_id', string='Planning Phase Records')
