# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions


TEMPLATE_CATEGORY = [
    ('client_onboarding', 'A. Client Onboarding & Administration'),
    ('professional_clearance', 'B. Professional Clearance & Communication'),
    ('audit_assurance', 'C. Audit & Assurance Engagement'),
    ('tax_engagements', 'D. Tax Engagements'),
    ('other_letters', 'E. Other Standard Letters & Confirmations'),
]


class OnboardingTemplateCategory(models.Model):
    """Template categories for organizing standard documents."""
    _name = 'qaco.onboarding.template.category'
    _description = 'Onboarding Template Category'
    _order = 'sequence, name'

    name = fields.Char(string='Category Name', required=True)
    code = fields.Char(string='Code', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    template_ids = fields.One2many(
        'qaco.onboarding.template.document',
        'category_id',
        string='Templates',
    )
    template_count = fields.Integer(
        string='Template Count',
        compute='_compute_template_count',
    )

    @api.depends('template_ids')
    def _compute_template_count(self):
        for rec in self:
            rec.template_count = len(rec.template_ids)


class OnboardingTemplateDocument(models.Model):
    """Standard professional templates available for download/attach."""
    _name = 'qaco.onboarding.template.document'
    _description = 'Onboarding Template Document'
    _order = 'category_id, sequence, name'

    name = fields.Char(string='Template Name', required=True)
    category_id = fields.Many2one(
        'qaco.onboarding.template.category',
        string='Category',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(string='Sequence', default=10)
    description = fields.Text(string='Description')
    template_file = fields.Binary(string='Template File', attachment=True)
    template_filename = fields.Char(string='Filename')
    file_type = fields.Selection(
        [('docx', 'Word Document (.docx)'), ('xlsx', 'Excel (.xlsx)'), ('pdf', 'PDF')],
        string='File Type',
        default='docx',
    )
    file_size = fields.Integer(string='File Size (bytes)', compute='_compute_file_size', store=True)
    active = fields.Boolean(string='Active', default=True)

    def _compute_file_size(self):
        import base64
        for rec in self:
            try:
                if rec.template_file:
                    # template_file is base64-encoded binary
                    rec.file_size = len(base64.b64decode(rec.template_file))
                else:
                    rec.file_size = 0
            except Exception:
                rec.file_size = 0

    def action_download(self):
        """Download the template file."""
        self.ensure_one()
        if not self.template_file:
            return {'type': 'ir.actions.act_window_close'}
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self._name}/{self.id}/template_file/{self.template_filename}?download=true',
            'target': 'self',
        }

    def action_attach_to_onboarding(self):
        """Attach this template to the active onboarding record.

        This will create a `qaco.onboarding.attached.template` record with the
        template file prefilled if available.
        """
        self.ensure_one()
        onboarding_id = (self.env.context.get('onboarding_id') or
                         self.env.context.get('active_id') or
                         self.env.context.get('res_id'))
        if not onboarding_id:
            raise exceptions.UserError(_('Open an Onboarding record to attach this template.'))
        onboarding = self.env['qaco.client.onboarding'].browse(onboarding_id)
        if not onboarding:
            raise exceptions.UserError(_('Onboarding record not found.'))

        # Avoid duplicate attachments
        existing = onboarding.attached_template_ids.filtered(lambda t: t.template_id.id == self.id)
        if existing:
            onboarding.message_post(body=_('Template %s already attached') % self.name)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Info'),
                    'message': _('Template %s already attached.') % self.name,
                    'type': 'info',
                    'sticky': False,
                },
            }

        vals = {
            'onboarding_id': onboarding.id,
            'template_id': self.id,
        }
        if self.template_file:
            vals['attached_file'] = self.template_file
            vals['attached_filename'] = self.template_filename
        attached = self.env['qaco.onboarding.attached.template'].create(vals)
        onboarding.message_post(body=_('Template %s attached by %s') % (self.name, self.env.user.name))
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Attached'),
                'message': _('Template %s attached to onboarding.') % self.name,
                'type': 'success',
                'sticky': False,
            },
        }


class OnboardingAttachedTemplate(models.Model):
    """Templates attached to a specific onboarding record."""
    _name = 'qaco.onboarding.attached.template'
    _description = 'Attached Template to Onboarding'
    _order = 'create_date desc'

    onboarding_id = fields.Many2one(
        'qaco.client.onboarding',
        string='Onboarding',
        required=True,
        ondelete='cascade',
        index=True,
    )
    template_id = fields.Many2one(
        'qaco.onboarding.template.document',
        string='Template',
        required=True,
        ondelete='restrict',
    )
    attached_file = fields.Binary(string='Attached File', attachment=True)
    attached_filename = fields.Char(string='Filename')
    notes = fields.Text(string='Notes')
    attached_by = fields.Many2one(
        'res.users',
        string='Attached By',
        default=lambda self: self.env.user,
        readonly=True,
    )
    attached_date = fields.Datetime(
        string='Attached Date',
        default=fields.Datetime.now,
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-populate file from template if not provided."""
        for vals in vals_list:
            if vals.get('template_id') and not vals.get('attached_file'):
                template = self.env['qaco.onboarding.template.document'].browse(vals['template_id'])
                if template.template_file:
                    vals['attached_file'] = template.template_file
                    vals['attached_filename'] = template.template_filename
        return super().create(vals_list)


class OnboardingAttachTemplatesWizard(models.TransientModel):
    """Wizard to attach multiple templates to an onboarding record."""
    _name = 'qaco.onboarding.attach.templates.wizard'
    _description = 'Attach Templates to Onboarding Wizard'

    onboarding_id = fields.Many2one('qaco.client.onboarding', string='Onboarding', required=True)
    # Use an explicit, short relation name to avoid exceeding DB identifier length limits
    template_ids = fields.Many2many(
        'qaco.onboarding.template.document',
        'qaco_onb_attach_tpl_rel',
        'wizard_id',
        'template_id',
        string='Templates',
        required=True,
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        onboarding_id = self.env.context.get('onboarding_id') or self.env.context.get('active_id')
        if onboarding_id and 'onboarding_id' in fields:
            res['onboarding_id'] = onboarding_id
        # default template selection may be empty; UI can select
        return res

    def action_attach(self):
        self.ensure_one()
        Attached = self.env['qaco.onboarding.attached.template']
        onboarding = self.onboarding_id
        attached_templates = []
        for tpl in self.template_ids:
            if not onboarding.attached_template_ids.filtered(lambda t: t.template_id.id == tpl.id):
                vals = {'onboarding_id': onboarding.id, 'template_id': tpl.id}
                if tpl.template_file:
                    vals['attached_file'] = tpl.template_file
                    vals['attached_filename'] = tpl.template_filename
                Attached.create([vals])
                attached_templates.append(tpl.name)
        if attached_templates:
            onboarding.message_post(body=_('Attached templates: %s') % ', '.join(attached_templates))
        return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {'title': _('Done'), 'message': _('Templates attached'), 'type': 'success', 'sticky': False}}
