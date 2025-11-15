from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PlanningPhase(models.Model):
    _name = "qaco.planning.phase"
    _description = "Audit Planning Phase (ISA)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    # Basic fields
    name = fields.Char(
        default=lambda self: self.env["ir.sequence"].next_by_code("qaco.planning.phase") or _("New"),
        tracking=True,
        readonly=True,
        string="Planning Reference"
    )
    audit_id = fields.Many2one("qaco.audit", required=True, ondelete="cascade", tracking=True, string="Audit Reference")
    client_id = fields.Many2one(related='audit_id.client_id', string='Client', store=True, readonly=True)
    
    state = fields.Selection([
        ("draft", "Draft"),
        ("in_progress", "In Progress"),
        ("review", "Partner Review"),
        ("approved", "Approved"),
    ], default="draft", tracking=True, string="Status")

    # ISA 300: Overall Audit Strategy
    overall_strategy = fields.Text(
        string="Overall Audit Strategy (ISA 300)",
        tracking=True,
        help="Scope, timing, direction, and areas of emphasis for the audit"
    )
    scope = fields.Text(string="Scope and Components", tracking=True)
    audit_scope = fields.Text(string='Audit Scope & Objectives', tracking=True)
    
    use_of_experts = fields.Boolean(string="Planned Use of Experts (ISA 620)", tracking=True)
    rely_on_internal_audit = fields.Boolean(string="Rely on Internal Audit (ISA 610)", tracking=True)
    significant_components = fields.Text(string="Significant Areas / Components")
    key_risk_areas = fields.Text(string='Key Risk Areas Identified', tracking=True)
    
    audit_approach = fields.Selection([
        ("substantive", "Substantive Approach"),
        ("controls", "Controls Reliance"),
        ("combined", "Combined Approach"),
    ], string="Overall Audit Approach", default="combined", tracking=True)

    # ISA 320: Materiality
    materiality_basis = fields.Selection([
        ("profit_before_tax", "Profit Before Tax (5%)"),
        ("revenue", "Revenue (0.5-1%)"),
        ("assets", "Total Assets (1-2%)"),
        ("equity", "Equity (3-5%)"),
        ("custom", "Custom"),
    ], default="profit_before_tax", tracking=True, string="Materiality Benchmark")
    
    materiality_amount = fields.Monetary(
        string="Overall Materiality",
        tracking=True,
        currency_field="currency_id"
    )
    overall_materiality = fields.Monetary(
        string='Overall Materiality (Legacy)', 
        currency_field='currency_id', 
        tracking=True
    )
    
    performance_materiality = fields.Monetary(
        string="Performance Materiality (50-75%)",
        tracking=True,
        currency_field="currency_id",
        help="Set at 50-75% of overall materiality"
    )
    
    trivial_misstatement = fields.Monetary(
        string="Trivial Threshold (3-5%)",
        tracking=True,
        currency_field="currency_id",
        help="Typically 3-5% of overall materiality"
    )
    trivial_threshold = fields.Monetary(
        string='Trivial Threshold (Legacy)', 
        currency_field='currency_id', 
        tracking=True
    )
    
    materiality_notes = fields.Text(string="Materiality Rationale")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id
    )

    # ISA 210/220: Ethics & Acceptance
    engagement_letter_obtained = fields.Boolean(
        string="Engagement Letter Obtained (ISA 210)",
        tracking=True
    )
    engagement_letter_signed = fields.Boolean(
        string='Engagement Letter Signed (Legacy)', 
        tracking=True
    )
    engagement_letter_date = fields.Date(string="Engagement Letter Date")
    
    independence_confirmed = fields.Boolean(
        string="Independence Confirmed (IESBA Code)",
        tracking=True
    )
    independence_date = fields.Date(string="Independence Confirmation Date")
    
    ethical_requirements_met = fields.Boolean(
        string="Ethical Requirements Met (ISA 220)",
        tracking=True
    )
    
    previous_auditor_communication = fields.Boolean(
        string='Previous Auditor Communication', 
        tracking=True
    )

    # Client & Industry Information
    industry_sector_id = fields.Many2one(
        'planning.industry.sector', 
        string='Client Industry / Sector', 
        tracking=True
    )
    business_nature = fields.Text(string='Nature of Business', tracking=True)
    key_personnel = fields.Text(string='Key Client Personnel', tracking=True)
    
    # Engagement Information
    engagement_type = fields.Selection([
        ('statutory', 'Statutory Audit'),
        ('internal', 'Internal Audit'),
        ('special', 'Special Purpose Audit'),
        ('review', 'Review Engagement'),
        ('agreed_procedures', 'Agreed Upon Procedures'),
    ], string='Engagement Type', tracking=True)
    
    reporting_framework = fields.Selection([
        ('ifrs', 'IFRS'),
        ('ifrs_sme', 'IFRS for SMEs'),
        ('local_gaap', 'Local GAAP'),
        ('other', 'Other'),
    ], string='Reporting Framework', tracking=True)
    
    # Risk Assessment
    inherent_risk = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Inherent Risk', tracking=True)
    
    control_risk = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Control Risk', tracking=True)
    
    detection_risk = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Detection Risk', tracking=True)
    
    fraud_risk_assessment = fields.Text(string='Fraud Risk Assessment', tracking=True)
    
    # Planning Checklists (Legacy)
    understanding_entity_obtained = fields.Boolean(
        string='Understanding of Entity Obtained', 
        tracking=True
    )
    internal_controls_documented = fields.Boolean(
        string='Internal Controls Documented', 
        tracking=True
    )
    analytical_procedures_performed = fields.Boolean(
        string='Analytical Procedures Performed', 
        tracking=True
    )

    # Team
    partner_id = fields.Many2one("res.users", string="Engagement Partner", tracking=True)
    manager_id = fields.Many2one("res.users", string="Engagement Manager", tracking=True)
    team_ids = fields.Many2many("res.users", string="Engagement Team")

    # Timeline
    planning_start_date = fields.Date(string='Planning Start Date', tracking=True)
    planning_end_date = fields.Date(string='Planning End Date', tracking=True)
    fieldwork_start_date = fields.Date(string='Fieldwork Start Date', tracking=True)
    fieldwork_end_date = fields.Date(string='Fieldwork End Date', tracking=True)
    estimated_hours = fields.Float(string='Estimated Hours', tracking=True)

    # Related records
    risk_ids = fields.One2many("qaco.planning.risk", "planning_id", string="Identified Risks")
    checklist_ids = fields.One2many("qaco.planning.checklist", "planning_id", string="Planning Checklist")
    pbc_ids = fields.One2many("qaco.planning.pbc", "planning_id", string="PBC List")
    milestone_ids = fields.One2many("qaco.planning.milestone", "planning_id", string="Timeline")

    # Progress tracking
    checklist_total = fields.Integer(compute="_compute_progress", store=True)
    checklist_done = fields.Integer(compute="_compute_progress", store=True)
    progress = fields.Integer(string="Progress %", compute="_compute_progress", store=True)
    risk_count = fields.Integer(compute="_compute_counts", string="Risk Count")
    significant_risk_count = fields.Integer(compute="_compute_counts", string="Significant Risks")
    pbc_count = fields.Integer(compute="_compute_counts", string="PBC Items")
    pbc_received_count = fields.Integer(compute="_compute_counts", string="PBC Received")
    milestone_count = fields.Integer(compute="_compute_counts", string="Milestones")
    
    # Documents & Notes
    planning_notes = fields.Html(string='Planning Notes')
    planning_attachments = fields.Many2many(
        'ir.attachment', 
        'planning_phase_attachment_rel',
        'planning_id', 
        'attachment_id',
        string='Planning Documents'
    )
    
    # UI helpers
    color = fields.Integer(string="Color Index", default=0)
    active = fields.Boolean(default=True, tracking=True)

    @api.depends("checklist_ids.done")
    def _compute_progress(self):
        for rec in self:
            total = len(rec.checklist_ids)
            done = sum(1 for c in rec.checklist_ids if c.done)
            rec.checklist_total = total
            rec.checklist_done = done
            rec.progress = int((done / total) * 100) if total else 0

    @api.depends("risk_ids", "pbc_ids", "milestone_ids")
    def _compute_counts(self):
        for rec in self:
            rec.risk_count = len(rec.risk_ids)
            rec.significant_risk_count = sum(1 for r in rec.risk_ids if r.significant)
            rec.pbc_count = len(rec.pbc_ids)
            rec.pbc_received_count = sum(1 for p in rec.pbc_ids if p.received)
            rec.milestone_count = len(rec.milestone_ids)

    @api.constrains('planning_start_date', 'planning_end_date')
    def _check_planning_dates(self):
        """Validate planning dates"""
        for rec in self:
            if rec.planning_start_date and rec.planning_end_date:
                if rec.planning_end_date < rec.planning_start_date:
                    raise ValidationError(_("Planning end date must be after start date."))

    @api.constrains('fieldwork_start_date', 'fieldwork_end_date')
    def _check_fieldwork_dates(self):
        """Validate fieldwork dates"""
        for rec in self:
            if rec.fieldwork_start_date and rec.fieldwork_end_date:
                if rec.fieldwork_end_date < rec.fieldwork_start_date:
                    raise ValidationError(_("Fieldwork end date must be after start date."))

    @api.onchange('materiality_amount')
    def _onchange_materiality_amount(self):
        """Auto-calculate performance materiality and trivial threshold"""
        if self.materiality_amount:
            if not self.performance_materiality:
                # Default to 75% of overall materiality
                self.performance_materiality = self.materiality_amount * 0.75
            if not self.trivial_misstatement:
                # Default to 5% of overall materiality
                self.trivial_misstatement = self.materiality_amount * 0.05

    def action_start(self):
        self.write({'state': 'in_progress'})
    
    def action_start_planning(self):
        """Legacy method compatibility"""
        return self.action_start()

    def action_submit_review(self):
        for rec in self:
            if rec.progress < 70:
                raise ValidationError(_("Complete at least 70% of the checklist before submitting for review."))
            if not rec.materiality_amount and not rec.overall_materiality:
                raise ValidationError(_("Set overall materiality before submitting for review."))
            rec.state = "review"

    def action_approve(self):
        for rec in self:
            # Validation checks
            if any(r.significant and not r.response for r in rec.risk_ids):
                raise ValidationError(_("All significant risks must have a planned audit response."))
            if not rec.engagement_letter_obtained and not rec.engagement_letter_signed:
                raise ValidationError(_("Engagement letter must be obtained before approval."))
            if not rec.independence_confirmed:
                raise ValidationError(_("Independence must be confirmed before approval."))
            rec.state = "approved"

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    def action_view_risks(self):
        """Smart button: View all risks"""
        self.ensure_one()
        return {
            'name': _('Identified Risks'),
            'type': 'ir.actions.act_window',
            'res_model': 'qaco.planning.risk',
            'view_mode': 'tree,form',
            'domain': [('planning_id', '=', self.id)],
            'context': {
                'default_planning_id': self.id,
                'search_default_planning_id': self.id,
            },
        }

    def action_view_significant_risks(self):
        """Smart button: View significant risks only"""
        self.ensure_one()
        return {
            'name': _('Significant Risks'),
            'type': 'ir.actions.act_window',
            'res_model': 'qaco.planning.risk',
            'view_mode': 'tree,form',
            'domain': [('planning_id', '=', self.id), ('significant', '=', True)],
            'context': {
                'default_planning_id': self.id,
                'default_significant': True,
                'search_default_significant': 1,
            },
        }

    def action_view_pbc(self):
        """Smart button: View PBC items"""
        self.ensure_one()
        return {
            'name': _('PBC List'),
            'type': 'ir.actions.act_window',
            'res_model': 'qaco.planning.pbc',
            'view_mode': 'tree,form',
            'domain': [('planning_id', '=', self.id)],
            'context': {
                'default_planning_id': self.id,
                'search_default_planning_id': self.id,
            },
        }

    def action_view_milestones(self):
        """Smart button: View milestones"""
        self.ensure_one()
        return {
            'name': _('Timeline & Milestones'),
            'type': 'ir.actions.act_window',
            'res_model': 'qaco.planning.milestone',
            'view_mode': 'tree,form',
            'domain': [('planning_id', '=', self.id)],
            'context': {
                'default_planning_id': self.id,
                'search_default_planning_id': self.id,
            },
        }

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        # Auto-seed ISA-oriented checklist
        for rec in records:
            if not rec.checklist_ids:
                rec._create_default_checklist()
        return records

    def _create_default_checklist(self):
        """Create standard ISA-aligned checklist items"""
        self.ensure_one()
        
        checklist_items = [
            # ISA 210/220/IESBA - Acceptance & Ethics
            {
                "section": "acceptance",
                "description": "Obtain and review signed engagement letter with agreed terms",
                "isa_ref": "ISA 210.10",
                "sequence": 10,
            },
            {
                "section": "acceptance",
                "description": "Confirm independence of engagement team members",
                "isa_ref": "IESBA Code",
                "sequence": 20,
            },
            {
                "section": "acceptance",
                "description": "Document compliance with ethical requirements",
                "isa_ref": "ISA 220.11",
                "sequence": 30,
            },
            
            # ISA 300 - Planning
            {
                "section": "strategy",
                "description": "Define overall audit strategy including scope, timing, and direction",
                "isa_ref": "ISA 300.7",
                "sequence": 40,
            },
            {
                "section": "strategy",
                "description": "Determine nature and extent of resources needed for the engagement",
                "isa_ref": "ISA 300.8",
                "sequence": 50,
            },
            {
                "section": "strategy",
                "description": "Assign engagement team roles and plan supervision/review",
                "isa_ref": "ISA 300.8",
                "sequence": 60,
            },
            
            # ISA 315 - Risk Assessment
            {
                "section": "risk",
                "description": "Obtain understanding of entity, its environment, and applicable financial reporting framework",
                "isa_ref": "ISA 315.11",
                "sequence": 70,
            },
            {
                "section": "risk",
                "description": "Understand internal controls relevant to the audit",
                "isa_ref": "ISA 315.12",
                "sequence": 80,
            },
            {
                "section": "risk",
                "description": "Identify and assess risks of material misstatement at financial statement and assertion levels",
                "isa_ref": "ISA 315.25",
                "sequence": 90,
            },
            {
                "section": "risk",
                "description": "Determine significant risks requiring special audit consideration",
                "isa_ref": "ISA 315.27",
                "sequence": 100,
            },
            
            # ISA 320 - Materiality
            {
                "section": "materiality",
                "description": "Determine overall materiality for financial statements as a whole",
                "isa_ref": "ISA 320.10",
                "sequence": 110,
            },
            {
                "section": "materiality",
                "description": "Determine performance materiality",
                "isa_ref": "ISA 320.11",
                "sequence": 120,
            },
            {
                "section": "materiality",
                "description": "Set threshold for trivial misstatements",
                "isa_ref": "ISA 320.14",
                "sequence": 130,
            },
            
            # ISA 240 - Fraud
            {
                "section": "fraud",
                "description": "Conduct engagement team discussion on fraud risks",
                "isa_ref": "ISA 240.15",
                "sequence": 140,
            },
            {
                "section": "fraud",
                "description": "Make inquiries of management regarding fraud risk assessment",
                "isa_ref": "ISA 240.17",
                "sequence": 150,
            },
            {
                "section": "fraud",
                "description": "Identify and assess risks of material misstatement due to fraud",
                "isa_ref": "ISA 240.25",
                "sequence": 160,
            },
            {
                "section": "fraud",
                "description": "Presume risk of fraud in revenue recognition",
                "isa_ref": "ISA 240.26",
                "sequence": 170,
            },
        ]
        
        owner_id = self.partner_id.id or self.env.user.id
        self.checklist_ids = [(0, 0, {**item, "owner_id": owner_id}) for item in checklist_items]


