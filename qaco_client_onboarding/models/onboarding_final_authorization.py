# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
import base64

_logger = logging.getLogger(__name__)

DECISION_SELECTION = [
    ('accept', 'Accept'),
    ('decline', 'Decline'),
    ('conditions', 'Accept - Conditional'),
]

CONDITION_TYPES = [
    ('engagement_letter', 'Signed engagement letter / agreed scope'),
    ('fee_retainer', 'Fee retainer / payment milestones agreed'),
    ('information_access', 'Information access / management responsibility confirmations'),
    ('governance_approval', 'Governance approvals obtained'),
    ('independence_resolution', 'Resolution of independence threats / conflicts'),
    ('other', 'Other'),
]

CONDITION_STATUS = [
    ('pending', 'Pending'),
    ('met', 'Met'),
    ('waived', 'Waived'),
]


class FinalAuthorizationCondition(models.Model):
    _name = 'qaco.onboarding.final.authorization.condition'
    _description = 'Final authorization condition'

    onboarding_id = fields.Many2one('qaco.client.onboarding', required=True, ondelete='cascade', index=True)
    authorization_id = fields.Many2one('qaco.onboarding.final.authorization', ondelete='cascade')
    condition_type = fields.Selection(CONDITION_TYPES, string='Condition type')
    owner = fields.Selection([('client', 'Client'), ('firm', 'Firm')], string='Owner')
    due_date = fields.Date(string='Due date')
    evidence_attachment = fields.Many2one('ir.attachment', string='Evidence')
    note = fields.Text(string='Notes')
    status = fields.Selection(CONDITION_STATUS, default='pending')


class FinalAuthorization(models.Model):
    _name = 'qaco.onboarding.final.authorization'
    _description = 'Final Authorization Record'

    onboarding_id = fields.Many2one('qaco.client.onboarding', required=True, ondelete='cascade', index=True)
    decision = fields.Selection(DECISION_SELECTION, required=True)
    decision_rationale = fields.Text(string='Decision rationale')
    decision_date = fields.Datetime(string='Decision date', required=True, default=fields.Datetime.now)
    approver_id = fields.Many2one('res.users', string='Approver', default=lambda self: self.env.uid)
    digital_signature = fields.Binary(string='Digital signature')
    condition_ids = fields.One2many('qaco.onboarding.final.authorization.condition', 'authorization_id', string='Conditions')
    eqcr_required = fields.Boolean(string='EQCR required')
    eqcr_basis = fields.Text(string='EQCR basis / rationale')
    eqcr_partner_id = fields.Many2one('res.users', string='Assigned EQCR partner')
    team_competence_confirmed = fields.Boolean(string='Team competence confirmed')
    resources_timeline_confirmed = fields.Boolean(string='Resources & timeline confirmed')
    specialists_required = fields.Boolean(string='Specialists required')
    specialists_notes = fields.Text(string='Specialists notes')
    created_by = fields.Many2one('res.users', string='Created by', default=lambda self: self.env.uid)


