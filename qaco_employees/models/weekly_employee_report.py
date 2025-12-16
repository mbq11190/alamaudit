from odoo import models, fields, api
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)  # Logger for debugging

class WeeklyEmployeeReport(models.Model):
    _name = "weekly.employee.report"
    _description = "Automated Weekly Employee Allocation Report"

    @api.model
    def generate_employee_report(self):
        """Generate Weekly Employee Allocation Report and Send Email"""

        # Define date range for the last 7 days
        today = fields.Date.today()
        start_date = today - timedelta(days=7)

        # Load Employees & Transfers (Only transfers from the last week)
        employees = self.env["hr.employee"].search([])
        if not employees:
            return

        transfers = self.env["hr.employee.transfer"].search([
            ("employee_id", "in", employees.ids),
            ("transfer_date_to", ">=", start_date),
        ])

        # Special Clients (to be sorted separately)
        special_clients = ["UNALLOCATED", "LEAVE", "BAKERTILLY-STATELIFE", "BAKERTILLY-RDF"]

        # Department Sorting Order (Used for all clients)
        department_order = {
            "Audit": 1,
            "Outsourcing": 2,
            "BT-Q": 3,
            "BT-S": 4,
            "Advisory": 5,
            "Administration": 6,
            "Partners": 7,
            "Other": 8,  # Any other department should be last
        }

        # Function to get latest client based on transfer history
        def get_latest_client(employee):
            employee_transfers = transfers.filtered(lambda t: t.employee_id.id == employee.id)
            if employee_transfers:
                latest_transfer = employee_transfers.sorted("transfer_date_to", reverse=True)[0]
                return latest_transfer.to_client_id.name
            return "UNALLOCATED"

        # Collect Employee Allocations
        client_mapping = {}

        for emp in employees:
            latest_client = get_latest_client(emp)
            department = emp.department_id.name if emp.department_id else "Other"

            # Assign department priority for sorting
            department_priority = department_order.get(department, 8)

            # Calculate Experience
            if emp.date_of_joining:
                experience_years = round((today - emp.date_of_joining).days / 365, 1)
            elif emp.date_of_articles_registration:
                experience_years = round((today - emp.date_of_articles_registration).days / 365, 1)
            else:
                experience_years = 0

            if latest_client not in client_mapping:
                client_mapping[latest_client] = {
                    "No. Of Staff Deputed": 0,
                    "Employees": [],
                    "Client Sorting Priority": (
                        2 if latest_client == "UNALLOCATED" else
                        3 if latest_client == "LEAVE" else
                        4 if latest_client == "BAKERTILLY-STATELIFE" else
                        5 if latest_client == "BAKERTILLY-RDF" else 1  # Normal clients first
                    )
                }

            # Store employee details as a dictionary (for sorting by department later)
            client_mapping[latest_client]["Employees"].append({
                "name": emp.name,
                "manager": emp.parent_id.name if emp.parent_id else "N/A",
                "department": department,
                "department_priority": department_priority,  # Sorting key
                "experience": experience_years
            })
            client_mapping[latest_client]["No. Of Staff Deputed"] += 1  # Increase count

        # Sort employees within each client by department priority
        for client in client_mapping:
            client_mapping[client]["Employees"] = sorted(
                client_mapping[client]["Employees"], key=lambda x: x["department_priority"]
            )

        sorted_clients = sorted(
            client_mapping.items(),
            key=lambda kv: (
                kv[1]["Client Sorting Priority"],
                -kv[1]["No. Of Staff Deputed"],
                kv[0] or "",
            ),
        )

        table_html = self._generate_html_table(sorted_clients)

        # Send Email with HTML Table
        self.send_email(table_html)

    def _generate_html_table(self, sorted_clients):
        """Render HTML with continuous numbering and per-client shading."""
        employee_counter = 1

        html = """
        <html>
        <head>
        <style>
            body { font-family: Arial, sans-serif; }
            table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            th, td { padding: 8px; border: 1px solid #dddddd; text-align: left; vertical-align: top; }
            th { background-color: #004080; color: white; font-weight: bold; }
            
            /* ✅ Reduce width of "No. Of Staff Deputed" and "Experience" columns */
            th:nth-child(3), td:nth-child(3) { width: 8%; }  /* "No. Of Staff Deputed" */
            th:nth-child(7), td:nth-child(7) { width: 8%; }  /* "Experience (Years)" */
        </style>

        </head>
        <body>
        <p>Dear Team,</p>
        <p>Please find below the latest Weekly Employee Allocation Report:</p>
        <table>
            <tr>
                <th>S.No</th>
                <th>Client Name</th>
                <th>No. Of Staff Deputed</th>
                <th>Employee Name</th>
                <th>Manager Name</th>
                <th>Department</th>
                <th>Experience (Years)</th>
            </tr>
        """

        # Populate table rows with alternate row shading per client
        row_color = "#f9f9f9"
        serial = 1
        for client_name, data in sorted_clients:
            employees = data.get("Employees", [])
            if not employees:
                continue

            employee_count = len(employees)
            row_color = "#e6f2ff" if row_color == "#f9f9f9" else "#f9f9f9"

            for i, employee in enumerate(employees):
                numbered_employee_name = f"{employee_counter}. {employee['name']}"
                employee_counter += 1

                if i == 0:
                    html += f"""
                    <tr style="background-color: {row_color};">
                        <td rowspan="{employee_count}">{serial}</td>
                        <td rowspan="{employee_count}">{client_name}</td>
                        <td rowspan="{employee_count}">{data['No. Of Staff Deputed']}</td>
                        <td>{numbered_employee_name}</td>
                        <td>{employee.get('manager', 'N/A')}</td>
                        <td>{employee.get('department', 'Other')}</td>
                        <td>{employee.get('experience', 0)}</td>
                    </tr>
                    """
                else:
                    html += f"""
                    <tr style="background-color: {row_color};">
                        <td>{numbered_employee_name}</td>
                        <td>{employee.get('manager', 'N/A')}</td>
                        <td>{employee.get('department', 'Other')}</td>
                        <td>{employee.get('experience', 0)}</td>
                    </tr>
                    """

            serial += 1

        html += "</table><p>Best Regards,<br><strong>Odoo System</strong></p></body></html>"

        return html

    def send_email(self, email_body):
        """Send Weekly Employee Allocation Report to selected designations"""

        try:
            # Designations to receive the email
            target_designations = ['HR Manager', 'Admin Manager', 'Assistant Manager', 'Manager', 'Partner']

            # Get employees by designation
            recipient_employees = self.env['hr.employee'].search([
                ('designation_id.name', 'in', target_designations),
                ('work_email', '!=', False)
            ])

            email_to = list(set(emp.work_email for emp in recipient_employees if emp.work_email))

            _logger.info(f"Weekly Report - To: {email_to}")

            if not email_to:
                _logger.warning("No valid recipients found for Weekly Employee Report.")
                return

            mail_values = {
                "subject": "Weekly Employee Allocation Report",
                "email_to": ",".join(email_to),
                "email_from": self.env.user.email or "admin@company.com",
                "body_html": email_body,
            }

            mail = self.env["mail.mail"].create(mail_values)
            mail.send()

            _logger.info("Weekly Employee Report email sent successfully.")

        except Exception as e:
            _logger.error(f"Error sending Weekly Employee Report email: {str(e)}")
