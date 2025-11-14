from odoo import models, fields, api
import werkzeug.urls


class auditAttachment(models.Model):
    _name = 'audit.attachment'
    _description = 'audit Attachment'

    name = fields.Char(string='File Name')
    file = fields.Binary(string='File Size')
    audit_id = fields.Many2one('qaco.audit', string='Audit')

    def download_attachment(self):
        """Return an action opening the binary file in the browser."""
        self.ensure_one()
        url = '/web/content/%s/%s/file/%s?download=true' % (
            self._name,
            self.id,
            werkzeug.urls.url_quote(self.name or 'file'),
        )
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    def delete_attachment(self):
        self.unlink()