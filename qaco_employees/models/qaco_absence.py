from datetime import date, datetime, time

from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    is_absent_today = fields.Boolean(compute="_compute_absent_today", store=True)
    active = fields.Boolean("Active", default=True)
    create_date = fields.Datetime("Created On", readonly=True, index=True)
    write_date = fields.Datetime("Last Updated On", readonly=True)

    def action_archive(self):
        self.write({"active": False})

    @api.depends(
        "attendance_ids.check_in",
        "attendance_ids.check_out",
        "attendance_ids.employee_id",
    )
    def _compute_absent_today(self):
        today_start = datetime.combine(date.today(), time.min)
        today_end = datetime.combine(date.today(), time.max)
        for record in self:
            domain = [
                ("employee_id", "=", record.id),
                ("check_in", ">=", today_start),
                ("check_in", "<=", today_end),
            ]
            employee_attendances_today = self.env["hr.attendance"].search(domain)
            if not employee_attendances_today or all(
                att.check_out for att in employee_attendances_today
            ):
                record.is_absent_today = True
            else:
                record.is_absent_today = False
