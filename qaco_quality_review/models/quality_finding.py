# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class QacoQualityFinding(models.Model):
    _name = 'qaco.quality.finding'
    _description = 'Quality Review Finding'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'severity desc, id desc'

    quality_review_id = fields.Many2one(
        'qaco.quality.review',
        string='Quality Review',
        required=True,
        ondelete='cascade'
    )
    name = fields.Char(
        string='Finding Title',
        required=True,
        tracking=True
    )
    finding_number = fields.Char(
        string='Finding Number',
        tracking=True
    )
    severity = fields.Selection([
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ], string='Severity', required=True, default='medium', tracking=True)
    category = fields.Selection([
        ('planning', 'Planning'),
        ('risk_assessment', 'Risk Assessment'),
        ('execution', 'Execution'),
        ('evidence', 'Evidence'),
        ('documentation', 'Documentation'),
        ('independence', 'Independence'),
        ('professional_judgment', 'Professional Judgment'),
        ('reporting', 'Reporting'),
        ('quality_control', 'Quality Control'),
        ('compliance', 'Compliance'),
        ('other', 'Other'),
    ], string='Category', required=True, tracking=True)
    description = fields.Text(
        string='Finding Description',
        required=True,
        tracking=True
    )
    impact = fields.Text(
        string='Impact/Risk',
        tracking=True
    )
    recommendation = fields.Text(
        string='Recommendation',
        tracking=True
    )
    
    # Remediation
    state = fields.Selection([
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('accepted_risk', 'Accepted Risk'),
    ], string='Status', default='open', required=True, tracking=True)
    responsible_person_id = fields.Many2one(
        'res.users',
        string='Responsible Person',
        tracking=True
    )
    due_date = fields.Date(
        string='Due Date',
        tracking=True
    )
    remediation_action = fields.Text(
        string='Remediation Action',
        tracking=True
    )
    remediation_date = fields.Date(
        string='Remediation Date',
        tracking=True
    )
    remediation_evidence = fields.Binary(
        string='Remediation Evidence',
        attachment=True
    )
    remediation_evidence_filename = fields.Char(
        string='Evidence Filename'
    )
    
    # Verification
    verified_by_id = fields.Many2one(
        'res.users',
        string='Verified By',
        tracking=True
    )
    verification_date = fields.Date(
        string='Verification Date',
        tracking=True
    )
    verification_notes = fields.Text(
        string='Verification Notes',
        tracking=True
    )
    
    # Reference
    related_workpaper = fields.Char(
        string='Related Working Paper',
        tracking=True
    )
    related_section = fields.Char(
        string='Related Audit Section',
        tracking=True
    )
    
    notes = fields.Text(
        string='Additional Notes',
        tracking=True
    )

    def action_start_remediation(self):
        self.ensure_one()
        if not self.responsible_person_id:
            raise ValidationError('Please assign a responsible person before starting remediation.')
        self.write({'state': 'in_progress'})

    def action_mark_resolved(self):
        self.ensure_one()
        if not self.remediation_action:
            raise ValidationError('Please document the remediation action before marking as resolved.')
        self.write({
            'state': 'resolved',
            'remediation_date': fields.Date.context_today(self),
            'verified_by_id': self.env.user.id,
            'verification_date': fields.Date.context_today(self)
        })

    def action_accept_risk(self):
        self.ensure_one()
        self.write({'state': 'accepted_risk'})

    def action_reopen(self):
        self.ensure_one()
        self.write({'state': 'open'})
