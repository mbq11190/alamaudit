# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AuditEngagementChecklist(models.Model):
    _name = "audit.engagement.checklist"
    _description = "Audit Engagement Checklist"
    _order = "engagement_id, id"

    engagement_id = fields.Many2one(
        "audit.engagement",
        string="Engagement",
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
        if self.engagement_id and self._origin:
            self.engagement_id.message_post(
                body=f"Checklist item '{self.name}' marked {'completed' if self.completed else 'incomplete'}."
            )

    @api.constrains("engagement_id", "is_template")
    def _check_planning_required(self):
        for rec in self:
            if not rec.is_template and not rec.engagement_id:
                raise ValidationError("Checklist rows must belong to an engagement unless marked as template.")
