# -*- coding: utf-8 -*-

from odoo import fields, models


class FirmName(models.Model):
    _name = "audit.firm.name"
    _description = "Audit Firm Name Configuration"
    _order = "sequence, name"

    name = fields.Char(string="Firm Name", required=True)
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string="Active", default=True)
    description = fields.Text(string="Description")

    _sql_constraints = [("name_unique", "unique(name)", "Firm name must be unique!")]
