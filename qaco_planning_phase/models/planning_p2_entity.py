# -*- coding: utf-8 -*-
"""
P-2: Understanding the Entity & Environment
Standard: ISA 315
Purpose: Obtain understanding of the entity, its environment, and business model.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError


class PlanningP2Entity(models.Model):
    """P-2: Understanding the Entity & Environment (ISA 315)"""
    _name = 'qaco.planning.p2.entity'
    _description = 'P-2: Understanding the Entity & Environment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    TAB_STATE = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
    ]

    INDUSTRY_TYPES = [
        ('manufacturing', 'Manufacturing'),
        ('trading', 'Trading'),
        ('services', 'Services'),
        ('financial', 'Financial Services'),
        ('insurance', 'Insurance'),
        ('nfbc', 'NFBC'),
        ('public_sector', 'Public Sector Entity'),
        ('sme', 'SME'),
        ('other', 'Other'),
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
        index=True,
        tracking=True
    )
    planning_main_id = fields.Many2one(
        'qaco.planning.main',
        string='Planning Phase',
        ondelete='cascade',
        index=True
    )
    client_id = fields.Many2one(
        'res.partner',
        string='Client Name',
        related='audit_id.client_id',
        readonly=True,
        store=True
    )

    # ===== Nature of Business =====
    nature_of_business = fields.Html(
        string='Nature of Business',
        help='Describe the entity\'s principal business activities'
    )
    principal_activities = fields.Html(
        string='Principal Activities'
    )
    products_services = fields.Html(
        string='Products and Services'
    )
    market_position = fields.Html(
        string='Market Position & Competition'
    )

    # ===== Ownership & Governance =====
    ownership_structure = fields.Html(
        string='Ownership Structure',
        help='Major shareholders, beneficial ownership'
    )
    governance_structure = fields.Html(
        string='Governance Structure',
        help='Board composition, audit committee, key management'
    )
    key_management = fields.Html(
        string='Key Management Personnel'
    )
    management_philosophy = fields.Html(
        string='Management Philosophy & Operating Style'
    )
    board_oversight = fields.Html(
        string='Board Oversight of Financial Reporting'
    )

    # ===== Industry & Economic Factors =====
    industry_id = fields.Many2one(
        'qaco.industry',
        string='Industry Classification',
        tracking=True
    )
    industry_type = fields.Selection(
        INDUSTRY_TYPES,
        string='Industry Sector',
        default='other'
    )
    industry_conditions = fields.Html(
        string='Industry Conditions',
        help='Market conditions, competition, demand, cycles'
    )
    economic_conditions = fields.Html(
        string='Economic Conditions',
        help='Interest rates, inflation, currency, economic policy'
    )
    regulatory_environment = fields.Html(
        string='Regulatory Environment',
        help='Industry-specific regulations and their impact'
    )
    technology_environment = fields.Html(
        string='Technology Environment',
        help='Technology changes affecting the entity'
    )

    # ===== Business Model & Revenue =====
    business_model = fields.Html(
        string='Business Model',
        help='How the entity creates, delivers, and captures value'
    )
    revenue_streams = fields.Html(
        string='Revenue Streams',
        help='Principal sources of revenue and key customers'
    )
    cost_structure = fields.Html(
        string='Cost Structure',
        help='Major cost components and behavior'
    )
    key_contracts = fields.Html(
        string='Key Contractual Arrangements'
    )
    supply_chain = fields.Html(
        string='Supply Chain & Key Suppliers'
    )

    # ===== Organizational Structure =====
    organizational_structure = fields.Html(
        string='Organizational Structure',
        help='Divisions, subsidiaries, locations'
    )
    operational_locations = fields.Html(
        string='Operational Locations',
        help='Geographic locations and branches'
    )
    key_processes = fields.Html(
        string='Key Business Processes',
        help='Critical operational processes'
    )
    outsourced_functions = fields.Html(
        string='Outsourced Functions',
        help='Functions outsourced to service organizations'
    )

    # ===== IT Environment Overview =====
    it_environment_overview = fields.Html(
        string='IT Environment Overview',
        help='General IT infrastructure and systems used'
    )
    key_applications = fields.Html(
        string='Key Applications',
        help='ERP, accounting software, and critical applications'
    )
    it_complexity = fields.Selection([
        ('simple', 'Simple'),
        ('moderate', 'Moderate'),
        ('complex', 'Complex'),
    ], string='IT Complexity', tracking=True)

    # ===== Applicable Regulators =====
    applicable_regulators = fields.Many2many(
        'qaco.regulator',
        'qaco_p2_regulators_rel',
        'p2_id',
        'regulator_id',
        string='Applicable Regulators'
    )

    # ===== Attachments =====
    organogram_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p2_organogram_rel',
        'p2_id',
        'attachment_id',
        string='Organogram Files'
    )
    process_flow_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p2_process_flow_rel',
        'p2_id',
        'attachment_id',
        string='Process Flowcharts'
    )
    other_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p2_other_rel',
        'p2_id',
        'attachment_id',
        string='Other Supporting Documents'
    )

    # ===== Summary Outputs =====
    entity_understanding_summary = fields.Html(
        string='Entity Understanding Summary',
        help='Consolidated summary of entity understanding per ISA 315'
    )
    isa_reference = fields.Char(
        string='ISA Reference',
        default='ISA 315',
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
        ('audit_unique', 'UNIQUE(audit_id)', 'Only one P-2 record per Audit Engagement is allowed.')
    ]

    @api.depends('audit_id', 'client_id')
    def _compute_name(self):
        for record in self:
            if record.client_id:
                record.name = f"P2-{record.client_id.name[:15]}"
            else:
                record.name = 'P-2: Entity Understanding'

    def _validate_mandatory_fields(self):
        """Validate mandatory fields before completing P-2."""
        self.ensure_one()
        errors = []
        if not self.nature_of_business:
            errors.append('Nature of business must be documented')
        if not self.industry_type:
            errors.append('Industry sector must be selected')
        if not self.business_model:
            errors.append('Business model must be documented')
        if not self.governance_structure:
            errors.append('Governance structure must be documented')
        if not self.entity_understanding_summary:
            errors.append('Entity understanding summary is required')
        if errors:
            raise UserError('Cannot complete P-2. Missing requirements:\n• ' + '\n• '.join(errors))

    def action_start_work(self):
        for record in self:
            if record.state != 'not_started':
                raise UserError('Can only start work on tabs that are Not Started.')
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
