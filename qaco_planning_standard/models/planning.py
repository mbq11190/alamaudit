from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class PlanningPlan(models.Model):
    _name = "qaco.planning.plan"
    _description = "Audit Planning (ISA)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(default=lambda self: self.env["ir.sequence"].next_by_code("qaco.planning.plan") or _("New"), tracking=True)
    audit_id = fields.Many2one("qaco.audit", required=True, ondelete="cascade", tracking=True)
    state = fields.Selection([
        ("draft", "Draft"),
        ("in_progress", "In Progress"),
        ("review", "Partner Review"),
        ("approved", "Approved"),
    ], default="draft", tracking=True)

    # Strategy (ISA 300)
    overall_strategy = fields.Text(string="Overall Audit Strategy (ISA 300)", tracking=True)
    scope = fields.Text(string="Scope and Components", tracking=True)
    use_of_experts = fields.Boolean(string="Planned Use of Experts (ISA 620)")
    rely_on_internal_audit = fields.Boolean(string="Rely on Internal Audit (ISA 610)")
    significant_components = fields.Text(string="Significant Areas / Components")

    # Materiality (ISA 320)
    materiality_basis = fields.Selection([
        ("profit_before_tax", "Profit Before Tax"),
        ("revenue", "Revenue"),
        ("assets", "Total Assets"),
        ("equity", "Equity"),
        ("custom", "Custom"),
    ], default="profit_before_tax", tracking=True)
    materiality_amount = fields.Float(string="Overall Materiality", tracking=True)
    performance_materiality = fields.Float(string="Performance Materiality", tracking=True)
    trivial_misstatement = fields.Float(string="Trivial Threshold", tracking=True)
    materiality_notes = fields.Text(string="Materiality Rationale")

    # Ethics / acceptance (ISA 200/210/220 + IESBA)
    engagement_letter_obtained = fields.Boolean(string="Engagement Letter Obtained (ISA 210)")
    independence_confirmed = fields.Boolean(string="Independence Confirmed (Ethics)")

    # Links
    risk_ids = fields.One2many("qaco.planning.risk", "plan_id", string="Identified Risks")
    checklist_ids = fields.One2many("qaco.planning.checklist", "plan_id", string="Planning Checklist")
    pbc_ids = fields.One2many("qaco.planning.pbc", "plan_id", string="PBC List")
    milestone_ids = fields.One2many("qaco.planning.milestone", "plan_id", string="Milestones")

    # Team
    partner_id = fields.Many2one("res.users", string="Engagement Partner", tracking=True)
    manager_id = fields.Many2one("res.users", string="Engagement Manager", tracking=True)
    team_ids = fields.Many2many("res.users", string="Engagement Team")

    # Progress
    checklist_total = fields.Integer(compute="_compute_progress", store=True)
    checklist_done = fields.Integer(compute="_compute_progress", store=True)
    progress = fields.Integer(string="Progress %", compute="_compute_progress", store=True)
    color = fields.Integer(string="Color Index")

    @api.depends("checklist_ids.done")
    def _compute_progress(self):
        for rec in self:
            total = len(rec.checklist_ids)
            done = sum(1 for c in rec.checklist_ids if c.done)
            rec.checklist_total = total
            rec.checklist_done = done
            rec.progress = int((done / total) * 100) if total else 0

    def action_start(self):
        for rec in self:
            rec.state = "in_progress"

    def action_submit_review(self):
        for rec in self:
            if rec.progress < 70:
                raise ValidationError(_("Complete at least 70% of checklist before review."))
            rec.state = "review"

    def action_approve(self):
        for rec in self:
            if any(r.significant and not r.response for r in rec.risk_ids):
                raise ValidationError(_("All significant risks need an audit response."))
            rec.state = "approved"

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        # Auto-seed ISA-oriented checklist (paraphrased)
        for rec in records:
            if not rec.checklist_ids:
                items = [
                    # ISA 210/220/IESBA
                    {"section": "acceptance", "description": "Engagement terms agreed and documented", "isa_ref": "ISA 210", "owner_id": rec.partner_id.id or self.env.user.id},
                    {"section": "acceptance", "description": "Independence and ethical compliance confirmed", "isa_ref": "Ethics", "owner_id": rec.partner_id.id or self.env.user.id},
                    # ISA 300
                    {"section": "strategy", "description": "Define overall audit strategy incl. scope and timing", "isa_ref": "ISA 300"},
                    {"section": "strategy", "description": "Assign team roles and plan supervision/review", "isa_ref": "ISA 300"},
                    # ISA 315
                    {"section": "risk", "description": "Obtain understanding of entity and environment", "isa_ref": "ISA 315"},
                    {"section": "risk", "description": "Understand internal control relevant to audit", "isa_ref": "ISA 315"},
                    # ISA 320
                    {"section": "materiality", "description": "Determine overall and performance materiality", "isa_ref": "ISA 320"},
                    {"section": "materiality", "description": "Set trivial misstatement threshold", "isa_ref": "ISA 320"},
                    # ISA 240
                    {"section": "fraud", "description": "Team fraud brainstorming and documentation", "isa_ref": "ISA 240"},
                    {"section": "fraud", "description": "Identify and document fraud risk factors", "isa_ref": "ISA 240"},
                ]
                rec.checklist_ids = [(0, 0, i) for i in items]
        return records


