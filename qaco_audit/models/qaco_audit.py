# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import AccessError
import logging

_logger = logging.getLogger(__name__)


# Corporate model
class Qacoaudit(models.Model):
    _name = 'qaco.audit'
    _rec_name = 'client_id'
    # Order of the records will be based on priority, sequence, and date_deadline
    _order = "create_date desc, seq_code desc"
    # Inherit from mail.thread for messaging and mail.activity.mixin for activities
    _inherit = ["mail.thread", "mail.activity.mixin", "mail.tracking.duration.mixin"]
    _description = 'QACO Audit Work Portal'
    # Not Used yet, but I will use it later to Track Duration of each stage
    _track_duration_field = 'stage_id'

    # I am defining all fields in my model here
    client_id = fields.Many2one('res.partner', required=True, string='Client Name')
    # This field is used to assign multiple users to a task
    user_ids = fields.Many2many('res.users', string='Users', group_expand="_group_expand_user_ids")
    contact = fields.Char(string='Phone', related='client_id.phone', readonly=True)
    referral = fields.Many2one('res.partner', string='Referral')
    audit_year = fields.Many2many('audit.year', string='Audit Year')
    repeat = fields.Selection([('New Client', 'New Client'), ('Repeat Client', 'Repeat Client')],
                              string='Recurring')
    folder = fields.Char(string='Folder Path', )
    qaco_assigning_partner = fields.Many2one(
        'hr.employee',
        string='Assigning Partner',
        domain="[('designation_id.name', '=', 'Partner')]"
    )
    documents_info = fields.Char(string='Docs More Info/Location', )
    documents = fields.Selection(
        [('Received', 'Received'), ('Not Received', 'Not Received'), ('Partially Received', 'Partially Received')],
        string='Documents Status')
    firm_name = fields.Many2one('audit.firm.name', string='Firm Name', ondelete='set null')
    report_type = fields.Selection([('UDIN', 'UDIN'),('Agreed Upon Procedures','Agreed upon Procedures'), ('Internal Audit', 'Internal Audit'), ('3rd Party Audits', '3rd Party Audits')], string='Audit Type')
    udin_no = fields.Char(string='UDIN No',)
    legal_entity = fields.Selection([('Pvt Company', 'Pvt Company'), ('SMC Company', 'SMC Company'), ('Public Company', 'Public Company'), ('Branch Office', 'Branch Office'), ('Govt Organisation', 'Govt Organisation'), ('NGO Sec 42', 'NGO Sec 42'),('NGO-Other', 'NGO-Other'), ('Partnership', 'Partnership'),
                                    ('Sole Proprietorship', 'Sole Proprietorship'), ('Provident Fund', 'Provident Fund'), ('Pension Fund', 'Pension FUnd')], string='Legal Entity')
    share_capital = fields.Monetary(string='Paid-up Share Capital', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency')
    turnover = fields.Monetary(string='Turnover', currency_field='currency_id')
    bank_balance = fields.Monetary(string='Bank Balance', currency_field='currency_id')
    qaco_audit_partner = fields.Many2one(
        'hr.employee',
        string='Audit Partner',
        domain="[('designation_id.name', '=', 'Partner')]"
    )
    audit_location_1 = fields.Selection([('Client Premises', 'Client Premises'), ('QACO Office', 'QACO Office')], string='Audit Location')
    audit_location_2 = fields.Char(string='Client Address', related='client_id.street', readonly=True)
    no_of_persons = fields.Integer(string='No of Persons Required', )
    scanned = fields.Selection([('Done/Saved', 'Done/Saved'), ('Not Yet', 'Not Yet'), ('NA', 'NA')], string='Data Scan Status')
    original_file = fields.Selection([('Stored In Office', 'Stored In Office'), ('Returned', 'Returned'), ('NA', 'NA')],
                                     string='Client Original Documents')
    employee_id = fields.Many2one('hr.employee', string="Team Lead", ondelete='cascade', index=True)
    team_id = fields.Many2many('hr.employee', string="Team Members", ondelete='cascade', index=True)
    description = fields.Text()
    # This field is used to set priority of a task
    priority = fields.Selection([('0', 'Na'), ('1', 'Low'), ('2', 'Mid'), ('3', 'High'), ], default='0', index=True, string="Priority",
                                tracking=True)
    stage_id = fields.Many2one('audit.stages', default=lambda self: self._get_default_stage_id(), string='Stage',
                               store=True, readonly=True, ondelete='restrict', index=True, tracking=True,
                               group_expand='_group_expand_stage_ids')
    color = fields.Integer(string='Color Index')
    state = fields.Selection([('Pending Client Side', 'Pending Client Side'), ('Working on it', 'Working on it'),
                              ('Client Confirmed', 'Client Confirmed')], string='Client Status')
    pending_reason = fields.Char(string='Pending Reason', default="Write Pending Reason in the Chatter Below", readonly=True)
    # This field is used to hide or show a record, but it is not added to views yet
    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer(default=1)
    date_deadline = fields.Datetime(string='Deadline', index=True, copy=False, tracking=True)
    create_date = fields.Datetime("Created On", readonly=True, index=True)
    write_date = fields.Datetime("Last Updated On", readonly=True)
    date_end = fields.Datetime(string='Ending Date', index=True, copy=False)
    date_assign = fields.Datetime(string='Assigning Date', copy=False, readonly=True,
                                  help="Date on which this task was last assigned (or unassigned). Based on this, you can get statistics on the time it usually takes to assign tasks.")
    date_last_stage_update = fields.Datetime(string='Last Stage Update', index=True, copy=False, readonly=True,
                                             help="Date on which the state of your task has last been modified.\n" "Based on this information you can identify tasks that are stalling and get statistics on the time it usually takes to move tasks from one stage/state to another.")
    allocated_hours = fields.Float("Allocated Time", tracking=True)
    manager_review = fields.Selection([('Okay to Print', 'Okay to Print'), ('Revision Required', 'Revision Required'),
                                       ('Review Pending', 'Review Pending')], string='Manager Review')
    client_review = fields.Selection(
        [('Client Confirmed', 'Client Confirmed'), ('Pending Confirmation', 'Pending Confirmation')],
        string='Client Review')
    client_signature = fields.Selection([('Signed Accounts Received', 'Signed Accounts Received'), ('Sent to Client', 'Sent to Client'), ('Pending Signature', 'Pending Signature')],
                                       string='Client Signature')
    file_attachments = fields.One2many('audit.attachment', 'audit_id', string='File Attachments')
    is_favourite = fields.Boolean("Favourite", help="Mark this task as a favorite to easily find it again", tracking=True)
    # Smart button counts removed - only keeping fields for modules that exist
    audit_count = fields.Integer(compute='compute_audit_count')


    def _get_default_seq_code(self):
        return 'New'

    seq_code = fields.Char(string='Seq Number', required=True, copy=False, readonly=False, index=True, default=_get_default_seq_code)

    # Function to Show Empty Stages in Kanban View
    def _group_expand_stage_ids(self, stages, domain, order):
        """Read group customization in order to display all the stages in the
        Kanban view, even if they are empty.
        """
        stage_ids = stages._search([], order=order)
        return stages.browse(stage_ids)

    # Function to show all users in Kanban grouping
    def _group_expand_user_ids(self, users, domain, order):
        """Return all users so Kanban grouping by user shows empty groups."""
        user_ids = users._search([], order=order)
        return users.browse(user_ids)

    # Function to get default stage id as first stage
    def _get_default_stage_id(self):
        return self.env['audit.stages'].search([('name', '=', 'New')], limit=1).id



# Function to Move to Next Stage and Add constraints to move to next stage
    def move_to_next_stage(self):
        next_stage = self.env['audit.stages'].search([
            ('sequence', '>', self.stage_id.sequence)
        ], order='sequence', limit=1)
        if not next_stage:
            return

        missing_fields = []

        if next_stage.id == 3:
            if not self.employee_id:
                missing_fields.append(self._fields['employee_id'].string)
            if not self.team_id:
                missing_fields.append(self._fields['team_id'].string)

        if next_stage.id == 4:
            for field in ['folder', 'legal_entity', 'qaco_audit_partner']:
                if not getattr(self, field):
                    missing_fields.append(self._fields[field].string)

        if next_stage.id == 2:
            for field in ['client_id', 'contact', 'audit_year', 'firm_name', 'report_type', 'audit_location_1']:
                if not getattr(self, field):
                    missing_fields.append(self._fields[field].string)

        if missing_fields:
            raise exceptions.ValidationError(
                _("Please fill the following fields before moving to the next stage: %s") % ", ".join(missing_fields)
            )

        if next_stage.name == 'Invoiced' and not self.user_has_groups('base.group_system'):
            raise exceptions.ValidationError("Only Partner may move it to the next stage.")

        if next_stage.name == 'Done':
            return {
                'name': _('Audit Done'),
                'type': 'ir.actions.act_window',
                'view_id': self.env.ref('qaco_audit.audit_done_form_view').id,
                'res_model': 'audit.done',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'active_id': self.ids[0],
                },
            }

        self.stage_id = next_stage


    def move_to_previous_stage(self):
        previous_stage = self.env['audit.stages'].search([('sequence', '<', self.stage_id.sequence)],
                                                       order='sequence desc', limit=1)
        if previous_stage:
            self.stage_id = previous_stage

    # Function to Archive Record

    def action_archive(self):
        if not self.user_has_groups(
            'qaco_audit.group_audit_partner,qaco_audit.group_audit_administrator'
        ):
            raise AccessError(_('You do not have permission to perform this action.'))
        self.write({'active': False})


