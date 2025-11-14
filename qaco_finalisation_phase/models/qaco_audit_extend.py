from odoo import models, fields, api


class QacoAuditExtend(models.Model):
    _inherit = 'qaco.audit'

    finalisation_phase_id = fields.Many2one('qaco.finalisation.phase', string='Finalisation Phase', 
                                           compute='_compute_finalisation_phase', store=False)
    finalisation_state = fields.Selection([
        ('draft', 'Draft'),
        ('report_drafting', 'Drafting'),
        ('review', 'Review'),
        ('qc_review', 'QC Review'),
        ('client_discussion', 'Client Discussion'),
        ('signoff', 'Sign-off'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
        ('not_started', 'Not Started')
    ], string='Finalisation Status', compute='_compute_finalisation_phase', store=False)
    
    def _compute_finalisation_phase(self):
        for record in self:
            finalisation = self.env['qaco.finalisation.phase'].search([('audit_id', '=', record.id)], limit=1)
            record.finalisation_phase_id = finalisation.id if finalisation else False
            record.finalisation_state = finalisation.state if finalisation else 'not_started'
    
    def action_open_finalisation_phase(self):
        """Open finalisation phase form or create if doesn't exist"""
        self.ensure_one()
        finalisation = self.env['qaco.finalisation.phase'].search([('audit_id', '=', self.id)], limit=1)
        
        if not finalisation:
            # Create new finalisation phase
            finalisation = self.env['qaco.finalisation.phase'].create({
                'audit_id': self.id,
            })
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Finalisation Phase',
            'res_model': 'qaco.finalisation.phase',
            'res_id': finalisation.id,
            'view_mode': 'form',
            'view_id': self.env.ref('qaco_finalisation_phase.view_finalisation_phase_form').id,
            'target': 'current',
            'context': {'default_audit_id': self.id},
        }
