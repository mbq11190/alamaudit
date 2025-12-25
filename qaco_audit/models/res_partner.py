from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"
    _description = "Partner enhancements for QACO Audit"

    audit_engagement_ids = fields.One2many(
        "qaco.audit.engagement", "client_id", string="Audit Engagements"
    )
    is_qaco_audit_client = fields.Boolean(string="Audit Client")
