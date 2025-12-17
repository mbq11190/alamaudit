# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AuditEngagement(models.Model):
    _name = "audit.engagement"
    _description = "Audit Planning Engagement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    # Engagement context
    name = fields.Char(string="Planning Reference", required=True, tracking=True)
    audit_id = fields.Many2one(
        "qaco.audit",
        string="Audit",
        required=True,
        tracking=True,
        ondelete="cascade",
        index=True,
        help="Source audit record that anchors this planning engagement.",
    )
    client_id = fields.Many2one(
        "res.partner",
        string="Client",
        related="audit_id.client_id",
        store=True,
        readonly=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
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
    amount_agreed = fields.Monetary(string="Amount Agreed", currency_field="currency_id")
    tentative_start_date = fields.Date(string="Tentative Start Date")
    tentative_end_date = fields.Date(string="Tentative End Date")

    # Compliance identifiers
    ntn = fields.Char(string="NTN")
    strn = fields.Char(string="STRN")
    audit_tenure_years = fields.Integer(string="Audit Tenure (Years)")
    previous_auditor = fields.Char(string="Previous Auditor")
    udin = fields.Char(string="UDIN")
    udin_generated_on = fields.Date(string="UDIN Generated On", readonly=True)

    # Organization touchpoints
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

    # Workflow + governance
    manager_id = fields.Many2one("res.users", string="Manager", help="Assigned audit manager")
    partner_id = fields.Many2one("res.users", string="Partner", help="Assigned audit partner")
    manager_signed = fields.Boolean(string="Manager Signed", tracking=True)
    manager_signed_on = fields.Datetime(string="Manager Signed On")
    partner_signed = fields.Boolean(string="Partner Signed", tracking=True)
    partner_signed_on = fields.Datetime(string="Partner Signed On")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("staff_prepared", "Staff Prepared"),
            ("manager_review", "Manager Review"),
            ("partner_approved", "Partner Approved"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # ISA-aligned narrative fields
    entity_understanding = fields.Text(string="Entity & Environment (ISA 315)")
    analytics_notes = fields.Text(string="Analytics (ISA 520)")
    materiality_notes = fields.Text(string="Materiality (ISA 320)")
    controls_notes = fields.Text(string="Controls (ISA 315)")
    risk_strategy_notes = fields.Text(string="Risk Response (ISA 315/330)")
    fraud_risk_notes = fields.Text(string="Fraud Risk (ISA 240)")

    # Attachments grouped for audit evidence
    organogram_attachment_ids = fields.Many2many(
        "ir.attachment",
        "audit_engagement_organogram_attachment_rel",
        "engagement_id",
        "attachment_id",
        string="Organogram Attachments",
        help="Organizational charts captured during planning.",
    )
    engagement_letter_attachment_ids = fields.Many2many(
        "ir.attachment",
        "audit_engagement_letter_rel",
        "engagement_id",
        "attachment_id",
        string="Engagement Letters",
        help="Signed engagement letters tied to ISA 210.",
    )
    board_minutes_attachment_ids = fields.Many2many(
        "ir.attachment",
        "audit_engagement_board_minutes_rel",
        "engagement_id",
        "attachment_id",
        string="Board Minutes",
        help="Governance minutes supporting entity understanding.",
    )
    process_flow_attachment_ids = fields.Many2many(
        "ir.attachment",
        "audit_engagement_process_flow_rel",
        "engagement_id",
        "attachment_id",
        string="Process Flows",
        help="Process narratives / flowcharts.",
    )
    related_party_attachment_ids = fields.Many2many(
        "ir.attachment",
        "audit_engagement_related_party_rel",
        "engagement_id",
        "attachment_id",
        string="Related Parties",
        help="Listings, approvals, and supporting evidence.",
    )
    materiality_worksheet_attachment_ids = fields.Many2many(
        "ir.attachment",
        "audit_engagement_materiality_rel",
        "engagement_id",
        "attachment_id",
        string="Materiality Worksheets",
        help="Benchmarks and performance materiality computations.",
    )

    # Linked planning artifacts
    fs_risk_ids = fields.One2many("audit.risk.fs", "engagement_id", string="FS-Level Risks")
    assertion_risk_ids = fields.One2many("audit.risk.assertion", "engagement_id", string="Assertion Risks")
    fraud_risk_ids = fields.One2many("audit.fraud.risk", "engagement_id", string="Fraud Risks")
    law_compliance_ids = fields.One2many("audit.law.compliance", "engagement_id", string="Laws & Regulations")
    control_assessment_ids = fields.One2many("audit.internal.control", "engagement_id", string="Control Evaluations")
    materiality_ids = fields.One2many("audit.materiality", "engagement_id", string="Materiality Workpapers")
    sampling_ids = fields.One2many("audit.sampling", "engagement_id", string="Sampling Plans")

    # Checklist scaffolding
    checklist_ids = fields.One2many(
        "audit.engagement.checklist",
        "engagement_id",
        string="Checklist",
        copy=True,
    )
    checklist_completion = fields.Float(string="Checklist Completion", compute="_compute_progress", store=True)

    # Progress trackers for dashboard widget
    entity_progress = fields.Float(string="Entity Progress", compute="_compute_progress", store=True)
    analytics_progress = fields.Float(string="Analytics Progress", compute="_compute_progress", store=True)
    materiality_progress = fields.Float(string="Materiality Progress", compute="_compute_progress", store=True)
    controls_progress = fields.Float(string="Controls Progress", compute="_compute_progress", store=True)
    risk_progress = fields.Float(string="Risk Progress", compute="_compute_progress", store=True)
    overall_progress = fields.Float(string="Overall Progress", compute="_compute_progress", store=True)
    romm_level = fields.Selection(
        [
            ("low", "Low"),
            ("moderate", "Moderate"),
            ("high", "High"),
        ],
        string="Aggregated RoMM",
        compute="_compute_romm_level",
        help="Summarized risk of material misstatement derived from FS and assertion matrices.",
    )

    # Convenience counters
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
        for record in self:
            record.entity_progress = 100.0 if record.entity_understanding else 0.0
            record.analytics_progress = 100.0 if record.analytics_notes else 0.0
            record.materiality_progress = 100.0 if record.materiality_notes else 0.0
            record.controls_progress = 100.0 if record.controls_notes else 0.0
            record.risk_progress = 100.0 if (record.risk_strategy_notes and record.fraud_risk_notes) else 0.0

            mandatory = record.checklist_ids.filtered("is_mandatory")
            completed = mandatory.filtered("completed")
            record.checklist_completion = (len(completed) / len(mandatory) * 100.0) if mandatory else 0.0

            components = [
                record.entity_progress,
                record.analytics_progress,
                record.materiality_progress,
                record.controls_progress,
                record.risk_progress,
                record.checklist_completion,
            ]
            record.overall_progress = sum(components) / len(components)

    @api.depends(
        "organogram_attachment_ids",
        "engagement_letter_attachment_ids",
        "board_minutes_attachment_ids",
        "process_flow_attachment_ids",
        "related_party_attachment_ids",
        "materiality_worksheet_attachment_ids",
    )
    def _compute_attachment_count(self):
        for record in self:
            record.attachment_count = sum(
                [
                    len(record.organogram_attachment_ids),
                    len(record.engagement_letter_attachment_ids),
                    len(record.board_minutes_attachment_ids),
                    len(record.process_flow_attachment_ids),
                    len(record.related_party_attachment_ids),
                    len(record.materiality_worksheet_attachment_ids),
                ]
            )

    @api.depends("checklist_ids")
    def _compute_checklist_count(self):
        for record in self:
            record.checklist_count = len(record.checklist_ids)

    @api.depends("fs_risk_ids.risk_level", "assertion_risk_ids.risk_level")
    def _compute_romm_level(self):
        for record in self:
            record.romm_level = record._derive_romm_level()

    def action_view_checklist(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Checklist"),
            "res_model": "audit.engagement.checklist",
            "view_mode": "tree,form",
            "domain": [("engagement_id", "=", self.id)],
            "context": {"default_engagement_id": self.id},
            "target": "current",
        }

    def action_view_attachments(self):
        self.ensure_one()
        attachment_ids = (
            self.organogram_attachment_ids
            | self.engagement_letter_attachment_ids
            | self.board_minutes_attachment_ids
            | self.process_flow_attachment_ids
            | self.related_party_attachment_ids
            | self.materiality_worksheet_attachment_ids
        ).ids
        return {
            "type": "ir.actions.act_window",
            "name": _("Attachments"),
            "res_model": "ir.attachment",
            "view_mode": "kanban,tree,form",
            "domain": [("id", "in", attachment_ids)],
            "target": "current",
        }

    def action_submit_review(self):
        for record in self:
            if record.state != "draft":
                continue
            if record.checklist_completion < 100.0:
                raise ValidationError(_("Complete all mandatory checklist items before staff submission."))
            record.state = "staff_prepared"
            record.message_post(body=_("Marked as staff prepared."))

    def action_manager_sign(self):
        for record in self:
            if record.state != "staff_prepared":
                raise ValidationError(_("Engagement must be staff prepared before manager review."))
            record.manager_signed = True
            record.manager_signed_on = fields.Datetime.now()
            record.state = "manager_review"
            record.message_post(body=_("Manager signed off."))

    def action_partner_sign(self):
        for record in self:
            if record.state != "manager_review":
                raise ValidationError(_("Engagement must be under manager review before partner approval."))
            if not record.manager_signed:
                raise ValidationError(_("Manager must sign before partner approval."))
            if record.checklist_completion < 100.0:
                raise ValidationError(_("Complete all mandatory checklist items before partner approval."))
            record.partner_signed = True
            record.partner_signed_on = fields.Datetime.now()
            record.state = "partner_approved"
            record.message_post(body=_("Partner approved and locked."))

    def action_mark_udin_generated(self):
        for record in self:
            if not record.udin:
                raise ValidationError(_("Set UDIN before marking generated."))
            record.udin_generated_on = fields.Date.context_today(record)
            record.message_post(body=_("UDIN generated on %s") % record.udin_generated_on)

    def write(self, vals):
        if any(rec.state == "partner_approved" for rec in self):
            disallowed = set(vals.keys()) - {"message_follower_ids", "activity_ids"}
            if disallowed:
                raise ValidationError(_("Partner approved engagements are locked."))
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
        template_items = self.env["audit.engagement.checklist"].search_read(
            [("is_template", "=", True)],
            ["name", "isa_reference", "is_mandatory"],
        )
        checklist_vals = [
            {
                "engagement_id": self.id,
                "name": item["name"],
                "isa_reference": item.get("isa_reference"),
                "is_mandatory": item.get("is_mandatory", True),
                "completed": False,
                "is_template": False,
            }
            for item in template_items
        ]
        if checklist_vals:
            self.env["audit.engagement.checklist"].create(checklist_vals)

    def _derive_romm_level(self):
        self.ensure_one()
        risk_levels = list(filter(None, self.fs_risk_ids.mapped("risk_level")))
        risk_levels += list(filter(None, self.assertion_risk_ids.mapped("risk_level")))
        if "high" in risk_levels:
            return "high"
        if "moderate" in risk_levels:
            return "moderate"
        return "low"
