import json
import re

from odoo import _, fields, models


class AuditPlan(models.Model):
    _name = "audit.plan"
    _description = "Audit Planning (ISA 300 & 315)"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
        "audit.ai.helper.mixin",
        "audit.collaboration.mixin",
    ]
    _order = "financial_year desc"

    name = fields.Char(default=lambda self: _("Audit Plan"), tracking=True)
    client_id = fields.Many2one("res.partner", tracking=True)
    financial_year = fields.Char(required=True, tracking=True)
    overall_materiality = fields.Float(tracking=True)
    performance_materiality = fields.Float(tracking=True)
    entity_understanding = fields.Text(tracking=True)
    risk_assessment_summary = fields.Text(tracking=True)
    planned_procedures_json = fields.Json()
    planned_procedures_text = fields.Text(string="Planned Procedures (Readable)")
    team_assignments = fields.Many2many(
        "hr.employee", string="Team Assignments", tracking=True
    )
    approval_state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("approved", "Approved"),
        ],
        default="draft",
        tracking=True,
    )
    document_ids = fields.Many2many(
        "ir.attachment",
        "audit_plan_document_rel",
        "plan_id",
        "attachment_id",
        string="Reference Documents",
    )
    assigned_user_ids = fields.Many2many(
        "res.users", string="Assigned Team", tracking=True
    )

    def action_submit_for_approval(self):
        self.write({"approval_state": "submitted"})
        self.schedule_review_activity(_("Audit plan submitted for approval."))

    def action_mark_approved(self):
        self.write({"approval_state": "approved"})

    def ai_calculate_materiality(self):
        for record in self:
            prompt = f"""
                Provide overall and performance materiality benchmarks using ISA 320 heuristics.
                Client: {record.client_id.display_name if record.client_id else 'Unknown'}
                Financial Year: {record.financial_year}
                Known Risk Summary: {record.risk_assessment_summary}
                Provide numeric basis in PKR.
            """
            response = record._call_openai(prompt, temperature=0.05)
            record.planned_procedures_text = response
            numbers = re.findall(r"[0-9]+(?:\.[0-9]+)?", response)
            if numbers:
                record.overall_materiality = float(numbers[0])
                if len(numbers) > 1:
                    record.performance_materiality = float(numbers[1])
        return True

    def ai_generate_audit_plan(self):
        for record in self:
            prompt = f"""
                Generate a structured ISA compliant audit plan json.
                Entity: {record.client_id.display_name if record.client_id else 'Client'}
                Year: {record.financial_year}
                Understanding: {record.entity_understanding}
                Materiality: {record.overall_materiality}
                Risks: {record.risk_assessment_summary}
                Output keys: scope, staffing, timelines, procedures.
            """
            content = record._call_openai(prompt)
            record.planned_procedures_text = content
            try:
                record.planned_procedures_json = json.loads(content)
            except json.JSONDecodeError:
                record.planned_procedures_json = {"raw": content}
        return True

    def ai_identify_risks_from_uploaded_docs(self):
        for record in self:
            doc_names = ", ".join(record.document_ids.mapped("name"))
            prompt = f"""
                Review analytical documents ({doc_names}) and summarise key ISA 315 risks.
                Provide bullets for inherent, control, and fraud risks referencing Pakistan regulations.
            """
            record.risk_assessment_summary = record._call_openai(prompt)
        return True