class PlanningRisk(models.Model):
    _name = "qaco.planning.risk"
    _description = "Identified Risk (ISA 315/240)"
    _order = "risk_score desc, id desc"

    planning_id = fields.Many2one("qaco.planning.phase", required=True, ondelete="cascade")
    name = fields.Char(required=True, string="Risk Description")
    
    # Risk classification
    risk_type = fields.Selection([
        ("fraud", "Fraud Risk (ISA 240)"),
        ("significant", "Significant Risk (ISA 315)"),
        ("routine", "Routine Risk"),
    ], default="routine", required=True)
    
    assertion = fields.Selection([
        ("existence", "Existence / Occurrence"),
        ("completeness", "Completeness"),
        ("rights", "Rights & Obligations"),
        ("valuation", "Valuation / Allocation"),
        ("presentation", "Presentation & Disclosure"),
        ("cutoff", "Cut-off"),
        ("accuracy", "Accuracy"),
    ], string="Assertion Affected")
    
    account_area = fields.Selection([
        ("revenue", "Revenue"),
        ("inventory", "Inventory"),
        ("receivables", "Receivables"),
        ("payables", "Payables"),
        ("ppe", "Property, Plant & Equipment"),
        ("intangibles", "Intangibles"),
        ("investments", "Investments"),
        ("debt", "Debt & Financing"),
        ("equity", "Equity"),
        ("tax", "Taxation"),
        ("provisions", "Provisions"),
        ("other", "Other"),
    ], string="Account Area")
    
    # Risk assessment
    likelihood = fields.Selection([
        ("1", "Low"),
        ("2", "Medium"),
        ("3", "High"),
    ], default="2", required=True)
    
    impact = fields.Selection([
        ("1", "Low"),
        ("2", "Medium"),
        ("3", "High"),
    ], default="2", required=True)
    
    risk_score = fields.Integer(compute="_compute_score", store=True, string="Risk Rating")
    significant = fields.Boolean(string="Significant Risk")
    
    # Audit response
    response = fields.Selection([
        ("substantive", "Substantive Procedures Only"),
        ("controls", "Tests of Controls"),
        ("combined", "Combined Approach"),
    ], string="Planned Response")
    
    response_detail = fields.Text(string="Detailed Response")
    isa_ref = fields.Char(string="ISA Reference", help="e.g., ISA 315.27, ISA 240.26")
    notes = fields.Text()

    @api.depends("likelihood", "impact")
    def _compute_score(self):
        for rec in self:
            rec.risk_score = int(rec.likelihood or "1") * int(rec.impact or "1")

    @api.onchange('risk_score')
    def _onchange_risk_score(self):
        """Auto-flag as significant if score is high"""
        if self.risk_score >= 6 and not self.significant:
            return {
                'warning': {
                    'title': _('High Risk Score'),
                    'message': _('This risk has a high score (≥6). Consider marking it as Significant Risk.'),
                }
            }


