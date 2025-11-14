from odoo import http
from odoo.http import request
import uuid


class LeaveCondonationApprovalController(http.Controller):

    @http.route(['/leave_condonation/approve/<string:token>'], type='http', auth='public', website=True)
    def approve_condonation(self, token):
        validator = request.env['leave.condonation.approval'].sudo().search([('approve_token', '=', token)], limit=1)
        if not validator or validator.is_validation_status:
            return request.render('qaco_employees.condonation_invalid_token')
        record = validator.condonation_id
        if not record or record.state != 'submitted':
            return request.render('qaco_employees.condonation_invalid_token')
        record.sudo().with_user(validator.validating_users_id).action_approve()
        return request.render('qaco_employees.condonation_approval_success', {'record': record})

    @http.route(['/leave_condonation/refuse/<string:token>'], type='http', auth='public', website=True)
    def refuse_condonation(self, token):
        validator = request.env['leave.condonation.approval'].sudo().search([('approve_token', '=', token)], limit=1)
        if not validator or validator.is_validation_status:
            return request.render('qaco_employees.condonation_invalid_token')
        record = validator.condonation_id
        if not record or record.state != 'submitted':
            return request.render('qaco_employees.condonation_invalid_token')
        validator.is_validation_status = False
        record.action_reject()
        record.message_post(body=f"Leave condonation rejected by {validator.validating_users_id.name}")
        return request.render('qaco_employees.condonation_rejected', {'record': record})

    @http.route(['/leave_condonation/revert/<string:token>'], type='http', auth='public', website=True, methods=['GET', 'POST'], csrf=False)
    def revert_condonation(self, token, **post):
        validator = request.env['leave.condonation.approval'].sudo().search([('approve_token', '=', token)], limit=1)
        if not validator:
            return request.render('qaco_employees.condonation_invalid_token')
        record = validator.condonation_id
        if not record or record.state != 'submitted':
            return request.render('qaco_employees.condonation_invalid_token')

        if request.httprequest.method == 'POST':
            remark = post.get('remark')
            record.state = 'reverted'
            for line in record.approval_ids:
                line.is_validation_status = False
                line.approve_token = str(uuid.uuid4())
            remark_txt = f"\n{remark}" if remark else ""
            record.message_post(body=f"Condonation reverted by {validator.validating_users_id.name}{remark_txt}", subject='Condonation Reverted')

            if record.employee_id.work_email:
                body = ("<p>Your leave condonation has been reverted.</p>" +
                        (f"<p>Revert Remarks: <span style='color:#d9534f'>{remark}</span></p>" if remark else '') +
                        "<p>Please update and submit again.</p>")
                mail = request.env['mail.mail'].sudo().create({
                    'subject': 'Condonation Reverted',
                    'body_html': body,
                    'email_to': record.employee_id.work_email,
                    'email_from': request.env.user.email_formatted if request.env.user else '',
                })
                mail.send()
                record.message_post(body=body, subject='Condonation Reverted')

            record_url = record.get_record_url()
            approver_users = set(record.approval_ids.mapped('validating_users_id'))
            for user in approver_users:
                if user and user != validator.validating_users_id and user.partner_id.email:
                    body = ("<p>The leave condonation has been reverted.</p>" +
                            (f"<p>Revert Remarks: {remark}</p>" if remark else '') +
                            f"<p><a href='{record_url}'>View</a></p>")
                    request.env['mail.mail'].sudo().create({
                        'subject': 'Condonation Reverted',
                        'body_html': body,
                        'email_to': user.partner_id.email,
                        'email_from': request.env.user.email_formatted if request.env.user else '',
                    }).send()
            return request.render('qaco_employees.condonation_reverted', {'record': record})

        return request.render('qaco_employees.condonation_revert_form', {'token': token, 'record': record})

