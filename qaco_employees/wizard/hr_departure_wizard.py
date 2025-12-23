# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class HrDepartureWizard(models.TransientModel):
    _inherit = "hr.departure.wizard"

    def action_register_departure(self):
        """
        Override hr_holidays version to add safety checks for empty recordsets.
        Prevents ValueError when calling ensure_one() on empty recordsets.

        This reimplements the hr_holidays logic with proper empty recordset checks.
        """
        # Call the base hr module's method (not hr_holidays)
        employee = self.employee_id
        if self.env.context.get("toggle_active", False) and employee.active:
            employee.with_context(no_wizard=True).toggle_active()
        employee.departure_reason_id = self.departure_reason_id
        employee.departure_description = self.departure_description
        employee.departure_date = self.departure_date

        # Now apply the hr_holidays logic with safety checks
        if hasattr(self, "cancel_leaves") and self.cancel_leaves:
            future_leaves = self.env["hr.leave"].search(
                [
                    ("employee_id", "=", self.employee_id.id),
                    ("date_to", ">", self.departure_date),
                    ("state", "!=", "refuse"),
                ]
            )
            # Safety check: only call action_refuse if there are records
            if future_leaves:
                future_leaves.action_refuse()

        if hasattr(self, "archive_allocation") and self.archive_allocation:
            employee_allocations = self.env["hr.leave.allocation"].search(
                [("employee_id", "=", self.employee_id.id)]
            )
            # Safety check: only call action_archive if there are records
            if employee_allocations:
                employee_allocations.action_archive()