class PlanningRisk(models.Model):
    _name = "qaco.planning.risk"
    _description = "Audit Risk (ISA 315)"
    _order = "risk_score desc, id desc"

    plan_id = fields.Many2one("qaco.planning.plan", required=True, ondelete="cascade")
    name = fields.Char(required=True)
    assertion = fields.Selection([
        ("existence", "Existence"),
        ("completeness", "Completeness"),
        ("rights", "Rights & Obligations"),
        ("valuation", "Valuation"),
        ("presentation", "Presentation & Disclosure"),
    ], string="Assertion")
    likelihood = fields.Selection([("1", "Low"), ("2", "Medium"), ("3", "High")], default="2")
    impact = fields.Selection([("1", "Low"), ("2", "Medium"), ("3", "High")], default="2")
    risk_score = fields.Integer(compute="_compute_score", store=True)
    significant = fields.Boolean(string="Significant Risk")
    response = fields.Selection([
        ("substantive", "Substantive Procedures"),
        ("controls", "Tests of Controls"),
        ("mixed", "Combined Approach"),
    ], string="Planned Response")
    isa_ref = fields.Char(string="Reference (e.g., ISA 315/240)")
    notes = fields.Text()

    @api.depends("likelihood", "impact")
    def _compute_score(self):
        for rec in self:
            rec.risk_score = int(rec.likelihood or "0") * int(rec.impact or "0")


class PlanningChecklist(models.Model):
    _name = "qaco.planning.checklist"
    _description = "Planning Checklist (ISA)"
    _order = "sequence, id"

    plan_id = fields.Many2one("qaco.planning.plan", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    section = fields.Selection([
        ("acceptance", "Acceptance & Ethics"),
        ("strategy", "Overall Strategy"),
        ("materiality", "Materiality"),
        ("risk", "Risk Assessment"),
        ("fraud", "Fraud Considerations"),
    ], required=True)
    description = fields.Char(required=True)
    isa_ref = fields.Char(string="ISA Ref")
    done = fields.Boolean()
    owner_id = fields.Many2one("res.users", default=lambda self: self.env.user)


class PlanningPBC(models.Model):
    _name = "qaco.planning.pbc"
    _description = "PBC Request"
    _order = "due_date asc, id desc"

    plan_id = fields.Many2one("qaco.planning.plan", required=True, ondelete="cascade")
    name = fields.Char(string="Item", required=True)
    due_date = fields.Date()
    received = fields.Boolean()
    partner_contact = fields.Char(string="Client Contact")
    attachment_ids = fields.Many2many("ir.attachment", string="Attachments")
    notes = fields.Text()


class PlanningMilestone(models.Model):
    _name = "qaco.planning.milestone"
    _description = "Planning Milestone"
    _order = "date asc, id desc"

    plan_id = fields.Many2one("qaco.planning.plan", required=True, ondelete="cascade")
    name = fields.Char(required=True)
    date = fields.Date(required=True)
    category = fields.Selection([
        ("kickoff", "Kickoff"),
        ("pbc_due", "PBC Due"),
        ("fieldwork_start", "Fieldwork Start"),
        ("review", "Review"),
        ("report", "Report"),
    ], default="kickoff")
    completed = fields.Boolean()
