from odoo import models, fields, api

class HrPublicHoliday(models.Model):
    _name = 'hr.public.holiday'
    _description = 'Public Holiday'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Holiday Name", required=True, tracking=True)
    date = fields.Date(string="Holiday Date", required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved')
    ], default='draft', string="Status", tracking=True)

    def action_approve(self):
        for rec in self:
            rec.state = 'approved'

    def action_reset_to_draft(self):
        for rec in self:
            rec.state = 'draft'
