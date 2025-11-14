from odoo import models, fields, api


class QacoMonthlyInternalAudit(models.Model):
    _name = 'qaco.monthly.internal.audit'
    _description = 'QACO Monthly Internal Audit'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin',
        'mail.tracking.duration.mixin',
    ]
    _track_duration_field = 'stage_id'
    _order = 'create_date desc'

    name = fields.Char(string='Name', tracking=True)
    seq_code = fields.Char(string='Sequence', required=True, copy=False, default='New')
    client_id = fields.Many2one('res.partner', string='Client')
    month_id = fields.Many2one('monthly.audit.month', string='Month', default=lambda self: self._get_default_month_id())
    stage_id = fields.Many2one('monthly.audit.stages', string='Stage', default=lambda self: self._get_default_stage_id())

    def _get_default_stage_id(self):
        return self.env['monthly.audit.stages'].search([], order='sequence', limit=1).id

    def _get_default_month_id(self):
        today = fields.Date.context_today(self)
        current_month = "%s-%02d" % (today.year, today.month)
        month_record = self.env['monthly.audit.month'].search([
            ('name', 'ilike', current_month + '%')], limit=1)
        return month_record.id if month_record else None

    def move_to_next_stage(self):
        next_stage = self.env['monthly.audit.stages'].search(
            [('sequence', '>', self.stage_id.sequence)], order='sequence', limit=1)
        if next_stage:
            self.stage_id = next_stage

    def move_to_previous_stage(self):
        prev_stage = self.env['monthly.audit.stages'].search(
            [('sequence', '<', self.stage_id.sequence)], order='sequence desc', limit=1)
        if prev_stage:
            self.stage_id = prev_stage

    def move_to_next_month(self):
        next_month = self.env['monthly.audit.month'].search(
            [('sequence', '>', self.month_id.sequence)], order='sequence', limit=1)
        if next_month:
            self.month_id = next_month

    def move_to_previous_month(self):
        prev_month = self.env['monthly.audit.month'].search(
            [('sequence', '<', self.month_id.sequence)], order='sequence desc', limit=1)
        if prev_month:
            self.month_id = prev_month

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('seq_code', 'New') == 'New':
                vals['seq_code'] = self.env['ir.sequence'].next_by_code(
                    'monthly.internal.audit.sequence') or 'New'
        return super().create(vals_list)
