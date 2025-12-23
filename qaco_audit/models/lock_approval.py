# -*- coding: utf-8 -*-
from odoo import _, api, exceptions, fields, models


class AuditLockApproval(models.Model):
    _name = "qaco.audit.lock.approval"
    _description = "Audit Lock/Unlock Approval"
    _order = "requested_on desc"

    audit_id = fields.Many2one(
        "qaco.audit", string="Engagement", required=True, ondelete="cascade", index=True
    )
    requestor_id = fields.Many2one(
        "res.users",
        string="Requested by",
        default=lambda self: self.env.user,
        readonly=True,
    )
    requested_on = fields.Datetime(
        string="Requested On", default=fields.Datetime.now, readonly=True
    )
    reason = fields.Text(string="Reason for override", required=True)
    status = fields.Selection(
        [("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
        string="Status",
        default="pending",
        tracking=True,
    )
    approver_id = fields.Many2one("res.users", string="Reviewed by", readonly=True)
    approved_on = fields.Datetime(string="Reviewed On", readonly=True)
    resolution_note = fields.Text(string="Resolution Note")
    applied = fields.Boolean(string="Applied", default=False, readonly=True)

    attachment_ids = fields.Many2many("ir.attachment", string="Supporting Documents")

    def action_approve(self, note=None):
        """Approve the override and apply the unlock to the linked audit (manager-only action)."""
        for rec in self:
            if not self.env.user.has_group("qaco_audit.group_audit_manager"):
                raise exceptions.AccessError(
                    _("Only managers can approve lock/unlock requests.")
                )
            if rec.status == "approved":
                continue
            rec.write(
                {
                    "status": "approved",
                    "approver_id": self.env.user.id,
                    "approved_on": fields.Datetime.now(),
                    "resolution_note": note or rec.resolution_note,
                }
            )
            # Apply the unlock if the audit is still locked
            if (
                rec.audit_id
                and rec.audit_id.engagement_status == "locked"
                and not rec.applied
            ):
                rec.audit_id.action_unlock_engagement(
                    reason=f"Override approved: {rec.reason}"
                )
                rec.applied = True

    def action_reject(self, note=None):
        for rec in self:
            if not self.env.user.has_group("qaco_audit.group_audit_manager"):
                raise exceptions.AccessError(
                    _("Only managers can reject lock/unlock requests.")
                )
            rec.write(
                {
                    "status": "rejected",
                    "approver_id": self.env.user.id,
                    "approved_on": fields.Datetime.now(),
                    "resolution_note": note or rec.resolution_note,
                }
            )

    @api.model
    def create(self, vals):
        rec = super(AuditLockApproval, self).create(vals)
        # notify the managing partners/group for attention
        rec.audit_id.message_post(
            body=f"{rec.requestor_id.name} requested unlock: {rec.reason}"
        )
        return rec
