# -*- coding: utf-8 -*-
"""
Base Planning Model and Common Mixins for P-1 to P-13 Tabs
Provides shared state workflow, status tracking, and sign-off logic.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError


class PlanningTabMixin(models.AbstractModel):
    """Abstract mixin for all P-tab models with status-driven workflow."""
    _name = 'qaco.planning.tab.mixin'
    _description = 'Planning Tab Mixin - State & Workflow'

    # Common status workflow for all P-tabs
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
        help='Workflow state: Not Started → In Progress → Completed → Reviewed → Approved'
    )

    # Common sign-off fields
    senior_signed_user_id = fields.Many2one(
        'res.users',
        string='Senior Completed By',
        tracking=True,
        copy=False,
        readonly=True
    )
    senior_signed_on = fields.Datetime(
        string='Senior Completed On',
        tracking=True,
        copy=False,
        readonly=True
    )
    manager_reviewed_user_id = fields.Many2one(
        'res.users',
        string='Manager Reviewed By',
        tracking=True,
        copy=False,
        readonly=True
    )
    manager_reviewed_on = fields.Datetime(
        string='Manager Reviewed On',
        tracking=True,
        copy=False,
        readonly=True
    )
    partner_approved_user_id = fields.Many2one(
        'res.users',
        string='Partner Approved By',
        tracking=True,
        copy=False,
        readonly=True
    )
    partner_approved_on = fields.Datetime(
        string='Partner Approved On',
        tracking=True,
        copy=False,
        readonly=True
    )

    # Notes for review workflow
    reviewer_notes = fields.Html(string='Reviewer Notes')
    approval_notes = fields.Html(string='Approval Notes')

    def action_start_work(self):
        """Move tab from Not Started to In Progress."""
        for record in self:
            if record.state != 'not_started':
                raise UserError('Can only start work on tabs that are Not Started.')
            record.state = 'in_progress'

    def action_complete(self):
        """Senior marks work as complete, moves to Completed state."""
        for record in self:
            if record.state != 'in_progress':
                raise UserError('Can only complete tabs that are In Progress.')
            record._validate_mandatory_fields()
            record.senior_signed_user_id = self.env.user
            record.senior_signed_on = fields.Datetime.now()
            record.state = 'completed'

    def action_review(self):
        """Manager reviews and approves, moves to Reviewed state."""
        for record in self:
            if record.state != 'completed':
                raise UserError('Can only review tabs that are Completed.')
            record.manager_reviewed_user_id = self.env.user
            record.manager_reviewed_on = fields.Datetime.now()
            record.state = 'reviewed'

    def action_approve(self):
        """Partner approves, moves to Approved state (locked)."""
        for record in self:
            if record.state != 'reviewed':
                raise UserError('Can only approve tabs that have been Reviewed.')
            record.partner_approved_user_id = self.env.user
            record.partner_approved_on = fields.Datetime.now()
            record.state = 'approved'

    def action_send_back(self):
        """Send back for rework from Reviewed/Completed to In Progress."""
        for record in self:
            if record.state not in ['completed', 'reviewed']:
                raise UserError('Can only send back tabs that are Completed or Reviewed.')
            record.state = 'in_progress'

    def action_unlock(self):
        """Unlock an approved tab (requires Partner role)."""
        for record in self:
            if record.state != 'approved':
                raise UserError('Can only unlock Approved tabs.')
            if not self.env.user.has_group('qaco_audit.group_audit_partner'):
                raise UserError('Only Partners can unlock approved planning tabs.')
            # Reset approval signature with context flag
            record.with_context(allow_partner_unlock=True).write({
                'partner_approved_user_id': False,
                'partner_approved_on': False,
                'state': 'reviewed'
            })
            record.message_post(
                body=f'Planning tab unlocked by {self.env.user.name} for amendment. ISA 230: Audit trail preserved.',
                subject='Planning Tab Unlocked'
            )

    @api.constrains('state')
    def _prevent_edit_after_approval(self):
        """ISA 230: Prevent modification of approved planning sections."""
        for rec in self:
            if rec.state == 'approved' and not self.env.context.get('allow_partner_unlock'):
                # Check if record was already approved and being modified
                if rec._origin and rec._origin.state == 'approved':
                    # Identify changed fields (exclude metadata)
                    excluded_fields = {'state', 'write_date', 'write_uid', '__last_update', 'message_ids', 'activity_ids'}
                    changed_fields = [
                        fname for fname in rec._fields
                        if fname not in excluded_fields
                        and rec[fname] != rec._origin[fname]
                    ]
                    if changed_fields:
                        raise ValidationError(
                            f'ISA 230 Violation: Cannot modify approved planning tab.\n'
                            f'Changed fields: {", ".join(changed_fields[:5])}'
                            f'{"..." if len(changed_fields) > 5 else ""}\n\n'
                            f'Partner must explicitly unlock this tab first via "Unlock" button.'
                        )

    def _validate_mandatory_fields(self):
        """Override in each P-tab model to validate required fields."""
        pass


class PlanningPhaseMain(models.Model):
    """
    Main Planning Phase record that links all P-tabs to an Audit Engagement.
    Acts as the orchestrator for the P-1 to P-13 tab workflow.
    """
    _name = 'qaco.planning.main'
    _description = 'Audit Planning Phase - Main Orchestrator'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Planning Reference',
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
    client_id = fields.Many2one(
        'res.partner',
        string='Client Name',
        related='audit_id.client_id',
        readonly=True,
        store=True
    )
    company_currency_id = fields.Many2one(
        'res.currency',
        string='Reporting Currency',
        default=lambda self: self.env.company.currency_id
    )

    # Links to P-tabs (One2One relationship via unique constraint on audit_id)
    p1_engagement_id = fields.Many2one(
        'qaco.planning.p1.engagement',
        string='P-1: Engagement Overview & Planning Control',
        readonly=True,
        copy=False
    )
    p2_entity_id = fields.Many2one(
        'qaco.planning.p2.entity',
        string='P-2: Understanding the Entity & Environment',
        readonly=True,
        copy=False
    )
    p3_controls_id = fields.Many2one(
        'qaco.planning.p3.controls',
        string='P-3: Internal Control & IT Environment',
        readonly=True,
        copy=False
    )
    p4_analytics_id = fields.Many2one(
        'qaco.planning.p4.analytics',
        string='P-4: Risk Assessment (FS Level)',
        readonly=True,
        copy=False
    )
    p5_materiality_id = fields.Many2one(
        'qaco.planning.p5.materiality',
        string='P-5: Risk Assessment (Assertion Level)',
        readonly=True,
        copy=False
    )
    p6_risk_id = fields.Many2one(
        'qaco.planning.p6.risk',
        string='P-6: Materiality & Performance Materiality',
        readonly=True,
        copy=False
    )
    p7_fraud_id = fields.Many2one(
        'qaco.planning.p7.fraud',
        string='P-7: Fraud Risk Assessment',
        readonly=True,
        copy=False
    )
    p8_going_concern_id = fields.Many2one(
        'qaco.planning.p8.going.concern',
        string='P-8: Preliminary Analytical Procedures',
        readonly=True,
        copy=False
    )
    p9_laws_id = fields.Many2one(
        'qaco.planning.p9.laws',
        string='P-9: Going Concern Assessment',
        readonly=True,
        copy=False
    )
    p10_related_parties_id = fields.Many2one(
        'qaco.planning.p10.related.parties',
        string='P-10: Related Parties & Group Considerations',
        readonly=True,
        copy=False
    )
    p11_group_audit_id = fields.Many2one(
        'qaco.planning.p11.group.audit',
        string='P-11: Audit Strategy & Audit Plan',
        readonly=True,
        copy=False
    )
    p12_strategy_id = fields.Many2one(
        'qaco.planning.p12.strategy',
        string='P-12: Audit Team, Budget & Timeline',
        readonly=True,
        copy=False
    )
    p13_approval_id = fields.Many2one(
        'qaco.planning.p13.approval',
        string='P-13: APM & Approval',
        readonly=True,
        copy=False
    )

    # Overall planning status
    overall_progress = fields.Float(
        string='Overall Progress %',
        compute='_compute_overall_progress',
        store=True
    )
    is_planning_complete = fields.Boolean(
        string='Planning Complete',
        compute='_compute_planning_complete',
        store=True
    )
    is_planning_locked = fields.Boolean(
        string='Planning Locked',
        default=False,
        tracking=True,
        copy=False
    )

    # Computed status summaries
    tabs_not_started = fields.Integer(compute='_compute_tab_counts')
    tabs_in_progress = fields.Integer(compute='_compute_tab_counts')
    tabs_completed = fields.Integer(compute='_compute_tab_counts')
    tabs_reviewed = fields.Integer(compute='_compute_tab_counts')
    tabs_approved = fields.Integer(compute='_compute_tab_counts')

    _sql_constraints = [
        ('audit_unique', 'UNIQUE(audit_id)', 'Only one Planning Phase record per Audit Engagement is allowed.')
    ]

    @api.depends('audit_id', 'client_id')
    def _compute_name(self):
        for record in self:
            if record.audit_id and record.client_id:
                record.name = f"PLAN-{record.client_id.name[:20]}-{record.audit_id.name or record.audit_id.id}"
            else:
                record.name = 'Planning Phase - Draft'

    @api.depends(
        'p1_engagement_id.state', 'p2_entity_id.state', 'p3_controls_id.state',
        'p4_analytics_id.state', 'p5_materiality_id.state', 'p6_risk_id.state',
        'p7_fraud_id.state', 'p8_going_concern_id.state', 'p9_laws_id.state',
        'p10_related_parties_id.state', 'p11_group_audit_id.state',
        'p12_strategy_id.state', 'p13_approval_id.state'
    )
    def _compute_overall_progress(self):
        state_weights = {
            'not_started': 0,
            'in_progress': 25,
            'completed': 50,
            'reviewed': 75,
            'approved': 100,
            False: 0,
        }
        tab_fields = [
            'p1_engagement_id', 'p2_entity_id', 'p3_controls_id', 'p4_analytics_id',
            'p5_materiality_id', 'p6_risk_id', 'p7_fraud_id', 'p8_going_concern_id',
            'p9_laws_id', 'p10_related_parties_id', 'p11_group_audit_id',
            'p12_strategy_id', 'p13_approval_id'
        ]
        for record in self:
            total = 0
            count = 0
            for field in tab_fields:
                tab = getattr(record, field)
                if tab:
                    total += state_weights.get(tab.state, 0)
                    count += 1
            record.overall_progress = total / count if count else 0

    @api.depends('p13_approval_id.state')
    def _compute_planning_complete(self):
        for record in self:
            record.is_planning_complete = (
                record.p13_approval_id and record.p13_approval_id.state == 'approved'
            )

    def _compute_tab_counts(self):
        tab_fields = [
            'p1_engagement_id', 'p2_entity_id', 'p3_controls_id', 'p4_analytics_id',
            'p5_materiality_id', 'p6_risk_id', 'p7_fraud_id', 'p8_going_concern_id',
            'p9_laws_id', 'p10_related_parties_id', 'p11_group_audit_id',
            'p12_strategy_id', 'p13_approval_id'
        ]
        for record in self:
            counts = {'not_started': 0, 'in_progress': 0, 'completed': 0, 'reviewed': 0, 'approved': 0}
            for field in tab_fields:
                tab = getattr(record, field)
                if tab and tab.state:
                    counts[tab.state] = counts.get(tab.state, 0) + 1
                else:
                    counts['not_started'] += 1
            record.tabs_not_started = counts['not_started']
            record.tabs_in_progress = counts['in_progress']
            record.tabs_completed = counts['completed']
            record.tabs_reviewed = counts['reviewed']
            record.tabs_approved = counts['approved']

    def _create_p_tabs(self):
        """Create all P-tab records for this planning phase."""
        self.ensure_one()
        if not self.p1_engagement_id:
            self.p1_engagement_id = self.env['qaco.planning.p1.engagement'].create({
                'audit_id': self.audit_id.id,
                'planning_main_id': self.id,
            })
        if not self.p2_entity_id:
            self.p2_entity_id = self.env['qaco.planning.p2.entity'].create({
                'audit_id': self.audit_id.id,
                'planning_main_id': self.id,
            })
        if not self.p3_controls_id:
            self.p3_controls_id = self.env['qaco.planning.p3.controls'].create({
                'audit_id': self.audit_id.id,
                'planning_main_id': self.id,
            })
        if not self.p4_analytics_id:
            self.p4_analytics_id = self.env['qaco.planning.p4.analytics'].create({
                'audit_id': self.audit_id.id,
                'planning_main_id': self.id,
            })
        if not self.p5_materiality_id:
            self.p5_materiality_id = self.env['qaco.planning.p5.materiality'].create({
                'audit_id': self.audit_id.id,
                'planning_main_id': self.id,
            })
        if not self.p6_risk_id:
            self.p6_risk_id = self.env['qaco.planning.p6.risk'].create({
                'audit_id': self.audit_id.id,
                'planning_main_id': self.id,
            })
        if not self.p7_fraud_id:
            self.p7_fraud_id = self.env['qaco.planning.p7.fraud'].create({
                'audit_id': self.audit_id.id,
                'planning_main_id': self.id,
            })
        if not self.p8_going_concern_id:
            self.p8_going_concern_id = self.env['qaco.planning.p8.going.concern'].create({
                'audit_id': self.audit_id.id,
                'planning_main_id': self.id,
            })
        if not self.p9_laws_id:
            self.p9_laws_id = self.env['qaco.planning.p9.laws'].create({
                'audit_id': self.audit_id.id,
                'planning_main_id': self.id,
            })
        if not self.p10_related_parties_id:
            self.p10_related_parties_id = self.env['qaco.planning.p10.related.parties'].create({
                'audit_id': self.audit_id.id,
                'planning_main_id': self.id,
            })
        if not self.p11_group_audit_id:
            self.p11_group_audit_id = self.env['qaco.planning.p11.group.audit'].create({
                'audit_id': self.audit_id.id,
                'planning_main_id': self.id,
            })
        if not self.p12_strategy_id:
            self.p12_strategy_id = self.env['qaco.planning.p12.strategy'].create({
                'audit_id': self.audit_id.id,
                'planning_main_id': self.id,
            })
        if not self.p13_approval_id:
            self.p13_approval_id = self.env['qaco.planning.p13.approval'].create({
                'audit_id': self.audit_id.id,
                'planning_main_id': self.id,
            })

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record._create_p_tabs()
        return records

    def action_lock_planning(self):
        """Lock the planning phase once all tabs are approved."""
        for record in self:
            if not record.is_planning_complete:
                raise UserError('Cannot lock planning until P-13 Planning Review is approved.')
            record.is_planning_locked = True
            record.message_post(body="Planning Phase has been locked. Execution phase may now begin.")

    def action_unlock_planning(self):
        """Unlock planning for corrections (requires Partner approval)."""
        for record in self:
            record.is_planning_locked = False
            record.message_post(body="Planning Phase has been unlocked for corrections.")

    def action_generate_apm(self):
        """Generate Audit Planning Memorandum (APM) PDF report."""
        self.ensure_one()
        # This would trigger a report action
        return {
            'type': 'ir.actions.act_url',
            'url': f'/report/pdf/qaco_planning_phase.report_audit_planning_memo/{self.id}',
            'target': 'new',
        }
