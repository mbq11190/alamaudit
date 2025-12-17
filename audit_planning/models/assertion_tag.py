# -*- coding: utf-8 -*-
from odoo import fields, models


class AuditAssertionTag(models.Model):
    _name = "audit.assertion.tag"
    _description = "Audit Assertion"
    _order = "sequence, name"

    name = fields.Char(string="Assertion", required=True)
    code = fields.Char(string="Code", required=True)
    isa_reference = fields.Char(string="ISA Reference")
    sequence = fields.Integer(default=10)

    _sql_constraints = [
        ("assertion_code_unique", "unique(code)", "Assertion code must be unique."),
    ]
