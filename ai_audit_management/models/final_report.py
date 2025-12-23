import json

from odoo import _, fields, models


class AuditFinalReport(models.Model):
    _name = "audit.final.report"
    _description = "Audit Report Generation"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
        "audit.ai.helper.mixin",
        "audit.collaboration.mixin",
    ]

    name = fields.Char(default=lambda self: _("Audit Report"))
    client_id = fields.Many2one("res.partner", tracking=True)
    report_type = fields.Selection(
        [
            ("unmodified", "Unmodified Opinion"),
            ("qualified", "Qualified Opinion"),
            ("disclaimer", "Disclaimer"),
            ("adverse", "Adverse"),
        ],
        default="unmodified",
        tracking=True,
    )
    key_audit_matter_ids = fields.One2many(
        "audit.final.report.kam", "final_report_id", string="Key Audit Matters"
    )
    final_pdf_report = fields.Binary(string="Signed Report")
    opinion_text = fields.Html()
    isa_quality_notes = fields.Text()
    assigned_user_ids = fields.Many2many(
        "res.users", string="Assigned Team", tracking=True
    )

    def ai_draft_audit_opinion(self):
        for record in self:
            prompt = f"""
                Draft a Pakistan ISA compliant audit opinion.
                Report Type: {record.report_type}
                Client: {record.client_id.display_name if record.client_id else 'Client'}
                Include references to Companies Act 2017 and ISA 700.
            """
            record.opinion_text = record._call_openai(prompt)
        return True

    def ai_generate_KAMs_from_workpapers(self):
        for record in self:
            prompt = f"""
                Derive key audit matters from workpaper summaries: {record.opinion_text}.
                Respond using JSON list with keys title, description, response.
            """
            kam_raw = record._call_openai(prompt)
            record.isa_quality_notes = kam_raw
            try:
                kam_payload = json.loads(kam_raw)
            except json.JSONDecodeError:
                kam_payload = [
                    {
                        "title": _("AI Generated Matter"),
                        "description": kam_raw,
                        "response": "",
                    }
                ]
            record.key_audit_matter_ids.unlink()
            vals_list = []
            for kam in kam_payload:
                vals_list.append(
                    (
                        0,
                        0,
                        {
                            "name": kam.get("title") or _("Key Matter"),
                            "description": kam.get("description"),
                            "response": kam.get("response"),
                        },
                    )
                )
            if vals_list:
                record.write({"key_audit_matter_ids": vals_list})
        return True

    def ai_quality_check_ISA_compliance(self):
        for record in self:
            prompt = f"""
                Review this draft opinion for ISA 700 and ISA 705 compliance, list gaps.
                Content: {record.opinion_text}
            """
            record.isa_quality_notes = record._call_openai(prompt)
        return True

    def action_print_report(self):
        return self.env.ref("ai_audit_management.report_audit_final").report_action(
            self
        )


class AuditFinalReportKAM(models.Model):
    _name = "audit.final.report.kam"
    _description = "Key Audit Matter"

    name = fields.Char(required=True)
    description = fields.Text()
    response = fields.Text()
    final_report_id = fields.Many2one("audit.final.report", ondelete="cascade")
