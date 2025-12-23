import uuid

from odoo import fields, models


class LeaveAdjustmentApproval(models.Model):
    _name = "leave.adjustment.approval"
    _description = "Leave Adjustment Approval"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    adjustment_id = fields.Many2one("leave.adjustment", string="Leave Adjustment")
    validating_users_id = fields.Many2one(
        "res.users", string="Approver", domain="[('share','=',False)]"
    )
    is_validation_status = fields.Boolean(
        string="Approved", readonly=True, default=False, tracking=True
    )
    is_manager = fields.Boolean(string="Manager", readonly=True, default=False)
    is_partner = fields.Boolean(string="Partner", readonly=True, default=False)
    approve_token = fields.Char(
        readonly=True, copy=False, default=lambda self: str(uuid.uuid4())
    )

    _sql_constraints = [
        (
            "unique_adjustment_user",
            "unique(adjustment_id, validating_users_id)",
            "An approver can only be added once per leave adjustment.",
        )
    ]
