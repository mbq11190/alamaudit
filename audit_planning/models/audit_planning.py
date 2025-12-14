# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AuditPlanning(models.Model):
    _name = "audit.planning"
    _description = "Audit Planning"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    # Engagement details
    name = fields.Char(string="Planning Reference", required=True, tracking=True)
    client_id = fields.Many2one(
        "res.partner",
        string="Client",
        required=True,
        tracking=True,
        domain=[("is_company", "=", True)],
    )
    ntn = fields.Char(string="NTN")
    strn = fields.Char(string="STRN")
    company_nature = fields.Selection(
        [
            ("manufacturing", "Manufacturing"),
            ("services", "Services"),
            ("trading", "Trading"),
            ("financial", "Financial Services"),
            ("public", "Public Sector"),
            ("nonprofit", "Not-for-Profit"),
        ],
        string="Company Nature",
    )
    focal_person = fields.Char(string="Focal Person")
    focal_phone = fields.Char(string="Focal Phone")
    focal_email = fields.Char(string="Focal Email")
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company, required=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    amount_agreed = fields.Monetary(string="Amount Agreed", currency_field="currency_id")
    tentative_start_date = fields.Date(string="Tentative Start Date")
    tentative_end_date = fields.Date(string="Tentative End Date")
    udin = fields.Char(string="UDIN")
    udin_generated_on = fields.Date(string="UDIN Generated On", readonly=True)
    audit_type = fields.Selection(
        [
            ("statutory", "Statutory"),
            ("internal", "Internal"),
            ("special", "Special"),
        ],
        string="Audit Type",
        required=True,
        default="statutory",
        tracking=True,
    )
    audit_period_from = fields.Date(string="Audit Period From", tracking=True)
    audit_period_to = fields.Date(string="Audit Period To", tracking=True)
    financial_year_end = fields.Date(string="Financial Year End")
    previous_auditor = fields.Char(string="Previous Auditor")
    audit_tenure_years = fields.Integer(string="Audit Tenure (Years)")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("in_review", "In Review"),
            ("approved", "Approved"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # ISA sections
    entity_understanding = fields.Text(string="Entity & Environment (ISA 315)")
    analytics_notes = fields.Text(string="Analytics (ISA 520)")
    materiality_notes = fields.Text(string="Materiality (ISA 320)")
    controls_notes = fields.Text(string="Controls (ISA 315)")
    risk_strategy_notes = fields.Text(string="Risk Response (ISA 315/330)")
    fraud_risk_notes = fields.Text(string="Fraud Risk (ISA 240)")

    # Attachments
    organogram_attachment_ids = fields.Many2many(
        "ir.attachment",
        "audit_planning_organogram_attachment_rel",
        "planning_id",
        "attachment_id",
        string="Organogram Attachments",
        help="Organizational charts required for planning.",
    )
    engagement_letter_attachment_ids = fields.Many2many(
        "ir.attachment",
        "audit_planning_engagement_letter_rel",
        "planning_id",
        "attachment_id",
        string="Engagement Letters",
        help="Signed engagement letters.",
    )
    board_minutes_attachment_ids = fields.Many2many(
        "ir.attachment",
        "audit_planning_board_minutes_rel",
        "planning_id",
        "attachment_id",
        string="Board Minutes",
        help="Relevant board and governance minutes.",
    )
    process_flow_attachment_ids = fields.Many2many(
        "ir.attachment",
        "audit_planning_process_flow_rel",
        "planning_id",
        "attachment_id",
        string="Process Flows",
        help="Process flows and narratives.",
    )
    related_party_attachment_ids = fields.Many2many(
        "ir.attachment",
        "audit_planning_related_party_rel",
        "planning_id",
        "attachment_id",
        string="Related Parties",
        help="Related party listings and approvals.",
    )
    materiality_worksheet_attachment_ids = fields.Many2many(
        "ir.attachment",
        "audit_planning_materiality_rel",
        "planning_id",
        "attachment_id",
        string="Materiality Worksheets",
        help="Materiality calculations and thresholds.",
    )

    # Checklist
    checklist_ids = fields.One2many(
        "audit.planning.checklist",
        "planning_id",
        string="Checklist",
        copy=True,
    )
    checklist_completion = fields.Float(
        string="Checklist Completion",
        compute="_compute_progress",
        store=True,
    )

    # Progress fields
    entity_progress = fields.Float(string="Entity Progress", compute="_compute_progress", store=True)
    analytics_progress = fields.Float(string="Analytics Progress", compute="_compute_progress", store=True)
    materiality_progress = fields.Float(string="Materiality Progress", compute="_compute_progress", store=True)
    controls_progress = fields.Float(string="Controls Progress", compute="_compute_progress", store=True)
    risk_progress = fields.Float(string="Risk Progress", compute="_compute_progress", store=True)
    overall_progress = fields.Float(string="Overall Progress", compute="_compute_progress", store=True)

    # Approvals
    manager_id = fields.Many2one(
        "res.users",
        string="Manager",
        help="Assigned audit manager.",
    )
    partner_id = fields.Many2one(
        "res.users",
        string="Partner",
        help="Assigned audit partner.",
    )
    manager_signed = fields.Boolean(string="Manager Signed", tracking=True)
    partner_signed = fields.Boolean(string="Partner Signed", tracking=True)
    manager_signed_on = fields.Datetime(string="Manager Signed On")
    partner_signed_on = fields.Datetime(string="Partner Signed On")

    # Convenience counts
    attachment_count = fields.Integer(string="Attachment Count", compute="_compute_attachment_count")
    checklist_count = fields.Integer(string="Checklist Count", compute="_compute_checklist_count")

    @api.depends(
        "entity_understanding",
        "analytics_notes",
        "materiality_notes",
        "controls_notes",
        "risk_strategy_notes",
        "fraud_risk_notes",
        "checklist_ids.completed",
        "checklist_ids.is_mandatory",
    )
    def _compute_progress(self):
        for rec in self:
            rec.entity_progress = 100.0 if rec.entity_understanding else 0.0
            rec.analytics_progress = 100.0 if rec.analytics_notes else 0.0
            rec.materiality_progress = 100.0 if rec.materiality_notes else 0.0
            rec.controls_progress = 100.0 if rec.controls_notes else 0.0
            rec.risk_progress = 100.0 if (rec.risk_strategy_notes and rec.fraud_risk_notes) else 0.0

            mandatory = rec.checklist_ids.filtered("is_mandatory")
            completed = mandatory.filtered("completed")
            rec.checklist_completion = (len(completed) / len(mandatory) * 100.0) if mandatory else 0.0

            components = [
                rec.entity_progress,
                rec.analytics_progress,
                rec.materiality_progress,
                rec.controls_progress,
                rec.risk_progress,
                rec.checklist_completion,
            ]
            rec.overall_progress = sum(components) / len(components)

    @api.depends(
        "organogram_attachment_ids",
        "engagement_letter_attachment_ids",
        "board_minutes_attachment_ids",
        "process_flow_attachment_ids",
        "related_party_attachment_ids",
        "materiality_worksheet_attachment_ids",
    )
    def _compute_attachment_count(self):
        for rec in self:
            rec.attachment_count = sum(
                [
                    len(rec.organogram_attachment_ids),
                    len(rec.engagement_letter_attachment_ids),
                    len(rec.board_minutes_attachment_ids),
                    len(rec.process_flow_attachment_ids),
                    len(rec.related_party_attachment_ids),
                    len(rec.materiality_worksheet_attachment_ids),
                ]
            )

    @api.depends("checklist_ids")
    def _compute_checklist_count(self):
        for rec in self:
            rec.checklist_count = len(rec.checklist_ids)

    def action_view_checklist(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Checklist"),
            "res_model": "audit.planning.checklist",
            "view_mode": "tree,form",
            "domain": [("planning_id", "=", self.id)],
            "context": {"default_planning_id": self.id},
            "target": "current",
        }

    def action_view_attachments(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Attachments"),
            "res_model": "ir.attachment",
            "view_mode": "kanban,tree,form",
            "domain": [
                ("id", "in", (self.organogram_attachment_ids | self.engagement_letter_attachment_ids | self.board_minutes_attachment_ids | self.process_flow_attachment_ids | self.related_party_attachment_ids | self.materiality_worksheet_attachment_ids).ids)
            ],
            "target": "current",
        }

    def action_submit_review(self):
        for rec in self:
            if rec.state != "draft":
                continue
            if rec.checklist_completion < 100.0:
                raise ValidationError(_("Complete all mandatory checklist items before submitting for review."))
            rec.state = "in_review"
            rec.message_post(body=_("Submitted for review."))

    def action_manager_sign(self):
        for rec in self:
            if rec.state != "in_review":
                raise ValidationError(_("Record must be in review before manager sign-off."))
            rec.manager_signed = True
            rec.manager_signed_on = fields.Datetime.now()
            rec.message_post(body=_("Manager signed off."))

    def action_partner_sign(self):
        for rec in self:
            if not rec.manager_signed:
                raise ValidationError(_("Manager must sign before partner approval."))
            if rec.checklist_completion < 100.0:
                raise ValidationError(_("Complete all mandatory checklist items before partner approval."))
            rec.partner_signed = True
            rec.partner_signed_on = fields.Datetime.now()
            rec.state = "approved"
            rec.message_post(body=_("Partner approved and locked."))

    def action_mark_udin_generated(self):
        for rec in self:
            if not rec.udin:
                raise ValidationError(_("Set UDIN before marking generated."))
            rec.udin_generated_on = fields.Date.context_today(rec)
            rec.message_post(body=_("UDIN generated on %s") % rec.udin_generated_on)

    def write(self, vals):
        if any(rec.state == "approved" for rec in self):
            disallowed = set(vals.keys()) - {"message_follower_ids", "activity_ids"}
            if disallowed:
                raise ValidationError(_("Approved records are locked."))
        return super().write(vals)

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._populate_default_checklist()
        return record

    @api.onchange("udin")
    def _onchange_udin(self):
        if self.udin and not self.udin_generated_on:
            self.udin_generated_on = fields.Date.context_today(self)

    def _populate_default_checklist(self):
        template_items = self.env["audit.planning.checklist"].search_read(
            [("is_template", "=", True)],
            ["name", "isa_reference", "is_mandatory"],
        )
        if not template_items:
            return
        checklist_vals = [
            {
                "planning_id": self.id,
                "name": item["name"],
                "isa_reference": item.get("isa_reference"),
                "is_mandatory": item.get("is_mandatory", True),
                "completed": False,
                "is_template": False,
            }
            for item in template_items
        ]
        if checklist_vals:
            self.env["audit.planning.checklist"].create(checklist_vals)
