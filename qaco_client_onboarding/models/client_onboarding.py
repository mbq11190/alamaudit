# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class QacoClientOnboarding(models.Model):
    _name = 'qaco.client.onboarding'
    _description = 'Client Onboarding and Acceptance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    # Basic Information
    name = fields.Char(
        string='Onboarding Reference',
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
    onboarding_date = fields.Date(
        string='Onboarding Date',
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
    responsible_manager_id = fields.Many2one(
        'res.users',
        string='Responsible Manager',
        tracking=True,
        domain=lambda self: [('groups_id', 'in', [self.env.ref('qaco_audit.group_audit_manager').id])]
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('kyc_review', 'KYC Review'),
        ('conflict_check', 'Conflict Check'),
        ('independence_check', 'Independence Check'),
        ('acceptance_review', 'Acceptance Review'),
        ('proposal_preparation', 'Proposal Preparation'),
        ('engagement_letter', 'Engagement Letter'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', required=True, tracking=True)

    # Client Acceptance Evaluation
    acceptance_evaluation = fields.Selection([
        ('low_risk', 'Low Risk'),
        ('medium_risk', 'Medium Risk'),
        ('high_risk', 'High Risk'),
    ], string='Client Risk Rating', tracking=True)
    is_new_client = fields.Boolean(
        string='New Client',
        default=True,
        tracking=True
    )
    is_recurring_client = fields.Boolean(
        string='Recurring Client',
        compute='_compute_is_recurring_client',
        store=True
    )
    client_since = fields.Date(
        string='Client Since',
        tracking=True
    )
    previous_auditor = fields.Char(
        string='Previous Auditor',
        tracking=True
    )
    reason_for_change = fields.Text(
        string='Reason for Auditor Change',
        tracking=True
    )
    previous_auditor_contacted = fields.Boolean(
        string='Previous Auditor Contacted',
        default=False,
        tracking=True
    )
    previous_auditor_response = fields.Text(
        string='Previous Auditor Response',
        tracking=True
    )

    # KYC Documentation
    kyc_documents_complete = fields.Boolean(
        string='KYC Documents Complete',
        default=False,
        tracking=True
    )
    company_registration = fields.Binary(
        string='Company Registration Certificate',
        attachment=True
    )
    company_registration_filename = fields.Char(
        string='Registration Filename'
    )
    articles_of_association = fields.Binary(
        string='Articles of Association',
        attachment=True
    )
    articles_filename = fields.Char(
        string='Articles Filename'
    )
    beneficial_ownership_docs = fields.Binary(
        string='Beneficial Ownership Documentation',
        attachment=True
    )
    beneficial_ownership_filename = fields.Char(
        string='Beneficial Ownership Filename'
    )
    director_id_copies = fields.Binary(
        string='Director ID Copies',
        attachment=True
    )
    director_id_filename = fields.Char(
        string='Director ID Filename'
    )
    address_proof = fields.Binary(
        string='Proof of Address',
        attachment=True
    )
    address_proof_filename = fields.Char(
        string='Address Proof Filename'
    )
    tax_registration = fields.Binary(
        string='Tax Registration Certificate',
        attachment=True
    )
    tax_registration_filename = fields.Char(
        string='Tax Registration Filename'
    )

    # Due Diligence
    background_check_completed = fields.Boolean(
        string='Background Check Completed',
        default=False,
        tracking=True
    )
    background_check_date = fields.Date(
        string='Background Check Date',
        tracking=True
    )
    background_check_findings = fields.Text(
        string='Background Check Findings',
        tracking=True
    )
    sanctions_screening_completed = fields.Boolean(
        string='Sanctions Screening Completed',
        default=False,
        tracking=True
    )
    sanctions_screening_result = fields.Selection([
        ('clear', 'Clear'),
        ('matched', 'Matched - Reviewed'),
        ('escalated', 'Escalated'),
    ], string='Sanctions Result', tracking=True)
    pep_screening_completed = fields.Boolean(
        string='PEP Screening Completed',
        default=False,
        tracking=True
    )
    pep_screening_result = fields.Selection([
        ('not_pep', 'Not a PEP'),
        ('pep_enhanced_dd', 'PEP - Enhanced DD Required'),
    ], string='PEP Result', tracking=True)
    adverse_media_check = fields.Boolean(
        string='Adverse Media Check Completed',
        default=False,
        tracking=True
    )
    adverse_media_findings = fields.Text(
        string='Adverse Media Findings',
        tracking=True
    )

    # Conflict of Interest
    conflict_check_completed = fields.Boolean(
        string='Conflict Check Completed',
        default=False,
        tracking=True
    )
    conflict_check_date = fields.Date(
        string='Conflict Check Date',
        tracking=True
    )
    conflicts_identified = fields.Boolean(
        string='Conflicts Identified',
        default=False,
        tracking=True
    )
    conflict_details = fields.Text(
        string='Conflict Details',
        tracking=True
    )
    conflict_resolution = fields.Text(
        string='Conflict Resolution/Safeguards',
        tracking=True
    )
    conflict_waiver_obtained = fields.Boolean(
        string='Conflict Waiver Obtained',
        default=False,
        tracking=True
    )

    # Independence Assessment
    independence_check_completed = fields.Boolean(
        string='Independence Check Completed',
        default=False,
        tracking=True
    )
    independence_threats_identified = fields.Boolean(
        string='Independence Threats Identified',
        default=False,
        tracking=True
    )
    independence_threat_details = fields.Text(
        string='Independence Threat Details',
        tracking=True
    )
    independence_safeguards = fields.Text(
        string='Independence Safeguards',
        tracking=True
    )
    rotation_requirements_met = fields.Boolean(
        string='Rotation Requirements Met',
        default=True,
        tracking=True
    )
    rotation_notes = fields.Text(
        string='Rotation Notes',
        tracking=True
    )

    # Competence and Resources
    technical_competence_assessed = fields.Boolean(
        string='Technical Competence Assessed',
        default=False,
        tracking=True
    )
    industry_expertise_available = fields.Boolean(
        string='Industry Expertise Available',
        default=False,
        tracking=True
    )
    specialist_skills_required = fields.Text(
        string='Specialist Skills Required',
        tracking=True
    )
    resources_available = fields.Boolean(
        string='Sufficient Resources Available',
        default=False,
        tracking=True
    )
    resource_notes = fields.Text(
        string='Resource Assessment Notes',
        tracking=True
    )

    # Fee Proposal
    proposed_fee = fields.Monetary(
        string='Proposed Audit Fee',
        currency_field='currency_id',
        tracking=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    fee_basis = fields.Selection([
        ('fixed', 'Fixed Fee'),
        ('time_based', 'Time-Based'),
        ('value_based', 'Value-Based'),
    ], string='Fee Basis', tracking=True)
    estimated_hours = fields.Float(
        string='Estimated Hours',
        tracking=True
    )
    fee_proposal_sent = fields.Boolean(
        string='Fee Proposal Sent',
        default=False,
        tracking=True
    )
    fee_proposal_date = fields.Date(
        string='Fee Proposal Date',
        tracking=True
    )
    fee_accepted = fields.Boolean(
        string='Fee Accepted by Client',
        default=False,
        tracking=True
    )
    fee_acceptance_date = fields.Date(
        string='Fee Acceptance Date',
        tracking=True
    )

    # Engagement Letter
    engagement_letter_prepared = fields.Boolean(
        string='Engagement Letter Prepared',
        default=False,
        tracking=True
    )
    engagement_letter = fields.Binary(
        string='Engagement Letter Document',
        attachment=True
    )
    engagement_letter_filename = fields.Char(
        string='Engagement Letter Filename'
    )
    engagement_letter_sent = fields.Boolean(
        string='Engagement Letter Sent',
        default=False,
        tracking=True
    )
    engagement_letter_sent_date = fields.Date(
        string='Letter Sent Date',
        tracking=True
    )
    engagement_letter_signed = fields.Boolean(
        string='Engagement Letter Signed',
        default=False,
        tracking=True
    )
    engagement_letter_signed_date = fields.Date(
        string='Letter Signed Date',
        tracking=True
    )
    signed_engagement_letter = fields.Binary(
        string='Signed Engagement Letter',
        attachment=True
    )
    signed_engagement_letter_filename = fields.Char(
        string='Signed Letter Filename'
    )

    # Terms and Conditions
    terms_accepted = fields.Boolean(
        string='Terms & Conditions Accepted',
        default=False,
        tracking=True
    )
    terms_acceptance_date = fields.Date(
        string='Terms Acceptance Date',
        tracking=True
    )
    data_privacy_consent = fields.Boolean(
        string='Data Privacy Consent Obtained',
        default=False,
        tracking=True
    )
    aml_questionnaire_completed = fields.Boolean(
        string='AML Questionnaire Completed',
        default=False,
        tracking=True
    )

    # Approval and Notes
    acceptance_decision = fields.Selection([
        ('accept', 'Accept'),
        ('accept_with_conditions', 'Accept with Conditions'),
        ('reject', 'Reject'),
    ], string='Acceptance Decision', tracking=True)
    acceptance_conditions = fields.Text(
        string='Acceptance Conditions',
        tracking=True
    )
    rejection_reason = fields.Text(
        string='Rejection Reason',
        tracking=True
    )
    partner_approval = fields.Boolean(
        string='Partner Approval',
        default=False,
        tracking=True
    )
    partner_approval_date = fields.Date(
        string='Partner Approval Date',
        tracking=True
    )
    notes = fields.Html(
        string='Additional Notes',
        tracking=True
    )

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('qaco.client.onboarding') or 'New'
        return super(QacoClientOnboarding, self).create(vals)

    @api.depends('is_new_client')
    def _compute_is_recurring_client(self):
        for record in self:
            record.is_recurring_client = not record.is_new_client

    def action_start_kyc_review(self):
        self.ensure_one()
        self.write({'state': 'kyc_review'})

    def action_start_conflict_check(self):
        self.ensure_one()
        if not self.kyc_documents_complete:
            raise ValidationError('Please complete KYC documentation before proceeding to conflict check.')
        self.write({'state': 'conflict_check'})

    def action_start_independence_check(self):
        self.ensure_one()
        if not self.conflict_check_completed:
            raise ValidationError('Please complete conflict check before proceeding to independence assessment.')
        self.write({'state': 'independence_check'})

    def action_start_acceptance_review(self):
        self.ensure_one()
        if not self.independence_check_completed:
            raise ValidationError('Please complete independence check before proceeding to acceptance review.')
        self.write({'state': 'acceptance_review'})

    def action_prepare_proposal(self):
        self.ensure_one()
        self.write({'state': 'proposal_preparation'})

    def action_prepare_engagement_letter(self):
        self.ensure_one()
        if not self.fee_accepted:
            raise ValidationError('Fee proposal must be accepted before preparing engagement letter.')
        self.write({'state': 'engagement_letter'})

    def action_approve(self):
        self.ensure_one()
        if not self.engagement_letter_signed:
            raise ValidationError('Engagement letter must be signed before approval.')
        self.write({
            'state': 'approved',
            'acceptance_decision': 'accept',
            'partner_approval': True,
            'partner_approval_date': fields.Date.context_today(self)
        })

    def action_reject(self):
        self.ensure_one()
        self.write({
            'state': 'rejected',
            'acceptance_decision': 'reject'
        })

    def action_reset_to_draft(self):
        self.ensure_one()
        self.write({'state': 'draft'})
