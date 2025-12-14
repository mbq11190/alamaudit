# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AuditPlanningChecklist(models.Model):
    _name = "audit.planning.checklist"
    _description = "Audit Planning Checklist"
    _order = "planning_id, id"

    planning_id = fields.Many2one(
        "audit.planning",
        string="Planning",
        required=False,
        ondelete="cascade",
        index=True,
    )
    name = fields.Char(string="Item", required=True)
    isa_reference = fields.Char(string="ISA Reference")
    is_mandatory = fields.Boolean(string="Mandatory", default=True)
    completed = fields.Boolean(string="Completed", default=False)
    is_template = fields.Boolean(string="Template Item", default=False, help="Template rows copied into new plans.")

    @api.onchange("completed")
    def _onchange_completed(self):
        # Keep chatter consistent when checklist items change.
        if self.planning_id and self._origin:
            self.planning_id.message_post(
                body=f"Checklist item '{self.name}' marked {'completed' if self.completed else 'incomplete'}."
            )

    @api.constrains("planning_id", "is_template")
    def _check_planning_required(self):
        for rec in self:
            if not rec.is_template and not rec.planning_id:
                raise ValidationError("Planning checklist rows must belong to a plan unless marked as template.")
