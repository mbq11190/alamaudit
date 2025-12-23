import logging
from collections import defaultdict
from datetime import datetime, time, timedelta

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class DailyAttendanceReport(models.Model):
    _name = "daily.attendance.report"
    _description = "Automated Daily Attendance Report"

    @api.model
    def generate_daily_attendance_report(self):
        tz = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("qaco_employees.report_tz", "Asia/Karachi")
        )
        today = fields.Date.context_today(self.with_context(tz=tz))
        start_date = today - timedelta(days=30)

        if today.weekday() in (5, 6):
            return

        employees = self.env["hr.employee"].search([])
        attendance = self.env["hr.attendance"].search([("check_in", ">=", start_date)])
        leaves = self.env["hr.leave"].search(
            [
                ("request_date_from", "<=", today),
                ("request_date_to", ">=", today),
                ("state", "=", "validate"),
            ]
        )
        leave_summary_model = self.env["leave.summary"]

        grouped_by_manager = defaultdict(list)
        manager_summary = defaultdict(
            lambda: {"late": 0, "approved": 0, "unauthorized": 0}
        )

        for emp in employees:
            emp_attendance = attendance.filtered(lambda a: a.employee_id.id == emp.id)
            checkins = []
            today_checkin = None

            for att in emp_attendance:
                employee_tz = emp.user_id.partner_id.tz or "Asia/Karachi"
                local_check_in = fields.Datetime.context_timestamp(
                    att.with_context(tz=employee_tz), att.check_in
                )
                if local_check_in.date() == today:
                    today_checkin = local_check_in
                else:
                    checkins.append(local_check_in.time())

            if checkins:
                avg_seconds = sum(
                    t.hour * 3600 + t.minute * 60 for t in checkins
                ) / len(checkins)
                avg_time = (datetime.min + timedelta(seconds=avg_seconds)).time()
            else:
                avg_time = None

            if not today_checkin:
                if leaves.filtered(lambda leave: leave.employee_id.id == emp.id):
                    today_status = "Approved Leave"
                    manager_summary[emp.parent_id.name if emp.parent_id else "N/A"][
                        "approved"
                    ] += 1
                else:
                    today_status = "Unauthorized Leave"
                    manager_summary[emp.parent_id.name if emp.parent_id else "N/A"][
                        "unauthorized"
                    ] += 1
                checkin_raw = None
            else:
                checkin_raw = today_checkin.time()
                today_status = today_checkin.strftime("%I:%M %p")
                if checkin_raw > time(10, 0):
                    manager_summary[emp.parent_id.name if emp.parent_id else "N/A"][
                        "late"
                    ] += 1

            summary = leave_summary_model.search(
                [("employee_id", "=", emp.id)], order="event_date desc", limit=1
            )

            record = {
                "name": emp.name,
                "client": (
                    emp.latest_deputation_client_id.name
                    if emp.latest_deputation_client_id
                    else "UNALLOCATED"
                ),
                "today_checkin": today_status,
                "checkin_raw": checkin_raw,
                "avg_checkin": avg_time.strftime("%I:%M %p") if avg_time else "N/A",
                "avg_time_sort": avg_time if avg_time else time.min,
                "allowed_leaves": summary.allowed_leaves if summary else 0,
                "availed_leaves": summary.closing_leaves if summary else 0,
                "remaining_leaves": summary.remaining_leaves if summary else 0,
                "department": emp.department_id.name if emp.department_id else "N/A",
                "manager": emp.parent_id.name if emp.parent_id else "N/A",
            }

            grouped_by_manager[record["manager"]].append(record)

        final_report = []
        for manager, group in grouped_by_manager.items():
            group.sort(key=lambda r: r["avg_time_sort"], reverse=True)
            final_report.append(
                {"is_manager_header": True, "manager": manager, "count": len(group)}
            )
            final_report.extend(group)

        total_employees = len(employees)
        present_employees = sum(
            1 for r in final_report if isinstance(r.get("checkin_raw"), time)
        )
        approved_leaves = sum(
            1 for r in final_report if r.get("today_checkin") == "Approved Leave"
        )
        unauthorized_leaves = sum(
            1 for r in final_report if r.get("today_checkin") == "Unauthorized Leave"
        )
        late_checkins = sum(
            1
            for r in final_report
            if isinstance(r.get("checkin_raw"), time) and r["checkin_raw"] > time(10, 0)
        )

        report_date = today.strftime("%d %B %Y")

        # sort manager_summary by late check-ins and then unauthorized leaves
        sorted_summary = sorted(
            manager_summary.items(),
            key=lambda x: (-x[1]["late"], -x[1]["unauthorized"]),
        )

        html_body = """
        <h3 style='color: #006666;'>Manager-wise Summary</h3>
        <table style='background-color: #e0f7fa;'>
            <tr style='background-color: #00695c; color: white;'>
                <th style='text-align: center;'>Manager Name</th>
                <th style='text-align: center;'>Late Check-ins</th>
                <th style='text-align: center;'>Approved Leaves</th>
                <th style='text-align: center;'>Unauthorized Leaves</th>
                <th style='text-align: center;'>Total Employees Managed</th>
            </tr>
        """

        for manager, data in sorted_summary:
            total_managed = (
                len(grouped_by_manager[manager]) if manager in grouped_by_manager else 0
            )
            html_body += f"""
            <tr style='text-align: center;'>
                <td>{manager}</td>
                <td>{data['late']}</td>
                <td>{data['approved']}</td>
                <td>{data['unauthorized']}</td>
                <td>{total_managed}</td>
            </tr>
            """

        html_body += "</table><br>"

        html_body += """
        <table>
            <tr>
                <th>S.No</th>
                <th>Employee Name</th>
                <th>Client</th>
                <th>Department</th>
                <th>Manager</th>
                <th>Today's Check-in</th>
                <th>Avg. Check-in (30 Days)</th>
                <th>Allowed Leaves</th>
                <th>Availed Leaves</th>
                <th>Remaining Leaves</th>
            </tr>
        """

        row_color1 = "#f9f9f9"
        row_color2 = "#e6f2ff"
        row_num = 1
        manager_rowspan = {}
        for row in final_report:
            if row.get("is_manager_header"):
                manager = row["manager"]
                manager_rowspan[manager] = row["count"]
                continue

        processed_managers = set()
        for idx, row in enumerate(final_report):
            if row.get("is_manager_header"):
                continue

            bg = row_color1 if row_num % 2 else row_color2
            checkin_display = row["today_checkin"]
            if row["checkin_raw"] and row["checkin_raw"] > time(10, 0):
                checkin_display = f"<span class='late-checkin'>{checkin_display}</span>"

            html_body += f"<tr style='background-color: {bg};'>"
            html_body += f"<td>{row_num}</td>"
            html_body += f"<td>{row['name']}</td>"
            html_body += f"<td>{row['client']}</td>"
            html_body += f"<td>{row['department']}</td>"

            if row["manager"] not in processed_managers:
                rowspan = manager_rowspan[row["manager"]]
                html_body += f"<td rowspan='{rowspan}' style='vertical-align: middle; text-align: center;'>{row['manager']}</td>"
                processed_managers.add(row["manager"])

            html_body += f"<td>{checkin_display}</td>"
            html_body += f"<td>{row['avg_checkin']}</td>"
            html_body += f"<td>{row['allowed_leaves']}</td>"
            html_body += f"<td>{row['availed_leaves']}</td>"
            html_body += f"<td>{row['remaining_leaves']}</td>"
            html_body += "</tr>"
            row_num += 1

        html_body += "</table>"

        self.send_email(
            body_html=html_body,
            total_employees=total_employees,
            present_employees=present_employees,
            approved_leaves=approved_leaves,
            unauthorized_leaves=unauthorized_leaves,
            late_checkins=late_checkins,
            report_date=report_date,
        )

    def send_email(
        self,
        body_html,
        total_employees,
        present_employees,
        approved_leaves,
        unauthorized_leaves,
        late_checkins,
        report_date,
    ):
        try:
            target_designations = [
                "HR Manager",
                "Admin Manager",
                "Assistant Manager",
                "Manager",
                "Partner",
            ]

            recipient_employees = self.env["hr.employee"].search(
                [
                    ("designation_id.name", "in", target_designations),
                    ("work_email", "!=", False),
                ]
            )

            email_list = list(
                set(emp.work_email for emp in recipient_employees if emp.work_email)
            )

            if not email_list:
                return

            html = f"""
            <html><head><style>
            table {{ font-family: Arial, sans-serif; border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid black; text-align: left; padding: 8px; }}
            th {{ background-color: #004080; color: white; }}
            span.late-checkin {{ color: red; font-weight: bold; }}
            </style></head><body>
            <p>Dear Team,</p>
            <p>Daily Attendance Report - {report_date}</p>
            <p><strong>Summary:</strong></p>
            <ul>
                <li>Total Employees: {total_employees}</li>
                <li>Present Today: {present_employees}</li>
                <li>Approved Leaves: {approved_leaves}</li>
                <li>Unauthorized Leaves: {unauthorized_leaves}</li>
                <li>Late Check-ins (after 10:00 AM): {late_checkins}</li>
            </ul>
            {body_html}
            <p>Best Regards,<br><strong>Odoo System</strong></p>
            </body></html>
            """

            mail_values = {
                "subject": "Daily Attendance Report",
                "email_to": ",".join(email_list),
                "email_from": self.env.user.email or "admin@company.com",
                "body_html": html,
            }

            mail = self.env["mail.mail"].create(mail_values)
            mail.send()

        except Exception as e:
            _logger.error(f"Failed to send Daily Attendance Report: {str(e)}")
