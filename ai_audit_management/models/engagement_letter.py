from odoo import _, fields, models


class AuditEngagementLetter(models.Model):
    _name = "audit.engagement.letter"
    _description = "Engagement Letter"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
        "audit.ai.helper.mixin",
        "audit.collaboration.mixin",
    ]
    _order = "create_date desc"

    name = fields.Char(default=lambda self: _("Engagement Letter"), tracking=True)
    client_acceptance_id = fields.Many2one(
        "audit.client.acceptance", string="Acceptance", ondelete="set null"
    )
    client_id = fields.Many2one("res.partner", required=False, tracking=True)
    scope_of_audit = fields.Text(tracking=True)
    laws_applicable = fields.Selection(
        [
            ("companies_act_2017", "Companies Act 2017"),
            ("ifrs", "IFRS"),
            ("isa", "ISA"),
            ("combined", "Combined Pakistan Framework"),
        ],
        default="isa",
        tracking=True,
    )
    fee = fields.Float(tracking=True)
    start_date = fields.Date(tracking=True)
    end_date = fields.Date(tracking=True)
    approval_status = fields.Selection(
        [
            ("draft", "Draft"),
            ("under_review", "Under Review"),
            ("approved", "Approved"),
        ],
        default="draft",
        tracking=True,
    )
    generated_pdf = fields.Binary(string="Signed PDF")
    letter_body = fields.Html(sanitize=False)
    assigned_user_ids = fields.Many2many(
        "res.users", string="Assigned Team", tracking=True
    )

    def action_submit(self):
        self.write({"approval_status": "under_review"})
        self.schedule_review_activity(_("Engagement letter ready for approval."))

    def action_approve(self):
        self.write({"approval_status": "approved"})

    def action_ai_draft_letter(self):
        for record in self:
            prompt = f"""
                Draft an ISA 210 compliant engagement letter referencing Pakistan Companies Act 2017.
                Client: {record.client_id.display_name if record.client_id else record.name}
                Scope: {record.scope_of_audit}
                Laws: {record.laws_applicable}
                Fee: {record.fee}
                Period: {record.start_date} to {record.end_date}
            """
            record.letter_body = record._call_openai(prompt, temperature=0.1)
        return True

    def action_print_letter(self):
        return self.env.ref(
            "ai_audit_management.report_engagement_letter"
        ).report_action(self)
