# -*- coding: utf-8 -*-
"""
Core Audit Planning Model - ISA-Compliant Statutory Audit Planning (Pakistan)

This module implements the main audit.planning model that orchestrates
the 13-tab planning workflow per ISA/ICAP/AOB requirements.
"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AuditPlanning(models.Model):
    _name = "audit.planning"
    _description = "Statutory Audit Planning (Pakistan)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    PLANNING_STATES = [
        ("draft", "Draft"),
        ("in_progress", "In Progress"),
        ("under_review", "Under Review"),
        ("approved", "Approved"),
        ("locked", "Locked"),
    ]

    # ─────────────────────────────────────────────────────────────────
    # Core Fields
    # ─────────────────────────────────────────────────────────────────
    name = fields.Char(
        string="Planning Reference",
        compute="_compute_name",
        store=True,
        readonly=True,
    )
    engagement_id = fields.Many2one(
        "audit.engagement",
        string="Engagement",
        required=True,
        ondelete="cascade",
        tracking=True,
        help="Source audit engagement that anchors this planning.",
    )
    audit_id = fields.Many2one(
        "qaco.audit",
        string="Audit",
        related="engagement_id.audit_id",
        store=True,
        readonly=True,
    )
    client_id = fields.Many2one(
        "res.partner",
        string="Client",
        related="engagement_id.client_id",
        store=True,
        readonly=True,
    )
    onboarding_id = fields.Many2one(
        "qaco.client.onboarding",
        string="Client Onboarding",
        compute="_compute_onboarding_id",
        store=True,
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

    # ─────────────────────────────────────────────────────────────────
    # Workflow State & Navigation
    # ─────────────────────────────────────────────────────────────────
    planning_state = fields.Selection(
        PLANNING_STATES,
        string="Planning Status",
        default="draft",
        tracking=True,
        copy=False,
    )
    current_tab = fields.Integer(
        string="Current Tab",
        default=1,
        help="Tracks which P-tab user is currently on (1-13)",
    )
    can_proceed_next = fields.Boolean(
        string="Can Proceed to Next Tab",
        compute="_compute_can_proceed",
        store=True,
    )

    # ─────────────────────────────────────────────────────────────────
    # Partner & Review
    # ─────────────────────────────────────────────────────────────────
    partner_id = fields.Many2one(
        "res.users",
        string="Engagement Partner",
        tracking=True,
    )
    manager_id = fields.Many2one(
        "res.users",
        string="Engagement Manager",
        tracking=True,
    )
    eqcr_id = fields.Many2one(
        "res.users",
        string="EQCR Reviewer",
        tracking=True,
        help="Engagement Quality Control Reviewer (ISQM-1)",
    )
    review_notes = fields.Html(
        string="Review Notes",
        tracking=True,
    )

    # ─────────────────────────────────────────────────────────────────
    # APM (Audit Planning Memorandum) Generation
    # ─────────────────────────────────────────────────────────────────
    apm_generated = fields.Boolean(
        string="APM Generated",
        default=False,
        tracking=True,
        copy=False,
    )
    apm_generated_on = fields.Datetime(
        string="APM Generated On",
        readonly=True,
        copy=False,
    )
    apm_attachment_id = fields.Many2one(
        "ir.attachment",
        string="APM Document",
        readonly=True,
        copy=False,
    )
    apm_version = fields.Integer(
        string="APM Version",
        default=0,
        readonly=True,
    )

    # ─────────────────────────────────────────────────────────────────
    # One2many Links to Tab Sub-Models (P-1 through P-13)
    # ─────────────────────────────────────────────────────────────────
    p1_team_id = fields.Many2one(
        "audit.planning.p1.team",
        string="P-1: Team Assignment",
        ondelete="cascade",
    )
    p2_entity_id = fields.Many2one(
        "audit.planning.p2.entity",
        string="P-2: Entity Understanding",
        ondelete="cascade",
    )
    p3_controls_id = fields.Many2one(
        "audit.planning.p3.controls",
        string="P-3: Internal Controls",
        ondelete="cascade",
    )
    p4_analytics_id = fields.Many2one(
        "audit.planning.p4.analytics",
        string="P-4: Analytical Procedures",
        ondelete="cascade",
    )
    p5_materiality_id = fields.Many2one(
        "audit.planning.p5.materiality",
        string="P-5: Materiality",
        ondelete="cascade",
    )
    p6_risk_id = fields.Many2one(
        "audit.planning.p6.risk",
        string="P-6: Risk Assessment",
        ondelete="cascade",
    )
    p7_fraud_id = fields.Many2one(
        "audit.planning.p7.fraud",
        string="P-7: Fraud Risk",
        ondelete="cascade",
    )
    p8_going_concern_id = fields.Many2one(
        "audit.planning.p8.going_concern",
        string="P-8: Going Concern",
        ondelete="cascade",
    )
    p9_compliance_id = fields.Many2one(
        "audit.planning.p9.compliance",
        string="P-9: Laws & Regulations",
        ondelete="cascade",
    )
    p10_related_party_id = fields.Many2one(
        "audit.planning.p10.related_party",
        string="P-10: Related Parties",
        ondelete="cascade",
    )
    p11_group_id = fields.Many2one(
        "audit.planning.p11.group",
        string="P-11: Group Audit",
        ondelete="cascade",
    )
    p12_strategy_id = fields.Many2one(
        "audit.planning.p12.strategy",
        string="P-12: Audit Strategy",
        ondelete="cascade",
    )
    p13_review_id = fields.Many2one(
        "audit.planning.p13.review",
        string="P-13: Planning Review",
        ondelete="cascade",
    )

    # ─────────────────────────────────────────────────────────────────
    # Auto-Generated Audit Programs
    # ─────────────────────────────────────────────────────────────────
    auto_generated_program_ids = fields.One2many(
        "audit.planning.program",
        "planning_id",
        string="Auto-Generated Audit Programs",
    )
    programs_generated = fields.Boolean(
        string="Programs Generated",
        default=False,
        tracking=True,
    )

    # ─────────────────────────────────────────────────────────────────
    # Progress Tracking
    # ─────────────────────────────────────────────────────────────────
    overall_progress = fields.Float(
        string="Overall Progress %",
        compute="_compute_overall_progress",
        store=True,
    )
    tabs_completed = fields.Integer(
        string="Tabs Completed",
        compute="_compute_overall_progress",
        store=True,
    )

    # ─────────────────────────────────────────────────────────────────
    # Sign-offs
    # ─────────────────────────────────────────────────────────────────
    manager_signed = fields.Boolean(string="Manager Signed", tracking=True, copy=False)
    manager_signed_on = fields.Datetime(string="Manager Signed On", readonly=True, copy=False)
    partner_signed = fields.Boolean(string="Partner Signed", tracking=True, copy=False)
    partner_signed_on = fields.Datetime(string="Partner Signed On", readonly=True, copy=False)
    eqcr_signed = fields.Boolean(string="EQCR Signed", tracking=True, copy=False)
    eqcr_signed_on = fields.Datetime(string="EQCR Signed On", readonly=True, copy=False)

    # ─────────────────────────────────────────────────────────────────
    # Computed Fields
    # ─────────────────────────────────────────────────────────────────
    @api.depends("engagement_id", "client_id", "create_date")
    def _compute_name(self):
        for record in self:
            if record.client_id and record.create_date:
                record.name = f"PLAN/{record.client_id.name[:20]}/{record.create_date.strftime('%Y%m%d')}"
            elif record.client_id:
                record.name = f"PLAN/{record.client_id.name[:20]}/DRAFT"
            else:
                record.name = "PLAN/NEW"

    @api.depends("audit_id")
    def _compute_onboarding_id(self):
        for record in self:
            if record.audit_id:
                onboarding = self.env["qaco.client.onboarding"].search([
                    ("audit_id", "=", record.audit_id.id)
                ], limit=1)
                record.onboarding_id = onboarding.id if onboarding else False
            else:
                record.onboarding_id = False

    @api.depends(
        "p1_team_id.review_status",
        "p2_entity_id.review_status",
        "p3_controls_id.review_status",
        "p4_analytics_id.review_status",
        "p5_materiality_id.review_status",
        "p6_risk_id.review_status",
        "p7_fraud_id.review_status",
        "p8_going_concern_id.review_status",
        "p9_compliance_id.review_status",
        "p10_related_party_id.review_status",
        "p11_group_id.review_status",
        "p12_strategy_id.review_status",
        "p13_review_id.review_status",
    )
    def _compute_overall_progress(self):
        tab_fields = [
            "p1_team_id", "p2_entity_id", "p3_controls_id", "p4_analytics_id",
            "p5_materiality_id", "p6_risk_id", "p7_fraud_id", "p8_going_concern_id",
            "p9_compliance_id", "p10_related_party_id", "p11_group_id",
            "p12_strategy_id", "p13_review_id"
        ]
        for record in self:
            completed = 0
            for field in tab_fields:
                tab_record = getattr(record, field)
                if tab_record and tab_record.review_status == "reviewed":
                    completed += 1
            record.tabs_completed = completed
            record.overall_progress = (completed / 13.0) * 100.0

    @api.depends("current_tab")
    def _compute_can_proceed(self):
        for record in self:
            record.can_proceed_next = record._check_tab_complete(record.current_tab)

    def _check_tab_complete(self, tab_num):
        """Check if a specific tab has all mandatory fields completed."""
        self.ensure_one()
        tab_map = {
            1: self.p1_team_id,
            2: self.p2_entity_id,
            3: self.p3_controls_id,
            4: self.p4_analytics_id,
            5: self.p5_materiality_id,
            6: self.p6_risk_id,
            7: self.p7_fraud_id,
            8: self.p8_going_concern_id,
            9: self.p9_compliance_id,
            10: self.p10_related_party_id,
            11: self.p11_group_id,
            12: self.p12_strategy_id,
            13: self.p13_review_id,
        }
        tab_record = tab_map.get(tab_num)
        if not tab_record:
            return False
        return tab_record.is_complete

    # ─────────────────────────────────────────────────────────────────
    # Actions - Navigation
    # ─────────────────────────────────────────────────────────────────
    def action_save_and_next(self):
        """Save current tab and proceed to next."""
        self.ensure_one()
        if not self._check_tab_complete(self.current_tab):
            raise UserError(
                _("Complete all mandatory fields and upload required attachments before proceeding.")
            )
        if self.current_tab < 13:
            self.current_tab += 1
            if self.planning_state == "draft":
                self.planning_state = "in_progress"
        return True

    def action_go_back(self):
        """Go back to previous tab."""
        self.ensure_one()
        if self.planning_state == "locked":
            raise UserError(_("Planning is locked and cannot be modified."))
        if self.current_tab > 1:
            self.current_tab -= 1
        return True

    def action_go_to_tab(self, tab_num):
        """Navigate to a specific tab (only if previous tabs are complete)."""
        self.ensure_one()
        if self.planning_state == "locked":
            raise UserError(_("Planning is locked."))
        # Allow going back to any previous tab
        if tab_num < self.current_tab:
            self.current_tab = tab_num
            return True
        # For forward navigation, check all previous tabs
        for i in range(1, tab_num):
            if not self._check_tab_complete(i):
                raise UserError(
                    _("Complete Tab P-%d before proceeding to P-%d.") % (i, tab_num)
                )
        self.current_tab = tab_num
        return True

    # ─────────────────────────────────────────────────────────────────
    # Actions - Workflow
    # ─────────────────────────────────────────────────────────────────
    def action_submit_for_review(self):
        """Submit planning for manager review."""
        self.ensure_one()
        if self.overall_progress < 100.0:
            raise UserError(_("Complete all 13 planning tabs before submission."))
        self.planning_state = "under_review"
        self.message_post(body=_("Planning submitted for review."))
        return True

    def action_manager_sign(self):
        """Manager sign-off."""
        self.ensure_one()
        if self.planning_state != "under_review":
            raise UserError(_("Planning must be under review for manager sign-off."))
        self.manager_signed = True
        self.manager_signed_on = fields.Datetime.now()
        self.message_post(body=_("Manager signed off on planning."))
        return True

    def action_partner_sign(self):
        """Partner sign-off."""
        self.ensure_one()
        if not self.manager_signed:
            raise UserError(_("Manager must sign before partner approval."))
        self.partner_signed = True
        self.partner_signed_on = fields.Datetime.now()
        self.message_post(body=_("Partner signed off on planning."))
        return True

    def action_approve_planning(self):
        """Final approval - locks planning and generates APM."""
        self.ensure_one()
        if not self.partner_signed:
            raise UserError(_("Partner must sign before approval."))
        if not self.apm_generated:
            self.action_generate_apm()
        if not self.programs_generated:
            self.action_generate_programs()
        self.planning_state = "approved"
        self.message_post(body=_("Planning approved and ready for execution."))
        return True

    def action_lock_planning(self):
        """Lock planning after approval."""
        self.ensure_one()
        if self.planning_state != "approved":
            raise UserError(_("Planning must be approved before locking."))
        self.planning_state = "locked"
        self.message_post(body=_("Planning locked. Execution phase enabled."))
        return True

    # ─────────────────────────────────────────────────────────────────
    # Actions - APM Generation
    # ─────────────────────────────────────────────────────────────────
    def action_generate_apm(self):
        """Generate Audit Planning Memorandum PDF."""
        self.ensure_one()
        if self.overall_progress < 100.0:
            raise UserError(_("Complete all planning tabs before generating APM."))
        
        # Increment version
        self.apm_version += 1
        self.apm_generated = True
        self.apm_generated_on = fields.Datetime.now()
        
        # Generate PDF (placeholder - actual report generation)
        self.message_post(
            body=_("Audit Planning Memorandum v%d generated.") % self.apm_version
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("APM Generated"),
                "message": _("Audit Planning Memorandum v%d has been generated.") % self.apm_version,
                "type": "success",
                "sticky": False,
            }
        }

    # ─────────────────────────────────────────────────────────────────
    # Actions - Auto Audit Program Generation
    # ─────────────────────────────────────────────────────────────────
    def action_generate_programs(self):
        """Auto-generate risk-based audit programs from P-6 risk assessment."""
        self.ensure_one()
        if not self.p6_risk_id:
            raise UserError(_("Complete Risk Assessment (P-6) before generating programs."))
        
        # Get cycles to generate programs for
        cycles = [
            ("revenue", "Revenue Cycle"),
            ("purchases", "Purchases & Payables Cycle"),
            ("payroll", "Payroll Cycle"),
            ("inventory", "Inventory Cycle"),
            ("fixed_assets", "Fixed Assets Cycle"),
            ("cash_bank", "Cash & Bank Cycle"),
            ("borrowings", "Borrowings Cycle"),
            ("related_parties", "Related Parties Cycle"),
        ]
        
        Program = self.env["audit.planning.program"]
        for cycle_code, cycle_name in cycles:
            # Check if program already exists
            existing = Program.search([
                ("planning_id", "=", self.id),
                ("cycle", "=", cycle_code),
            ])
            if existing:
                continue
            
            # Create program based on risk level
            risk_level = self._get_cycle_risk_level(cycle_code)
            Program.create({
                "planning_id": self.id,
                "name": f"{cycle_name} - Audit Program",
                "cycle": cycle_code,
                "risk_level": risk_level,
                "sample_size": self._compute_sample_size(risk_level),
                "nature_of_procedures": self._get_procedure_nature(risk_level),
                "timing_of_procedures": self._get_procedure_timing(risk_level),
                "extent_of_procedures": self._get_procedure_extent(risk_level),
            })
        
        self.programs_generated = True
        self.message_post(body=_("Audit programs auto-generated based on risk assessment."))
        return True

    def _get_cycle_risk_level(self, cycle_code):
        """Determine risk level for a cycle from P-6 assessment."""
        # Default to moderate - actual implementation would read from risk_ids
        return "moderate"

    def _compute_sample_size(self, risk_level):
        """Compute sample size based on risk level."""
        sizes = {"low": 10, "moderate": 25, "high": 40}
        return sizes.get(risk_level, 25)

    def _get_procedure_nature(self, risk_level):
        """Get procedure nature based on risk."""
        if risk_level == "high":
            return "Extended substantive testing with increased sample sizes"
        elif risk_level == "moderate":
            return "Substantive testing with standard procedures"
        return "Analytical procedures with limited substantive testing"

    def _get_procedure_timing(self, risk_level):
        """Get procedure timing based on risk."""
        if risk_level == "high":
            return "Year-end testing with surprise procedures"
        return "Interim and year-end testing"

    def _get_procedure_extent(self, risk_level):
        """Get procedure extent based on risk."""
        if risk_level == "high":
            return "100% testing of significant items, increased sampling for others"
        elif risk_level == "moderate":
            return "Standard sampling with focus on material items"
        return "Limited sampling with analytical reliance"

    # ─────────────────────────────────────────────────────────────────
    # Pre-conditions Check
    # ─────────────────────────────────────────────────────────────────
    @api.model
    def create(self, vals):
        """Check pre-conditions before creating planning record."""
        record = super().create(vals)
        record._check_preconditions()
        record._create_tab_records()
        return record

    def _check_preconditions(self):
        """Verify onboarding is complete and partner-approved."""
        self.ensure_one()
        if not self.onboarding_id:
            return  # Allow creation without onboarding for now
        
        onboarding = self.onboarding_id
        if not onboarding.partner_approved:
            raise ValidationError(
                _("Client onboarding must be partner-approved before starting planning.")
            )
        if not onboarding.engagement_letter_signed:
            raise ValidationError(
                _("Engagement letter must be signed before starting planning.")
            )
        if not onboarding.independence_confirmed:
            raise ValidationError(
                _("Independence must be confirmed before starting planning.")
            )

    def _create_tab_records(self):
        """Create empty records for all 13 tabs."""
        self.ensure_one()
        tab_models = [
            ("p1_team_id", "audit.planning.p1.team"),
            ("p2_entity_id", "audit.planning.p2.entity"),
            ("p3_controls_id", "audit.planning.p3.controls"),
            ("p4_analytics_id", "audit.planning.p4.analytics"),
            ("p5_materiality_id", "audit.planning.p5.materiality"),
            ("p6_risk_id", "audit.planning.p6.risk"),
            ("p7_fraud_id", "audit.planning.p7.fraud"),
            ("p8_going_concern_id", "audit.planning.p8.going_concern"),
            ("p9_compliance_id", "audit.planning.p9.compliance"),
            ("p10_related_party_id", "audit.planning.p10.related_party"),
            ("p11_group_id", "audit.planning.p11.group"),
            ("p12_strategy_id", "audit.planning.p12.strategy"),
            ("p13_review_id", "audit.planning.p13.review"),
        ]
        for field_name, model_name in tab_models:
            if not getattr(self, field_name):
                tab_record = self.env[model_name].create({
                    "planning_id": self.id,
                })
                setattr(self, field_name, tab_record.id)

    # ─────────────────────────────────────────────────────────────────
    # Write Protection
    # ─────────────────────────────────────────────────────────────────
    def write(self, vals):
        for record in self:
            if record.planning_state == "locked":
                allowed = {"message_follower_ids", "activity_ids", "message_ids"}
                if set(vals.keys()) - allowed:
                    raise UserError(_("Planning is locked and cannot be modified."))
        return super().write(vals)
