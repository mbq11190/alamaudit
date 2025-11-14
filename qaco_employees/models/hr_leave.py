from odoo import models, api


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    @api.depends_context('uid')
    @api.depends('state', 'employee_id')
    def _compute_can_cancel(self):
        user = self.env.user
        for leave in self:
            leave.can_cancel = user.has_group('qaco_employees.group_qaco_employee_administrator')