class PlanningChecklist(models.Model):
    _name = "qaco.planning.checklist"
    _description = "Planning Checklist Item"
    _order = "sequence, id"

    planning_id = fields.Many2one("qaco.planning.phase", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    
    section = fields.Selection([
        ("acceptance", "Acceptance & Ethics"),
        ("strategy", "Overall Strategy"),
        ("materiality", "Materiality"),
        ("risk", "Risk Assessment"),
        ("fraud", "Fraud Considerations"),
    ], required=True, string="Section")
    
    description = fields.Text(required=True)
    isa_ref = fields.Char(string="ISA Reference")
    done = fields.Boolean(string="Completed")
    owner_id = fields.Many2one("res.users", string="Owner", default=lambda self: self.env.user)
    completion_date = fields.Date(string="Completion Date")
    notes = fields.Text()

    @api.onchange('done')
    def _onchange_done(self):
        """Auto-set completion date when marked as done"""
        if self.done and not self.completion_date:
            self.completion_date = fields.Date.today()
        elif not self.done:
            self.completion_date = False


class PlanningPBC(models.Model):
    _name = "qaco.planning.pbc"
    _description = "Prepared By Client (PBC) Request"
    _order = "due_date asc, id desc"

    planning_id = fields.Many2one("qaco.planning.phase", required=True, ondelete="cascade")
    name = fields.Char(string="PBC Item", required=True)
    description = fields.Text(string="Description")
    category = fields.Selection([
        ("financial", "Financial Statements"),
        ("tb", "Trial Balance / Ledgers"),
        ("reconciliation", "Reconciliations"),
        ("contracts", "Contracts / Agreements"),
        ("legal", "Legal Documents"),
        ("tax", "Tax Returns / Filings"),
        ("governance", "Governance / Minutes"),
        ("other", "Other"),
    ], string="Category", default="other")
    
    due_date = fields.Date(string="Due Date")
    received = fields.Boolean(string="Received")
    received_date = fields.Date(string="Received Date")
    client_contact = fields.Char(string="Client Contact")
    
    attachment_ids = fields.Many2many("ir.attachment", string="Attachments")
    notes = fields.Text()

    @api.onchange('received')
    def _onchange_received(self):
        """Auto-set received date when marked as received"""
        if self.received and not self.received_date:
            self.received_date = fields.Date.today()
        elif not self.received:
            self.received_date = False

    @api.constrains('due_date')
    def _check_overdue(self):
        """Check for overdue PBC items"""
        today = fields.Date.today()
        for rec in self:
            if rec.due_date and rec.due_date < today and not rec.received:
                # Just a soft check, no error raised
                pass


class PlanningMilestone(models.Model):
    _name = "qaco.planning.milestone"
    _description = "Planning Timeline Milestone"
    _order = "date asc, id desc"

    planning_id = fields.Many2one("qaco.planning.phase", required=True, ondelete="cascade")
    name = fields.Char(required=True, string="Milestone")
    date = fields.Date(required=True)
    
    category = fields.Selection([
        ("kickoff", "Kickoff Meeting"),
        ("pbc_due", "PBC Due"),
        ("planning_complete", "Planning Complete"),
        ("fieldwork_start", "Fieldwork Start"),
        ("fieldwork_end", "Fieldwork End"),
        ("review", "Partner Review"),
        ("report", "Report Issuance"),
    ], default="kickoff", string="Type")
    
    completed = fields.Boolean(string="Completed")
    completion_date = fields.Date(string="Actual Completion")
    owner_id = fields.Many2one("res.users", string="Responsible", default=lambda self: self.env.user)
    notes = fields.Text()

    @api.onchange('completed')
    def _onchange_completed(self):
        """Auto-set completion date when marked as completed"""
        if self.completed and not self.completion_date:
            self.completion_date = fields.Date.today()
        elif not self.completed:
            self.completion_date = False


class PlanningIndustrySector(models.Model):
    _name = "planning.industry.sector"
    _description = "Industry Sector"
    _order = "sequence, name"

    name = fields.Char(string="Sector Name", required=True)
    sequence = fields.Integer(string="Sequence", default=10)
    description = fields.Text(string="Description")
    active = fields.Boolean(default=True)
    
    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Industry sector name must be unique!')
    ]
