# -*- coding: utf-8 -*-
"""
P-13: Planning Review & Approval
Standards: ISA 220, ISQM-1
Purpose: Final quality and engagement approval.
"""

import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PlanningP13Approval(models.Model):
    """P-13: Planning Review & Approval (ISA 220, ISQM-1)"""

    _name = "qaco.planning.p13.approval"
    _description = "P-13: Audit Planning Memorandum (APM) & Approval"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    TAB_STATE = [
        ("not_started", "Not Started"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("reviewed", "Reviewed"),
        ("approved", "Approved"),
    ]

    state = fields.Selection(
        TAB_STATE,
        string="Status",
        default="not_started",
        tracking=True,
        copy=False,
    )

    # Sequential Gating (ISA 300/220: Systematic Planning Approach)
    can_open = fields.Boolean(
        string="Can Open This Tab",
        compute="_compute_can_open",
        store=False,
        help="P-13 can only be opened after P-12 is approved",
    )

    @api.depends("audit_id")
    def _compute_can_open(self):
        """P-13 requires P-12 to be approved."""
        for rec in self:
            if not rec.audit_id:
                rec.can_open = False
                continue
            # Find P-12 for this audit
            p12 = self.env["qaco.planning.p12.strategy"].search(
                [("audit_id", "=", rec.audit_id.id)], limit=1
            )
            # P-12 uses 'locked' as its final approved state
            rec.can_open = p12.state in ("partner", "locked") if p12 else False

    @api.constrains("state")
    def _check_sequential_gating(self):
        """ISA 300/220: Enforce sequential planning approach."""
        for rec in self:
            if rec.state != "not_started" and not rec.can_open:
                raise UserError(
                    "ISA 300/220 & ISQM-1 Violation: Sequential Planning Approach Required.\n\n"
                    "P-13 (Planning Approval) cannot be started until P-12 (Audit Strategy) "
                    "has been Partner-approved and locked.\n\n"
                    "Reason: Final planning approval and quality review per ISQM-1 requires "
                    "completed and approved audit strategy from P-12.\n\n"
                    "Action: Please complete and obtain Partner approval for P-12 first."
                )

    name = fields.Char(
        string="Reference", compute="_compute_name", store=True, readonly=True
    )
    audit_id = fields.Many2one(
        "qaco.audit",
        string="Audit Engagement",
        required=True,
        ondelete="cascade",
        index=True,
        tracking=True,
    )
    planning_main_id = fields.Many2one(
        "qaco.planning.main", string="Planning Phase", ondelete="cascade", index=True
    )
    client_id = fields.Many2one(
        "res.partner",
        string="Client Name",
        related="audit_id.client_id",
        readonly=True,
        store=False,
    )

    # ===== Planning Completion Checklist =====
    checklist_p1_complete = fields.Boolean(string="P-1: Engagement Setup Complete")
    checklist_p2_complete = fields.Boolean(string="P-2: Entity Understanding Complete")
    checklist_p3_complete = fields.Boolean(string="P-3: Internal Controls Complete")
    checklist_p4_complete = fields.Boolean(string="P-4: Analytical Procedures Complete")
    checklist_p5_complete = fields.Boolean(string="P-5: Materiality Complete")
    checklist_p6_complete = fields.Boolean(string="P-6: Risk Assessment Complete")
    checklist_p7_complete = fields.Boolean(string="P-7: Fraud Risk Complete")
    checklist_p8_complete = fields.Boolean(string="P-8: Going Concern Complete")
    checklist_p9_complete = fields.Boolean(string="P-9: Laws & Regulations Complete")
    checklist_p10_complete = fields.Boolean(string="P-10: Related Parties Complete")
    checklist_p11_complete = fields.Boolean(string="P-11: Group Audit Complete")
    checklist_p12_complete = fields.Boolean(string="P-12: Audit Strategy Complete")

    all_tabs_complete = fields.Boolean(
        string="All P-Tabs Complete", compute="_compute_all_tabs_complete", store=True
    )

    # Alias for XML compatibility
    all_tabs_approved = fields.Boolean(
        related="all_tabs_complete", string="All Tabs Approved", readonly=False
    )
    planning_lock_date = fields.Datetime(
        related="planning_locked_date", string="Planning Lock Date", readonly=False
    )

    # Dynamic checklist One2many
    checklist_ids = fields.One2many(
        "qaco.planning.checklist.line", "p13_approval_id", string="Planning Checklist"
    )

    # ===== Planning Review Notes =====
    manager_review_notes = fields.Html(
        string="Manager Review Notes", help="Manager's review comments on planning"
    )
    manager_review_complete = fields.Boolean(
        string="Manager Review Complete", tracking=True
    )
    manager_review_date = fields.Datetime(string="Manager Review Date")
    manager_reviewer_id = fields.Many2one("res.users", string="Manager Reviewer")

    partner_review_notes = fields.Html(
        string="Partner Review Notes", help="Partner's review comments on planning"
    )
    partner_review_complete = fields.Boolean(
        string="Partner Review Complete", tracking=True
    )
    partner_review_date = fields.Datetime(string="Partner Review Date")
    partner_reviewer_id = fields.Many2one("res.users", string="Partner Reviewer")

    # Quality Review fields for XML compatibility
    quality_review_summary = fields.Html(
        string="Quality Review Summary", help="Summary of quality review performed"
    )
    issues_identified = fields.Html(
        string="Issues Identified", help="Issues identified during quality review"
    )
    issues_resolution = fields.Html(
        string="Issues Resolution", help="Resolution of identified issues"
    )

    # ===== EQCR (Engagement Quality Control Review) =====
    eqcr_required = fields.Boolean(
        string="EQCR Required",
        tracking=True,
        help="Is an Engagement Quality Control Review required per ISA 220/ISQM-1?",
    )
    eqcr_criteria = fields.Html(
        string="EQCR Criteria", help="Document the criteria for EQCR requirement"
    )
    eqcr_reviewer_id = fields.Many2one(
        "res.users", string="EQCR Reviewer", tracking=True
    )
    eqcr_review_date = fields.Datetime(string="EQCR Review Date")
    eqcr_review_notes = fields.Html(
        string="EQCR Review Notes", help="EQCR reviewer's comments on planning phase"
    )
    eqcr_approval = fields.Boolean(string="EQCR Approved", tracking=True)
    eqcr_matters_raised = fields.Html(
        string="EQCR Matters Raised", help="Significant matters raised during EQCR"
    )
    eqcr_resolution = fields.Html(
        string="EQCR Resolution", help="Resolution of matters raised by EQCR"
    )

    # EQCR aliases for XML compatibility
    eqcr_scope = fields.Html(
        related="eqcr_criteria", string="EQCR Scope", readonly=False
    )
    eqcr_findings = fields.Html(
        related="eqcr_matters_raised", string="EQCR Findings", readonly=False
    )
    eqcr_conclusion = fields.Html(
        related="eqcr_resolution", string="EQCR Conclusion", readonly=False
    )
    eqcr_signed_on = fields.Datetime(
        related="eqcr_review_date", string="EQCR Signed On", readonly=False
    )

    # ===== Quality Standards Compliance =====
    icap_standards_compliant = fields.Boolean(
        string="ICAP Standards Compliance Verified", tracking=True
    )
    secp_requirements_addressed = fields.Boolean(
        string="SECP Requirements Addressed", tracking=True
    )
    aob_guidelines_considered = fields.Boolean(
        string="AOB Guidelines Considered", tracking=True
    )
    isqm1_compliance = fields.Html(string="ISQM-1 Compliance Documentation")

    # ===== Partner Sign-off =====
    partner_signoff = fields.Boolean(string="Partner Sign-off", tracking=True)
    partner_signoff_date = fields.Datetime(string="Partner Sign-off Date")
    partner_signoff_user_id = fields.Many2one(
        "res.users", string="Partner Who Signed Off"
    )
    partner_signoff_notes = fields.Html(string="Partner Sign-off Notes")

    # Execution phase unlock flag
    execution_unlocked = fields.Boolean(
        string="Execution Phase Unlocked",
        readonly=True,
        copy=False,
        help="Set to True when execution phase is auto-unlocked after P-13 approval",
    )

    # Partner confirmation fields for XML compatibility
    partner_confirmed_resources = fields.Boolean(
        string="Resources Confirmed", help="Partner confirms resources are adequate"
    )
    partner_confirmed_strategy = fields.Boolean(
        string="Strategy Confirmed",
        help="Partner confirms audit strategy is appropriate",
    )
    partner_confirmed_timing = fields.Boolean(
        string="Timing Confirmed", help="Partner confirms audit timing is realistic"
    )
    partner_confirmed_risks = fields.Boolean(
        string="Risks Confirmed",
        help="Partner confirms risks have been properly addressed",
    )

    # ===== Planning Lock =====
    planning_locked = fields.Boolean(
        string="Planning Locked",
        default=False,
        tracking=True,
        help="Once locked, planning cannot be modified without partner approval",
    )
    planning_locked_date = fields.Datetime(string="Planning Locked Date")
    planning_locked_by_id = fields.Many2one("res.users", string="Planning Locked By")

    # ===== Outstanding Matters =====
    outstanding_matters = fields.Html(
        string="Outstanding Matters",
        help="Any matters requiring resolution before execution",
    )
    carryforward_issues = fields.Html(
        string="Carryforward Issues", help="Issues from prior year requiring attention"
    )

    # ===== APM (Audit Planning Memorandum) =====
    apm_generated = fields.Boolean(string="APM Generated", tracking=True)
    apm_generation_date = fields.Datetime(string="APM Generation Date")
    apm_approved = fields.Boolean(string="APM Approved", tracking=True)

    # APM fields for XML compatibility
    apm_summary = fields.Html(
        string="APM Summary", help="Audit Planning Memorandum summary"
    )
    key_decisions = fields.Html(
        string="Key Decisions", help="Key planning decisions made"
    )
    partner_attention_matters = fields.Html(
        string="Matters for Partner Attention",
        help="Matters requiring partner attention",
    )

    # Change log One2many
    change_log_ids = fields.One2many(
        "qaco.planning.change.log", "p13_approval_id", string="Change Log"
    )

    # ===== Attachments =====
    apm_attachment_ids = fields.Many2many(
        "ir.attachment",
        "qaco_p13_apm_rel",
        "p13_id",
        "attachment_id",
        string="Audit Planning Memorandum",
    )
    signoff_attachment_ids = fields.Many2many(
        "ir.attachment",
        "qaco_p13_signoff_rel",
        "p13_id",
        "attachment_id",
        string="Sign-off Documentation",
    )
    eqcr_attachment_ids = fields.Many2many(
        "ir.attachment",
        "qaco_p13_eqcr_rel",
        "p13_id",
        "attachment_id",
        string="EQCR Documentation",
    )

    # Approval attachments for XML compatibility
    approval_attachment_ids = fields.Many2many(
        "ir.attachment",
        "qaco_p13_approval_rel",
        "p13_id",
        "attachment_id",
        string="Approval Attachments",
    )

    # Planning completion notes for XML compatibility
    planning_completion_notes = fields.Html(
        string="Planning Completion Notes", help="Notes on planning phase completion"
    )

    # ===== Summary =====
    planning_approval_summary = fields.Html(
        string="Planning Approval Summary",
        help="Final planning review and approval summary",
    )
    isa_reference = fields.Char(
        string="ISA Reference", default="ISA 220/ISQM-1", readonly=True
    )

    # ===== Sign-off Fields =====
    senior_signed_user_id = fields.Many2one(
        "res.users",
        string="Senior Completed By",
        tracking=True,
        copy=False,
        readonly=True,
    )
    senior_signed_on = fields.Datetime(
        string="Senior Completed On", tracking=True, copy=False, readonly=True
    )
    manager_reviewed_user_id = fields.Many2one(
        "res.users",
        string="Manager Reviewed By",
        tracking=True,
        copy=False,
        readonly=True,
    )
    manager_reviewed_on = fields.Datetime(
        string="Manager Reviewed On", tracking=True, copy=False, readonly=True
    )
    partner_approved_user_id = fields.Many2one(
        "res.users",
        string="Partner Approved By",
        tracking=True,
        copy=False,
        readonly=True,
    )
    partner_approved_on = fields.Datetime(
        string="Partner Approved On", tracking=True, copy=False, readonly=True
    )
    reviewer_notes = fields.Html(string="Reviewer Notes")
    approval_notes = fields.Html(string="Approval Notes")

    _sql_constraints = [
        (
            "audit_unique",
            "UNIQUE(audit_id)",
            "Only one P-13 record per Audit Engagement is allowed.",
        )
    ]

    @api.depends("audit_id", "client_id")
    def _compute_name(self):
        for record in self:
            if record.client_id:
                record.name = f"P13-{record.client_id.name[:15]}"
            else:
                record.name = "P-13: Planning Review"

    @api.depends(
        "checklist_p1_complete",
        "checklist_p2_complete",
        "checklist_p3_complete",
        "checklist_p4_complete",
        "checklist_p5_complete",
        "checklist_p6_complete",
        "checklist_p7_complete",
        "checklist_p8_complete",
        "checklist_p9_complete",
        "checklist_p10_complete",
        "checklist_p11_complete",
        "checklist_p12_complete",
    )
    def _compute_all_tabs_complete(self):
        for record in self:
            record.all_tabs_complete = all(
                [
                    record.checklist_p1_complete,
                    record.checklist_p2_complete,
                    record.checklist_p3_complete,
                    record.checklist_p4_complete,
                    record.checklist_p5_complete,
                    record.checklist_p6_complete,
                    record.checklist_p7_complete,
                    record.checklist_p8_complete,
                    record.checklist_p9_complete,
                    record.checklist_p10_complete,
                    record.checklist_p11_complete,
                    record.checklist_p12_complete,
                ]
            )

    def action_refresh_checklist(self):
        """Refresh the completion checklist from P-tabs."""
        self.ensure_one()
        main = self.planning_main_id
        if main:
            # Map checklist flags to actual P-tabs (P-1 deprecated)
            self.checklist_p1_complete = (
                main.p2_entity_id.state == "approved" if main.p2_entity_id else False
            )
            self.checklist_p2_complete = (
                main.p3_controls_id.state == "approved" if main.p3_controls_id else False
            )
            self.checklist_p3_complete = (
                main.p4_analytics_id.state == "approved" if main.p4_analytics_id else False
            )
            self.checklist_p4_complete = (
                main.p5_materiality_id.state == "approved" if main.p5_materiality_id else False
            )
            self.checklist_p5_complete = (
                main.p6_risk_id.state == "approved" if main.p6_risk_id else False
            )
            self.checklist_p6_complete = (
                main.p7_fraud_id.state == "approved" if main.p7_fraud_id else False
            )
            self.checklist_p7_complete = (
                main.p8_going_concern_id.state == "approved" if main.p8_going_concern_id else False
            )
            self.checklist_p8_complete = (
                main.p9_laws_id.state == "approved" if main.p9_laws_id else False
            )
            self.checklist_p9_complete = (
                main.p10_related_parties_id.state == "approved" if main.p10_related_parties_id else False
            )
            self.checklist_p10_complete = (
                main.p11_group_audit_id.state == "approved" if main.p11_group_audit_id else False
            )
            self.checklist_p11_complete = (
                main.p12_strategy_id.state == "approved" if main.p12_strategy_id else False
            )
            self.checklist_p12_complete = (
                main.p13_approval_id.state == "approved" if main.p13_approval_id else False
            )

    def action_manager_review(self):
        """Manager completes review."""
        self.ensure_one()
        self.action_refresh_checklist()
        self.manager_review_complete = True
        self.manager_review_date = fields.Datetime.now()
        self.manager_reviewer_id = self.env.user

    def action_partner_review(self):
        """Partner completes review."""
        self.ensure_one()
        if not self.manager_review_complete:
            raise UserError("Manager review must be completed before partner review.")
        self.partner_review_complete = True
        self.partner_review_date = fields.Datetime.now()
        self.partner_reviewer_id = self.env.user

    def action_partner_signoff(self):
        """Partner signs off on planning."""
        self.ensure_one()
        if not self.all_tabs_complete:
            raise UserError("All P-tabs must be approved before partner sign-off.")
        if not self.partner_review_complete:
            raise UserError("Partner review must be completed before sign-off.")
        if self.eqcr_required and not self.eqcr_approval:
            raise UserError("EQCR approval is required before partner sign-off.")
        self.partner_signoff = True
        self.partner_signoff_date = fields.Datetime.now()
        self.partner_signoff_user_id = self.env.user

    def action_lock_planning(self):
        """
        Lock planning phase.
        Session 6C: Auto-unlock execution phase when planning is locked.
        """
        self.ensure_one()
        if not self.partner_signoff:
            raise UserError("Partner sign-off is required before locking planning.")
        self.planning_locked = True
        self.planning_locked_date = fields.Datetime.now()
        self.planning_locked_by_id = self.env.user
        # Update main planning phase
        if self.planning_main_id:
            self.planning_main_id.is_planning_locked = True

        # Session 6C: Auto-unlock execution phase
        self._auto_unlock_execution_phase()

    def _auto_unlock_execution_phase(self):
        """
        Session 6C: Automatically unlock/enable execution phase when planning is locked.
        Ensures seamless audit lifecycle progression from planning → execution.
        """
        self.ensure_one()
        if not self.audit_id:
            return

        # Check if execution phase module is installed
        if "qaco.execution.phase" in self.env:
            # Try to find or create execution phase record
            execution = self.env["qaco.execution.phase"].search(
                [("audit_id", "=", self.audit_id.id)], limit=1
            )

            if execution:
                # Unlock execution if it was previously locked
                if hasattr(execution, "is_locked") and execution.is_locked:
                    execution.is_locked = False
                    _logger.info(
                        f"Session 6C: Execution phase unlocked for audit {self.audit_id.id}"
                    )
                    self.message_post(
                        body="✅ Planning locked successfully. Execution phase has been automatically unlocked."
                    )
            else:
                # Create execution phase if it doesn't exist
                try:
                    execution = self.env["qaco.execution.phase"].create(
                        {
                            "audit_id": self.audit_id.id,
                        }
                    )
                    _logger.info(
                        f"Session 6C: Execution phase created and unlocked for audit {self.audit_id.id}"
                    )
                    self.message_post(
                        body="✅ Planning locked successfully. Execution phase has been created and is now ready."
                    )
                except Exception as e:
                    _logger.warning(
                        f"Session 6C: Could not auto-create execution phase: {e}"
                    )
                    # Don't fail planning lock if execution phase creation fails
                    self.message_post(
                        body="✅ Planning locked successfully. Note: Execution phase needs to be manually created."
                    )
        else:
            # Execution phase module not installed - just log it
            _logger.info(
                f"Session 6C: Execution phase module not installed. Planning locked for audit {self.audit_id.id}"
            )
            self.message_post(body="✅ Planning locked successfully.")

    def action_unlock_planning(self):
        """Unlock planning for corrections."""
        self.ensure_one()
        self.planning_locked = False
        if self.planning_main_id:
            self.planning_main_id.is_planning_locked = False

    def action_generate_apm(self):
        """Generate Audit Planning Memorandum."""
        self.ensure_one()
        self.apm_generated = True
        self.apm_generation_date = fields.Datetime.now()
        return {
            "type": "ir.actions.act_url",
            "url": f"/report/pdf/qaco_planning_phase.report_audit_planning_memo/{self.planning_main_id.id if self.planning_main_id else self.id}",
            "target": "new",
        }

    def action_eqcr_approve(self):
        """EQCR approves planning."""
        self.ensure_one()
        if not self.eqcr_reviewer_id:
            raise UserError("EQCR reviewer must be assigned.")
        self.eqcr_approval = True
        self.eqcr_review_date = fields.Datetime.now()

    def _validate_mandatory_fields(self):
        """Validate mandatory fields before completing P-13."""
        self.ensure_one()
        errors = []
        if not self.all_tabs_complete:
            errors.append("All P-tabs (P-1 to P-12) must be approved")
        if not self.manager_review_complete:
            errors.append("Manager review must be completed")
        if not self.partner_signoff:
            errors.append("Partner sign-off is required")
        if self.eqcr_required and not self.eqcr_approval:
            errors.append("EQCR approval is required")
        if not self.planning_approval_summary:
            errors.append("Planning approval summary is required")
        if errors:
            raise UserError(
                "Cannot complete P-13. Missing requirements:\n- " + "\n- ".join(errors)
            )

    def action_start_work(self):
        for record in self:
            if record.state != "not_started":
                raise UserError("Can only start work on tabs that are Not Started.")
            record.action_refresh_checklist()
            record.state = "in_progress"

    def action_complete(self):
        for record in self:
            if record.state != "in_progress":
                raise UserError("Can only complete tabs that are In Progress.")
            record._validate_mandatory_fields()
            record.senior_signed_user_id = self.env.user
            record.senior_signed_on = fields.Datetime.now()
            record.state = "completed"

    def action_review(self):
        for record in self:
            if record.state != "completed":
                raise UserError("Can only review tabs that are Completed.")
            record.manager_reviewed_user_id = self.env.user
            record.manager_reviewed_on = fields.Datetime.now()
            record.state = "reviewed"

    def action_approve(self):
        """Approve P-13 and lock entire planning phase, unlock execution."""
        for record in self:
            if record.state != "reviewed":
                raise UserError("Can only approve tabs that have been Reviewed.")
            record.partner_approved_user_id = self.env.user
            record.partner_approved_on = fields.Datetime.now()
            record.state = "approved"
            # Lock planning when P-13 is approved
            record.action_lock_planning()
            # Auto-unlock execution phase (ISA 300)
            record._auto_unlock_execution_phase()

    def action_send_back(self):
        for record in self:
            if record.state not in ["completed", "reviewed"]:
                raise UserError(
                    "Can only send back tabs that are Completed or Reviewed."
                )
            record.state = "in_progress"

    def action_unlock(self):
        for record in self:
            if record.state != "approved":
                raise UserError("Can only unlock Approved tabs.")
            record.partner_approved_user_id = False
            record.partner_approved_on = False
            record.state = "reviewed"
            record.action_unlock_planning()


class PlanningChecklistLine(models.Model):
    """Planning Checklist Line Item for P-13 Approval."""

    _name = "qaco.planning.checklist.line"
    _description = "Planning Checklist Line"
    _order = "tab_code"

    p13_approval_id = fields.Many2one(
        "qaco.planning.p13.approval",
        string="P-13 Approval",
        required=True,
        ondelete="cascade",
    )
    tab_code = fields.Char(
        string="Tab Code", required=True, help="e.g., P-1, P-2, etc."
    )
    tab_name = fields.Char(string="Tab Name", required=True)
    isa_reference = fields.Char(
        string="ISA Reference", help="e.g., ISA 300, ISA 315, etc."
    )
    status = fields.Selection(
        [
            ("not_started", "Not Started"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("reviewed", "Reviewed"),
            ("approved", "Approved"),
        ],
        string="Status",
        default="not_started",
    )
    completed_by = fields.Many2one("res.users", string="Completed By")
    completed_on = fields.Datetime(string="Completed On")
    reviewed_by = fields.Many2one("res.users", string="Reviewed By")
    reviewed_on = fields.Datetime(string="Reviewed On")


class PlanningChangeLog(models.Model):
    """Change Log for Planning Phase changes after lock."""

    _name = "qaco.planning.change.log"
    _description = "Planning Change Log"
    _order = "change_date desc"

    p13_approval_id = fields.Many2one(
        "qaco.planning.p13.approval",
        string="P-13 Approval",
        required=True,
        ondelete="cascade",
    )
    change_date = fields.Datetime(
        string="Change Date", default=fields.Datetime.now, required=True
    )
    changed_by_id = fields.Many2one(
        "res.users",
        string="Changed By",
        default=lambda self: self._get_default_user(),
        required=True,
    )
    tab_affected = fields.Char(
        string="Tab Affected", required=True, help="e.g., P-1, P-5, etc."
    )
    change_description = fields.Text(string="Change Description", required=True)
    approved_by_id = fields.Many2one("res.users", string="Approved By")
    approval_date = fields.Datetime(string="Approval Date")
