from odoo import models, fields, api
from odoo.exceptions import AccessError

class LeaveAllowance(models.Model):
    _name = 'leave.allowance'
    _description = 'Leave Allowance'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = 'create_date desc'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    time_off_type = fields.Selection([
        ('ca_130', 'CA 130 Days Leave'),
        ('ca_150', 'CA 150 Days Leave'),
        ('ca_115', 'CA 115 Days Leave'),
        ('annual_perm', 'Permanent Staff Annual Leaves')
    ], string='Time Off Type', required=True)
    active = fields.Boolean('Active', default=True)
    create_date = fields.Datetime("Created On", readonly=True, index=True)
    write_date = fields.Datetime("Last Updated On", readonly=True)

    from_date = fields.Date(string='Valid From')
    to_date = fields.Date(string='Valid To')

    allowed_leaves = fields.Float(string='Allowed Leaves')

    state = fields.Selection([
        ('draft', 'To Approve'),
        ('approved', 'Approved')
    ], string='Status', default='draft', tracking=True)

    def action_archive(self):
        self.write({'active': False})

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """Auto-fill from/to date based on employee article dates"""
        for record in self:
            if record.employee_id:
                record.from_date = record.employee_id.date_of_articles_registration
                record.to_date = record.employee_id.date_of_articles_end

    def action_validate(self):
        for record in self:
            if record.state != 'draft':
                continue
            record.state = 'approved'
            record.create_leave_summary_event()

    def create_leave_summary_event(self):
        for record in self:
            if not record.employee_id or not record.from_date:
                continue

            # ✅ Create the summary without setting allowed_leaves manually
            summary = self.env['leave.summary'].create({
                'employee_id': record.employee_id.id,
                'event_date': record.from_date,
                'allowance_ref_id': record.id,
            })

            # ✅ Force recompute and store result
            summary.with_context(force_recompute=True)._compute_allowed_leaves()
            summary.write({'allowed_leaves': summary.allowed_leaves})

            # ✅ Cascade to future summaries
            summary._cascade_update_future_months()

    def action_reset_to_draft(self):
        if not (
            self.env.user.has_group('qaco_employees.group_qaco_employee_hr_manager')
            or self.env.user.has_group('qaco_employees.group_qaco_employee_administrator')
            or self.env.user.has_group('base.group_system')
        ):
            raise AccessError("Only HR managers or administrators can reset allowances.")

        for rec in self:
            rec.state = 'draft'
            summaries = self.env['leave.summary'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('allowance_ref_id', '=', rec.id),
            ])
            summary_dates = summaries.mapped('event_date')
            summaries.unlink()

            # Recompute future summaries that depended on this allowance
            if summary_dates:
                min_date = min(summary_dates)
                future_summaries = self.env['leave.summary'].search([
                    ('employee_id', '=', rec.employee_id.id),
                    ('event_date', '>', min_date),
                ])
                previous = self.env['leave.summary'].search([
                    ('employee_id', '=', rec.employee_id.id),
                    ('event_date', '<', min_date),
                ], order='event_date desc', limit=1)

                for summary in future_summaries:
                    summary.opening_leaves = previous.closing_leaves if previous else 0.0
                    summary.with_context(force_recompute=True)._compute_allowed_leaves()
                    if summary.is_monthly_summary:
                        summary._compute_approved_leaves()
                    summary._compute_absent_days()
                    summary._compute_closing_leaves()
                    summary._compute_remaining_leaves()
                    
                    # ✅ Persist the recomputed values with skip_cascade
                    summary.with_context(skip_cascade=True).write({
                        'opening_leaves': summary.opening_leaves,
                        'closing_leaves': summary.closing_leaves,
                        'remaining_leaves': summary.remaining_leaves,
                    })
                    previous = summary

    @api.constrains('employee_id', 'from_date', 'to_date')
    def _check_duplicate_period(self):
        for record in self:
            domain = [
                ('id', '!=', record.id),
                ('employee_id', '=', record.employee_id.id),
                '|',
                '&', ('from_date', '<=', record.to_date), ('to_date', '>=', record.from_date),
                '&', ('from_date', '<=', record.from_date), ('to_date', '>=', record.to_date),
            ]
            overlap = self.search(domain)
            if overlap:
                raise models.ValidationError(
                    "Leave allowance period overlaps with another record for the same employee."
                )

