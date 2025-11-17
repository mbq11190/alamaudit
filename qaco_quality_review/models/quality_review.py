# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class QacoQualityReview(models.Model):
    _name = 'qaco.quality.review'
    _description = 'Quality Review and EQCR'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    # Basic Information
    name = fields.Char(
        string='Quality Review Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New',
        tracking=True
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
        string='Client',
        related='audit_id.client_id',
        store=True,
        readonly=True
    )
    deliverables_id = fields.Many2one(
        'qaco.deliverables',
        string='Deliverables',
        tracking=True
    )
    review_date = fields.Date(
        string='Review Date',
        default=fields.Date.context_today,
        required=True,
        tracking=True
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('findings_identified', 'Findings Identified'),
        ('remediation', 'Remediation'),
        ('final_review', 'Final Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', required=True, tracking=True)

    # Review Type
    review_type = fields.Selection([
        ('eqcr', 'Engagement Quality Control Review (EQCR)'),
        ('hot_review', 'Hot Review (Concurrent)'),
        ('cold_review', 'Cold Review (Post-Completion)'),
        ('peer_review', 'Peer Review'),
        ('compliance_review', 'Compliance Review'),
        ('technical_review', 'Technical Review'),
    ], string='Review Type', required=True, tracking=True)
    review_scope = fields.Text(
        string='Review Scope',
        tracking=True
    )
    
    # Review Team
    lead_reviewer_id = fields.Many2one(
        'res.users',
        string='Lead Reviewer',
        required=True,
        tracking=True,
        domain=lambda self: [('groups_id', 'in', [self.env.ref('qaco_audit.group_audit_partner').id])]
    )
    reviewer_ids = fields.Many2many(
        'res.users',
        'quality_review_reviewer_rel',
        'review_id',
        'user_id',
        string='Review Team',
        tracking=True
    )
    
    # EQCR Specific Fields
    is_eqcr_required = fields.Boolean(
        string='EQCR Required',
        default=False,
        tracking=True,
        help='Required for listed entities and public interest entities'
    )
    eqcr_reviewer_id = fields.Many2one(
        'res.users',
        string='EQCR Reviewer',
        tracking=True,
        domain=lambda self: [('groups_id', 'in', [self.env.ref('qaco_audit.group_audit_partner').id])],
        help='Must be independent partner not involved in engagement'
    )
    eqcr_independence_confirmed = fields.Boolean(
        string='EQCR Independence Confirmed',
        default=False,
        tracking=True
    )
    eqcr_completion_date = fields.Date(
        string='EQCR Completion Date',
        tracking=True
    )
    
    # Review Areas
    planning_review_completed = fields.Boolean(
        string='Planning Review Completed',
        default=False,
        tracking=True
    )
    execution_review_completed = fields.Boolean(
        string='Execution Review Completed',
        default=False,
        tracking=True
    )
    finalisation_review_completed = fields.Boolean(
        string='Finalisation Review Completed',
        default=False,
        tracking=True
    )
    documentation_review_completed = fields.Boolean(
        string='Documentation Review Completed',
        default=False,
        tracking=True
    )
    
    # Checklist
    checklist_item_ids = fields.One2many(
        'qaco.quality.checklist.item',
        'quality_review_id',
        string='Quality Checklist Items',
        tracking=True
    )
    checklist_completion_percentage = fields.Float(
        string='Checklist Completion %',
        compute='_compute_checklist_completion',
        store=True
    )
    
    # Findings
    finding_ids = fields.One2many(
        'qaco.quality.finding',
        'quality_review_id',
        string='Quality Findings',
        tracking=True
    )
    findings_count = fields.Integer(
        string='Findings Count',
        compute='_compute_findings_count',
        store=True
    )
    critical_findings_count = fields.Integer(
        string='Critical Findings',
        compute='_compute_critical_findings_count',
        store=True
    )
    open_findings_count = fields.Integer(
        string='Open Findings',
        compute='_compute_open_findings_count',
        store=True
    )
    
    # Overall Assessment
    overall_quality_rating = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('satisfactory_with_improvements', 'Satisfactory with Improvements'),
        ('needs_improvement', 'Needs Improvement'),
        ('unsatisfactory', 'Unsatisfactory'),
    ], string='Overall Quality Rating', tracking=True)
    professional_standards_compliance = fields.Selection([
        ('compliant', 'Compliant'),
        ('minor_deviations', 'Minor Deviations'),
        ('significant_deviations', 'Significant Deviations'),
        ('non_compliant', 'Non-Compliant'),
    ], string='Professional Standards Compliance', tracking=True)
    file_completeness_rating = fields.Selection([
        ('complete', 'Complete'),
        ('substantially_complete', 'Substantially Complete'),
        ('incomplete', 'Incomplete'),
    ], string='File Completeness', tracking=True)
    
    # Review Completion
    review_hours = fields.Float(
        string='Review Hours',
        tracking=True
    )
    review_start_date = fields.Date(
        string='Review Start Date',
        tracking=True
    )
    review_completion_date = fields.Date(
        string='Review Completion Date',
        tracking=True
    )
    
    # Sign-off
    reviewer_signoff = fields.Boolean(
        string='Reviewer Sign-off',
        default=False,
        tracking=True
    )
    reviewer_signoff_date = fields.Date(
        string='Reviewer Sign-off Date',
        tracking=True
    )
    quality_partner_signoff = fields.Boolean(
        string='Quality Partner Sign-off',
        default=False,
        tracking=True
    )
    quality_partner_signoff_date = fields.Date(
        string='Quality Partner Sign-off Date',
        tracking=True
    )
    
    # Recommendations and Notes
    key_strengths = fields.Text(
        string='Key Strengths',
        tracking=True
    )
    areas_for_improvement = fields.Text(
        string='Areas for Improvement',
        tracking=True
    )
    recommendations = fields.Text(
        string='Recommendations',
        tracking=True
    )
    notes = fields.Html(
        string='Notes',
        tracking=True
    )

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('qaco.quality.review') or 'New'
        return super(QacoQualityReview, self).create(vals)

    @api.depends('checklist_item_ids', 'checklist_item_ids.completed')
    def _compute_checklist_completion(self):
        for record in self:
            total_items = len(record.checklist_item_ids)
            if total_items > 0:
                completed_items = len(record.checklist_item_ids.filtered(lambda x: x.completed))
                record.checklist_completion_percentage = (completed_items / total_items) * 100
            else:
                record.checklist_completion_percentage = 0.0

    @api.depends('finding_ids')
    def _compute_findings_count(self):
        for record in self:
            record.findings_count = len(record.finding_ids)

    @api.depends('finding_ids', 'finding_ids.severity')
    def _compute_critical_findings_count(self):
        for record in self:
            record.critical_findings_count = len(
                record.finding_ids.filtered(lambda x: x.severity == 'critical')
            )

    @api.depends('finding_ids', 'finding_ids.state')
    def _compute_open_findings_count(self):
        for record in self:
            record.open_findings_count = len(
                record.finding_ids.filtered(lambda x: x.state in ('open', 'in_progress'))
            )

    def action_start_review(self):
        self.ensure_one()
        self.write({
            'state': 'in_progress',
            'review_start_date': fields.Date.context_today(self)
        })

    def action_identify_findings(self):
        self.ensure_one()
        if not self.finding_ids:
            raise ValidationError('Please add at least one finding before proceeding.')
        self.write({'state': 'findings_identified'})

    def action_start_remediation(self):
        self.ensure_one()
        self.write({'state': 'remediation'})

    def action_final_review(self):
        self.ensure_one()
        if self.open_findings_count > 0:
            raise ValidationError('All findings must be resolved before final review.')
        self.write({'state': 'final_review'})

    def action_approve(self):
        self.ensure_one()
        if self.checklist_completion_percentage < 100:
            raise ValidationError('All checklist items must be completed before approval.')
        if self.open_findings_count > 0:
            raise ValidationError('All findings must be resolved before approval.')
        self.write({
            'state': 'approved',
            'review_completion_date': fields.Date.context_today(self)
        })

    def action_reject(self):
        self.ensure_one()
        self.write({'state': 'rejected'})

    def action_reset_to_draft(self):
        self.ensure_one()
        self.write({'state': 'draft'})
