from datetime import datetime
from unittest.mock import patch

from odoo.tests import common


class DailyAttendanceReportTimezoneTest(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.env.company.partner_id.tz = "Asia/Karachi"
        self.employee = self.env["hr.employee"].create({"name": "Employee"})

    def test_report_uses_company_timezone(self):
        Attendance = self.env["hr.attendance"]
        check_in = datetime(2024, 1, 15, 5, 30, 0)
        Attendance.create({"employee_id": self.employee.id, "check_in": check_in})
        report = self.env["daily.attendance.report"]

        patch_path = (
            "odoo.addons.qaco_employees.models.daily_attendance_report."
            "DailyAttendanceReport.send_email"
        )
        with patch(
            "odoo.fields.Datetime.now", return_value=datetime(2024, 1, 15, 8, 0, 0)
        ):
            with patch(patch_path) as mock_send:
                report.generate_daily_attendance_report()
                args = mock_send.call_args[1]
                assert args["late_checkins"] == 1
                assert "10:30 AM" in args["body_html"]
