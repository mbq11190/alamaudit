# -*- coding: utf-8 -*-
from odoo import models, fields, api


class QacoAudit(models.Model):
    _inherit = 'qaco.audit'

    # Quality Review
    quality_review_id = fields.Many2one(
        'qaco.quality.review',
        string='Quality Review',
        compute='_compute_quality_review_id',
        store=True
    )
    quality_review_state = fields.Selection(
        related='quality_review_id.state',
        string='Quality Review Status',
        store=True
    )
    quality_review_count = fields.Integer(
        string='Quality Review Count',
        compute='_compute_quality_review_count'
    )

    @api.depends('id')
    def _compute_quality_review_id(self):
        for record in self:
            quality_review = self.env['qaco.quality.review'].search(
                [('audit_id', '=', record.id)], limit=1
            )
            record.quality_review_id = quality_review.id if quality_review else False

    def _compute_quality_review_count(self):
        for record in self:
            record.quality_review_count = self.env['qaco.quality.review'].search_count(
                [('audit_id', '=', record.id)]
            )

    def action_open_quality_review(self):
        self.ensure_one()
        
        existing_review = self.env['qaco.quality.review'].search(
            [('audit_id', '=', self.id)], limit=1
        )
        
        if existing_review:
            return {
                'name': 'Quality Review',
                'type': 'ir.actions.act_window',
                'res_model': 'qaco.quality.review',
                'view_mode': 'form',
                'res_id': existing_review.id,
                'target': 'current',
                'context': {'default_audit_id': self.id}
            }
        else:
            return {
                'name': 'Quality Review',
                'type': 'ir.actions.act_window',
                'res_model': 'qaco.quality.review',
                'view_mode': 'form',
                'target': 'current',
                'context': {'default_audit_id': self.id}
            }
