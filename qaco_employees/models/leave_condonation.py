import calendar
import uuid
from datetime import date

from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class LeaveCondonation(models.Model):
    _name = "leave.condonation"
    _description = "Leave Condonation"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "sequence"
    _order = "condonation_date desc, id desc"

    def _default_employee_id(self):
        return self.env.user.employee_id

    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        required=True,
        default=_default_employee_id,
        tracking=True,
    )

    condonation_date = fields.Date(
        string="Application Date",
        default=fields.Date.context_today,
        required=True,
        tracking=True,
    )

    condonation_month = fields.Selection(
        selection="_get_month_selection",
        string="Condonation Month",
        required=True,
        tracking=True,
        help="Select the month for which you are applying for leave condonation",
    )

    reason = fields.Text(
        string="Reason for Leave Condonation",
        required=True,
        tracking=True,
        help="Please provide a detailed reason for requesting leave condonation",
    )

    sequence = fields.Char(default="/", readonly=True, tracking=True)

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("reverted", "Reverted"),
        ],
        default="draft",
        string="Status",
        tracking=True,
    )

    line_ids = fields.One2many(
        "leave.condonation.line",
        "condonation_id",
        string="Payroll Deduction Lines",
        readonly=True,
    )

    approval_ids = fields.One2many(
        "leave.condonation.approval", "condonation_id", string="Approvals"
    )

    show_approval_buttons = fields.Boolean(
        string="Show Approval Buttons", compute="_compute_show_approval_buttons"
    )

    total_leave_deduction = fields.Float(
        string="Total Leave Deduction",
        compute="_compute_total_leave_deduction",
        store=True,
    )

    @api.model
    def _get_month_selection(self):
        """Generate month selection for current year and previous 6 months"""
        months = []
        today = date.today()
        for i in range(6, -1, -1):  # Last 6 months plus current month
            dt = today - relativedelta(months=i)
            month_key = dt.strftime("%Y-%m")
            month_label = dt.strftime("%B %Y")
            months.append((month_key, month_label))
        return months

    @api.depends("line_ids.leave_deduction_amount")
    def _compute_total_leave_deduction(self):
        for rec in self:
            rec.total_leave_deduction = sum(
                rec.line_ids.mapped("leave_deduction_amount")
            )

    def _is_admin_user(self):
        return self.env.user.has_group("base.group_system") or self.env.user.has_group(
            "qaco_employees.group_qaco_employee_administrator"
        )

    @api.model
    def default_get(self, fields_list):
        """Set default approver to Muhammad Bin Qasim"""
        res = super().default_get(fields_list)
        employee = (
            self.env["hr.employee"]
            .sudo()
            .search([("user_id", "=", self.env.uid)], limit=1)
        )

        if employee and "employee_id" in fields_list:
            res.setdefault("employee_id", employee.id)

        # Set Muhammad Bin Qasim as the sole approver
        if "approval_ids" in fields_list:
            mbq_user = (
                self.env["res.users"]
                .sudo()
                .search(
                    [
                        "|",
                        ("login", "=", "mbqasim"),
                        ("name", "ilike", "Muhammad Bin Qasim"),
                    ],
                    limit=1,
                )
            )

            if mbq_user:
                res.setdefault(
                    "approval_ids",
                    [
                        (
                            0,
                            0,
                            {
                                "validating_users_id": mbq_user.id,
                                "is_manager": False,
                                "is_partner": True,
                            },
                        )
                    ],
                )

        return res

    @api.onchange("condonation_month", "employee_id")
    def _onchange_condonation_month(self):
        """Fetch payroll data when month or employee changes"""
        if self.condonation_month and self.employee_id:
            self._load_payroll_deductions()

    def _load_payroll_deductions(self):
        """Load payroll deduction lines for the selected month"""
        self.ensure_one()

        if not self.condonation_month or not self.employee_id:
            return

        # Parse the month (format: 'YYYY-MM')
        year, month = map(int, self.condonation_month.split("-"))
        date_from = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        date_to = date(year, month, last_day)

        # Search for payroll in that month for this employee
        PayrollLine = self.env["qaco.payroll.line"].sudo()
        payroll_lines = PayrollLine.search(
            [
                ("employee_id", "=", self.employee_id.id),
                ("payroll_id.date_from", ">=", date_from),
                ("payroll_id.date_to", "<=", date_to),
                ("payroll_id.state", "in", ["draft", "submitted", "approved"]),
                ("leave_deduction_amount", ">", 0),
            ]
        )

        if not payroll_lines:
            raise UserError(
                _(
                    "No leave deduction found for %s in %s. "
                    "Please ensure you have absence deductions in your payroll for the selected month."
                )
                % (self.employee_id.name, date(year, month, 1).strftime("%B %Y"))
            )

        # Clear existing lines
        self.line_ids = [(5, 0, 0)]

        # Create new lines from payroll data
        line_vals = []
        for pline in payroll_lines:
            line_vals.append(
                (
                    0,
                    0,
                    {
                        "payroll_line_id": pline.id,
                        "employee_id": pline.employee_id.id,
                        "department_id": pline.department_id.id,
                        "designation_id": pline.designation_id.id,
                        "gross_salary": pline.gross_salary,
                        "allowance_amount": pline.allowance_amount,
                        "attendance_days": pline.attendance_days,
                        "leave_deduction_amount": pline.leave_deduction_amount,
                        "net_salary": pline.net_salary,
                        "payroll_month": pline.payroll_id.month_name or "",
                        "payroll_date_from": pline.payroll_id.date_from,
                        "payroll_date_to": pline.payroll_id.date_to,
                    },
                )
            )

        self.line_ids = line_vals

    @api.depends("approval_ids.is_validation_status", "state")
    def _compute_show_approval_buttons(self):
        """Check if current user is Muhammad Bin Qasim or admin"""
        mbq_user = (
            self.env["res.users"]
            .sudo()
            .search(
                [
                    "|",
                    ("login", "=", "mbqasim"),
                    ("name", "ilike", "Muhammad Bin Qasim"),
                ],
                limit=1,
            )
        )

        for rec in self:
            rec.show_approval_buttons = False
            if rec.state == "submitted":
                if rec._is_admin_user() or (
                    mbq_user and self.env.user.id == mbq_user.id
                ):
                    rec.show_approval_buttons = True

    @api.constrains("employee_id")
    def _check_employee_change(self):
        for rec in self:
            if not rec._is_admin_user() and rec.employee_id != rec.env.user.employee_id:
                raise UserError(
                    _("You can only create leave condonation for yourself.")
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not self._is_admin_user():
                employee_id = vals.get("employee_id")
                if employee_id and employee_id != self.env.user.employee_id.id:
                    raise UserError(
                        _("You can only create leave condonation for yourself.")
                    )
            if vals.get("sequence", "/") == "/":
                vals["sequence"] = (
                    self.env["ir.sequence"].next_by_code("leave.condonation.seq") or "/"
                )
        records = super().create(vals_list)
        for record in records:
            record._ensure_mbq_approver()
        return records

    def write(self, vals):
        if not self._is_admin_user() and "employee_id" in vals:
            if vals["employee_id"] != self.env.user.employee_id.id:
                raise UserError(_("You can only set the employee to yourself."))
        res = super().write(vals)
        self._ensure_mbq_approver()
        return res

    def _ensure_mbq_approver(self):
        """Ensure Muhammad Bin Qasim is the sole approver"""
        for rec in self:
            # Find Muhammad Bin Qasim user
            mbq_user = (
                self.env["res.users"]
                .sudo()
                .search(
                    [
                        "|",
                        ("login", "=", "mbqasim"),
                        ("name", "ilike", "Muhammad Bin Qasim"),
                    ],
                    limit=1,
                )
            )

            if not mbq_user:
                raise UserError(
                    _(
                        "Muhammad Bin Qasim user not found. Please contact administrator."
                    )
                )

            # Remove all existing approvers
            rec.approval_ids.unlink()

            # Add Muhammad Bin Qasim as sole approver
            self.env["leave.condonation.approval"].sudo().create(
                {
                    "condonation_id": rec.id,
                    "validating_users_id": mbq_user.id,
                    "is_manager": False,
                    "is_partner": True,
                }
            )

    def get_approval_url_for(self, user_id):
        self.ensure_one()
        validator = (
            self.approval_ids.filtered(lambda v: v.validating_users_id.id == user_id)[0]
            if self.approval_ids
            else False
        )
        if not validator or not validator.approve_token:
            return ""
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return f"{base_url}/leave_condonation/approve/{validator.approve_token}"

    def get_refusal_url_for(self, user_id):
        self.ensure_one()
        validator = (
            self.approval_ids.filtered(lambda v: v.validating_users_id.id == user_id)[0]
            if self.approval_ids
            else False
        )
        if not validator or not validator.approve_token:
            return ""
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return f"{base_url}/leave_condonation/refuse/{validator.approve_token}"

    def get_revert_url_for(self, user_id):
        self.ensure_one()
        validator = (
            self.approval_ids.filtered(lambda v: v.validating_users_id.id == user_id)[0]
            if self.approval_ids
            else False
        )
        if not validator or not validator.approve_token:
            return ""
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return f"{base_url}/leave_condonation/revert/{validator.approve_token}"

    def get_record_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return f"{base_url}/web#id={self.id}&model=leave.condonation&view_type=form"

    def action_submit(self):
        for rec in self:
            if not rec.line_ids:
                raise ValidationError(
                    _(
                        "No payroll deduction lines found. Please select a month with leave deductions."
                    )
                )
            if not rec.reason or not rec.reason.strip():
                raise ValidationError(
                    _("Please provide a reason for leave condonation.")
                )
            rec.state = "submitted"
            rec._ensure_mbq_approver()
            rec._send_submit_email()

    def action_load_deductions(self):
        """Button action to load/reload payroll deductions"""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("You can only load deductions in draft state."))
        self._load_payroll_deductions()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Success"),
                "message": _("Payroll deductions loaded successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_approve(self):
        self.ensure_one()

        # Check if user is Muhammad Bin Qasim or admin
        mbq_user = (
            self.env["res.users"]
            .sudo()
            .search(
                [
                    "|",
                    ("login", "=", "mbqasim"),
                    ("name", "ilike", "Muhammad Bin Qasim"),
                ],
                limit=1,
            )
        )

        if self._is_admin_user() or (mbq_user and self.env.user.id == mbq_user.id):
            self.approval_ids.write({"is_validation_status": True})
            self.state = "approved"
            self.message_post(
                body=_("%s approved the leave condonation.") % (self.env.user.name),
                subject=_("Leave Condonation Approved"),
            )
            # Notify employee
            if self.employee_id.user_id and self.employee_id.user_id.partner_id:
                self.env["mail.mail"].sudo().create(
                    {
                        "subject": _(
                            "Your Leave Condonation Request has been Approved"
                        ),
                        "body_html": _(
                            "<p>Dear %s,</p>"
                            "<p>Your leave condonation request for <strong>%s</strong> has been <strong>approved</strong>.</p>"
                            "<p>Total leave deduction to be refunded: <strong>%.2f</strong></p>"
                            "<p>This will be processed in the next payroll cycle.</p>"
                        )
                        % (
                            self.employee_id.name,
                            self.condonation_month,
                            self.total_leave_deduction,
                        ),
                        "email_to": self.employee_id.user_id.partner_id.email,
                        "email_from": self.env.user.email_formatted,
                    }
                ).send()
        else:
            raise UserError(
                _(
                    "Only Muhammad Bin Qasim or administrators can approve leave condonations."
                )
            )

    def action_reject(self):
        for rec in self:
            rec.state = "rejected"
            rec.message_post(
                body=_("Leave condonation rejected by %s") % (self.env.user.name)
            )
            # Notify employee
            if rec.employee_id.user_id and rec.employee_id.user_id.partner_id:
                self.env["mail.mail"].sudo().create(
                    {
                        "subject": _(
                            "Your Leave Condonation Request has been Rejected"
                        ),
                        "body_html": _(
                            "<p>Dear %s,</p>"
                            "<p>Your leave condonation request for <strong>%s</strong> has been <strong>rejected</strong>.</p>"
                            "<p>Please contact your supervisor for more information.</p>"
                        )
                        % (rec.employee_id.name, rec.condonation_month),
                        "email_to": rec.employee_id.user_id.partner_id.email,
                        "email_from": self.env.user.email_formatted,
                    }
                ).send()

    def action_revert(self):
        for rec in self:
            rec.state = "reverted"
            for line in rec.approval_ids:
                line.is_validation_status = False
                line.approve_token = str(uuid.uuid4())
            rec.message_post(
                body=_("Leave condonation reverted by %s") % (self.env.user.name)
            )

    def _send_submit_email(self):
        """Send email to Muhammad Bin Qasim with approval links and table of deductions"""
        for rec in self:
            mbq_user = rec.approval_ids.mapped("validating_users_id")
            if not mbq_user or not mbq_user.partner_id or not mbq_user.partner_id.email:
                continue

            # Build lines table
            lines_html = """
            <table style="width:92%; border-collapse:collapse; margin:16px auto 24px auto; border:1.5px solid #007bff;">
                <thead>
                    <tr>
                        <th style="background-color:#007bff; color:white; padding:10px 8px; border:1px solid #0056b3;">Employee</th>
                        <th style="background-color:#007bff; color:white; padding:10px 8px; border:1px solid #0056b3;">Department</th>
                        <th style="background-color:#007bff; color:white; padding:10px 8px; border:1px solid #0056b3;">Designation</th>
                        <th style="background-color:#007bff; color:white; padding:10px 8px; border:1px solid #0056b3;">Payroll Month</th>
                        <th style="background-color:#007bff; color:white; padding:10px 8px; border:1px solid #0056b3;">Attendance Days</th>
                        <th style="background-color:#007bff; color:white; padding:10px 8px; border:1px solid #0056b3;">Basic Salary</th>
                        <th style="background-color:#007bff; color:white; padding:10px 8px; border:1px solid #0056b3;">Allowance</th>
                        <th style="background-color:#007bff; color:white; padding:10px 8px; border:1px solid #0056b3;">Leave Deduction</th>
                        <th style="background-color:#007bff; color:white; padding:10px 8px; border:1px solid #0056b3;">Net Salary</th>
                    </tr>
                </thead>
                <tbody>
            """

            for idx, line in enumerate(rec.line_ids):
                row_style = "background-color:#f8f9fa;" if idx % 2 == 0 else ""
                lines_html += f"""
                    <tr style="{row_style}">
                        <td style="padding:8px 6px; border:1px solid #dee2e6;">{line.employee_id.name or ''}</td>
                        <td style="padding:8px 6px; border:1px solid #dee2e6;">{line.department_id.name or ''}</td>
                        <td style="padding:8px 6px; border:1px solid #dee2e6;">{line.designation_id.name or ''}</td>
                        <td style="padding:8px 6px; border:1px solid #dee2e6;">{line.payroll_month or ''}</td>
                        <td style="padding:8px 6px; border:1px solid #dee2e6; text-align:center;">{line.attendance_days}</td>
                        <td style="padding:8px 6px; border:1px solid #dee2e6; text-align:right;">{line.gross_salary:,.2f}</td>
                        <td style="padding:8px 6px; border:1px solid #dee2e6; text-align:right;">{line.allowance_amount:,.2f}</td>
                        <td style="padding:8px 6px; border:1px solid #dee2e6; text-align:right; font-weight:bold; color:#dc3545;">{line.leave_deduction_amount:,.2f}</td>
                        <td style="padding:8px 6px; border:1px solid #dee2e6; text-align:right;">{line.net_salary:,.2f}</td>
                    </tr>
                """

            lines_html += f"""
                    <tr style="background-color:#e7f3ff; font-weight:bold;">
                        <td colspan="7" style="padding:10px 6px; border:1px solid #0056b3; text-align:right;">Total Leave Deduction:</td>
                        <td colspan="2" style="padding:10px 6px; border:1px solid #0056b3; text-align:right; color:#dc3545; font-size:16px;">{rec.total_leave_deduction:,.2f}</td>
                    </tr>
                </tbody>
            </table>
            """

            # Build email body
            body_html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; color: #333; }}
                    .info-label {{ font-weight: bold; color: #555; }}
                </style>
            </head>
            <body>
                <div style="margin:20px 0;">
                    <a href="{rec.get_approval_url_for(mbq_user.id)}" style="background-color:#28a745; color:white; padding:6px 14px; text-decoration:none; border-radius:4px; margin-right:8px; display:inline-block; margin-bottom:6px;">✅ Approve</a>
                    <a href="{rec.get_refusal_url_for(mbq_user.id)}" style="background-color:#dc3545; color:white; padding:6px 14px; text-decoration:none; border-radius:4px; margin-right:8px; display:inline-block; margin-bottom:6px;">❌ Reject</a>
                    <a href="{rec.get_revert_url_for(mbq_user.id)}" style="background-color:#6c757d; color:white; padding:6px 14px; text-decoration:none; border-radius:4px; margin-right:8px; display:inline-block; margin-bottom:6px;">🔄 Revert</a>
                    <a href="{rec.get_record_url()}" style="background-color:#007bff; color:white; padding:6px 14px; text-decoration:none; border-radius:4px; display:inline-block; margin-bottom:6px;">📄 View Request</a>
                </div>
                
                <h3 style="color:#007bff;">Leave Condonation Request</h3>
                <div>
                    <p><span class="info-label">Employee:</span> {rec.employee_id.name}</p>
                    <p><span class="info-label">Application Date:</span> {rec.condonation_date.strftime('%B %d, %Y')}</p>
                    <p><span class="info-label">Condonation Month:</span> <strong>{rec.condonation_month}</strong></p>
                    <p><span class="info-label">Total Leave Deduction:</span> <strong style="color:#dc3545;">{rec.total_leave_deduction:,.2f}</strong></p>
                    <p><span class="info-label">Reason:</span></p>
                    <div style="background-color:#f8f9fa; padding:10px; border-left:4px solid #007bff; margin:10px 0;">
                        {rec.reason or ''}
                    </div>
                </div>
                
                <h4 style="color:#007bff; margin-top:25px;">Payroll Deduction Details</h4>
                {lines_html}
            </body>
            </html>
            """

            self.env["mail.mail"].sudo().create(
                {
                    "subject": f"Leave Condonation Approval Request - {rec.employee_id.name} ({rec.condonation_month})",
                    "body_html": body_html,
                    "email_to": mbq_user.partner_id.email,
                    "email_from": rec.env.user.email_formatted or "noreply@qaco.com.pk",
                }
            ).send()


class LeaveCondonationLine(models.Model):
    _name = "leave.condonation.line"
    _description = "Leave Condonation Line"

    condonation_id = fields.Many2one(
        "leave.condonation",
        string="Condonation",
        ondelete="cascade",
        required=True,
    )
    payroll_line_id = fields.Many2one(
        "qaco.payroll.line", string="Payroll Line Reference", readonly=True
    )
    employee_id = fields.Many2one("hr.employee", string="Employee", readonly=True)
    department_id = fields.Many2one("hr.department", string="Department", readonly=True)
    designation_id = fields.Many2one(
        "employee.designation", string="Designation", readonly=True
    )
    gross_salary = fields.Float(string="Basic Salary", readonly=True)
    allowance_amount = fields.Float(string="Allowance", readonly=True)
    attendance_days = fields.Integer(string="Attendance Days", readonly=True)
    leave_deduction_amount = fields.Float(string="Leave Deduction", readonly=True)
    net_salary = fields.Float(string="Net Salary", readonly=True)
    payroll_month = fields.Char(string="Payroll Month", readonly=True)
    payroll_date_from = fields.Date(string="Payroll From", readonly=True)
    payroll_date_to = fields.Date(string="Payroll To", readonly=True)


class LeaveCondonationApproval(models.Model):
    _name = "leave.condonation.approval"
    _description = "Leave Condonation Approval"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    condonation_id = fields.Many2one(
        "leave.condonation", string="Leave Condonation", ondelete="cascade"
    )
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
            "unique_condonation_user",
            "unique(condonation_id, validating_users_id)",
            "An approver can only be added once per leave condonation.",
        )
    ]
