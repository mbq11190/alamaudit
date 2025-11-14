from odoo import models, fields, api


class QacoAuditExtend(models.Model):
    _inherit = 'qaco.audit'

    planning_phase_id = fields.Many2one('qaco.planning.phase', string='Planning Phase', 
                                        compute='_compute_planning_phase', store=False)
    
    def _compute_planning_phase(self):
        for record in self:
            planning = self.env['qaco.planning.phase'].search([('audit_id', '=', record.id)], limit=1)
            record.planning_phase_id = planning.id if planning else False
    
    def action_create_planning_phase(self):
        """Create planning phase if it doesn't exist"""
        self.ensure_one()
        planning = self.env['qaco.planning.phase'].search([('audit_id', '=', self.id)], limit=1)
        if not planning:
            planning = self.env['qaco.planning.phase'].create({
                'audit_id': self.id,
            })
        # Recompute to update the field
        self._compute_planning_phase()
        return True
