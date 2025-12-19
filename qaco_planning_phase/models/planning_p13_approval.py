# -*- coding: utf-8 -*-
"""
P-13: Planning Review & Approval
Standards: ISA 220, ISQM-1
Purpose: Final quality and engagement approval.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError


class PlanningP13Approval(models.Model):
    """P-13: Planning Review & Approval (ISA 220, ISQM-1)"""
    _name = 'qaco.planning.p13.approval'
    _description = 'P-13: Planning Review & Approval'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    TAB_STATE = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
    ]

    state = fields.Selection(
        TAB_STATE,
        string='Status',
        default='not_started',
        tracking=True,
        copy=False,
    )

    name = fields.Char(
        string='Reference',
        compute='_compute_name',
        store=True,
        readonly=True
    )
    audit_id = fields.Many2one(
        'qaco.audit',
        string='Audit Engagement',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    planning_main_id = fields.Many2one(
        'qaco.planning.main',
        string='Planning Phase',
        ondelete='cascade'
    )
    client_id = fields.Many2one(
        'res.partner',
        string='Client Name',
        related='audit_id.client_id',
        readonly=True,
        store=True
    )

    # ===== Planning Completion Checklist =====
    checklist_p1_complete = fields.Boolean(string='P-1: Engagement Setup Complete')
    checklist_p2_complete = fields.Boolean(string='P-2: Entity Understanding Complete')
    checklist_p3_complete = fields.Boolean(string='P-3: Internal Controls Complete')
    checklist_p4_complete = fields.Boolean(string='P-4: Analytical Procedures Complete')
    checklist_p5_complete = fields.Boolean(string='P-5: Materiality Complete')
    checklist_p6_complete = fields.Boolean(string='P-6: Risk Assessment Complete')
    checklist_p7_complete = fields.Boolean(string='P-7: Fraud Risk Complete')
    checklist_p8_complete = fields.Boolean(string='P-8: Going Concern Complete')
    checklist_p9_complete = fields.Boolean(string='P-9: Laws & Regulations Complete')
    checklist_p10_complete = fields.Boolean(string='P-10: Related Parties Complete')
    checklist_p11_complete = fields.Boolean(string='P-11: Group Audit Complete')
    checklist_p12_complete = fields.Boolean(string='P-12: Audit Strategy Complete')

    all_tabs_complete = fields.Boolean(
        string='All P-Tabs Complete',
        compute='_compute_all_tabs_complete',
        store=True
    )

    # ===== Planning Review Notes =====
    manager_review_notes = fields.Html(
        string='Manager Review Notes',
        help='Manager\'s review comments on planning'
    )
    manager_review_complete = fields.Boolean(
        string='Manager Review Complete',
        tracking=True
    )
    manager_review_date = fields.Datetime(
        string='Manager Review Date'
    )
    manager_reviewer_id = fields.Many2one(
        'res.users',
        string='Manager Reviewer'
    )

    partner_review_notes = fields.Html(
        string='Partner Review Notes',
        help='Partner\'s review comments on planning'
    )
    partner_review_complete = fields.Boolean(
        string='Partner Review Complete',
        tracking=True
    )
    partner_review_date = fields.Datetime(
        string='Partner Review Date'
    )
    partner_reviewer_id = fields.Many2one(
        'res.users',
        string='Partner Reviewer'
    )

    # ===== EQCR (Engagement Quality Control Review) =====
    eqcr_required = fields.Boolean(
        string='EQCR Required',
        tracking=True,
        help='Is an Engagement Quality Control Review required per ISA 220/ISQM-1?'
    )
    eqcr_criteria = fields.Html(
        string='EQCR Criteria',
        help='Document the criteria for EQCR requirement'
    )
    eqcr_reviewer_id = fields.Many2one(
        'res.users',
        string='EQCR Reviewer',
        tracking=True
    )
    eqcr_review_date = fields.Datetime(
        string='EQCR Review Date'
    )
    eqcr_review_notes = fields.Html(
        string='EQCR Review Notes',
        help='EQCR reviewer\'s comments on planning phase'
    )
    eqcr_approval = fields.Boolean(
        string='EQCR Approved',
        tracking=True
    )
    eqcr_matters_raised = fields.Html(
        string='EQCR Matters Raised',
        help='Significant matters raised during EQCR'
    )
    eqcr_resolution = fields.Html(
        string='EQCR Resolution',
        help='Resolution of matters raised by EQCR'
    )

    # ===== Quality Standards Compliance =====
    icap_standards_compliant = fields.Boolean(
        string='ICAP Standards Compliance Verified',
        tracking=True
    )
    secp_requirements_addressed = fields.Boolean(
        string='SECP Requirements Addressed',
        tracking=True
    )
    aob_guidelines_considered = fields.Boolean(
        string='AOB Guidelines Considered',
        tracking=True
    )
    isqm1_compliance = fields.Html(
        string='ISQM-1 Compliance Documentation'
    )

    # ===== Partner Sign-off =====
    partner_signoff = fields.Boolean(
        string='Partner Sign-off',
        tracking=True
    )
    partner_signoff_date = fields.Datetime(
        string='Partner Sign-off Date'
    )
    partner_signoff_user_id = fields.Many2one(
        'res.users',
        string='Partner Who Signed Off'
    )
    partner_signoff_notes = fields.Html(
        string='Partner Sign-off Notes'
    )

    # ===== Planning Lock =====
    planning_locked = fields.Boolean(
        string='Planning Locked',
        default=False,
        tracking=True,
        help='Once locked, planning cannot be modified without partner approval'
    )
    planning_locked_date = fields.Datetime(
        string='Planning Locked Date'
    )
    planning_locked_by_id = fields.Many2one(
        'res.users',
        string='Planning Locked By'
    )

    # ===== Outstanding Matters =====
    outstanding_matters = fields.Html(
        string='Outstanding Matters',
        help='Any matters requiring resolution before execution'
    )
    carryforward_issues = fields.Html(
        string='Carryforward Issues',
        help='Issues from prior year requiring attention'
    )

    # ===== APM (Audit Planning Memorandum) =====
    apm_generated = fields.Boolean(
        string='APM Generated',
        tracking=True
    )
    apm_generation_date = fields.Datetime(
        string='APM Generation Date'
    )
    apm_approved = fields.Boolean(
        string='APM Approved',
        tracking=True
    )

    # ===== Attachments =====
    apm_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p13_apm_rel',
        'p13_id',
        'attachment_id',
        string='Audit Planning Memorandum'
    )
    signoff_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p13_signoff_rel',
        'p13_id',
        'attachment_id',
        string='Sign-off Documentation'
    )
    eqcr_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p13_eqcr_rel',
        'p13_id',
        'attachment_id',
        string='EQCR Documentation'
    )

    # ===== Summary =====
    planning_approval_summary = fields.Html(
        string='Planning Approval Summary',
        help='Final planning review and approval summary'
    )
    isa_reference = fields.Char(
        string='ISA Reference',
        default='ISA 220/ISQM-1',
        readonly=True
    )

    # ===== Sign-off Fields =====
    senior_signed_user_id = fields.Many2one('res.users', string='Senior Completed By', tracking=True, copy=False, readonly=True)
    senior_signed_on = fields.Datetime(string='Senior Completed On', tracking=True, copy=False, readonly=True)
    manager_reviewed_user_id = fields.Many2one('res.users', string='Manager Reviewed By', tracking=True, copy=False, readonly=True)
    manager_reviewed_on = fields.Datetime(string='Manager Reviewed On', tracking=True, copy=False, readonly=True)
    partner_approved_user_id = fields.Many2one('res.users', string='Partner Approved By', tracking=True, copy=False, readonly=True)
    partner_approved_on = fields.Datetime(string='Partner Approved On', tracking=True, copy=False, readonly=True)
    reviewer_notes = fields.Html(string='Reviewer Notes')
    approval_notes = fields.Html(string='Approval Notes')

    _sql_constraints = [
        ('audit_unique', 'UNIQUE(audit_id)', 'Only one P-13 record per Audit Engagement is allowed.')
    ]

    @api.depends('audit_id', 'client_id')
    def _compute_name(self):
        for record in self:
            if record.client_id:
                record.name = f"P13-{record.client_id.name[:15]}"
            else:
                record.name = 'P-13: Planning Review'

    @api.depends(
        'checklist_p1_complete', 'checklist_p2_complete', 'checklist_p3_complete',
        'checklist_p4_complete', 'checklist_p5_complete', 'checklist_p6_complete',
        'checklist_p7_complete', 'checklist_p8_complete', 'checklist_p9_complete',
        'checklist_p10_complete', 'checklist_p11_complete', 'checklist_p12_complete'
    )
    def _compute_all_tabs_complete(self):
        for record in self:
            record.all_tabs_complete = all([
                record.checklist_p1_complete, record.checklist_p2_complete,
                record.checklist_p3_complete, record.checklist_p4_complete,
                record.checklist_p5_complete, record.checklist_p6_complete,
                record.checklist_p7_complete, record.checklist_p8_complete,
                record.checklist_p9_complete, record.checklist_p10_complete,
                record.checklist_p11_complete, record.checklist_p12_complete
            ])

    def action_refresh_checklist(self):
        """Refresh the completion checklist from P-tabs."""
        self.ensure_one()
        main = self.planning_main_id
        if main:
            self.checklist_p1_complete = main.p1_engagement_id.state == 'approved' if main.p1_engagement_id else False
            self.checklist_p2_complete = main.p2_entity_id.state == 'approved' if main.p2_entity_id else False
            self.checklist_p3_complete = main.p3_controls_id.state == 'approved' if main.p3_controls_id else False
            self.checklist_p4_complete = main.p4_analytics_id.state == 'approved' if main.p4_analytics_id else False
            self.checklist_p5_complete = main.p5_materiality_id.state == 'approved' if main.p5_materiality_id else False
            self.checklist_p6_complete = main.p6_risk_id.state == 'approved' if main.p6_risk_id else False
            self.checklist_p7_complete = main.p7_fraud_id.state == 'approved' if main.p7_fraud_id else False
            self.checklist_p8_complete = main.p8_going_concern_id.state == 'approved' if main.p8_going_concern_id else False
            self.checklist_p9_complete = main.p9_laws_id.state == 'approved' if main.p9_laws_id else False
            self.checklist_p10_complete = main.p10_related_parties_id.state == 'approved' if main.p10_related_parties_id else False
            self.checklist_p11_complete = main.p11_group_audit_id.state == 'approved' if main.p11_group_audit_id else False
            self.checklist_p12_complete = main.p12_strategy_id.state == 'approved' if main.p12_strategy_id else False

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
            raise UserError('Manager review must be completed before partner review.')
        self.partner_review_complete = True
        self.partner_review_date = fields.Datetime.now()
        self.partner_reviewer_id = self.env.user

    def action_partner_signoff(self):
        """Partner signs off on planning."""
        self.ensure_one()
        if not self.all_tabs_complete:
            raise UserError('All P-tabs must be approved before partner sign-off.')
        if not self.partner_review_complete:
            raise UserError('Partner review must be completed before sign-off.')
        if self.eqcr_required and not self.eqcr_approval:
            raise UserError('EQCR approval is required before partner sign-off.')
        self.partner_signoff = True
        self.partner_signoff_date = fields.Datetime.now()
        self.partner_signoff_user_id = self.env.user

    def action_lock_planning(self):
        """Lock planning phase."""
        self.ensure_one()
        if not self.partner_signoff:
            raise UserError('Partner sign-off is required before locking planning.')
        self.planning_locked = True
        self.planning_locked_date = fields.Datetime.now()
        self.planning_locked_by_id = self.env.user
        # Update main planning phase
        if self.planning_main_id:
            self.planning_main_id.is_planning_locked = True

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
            'type': 'ir.actions.act_url',
            'url': f'/report/pdf/qaco_planning_phase.report_audit_planning_memo/{self.planning_main_id.id if self.planning_main_id else self.id}',
            'target': 'new',
        }

    def action_eqcr_approve(self):
        """EQCR approves planning."""
        self.ensure_one()
        if not self.eqcr_reviewer_id:
            raise UserError('EQCR reviewer must be assigned.')
        self.eqcr_approval = True
        self.eqcr_review_date = fields.Datetime.now()

    def _validate_mandatory_fields(self):
        """Validate mandatory fields before completing P-13."""
        self.ensure_one()
        errors = []
        if not self.all_tabs_complete:
            errors.append('All P-tabs (P-1 to P-12) must be approved')
        if not self.manager_review_complete:
            errors.append('Manager review must be completed')
        if not self.partner_signoff:
            errors.append('Partner sign-off is required')
        if self.eqcr_required and not self.eqcr_approval:
            errors.append('EQCR approval is required')
        if not self.planning_approval_summary:
            errors.append('Planning approval summary is required')
        if errors:
            raise UserError('Cannot complete P-13. Missing requirements:\n• ' + '\n• '.join(errors))

    def action_start_work(self):
        for record in self:
            if record.state != 'not_started':
                raise UserError('Can only start work on tabs that are Not Started.')
            record.action_refresh_checklist()
            record.state = 'in_progress'

    def action_complete(self):
        for record in self:
            if record.state != 'in_progress':
                raise UserError('Can only complete tabs that are In Progress.')
            record._validate_mandatory_fields()
            record.senior_signed_user_id = self.env.user
            record.senior_signed_on = fields.Datetime.now()
            record.state = 'completed'

    def action_review(self):
        for record in self:
            if record.state != 'completed':
                raise UserError('Can only review tabs that are Completed.')
            record.manager_reviewed_user_id = self.env.user
            record.manager_reviewed_on = fields.Datetime.now()
            record.state = 'reviewed'

    def action_approve(self):
        for record in self:
            if record.state != 'reviewed':
                raise UserError('Can only approve tabs that have been Reviewed.')
            record.partner_approved_user_id = self.env.user
            record.partner_approved_on = fields.Datetime.now()
            record.state = 'approved'
            # Lock planning when P-13 is approved
            record.action_lock_planning()

    def action_send_back(self):
        for record in self:
            if record.state not in ['completed', 'reviewed']:
                raise UserError('Can only send back tabs that are Completed or Reviewed.')
            record.state = 'in_progress'

    def action_unlock(self):
        for record in self:
            if record.state != 'approved':
                raise UserError('Can only unlock Approved tabs.')
            record.partner_approved_user_id = False
            record.partner_approved_on = False
            record.state = 'reviewed'
            record.action_unlock_planning()
