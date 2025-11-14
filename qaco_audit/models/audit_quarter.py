from odoo import models, fields, api, exceptions
from dateutil.relativedelta import relativedelta
import re


class AuditQuarter(models.Model):
    _name = 'audit.quarter'
    _description = 'Audit Quarter'
    _order = 'name asc'

    name = fields.Char(string='Quarter', required=True, translate=True,
                       help="Name of the quarter.")
    sequence = fields.Integer(string='Sequence', help="Sequence of the quarter.")
    audit_ids = fields.One2many('qaco.quarterly.audit', 'work_quarter',
                                string='Quarterly Audits')
    is_folded_in_kanban = fields.Boolean(string='Folded in Kanban',
                                         help="Indicates if the stage is folded in Kanban view or not.")

    @api.model
    def create_quarter(self, next_quarter, sequence):
        quarter_exists = self.search([('name', '=', next_quarter)], limit=1)
        if not quarter_exists:
            self.create({'name': next_quarter, 'sequence': sequence})

    @api.model
    def create_next_two_quarters(self):
        quarter_dict = {1: "01-Jan-Mar", 2: "02-Apr-Jun", 3: "03-Jul-Sep", 4: "04-Oct-Dec"}
        today = fields.Date.today()
        max_sequence = self.search([], order='sequence desc', limit=1).sequence

        next_quarter_date = today + relativedelta(months=3)
        next_quarter_num = (next_quarter_date.month - 1) // 3 + 1
        next_quarter_name = f"{next_quarter_date.year}-{quarter_dict[next_quarter_num]}"
        self.create_quarter(next_quarter_name, max_sequence + 1)

        quarter_after_next_date = today + relativedelta(months=6)
        quarter_after_next_num = (quarter_after_next_date.month - 1) // 3 + 1
        quarter_after_next_name = f"{quarter_after_next_date.year}-{quarter_dict[quarter_after_next_num]}"
        self.create_quarter(quarter_after_next_name, max_sequence + 2)

    @api.model
    def delete_empty_quarters(self):
        today = fields.Date.today()
        current_year = today.year
        current_quarter = ((today.month - 1) // 3) + 1
        empty_quarters = self.search([]).filtered(
            lambda m: len(m.audit_ids) == 0 and (
                int(m.name[:4]) < current_year or
                (int(m.name[:4]) == current_year and int(m.name[5:7]) < current_quarter)
            )
        )
        empty_quarters.unlink()

    @api.constrains('name')
    def _check_name(self):
        for record in self:
            if not re.match(r"^\d{4}-\d{2}-[a-zA-Z]*-[a-zA-Z]*$", record.name):
                raise exceptions.ValidationError(
                    "The name of the record does not follow the required format (2024-01-Jan-Mar)")
