# -*- coding: utf-8 -*-
from odoo import models, fields, api


class QacoDeliverableItem(models.Model):
    _name = 'qaco.deliverable.item'
    _description = 'Deliverable Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id'

    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    deliverable_id = fields.Many2one(
        'qaco.deliverables',
        string='Deliverables',
        required=True,
        ondelete='cascade'
    )
    name = fields.Char(
        string='Deliverable Name',
        required=True,
        tracking=True
    )
    deliverable_type = fields.Selection([
        ('audit_report', 'Audit Report'),
        ('financial_statements', 'Financial Statements'),
        ('management_letter', 'Management Letter'),
        ('management_representation', 'Management Representation Letter'),
        ('tax_return', 'Tax Return'),
        ('compliance_certificate', 'Compliance Certificate'),
        ('regulatory_filing', 'Regulatory Filing'),
        ('other', 'Other'),
    ], string='Type', required=True, tracking=True)
    description = fields.Text(
        string='Description',
        tracking=True
    )
    
    # Document Management
    document = fields.Binary(
        string='Document',
        attachment=True
    )
    document_filename = fields.Char(
        string='Document Filename'
    )
    version = fields.Char(
        string='Version',
        default='1.0',
        tracking=True
    )
    revision_number = fields.Integer(
        string='Revision Number',
        default=1,
        tracking=True
    )
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('delivered', 'Delivered'),
    ], string='Status', default='draft', required=True, tracking=True)
    
    # Prepared and Reviewed By
    prepared_by_id = fields.Many2one(
        'res.users',
        string='Prepared By',
        tracking=True
    )
    reviewed_by_id = fields.Many2one(
        'res.users',
        string='Reviewed By',
        tracking=True
    )
    approved_by_id = fields.Many2one(
        'res.users',
        string='Approved By',
        tracking=True
    )
    
    # Dates
    preparation_date = fields.Date(
        string='Preparation Date',
        tracking=True
    )
    review_date = fields.Date(
        string='Review Date',
        tracking=True
    )
    approval_date = fields.Date(
        string='Approval Date',
        tracking=True
    )
    
    # Distribution
    copies_required = fields.Integer(
        string='Copies Required',
        default=1
    )
    distribution_list = fields.Text(
        string='Distribution List',
        tracking=True
    )
    
    # Notes
    notes = fields.Text(
        string='Notes',
        tracking=True
    )

    def action_start_progress(self):
        self.ensure_one()
        self.write({
            'state': 'in_progress',
            'preparation_date': fields.Date.context_today(self)
        })

    def action_submit_for_review(self):
        self.ensure_one()
        from odoo.exceptions import ValidationError
        if not self.document:
            raise ValidationError('Please upload a document before submitting for review.')
        self.write({'state': 'review'})

    def action_approve(self):
        self.ensure_one()
        self.write({
            'state': 'approved',
            'approval_date': fields.Date.context_today(self),
            'approved_by_id': self.env.user.id
        })

    def action_deliver(self):
        self.ensure_one()
        from odoo.exceptions import ValidationError
        if self.state != 'approved':
            raise ValidationError('Item must be approved before delivery.')
        self.write({'state': 'delivered'})
