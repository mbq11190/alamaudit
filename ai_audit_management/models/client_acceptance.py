from odoo import _, api, fields, models


class AuditClientAcceptance(models.Model):
    _name = "audit.client.acceptance"
    _description = "Client Acceptance & Pre-Engagement"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
        "audit.ai.helper.mixin",
        "audit.collaboration.mixin",
    ]
    _order = "create_date desc"

    client_name = fields.Char(required=True, tracking=True)
    client_id = fields.Many2one("res.partner", string="Client", tracking=True)
    client_type = fields.Selection(
        [
            ("company", "Company"),
            ("ngo", "NGO"),
            ("section42", "Section 42 Company"),
            ("public_interest", "Public Interest Entity"),
        ],
        default="company",
        tracking=True,
    )
    background_check_notes = fields.Text(tracking=True)
    ai_background_summary = fields.Text(string="AI Risk Summary", tracking=True)
    integrity_score = fields.Float(tracking=True)
    risk_level = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("critical", "Critical"),
        ],
        default="medium",
        tracking=True,
    )
    prior_auditor_details = fields.Text()
    acceptance_status = fields.Selection(
        [
            ("draft", "Draft"),
            ("pending_review", "Pending Review"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="draft",
        tracking=True,
    )
    attachment_ids = fields.Many2many(
        "ir.attachment",
        "audit_acceptance_attachment_rel",
        "acceptance_id",
        "attachment_id",
        string="Supporting Attachments",
    )
    assigned_user_ids = fields.Many2many(
        "res.users", string="Assigned Team", tracking=True
    )
    generated_letter_id = fields.Many2one(
        "audit.engagement.letter", string="Engagement Letter"
    )
    approval_date = fields.Date(readonly=True)

    @api.onchange("client_id")
    def _onchange_client(self):
        for record in self:
            if record.client_id:
                record.client_name = record.client_id.name

    def action_submit(self):
        self.write({"acceptance_status": "pending_review"})
        self.schedule_review_activity(_("Please review the client acceptance dossier."))

    def action_approve(self):
        today = fields.Date.context_today(self)
        for record in self:
            record.write({"acceptance_status": "approved", "approval_date": today})
            record._create_engagement_letter()

    def action_reject(self):
        self.write({"acceptance_status": "rejected"})

    def action_ai_background_analysis(self):
        for record in self:
            prompt = f"""
                Provide a comprehensive client acceptance risk evaluation with Pakistan regulatory context.
                Client Name: {record.client_name}
                Type: {record.client_type}
                Integrity Score: {record.integrity_score}
                Background Notes: {record.background_check_notes}
                Prior Auditor: {record.prior_auditor_details}
                Desired Output: paragraph summary plus recommendation.
            """
            record.ai_background_summary = record._call_openai(prompt)
        return True

    def _create_engagement_letter(self):
        letter_model = self.env["audit.engagement.letter"]
        for record in self:
            if record.generated_letter_id:
                continue
            values = {
                "client_acceptance_id": record.id,
                "client_id": record.client_id.id,
                "scope_of_audit": record.background_check_notes
                or _("Scope auto-generated from acceptance memo."),
                "laws_applicable": "companies_act_2017",
                "fee": 0.0,
                "start_date": fields.Date.context_today(self),
                "approval_status": "draft",
            }
            letter = letter_model.create(values)
            record.generated_letter_id = letter.id
        return True
