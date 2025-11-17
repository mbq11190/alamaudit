# -*- coding: utf-8 -*-
from odoo import models, fields, api


class QacoQualityChecklistItem(models.Model):
    _name = 'qaco.quality.checklist.item'
    _description = 'Quality Review Checklist Item'
    _order = 'sequence, id'

    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    quality_review_id = fields.Many2one(
        'qaco.quality.review',
        string='Quality Review',
        required=True,
        ondelete='cascade'
    )
    name = fields.Char(
        string='Checklist Item',
        required=True,
        tracking=True
    )
    category = fields.Selection([
        ('planning', 'Planning'),
        ('execution', 'Execution'),
        ('finalisation', 'Finalisation'),
        ('documentation', 'Documentation'),
        ('independence', 'Independence'),
        ('quality_control', 'Quality Control'),
        ('professional_standards', 'Professional Standards'),
        ('regulatory_compliance', 'Regulatory Compliance'),
    ], string='Category', required=True, tracking=True)
    description = fields.Text(
        string='Description',
        tracking=True
    )
    completed = fields.Boolean(
        string='Completed',
        default=False,
        tracking=True
    )
    completion_date = fields.Date(
        string='Completion Date',
        tracking=True
    )
    reviewed_by_id = fields.Many2one(
        'res.users',
        string='Reviewed By',
        tracking=True
    )
    result = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('needs_improvement', 'Needs Improvement'),
        ('not_applicable', 'Not Applicable'),
    ], string='Result', tracking=True)
    comments = fields.Text(
        string='Comments',
        tracking=True
    )
    reference_document = fields.Char(
        string='Reference Document',
        tracking=True,
        help='Working paper reference or document location'
    )

    def action_mark_complete(self):
        self.ensure_one()
        self.write({
            'completed': True,
            'completion_date': fields.Date.context_today(self),
            'reviewed_by_id': self.env.user.id
        })

    def action_mark_incomplete(self):
        self.ensure_one()
        self.write({
            'completed': False,
            'completion_date': False
        })
