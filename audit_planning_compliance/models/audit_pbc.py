from __future__ import annotations

from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

from .audit_engagement import ENTITY_CLASSES


class AuditPbcTemplate(models.Model):
    _name = "audit.pbc.template"
    _description = "Default PBC Template"

    name = fields.Char(required=True)
    entity_classification = fields.Selection(ENTITY_CLASSES, required=True)
    description = fields.Text()
    category = fields.Selection(
        [
            ("financial", "Financial"),
            ("legal", "Legal"),
            ("tax", "Tax"),
            ("governance", "Governance"),
            ("other", "Other"),
        ],
        default="financial",
    )


class AuditPbcRequest(models.Model):
    _name = "audit.pbc.request"
    _description = "Provided By Client Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "due_date asc"

    engagement_id = fields.Many2one("audit.engagement", required=True, ondelete="cascade")
    name = fields.Char(required=True)
    description = fields.Text()
    requested_date = fields.Date()
    due_date = fields.Date(required=True)
    responsible_client_contact = fields.Many2one("res.partner", string="Client Contact")
    category = fields.Selection(
        [
            ("financial", "Financial"),
            ("legal", "Legal"),
            ("tax", "Tax"),
            ("governance", "Governance"),
            ("other", "Other"),
        ],
        default="financial",
        required=True,
    )
    delivery_status = fields.Selection(
        [
            ("not_requested", "Not Requested"),
            ("requested", "Requested"),
            ("received", "Received"),
            ("incomplete", "Incomplete"),
        ],
        default="not_requested",
        tracking=True,
    )
    received_date = fields.Date()
    attachment_ids = fields.Many2many("ir.attachment", string="Attachments")
    follow_up_log = fields.Html(string="Follow-up Log")
    reminder_count = fields.Integer(default=0)
    shared_with_portal = fields.Boolean(string="Client Portal Access", default=False)
    escalation_level = fields.Selection(
        [
            ("none", "None"),
            ("first", "Manager"),
            ("second", "Partner"),
        ],
        default="none",
    )
    reminder_log_ids = fields.One2many("audit.pbc.reminder.log", "request_id", string="Reminder History")

    def action_request(self):
        for record in self:
            record.delivery_status = "requested"
            record.requested_date = fields.Date.context_today(self)
            record.engagement_id.pbc_sent = True
            self.env["audit.evidence.log"].log_event(
                name=_("PBC issued"),
                model_name=self._name,
                res_id=record.id,
                action_type="state",
                note=record.description or record.name,
                standard_reference="ISA 300 para 13; ICAP APM section 7",
            )

    def action_mark_received(self):
        for record in self:
            record.delivery_status = "received"
            record.received_date = fields.Date.context_today(self)
            if not record.attachment_ids:
                raise ValidationError(_("Attach evidence before marking received."))
            self.env["audit.evidence.log"].log_event(
                name=_("PBC received"),
                model_name=self._name,
                res_id=record.id,
                action_type="update",
                note=_("Evidence attached for PBC."),
                standard_reference="ISA 300 para 11",
            )

    def action_send_reminder(self, escalation: bool = False):
        template = self.env.ref("audit_planning_compliance.email_template_pbc_reminder", raise_if_not_found=False)
        for record in self:
            if template:
                template.send_mail(record.id, force_send=True)
            record.reminder_count += 1
            if escalation:
                record.escalation_level = "second"
            elif record.reminder_count >= 2:
                record.escalation_level = "first"
            self.env["audit.pbc.reminder.log"].create(
                {
                    "request_id": record.id,
                    "reminder_type": "email",
                    "note": _("Automated reminder dispatched."),
                }
            )
            self.env["audit.evidence.log"].log_event(
                name=_("PBC reminder"),
                model_name=self._name,
                res_id=record.id,
                action_type="reminder",
                note=_("Reminder sent to client contact."),
                standard_reference="ICAP APM section 7; SECP Guide section 4",
            )

    @api.model
    def cron_escalate_overdue(self):
        escalation_days = int(self.env["ir.config_parameter"].sudo().get_param("audit_planning.pbc_escalation_days", 3))
        threshold = fields.Date.to_string(fields.Date.context_today(self) - timedelta(days=escalation_days))
        overdue = self.search(
            [
                ("delivery_status", "!=", "received"),
                ("due_date", "<=", threshold),
            ]
        )
        overdue.action_send_reminder(escalation=True)


class AuditPbcReminderLog(models.Model):
    _name = "audit.pbc.reminder.log"
    _description = "PBC Reminder Log"

    request_id = fields.Many2one("audit.pbc.request", required=True, ondelete="cascade")
    reminder_type = fields.Selection([("email", "Email"), ("call", "Call"), ("portal", "Portal")])
    reminder_date = fields.Datetime(default=fields.Datetime.now)
    note = fields.Text()
