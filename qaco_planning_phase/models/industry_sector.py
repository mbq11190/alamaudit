from odoo import models, fields, api


class IndustrySector(models.Model):
    _name = 'planning.industry.sector'
    _description = 'Industry and Sector Configuration'
    _order = 'sequence, name'

    name = fields.Char(string='Sector Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
    description = fields.Text(string='Description')

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Sector name must be unique!')
    ]
