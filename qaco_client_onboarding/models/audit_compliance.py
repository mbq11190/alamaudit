# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

ONBOARDING_AREAS = [
    ('legal_identity', 'Legal Identity'),
    ('regulatory_compliance', 'Regulatory & Compliance'),
    ('ownership_governance', 'Ownership & Governance'),
    ('pre_acceptance_risk', 'Pre-Acceptance Risk'),
    ('independence_ethics', 'Independence & Ethics'),
    ('predecessor_auditor', 'Predecessor Auditor'),
    ('engagement_terms', 'Engagement Terms'),
    ('partner_authorization', 'Partner Authorization'),
    ('audit_trail', 'Audit Trail'),
]

STANDARD_CATEGORY = [
    ('acceptance', 'Acceptance'),
    ('ethics', 'Ethics'),
    ('planning', 'Planning'),
    ('fraud', 'Fraud'),
    ('legal', 'Legal & Regulatory'),
    ('documentation', 'Documentation'),
]

REGULATOR_REFERENCE = [
    ('icap', 'ICAP'),
    ('aob', 'AOB'),
    ('secp', 'SECP'),
]


class AuditStandardLibrary(models.Model):
    _name = 'audit.standard.library'
    _description = 'Auditing Standard Reference'
    _order = 'code'

    code = fields.Char(string='Standard Code', required=True)
    title = fields.Char(string='Standard Title', required=True)
    applicability = fields.Text(string='Applicability / Guidance', required=True)
    category = fields.Selection(STANDARD_CATEGORY, string='Category', required=True)
    regulator_reference = fields.Selection(REGULATOR_REFERENCE, string='Regulator Reference', required=True, default='icap')
    mandatory = fields.Boolean(string='Mandatory', default=False)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('unique_code', 'unique(code)', 'Standard code must be unique.'),
    ]

    def name_get(self):
        return [(record.id, f"{record.code} - {record.title}") for record in self]


class AuditOnboardingChecklistTemplate(models.Model):
    _name = 'audit.onboarding.checklist.template'
    _description = 'Regulator Onboarding Checklist Template'
    _order = 'sequence, id'

    code = fields.Char(string='Code', help='Structured reference such as 1.1.1 or 1.2.1.')
    name = fields.Char(string='Checklist Requirement', required=True)
    onboarding_area = fields.Selection(ONBOARDING_AREAS, string='Onboarding Area', required=True)
    standard_ids = fields.Many2many('audit.standard.library', string='Standards')
    mandatory = fields.Boolean(string='Mandatory', default=True)
    sequence = fields.Integer(default=10)
    guidance = fields.Text(string='Guidance / Rationale')


class AuditOnboardingChecklist(models.Model):
    _name = 'audit.onboarding.checklist'
    _description = 'Regulator Onboarding Checklist'
    _order = 'sequence, id'

    code = fields.Char(string='Code', help='Structured reference such as 1.1.1 or 1.2.1.')
    onboarding_id = fields.Many2one('qaco.client.onboarding', string='Onboarding', required=True, ondelete='cascade')
    template_id = fields.Many2one('audit.onboarding.checklist.template', string='Template Reference', ondelete='set null')
    name = fields.Char(string='Checklist Requirement', required=True)
    onboarding_area = fields.Selection(ONBOARDING_AREAS, string='Onboarding Area', required=True)
    standard_ids = fields.Many2many('audit.standard.library', string='Standard Reference')
    mandatory = fields.Boolean(string='Mandatory', default=True)
    completed = fields.Boolean(string='Completed', default=False)
    completed_on = fields.Datetime(string='Completed On', readonly=True)
    completed_by = fields.Many2one('res.users', string='Completed By', readonly=True)
    notes = fields.Text(string='Notes')
    sequence = fields.Integer(default=10)

    def write(self, vals):
        completed_flag = vals.get('completed')
        res = super().write(vals)
        if completed_flag is not None:
            newly_completed = self.filtered(lambda r: r.completed and not r.completed_on)
            if newly_completed:
                super(AuditOnboardingChecklist, newly_completed).write({
                    'completed_on': fields.Datetime.now(),
                    'completed_by': self.env.user.id,
                })
            reset_records = self.filtered(lambda r: not r.completed)
            if reset_records:
                super(AuditOnboardingChecklist, reset_records).write({
                    'completed_on': False,
                    'completed_by': False,
                })
        return res
