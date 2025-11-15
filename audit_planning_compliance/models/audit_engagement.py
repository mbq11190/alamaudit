from __future__ import annotations

from datetime import date
from typing import List

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


ENTITY_CLASSES = [
    ("small", "Small Entity"),
    ("medium", "Medium Entity"),
    ("large", "Large Entity"),
    ("public_listed", "Public Listed"),
    ("public_unlisted", "Public Unlisted"),
    ("ngo", "NGO"),
    ("section_42", "Section 42 Company"),
    ("other", "Other"),
]


class AuditEngagement(models.Model):
    """Core engagement record covering ISA 300 planning requirements."""

    _name = "audit.engagement"
    _description = "Audit Engagement (Planning Phase)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(
        default=lambda self: self.env["ir.sequence"].next_by_code("audit.engagement") or _("New Engagement"),
        copy=False,
        tracking=True,
    )
    client_id = fields.Many2one("res.partner", string="Client", required=True, tracking=True)
    client_partner_id = fields.Many2one("res.partner", string="Client Audit Committee Chair", tracking=True)
    legal_form = fields.Selection(
        [
            ("company", "Company"),
            ("partnership", "Partnership"),
            ("ngo", "NGO"),
            ("section_42", "Section 42"),
            ("other", "Other"),
        ],
        default="company",
        required=True,
        tracking=True,
        help="(ISA 300 para 7) capture entity legal form to tailor planning approach.",
    )
    entity_classification = fields.Selection(
        ENTITY_CLASSES,
        string="Entity Classification",
        required=True,
        default="medium",
        tracking=True,
    )
    reporting_period_start = fields.Date(string="Period Start", required=True, tracking=True)
    reporting_period_end = fields.Date(string="Period End", required=True, tracking=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="Engagement Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    engagement_partner_id = fields.Many2one(
        "res.users",
        string="Engagement Partner",
        required=True,
        tracking=True,
        domain=[("groups_id", "in", ["audit_planning_compliance.group_audit_partner"])],
    )
    engagement_manager_id = fields.Many2one(
        "res.users",
        string="Engagement Manager",
        tracking=True,
        domain=[("groups_id", "in", ["audit_planning_compliance.group_audit_manager"])],
    )
    assigned_user_ids = fields.Many2many("res.users", string="Engagement Team")
    acceptance_state = fields.Selection(
        [
            ("draft", "Draft"),
            ("precheck", "Independence Pre-check"),
            ("awaiting_clearance", "Awaiting Ethics Clearance"),
            ("accepted", "Accepted"),
            ("rejected", "Rejected"),
        ],
        default="draft",
        tracking=True,
    )
    acceptance_rationale = fields.Text(
        string="Acceptance Rationale",
        help="Document independence, Companies Act / SECP compliance references (ISA 300 para 9; SECP Guide section 2).",
    )
    independence_confirmed = fields.Boolean(
        string="Independence Confirmed",
        tracking=True,
        help="ISA 300 para 7 requires confirmation before acceptance; ICAP ethics questionnaire.",
    )
    independence_questionnaire_result = fields.Selection(
        [
            ("clean", "No conflicts"),
            ("review", "Needs QCR review"),
            ("block", "Block engagement"),
        ],
        string="Independence Outcome",
        default="clean",
        tracking=True,
    )
    independence_notes = fields.Text(string="Independence Notes")
    qcr_contact_id = fields.Many2one("res.users", string="Ethics / QCR Contact")
    related_party_register = fields.Text(string="Related Parties Log")
    company_registration_no = fields.Char(string="Company Registration No")
    statutory_filing_obligations = fields.Text(
        string="Statutory Filing Obligations",
        help="SECP appointment/reporting obligations and Companies Act disclosures.",
    )
    secp_reporting_required = fields.Boolean(string="SECP Filing Required", default=True)
    audit_committee_required = fields.Boolean(
        string="Audit Committee Briefing",
        compute="_compute_committee_required",
        store=True,
    )
    engagement_letter_attachment_ids = fields.Many2many(
        "ir.attachment",
        "audit_eng_letter_rel",
        "engagement_id",
        "attachment_id",
        string="Engagement Letters",
    )
    materiality_ids = fields.One2many("audit.materiality", "engagement_id", string="Materiality Worksheets")
    risk_ids = fields.One2many("audit.risk.assessment", "engagement_id", string="Risk Register")
    pbc_request_ids = fields.One2many("audit.pbc.request", "engagement_id", string="PBC Requests")
    staff_plan_ids = fields.One2many("audit.staff.plan", "engagement_id", string="Staffing Plan")
    timeline_task_ids = fields.One2many("audit.timeline.task", "engagement_id", string="Timeline Tasks")
    evidence_log_ids = fields.One2many("audit.evidence.log", "res_id", domain=[("model_name", "=", "audit.engagement")])
    materiality_ready = fields.Boolean(string="Materiality Documented", default=False, tracking=True)
    risk_register_ready = fields.Boolean(string="Risk Register Complete", default=False, tracking=True)
    pbc_sent = fields.Boolean(string="PBC Requests Sent", default=False, tracking=True)
    staffing_signed_off = fields.Boolean(string="Staffing Signed Off", default=False, tracking=True)
    state = fields.Selection(
        [
            ("planning", "Planning"),
            ("fieldwork", "Fieldwork"),
            ("finalisation", "Finalisation"),
        ],
        default="planning",
        tracking=True,
    )
    audit_committee_briefing = fields.Html(string="Audit Committee Briefing Notes")

    materiality_count = fields.Integer(compute="_compute_counts")
    risk_count = fields.Integer(compute="_compute_counts")
    pbc_count = fields.Integer(compute="_compute_counts")
    timeline_count = fields.Integer(compute="_compute_counts")

    secp_export_payload = fields.Binary(string="SECP Export Package", readonly=True, attachment=True)

    @api.depends("entity_classification")
    def _compute_committee_required(self) -> None:
        for engagement in self:
            engagement.audit_committee_required = engagement.entity_classification in {"public_listed", "public_unlisted"}

    @api.depends("materiality_ids", "risk_ids", "pbc_request_ids", "timeline_task_ids")
    def _compute_counts(self) -> None:
        for engagement in self:
            engagement.materiality_count = len(engagement.materiality_ids)
            engagement.risk_count = len(engagement.risk_ids)
            engagement.pbc_count = len(engagement.pbc_request_ids)
            engagement.timeline_count = len(engagement.timeline_task_ids)

    def action_accept_engagement(self) -> None:
        """Mark engagement as accepted per ISA 300 para 7 requirements."""

        for engagement in self:
            if not engagement.independence_confirmed or engagement.independence_questionnaire_result == "block":
                raise ValidationError(
                    _(
                        "Independence questionnaire must be clean before acceptance (ISA 300 para 7 / ICAP ethics guidance)."
                    )
                )
            if not engagement.engagement_letter_attachment_ids:
                raise ValidationError(_("Upload an engagement letter before acceptance (SECP Guide section 2)."))
            engagement.acceptance_state = "accepted"
            engagement._bootstrap_planning_pack()
            self.env["audit.evidence.log"].log_event(
                name=_("Engagement accepted"),
                model_name=engagement._name,
                res_id=engagement.id,
                action_type="state",
                note=engagement.acceptance_rationale or _("Acceptance rationale captured."),
                standard_reference="ISA 300 para 7; SECP Guide section 2",
            )

    def _bootstrap_planning_pack(self) -> None:
        """Create default planning artefacts once engagement is accepted."""

        for engagement in self:
            if engagement.materiality_ids:
                continue
            config = self.env["audit.materiality.config"].search(
                ["|", ("entity_classification", "=", engagement.entity_classification), ("entity_classification", "=", "other")],
                limit=1,
            )
            self.env["audit.materiality"].create(
                {
                    "engagement_id": engagement.id,
                    "basis": config.default_basis if config else "pbt",
                    "base_source_type": "manual",
                    "base_value": 0.0,
                    "applied_percentage": config.default_pct_pbt if config else 5.0,
                    "justification_text": _(
                        "Default planning pack generated (ISA 320 para 10). Update base figures from TB snapshot."
                    ),
                }
            )
            engagement._generate_default_pbc_items()
            engagement._generate_default_timeline()

    def _generate_default_pbc_items(self) -> None:
        template_model = self.env["audit.pbc.template"]
        for engagement in self:
            templates = template_model.search([("entity_classification", "=", engagement.entity_classification)])
            if not templates:
                templates = template_model.search([("entity_classification", "=", "other")])
            for template in templates:
                self.env["audit.pbc.request"].create(
                    {
                        "engagement_id": engagement.id,
                        "name": template.name,
                        "description": template.description,
                        "category": template.category,
                        "delivery_status": "not_requested",
                        "requested_date": fields.Date.context_today(self),
                        "due_date": engagement.reporting_period_end,
                        "responsible_client_contact": engagement.client_partner_id.id,
                    }
                )

    def _generate_default_timeline(self) -> None:
        for engagement in self:
            start = engagement.reporting_period_start or fields.Date.context_today(self)
            milestones = [
                ("Planning Memorandum", start, start),
                ("Risk Workshops", start, start),
                ("Audit Committee Briefing", engagement.reporting_period_end, engagement.reporting_period_end),
            ]
            for name, start_date, end_date in milestones:
                self.env["audit.timeline.task"].create(
                    {
                        "engagement_id": engagement.id,
                        "name": name,
                        "start_date": start_date,
                        "end_date": end_date,
                        "percent_complete": 0.0,
                        "assigned_to": engagement.engagement_manager_id.id or engagement.engagement_partner_id.id,
                    }
                )

    def action_open_materiality(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Materiality"),
            "res_model": "audit.materiality",
            "view_mode": "tree,form",
            "domain": [("engagement_id", "=", self.id)],
            "context": {
                "default_engagement_id": self.id,
            },
        }

    def action_open_risks(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Risk Register"),
            "res_model": "audit.risk.assessment",
            "view_mode": "kanban,tree,form",
            "domain": [("engagement_id", "=", self.id)],
            "context": {"default_engagement_id": self.id},
        }

    def action_open_pbc(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("PBC Requests"),
            "res_model": "audit.pbc.request",
            "view_mode": "kanban,tree,form",
            "domain": [("engagement_id", "=", self.id)],
            "context": {"default_engagement_id": self.id},
        }

    def action_open_staff_plan(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Staffing Plan"),
            "res_model": "audit.staff.plan",
            "view_mode": "tree,form",
            "domain": [("engagement_id", "=", self.id)],
            "context": {"default_engagement_id": self.id},
        }

    def action_open_timeline(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Timeline"),
            "res_model": "audit.timeline.task",
            "view_mode": "gantt,calendar,tree,form",
            "domain": [("engagement_id", "=", self.id)],
            "context": {"default_engagement_id": self.id},
        }

    def action_export_planning_memorandum(self):
        self.ensure_one()
        return self.env.ref("audit_planning_compliance.report_planning_memorandum").report_action(self)

    def action_export_secp_package(self):
        self.ensure_one()
        payload = {
            "engagement": self.name,
            "client": self.client_id.display_name,
            "entity_class": self.entity_classification,
            "materiality": [
                {
                    "basis": m.basis,
                    "overall": m.overall_materiality,
                    "performance": m.performance_materiality,
                }
                for m in self.materiality_ids
            ],
            "risks": [
                {
                    "name": r.name,
                    "rating": r.risk_rating,
                    "procedures": r.planned_substantive_procedures,
                }
                for r in self.risk_ids if r.overall_risk in ("high", "very_high")
            ],
        }
        attachment = self.env["ir.attachment"].create(
            {
                "name": f"SECP-package-{self.name}.json",
                "datas": self.env["ir.binary"]._encode_base64(str(payload).encode()),
                "res_model": self._name,
                "res_id": self.id,
            }
        )
        self.secp_export_payload = attachment.datas
        self.env["audit.evidence.log"].log_event(
            name=_("SECP export"),
            model_name=self._name,
            res_id=self.id,
            action_type="export",
            note=_("SECP / PSX export generated for regulator submission."),
            standard_reference="SECP Guide section 5; PSX ToR section 8",
        )
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}?download=true",
            "target": "self",
        }

    def action_mark_ready_for_fieldwork(self):
        for engagement in self:
            if not all([engagement.materiality_ready, engagement.risk_register_ready, engagement.pbc_sent, engagement.staffing_signed_off]):
                raise ValidationError(
                    _(
                        "Materiality, risk register, PBC issuance and staffing sign-off must be complete before fieldwork (ISA 300 para 13; PSX ToR)."
                    )
                )
            engagement.state = "fieldwork"
            self.env["audit.evidence.log"].log_event(
                name=_("Planning complete"),
                model_name=engagement._name,
                res_id=engagement.id,
                action_type="state",
                note=_("Planning phase sign-offs completed."),
                standard_reference="ISA 300 para 13",
            )

    def action_trigger_independence_escalation(self):
        for engagement in self:
            if engagement.independence_questionnaire_result != "review":
                continue
            if not engagement.qcr_contact_id:
                raise ValidationError(_("Assign a QCR / ethics contact before escalation."))
            engagement.acceptance_state = "awaiting_clearance"
            self.env["audit.evidence.log"].log_event(
                name=_("Independence escalation"),
                model_name=self._name,
                res_id=engagement.id,
                action_type="state",
                note=_("Routed to QCR contact per ICAP ethics guidance."),
                standard_reference="ICAP ethics guidance section 2",
            )
