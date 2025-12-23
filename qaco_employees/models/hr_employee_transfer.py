import logging

from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)


class HrEmployeeTransfer(models.Model):
    _name = "hr.employee.transfer"
    _description = "Employee Transfer Record"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "transfer_date_from desc, id desc"
    _rec_name = "sequence"

    sequence = fields.Char(
        string="Reference", required=True, copy=False, readonly=True, default="/"
    )
    active = fields.Boolean(string="Active", default=True)

    employee_id = fields.Many2one("hr.employee", string="Employee", required=True)
    manager_id = fields.Many2one(
        "res.users",
        string="Manager",
        compute="_compute_manager",
        store=True,
        readonly=True,
    )
    from_client_id = fields.Many2one(
        "res.partner", string="From Client", readonly=True, store=True
    )
    to_client_id = fields.Many2one("res.partner", string="To Client", required=True)
    transfer_date_from = fields.Date(
        string="Transfer Date From", required=True, default=fields.Date.today
    )
    transfer_date_to = fields.Date(string="Transfer Date To", required=True)
    reason = fields.Text(string="Reason for Transfer")
    notes = fields.Text(string="Notes")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Pending Approval"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("returned", "Returned"),  # ✅ Ensure "Returned" is added here
        ],
        default="draft",
        string="Status",
        tracking=True,
    )

    previous_transfers_count = fields.Integer(
        string="Previous Transfers", compute="_compute_previous_transfers_count"
    )

    restricted_clients = [
        "LEAVE",
        "UNALLOCATED",
        "BAKERTILLY-RDF",
        "BAKERTILLY-STATELIFE",
    ]

    @api.constrains("transfer_date_from", "transfer_date_to")
    def _check_transfer_date_gap(self):
        """Ensure the date gap does not exceed allowed months.

        Default: 2 months. For 'Assistant Manager' and 'Manager': 6 months.
        """
        for record in self:
            if record.transfer_date_from and record.transfer_date_to:
                designation_name = (
                    (record.employee_id.designation_id.name or "").strip().lower()
                )
                allowed_months = (
                    6 if designation_name in ["assistant manager", "manager"] else 2
                )
                max_allowed_date = record.transfer_date_from + relativedelta(
                    months=allowed_months
                )
                if record.transfer_date_to > max_allowed_date:
                    raise ValidationError(
                        _(
                            "The gap between 'Transfer Date From' and 'Transfer Date To' cannot exceed %s months for this designation.",
                            allowed_months,
                        )
                    )

    def action_set_unallocated(self):
        """Mark employee as unallocated, update latest deputation client, and set stage to 'Returned'."""
        for record in self:
            if record.state != "approved":
                raise UserError(
                    "You can only mark employees as 'Unallocated' after approval."
                )

            if not record.employee_id:
                raise UserError("No employee selected.")

            unallocated_client = self.env["res.partner"].search(
                [("name", "=", "UNALLOCATED")], limit=1
            )
            if not unallocated_client:
                raise UserError(
                    "Unallocated client not found. Please create 'UNALLOCATED' in Clients."
                )

            # ✅ Update employee's latest deputation client and change state to "Returned"
            record.employee_id.write(
                {
                    "latest_deputation_client_id": unallocated_client.id,
                    # ✅ Ensure latest work location updates to Unallocated
                    "was_unallocated": True,  # ✅ Track that employee was unallocated
                }
            )

            # ✅ Change the state to "Returned"
            record.write({"state": "returned"})

    @api.model
    def auto_set_unallocated(self):
        """Automatically mark expired latest transfers as 'Returned' and notify managers."""
        today = fields.Date.today()
        unallocated_client = self.env["res.partner"].search(
            [("name", "=", "UNALLOCATED")], limit=1
        )

        if not unallocated_client:
            # Try to get from XML ID if seeded
            unallocated_client = self.env.ref(
                "qaco_employees.partner_unallocated", raise_if_not_found=False
            )

        if not unallocated_client:
            _logger.warning(
                "Unallocated client not found. Skipping auto_set_unallocated cron. Please create 'UNALLOCATED' in Clients or upgrade qaco_employees module."
            )
            return

        # ✅ Get the latest transfer for each employee
        all_transfers = self.env["hr.employee.transfer"].search(
            [("state", "in", ["approved", "returned"])], order="transfer_date_to desc"
        )

        latest_transfer_map = {}
        for transfer in all_transfers:
            emp_id = transfer.employee_id.id
            if emp_id not in latest_transfer_map:
                latest_transfer_map[emp_id] = transfer

        # ✅ Process only if latest transfer is expired
        transfers_to_unallocate = []
        for transfer in latest_transfer_map.values():
            if transfer.transfer_date_to < today:
                transfers_to_unallocate.append(transfer)

        for transfer in transfers_to_unallocate:
            employee = transfer.employee_id

            if employee.latest_deputation_client_id.id != unallocated_client.id:
                employee.write(
                    {
                        "latest_deputation_client_id": unallocated_client.id,
                        "was_unallocated": True,
                    }
                )

            if transfer.state != "returned":
                transfer.write({"state": "returned"})

            # ✅ Remove employee from previous client's geofence (if exists)
            from_client = transfer.to_client_id
            if from_client:
                geofence = self.env["hr.attendance.geofence"].search(
                    [("name", "=", from_client.name)], limit=1
                )
                if geofence:
                    geofence.write({"employee_ids": [(3, employee.id)]})

        # ✅ Now notify managers
        self.send_expiry_email_to_manager()

    def send_expiry_email_to_manager(self):
        """Sends email to each manager listing employees whose latest deputation expired and are currently unallocated and active."""
        today = fields.Date.today()
        unallocated_client = self.env["res.partner"].search(
            [("name", "=", "UNALLOCATED")], limit=1
        )

        if not unallocated_client:
            raise UserError(
                "Unallocated client not found. Please create 'UNALLOCATED' in Clients."
            )

        # ✅ Get all expired + returned transfers with active employees
        returned_transfers = self.env["hr.employee.transfer"].search(
            [
                ("state", "=", "returned"),
                ("transfer_date_to", "<", today),
                ("employee_id.active", "=", True),  # ✅ Only include active employees
            ]
        )

        # ✅ Pick only the latest one per employee
        latest_transfer_map = {}
        for transfer in returned_transfers:
            emp_id = transfer.employee_id.id
            if (
                emp_id not in latest_transfer_map
                or transfer.transfer_date_to
                > latest_transfer_map[emp_id].transfer_date_to
            ):
                latest_transfer_map[emp_id] = transfer

        # ✅ Filter: only if employee is still unallocated
        unallocated_transfers = [
            t
            for t in latest_transfer_map.values()
            if t.employee_id.latest_deputation_client_id.id == unallocated_client.id
        ]

        if not unallocated_transfers:
            return  # ✅ Nothing to email

        # ✅ Group by manager email
        manager_dict = {}
        for transfer in unallocated_transfers:
            if transfer.manager_id and transfer.manager_id.email:
                manager_email = transfer.manager_id.email
                manager_dict.setdefault(manager_email, []).append(transfer)

        # ✅ Send grouped email to each manager using QWeb template
        for manager_email, transfers in manager_dict.items():
            email_body = self.env["ir.qweb"]._render(
                "qaco_employees.email_transfer_expired",
                {
                    "manager_name": transfers[0].manager_id.name,
                    "transfers": transfers,
                },
                minimal_qcontext=True,
            )

            mail_values = {
                "subject": "Deputation Expired - Action Required",
                "email_to": manager_email,
                "email_from": self.env.user.email or "admin@company.com",
                "body_html": email_body,
            }

            self.env["mail.mail"].sudo().create(mail_values).send()

    @api.depends("employee_id", "employee_id.parent_id")
    def _compute_manager(self):
        """Automatically assign manager from the employee's parent_id field"""
        for record in self:
            if record.employee_id and record.employee_id.parent_id:
                record.manager_id = (
                    record.employee_id.parent_id.user_id
                )  # Assign the manager
            else:
                record.manager_id = None  # Ensure field clears if no manager is set

    @api.model_create_multi
    def create(self, vals_list):
        """Assign correct 'From Client' when creating a new transfer."""
        for vals in vals_list:
            if vals.get("sequence", "/") == "/":
                vals["sequence"] = (
                    self.env["ir.sequence"].next_by_code("transfer.sequence") or "/"
                )

            if "employee_id" in vals and "from_client_id" not in vals:
                employee = self.env["hr.employee"].browse(vals["employee_id"])

                if employee.was_unallocated:
                    # ✅ If employee was previously unallocated, set "UNALLOCATED"
                    unallocated_client = self.env["res.partner"].search(
                        [("name", "=", "UNALLOCATED")], limit=1
                    )
                    if unallocated_client:
                        vals["from_client_id"] = unallocated_client.id
                else:
                    # ✅ Otherwise, get last approved transfer
                    latest_approved = self.env["hr.employee.transfer"].search(
                        [
                            ("employee_id", "=", vals["employee_id"]),
                            ("state", "=", "approved"),
                        ],
                        order="transfer_date_to desc",
                        limit=1,
                    )

                    if latest_approved:
                        vals["from_client_id"] = latest_approved.to_client_id.id
                    else:
                        # ✅ If no approved transfer exists, fallback to "UNALLOCATED"
                        unallocated_client = self.env["res.partner"].search(
                            [("name", "=", "UNALLOCATED")], limit=1
                        )
                        if unallocated_client:
                            vals["from_client_id"] = unallocated_client.id

        return super(HrEmployeeTransfer, self).create(vals_list)

    def send_email_to_manager(self):
        """Sends an email notification to the manager for approval with a professionally styled table"""
        for record in self:
            if not record.manager_id:
                continue  # Skip if no manager is assigned

            email_body = self.env["ir.qweb"]._render(
                "qaco_employees.email_transfer_request",
                {
                    "manager_name": record.manager_id.name,
                    "transfer": record,
                },
                minimal_qcontext=True,
            )

            mail_values = {
                "subject": f"Approval Required: Employee Transfer - {record.employee_id.name}",
                "email_to": record.manager_id.email,
                "email_from": self.env.user.email or "admin@company.com",
                "body_html": email_body,
            }

            self.env["mail.mail"].sudo().create(mail_values).send()

    def action_submit(self):
        """Submit for approval and ensure manager_id is selected"""
        for record in self:
            if not record.manager_id:
                raise UserError(
                    "You cannot submit this transfer request without selecting a Manager."
                )

            client_name = record.to_client_id.name if record.to_client_id else ""
            # Try both job_title and job_id.name to cover all cases
            designation = (record.employee_id.designation_id.name or "").strip().lower()
            is_manager = designation == "manager"

            if client_name in self.restricted_clients:
                if is_manager and record.work_from not in ["firm", "partial"]:
                    raise UserError(
                        f"Invalid 'Work From' selection for restricted client '{client_name}'.\n\n"
                        f"Since the employee's designation is 'Manager', only the following options are allowed:\n"
                        f"✔ Firm Office\n"
                        f"✔ Partial (Client + Firm Office)\n\n"
                        f"Please update the 'Work From' field before submitting."
                    )
                elif not is_manager and record.work_from != "firm":
                    raise UserError(
                        f"Invalid 'Work From' selection for restricted client '{client_name}'.\n\n"
                        f"For this client, only the following option is allowed:\n"
                        f"✔ Firm Office\n\n"
                        f"Please update the 'Work From' field before submitting."
                    )

            # ✅ Continue with submit
            record.write({"state": "submitted"})

            # Create an approval request activity for the manager
            activity_id = record.activity_schedule(
                activity_type_id=self.env.ref("mail.mail_activity_data_todo").id,
                summary="Employee Transfer Approval Required",
                note=f"Please review and approve the transfer request for {record.employee_id.name}.",
                user_id=record.manager_id.id,
            )
            if activity_id:
                self.env["mail.activity"].browse(activity_id.id).action_done()

            record.send_email_to_manager()

    def action_approve(self):
        for record in self:
            if self.env.user != record.manager_id and not self.env.user.has_group(
                "base.group_system"
            ):
                raise UserError(
                    "Access Denied: Only the assigned manager or system admin can approve this request."
                )

            record.write({"state": "approved"})

            employee = record.employee_id
            to_client = record.to_client_id
            from_client = record.from_client_id
            work_from = record.work_from

            # ✅ Update latest deputation client
            employee.write(
                {"latest_deputation_client_id": to_client.id, "was_unallocated": False}
            )

            geofence_model = self.env["hr.attendance.geofence"]

            # ✅ Assign geofences only if employee will work from client or partial
            if work_from == "client":
                to_geofence = geofence_model.search(
                    [("name", "=", to_client.name)], limit=1
                )
                if not to_geofence:
                    to_geofence = geofence_model.create(
                        {
                            "name": to_client.name,
                            "description": f"Auto-created for {to_client.name}",
                        }
                    )
                to_geofence.write({"employee_ids": [(4, employee.id)]})

            # ✅ Remove from previous client's geofence regardless of work_from
            if from_client:
                from_geofence = geofence_model.search(
                    [("name", "=", from_client.name)], limit=1
                )
                if from_geofence:
                    from_geofence.write({"employee_ids": [(3, employee.id)]})

            # ✅ Auto-delete empty geofences
            today = fields.Date.today()
            empty_geofences = geofence_model.search(
                [
                    ("employee_ids", "=", False),
                    ("last_employee_removed_date", "!=", False),
                ]
            )
            for geo in empty_geofences:
                if (today - geo.last_employee_removed_date).days >= 60:
                    geo.unlink()

    def action_reject(self):
        """Reject transfer request (Only the assigned manager can reject)"""
        for record in self:
            if self.env.user != record.manager_id:
                raise UserError(
                    "Access Denied: Only the assigned manager can reject this request."
                )

            record.write({"state": "rejected"})

    def action_open_previous_transfers(self):
        return {
            "name": "Previous Transfers",
            "type": "ir.actions.act_window",
            "res_model": "hr.employee.transfer",
            "view_mode": "tree,form",
            "domain": [
                ("employee_id", "=", self.employee_id.id),
                ("id", "!=", self.id),
            ],
            "context": {"default_employee_id": self.employee_id.id},
        }

    @api.onchange("employee_id")
    def _onchange_employee_id(self):
        """Automatically set 'From Client' based on Unallocated status or last approved transfer."""
        for record in self:
            if record.employee_id:
                if record.employee_id.was_unallocated:
                    # ✅ If the employee was previously unallocated, set "UNALLOCATED"
                    unallocated_client = self.env["res.partner"].search(
                        [("name", "=", "UNALLOCATED")], limit=1
                    )
                    if unallocated_client:
                        record.from_client_id = unallocated_client.id
                else:
                    # ✅ Otherwise, get the last APPROVED transfer
                    latest_approved = self.env["hr.employee.transfer"].search(
                        [
                            ("employee_id", "=", record.employee_id.id),
                            ("state", "=", "approved"),
                        ],
                        order="transfer_date_to desc",
                        limit=1,
                    )

                    if latest_approved:
                        record.from_client_id = latest_approved.to_client_id.id
                    else:
                        # ✅ If no approved transfer exists, fallback to "UNALLOCATED"
                        unallocated_client = self.env["res.partner"].search(
                            [("name", "=", "UNALLOCATED")], limit=1
                        )
                        if unallocated_client:
                            record.from_client_id = unallocated_client.id

    @api.depends("employee_id")
    def _compute_previous_transfers_count(self):
        counts = self.env["hr.employee.transfer"].read_group(
            [
                ("employee_id", "in", self.mapped("employee_id").ids),
                ("id", "not in", self.ids),
            ],
            ["employee_id"],
            ["employee_id"],
        )
        count_dict = {rec["employee_id"][0]: rec["employee_id_count"] for rec in counts}
        for record in self:
            record.previous_transfers_count = count_dict.get(record.employee_id.id, 0)

    def action_archive(self):
        for record in self:
            record.write({"active": False})

    def action_unarchive(self):
        for record in self:
            record.write({"active": True})

    def send_pending_transfer_reminder(self):
        """Send email reminders to managers and partners for pending transfer approvals"""
        # Only get submitted transfers for active employees
        pending_transfers = self.env["hr.employee.transfer"].search(
            [("state", "=", "submitted"), ("employee_id.active", "=", True)]
        )

        if not pending_transfers:
            return  # ✅ No pending transfers, exit function

        reminder_dict = {}

        for transfer in pending_transfers:
            recipients = []

            # Add Manager (if exists)
            if (
                transfer.employee_id.parent_id
                and transfer.employee_id.parent_id.user_id
            ):
                recipients.append(transfer.employee_id.parent_id.user_id.email)

            # Add Partner (if needed)
            # if transfer.employee_id.partner_id and transfer.employee_id.partner_id.email:
            #     recipients.append(transfer.employee_id.partner_id.email)

            recipients = list(
                set(filter(None, recipients))
            )  # Remove duplicates & empty

            if not recipients:
                continue

            recipients_key = ",".join(recipients)

            if recipients_key not in reminder_dict:
                reminder_dict[recipients_key] = []

            reminder_dict[recipients_key].append(transfer)

        for recipients, transfers in reminder_dict.items():
            email_body = """
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; }
                    table { width: 100%; border-collapse: collapse; margin-top: 10px; }
                    th, td { padding: 10px; border: 1px solid #dddddd; text-align: left; }
                    th { background-color: #004080; color: white; font-weight: bold; }
                    tr:nth-child(even) { background-color: #f2f2f2; }
                </style>
            </head>
            <body>
                <p>Dear Approver,</p>
                <p>The following employee transfer requests are pending for approval:</p>
                <table>
                    <tr>
                        <th>Employee</th>
                        <th>From Client</th>
                        <th>To Client</th>
                        <th>Transfer Date</th>
                    </tr>
            """

            for transfer in transfers:
                email_body += f"""
                    <tr>
                        <td>{transfer.employee_id.name}</td>
                        <td>{transfer.from_client_id.name or 'N/A'}</td>
                        <td>{transfer.to_client_id.name}</td>
                        <td>{transfer.transfer_date_from} - {transfer.transfer_date_to}</td>
                    </tr>
                """

            email_body += """
                </table>
                <p>Please log in to Odoo to approve or reject these requests.</p>
                <p>Best Regards,</p>
                <p><strong>Odoo System</strong></p>
            </body>
            </html>
            """

            mail_values = {
                "subject": f"⚠️ Action Required: {len(transfers)} Employee Transfers Pending Approval",
                "email_to": recipients,
                "email_from": self.env.user.email or "admin@company.com",
                "body_html": email_body,
            }

            self.env["mail.mail"].sudo().create(mail_values).send()

    def send_email_to_employee(self):
        """Sends an email notification to the employee when their transfer is approved"""
        for record in self:
            if not record.employee_id.work_email:
                # ✅ If employee has no email, send a message in the Odoo chatter
                record.message_post(
                    body=f"Your transfer to {record.to_client_id.name} has been approved. "
                    f"Please report on {record.transfer_date_from}.",
                    subtype_xmlid="mail.mt_comment",
                )
                continue  # ✅ Skip sending email

            # ✅ Ensure `to_client_id` exists to prevent empty fields
            new_client = record.to_client_id.name if record.to_client_id else "N/A"
            approving_manager = (
                record.manager_id.name if record.manager_id else "HR Department"
            )

            cc_emails = ",".join(
                rec.employee_id.work_email
                for rec in self.env["hr.transfer.cc.recipient"].search(
                    [("active", "=", True)]
                )
                if rec.employee_id.work_email
            )

            mail_values = {
                "subject": f"🚀 Transfer Approved - {record.employee_id.name}",
                "email_to": record.employee_id.work_email,  # Employee's work email
                "email_cc": cc_emails,
                "email_from": self.env.user.email or "admin@company.com",
                "body_html": f"""
                    <html>
                    <head>
                        <style>
                            body {{ font-family: Arial, sans-serif; }}
                            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                            th, td {{ 
                                padding: 10px; 
                                border: 1px solid #dddddd; 
                                text-align: left; 
                            }}
                            th {{ background-color: #004080; color: white; font-weight: bold; }}
                            tr:nth-child(even) {{ background-color: #f2f2f2; }}
                        </style>
                    </head>
                    <body>
                        <p>Dear {record.employee_id.name},</p>
                        <p>Your transfer request has been <strong>approved</strong>. Below are the details:</p>
                        <table>
                            <tr>
                                <th>Field</th>
                                <th>Details</th>
                            </tr>
                            <tr><td><strong>Employee:</strong></td><td>{record.employee_id.name}</td></tr>
                            <tr><td><strong>From Client:</strong></td><td>{record.from_client_id.name or 'N/A'}</td></tr>
                            <tr><td><strong>To Client:</strong></td><td>{new_client}</td></tr>
                            <tr><td><strong>Transfer Date:</strong></td><td>{record.transfer_date_from} - {record.transfer_date_to}</td></tr>
                            <tr><td><strong>Reason:</strong></td><td>{record.reason}</td></tr>
                            <tr><td><strong>Approved By:</strong></td><td>{approving_manager}</td></tr>
                        </table>
                        <p><strong>Please report to your new client as per the scheduled transfer date.</strong></p>
                        <p>If you have any questions, please contact HR.</p>
                        <p>Best Regards,</p>
                        <p><strong>HR Department</strong></p>
                    </body>
                    </html>
                """,
            }

            # ✅ Send the email
            self.env["mail.mail"].sudo().create(mail_values).send()

    @api.model
    def reconcile_geofences(self):
        """Monthly job: clean up and regenerate geofences based on current deputations."""
        geofence_model = self.env["hr.attendance.geofence"]
        employee_model = self.env["hr.employee"]

        # ✅ Map of client name -> list of employee IDs
        client_map = {}
        employees = employee_model.search(
            [("latest_deputation_client_id", "!=", False)]
        )
        for emp in employees:
            client = emp.latest_deputation_client_id
            if client and client.name not in HrEmployeeTransfer.restricted_clients:
                client_map.setdefault(client.name, []).append(emp.id)

        # ✅ Ensure each client with employees has a geofence with employees assigned
        for client_name, emp_ids in client_map.items():
            geofence = geofence_model.search([("name", "=", client_name)], limit=1)
            if geofence:
                geofence.write({"employee_ids": [(6, 0, emp_ids)]})  # replace all
            else:
                geofence_model.create(
                    {
                        "name": client_name,
                        "description": f"Auto-created by cron for {client_name}",
                        "employee_ids": [(6, 0, emp_ids)],
                    }
                )

        # ✅ Delete geofences with no employees assigned
        today = fields.Date.today()
        empty_geofences = geofence_model.search(
            [("employee_ids", "=", False), ("last_employee_removed_date", "!=", False)]
        )
        for geo in empty_geofences:
            if (today - geo.last_employee_removed_date).days >= 60:
                geo.unlink()

    work_from = fields.Selection(
        [
            ("client", "Client Premises"),
            ("firm", "Firm Office"),
            ("partial", "Partial (Client + Firm Office)"),
        ],
        string="Work From",
        default="firm",
        required=True,
    )

    def unlink(self):
        if not self.user_has_groups("qaco_employees.group_qaco_employee_administrator"):
            raise AccessError(_("You do not have permission to delete transfers."))
        return super().unlink()

    def write(self, vals):
        if (
            "active" in vals
            and vals["active"] is False
            and not self.user_has_groups(
                "qaco_employees.group_qaco_employee_administrator"
            )
        ):
            raise AccessError(_("You do not have permission to archive transfers."))
        return super().write(vals)

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        if not self.user_has_groups("qaco_employees.group_qaco_employee_administrator"):
            raise AccessError(_("You do not have permission to duplicate transfers."))
        return super().copy(default)
