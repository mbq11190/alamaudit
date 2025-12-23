from odoo import _, fields, models
from odoo.exceptions import UserError


class AuditOCRDocument(models.Model):
    _name = "audit.ocr.document"
    _description = "OCR Document"
    _inherit = ["mail.thread", "mail.activity.mixin", "audit.ai.helper.mixin"]

    name = fields.Char(required=True, default="Uploaded Document", tracking=True)
    attachment_id = fields.Many2one(
        "ir.attachment", string="Source File", required=True
    )
    document_type = fields.Selection(
        [
            ("bank_statement", "Bank Statement"),
            ("invoice", "Invoice"),
            ("ledger", "Ledger Extract"),
            ("contract", "Contract"),
            ("other", "Other"),
        ],
        default="other",
        tracking=True,
    )
    extracted_text = fields.Text(tracking=True)
    ai_summary = fields.Text(tracking=True)
    ai_sampling_suggestion = fields.Text(tracking=True)

    def action_run_ocr(self):
        # Placeholder: actual OCR requires Tesseract or OpenAI Vision. Here we guard and reuse AI for summarisation.
        for record in self:
            if not record.attachment_id:
                raise UserError(_("Please attach a document before running OCR."))
            base_info = _("File name: %s, type: %s") % (
                record.attachment_id.name,
                record.document_type,
            )
            # Fake extraction for now
            record.extracted_text = base_info
            prompt = f"""
                You are reviewing an audit evidence document. Summarize key points and suggest sampling.
                Context: {base_info}
            """
            record.ai_summary = record._call_openai(prompt)
            record.ai_sampling_suggestion = record._call_openai(
                "Suggest a sampling approach for this document type: %s"
                % record.document_type
            )
        return True
