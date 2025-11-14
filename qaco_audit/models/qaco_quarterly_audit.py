from odoo import models, fields, api, _, exceptions
from odoo.exceptions import AccessError, UserError
from datetime import datetime, timedelta
from calendar import monthrange


class QacoQuarterlyAudit(models.Model):
    _name = 'qaco.quarterly.audit'
    _rec_name = 'client_id'
    _order = 'seq_code desc, create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'mail.tracking.duration.mixin']
    _description = 'QACO Quarterly Audit'
    _track_duration_field = 'stage_id'

    quarter_dict = {1: '01-Jan-Mar', 2: '02-Apr-Jun', 3: '03-Jul-Sep', 4: '04-Oct-Dec'}

    client_id = fields.Many2one('res.partner', required=True, string='Client Name')
    user_ids = fields.Many2many('res.users', string='Users')
    contact = fields.Char(string='Phone', related='client_id.phone', readonly=True)
    work_quarter = fields.Many2one('audit.quarter', required=True,
                                   default=lambda self: self._get_default_quarter(),
                                   string='Quarter', store=True, index=True, tracking=True)
    stage_id = fields.Many2one('audit.quarter.stages',
                               default=lambda self: self._get_default_stage_id(),
                               string='Stage', store=True, readonly=True,
                               ondelete='restrict', index=True, tracking=True)
    stage_name = fields.Char(related='stage_id.name', string='Stage Name', readonly=True)
    folder = fields.Char(string='Folder Path')
    employee_id = fields.Many2one('hr.employee', string='Assigned To', ondelete='cascade', index=True)
    description = fields.Text()
    priority = fields.Selection([('0', 'Na'), ('1', 'Low'), ('2', 'Mid'), ('3', 'High')],
                                default='0', index=True, tracking=True)
    color = fields.Integer(string='Color Index')
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=1)
    date_deadline = fields.Datetime(string='Last Date', compute='_compute_date_deadline',
                                    store=True, copy=False, tracking=True)
    create_date = fields.Datetime(readonly=True, index=True)
    write_date = fields.Datetime(readonly=True)
    date_end = fields.Datetime(string='Ending Date', index=True, copy=False)
    date_assign = fields.Datetime(string='Assigning Date', copy=False, readonly=True,
                                  help='Date on which this task was last assigned (or unassigned).')
    is_favourite = fields.Boolean('Favourite', help='Mark this task as a favourite to easily find it again',
                                  tracking=True)

    def _get_default_seq_code(self):
        return 'New'

    seq_code = fields.Char(string='Seq Number', required=True, copy=False, readonly=False,
                           index=True, default=_get_default_seq_code)

    _sql_constraints = [
        ('seq_code_unique', 'unique(seq_code)', 'Sequence number must be unique.'),
    ]

    def action_archive(self):
        if not self.user_has_groups('qaco_audit.group_audit_partner,qaco_audit.group_audit_administrator'):
            raise AccessError(_('You do not have permission to perform this action.'))
        self.write({'active': False})

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        if not self.user_has_groups('qaco_audit.group_audit_partner,qaco_audit.group_audit_administrator'):
            raise AccessError(_('You do not have permission to perform this action.'))
        default = default or {}
        default.update({'employee_id': False, 'seq_code': 'New'})
        new_record = super().copy(default)
        new_record.message_post(body="This record is duplicated from record with ID %s" % self.id)
        return new_record

    def unlink(self):
        if not self.user_has_groups('qaco_audit.group_audit_partner,qaco_audit.group_audit_administrator'):
            raise AccessError(_('You do not have permission to perform this action.'))
        return super().unlink()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('seq_code', 'New') == 'New':
                seq_code = self.env['ir.sequence'].next_by_code(
                    'quarterly.audit.sequence', sequence_date=fields.Date.today()) or 'New'
                vals['seq_code'] = seq_code
        records = super().create(vals_list)
        followers = self.env['qaco_audit.auto.follower'].search([])
        partner_ids = followers.mapped('employee_id.user_id.partner_id.id')
        partner_ids = [pid for pid in partner_ids if pid]
        if partner_ids:
            records.message_subscribe(partner_ids=list(set(partner_ids)))
        return records

    def _get_default_quarter(self):
        today = datetime.now()
        quarter_num = (today.month - 1) // 3 + 1
        current_quarter = f"{today.year}-{quarter_num:02d}"
        quarter_record = self.env['audit.quarter'].search([('name', 'ilike', current_quarter + '%')], limit=1)
        return quarter_record.id if quarter_record else None

    def _get_default_stage_id(self):
        return self.env['audit.quarter.stages'].search([('name', '=', 'New')], limit=1).id

    @api.depends('work_quarter')
    def _compute_date_deadline(self):
        for record in self:
            if record.work_quarter:
                year, quarter = record.work_quarter.name.split('-')[:2]
                first_month = (int(quarter) - 1) * 3 + 1
                last_month = first_month + 2
                work_quarter_date = datetime(int(year), last_month, 1)
                last_day_of_month = monthrange(int(year), last_month)[1]
                work_quarter_date = work_quarter_date.replace(day=last_day_of_month)
                deadline_date = work_quarter_date + timedelta(days=18)
                record.date_deadline = fields.Datetime.to_string(deadline_date)
            else:
                record.date_deadline = False

    def move_to_next_stage(self):
        for record in self:
            record.ensure_one()
            next_stage = self.env['audit.quarter.stages'].search([
                ('sequence', '>', record.stage_id.sequence)
            ], order='sequence', limit=1)
            if not next_stage:
                continue
            missing_fields = []
            if next_stage.name == 'Assign':
                for field in ['client_id', 'contact', 'work_quarter']:
                    if not getattr(record, field):
                        missing_fields.append(record._fields[field].string)
            if next_stage.name == 'In Progress' and not record.employee_id:
                missing_fields.append(record._fields['employee_id'].string)
            if missing_fields:
                raise UserError(_('Please fill the following fields before moving to the next stage: %s') % ', '.join(missing_fields))
            record.stage_id = next_stage
            if next_stage.name == 'Done':
                if not record.folder:
                    raise UserError(_('Please fill the following fields before moving to the next stage: %s') % record._fields['folder'].string)
                created = record._create_next_quarter_record()
                msg = _('Next quarter record created.') if created else _('Next quarter record already exists.')
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
            previous_stage = self.env['audit.quarter.stages'].search([
                ('sequence', '<', record.stage_id.sequence)
            ], order='sequence desc', limit=1)
            if previous_stage:
                record.stage_id = previous_stage

    def _create_next_quarter_record(self):
        created = False
        for record in self:
            record.ensure_one()
            next_quarter = self.env['audit.quarter'].search([
                ('sequence', '>', record.work_quarter.sequence)
            ], order='sequence', limit=1)
            if not next_quarter:
                continue
            exists = self.search([
                ('client_id', '=', record.client_id.id),
                ('work_quarter', '=', next_quarter.id),
            ], limit=1)
            if exists:
                continue
            vals = record.copy_data()[0]
            vals.update({
                'work_quarter': next_quarter.id,
                'stage_id': self.env.ref('qaco_audit.audit_quarter_stage_new').id if self.env.ref('qaco_audit.audit_quarter_stage_new', raise_if_not_found=False) else False,
                'seq_code': 'New',
            })
            self.create(vals)
            created = True
        return created

    def write(self, vals):
        if 'employee_id' in vals:
            for record in self:
                if record.employee_id and record.employee_id.user_id:
                    partner_id = record.employee_id.user_id.partner_id.id
                    if partner_id:
                        record.message_unsubscribe(partner_ids=[partner_id])
        res = super().write(vals)
        if 'employee_id' in vals:
            for record in self:
                if record.employee_id and record.employee_id.user_id:
                    partner_id = record.employee_id.user_id.partner_id.id
                    if partner_id:
                        record.message_subscribe(partner_ids=[partner_id])
        return res
