from odoo import models, fields


class AuditQuarterStages(models.Model):
    _name = 'audit.quarter.stages'
    _description = 'Audit Quarter Stages'
    _order = 'sequence'

    is_active = fields.Boolean(string='Active', default=True,
                               help="Indicates if the stage is active or not.")
    name = fields.Char(string='Name', required=True, translate=True, default='New',
                       help="Name of the stage.")
    description = fields.Text(string='Description', translate=True,
                              help="Description of the stage.")
    sequence = fields.Integer(string='Sequence', default=1,
                              help="Sequence to order the stages.")
    is_folded_in_kanban = fields.Boolean(string='Folded in Kanban',
                                         help="Indicates if the stage is folded in Kanban view or not.")
