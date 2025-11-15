import base64
from datetime import timedelta

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
    client_partner_id = fields.Many2one("res.partner", string="Audit Committee Chair")
    reporting_period_start = fields.Date(string="Period Start", tracking=True)
    reporting_period_end = fields.Date(string="Period End", tracking=True)
    legal_form = fields.Selection(
        [
            ("company", "Company"),
            ("partnership", "Partnership"),
            ("ngo", "NGO"),
            ("section_42", "Section 42 Company"),
            ("other", "Other"),
        ],
        default="company",
        tracking=True,
    )
    entity_classification = fields.Selection(ENTITY_CLASSES, string="Entity Classification", default="medium", tracking=True)
    
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
    acceptance_rationale = fields.Text(string="Acceptance Rationale")
    independence_questionnaire_result = fields.Selection(
        [
            ("clean", "No conflicts"),
            ("review", "Needs QCR review"),
            ("block", "Block engagement"),
        ],
        default="clean",
        tracking=True,
    )
    independence_notes = fields.Text(string="Independence Notes")
    qcr_contact_id = fields.Many2one("res.users", string="Ethics / QCR Contact")
    related_party_register = fields.Text(string="Related Parties Log")
    company_registration_no = fields.Char(string="Company Registration No")
    statutory_filing_obligations = fields.Text(string="Statutory Filing Obligations")
    audit_committee_required = fields.Boolean(compute="_compute_committee_required", store=True)
    secp_reporting_required = fields.Boolean(default=True)
    
    state = fields.Selection([
        ("draft", "Draft"),
        ("in_progress", "In Progress"),
        ("review", "Partner Review"),
        ("approved", "Approved"),
        ("fieldwork", "Fieldwork"),
        ("finalisation", "Finalisation"),
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
    materiality_ids = fields.One2many("qaco.planning.materiality", "planning_id", string="Materiality Worksheets")
    risk_ids = fields.One2many("qaco.planning.risk", "planning_id", string="Identified Risks")
    checklist_ids = fields.One2many("qaco.planning.checklist", "planning_id", string="Planning Checklist")
    pbc_ids = fields.One2many("qaco.planning.pbc", "planning_id", string="PBC List")
    milestone_ids = fields.One2many("qaco.planning.milestone", "planning_id", string="Timeline")
    evidence_log_ids = fields.One2many(
        "qaco.planning.evidence",
        "res_id",
        string="Evidence Log",
        domain=[("model_name", "=", "qaco.planning.phase")],
    )

    # Progress tracking
    checklist_total = fields.Integer(compute="_compute_progress", store=True)
    checklist_done = fields.Integer(compute="_compute_progress", store=True)
    progress = fields.Integer(string="Progress %", compute="_compute_progress", store=True)
    materiality_ready = fields.Boolean(string="Materiality Documented", default=False, tracking=True)
    risk_register_ready = fields.Boolean(string="Risk Register Complete", default=False, tracking=True)
    pbc_sent = fields.Boolean(string="PBC Requests Sent", default=False, tracking=True)
    staffing_signed_off = fields.Boolean(string="Staffing Signed Off", default=False, tracking=True)
    materiality_count = fields.Integer(compute="_compute_counts", string="Materiality")
    risk_count = fields.Integer(compute="_compute_counts", string="Risk Count")
    significant_risk_count = fields.Integer(compute="_compute_counts", string="Significant Risks")
    pbc_count = fields.Integer(compute="_compute_counts", string="PBC Items")
    pbc_received_count = fields.Integer(compute="_compute_counts", string="PBC Received")
    milestone_count = fields.Integer(compute="_compute_counts", string="Milestones")
    timeline_count = fields.Integer(compute="_compute_counts", string="Timeline Tasks")
    
    # Documents & Notes
    planning_notes = fields.Html(string='Planning Notes')
    planning_attachments = fields.Many2many(
        'ir.attachment', 
        'planning_phase_attachment_rel',
        'planning_id', 
        'attachment_id',
        string='Planning Documents'
    )
    audit_committee_briefing = fields.Html(string="Audit Committee Briefing Notes")
    secp_export_payload = fields.Binary(string="SECP Export Package", attachment=True, readonly=True)
    
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

    @api.depends("entity_classification")
    def _compute_committee_required(self):
        for rec in self:
            rec.audit_committee_required = rec.entity_classification in {"public_listed", "public_unlisted"}

    @api.depends("materiality_ids", "risk_ids", "pbc_ids", "milestone_ids")
    def _compute_counts(self):
        for rec in self:
            rec.materiality_count = len(rec.materiality_ids)
            rec.risk_count = len(rec.risk_ids)
            rec.significant_risk_count = sum(1 for r in rec.risk_ids if r.significant)
            rec.pbc_count = len(rec.pbc_ids)
            rec.pbc_received_count = sum(1 for p in rec.pbc_ids if p.received)
            rec.milestone_count = len(rec.milestone_ids)
            rec.timeline_count = rec.milestone_count

    def _log_evidence(self, name, action_type, note, standard_reference, **kwargs):
        self.ensure_one()
        self.env["qaco.planning.evidence"].log_event(
            name=name,
            model_name=self._name,
            res_id=self.id,
            action_type=action_type,
            note=note,
            standard_reference=standard_reference,
            **kwargs,
        )

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

    def action_view_materiality(self):
        self.ensure_one()
        return {
            'name': _('Materiality Worksheets'),
            'type': 'ir.actions.act_window',
            'res_model': 'qaco.planning.materiality',
            'view_mode': 'tree,form',
            'domain': [('planning_id', '=', self.id)],
            'context': {'default_planning_id': self.id},
        }

    def action_accept_planning(self):
        for rec in self:
            if not rec.independence_confirmed or rec.independence_questionnaire_result == 'block':
                raise ValidationError(_("Independence questionnaire must be clean before acceptance (ISA 300 para 7)."))
            if not rec.engagement_letter_obtained:
                raise ValidationError(_("Mark the engagement letter as obtained before acceptance."))
            rec.acceptance_state = 'accepted'
            rec._bootstrap_planning_pack()
            rec._log_evidence(
                name=_('Engagement accepted'),
                action_type='state',
                note=rec.acceptance_rationale or _('Acceptance rationale captured.'),
                standard_reference='ISA 300 para 7; SECP Guide section 2',
            )

    def _bootstrap_planning_pack(self):
        for rec in self:
            if rec.materiality_ids:
                continue
            config = self.env['qaco.planning.materiality.config'].search(
                ['|', ('entity_classification', '=', rec.entity_classification), ('entity_classification', '=', 'other')],
                limit=1,
            )
            self.env['qaco.planning.materiality'].create(
                {
                    'planning_id': rec.id,
                    'basis': config.default_basis if config else 'pbt',
                    'base_source_type': 'manual',
                    'base_value': 0.0,
                    'applied_percentage': config.default_pct_pbt if config else 5.0,
                    'justification_text': _('Default planning pack generated (ISA 320 para 10). Update base figures from TB snapshot.'),
                }
            )
            rec._generate_default_pbc_items()
            rec._generate_default_milestones()

    def _generate_default_pbc_items(self):
        template_model = self.env['qaco.planning.pbc.template']
        for rec in self:
            templates = template_model.search([('entity_classification', '=', rec.entity_classification)])
            if not templates:
                templates = template_model.search([('entity_classification', '=', 'other')])
            for template in templates:
                self.env['qaco.planning.pbc'].create(
                    {
                        'planning_id': rec.id,
                        'name': template.name,
                        'description': template.description,
                        'category': template.category,
                        'delivery_status': 'not_requested',
                        'requested_date': fields.Date.context_today(self),
                        'due_date': rec.reporting_period_end,
                        'client_contact': rec.client_partner_id.name,
                        'client_contact_id': rec.client_partner_id.id,
                    }
                )

    def _generate_default_milestones(self):
        for rec in self:
            start = rec.reporting_period_start or fields.Date.context_today(self)
            milestones = [
                ('Planning Memorandum', start),
                ('Risk Workshops', start),
                ('Audit Committee Briefing', rec.reporting_period_end or start),
            ]
            for name, milestone_date in milestones:
                self.env['qaco.planning.milestone'].create(
                    {
                        'planning_id': rec.id,
                        'name': name,
                        'date': milestone_date,
                        'owner_id': rec.manager_id.id or rec.partner_id.id,
                    }
                )

    def action_export_planning_memorandum(self):
        self.ensure_one()
        report = self.env.ref('qaco_planning_phase.report_planning_memorandum', raise_if_not_found=False)
        if not report:
            raise ValidationError(_('Planning memorandum report is not configured.'))
        return report.report_action(self)

    def action_export_secp_package(self):
        self.ensure_one()
        payload = {
            'planning': self.name,
            'client': self.client_id.display_name,
            'entity_class': self.entity_classification,
            'materiality': [
                {
                    'basis': m.basis,
                    'overall': m.overall_materiality,
                    'performance': m.performance_materiality,
                }
                for m in self.materiality_ids
            ],
            'risks': [
                {
                    'name': r.name,
                    'rating': r.risk_score,
                    'response': r.response_detail or r.response,
                }
                for r in self.risk_ids if r.significant
            ],
        }
        attachment = self.env['ir.attachment'].create(
            {
                'name': f'SECP-package-{self.name}.json',
                'datas': base64.b64encode(str(payload).encode()).decode(),
                'res_model': self._name,
                'res_id': self.id,
            }
        )
        self.secp_export_payload = attachment.datas
        self._log_evidence(
            name=_('SECP export'),
            action_type='export',
            note=_('SECP / PSX export generated for regulator submission.'),
            standard_reference='SECP Guide section 5; PSX ToR section 8',
        )
        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content/{attachment.id}?download=true",
            'target': 'self',
        }

    def action_mark_ready_for_fieldwork(self):
        for rec in self:
            if not all([rec.materiality_ready, rec.risk_register_ready, rec.pbc_sent, rec.staffing_signed_off]):
                raise ValidationError(_("Materiality, risk register, PBC issuance and staffing sign-off must be complete before fieldwork."))
            rec.state = 'fieldwork'
            rec._log_evidence(
                name=_('Planning complete'),
                action_type='state',
                note=_('Planning phase sign-offs completed.'),
                standard_reference='ISA 300 para 13',
            )

    def action_trigger_independence_escalation(self):
        for rec in self:
            if rec.independence_questionnaire_result != 'review':
                continue
            if not rec.qcr_contact_id:
                raise ValidationError(_("Assign a QCR / ethics contact before escalation."))
            rec.acceptance_state = 'awaiting_clearance'
            rec._log_evidence(
                name=_('Independence escalation'),
                action_type='state',
                note=_('Routed to QCR contact per ICAP ethics guidance.'),
                standard_reference='ICAP ethics guidance section 2',
            )

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
    business_area = fields.Selection([
        ("revenue", "Revenue"),
        ("inventory", "Inventory"),
        ("receivables", "Receivables"),
        ("payables", "Payables"),
        ("cash", "Cash & Equivalents"),
        ("estimates", "Accounting Estimates"),
        ("disclosures", "Disclosures"),
        ("other", "Other"),
    ], string="Business Area")
    
    # Risk classification
    risk_type = fields.Selection([
        ("fraud", "Fraud Risk (ISA 240)"),
        ("significant", "Significant Risk (ISA 315)"),
        ("routine", "Routine Risk"),
    ], default="routine", required=True)
    
    assertion = fields.Selection([
        ("occurrence", "Occurrence"),
        ("existence", "Existence"),
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
    inherent_risk_level = fields.Integer(string="Inherent Risk (1-5)", default=3)
    control_risk_level = fields.Integer(string="Control Risk (1-5)", default=3)
    detection_risk_level = fields.Integer(string="Detection Risk", compute="_compute_score", store=True)
    overall_risk = fields.Selection([
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("very_high", "Very High"),
    ], compute="_compute_score", store=True)
    risk_score = fields.Integer(compute="_compute_score", store=True, string="Risk Rating")
    significant = fields.Boolean(string="Significant Risk")
    
    # Audit response
    response = fields.Selection([
        ("substantive", "Substantive Procedures Only"),
        ("controls", "Tests of Controls"),
        ("combined", "Combined Approach"),
    ], string="Planned Response")
    response_detail = fields.Text(string="Detailed Response")
    planned_substantive_procedures = fields.Text(string="Planned Substantive Procedures")
    planned_control_tests = fields.Text(string="Planned Control Tests")
    risk_triggers = fields.Text(string="Risk Triggers")
    risk_narrative = fields.Text(string="Risk Narrative")
    isa_ref = fields.Char(string="ISA Reference", help="e.g., ISA 315.27, ISA 240.26")
    notes = fields.Text()
    sign_off_user_id = fields.Many2one("res.users", string="Reviewer")
    sign_off_date = fields.Date()

    @api.depends("likelihood", "impact", "inherent_risk_level", "control_risk_level")
    def _compute_score(self):
        for rec in self:
            inherent = rec.inherent_risk_level or int(rec.likelihood or "1")
            control = rec.control_risk_level or int(rec.impact or "1")
            rec.detection_risk_level = max(1, 6 - min(inherent, control))
            rec.risk_score = inherent * control * rec.detection_risk_level
            if rec.risk_score >= 60:
                rec.overall_risk = "very_high"
            elif rec.risk_score >= 36:
                rec.overall_risk = "high"
            elif rec.risk_score >= 18:
                rec.overall_risk = "medium"
            else:
                rec.overall_risk = "low"

    @api.onchange('risk_score')
    def _onchange_risk_score(self):
        """Auto-flag as significant if score is high"""
        if self.risk_score >= 36 and not self.significant:
            return {
                'warning': {
                    'title': _('High Risk Score'),
                    'message': _('This risk has a high score (≥6). Consider marking it as Significant Risk.'),
                }
            }

    @api.constrains('overall_risk', 'risk_triggers', 'planned_substantive_procedures')
    def _check_high_risk_documentation(self):
        for rec in self:
            if rec.overall_risk in ('high', 'very_high'):
                if not rec.risk_triggers or not rec.planned_substantive_procedures:
                    raise ValidationError(_("High/very high risks require triggers and planned procedures (ISA 315 para 32)."))

    def action_sign_off(self):
        self.ensure_one()
        if self.env.user not in (self.planning_id.partner_id, self.planning_id.manager_id):
            raise ValidationError(_('Only the engagement partner or manager can sign-off risks.'))
        self.sign_off_user_id = self.env.user
        self.sign_off_date = fields.Date.context_today(self)
        high_risks = self.planning_id.risk_ids.filtered(lambda r: r.overall_risk in ('high', 'very_high'))
        self.planning_id.risk_register_ready = bool(high_risks)
        self.planning_id._log_evidence(
            name=_('Risk sign-off'),
            action_type='approval',
            note=_('Risk reviewed and response deemed adequate.'),
            standard_reference='ISA 315 para 32',
        )


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
    requested_date = fields.Date(string="Requested Date")
    delivery_status = fields.Selection([
        ("not_requested", "Not Requested"),
        ("requested", "Requested"),
        ("received", "Received"),
        ("incomplete", "Incomplete"),
    ], default="not_requested", tracking=True)
    received = fields.Boolean(string="Received")
    received_date = fields.Date(string="Received Date")
    client_contact = fields.Char(string="Client Contact (Legacy)")
    client_contact_id = fields.Many2one("res.partner", string="Client Contact")
    
    attachment_ids = fields.Many2many("ir.attachment", string="Attachments")
    notes = fields.Text()
    follow_up_log = fields.Html(string="Follow-up Log")
    reminder_count = fields.Integer(default=0)
    shared_with_portal = fields.Boolean(string="Client Portal Access", default=False)
    escalation_level = fields.Selection([
        ("none", "None"),
        ("first", "Manager"),
        ("second", "Partner"),
    ], default="none")
    reminder_log_ids = fields.One2many("qaco.planning.pbc.reminder", "request_id", string="Reminder History")

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

    def action_request(self):
        for rec in self:
            rec.delivery_status = 'requested'
            rec.requested_date = fields.Date.context_today(self)
            rec.planning_id.pbc_sent = True
            rec.planning_id._log_evidence(
                name=_('PBC issued'),
                action_type='state',
                note=rec.description or rec.name,
                standard_reference='ISA 300 para 13; ICAP APM section 7',
            )

    def action_mark_received(self):
        for rec in self:
            rec.delivery_status = 'received'
            rec.received = True
            rec.received_date = fields.Date.context_today(self)
            if not rec.attachment_ids:
                raise ValidationError(_('Attach evidence before marking received.'))
            rec.planning_id._log_evidence(
                name=_('PBC received'),
                action_type='update',
                note=_('Evidence attached for PBC.'),
                standard_reference='ISA 300 para 11',
            )

    def action_send_reminder(self, escalation=False):
        template = self.env.ref('qaco_planning_phase.email_template_pbc_reminder', raise_if_not_found=False)
        for rec in self:
            if template:
                template.send_mail(rec.id, force_send=True)
            rec.reminder_count += 1
            if escalation:
                rec.escalation_level = 'second'
            elif rec.reminder_count >= 2:
                rec.escalation_level = 'first'
            self.env['qaco.planning.pbc.reminder'].create(
                {
                    'request_id': rec.id,
                    'reminder_type': 'email',
                    'note': _('Automated reminder dispatched.'),
                }
            )
            rec.planning_id._log_evidence(
                name=_('PBC reminder'),
                action_type='reminder',
                note=_('Reminder sent to client contact.'),
                standard_reference='ICAP APM section 7; SECP Guide section 4',
            )

    @api.model
    def cron_escalate_overdue(self):
        escalation_days = int(self.env['ir.config_parameter'].sudo().get_param('qaco_planning.pbc_escalation_days', 3))
        threshold = fields.Date.to_string(fields.Date.context_today(self) - timedelta(days=escalation_days))
        overdue = self.search([
            ('delivery_status', '!=', 'received'),
            ('due_date', '<=', threshold),
        ])
        overdue.action_send_reminder(escalation=True)


class PlanningPbcTemplate(models.Model):
    _name = "qaco.planning.pbc.template"
    _description = "Default PBC Template"

    name = fields.Char(required=True)
    entity_classification = fields.Selection(ENTITY_CLASSES, required=True)
    description = fields.Text()
    category = fields.Selection([
        ("financial", "Financial"),
        ("legal", "Legal"),
        ("tax", "Tax"),
        ("governance", "Governance"),
        ("other", "Other"),
    ], default="financial")


class PlanningPbcReminder(models.Model):
    _name = "qaco.planning.pbc.reminder"
    _description = "PBC Reminder Log"

    request_id = fields.Many2one("qaco.planning.pbc", required=True, ondelete="cascade")
    reminder_type = fields.Selection([
        ("email", "Email"),
        ("call", "Call"),
        ("portal", "Portal"),
    ], default="email")
    reminder_date = fields.Datetime(default=fields.Datetime.now)
    note = fields.Text()


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


class PlanningEvidenceLog(models.Model):
    _name = "qaco.planning.evidence"
    _description = "Planning Evidence Log"
    _order = "create_date desc"

    name = fields.Char(string="Reference", required=True)
    model_name = fields.Char(string="Model")
    res_id = fields.Integer(string="Record ID")
    field_name = fields.Char(string="Field")
    action_type = fields.Selection([
        ("create", "Create"),
        ("update", "Update"),
        ("state", "State Change"),
        ("approval", "Approval"),
        ("export", "Export"),
        ("reminder", "Reminder"),
    ], required=True)
    before_value = fields.Text(string="Before Snapshot")
    after_value = fields.Text(string="After Snapshot")
    note = fields.Text(string="Justification / Narrative")
    standard_reference = fields.Char(string="Authority Reference")
    user_id = fields.Many2one("res.users", string="Performed By", default=lambda self: self.env.user)
    exported = fields.Boolean(string="Included in Latest Export", default=False)

    @api.model
    def log_event(self, name, model_name, res_id, action_type, note, standard_reference, field_name=None, before_value=None, after_value=None):
        return self.sudo().create(
            {
                "name": name,
                "model_name": model_name,
                "res_id": res_id,
                "action_type": action_type,
                "note": note,
                "standard_reference": standard_reference,
                "field_name": field_name,
                "before_value": before_value,
                "after_value": after_value,
            }
        )

    def export_payload(self):
        self.ensure_one()
        return {
            "reference": self.name,
            "model": self.model_name,
            "res_id": self.res_id,
            "action": self.action_type,
            "note": self.note,
            "standard": self.standard_reference,
            "timestamp": fields.Datetime.to_string(self.create_date),
            "user": self.user_id.name,
        }


class PlanningMaterialityConfig(models.Model):
    _name = "qaco.planning.materiality.config"
    _description = "Materiality Configuration"

    name = fields.Char(required=True)
    entity_classification = fields.Selection(ENTITY_CLASSES, required=True)
    default_basis = fields.Selection([
        ("pbt", "Profit before tax"),
        ("revenue", "Revenue"),
        ("assets", "Total assets"),
        ("equity", "Equity"),
    ], default="pbt")
    default_pct_pbt = fields.Float(default=5.0)
    default_pct_revenue = fields.Float(default=1.0)
    default_pct_assets = fields.Float(default=1.5)
    default_pct_equity = fields.Float(default=3.0)
    performance_factor = fields.Float(default=0.75)
    tolerable_factor = fields.Float(default=0.5)


class PlanningMateriality(models.Model):
    _name = "qaco.planning.materiality"
    _description = "Materiality Worksheet"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(default=lambda self: _("Materiality"), required=True)
    planning_id = fields.Many2one("qaco.planning.phase", required=True, ondelete="cascade")
    basis = fields.Selection([
        ("pbt", "Profit before tax"),
        ("revenue", "Revenue"),
        ("assets", "Total assets"),
        ("equity", "Equity"),
    ], required=True, tracking=True)
    base_value = fields.Monetary(string="Benchmark Amount", tracking=True)
    base_source_type = fields.Selection([
        ("tb_snapshot", "Trial balance snapshot"),
        ("account_move", "Accounting module"),
        ("manual", "Manual entry"),
    ], default="manual", tracking=True)
    base_source_reference = fields.Char(string="Source Reference")
    default_percentage = fields.Float(string="Default %", readonly=True)
    applied_percentage = fields.Float(string="Applied %", required=True)
    overall_materiality = fields.Monetary(string="Overall Materiality", compute="_compute_amounts", store=True)
    performance_factor = fields.Float(string="Performance Factor", default=0.75)
    performance_materiality = fields.Monetary(string="Performance Materiality", compute="_compute_amounts", store=True)
    tolerable_factor = fields.Float(string="Tolerable Factor", default=0.5)
    tolerable_misstatement = fields.Monetary(string="Tolerable Misstatement", compute="_compute_amounts", store=True)
    currency_id = fields.Many2one(related="planning_id.currency_id", store=True)
    justification_text = fields.Text(string="Justification", required=True)
    evidence_attachment_id = fields.Many2one("ir.attachment", string="Evidence Attachment")
    computed_by = fields.Many2one("res.users", default=lambda self: self.env.user)
    computed_on = fields.Datetime(default=fields.Datetime.now)
    approved = fields.Boolean(string="Partner Approved", default=False)

    @api.depends("base_value", "applied_percentage", "performance_factor", "tolerable_factor")
    def _compute_amounts(self):
        for rec in self:
            rec.overall_materiality = (rec.base_value or 0.0) * (rec.applied_percentage or 0.0) / 100.0
            rec.performance_materiality = rec.overall_materiality * (rec.performance_factor or 0.0)
            rec.tolerable_misstatement = rec.overall_materiality * (rec.tolerable_factor or 0.0)

    @api.constrains("applied_percentage", "default_percentage")
    def _check_justification(self):
        for rec in self:
            if rec.default_percentage and abs(rec.applied_percentage - rec.default_percentage) > 0.01 and not rec.justification_text:
                raise ValidationError(_("Provide justification when overriding default percentage (ISA 320 para 12)."))

    def action_partner_approve(self):
        self.ensure_one()
        if self.env.user not in (self.planning_id.partner_id,):
            raise ValidationError(_("Only the engagement partner can approve materiality."))
        self.approved = True
        self.planning_id.materiality_ready = True
        self.planning_id._log_evidence(
            name=_('Materiality approved'),
            action_type='approval',
            note=self.justification_text,
            standard_reference='ISA 320 para 14; ICAP APM section 5',
        )


class PlanningMaterialityWizard(models.TransientModel):
    _name = "qaco.planning.materiality.wizard"
    _description = "Materiality Wizard"

    planning_id = fields.Many2one("qaco.planning.phase", required=True)
    basis = fields.Selection(selection=PlanningMateriality._fields["basis"].selection, required=True)
    base_value = fields.Float(required=True)
    base_source_type = fields.Selection(selection=PlanningMateriality._fields["base_source_type"].selection, default="manual")
    base_source_reference = fields.Char()
    applied_percentage = fields.Float()
    justification_text = fields.Text(required=True)

    def action_apply(self):
        self.ensure_one()
        config = self.env['qaco.planning.materiality.config'].search(
            ['|', ('entity_classification', '=', self.planning_id.entity_classification), ('entity_classification', '=', 'other')],
            limit=1,
        )
        default_pct = 5.0
        if config:
            default_pct = getattr(config, f"default_pct_{self.basis}", default_pct)
        applied_pct = self.applied_percentage or default_pct
        materiality = self.env['qaco.planning.materiality'].create(
            {
                'planning_id': self.planning_id.id,
                'basis': self.basis,
                'base_value': self.base_value,
                'base_source_type': self.base_source_type,
                'base_source_reference': self.base_source_reference,
                'default_percentage': default_pct,
                'applied_percentage': applied_pct,
                'performance_factor': config.performance_factor if config else 0.75,
                'tolerable_factor': config.tolerable_factor if config else 0.5,
                'justification_text': self.justification_text,
            }
        )
        return materiality.action_partner_approve()


class PlanningSettings(models.TransientModel):
    _inherit = "res.config.settings"

    materiality_performance_factor = fields.Float(
        string="Performance Factor",
        config_parameter="qaco_planning.performance_factor",
        default=0.75,
    )
    pbc_escalation_days = fields.Integer(
        string="PBC Escalation Days",
        config_parameter="qaco_planning.pbc_escalation_days",
        default=3,
    )
