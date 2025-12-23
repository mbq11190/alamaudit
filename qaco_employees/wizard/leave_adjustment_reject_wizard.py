# -*- coding: utf-8 -*-
from odoo import _, fields, models
from odoo.exceptions import UserError


class LeaveAdjustmentRejectWizard(models.TransientModel):
    _name = "leave.adjustment.reject.wizard"
    _description = "Leave Adjustment Rejection Wizard"

    adjustment_id = fields.Many2one(
        "leave.adjustment", string="Adjustment", required=True
    )
    employee_name = fields.Char(
        related="adjustment_id.employee_id.name", string="Employee", readonly=True
    )
    adjustment_amount = fields.Float(
        related="adjustment_id.adjustment", string="Adjustment", readonly=True
    )
    adjustment_type = fields.Selection(
        related="adjustment_id.adjustment_type", string="Type", readonly=True
    )
    adjustment_date = fields.Date(
        related="adjustment_id.adjustment_date", string="Date", readonly=True
    )
    reason = fields.Text(
        related="adjustment_id.reason", string="Adjustment Reason", readonly=True
    )
    rejection_reason = fields.Text(
        string="Reason for Rejection",
        required=True,
        help="Please provide a clear reason for rejecting this adjustment",
    )

    def action_confirm_rejection(self):
        """Confirm rejection with reason."""
        self.ensure_one()
        if not self.rejection_reason:
            raise UserError(_("Please provide a reason for rejection."))

        # Call the rejection method with reason
        self.adjustment_id.do_reject_with_reason(self.rejection_reason)

        # Return notification
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Adjustment Rejected"),
                "message": _("The leave adjustment has been rejected."),
                "type": "warning",
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
