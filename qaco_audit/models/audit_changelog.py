# -*- coding: utf-8 -*-
from odoo import fields, models


class AuditChangeLog(models.Model):
    _name = "qaco.audit.changelog"
    _description = "Audit Record Change Log"

    audit_id = fields.Many2one(
        "qaco.audit", string="Audit", required=True, ondelete="cascade", index=True
    )
    field_name = fields.Char(string="Field")
    old_value = fields.Text(string="Old Value")
    new_value = fields.Text(string="New Value")
    changed_by = fields.Many2one("res.users", string="Changed By", readonly=True)
    changed_on = fields.Datetime(
        string="Changed On", default=fields.Datetime.now, readonly=True
    )
    note = fields.Text(string="Note")
