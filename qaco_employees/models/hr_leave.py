from odoo import api, models


class HrLeave(models.Model):
    _inherit = "hr.leave"
    _description = "HR Leave extensions for QACO"

    @api.depends_context("uid")
    @api.depends("state", "employee_id")
    def _compute_can_cancel(self):
        user = self.env.user
        for leave in self:
            leave.can_cancel = user.has_group(
                "qaco_employees.group_qaco_employee_administrator"
            )

    def action_cancel(self):
        """Cancel the leave (wrapper over standard refusal/cancel action)."""
        for leave in self:
            # Prefer using existing HR leave workflow if available
            if hasattr(leave, "action_refuse") and callable(getattr(leave, "action_refuse")):
                try:
                    leave.action_refuse()
                    continue
                except Exception:
                    pass
            # Fallback to setting state if no helper available
            try:
                leave.state = "cancel"
            except Exception:
                # Be defensive: if state field doesn't exist, silently ignore
                pass
        return True
