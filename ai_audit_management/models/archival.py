from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AuditArchival(models.Model):
    _name = "audit.archival"
    _description = "Post-Audit Archival & Quality Control"
    _inherit = ["mail.thread", "mail.activity.mixin", "audit.collaboration.mixin"]

    file_index = fields.Char(required=True, tracking=True)
    locked_status = fields.Boolean(default=False, tracking=True)
    archival_date = fields.Date(
        default=lambda self: fields.Date.context_today(self), tracking=True
    )
    retention_period = fields.Integer(
        default=365, help="Retention in days.", tracking=True
    )
    qc_reviewer = fields.Many2one("res.users", tracking=True)
    qc_comments = fields.Text()
    document_ids = fields.Many2many(
        "ir.attachment",
        "audit_archival_attachment_rel",
        "archival_id",
        "attachment_id",
        string="Archived Files",
    )
    assigned_user_ids = fields.Many2many(
        "res.users", string="Assigned Team", tracking=True
    )

    def write(self, vals):
        if any(record.locked_status for record in self):
            disallowed = set(vals) - {"qc_comments"}
            if disallowed:
                raise UserError(_("Locked archives cannot be edited."))
        return super().write(vals)

    def unlink(self):
        if any(record.locked_status for record in self):
            raise UserError(_("Locked archives cannot be deleted."))
        return super().unlink()

    def action_lock(self):
        self.write({"locked_status": True})

    @api.model
    def cron_lock_archival_files(self):
        cutoff = fields.Date.context_today(self) - relativedelta(days=60)
        domain = [
            ("locked_status", "=", False),
            ("archival_date", "<=", cutoff),
        ]
        records = self.search(domain)
        records.write({"locked_status": True})
        return True
