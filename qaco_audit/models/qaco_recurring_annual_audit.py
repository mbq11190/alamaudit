from odoo import models, fields, api, _, exceptions
from datetime import datetime
from odoo.exceptions import UserError


class QacoRecurringAnnualAudit(models.Model):
    _name = 'qaco.recurring.annual.audit'
    _rec_name = 'client_id'
    _description = 'QACO Recurring Annual Audit'
    _order = "seq_code desc, create_date desc"
    _inherit = ["mail.thread", "mail.activity.mixin", "mail.tracking.duration.mixin"]
    _track_duration_field = 'stage_id'

    client_id = fields.Many2one('res.partner', required=True, string='Client Name')
    user_ids = fields.Many2many('res.users', string='Users')
    contact = fields.Char(string='Phone', related='client_id.phone', readonly=True)
    work_year = fields.Many2one('annual.audit.year', required=True,
                                default=lambda self: self._get_default_name(),
                                string='Year', index=True, tracking=True)
    stage_id = fields.Many2one('annual.audit.stages',
                               default=lambda self: self._get_default_stage_id(),
                               string='Stage', store=True, readonly=True,
                               ondelete='restrict', index=True, tracking=True)
    stage_name = fields.Char(related='stage_id.name', string='Stage Name', readonly=True)
    folder = fields.Char(string='Folder Path')
    employee_id = fields.Many2one('hr.employee', string="Assigned To", ondelete='cascade', index=True)
    description = fields.Text()
    priority = fields.Selection([
        ('0', 'Na'), ('1', 'Low'), ('2', 'Mid'), ('3', 'High')
    ], default='0', index=True, tracking=True)
    color = fields.Integer(string='Color Index')
    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer(default=1)
    date_deadline = fields.Datetime(string='Last Date', compute='_compute_date_deadline',
                                    store=True, copy=False, tracking=True)
    create_date = fields.Datetime("Created On", readonly=True, index=True)
    write_date = fields.Datetime("Last Updated On", readonly=True)

    def _get_default_seq_code(self):
        return 'New'

    seq_code = fields.Char(string='Seq Number', required=True, copy=False, readonly=False, index=True,
                           default=_get_default_seq_code)

    _sql_constraints = [
        ('seq_code_unique', 'unique(seq_code)', 'Sequence number must be unique.'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('seq_code', 'New') == 'New':
                seq_code = (
                    self.env['ir.sequence'].next_by_code(
                        'annual.audit.sequence', sequence_date=fields.Date.today()
                    ) or 'New'
                )
                vals['seq_code'] = seq_code
        return super().create(vals_list)

    def action_archive(self):
        self.write({'active': False})

    def _get_default_name(self):
        year_str = str(datetime.now().year)
        year_record = self.env['annual.audit.year'].search([('name', 'ilike', year_str + '%')], limit=1)
        return year_record.id if year_record else None

    @api.depends('work_year')
    def _compute_date_deadline(self):
        for record in self:
            if record.work_year:
                year = int(record.work_year.name)
                deadline_date = datetime(year, 12, 31)
                record.date_deadline = fields.Date.to_string(deadline_date)
            else:
                record.date_deadline = False

    def _get_default_stage_id(self):
        return self.env['annual.audit.stages'].search([('name', '=', 'New')], limit=1).id

    def move_to_next_stage(self):
        for record in self:
            record.ensure_one()
            next_stage = self.env['annual.audit.stages'].search([
                ('sequence', '>', record.stage_id.sequence)
            ], order='sequence', limit=1)
            if not next_stage:
                continue

            if next_stage.name == 'Assign':
                for field in ['client_id', 'contact', 'work_year']:
                    if not getattr(record, field):
                        raise UserError(_('Please fill all data before moving to the next stage.'))

            if next_stage.name == 'In Progress' and not record.employee_id:
                raise UserError(_('Please assign an employee before moving to the next stage.'))

            record.stage_id = next_stage

            if next_stage.name == 'Done':
                if not record.folder:
                    raise UserError(_('Please fill the following fields before moving to the next stage: %s') % record._fields['folder'].string)
                created = record._create_next_year_record()
                msg = _('Next year record created.') if created else _('Next year record already exists.')
                return {
                    'effect': {
                        'fadeout': 'slow',
                        'message': msg,
                        'type': 'rainbow_man',
                    }
                }
        return True

    def move_to_previous_stage(self):
        for record in self:
            record.ensure_one()
            previous_stage = self.env['annual.audit.stages'].search([
                ('sequence', '<', record.stage_id.sequence)
            ], order='sequence desc', limit=1)
            if previous_stage:
                record.stage_id = previous_stage

    def _create_next_year_record(self):
        created = False
        for record in self:
            record.ensure_one()
            next_year = self.env['annual.audit.year'].search([
                ('sequence', '>', record.work_year.sequence)
            ], order='sequence', limit=1)
            if not next_year:
                name = str(int(record.work_year.name) + 1)
                next_year = self.env['annual.audit.year'].create({
                    'name': name,
                    'sequence': record.work_year.sequence + 1,
                })
            existing = self.search([
                ('client_id', '=', record.client_id.id),
                ('work_year', '=', next_year.id),
            ], limit=1)
            if existing:
                continue

            vals = record.copy_data()[0]
            vals.update({
                'work_year': next_year.id,
                'stage_id': self.env.ref('qaco_audit.annual_audit_stage_new').id if self.env.ref('qaco_audit.annual_audit_stage_new', raise_if_not_found=False) else False,
                'seq_code': 'New',
            })
            self.create(vals)
            created = True
        return created

    def move_to_next_year(self):
        next_year = self.env['annual.audit.year'].search([
            ('sequence', '>', self.work_year.sequence)
        ], order='sequence', limit=1)
        if not next_year:
            name = str(int(self.work_year.name) + 1)
            next_year = self.env['annual.audit.year'].create({
                'name': name,
                'sequence': self.work_year.sequence + 1,
            })
        self.work_year = next_year

    def move_to_previous_year(self):
        prev_year = self.env['annual.audit.year'].search([
            ('sequence', '<', self.work_year.sequence)
        ], order='sequence desc', limit=1)
        if prev_year:
            self.work_year = prev_year

