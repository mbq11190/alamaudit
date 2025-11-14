from odoo import models, fields

class HrTransferCcRecipient(models.Model):
    _name = 'hr.transfer.cc.recipient'
    _description = 'Transfer Email CC Recipient'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    active = fields.Boolean(default=True)
