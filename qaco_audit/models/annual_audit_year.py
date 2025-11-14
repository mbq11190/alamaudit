from odoo import models, fields, api, exceptions
import re


class AnnualAuditYear(models.Model):
    _name = 'annual.audit.year'
    _description = 'Annual Audit Year'
    _order = 'name asc'

    name = fields.Char(string='Year', required=True, translate=True, help="Name of the year.")
    sequence = fields.Integer(string='Sequence', help="Sequence of the year.")
    audit_ids = fields.One2many('qaco.recurring.annual.audit', 'work_year', string='Annual Audits')
    is_folded_in_kanban = fields.Boolean(string='Folded in Kanban',
                                         help="Indicates if the stage is folded in Kanban view or not.")

    @api.model
    def create_year(self, year_name, sequence):
        if not self.search([('name', '=', year_name)], limit=1):
            self.create({'name': year_name, 'sequence': sequence})

    @api.constrains('name')
    def _check_name(self):
        for record in self:
            if not re.match(r'^20\d{2}$', record.name):
                raise exceptions.ValidationError(
                    "The name of the record does not follow the required format (2024)")
