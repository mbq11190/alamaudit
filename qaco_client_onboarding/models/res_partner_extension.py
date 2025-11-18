from odoo import fields, models


class ResPartnerAuditExtension(models.Model):
    _inherit = 'res.partner'

    audit_engagement_ids = fields.One2many('qaco.audit.engagement', 'client_id', string='Audit Engagements')
    is_qaco_audit_client = fields.Boolean(string='Audit Client', default=False)