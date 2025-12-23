# -*- coding: utf-8 -*-
import base64
import hashlib
import logging
from datetime import date

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

SENSITIVITY_LEVELS = [
    ("normal", "Normal"),
    ("restricted", "Restricted"),
    ("highly_restricted", "Highly Restricted"),
]

DOC_STATE = [
    ("draft", "Draft"),
    ("final", "Final"),
    ("superseded", "Superseded"),
    ("deleted", "Deleted"),
]

FOLDER_STATUS = [
    ("created", "Created"),
    ("partial", "Partially created"),
    ("exception", "Exception"),
]


class OnboardingDocumentFolder(models.Model):
    _name = "qaco.onboarding.document.folder"
    _description = "Onboarding Document Folder"

    onboarding_id = fields.Many2one(
        "qaco.client.onboarding", required=True, ondelete="cascade", index=True
    )
    name = fields.Char(string="Folder Name", required=True)
    code = fields.Char(string="Folder Code")
    parent_id = fields.Many2one(
        "qaco.onboarding.document.folder", string="Parent Folder"
    )
    status = fields.Selection(FOLDER_STATUS, default="partial")
    sequence = fields.Integer(string="Sequence", default=10)
    description = fields.Text(string="Description")
    client_visible = fields.Boolean(
        string="Client Uploads Visible",
        default=False,
        help="If true, client uploaded docs in this folder are visible to the portal user",
    )
    doc_count = fields.Integer(string="Documents", compute="_compute_doc_count")

    @api.depends("onboarding_id")
    def _compute_doc_count(self):
        for f in self:
            f.doc_count = self.env["qaco.onboarding.document"].search_count(
                [("folder_id", "=", f.id)]
            )


class OnboardingDocumentHistory(models.Model):
    _name = "qaco.onboarding.document.history"
    _description = "Onboarding Document History (versions)"

    document_id = fields.Many2one(
        "qaco.onboarding.document", required=True, ondelete="cascade", index=True
    )
    version = fields.Integer(string="Version", required=True)
    file = fields.Binary(string="File", attachment=True)
    file_name = fields.Char(string="File Name")
    checksum = fields.Char(string="Checksum (sha256)")
    file_size = fields.Integer(string="File size (bytes)")
    created_by = fields.Many2one(
        "res.users", string="Created by", default=lambda self: self.env.user
    )
    create_date = fields.Datetime(string="Timestamp", default=fields.Datetime.now)


class OnboardingDocumentAudit(models.Model):
    _name = "qaco.onboarding.document.audit"
    _description = "Document Vault Audit Log"

    document_id = fields.Many2one(
        "qaco.onboarding.document", required=True, ondelete="cascade", index=True
    )
    action = fields.Selection(
        [
            ("upload", "Upload"),
            ("view", "View"),
            ("download", "Download"),
            ("rename", "Rename"),
            ("move", "Move"),
            ("supersede", "Supersede"),
            ("delete", "Delete"),
            ("restore", "Restore"),
        ],
        required=True,
    )
    user_id = fields.Many2one(
        "res.users", string="User", default=lambda self: self.env.user
    )
    notes = fields.Text(string="Notes")
    create_date = fields.Datetime(string="Timestamp", default=fields.Datetime.now)


class OnboardingDocument(models.Model):
    _inherit = "qaco.onboarding.document"

    folder_id = fields.Many2one("qaco.onboarding.document.folder", string="Folder")
    sensitivity = fields.Selection(
        SENSITIVITY_LEVELS, string="Sensitivity", default="normal"
    )
    version = fields.Integer(string="Version", default=1)
    state = fields.Selection(DOC_STATE, string="Document state", default="draft")
    checksum = fields.Char(string="SHA256 Checksum")
    file_size = fields.Integer(string="File size (bytes)")
    legal_hold = fields.Boolean(
        string="Legal hold",
        default=False,
        help="When set deletion/archival is prevented",
    )
    retention_date = fields.Date(string="Retention until")
    retention_policy = fields.Char(string="Retention policy name")
    history_ids = fields.One2many(
        "qaco.onboarding.document.history", "document_id", string="Version history"
    )
    audit_ids = fields.One2many(
        "qaco.onboarding.document.audit", "document_id", string="Document audit log"
    )
    uploaded_by = fields.Many2one(
        "res.users", string="Uploaded by", default=lambda self: self.env.user
    )
    is_client_upload = fields.Boolean(string="Client upload", default=False)

    @api.model
    def create(self, vals):
        vals.setdefault("uploaded_by", self.env.uid)
        rec = super(OnboardingDocument, self).create(vals)
        rec._update_file_metadata()
        rec._record_audit("upload", notes=_("Document uploaded"))
        return rec

    def write(self, vals):
        # If file is being replaced, create history and increment version
        for rec in self:
            if "file" in vals or "file_name" in vals:
                # push current into history
                if rec.file:
                    hist_vals = {
                        "document_id": rec.id,
                        "version": rec.version,
                        "file": rec.file,
                        "file_name": rec.file_name,
                        "checksum": rec.checksum,
                        "file_size": rec.file_size,
                        "created_by": self.env.uid,
                    }
                    self.env["qaco.onboarding.document.history"].create(hist_vals)
                    vals["version"] = (rec.version or 1) + 1
                    vals["state"] = "final"
                # record upload audit
                self._record_audit("upload", notes=_("Document updated"))
        res = super(OnboardingDocument, self).write(vals)
        # Update metadata after write
        for rec in self:
            rec._update_file_metadata()
        return res

    def _update_file_metadata(self):
        for rec in self:
            if rec.file:
                try:
                    data = base64.b64decode(rec.file)
                except Exception:
                    data = base64.b64decode(
                        rec.file.decode("utf-8")
                        if isinstance(rec.file, bytes)
                        else rec.file or ""
                    )
                rec.file_size = len(data)
                rec.checksum = hashlib.sha256(data).hexdigest()
            else:
                rec.file_size = 0
                rec.checksum = False

    def _record_audit(self, action, notes=""):
        for rec in self:
            try:
                self.env["qaco.onboarding.document.audit"].create(
                    {
                        "document_id": rec.id,
                        "action": action,
                        "user_id": self.env.uid,
                        "notes": notes,
                    }
                )
            except Exception:
                _logger.exception("Failed to record document audit for %s", rec.id)

    def action_view_history(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "qaco.onboarding.document.history",
            "domain": [("document_id", "=", self.id)],
            "view_mode": "tree,form",
            "target": "new",
        }

    def action_record_view(self):
        for rec in self:
            rec._record_audit("view", notes=_("Viewed document"))
        return True

    def action_record_download(self):
        for rec in self:
            rec._record_audit("download", notes=_("Downloaded document"))
        return True

    def unlink(self):
        for rec in self:
            if rec.legal_hold:
                raise ValidationError(
                    _("Document is on legal hold and cannot be deleted.")
                )
            if rec.retention_date and rec.retention_date > date.today():
                raise ValidationError(
                    _("Document retention policy prevents deletion until %s")
                    % (rec.retention_date,)
                )
            # record deletion audit
            rec._record_audit("delete", notes=_("Document deleted"))
        return super(OnboardingDocument, self).unlink()

    def action_set_legal_hold(self, flag=True):
        self.write({"legal_hold": flag})
        for rec in self:
            rec._record_audit(
                "move" if flag else "restore",
                notes=_("Legal hold set" if flag else "Legal hold removed"),
            )
        return True
