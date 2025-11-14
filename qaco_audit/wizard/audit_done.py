
from odoo import fields, models
class AuditDone(models.TransientModel):
    _name = 'audit.done'
    _description = 'Move to Done Warning Audit'

    confirm = fields.Text('Confirm', default='Hey, have you made sure to save all the attachments and data in the Google Drive folder? Because once we hit Confirm Button, its bye-bye to those files in the Odoo Database! If you are sure, please click on Confirm otherwise Click Cancel, Save Files and Come back again.')

    def action_confirm(self):
        self.ensure_one()
        audit_id = self.env.context.get('active_id')
        # this will check if anything was entered in the field. Adjust accordingly
        if audit_id and self.confirm:
            corp = self.env['qaco.audit'].browse(audit_id)

            # Remove all attachments
            corp.remove_all_attachments()

            # Find the 'Done' stage
            done_stage = self.env['audit.stages'].search([('name', '=', 'Done')])
            if done_stage:
                corp.stage_id = done_stage

            return {'type': 'ir.actions.act_window_close'}


