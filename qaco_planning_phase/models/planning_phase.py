from odoo import models, fields, api


class PlanningPhase(models.Model):
    _name = 'qaco.planning.phase'
    _description = 'Planning Phase Notebook'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, 
                       default=lambda self: 'New', tracking=True)
    audit_id = fields.Many2one('qaco.audit', string='Audit Reference', 
                               required=True, ondelete='cascade', tracking=True)
    client_id = fields.Many2one(related='audit_id.client_id', string='Client', 
                                store=True, readonly=True)
    
    # Planning Fields
    industry_sector_id = fields.Many2one('planning.industry.sector', 
                                         string='Client Industry & Sector', 
                                         required=True, tracking=True)
    
    # System Fields
    active = fields.Boolean(default=True, tracking=True)
    create_date = fields.Datetime(string='Created On', readonly=True)
    write_date = fields.Datetime(string='Last Updated', readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('qaco.planning.phase') or 'New'
        return super(PlanningPhase, self).create(vals)

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.name} - {record.client_id.name if record.client_id else 'No Client'}"
            result.append((record.id, name))
        return result
