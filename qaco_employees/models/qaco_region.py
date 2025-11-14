from odoo import models, fields

class QACORegion(models.Model):
    _name = 'qaco.region'
    _description = 'QACO Region'

    name = fields.Char(string='Area Name', required=True)