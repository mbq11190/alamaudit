from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class QacoIndustry(models.Model):
    _name = 'qaco.industry'
    _description = 'Audit Industry Master Data'

    name = fields.Char(string='Industry Name', required=True)
    code = fields.Char(string='Industry Code', required=True)


class QacoBranchOffice(models.Model):
    _name = 'qaco.branch.office'
    _description = 'Branch Office Details'

    name = fields.Char(string='Branch Name', required=True)
    location = fields.Char(string='Location')
    city = fields.Char(string='City')
    province = fields.Char(string='Province')
    country = fields.Char(string='Country', default='Pakistan')
    phone = fields.Char(string='Phone')
    engagement_id = fields.Many2one('qaco.audit.engagement', string='Engagement', ondelete='cascade')


class QacoUBO(models.Model):
    _name = 'qaco.ubo'
    _description = 'Ultimate Beneficial Owner'

    name = fields.Char(string='Name', required=True)
    relation = fields.Char(string='Relation')
    ownership_percentage = fields.Float(string='Ownership Percentage')
    cnic = fields.Char(string='CNIC')
    engagement_id = fields.Many2one('qaco.audit.engagement', string='Engagement', ondelete='cascade')

    @api.constrains('cnic')
    def _check_cnic_ubo(self):
        for record in self:
            if record.cnic and (not record.cnic.isdigit() or len(record.cnic) != 13):
                raise ValidationError(_('CNIC for UBO must be 13 digits.'))


class QacoRegulatoryInspection(models.Model):
    _name = 'qaco.regulatory.inspection'
    _description = 'Regulatory Inspection History'

    name = fields.Char(string='Inspection Name', required=True)
    authority = fields.Char(string='Regulatory Authority')
    inspection_date = fields.Date(string='Inspection Date')
    findings = fields.Text(string='Findings')
    engagement_id = fields.Many2one('qaco.audit.engagement', string='Engagement', ondelete='cascade')


class QacoPep(models.Model):
    _name = 'qaco.pep'
    _description = 'Politically Exposed Person'

    name = fields.Char(string='Name', required=True)
    designation = fields.Char(string='Designation')
    country = fields.Char(string='Country', default='Pakistan')
    cnic = fields.Char(string='CNIC')
    engagement_id = fields.Many2one('qaco.audit.engagement', string='Engagement', ondelete='cascade')

    @api.constrains('cnic')
    def _check_cnic_pep(self):
        for record in self:
            if record.cnic and (not record.cnic.isdigit() or len(record.cnic) != 13):
                raise ValidationError(_('CNIC for PEP must be 13 digits.'))


class QacoAuditChecklist(models.Model):
    _name = 'qaco.audit.checklist'
    _description = 'Engagement Checklist Item'

    engagement_id = fields.Many2one('qaco.audit.engagement', string='Engagement', required=True, ondelete='cascade')
    checklist_type = fields.Selection([
        ('acceptance', 'Acceptance & Continuance'),
        ('independence', 'Independence & Ethics'),
        ('isqm', 'ISQM Firm Risk Assessment'),
    ], string='Checklist Type', required=True)
    question = fields.Char(string='Checklist Question', required=True)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('done', 'Done'),
        ('not_applicable', 'Not Applicable'),
    ], string='Status', default='pending')
    note = fields.Text(string='Notes')