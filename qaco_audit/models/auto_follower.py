from odoo import models, fields


class AuditAutoFollower(models.Model):
    _name = 'qaco_audit.auto.follower'
    _description = 'Audit Auto Follower'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        ondelete='cascade',
    )

