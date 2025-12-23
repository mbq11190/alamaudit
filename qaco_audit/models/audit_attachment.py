import werkzeug.urls
from odoo import api, fields, models


class auditAttachment(models.Model):
    _name = "audit.attachment"
    _description = "audit Attachment"

    name = fields.Char(string="File Name")
    file = fields.Binary(string="File")
    file_type = fields.Selection(
        [
            ("pdf", "PDF"),
            ("docx", "DOCX"),
            ("xlsx", "XLSX"),
            ("img", "Image"),
            ("eml", "Email"),
        ],
        string="File Type",
    )
    version = fields.Integer(string="Version", default=1)
    superseded = fields.Boolean(string="Superseded", default=False)
    document_index = fields.Char(string="Document Index", readonly=True)
    evidence_ref = fields.Char(string="Evidence Reference", readonly=True)
    confidentiality = fields.Selection(
        [("public", "Public"), ("restricted", "Restricted")],
        string="Confidentiality",
        default="public",
    )
    audit_id = fields.Many2one("qaco.audit", string="Audit")

    @api.model
    def create(self, vals):
        # assign document index and evidence ref sequences
        if not vals.get("document_index"):
            vals["document_index"] = (
                self.env["ir.sequence"].next_by_code("audit.document.index")
                or "DOC-NEW"
            )
        if not vals.get("evidence_ref"):
            vals["evidence_ref"] = (
                self.env["ir.sequence"].next_by_code("audit.evidence.ref") or "EVID-NEW"
            )
        rec = super().create(vals)
        # Log attachment creation on the audit record
        if rec.audit_id:
            rec.audit_id.message_post(
                body=f"Attachment {rec.name} uploaded ({rec.document_index}) by {rec.create_uid.name}"
            )
        return rec

    def download_attachment(self):
        """Return an action opening the binary file in the browser."""
        self.ensure_one()
        url = "/web/content/%s/%s/file/%s?download=true" % (
            self._name,
            self.id,
            werkzeug.urls.url_quote(self.name or "file"),
        )
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }

    def delete_attachment(self):
        """Delete the attachment safely."""
        self.unlink()
