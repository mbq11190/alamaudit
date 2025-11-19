# -*- coding: utf-8 -*-
"""Audit model extensions for quality review smart button."""

from odoo import models


class Audit(models.Model):
    _inherit = 'qaco.audit'

    def action_open_quality_review(self):
        """Open or lazily create the quality review shell for this audit."""
        self.ensure_one()
        review = self.env['qaco.quality.review'].search([('audit_id', '=', self.id)], limit=1)
        if not review:
            review = self.env['qaco.quality.review'].create({'audit_id': self.id})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Quality Review',
            'res_model': 'qaco.quality.review',
            'res_id': review.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_audit_id': self.id},
        }
