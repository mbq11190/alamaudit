import uuid
from html import escape

from odoo import fields, http, tools
from odoo.http import request


class LeaveAdjustmentApprovalController(http.Controller):

    @http.route(
        ["/leave_adjustment/approve/<string:token>"],
        type="http",
        auth="public",
        website=True,
    )
    def approve_adjustment(self, token):
        validator = (
            request.env["leave.adjustment.approval"]
            .sudo()
            .search([("approve_token", "=", token)], limit=1)
        )
        if not validator or validator.is_validation_status:
            return request.render("qaco_employees.adjustment_invalid_token")
        adjustment = validator.adjustment_id
        if not adjustment or adjustment.state != "submitted":
            return request.render("qaco_employees.adjustment_invalid_token")
        adjustment.sudo().with_user(validator.validating_users_id).action_approve()
        return request.render(
            "qaco_employees.adjustment_approval_success", {"adjustment": adjustment}
        )

    @http.route(
        ["/leave_adjustment/refuse/<string:token>"],
        type="http",
        auth="public",
        website=True,
        methods=["GET", "POST"],
        csrf=False,
    )
    def refuse_adjustment(self, token, **post):
        validator = (
            request.env["leave.adjustment.approval"]
            .sudo()
            .search([("approve_token", "=", token)], limit=1)
        )
        if not validator or validator.is_validation_status:
            return request.render("qaco_employees.adjustment_invalid_token")
        adjustment = validator.adjustment_id
        if not adjustment or adjustment.state != "submitted":
            return request.render("qaco_employees.adjustment_invalid_token")

        # Show refusal form on GET request
        if request.httprequest.method == "GET":
            return request.render(
                "qaco_employees.adjustment_refuse_form",
                {"token": token, "adjustment": adjustment},
            )

        # Process refusal on POST request
        rejection_reason = post.get("rejection_reason", "").strip()

        if not rejection_reason:
            return request.render(
                "qaco_employees.adjustment_refuse_form",
                {
                    "token": token,
                    "adjustment": adjustment,
                    "error": "Please provide a reason for rejection.",
                },
            )

        validator.is_validation_status = False
        adjustment.do_reject_with_reason(rejection_reason)

        return request.render(
            "qaco_employees.adjustment_rejected",
            {"adjustment": adjustment, "rejection_reason": rejection_reason},
        )

    @http.route(
        ["/leave_adjustment/revert/<string:token>"],
        type="http",
        auth="public",
        website=True,
        methods=["GET", "POST"],
        csrf=False,
    )
    def revert_adjustment(self, token, **post):
        validator = (
            request.env["leave.adjustment.approval"]
            .sudo()
            .search([("approve_token", "=", token)], limit=1)
        )
        if not validator:
            return request.render("qaco_employees.adjustment_invalid_token")
        adjustment = validator.adjustment_id
        if not adjustment or adjustment.state != "submitted":
            return request.render("qaco_employees.adjustment_invalid_token")

        if request.httprequest.method == "POST":
            remark = post.get("remark")
            adjustment.state = "reverted"
            for line in adjustment.approval_ids:
                line.is_validation_status = False
                line.approve_token = str(uuid.uuid4())
            remark_txt = f"\n{remark}" if remark else ""
            adjustment.message_post(
                body=f"Adjustment reverted by {validator.validating_users_id.name}{remark_txt}",
                subject="Adjustment Reverted",
            )

            if adjustment.employee_id.work_email:
                body = (
                    "<p>Your leave adjustment has been reverted.</p>"
                    + (
                        f"<p>Revert Remarks: <span style='color:#d9534f'>{remark}</span></p>"
                        if remark
                        else ""
                    )
                    + "<p>Please update and submit again.</p>"
                )
                mail = (
                    request.env["mail.mail"]
                    .sudo()
                    .create(
                        {
                            "subject": "Adjustment Reverted",
                            "body_html": body,
                            "email_to": adjustment.employee_id.work_email,
                            "email_from": (
                                request.env.user.email_formatted
                                if request.env.user
                                else ""
                            ),
                        }
                    )
                )
                mail.send()
                sanitized = tools.html_sanitize(
                    body, strip_style=True, strip_classes=True
                )
                adjustment.message_post(body=sanitized, subject="Adjustment Reverted")

            record_url = adjustment.get_record_url()
            approver_users = set(adjustment.approval_ids.mapped("validating_users_id"))
            for user in approver_users:
                if (
                    user
                    and user != validator.validating_users_id
                    and user.partner_id.email
                ):
                    body = (
                        "<p>The adjustment has been reverted.</p>"
                        + (f"<p>Revert Remarks: {remark}</p>" if remark else "")
                        + f"<p><a href='{record_url}'>View Adjustment</a></p>"
                    )
                    request.env["mail.mail"].sudo().create(
                        {
                            "subject": "Adjustment Reverted",
                            "body_html": body,
                            "email_to": user.partner_id.email,
                            "email_from": (
                                request.env.user.email_formatted
                                if request.env.user
                                else ""
                            ),
                        }
                    ).send()
            return request.render(
                "qaco_employees.adjustment_reverted", {"adjustment": adjustment}
            )

        return request.render(
            "qaco_employees.adjustment_revert_form",
            {"token": token, "adjustment": adjustment},
        )

    @http.route(
        ["/leave_adjustment/transfer/<string:token>"],
        type="http",
        auth="public",
        website=True,
        methods=["GET", "POST"],
        csrf=False,
    )
    def transfer_adjustment(self, token, **post):
        validator = (
            request.env["leave.adjustment.approval"]
            .sudo()
            .search([("approve_token", "=", token)], limit=1)
        )
        if not validator or validator.is_validation_status:
            return request.render("qaco_employees.adjustment_invalid_token")

        adjustment = validator.adjustment_id
        if not adjustment or adjustment.state != "submitted":
            return request.render("qaco_employees.adjustment_invalid_token")

        def _get_transfer_candidates(exclude_user=None):
            Users = request.env["res.users"].sudo()
            candidates = Users.browse()

            if adjustment:
                candidates |= adjustment.approval_ids.mapped("validating_users_id")

            group_xmlids = [
                "qaco_employees.group_qaco_employee_administrator",
                "qaco_employees.group_qaco_employee_hr_manager",
                "qaco_employees.group_qaco_employee_manager",
                "qaco_employees.group_qaco_employee_partner",
                "base.group_system",
            ]
            group_ids = []
            for xmlid in group_xmlids:
                try:
                    group_ids.append(request.env.ref(xmlid).id)
                except ValueError:
                    continue

            if group_ids:
                candidates |= Users.search([("groups_id", "in", group_ids)])

            candidates = candidates.filtered(lambda u: u.active)
            if exclude_user:
                candidates = candidates.filtered(lambda u: u != exclude_user)

            return candidates.sorted(key=lambda u: (u.name or "").lower())

        # GET - Show transfer form
        if request.httprequest.method == "GET":
            users = _get_transfer_candidates(exclude_user=validator.validating_users_id)
            return request.render(
                "qaco_employees.adjustment_transfer_form",
                {
                    "token": token,
                    "adjustment": adjustment,
                    "users": users,
                    "current_user": validator.validating_users_id,
                },
            )

        # POST - Process transfer
        new_user_id = post.get("new_user_id")
        transfer_reason = post.get("transfer_reason", "").strip()

        if not new_user_id:
            return request.render(
                "qaco_employees.adjustment_transfer_form",
                {
                    "token": token,
                    "adjustment": adjustment,
                    "users": _get_transfer_candidates(
                        exclude_user=validator.validating_users_id
                    ),
                    "current_user": validator.validating_users_id,
                    "error": "Please select a user to transfer to.",
                },
            )

        new_user = request.env["res.users"].sudo().browse(int(new_user_id))
        if not new_user.exists():
            return request.render(
                "qaco_employees.adjustment_transfer_form",
                {
                    "token": token,
                    "adjustment": adjustment,
                    "users": _get_transfer_candidates(
                        exclude_user=validator.validating_users_id
                    ),
                    "current_user": validator.validating_users_id,
                    "error": "Invalid user selected.",
                },
            )

        # Transfer the approval
        old_user = validator.validating_users_id
        validator.validating_users_id = new_user
        validator.is_validation_status = False

        # Log the transfer with reason in chatter
        transfer_msg = f"""
        <div style='font-family: Arial, sans-serif;'>
            <h4 style='color: #007bff; margin-bottom: 10px;'>🔄 Approval Transferred</h4>
            <table style='border-collapse: collapse; width: 100%;'>
                <tr>
                    <td style='padding: 8px; border: 1px solid #ddd; background-color: #f9f9f9;'><strong>From:</strong></td>
                    <td style='padding: 8px; border: 1px solid #ddd;'>{old_user.name}</td>
                </tr>
                <tr>
                    <td style='padding: 8px; border: 1px solid #ddd; background-color: #f9f9f9;'><strong>To:</strong></td>
                    <td style='padding: 8px; border: 1px solid #ddd;'>{new_user.name}</td>
                </tr>
                {f"<tr><td style='padding: 8px; border: 1px solid #ddd; background-color: #f9f9f9;'><strong>Reason:</strong></td><td style='padding: 8px; border: 1px solid #ddd;'>{transfer_reason}</td></tr>" if transfer_reason else ''}
                <tr>
                    <td style='padding: 8px; border: 1px solid #ddd; background-color: #f9f9f9;'><strong>Date:</strong></td>
                    <td style='padding: 8px; border: 1px solid #ddd;'>{fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td>
                </tr>
            </table>
        </div>
        """
        adjustment.message_post(body=transfer_msg, subject="Approval Transferred")

        # Send email to new approver with full action buttons
        notice_origin = escape(old_user.name or "")
        notice_target = escape(new_user.name or "")
        notice_chunks = [
            f"<p><strong>Transferred by:</strong> {notice_origin}</p>",
            f"<p><strong>Assigned to you:</strong> {notice_target}</p>",
        ]
        if transfer_reason:
            notice_chunks.append(
                f"<p><strong>Transfer reason:</strong> {escape(transfer_reason)}</p>"
            )
        transfer_notice = "".join(notice_chunks)

        adjustment._send_submit_email(
            target_validators=validator,
            log_chatter=False,
            transfer_notice=transfer_notice,
        )

        return request.render(
            "qaco_employees.adjustment_transfer_success",
            {"adjustment": adjustment, "old_user": old_user, "new_user": new_user},
        )
