from odoo import models, fields, api


class PlanningPhase(models.Model):
    _name = 'qaco.planning.phase'
    _description = 'Planning Phase'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Link to Audit
    audit_id = fields.Many2one('qaco.audit', string='Audit Reference', 
                               required=True, ondelete='cascade', tracking=True)
    client_id = fields.Many2one(related='audit_id.client_id', string='Client', 
                                store=True, readonly=True)
    
    # ==================
    # Client & Industry Information
    # ==================
    industry_sector_id = fields.Many2one('planning.industry.sector', 
                                         string='Client Industry & Sector', 
                                         tracking=True)
    business_nature = fields.Text(string='Nature of Business', tracking=True)
    key_personnel = fields.Text(string='Key Client Personnel', tracking=True)
    
    # ==================
    # Engagement Information
    # ==================
    engagement_type = fields.Selection([
        ('statutory', 'Statutory Audit'),
        ('internal', 'Internal Audit'),
        ('special', 'Special Purpose Audit'),
        ('review', 'Review Engagement'),
        ('agreed_procedures', 'Agreed Upon Procedures'),
    ], string='Engagement Type', tracking=True)
    
    audit_scope = fields.Text(string='Audit Scope & Objectives', tracking=True)
    reporting_framework = fields.Selection([
        ('ifrs', 'IFRS'),
        ('ifrs_sme', 'IFRS for SMEs'),
        ('local_gaap', 'Local GAAP'),
        ('other', 'Other'),
    ], string='Reporting Framework', tracking=True)
    
    # ==================
    # Risk Assessment
    # ==================
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
    key_risk_areas = fields.Text(string='Key Risk Areas Identified', tracking=True)
    
    # ==================
    # Materiality
    # ==================
    overall_materiality = fields.Monetary(string='Overall Materiality', 
                                          currency_field='currency_id', tracking=True)
    performance_materiality = fields.Monetary(string='Performance Materiality', 
                                              currency_field='currency_id', tracking=True)
    trivial_threshold = fields.Monetary(string='Trivial Threshold', 
                                        currency_field='currency_id', tracking=True)
    materiality_basis = fields.Selection([
        ('revenue', 'Revenue'),
        ('assets', 'Total Assets'),
        ('equity', 'Equity'),
        ('expenses', 'Total Expenses'),
        ('other', 'Other'),
    ], string='Materiality Basis', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                  default=lambda self: self.env.company.currency_id)
    
    # ==================
    # Planning Checklists
    # ==================
    engagement_letter_signed = fields.Boolean(string='Engagement Letter Signed', tracking=True)
    independence_confirmed = fields.Boolean(string='Independence Confirmed', tracking=True)
    previous_auditor_communication = fields.Boolean(string='Previous Auditor Communication', tracking=True)
    understanding_entity_obtained = fields.Boolean(string='Understanding of Entity Obtained', tracking=True)
    internal_controls_documented = fields.Boolean(string='Internal Controls Documented', tracking=True)
    analytical_procedures_performed = fields.Boolean(string='Analytical Procedures Performed', tracking=True)
    
    # ==================
    # Team & Timeline
    # ==================
    planning_start_date = fields.Date(string='Planning Start Date', tracking=True)
    planning_end_date = fields.Date(string='Planning End Date', tracking=True)
    fieldwork_start_date = fields.Date(string='Fieldwork Start Date', tracking=True)
    fieldwork_end_date = fields.Date(string='Fieldwork End Date', tracking=True)
    estimated_hours = fields.Float(string='Estimated Hours', tracking=True)
    
    # ==================
    # Documents & Notes
    # ==================
    planning_notes = fields.Html(string='Planning Notes')
    planning_attachments = fields.Many2many('ir.attachment', 
                                           'planning_phase_attachment_rel',
                                           'planning_id', 'attachment_id',
                                           string='Planning Documents')
    
    # ==================
    # Status
    # ==================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
    ], string='Status', default='draft', tracking=True)
    
    # System Fields
    active = fields.Boolean(default=True, tracking=True)
    create_date = fields.Datetime(string='Created On', readonly=True)
    write_date = fields.Datetime(string='Last Updated', readonly=True)

    def action_start_planning(self):
        self.write({'state': 'in_progress'})
    
    def action_submit_review(self):
        self.write({'state': 'review'})
    
    def action_approve(self):
        self.write({'state': 'approved'})
    
    def action_reset_draft(self):
        self.write({'state': 'draft'})
