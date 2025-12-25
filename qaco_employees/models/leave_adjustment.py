import uuid

from markupsafe import Markup
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import format_date


class LeaveAdjustment(models.Model):
    _name = "leave.adjustment"
    _description = "Leave Adjustment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "sequence"
    _order = "adjustment_date desc"

    def _default_employee_id(self):
        return self.env.user.employee_id

    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        required=True,
        default=_default_employee_id,
    )
    adjustment_type = fields.Selection(
        [("positive", "Add Leaves"), ("negative", "Reduce Leaves")],
        string="Adjustment Type",
        default="positive",
        required=True,
        tracking=True,
    )
    adjustment = fields.Float(string="Leave Adjustment", tracking=True)
    reason = fields.Text(string="Reason for Adjustment", required=True, tracking=True)
    adjustment_date = fields.Date(
        string="Adjustment Date",
        required=True,
        default=fields.Date.context_today,
    )
    sequence = fields.Char(default="/", readonly=True)
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
    adjustment_ref_id = fields.Many2one("leave.adjustment", string="Adjustment Ref")
    allowance_ref_id = fields.Many2one("leave.allowance", string="Allowance Ref")

    approval_ids = fields.One2many(
        "leave.adjustment.approval", "adjustment_id", string="Approvals"
    )

    rejection_reason = fields.Text(
        string="Rejection Reason", readonly=True, tracking=True
    )

    show_approval_buttons = fields.Boolean(
        string="Show Approval Buttons", compute="_compute_show_approval_buttons"
    )

    # History fields for displaying in form
    # Use computed Many2many fields for dynamic recordsets (no inverse required)
    leave_history_ids = fields.Many2many(
        "leave.summary", compute="_compute_leave_history", string="Leave History"
    )
    previous_adjustments_ids = fields.Many2many(
        "leave.adjustment",
        compute="_compute_previous_adjustments",
        string="Previous Adjustments",
    )

    def get_adjustment_type_display(self):
        """Return the human-readable label of the adjustment type."""
        self.ensure_one()
        selection = dict(self._fields["adjustment_type"].selection)
        return selection.get(self.adjustment_type, "")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        employee = (
            self.env["hr.employee"]
            .sudo()
            .search([("user_id", "=", self.env.uid)], limit=1)
        )
        if employee:
            if "employee_id" in fields_list:
                res.setdefault("employee_id", employee.id)
            manager = employee.parent_id
            partner = employee.partner_id
            lines = []
            if manager and manager.user_id:
                lines.append(
                    {
                        "validating_users_id": manager.user_id.id,
                        "is_manager": True,
                        "is_partner": partner and partner.user_id == manager.user_id,
                    }
                )
            if (
                partner
                and partner.user_id
                and partner.user_id != (manager and manager.user_id)
            ):
                lines.append(
                    {
                        "validating_users_id": partner.user_id.id,
                        "is_partner": True,
                        "is_manager": False,
                    }
                )
            if lines and "approval_ids" in fields_list:
                res.setdefault("approval_ids", [(0, 0, line) for line in lines])
        return res

    @api.depends("employee_id")
    def _compute_leave_history(self):
        """Compute leave history from leave summary for the employee."""
        for rec in self:
            if rec.employee_id:
                # Get leave history (excluding monthly summaries and the current adjustment)
                summaries = self.env["leave.summary"].search(
                    [
                        ("employee_id", "=", rec.employee_id.id),
                        ("is_monthly_summary", "=", False),
                        ("adjustment_ref_id", "!=", rec.id if rec.id else False),
                    ],
                    order="event_date desc",
                    limit=50,
                )
                rec.leave_history_ids = summaries
            else:
                rec.leave_history_ids = False

    @api.depends("employee_id")
    def _compute_previous_adjustments(self):
        """Compute previous leave adjustments for the employee."""
        for rec in self:
            if rec.employee_id:
                # Get previous adjustments (excluding current one)
                adjustments = self.search(
                    [
                        ("employee_id", "=", rec.employee_id.id),
                        ("id", "!=", rec.id if rec.id else False),
                        ("state", "in", ["approved", "rejected", "reverted"]),
                    ],
                    order="adjustment_date desc",
                    limit=20,
                )
                rec.previous_adjustments_ids = adjustments
            else:
                rec.previous_adjustments_ids = False

    @api.depends("approval_ids.is_validation_status", "state")
    def _compute_show_approval_buttons(self):
        for rec in self:
            rec.show_approval_buttons = False
            if rec.state == "submitted":
                if rec.env.user.has_group(
                    "base.group_system"
                ) or rec.env.user.has_group(
                    "qaco_employees.group_qaco_employee_administrator"
                ):
                    rec.show_approval_buttons = True
                else:
                    for line in rec.approval_ids.filtered(
                        lambda line: line.validating_users_id == rec.env.user
                    ):
                        if not line.is_validation_status:
                            rec.show_approval_buttons = True
                            break

    def _is_admin_user(self):
        return self.env.user.has_group("base.group_system") or self.env.user.has_group(
            "qaco_employees.group_qaco_employee_administrator"
        )

    @api.constrains("adjustment", "adjustment_type")
    def _check_adjustment_sign(self):
        for rec in self:
            if rec.adjustment_type == "negative" and rec.adjustment >= 0:
                raise ValidationError(_("Adjustment must be a negative number."))
            if rec.adjustment_type == "positive" and rec.adjustment < 0:
                raise ValidationError(_("Adjustment must be a positive number."))

    @api.constrains("adjustment_date")
    def _check_adjustment_date(self):
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.adjustment_date and rec.adjustment_date < today:
                raise ValidationError(_("Adjustment date cannot be in the past."))

    @api.constrains("employee_id", "adjustment_date", "state")
    def _check_duplicate_date(self):
        """Ensure there is only one adjustment per employee and date."""
        for rec in self:
            if not rec.employee_id or not rec.adjustment_date:
                continue
            duplicate = self.search(
                [
                    ("employee_id", "=", rec.employee_id.id),
                    ("adjustment_date", "=", rec.adjustment_date),
                    ("id", "!=", rec.id),
                    ("state", "not in", ["rejected", "reverted"]),
                ],
                limit=1,
            )
            if duplicate:
                raise ValidationError(
                    _("Employee already has a leave adjustment record for this date.")
                )

    def update_leave_summary(self):
        for record in self:
            summary = (
                self.env["leave.summary"]
                .sudo()
                .create(
                    {
                        "employee_id": record.employee_id.id,
                        "event_date": record.adjustment_date,
                        "leave_adjustment": record.adjustment,
                        "adjustment_ref_id": record.id,
                        "is_monthly_summary": False,
                    }
                )
            )

            summary._cascade_update_future_months()

    @api.onchange("employee_id")
    def _onchange_employee_set_approvers(self):
        for rec in self:
            employee = rec.employee_id.sudo()
            manager = employee.parent_id
            partner = employee.partner_id
            lines = []
            if manager and manager.user_id:
                lines.append(
                    {
                        "validating_users_id": manager.user_id.id,
                        "is_manager": True,
                        "is_partner": partner and partner.user_id == manager.user_id,
                    }
                )
            if (
                partner
                and partner.user_id
                and partner.user_id != (manager and manager.user_id)
            ):
                lines.append(
                    {
                        "validating_users_id": partner.user_id.id,
                        "is_partner": True,
                        "is_manager": False,
                    }
                )
            rec.approval_ids = [(5, 0, 0)] + [(0, 0, line) for line in lines]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not self._is_admin_user():
                employee_id = vals.get("employee_id")
                if employee_id and employee_id != self.env.user.employee_id.id:
                    raise UserError(
                        _("You can only create leave adjustments for yourself.")
                    )
            if vals.get("sequence", "/") == "/":
                vals["sequence"] = (
                    self.env["ir.sequence"].next_by_code("leave.adjustment.seq") or "/"
                )

        records = super().create(vals_list)
        for record in records:
            record._ensure_unique_approvers()
        return records

    def write(self, vals):
        if not self._is_admin_user() and "employee_id" in vals:
            if vals["employee_id"] != self.env.user.employee_id.id:
                raise UserError(_("You can only set the employee to yourself."))
        res = super().write(vals)
        self._ensure_unique_approvers()
        return res

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
        return f"{base_url}/leave_adjustment/approve/{validator.approve_token}"

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
        return f"{base_url}/leave_adjustment/refuse/{validator.approve_token}"

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
        return f"{base_url}/leave_adjustment/revert/{validator.approve_token}"

    def get_transfer_url_for(self, user_id):
        self.ensure_one()
        validator = (
            self.approval_ids.filtered(lambda v: v.validating_users_id.id == user_id)[0]
            if self.approval_ids
            else False
        )
        if not validator or not validator.approve_token:
            return ""
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return f"{base_url}/leave_adjustment/transfer/{validator.approve_token}"

    def get_record_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return f"{base_url}/web#id={self.id}&model=leave.adjustment&view_type=form"

    def action_submit(self):
        """Submit adjustment for approval with audit logging."""
        for rec in self:
            rec._check_duplicate_date()
            rec.state = "submitted"
            rec._ensure_unique_approvers()

            # Post audit log to chatter
            submitter_name = self.env.user.name
            submission_time = fields.Datetime.now().strftime("%d-%b-%Y %H:%M:%S")
            adjustment_label = (
                "Add Leaves" if rec.adjustment_type == "positive" else "Reduce Leaves"
            )

            body = f"""
                <div style="padding: 10px; border-left: 4px solid #2196F3; background-color: #e3f2fd; margin: 10px 0;">
                    <h4 style="margin-top: 0; color: #1976D2;">📤 Leave Adjustment Submitted</h4>
                    <p><strong>Submitted by:</strong> {submitter_name}</p>
                    <p><strong>Submission Time:</strong> {submission_time}</p>
                    <p><strong>Employee:</strong> {rec.employee_id.name}</p>
                    <p><strong>Adjustment Type:</strong> {adjustment_label}</p>
                    <p><strong>Adjustment Amount:</strong> {rec.adjustment} days</p>
                    <p><strong>Adjustment Date:</strong> {rec.adjustment_date.strftime('%d-%b-%Y')}</p>
                    <p><strong>Reason:</strong> {rec.reason}</p>
                    <ul style="margin: 5px 0;">
                        <li>Adjustment submitted for approval</li>
                        <li>Approval emails sent to all approvers</li>
                    </ul>
                </div>
            """
            rec.message_post(
                body=body,
                subject="Leave Adjustment Submitted",
                message_type="notification",
                subtype_xmlid="mail.mt_note",
            )

            rec._send_submit_email()  # ✅ correct method name for submit

    def action_approve(self):
        self.ensure_one()

        is_admin = self.env.user.has_group(
            "base.group_system"
        ) or self.env.user.has_group("qaco_employees.group_qaco_employee_administrator")

        if is_admin:
            self.approval_ids.write({"is_validation_status": True})
            self.state = "approved"

            # Admin approval audit log
            approver_name = self.env.user.name
            approval_time = fields.Datetime.now().strftime("%d-%b-%Y %H:%M:%S")
            body = f"""
                <div style="padding: 10px; border-left: 4px solid #4CAF50; background-color: #c8e6c9; margin: 10px 0;">
                    <h4 style="margin-top: 0; color: #2E7D32;">🎉 Leave Adjustment Approved (Administrator)</h4>
                    <p><strong>Approved by:</strong> {approver_name}</p>
                    <p><strong>Approval Time:</strong> {approval_time}</p>
                    <p><strong>Status:</strong> Approved as System Administrator</p>
                    <ul style="margin: 5px 0;">
                        <li>Adjustment has been approved</li>
                        <li>Leave summary has been updated</li>
                        <li>Employee has been notified</li>
                    </ul>
                </div>
            """
            self.message_post(
                body=body,
                subject="Adjustment Approved",
                message_type="notification",
                subtype_xmlid="mail.mt_note",
            )
            self.update_leave_summary()
            return

        validator = self.approval_ids.filtered(
            lambda v: v.validating_users_id.id == self.env.uid
        )
        validator = validator[0] if validator else False
        if validator and not validator.is_validation_status:
            validator.is_validation_status = True

            # Approval audit log
            approver_name = validator.validating_users_id.name
            approval_time = fields.Datetime.now().strftime("%d-%b-%Y %H:%M:%S")
            total_approvers = len(self.approval_ids)
            approved_count = len(
                self.approval_ids.filtered(lambda line: line.is_validation_status)
            )

            body = f"""
                <div style="padding: 10px; border-left: 4px solid #4CAF50; background-color: #e8f5e9; margin: 10px 0;">
                    <h4 style="margin-top: 0; color: #4CAF50;">✅ Leave Adjustment Approved</h4>
                    <p><strong>Approved by:</strong> {approver_name}</p>
                    <p><strong>Approval Time:</strong> {approval_time}</p>
                    <p><strong>Progress:</strong> {approved_count} of {total_approvers} approvals received</p>
                </div>
            """
            self.message_post(
                body=body,
                subject="Approval Received",
                message_type="notification",
                subtype_xmlid="mail.mt_note",
            )

        pending = self.approval_ids.filtered(lambda v: not v.is_validation_status)
        if not pending:
            self.state = "approved"

            # Final approval audit log
            final_approver = (
                validator.validating_users_id.name if validator else self.env.user.name
            )
            approval_time = fields.Datetime.now().strftime("%d-%b-%Y %H:%M:%S")
            body = f"""
                <div style="padding: 10px; border-left: 4px solid #4CAF50; background-color: #c8e6c9; margin: 10px 0;">
                    <h4 style="margin-top: 0; color: #2E7D32;">🎉 Leave Adjustment Fully Approved</h4>
                    <p><strong>Final Approval by:</strong> {final_approver}</p>
                    <p><strong>Approval Time:</strong> {approval_time}</p>
                    <p><strong>Status:</strong> All required approvals received</p>
                    <ul style="margin: 5px 0;">
                        <li>Adjustment is now fully approved</li>
                        <li>Leave summary has been updated</li>
                        <li>Employee has been notified</li>
                    </ul>
                </div>
            """
            self.message_post(
                body=body,
                subject="Adjustment Fully Approved",
                message_type="notification",
                subtype_xmlid="mail.mt_note",
            )
            self.update_leave_summary()
        else:
            for approver in pending:
                user = approver.validating_users_id
                partner_rec = user.partner_id
                if not partner_rec or not partner_rec.email:
                    continue
                body = (
                    f"<p>The leave adjustment for <strong>{self.employee_id.name}</strong> "
                    f"has been approved by <strong>{self.env.user.name}</strong>. It now awaits your approval.</p>"
                    f'<div style="margin:20px 0;">'
                    f"<a href='{self.get_approval_url_for(user.id)}' style='background-color:#28a745; color:white; padding:6px 14px; text-decoration:none; border-radius:4px; margin-right:8px; display:inline-block; margin-bottom:6px;'>✅ Approve</a>"
                    f"<a href='{self.get_refusal_url_for(user.id)}' style='background-color:#dc3545; color:white; padding:6px 14px; text-decoration:none; border-radius:4px; margin-right:8px; display:inline-block; margin-bottom:6px;'>❌ Reject</a>"
                    f"<a href='{self.get_revert_url_for(user.id)}' style='background-color:#6c757d; color:white; padding:6px 14px; text-decoration:none; border-radius:4px; margin-right:8px; display:inline-block; margin-bottom:6px;'>🔄 Revert</a>"
                    f"<a href='{self.get_record_url()}' style='background-color:#007bff; color:white; padding:6px 14px; text-decoration:none; border-radius:4px; display:inline-block; margin-bottom:6px;'>📄 View</a>"
                    f"</div>"
                )
                self.env["mail.mail"].sudo().create(
                    {
                        "subject": f"Pending Leave Adjustment Approval for {self.employee_id.name}",
                        "body_html": body,
                        "email_to": partner_rec.email,
                        "email_from": self.env.user.email_formatted,
                    }
                ).send()

    def action_reject(self):
        """Reject adjustment with reason - opens wizard for reason input."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Reject Leave Adjustment",
            "res_model": "leave.adjustment.reject.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_adjustment_id": self.id},
        }

    def do_reject_with_reason(self, rejection_reason):
        """Actually perform the rejection with the given reason."""
        for rec in self:

            rec.write(
                {
                    "state": "rejected",
                    "rejection_reason": rejection_reason,
                }
            )

            # Post audit log to chatter
            rejector_name = self.env.user.name
            rejection_time = fields.Datetime.now().strftime("%d-%b-%Y %H:%M:%S")
            body = f"""
                <div style="padding: 10px; border-left: 4px solid #F44336; background-color: #ffebee; margin: 10px 0;">
                    <h4 style="margin-top: 0; color: #C62828;">❌ Leave Adjustment Rejected</h4>
                    <p><strong>Rejected by:</strong> {rejector_name}</p>
                    <p><strong>Rejection Time:</strong> {rejection_time}</p>
                    <p><strong>Adjustment:</strong> {rec.adjustment} days ({rec.adjustment_type.replace('positive', 'Add Leaves').replace('negative', 'Reduce Leaves')})</p>
                    <p><strong>Reason for Rejection:</strong> {rejection_reason or 'No reason provided'}</p>
                    <ul style="margin: 5px 0;">
                        <li>Adjustment request has been rejected</li>
                        <li>Employee has been notified</li>
                        <li>All pending approvers have been informed</li>
                    </ul>
                </div>
            """
            rec.message_post(
                body=body,
                subject="Leave Adjustment Rejected",
                message_type="notification",
                subtype_xmlid="mail.mt_note",
            )

    def action_revert(self):
        """Revert adjustment with audit logging."""
        for rec in self:
            old_state = rec.state
            rec.state = "reverted"
            for line in rec.approval_ids:
                line.is_validation_status = False
                line.approve_token = str(uuid.uuid4())

            # Revert audit log
            reverter_name = self.env.user.name
            revert_time = fields.Datetime.now().strftime("%d-%b-%Y %H:%M:%S")
            body = f"""
                <div style="padding: 10px; border-left: 4px solid #FF9800; background-color: #fff3e0; margin: 10px 0;">
                    <h4 style="margin-top: 0; color: #F57C00;">🔄 Leave Adjustment Reverted</h4>
                    <p><strong>Reverted by:</strong> {reverter_name}</p>
                    <p><strong>Revert Time:</strong> {revert_time}</p>
                    <p><strong>Previous Status:</strong> {old_state.title()}</p>
                    <ul style="margin: 5px 0;">
                        <li>Adjustment has been reverted to draft</li>
                        <li>All approval statuses have been reset</li>
                        <li>Employee can now edit and resubmit</li>
                    </ul>
                </div>
            """
            rec.message_post(
                body=body,
                subject="Adjustment Reverted",
                message_type="notification",
                subtype_xmlid="mail.mt_note",
            )

    def action_validate(self):
        # Backward compatibility
        return self.action_approve()

    def action_reset_to_draft(self):
        for rec in self:
            summaries = self.env["leave.summary"].search(
                [("adjustment_ref_id", "=", rec.id)]
            )

            summaries.unlink()  # 🔥 Delete the related leave summaries

            rec.state = "draft"

    def _ensure_unique_approvers(self):
        for rec in self:
            existing_users = rec.approval_ids.mapped("validating_users_id.id")
            approvers = []

            manager = rec.employee_id.parent_id
            partner = rec.employee_id.partner_id

            if manager and manager.user_id and manager.user_id.id not in existing_users:
                approvers.append(
                    {
                        "adjustment_id": rec.id,
                        "validating_users_id": manager.user_id.id,
                        "is_manager": True,
                        "is_partner": partner and partner.user_id == manager.user_id,
                    }
                )
            if (
                partner
                and partner.user_id
                and partner.user_id != (manager and manager.user_id)
                and partner.user_id.id not in existing_users
            ):
                approvers.append(
                    {
                        "adjustment_id": rec.id,
                        "validating_users_id": partner.user_id.id,
                        "is_manager": False,
                        "is_partner": True,
                    }
                )

            for approver in approvers:
                self.env["leave.adjustment.approval"].sudo().create(approver)

    def _send_submit_email(
        self, target_validators=None, log_chatter=True, transfer_notice=None
    ):
        template_xmlid = "qaco_employees.leave_adjustment_approval_email_template"

        for rec in self:
            # Generate Leave Summary Table HTML
            leave_summary_html = rec._generate_leave_summary_table_html()

            # Generate Previous Adjustments Table HTML
            previous_adjustments_html = rec._generate_previous_adjustments_table_html()

            subject = (
                f"[Action Required] Approve Leave Adjustment {rec.employee_id.name}"
            )
            if transfer_notice:
                subject = f"[Transferred] {subject}"

            pending = rec.approval_ids.filtered(lambda a: not a.is_validation_status)

            if target_validators:
                if isinstance(target_validators, models.BaseModel):
                    if target_validators._name == "leave.adjustment.approval":
                        pending = pending & target_validators
                    elif target_validators._name == "res.users":
                        user_ids = target_validators.ids
                        pending = pending.filtered(
                            lambda a: a.validating_users_id.id in user_ids
                        )
                else:
                    user_ids = set(
                        target_validators
                        if isinstance(target_validators, (list, tuple, set))
                        else [target_validators]
                    )
                    pending = pending.filtered(
                        lambda a: a.validating_users_id.id in user_ids
                    )

            for approver in pending:
                user = approver.validating_users_id
                partner_rec = user.partner_id
                if not partner_rec or not partner_rec.email:
                    continue

                # Render email body using QWeb
                email_body = self.env["ir.qweb"]._render(
                    template_xmlid,
                    {
                        "employee_name": rec.employee_id.name or "",
                        "adjustment": str(rec.adjustment or ""),
                        "adjustment_type": dict(
                            rec._fields["adjustment_type"].selection
                        ).get(rec.adjustment_type, ""),
                        "adjustment_date": format_date(self.env, rec.adjustment_date),
                        "reason": rec.reason or "",
                        "approval_url": rec.get_approval_url_for(user.id),
                        "refusal_url": rec.get_refusal_url_for(user.id),
                        "revert_url": rec.get_revert_url_for(user.id),
                        "transfer_url": rec.get_transfer_url_for(user.id),
                        "record_url": rec.get_record_url(),
                        "leave_summary_table": Markup(leave_summary_html),
                        "previous_adjustments_table": Markup(previous_adjustments_html),
                        "transfer_notice": (
                            Markup(transfer_notice) if transfer_notice else ""
                        ),
                    },
                    minimal_qcontext=True,
                )

                self.env["mail.mail"].sudo().create(
                    {
                        "subject": subject,
                        "body_html": email_body,
                        "email_to": partner_rec.email,
                        "email_from": rec.env.user.email_formatted,
                    }
                ).send()

            if log_chatter:
                chatter_msg = f"{rec.employee_id.name} requests a leave adjustment of {rec.adjustment} day(s). Date: {format_date(self.env, rec.adjustment_date)}. Reason: {rec.reason}"
                rec.message_post(body=chatter_msg, subject=subject)

    def _generate_leave_summary_table_html(self):
        """Generate HTML table for employee leave history."""
        self.ensure_one()

        if not self.leave_history_ids:
            return '<p style="color:#999; font-style:italic;">No leave history available.</p>'

        # Limit to last 10 records for email brevity
        recent_history = self.leave_history_ids.sorted(
            key=lambda r: r.event_date, reverse=True
        )[:10]

        section_style = "color:#007bff;font-size:18px;font-weight:bold;margin-top:35px;margin-bottom:12px;border-bottom:3px solid #007bff;padding-bottom:8px;"
        table_style = "width:100%;border-collapse:collapse;margin:20px 0 30px 0;border:2px solid #007bff;"
        header_style = "background-color:#007bff;color:#ffffff;padding:12px 10px;text-align:left;font-weight:bold;border:1px solid #0056b3;"
        cell_style = (
            "padding:10px;border:1px solid #dee2e6;text-align:left;color:#495057;"
        )

        html = f'<div style="{section_style}">📊 Employee Leave History (Last 10 Records)</div>'
        html += f'<table style="{table_style}">'
        html += "<thead><tr>"
        html += f'<th style="{header_style}">Date</th>'
        html += f'<th style="{header_style}">Approved Leaves</th>'
        html += f'<th style="{header_style}">Adjustment</th>'
        html += f'<th style="{header_style}">Absent Days</th>'
        html += f'<th style="{header_style}">Allowed Leaves</th>'
        html += f'<th style="{header_style}">Remaining</th>'
        html += f'<th style="{header_style}">Closing Balance</th>'
        html += "</tr></thead>"
        html += "<tbody>"

        for idx, record in enumerate(recent_history, start=1):
            row_bg = "#f8f9fa" if idx % 2 == 0 else "#ffffff"
            row_style = f"background-color:{row_bg};"
            html += f'<tr style="{row_style}">'
            html += f'<td style="{cell_style}">{format_date(self.env, record.event_date)}</td>'
            html += f'<td style="{cell_style}">{record.approved_leaves:.2f}</td>'
            html += f'<td style="{cell_style}">{record.leave_adjustment:.2f}</td>'
            html += f'<td style="{cell_style}">{record.absent_days:.2f}</td>'
            html += f'<td style="{cell_style}">{record.allowed_leaves:.2f}</td>'
            html += f'<td style="{cell_style}">{record.remaining_leaves:.2f}</td>'
            html += f'<td style="{cell_style}"><strong>{record.closing_leaves:.2f}</strong></td>'
            html += "</tr>"

        html += "</tbody></table>"
        return html

    def _generate_previous_adjustments_table_html(self):
        """Generate HTML table for previous adjustments."""
        self.ensure_one()

        if not self.previous_adjustments_ids:
            return '<p style="color:#999; font-style:italic;">No previous adjustments found.</p>'

        # Limit to last 10 records for email brevity
        recent_adjustments = self.previous_adjustments_ids.sorted(
            key=lambda r: r.adjustment_date, reverse=True
        )[:10]

        table_style = "width:100%;border-collapse:collapse;margin:20px 0 30px 0;border:2px solid #007bff;"
        header_style = "background-color:#007bff;color:#ffffff;padding:12px 10px;text-align:left;font-weight:bold;border:1px solid #0056b3;"
        cell_style = (
            "padding:10px;border:1px solid #dee2e6;text-align:left;color:#495057;"
        )
        section_style = "color:#007bff;font-size:18px;font-weight:bold;margin-top:35px;margin-bottom:12px;border-bottom:3px solid #007bff;padding-bottom:8px;"
        separator_style = "height:25px;margin:30px 0;border-bottom:1px solid #dee2e6;"
        badge_base = "color:#ffffff;padding:4px 10px;border-radius:4px;font-size:12px;font-weight:bold;display:inline-block;"

        html = f'<div style="{separator_style}"></div>'
        html += f'<div style="{section_style}">📋 Previous Adjustments (Last 10 Records)</div>'
        html += f'<table style="{table_style}">'
        html += "<thead><tr>"
        html += f'<th style="{header_style}">Sequence</th>'
        html += f'<th style="{header_style}">Date</th>'
        html += f'<th style="{header_style}">Adjustment</th>'
        html += f'<th style="{header_style}">Type</th>'
        html += f'<th style="{header_style}">Reason</th>'
        html += f'<th style="{header_style}">Status</th>'
        html += "</tr></thead>"
        html += "<tbody>"

        for idx, record in enumerate(recent_adjustments, start=1):
            adjustment_type = dict(record._fields["adjustment_type"].selection).get(
                record.adjustment_type, ""
            )
            if record.state == "approved":
                state_badge = f'<span style="{badge_base}background-color:#28a745;">Approved</span>'
            elif record.state == "rejected":
                state_badge = f'<span style="{badge_base}background-color:#dc3545;">Rejected</span>'
            elif record.state == "reverted":
                state_badge = f'<span style="{badge_base}background-color:#6c757d;">Reverted</span>'
            else:
                state_badge = record.state.title()

            row_bg = "#f8f9fa" if idx % 2 == 0 else "#ffffff"
            row_style = f"background-color:{row_bg};"
            reason = record.reason or ""
            if len(reason) > 50:
                reason = reason[:50] + "..."

            html += f'<tr style="{row_style}">'
            html += f'<td style="{cell_style}">{record.sequence or ""}</td>'
            html += f'<td style="{cell_style}">{format_date(self.env, record.adjustment_date)}</td>'
            html += f'<td style="{cell_style}"><strong>{record.adjustment:.2f}</strong></td>'
            html += f'<td style="{cell_style}">{adjustment_type}</td>'
            html += f'<td style="{cell_style}">{reason}</td>'
            html += f'<td style="{cell_style}">{state_badge}</td>'
            html += "</tr>"

        html += "</tbody></table>"
        return html
