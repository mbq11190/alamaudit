from odoo import models, fields, api


class AuditStages(models.Model):
    _name = 'audit.stages'
    _description = 'Audit Stages'
    _order = 'sequence'

    # Boolean field to indicate if the stage is active or not
    is_active = fields.Boolean(string='Active', default=True, help="Indicates if the stage is active or not.")
    # Name of the stage
    name = fields.Char(string='Name', required=True, translate=True, default='New', help="Name of the stage.")
    # Description of the stage
    description = fields.Text(string='Description', translate=True, help="Description of the stage.")
    # Sequence to order the stages
    sequence = fields.Integer(string='Sequence', default=1, help="Sequence to order the stages.")
    # Boolean field to indicate if the stage is folded in Kanban view or not
    is_folded_in_kanban = fields.Boolean(string='Folded in Kanban', help="Indicates if the stage is folded in Kanban view or not.")
