from odoo import fields, models


class AuditEvidenceIndex(models.Model):
    _name = "audit.evidence.index"
    _description = "Audit Evidence Index"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(default="Evidence Index", required=True, tracking=True)
    final_report_id = fields.Many2one("audit.final.report", string="Final Report")
    attachment_ids = fields.Many2many("ir.attachment", string="Evidence Attachments")
    line_ids = fields.One2many(
        "audit.evidence.index.line", "index_id", string="Index Lines"
    )
    ai_summary = fields.Text()

    def action_generate_index(self):
        for record in self:
            record.line_ids.unlink()
            commands = []
            for attachment in record.attachment_ids:
                commands.append(
                    (
                        0,
                        0,
                        {
                            "name": attachment.name,
                            "source_document": attachment.datas_fname
                            or attachment.name,
                            "assertion_addressed": "Multiple",
                        },
                    )
                )
            if commands:
                record.write({"line_ids": commands})
            prompt = f"Summarize audit evidence set ({len(record.attachment_ids)} files) into a concise overview for partner review."
            if record.final_report_id:
                prompt += f" Report type: {record.final_report_id.report_type}."
            record.ai_summary = record.env["audit.ai.helper.mixin"]._call_openai(prompt)
        return True


class AuditEvidenceIndexLine(models.Model):
    _name = "audit.evidence.index.line"
    _description = "Evidence Index Line"

    name = fields.Char(required=True)
    source_document = fields.Char()
    assertion_addressed = fields.Char()
    index_id = fields.Many2one("audit.evidence.index", ondelete="cascade")