#Function to Override default Duplicate/copy function

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        if not self.user_has_groups(
            'qaco_audit.group_audit_partner,qaco_audit.group_audit_administrator'
        ):
            raise AccessError(_('You do not have permission to perform this action.'))
        default = default or {}
        default['audit_year'] = False
        default['repeat'] = False
        default['employee_id'] = False
        default['team_id'] = False
        default['qaco_audit_partner'] = False
        default['share_capital'] = False
        default['udin_no'] = False
        default['turnover'] = False
        default['client_signature'] = False
        default['bank_balance'] = False
        default['state'] = False
        default['manager_review'] = False
        default['pending_reason'] = False
        default['file_attachments'] = False
        # default['documents'] = False
        # default['scanned'] = False
        default['original_file'] = False
        default['date_deadline'] = False
        default['documents_info'] = False
        default['stage_id'] = 1
        new_record = super(Qacoaudit, self).copy(default)
        new_record.message_post(body="This record is duplicated from record with ID %s" % self.id)
        return new_record

    def unlink(self):
        if not self.user_has_groups(
            'qaco_audit.group_audit_partner,qaco_audit.group_audit_administrator'
        ):
            raise AccessError(_('You do not have permission to perform this action.'))
        return super(Qacoaudit, self).unlink()

    #Function to add sequence number automatically

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('seq_code', 'New') == 'New':
                seq_code = (
                    self.env['ir.sequence'].next_by_code(
                        'audit.sequence', sequence_date=fields.Date.today()
                    )
                    or 'New'
                )
                vals['seq_code'] = seq_code

        records = super().create(vals_list)

        followers = self.env['qaco_audit.auto.follower'].search([])
        partner_ids = followers.mapped('employee_id.user_id.partner_id.id')
        partner_ids = [pid for pid in partner_ids if pid]
        if partner_ids:
            records.message_subscribe(partner_ids=list(set(partner_ids)))
        return records

    # Funtion to add Subscribers to the record automatically

    def write(self, vals):
        if 'employee_id' in vals or 'team_id' in vals:
            for record in self:
                old_partners = []

                if 'employee_id' in vals and record.employee_id and record.employee_id.user_id and record.employee_id.user_id.partner_id:
                    old_partners.append(record.employee_id.user_id.partner_id.id)

                if 'team_id' in vals:
                    old_partners += [
                        emp.user_id.partner_id.id
                        for emp in record.team_id
                        if emp.user_id and emp.user_id.partner_id
                    ]

                if old_partners:
                    record.message_unsubscribe(partner_ids=list(set(old_partners)))

        res = super(Qacoaudit, self).write(vals)

        if 'employee_id' in vals or 'team_id' in vals:
            for record in self:
                new_partners = []

                if record.employee_id and record.employee_id.user_id and record.employee_id.user_id.partner_id:
                    new_partners.append(record.employee_id.user_id.partner_id.id)

                new_partners += [
                    emp.user_id.partner_id.id
                    for emp in record.team_id
                    if emp.user_id and emp.user_id.partner_id
                ]

                if new_partners:
                    record.message_subscribe(partner_ids=list(set(new_partners)))

        return res

        # Function to remove attachments when task is moved to done stage

    def remove_all_attachments(self):
        attachments = self.env['ir.attachment'].search([('res_model', '=', 'qaco.audit'), ('res_id', '=', self.id)])
        if attachments:
            attachments.unlink()

    @api.depends('client_id')
    def compute_audit_count(self):
        for record in self:
            record.audit_count = self.env['qaco.audit'].sudo().search_count([
                ('client_id', '=', record.client_id.id),
                ('active', '=', True)
            ])

    # ==================
    # Action Methods
    # ==================
    def get_audit(self):
        return self._open_related_records('qaco.audit', 'Audit')

    # ==================
    # Helper Method
    # ==================
    def _open_related_records(self, model_name, name):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'view_mode': 'tree,form',
            'res_model': model_name,
            'domain': [('client_id', '=', self.client_id.id)],
            'context': {'create': False},
        }

    def action_open_client_onboarding(self):
        """Open or create client onboarding record for this audit"""
        self.ensure_one()
        onboarding = self.env['qaco.client.onboarding'].search([('audit_id', '=', self.id)], limit=1)
        if not onboarding:
            onboarding = self.env['qaco.client.onboarding'].create({
                'audit_id': self.id,
            })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Client Onboarding',
            'res_model': 'qaco.client.onboarding',
            'res_id': onboarding.id,
            'view_mode': 'form',
            'target': 'current',
        }
