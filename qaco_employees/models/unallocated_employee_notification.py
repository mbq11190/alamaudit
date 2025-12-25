from collections import defaultdict
from datetime import datetime

from odoo import api, models


class UnallocatedEmployeeNotification(models.Model):
    _inherit = "hr.employee"
    _description = "Unallocated employee notification helpers"

    @api.model
    def send_unallocated_employee_email(self, custom_recipients=None, include_cc=False):
        """Sends an email notification for unallocated employees and employees assigned to 'LEAVE', with an optional CC for managers."""

        today = datetime.today().date()
        excluded_departments = ["Administration", "Partners", "Bahria Office"]

        # Get the UNALLOCATED and LEAVE client records
        unallocated_client = self.env["res.partner"].search(
            [("name", "=", "UNALLOCATED")], limit=1
        )
        leave_client = self.env["res.partner"].search([("name", "=", "LEAVE")], limit=1)

        # Find unallocated employees (no deputation or explicitly UNALLOCATED)
        unallocated_employees = self.env["hr.employee"].search(
            [
                "|",
                ("latest_deputation_client_id", "=", unallocated_client.id),
                ("latest_deputation_client_id", "=", False),
                ("department_id.name", "not in", excluded_departments),
            ]
        )

        # Find employees assigned to "LEAVE"
        employees_on_leave = (
            self.env["hr.employee"].search(
                [("latest_deputation_client_id", "=", leave_client.id)]
            )
            if leave_client
            else []
        )

        if not unallocated_employees and not employees_on_leave:
            return  # Exit if no relevant employees found

        # Group unallocated employees by department
        department_dict = defaultdict(list)
        leave_employees_list = []

        # Collect managers' emails
        manager_emails = set()

        for emp in unallocated_employees:
            department_name = (
                emp.department_id.name if emp.department_id else "No Department"
            )
            department_dict[department_name].append(emp.name)
            if emp.parent_id and emp.parent_id.work_email:
                manager_emails.add(emp.parent_id.work_email)

        for emp in employees_on_leave:
            department_name = (
                emp.department_id.name if emp.department_id else "No Department"
            )
            leave_employees_list.append(
                f"{emp.name} ({department_name})"
            )  # Add department name in parentheses
            if emp.parent_id and emp.parent_id.work_email:
                manager_emails.add(emp.parent_id.work_email)

        # Determine max rows for table
        max_rows = max(
            [len(emp_list) for emp_list in department_dict.values()]
            + [len(leave_employees_list)]
        )

        # Build recipient list from configured recipients when no custom list provided
        if custom_recipients:
            email_to = ",".join(custom_recipients)
        else:
            recipients = self.env["unallocated.employee.recipient"].sudo().search([])
            recipient_emails = [
                r.employee_id.work_email for r in recipients if r.employee_id.work_email
            ]
            email_to = ",".join(recipient_emails)

        # **CC will only be included if `include_cc=True`**
        email_cc = ",".join(manager_emails) if include_cc else ""

        # Prepare email content
        subject = (
            f"🚨 Unallocated Employees Notification - {today.strftime('%Y-%m-%d')}"
        )
        body = """
        <html>
        <body style="font-family: Arial, sans-serif;">
            <p>Dear Team,</p>
            <p>The following employees are currently <strong>unallocated</strong> or assigned to <strong>LEAVE</strong>:</p>
            <table style="width:100%; border-collapse: collapse; border: 1px solid black;">
                <tr style="background-color: #004080; color: white;">
        """

        # Add department headers
        for department in department_dict.keys():
            body += (
                f'<th style="border: 1px solid black; padding: 10px;">{department}</th>'
            )
        body += '<th style="border: 1px solid black; padding: 10px;">On LEAVE</th>'
        body += "</tr>"

        # Populate employee names row-wise
        for row in range(max_rows):
            body += (
                '<tr style="background-color: #f2f2f2;">' if row % 2 == 0 else "<tr>"
            )
            for department in department_dict.keys():
                emp_list = department_dict[department]
                employee_name = emp_list[row] if row < len(emp_list) else ""
                body += f'<td style="border: 1px solid black; padding: 10px; text-align: center;">{employee_name}</td>'

            # Add employees assigned to LEAVE
            leave_employee_name = (
                leave_employees_list[row] if row < len(leave_employees_list) else ""
            )
            body += f'<td style="border: 1px solid black; padding: 10px; text-align: center;">{leave_employee_name}</td>'
            body += "</tr>"

        body += """
            </table>
            <p>Please take necessary action to reassign these employees.</p>
            <p>Best Regards,</p>
            <p><strong>Odoo System</strong></p>
        </body>
        </html>
        """

        # Send email
        mail_values = {
            "subject": subject,
            "body_html": body,
            "email_to": email_to,
            "email_cc": email_cc,  # **Commented out for testing**
            "email_from": self.env.user.email or "admin@company.com",
        }

        if include_cc:  # Only add CC if explicitly enabled
            mail_values["email_cc"] = email_cc

        self.env["mail.mail"].sudo().create(mail_values).send()

        return True
