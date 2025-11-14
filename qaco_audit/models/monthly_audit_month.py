from odoo import models, fields, api, exceptions
from dateutil.relativedelta import relativedelta
import re


class MonthlyAuditMonth(models.Model):
    _name = 'monthly.audit.month'
    _description = 'Audit Month'
    _order = 'name asc'

    name = fields.Char(string='Month', required=True, translate=True,
                       help="Name of the month in format YYYY-MM-Mmm")
    sequence = fields.Integer(string='Sequence', help="Sequence of the month.")
    audit_ids = fields.One2many('qaco.monthly.internal.audit', 'month_id',
                                string='Monthly Internal Audits')
    is_folded_in_kanban = fields.Boolean(
        string='Folded in Kanban',
        help="Indicates if the stage is folded in Kanban view or not.")

    @api.model
    def create_month(self, next_month, sequence):
        month_exists = self.search([('name', '=', next_month)], limit=1)
        if not month_exists:
            self.create({'name': next_month, 'sequence': sequence})

    @api.model
    def create_next_two_months(self):
        today = fields.Date.today()
        max_sequence = self.search([], order='sequence desc', limit=1).sequence

        next_month_date = today + relativedelta(months=1)
        next_month_name = next_month_date.strftime('%Y-%m-%b')
        self.create_month(next_month_name, max_sequence + 1)

        month_after_next_date = today + relativedelta(months=2)
        month_after_next_name = month_after_next_date.strftime('%Y-%m-%b')
        self.create_month(month_after_next_name, max_sequence + 2)

    @api.model
    def delete_empty_months(self):
        today = fields.Date.today()
        current_year = today.year
        current_month = today.month

        empty_months = self.search([]).filtered(
            lambda m: len(m.audit_ids) == 0 and
                      (int(m.name.split("-")[0]) < current_year or
                       (int(m.name.split("-")[0]) == current_year and
                        int(m.name.split("-")[1]) < current_month)))
        empty_months.unlink()

    @api.constrains('name')
    def _check_name(self):
        for record in self:
            if not re.match(r'^20\d{2}-(0[1-9]|1[0-2])-[a-zA-Z]*$', record.name):
                raise exceptions.ValidationError(
                    "The name of the record does not follow the required format (2024-01-Jan)")
