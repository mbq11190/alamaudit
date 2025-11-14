from odoo import models, fields, api


class QacoAuditExtend(models.Model):
    _inherit = 'qaco.audit'

    execution_phase_id = fields.Many2one('qaco.execution.phase', string='Execution Phase', 
                                        compute='_compute_execution_phase', store=False)
    execution_state = fields.Selection([
        ('draft', 'Draft'),
        ('fieldwork', 'Fieldwork'),
        ('testing', 'Testing'),
        ('review', 'Review'),
        ('completed', 'Completed'),
        ('not_started', 'Not Started')
    ], string='Execution Status', compute='_compute_execution_phase', store=False)
    
    def _compute_execution_phase(self):
        for record in self:
            execution = self.env['qaco.execution.phase'].search([('audit_id', '=', record.id)], limit=1)
            record.execution_phase_id = execution.id if execution else False
            record.execution_state = execution.state if execution else 'not_started'
    
    def action_open_execution_phase(self):
        """Open execution phase form or create if doesn't exist"""
        self.ensure_one()
        execution = self.env['qaco.execution.phase'].search([('audit_id', '=', self.id)], limit=1)
        
        if not execution:
            # Create new execution phase
            execution = self.env['qaco.execution.phase'].create({
                'audit_id': self.id,
            })
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Execution Phase',
            'res_model': 'qaco.execution.phase',
            'res_id': execution.id,
            'view_mode': 'form',
            'view_id': self.env.ref('qaco_execution_phase.view_execution_phase_form').id,
            'target': 'current',
            'context': {'default_audit_id': self.id},
        }