class FinalAuthorizationWizard(models.TransientModel):
    _name = 'qaco.onboarding.final.authorization.wizard'
    _description = 'Finalize Engagement Authorization'

    onboarding_id = fields.Many2one('qaco.client.onboarding', required=True, ondelete='cascade')
    decision = fields.Selection(DECISION_SELECTION, required=True)
    decision_rationale = fields.Text(string='Decision rationale')
    eqcr_required = fields.Boolean(string='EQCR required')
    eqcr_basis = fields.Text(string='EQCR basis / rationale')
    eqcr_partner_id = fields.Many2one('res.users', string='Assigned EQCR partner')
    team_competence_confirmed = fields.Boolean(string='Team competence confirmed')
    resources_timeline_confirmed = fields.Boolean(string='Resources & timeline confirmed')
    specialists_required = fields.Boolean(string='Specialists required')
    specialists_notes = fields.Text(string='Specialists notes')
    include_summary_pack = fields.Boolean(string='Generate Onboarding Summary Pack (bundle)', default=True)
    generate_certificate = fields.Boolean(string='Generate Completion Certificate', default=True)
    planning_policy = fields.Selection([('locked', 'Lock Planning until conditions met'), ('partial', 'Allow Planning; restrict execution until conditions met')], string='Conditional planning policy', default='locked')

    def action_confirm_authorization(self):
        self.ensure_one()
        onboarding = self.onboarding_id
        # Run system prechecks
        onboarding._check_final_authorization_preconditions()
        # If decision is conditional, ensure conditions are present or wizard will create none - allow empty but require policy handling
        auth = self.env['qaco.onboarding.final.authorization'].create({
            'onboarding_id': onboarding.id,
            'decision': self.decision,
            'decision_rationale': self.decision_rationale,
            'eqcr_required': self.eqcr_required,
            'eqcr_basis': self.eqcr_basis,
            'eqcr_partner_id': self.eqcr_partner_id.id if self.eqcr_partner_id else False,
            'team_competence_confirmed': self.team_competence_confirmed,
            'resources_timeline_confirmed': self.resources_timeline_confirmed,
            'specialists_required': self.specialists_required,
            'specialists_notes': self.specialists_notes,
        })
        # persist attestation flags on onboarding for reference
        onboarding.write({
            'engagement_decision': self.decision,
            'engagement_justification': self.decision_rationale,
            'eqcr_partner_id': self.eqcr_partner_id.id if self.eqcr_partner_id else False,
            'team_competence_confirmed': self.team_competence_confirmed,
            'resources_timeline_confirmed': self.resources_timeline_confirmed,
            'specialists_required': self.specialists_required,
            'specialists_notes': self.specialists_notes,
        })
        # Handle decisions
        if self.decision == 'decline':
            onboarding.write({'state': 'locked'})
            onboarding._log_action('Final authorization: Declined', notes=self.decision_rationale)
            # generate decline memo/report (use existing acceptance report with modification or dedicated template)
            try:
                report = self.env.ref('qaco_client_onboarding.report_client_onboarding_pdf', raise_if_not_found=False)
                if report and auth:
                    pdf = report._render_qweb_pdf([onboarding.id])[0]
                    att = self.env['ir.attachment'].create({
                        'name': f'decline_memo_{onboarding.id}.pdf',
                        'type': 'binary',
                        'datas': base64.b64encode(pdf).decode('ascii'),
                        'res_model': 'qaco.client.onboarding',
                        'res_id': onboarding.id,
                        'mimetype': 'application/pdf',
                    })
            except Exception:
                _logger.exception('Failed to generate decline memo for onboarding %s', onboarding.id)
        else:
            # Accept or conditional -> set partner_approved state
            onboarding.write({'state': 'partner_approved'})
            onboarding._log_action('Final authorization: Partner approved', notes=self.decision_rationale)
            # Generate certificate and summary pack if requested (call onboarding helper)
            if self.generate_certificate:
                try:
                    report = self.env.ref('qaco_client_onboarding.report_client_onboarding_pdf', raise_if_not_found=False)
                    if report:
                        pdf = report._render_qweb_pdf([onboarding.id])[0]
                        self.env['ir.attachment'].create({
                            'name': f'onboarding_certificate_{onboarding.id}.pdf',
                            'type': 'binary',
                            'datas': base64.b64encode(pdf).decode('ascii'),
                            'res_model': 'qaco.client.onboarding',
                            'res_id': onboarding.id,
                            'mimetype': 'application/pdf',
                        })
                except Exception:
                    _logger.exception('Failed to generate acceptance/certificate report for onboarding %s', onboarding.id)
            if self.include_summary_pack:
                try:
                    onboarding.action_generate_onboarding_summary_pack()
                except Exception:
                    _logger.exception('Failed to generate onboarding summary pack for onboarding %s', onboarding.id)
        return {'type': 'ir.actions.act_window_close'}
