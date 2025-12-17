# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


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
    active = fields.Boolean(string='Active', default=True)

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
