# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class QacoDeliverables(models.Model):
    _name = 'qaco.deliverables'
    _description = 'Audit Deliverables Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    # Basic Information
    name = fields.Char(
        string='Deliverables Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New',
        tracking=True
    )
    audit_id = fields.Many2one(
        'qaco.audit',
        string='Audit Engagement',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    client_id = fields.Many2one(
        'res.partner',
        string='Client',
        related='audit_id.client_id',
        store=True,
        readonly=True
    )
    finalisation_id = fields.Many2one(
        'qaco.finalisation.phase',
        string='Finalisation Phase',
        tracking=True
    )
    deliverables_date = fields.Date(
        string='Deliverables Date',
        default=fields.Date.context_today,
        required=True,
        tracking=True
    )
    responsible_partner_id = fields.Many2one(
        'res.users',
        string='Responsible Partner',
        tracking=True,
        domain=lambda self: [('groups_id', 'in', [self.env.ref('qaco_audit.group_audit_partner').id])]
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('preparation', 'Preparation'),
        ('review', 'Review'),
        ('ready', 'Ready for Delivery'),
        ('delivered', 'Delivered'),
        ('acknowledged', 'Client Acknowledged'),
        ('completed', 'Completed'),
    ], string='Status', default='draft', required=True, tracking=True)

    # Deliverable Items
    deliverable_item_ids = fields.One2many(
        'qaco.deliverable.item',
        'deliverable_id',
        string='Deliverable Items',
        tracking=True
    )
    deliverable_count = fields.Integer(
        string='Deliverable Count',
        compute='_compute_deliverable_count',
        store=True
    )

    # Delivery Information
    scheduled_delivery_date = fields.Date(
        string='Scheduled Delivery Date',
        tracking=True
    )
    actual_delivery_date = fields.Date(
        string='Actual Delivery Date',
        tracking=True
    )
    delivery_method = fields.Selection([
        ('email', 'Email'),
        ('portal', 'Client Portal'),
        ('hand_delivery', 'Hand Delivery'),
        ('courier', 'Courier'),
        ('registered_mail', 'Registered Mail'),
    ], string='Delivery Method', tracking=True)
    delivery_contact_id = fields.Many2one(
        'res.partner',
        string='Delivery Contact',
        tracking=True
    )
    delivery_email = fields.Char(
        string='Delivery Email',
        tracking=True
    )
    delivery_address = fields.Text(
        string='Delivery Address',
        tracking=True
    )
    tracking_number = fields.Char(
        string='Tracking Number',
        tracking=True
    )

    # Client Acknowledgment
    acknowledgment_required = fields.Boolean(
        string='Acknowledgment Required',
        default=True,
        tracking=True
    )
    acknowledgment_received = fields.Boolean(
        string='Acknowledgment Received',
        default=False,
        tracking=True
    )
    acknowledgment_date = fields.Date(
        string='Acknowledgment Date',
        tracking=True
    )
    acknowledged_by = fields.Char(
        string='Acknowledged By',
        tracking=True
    )
    acknowledgment_document = fields.Binary(
        string='Acknowledgment Document',
        attachment=True
    )
    acknowledgment_filename = fields.Char(
        string='Acknowledgment Filename'
    )

    # Cover Letter
    cover_letter_required = fields.Boolean(
        string='Cover Letter Required',
        default=True,
        tracking=True
    )
    cover_letter = fields.Binary(
        string='Cover Letter',
        attachment=True
    )
    cover_letter_filename = fields.Char(
        string='Cover Letter Filename'
    )
    cover_letter_notes = fields.Text(
        string='Cover Letter Notes',
        tracking=True
    )

    # Follow-up
    follow_up_required = fields.Boolean(
        string='Follow-up Required',
        default=False,
        tracking=True
    )
    follow_up_date = fields.Date(
        string='Follow-up Date',
        tracking=True
    )
    follow_up_notes = fields.Text(
        string='Follow-up Notes',
        tracking=True
    )
    follow_up_completed = fields.Boolean(
        string='Follow-up Completed',
        default=False,
        tracking=True
    )

    # Regulatory Submissions
    regulatory_filing_required = fields.Boolean(
        string='Regulatory Filing Required',
        default=False,
        tracking=True
    )
    regulatory_body = fields.Char(
        string='Regulatory Body',
        tracking=True
    )
    filing_deadline = fields.Date(
        string='Filing Deadline',
        tracking=True
    )
    filing_completed = fields.Boolean(
        string='Filing Completed',
        default=False,
        tracking=True
    )
    filing_date = fields.Date(
        string='Filing Date',
        tracking=True
    )
    filing_reference = fields.Char(
        string='Filing Reference',
        tracking=True
    )

    # Notes
    notes = fields.Html(
        string='Notes',
        tracking=True
    )

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('qaco.deliverables') or 'New'
        return super(QacoDeliverables, self).create(vals)

    @api.depends('deliverable_item_ids')
    def _compute_deliverable_count(self):
        for record in self:
            record.deliverable_count = len(record.deliverable_item_ids)

    def action_start_preparation(self):
        self.ensure_one()
        self.write({'state': 'preparation'})

    def action_submit_for_review(self):
        self.ensure_one()
        if not self.deliverable_item_ids:
            raise ValidationError('Please add at least one deliverable item before submitting for review.')
        self.write({'state': 'review'})

    def action_mark_ready(self):
        self.ensure_one()
        incomplete_items = self.deliverable_item_ids.filtered(lambda x: x.state != 'approved')
        if incomplete_items:
            raise ValidationError('All deliverable items must be approved before marking as ready.')
        self.write({'state': 'ready'})

    def action_deliver(self):
        self.ensure_one()
        if not self.delivery_method:
            raise ValidationError('Please specify a delivery method.')
        self.write({
            'state': 'delivered',
            'actual_delivery_date': fields.Date.context_today(self)
        })

    def action_acknowledge(self):
        self.ensure_one()
        self.write({
            'state': 'acknowledged',
            'acknowledgment_received': True,
            'acknowledgment_date': fields.Date.context_today(self)
        })

    def action_complete(self):
        self.ensure_one()
        if self.acknowledgment_required and not self.acknowledgment_received:
            raise ValidationError('Client acknowledgment is required before completing.')
        if self.regulatory_filing_required and not self.filing_completed:
            raise ValidationError('Regulatory filing must be completed before marking as complete.')
        self.write({'state': 'completed'})

    def action_reset_to_draft(self):
        self.ensure_one()
        self.write({'state': 'draft'})


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
        if self.state != 'approved':
            raise ValidationError('Item must be approved before delivery.')
        self.write({'state': 'delivered'})
