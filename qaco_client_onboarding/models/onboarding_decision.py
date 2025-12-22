# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import base64
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

RISK_RATINGS = [
    ('low', 'Low'),
    ('moderate', 'Moderate'),
    ('high', 'High'),
    ('prohibitive', 'Prohibitive'),
]

DECISION_TYPES = [
    ('accept', 'Accept'),
    ('accept_conditions', 'Accept with Conditions'),
    ('decline', 'Decline'),
    ('withdraw', 'Withdraw'),
]

RISK_DRIVERS = [
    ('management_integrity', 'Management integrity / governance concerns'),
    ('independence_threats', 'Independence threats / conflicts'),
    ('complex_estimates', 'Complex accounting / estimates / judgments'),
    ('going_concern', 'Going concern / liquidity indicators'),
    ('fraud_risk', 'Fraud risk factors / related parties complexity'),
    ('regulatory_scrutiny', 'Regulatory scrutiny / sector risk'),
    ('first_year', 'First-year audit / change of auditor'),
    ('fee_dependency', 'Fee dependency / overdue fees / collection risk'),
    ('data_quality', 'Data quality / system limitations / access constraints'),
    ('geographic', 'Geographic / cross-border / sanctions exposure'),
]


class OnboardingDecision(models.Model):
    _name = 'qaco.onboarding.decision'
    _description = 'Engagement Decision (Go / No-Go)'
    _order = 'decision_date desc, id desc'

    onboarding_id = fields.Many2one('qaco.client.onboarding', required=True, ondelete='cascade', index=True)
    version = fields.Integer(string='Version', default=1)
    decision_type = fields.Selection(DECISION_TYPES, string='Decision', required=True)
    decision_rationale = fields.Text(string='Decision rationale', required=True)
    risk_rating = fields.Selection(RISK_RATINGS, string='Final risk rating', required=True)
    risk_driver_ids = fields.Many2many('qaco.onboarding.decision.driver', string='Risk drivers')
    decision_date = fields.Datetime(string='Decision date', default=fields.Datetime.now)
    decision_by = fields.Many2one('res.users', string='Approved by', default=lambda self: self.env.user)
    locked = fields.Boolean(string='Locked', default=False)
    lock_date = fields.Datetime(string='Lock date')
    lock_by = fields.Many2one('res.users', string='Locked by')
    superseded_by_id = fields.Many2one('qaco.onboarding.decision', string='Superseded by')
    evidence_attachment_ids = fields.Many2many('ir.attachment', string='Evidence attachments')
    auto_generated_certificate = fields.Many2one('ir.attachment', string='Decision memo')
    quality_approval_id = fields.Many2one('res.users', string='Quality/Compliance approver')
    eqcr_acknowledged = fields.Boolean(string='EQCR acknowledged')
    eqcr_partner_id = fields.Many2one('res.users', string='EQCR partner')

    @api.model
    def create(self, vals):
        # Ensure single active version sequence: compute next version for this onboarding
        onboarding_id = vals.get('onboarding_id')
        last = None
        if onboarding_id:
            last = self.search([('onboarding_id', '=', onboarding_id)], order='version desc', limit=1)
            if last:
                vals['version'] = (last.version or 1) + 1
        # If creating an Accept decision, enforce preconditions immediately
        if vals.get('decision_type') in ('accept', 'accept_conditions') and onboarding_id:
            onboarding = self.env['qaco.client.onboarding'].browse(onboarding_id)
            onboarding._check_final_authorization_preconditions()
            # If risk rating is prohibitive, require quality approval
            if vals.get('risk_rating') == 'prohibitive' and not vals.get('quality_approval_id'):
                raise ValidationError(_('Prohibitive risk requires Quality/Compliance approval to accept.'))
        rec = super(OnboardingDecision, self).create(vals)
        # Mark previous decision as superseded and update onboarding latest_decision
        if last:
            try:
                last.sudo().write({'superseded_by_id': rec.id})
            except Exception:
                _logger.exception('Failed to mark previous decision %s as superseded by %s', last.id, rec.id)
        try:
            rec.onboarding_id.write({'latest_decision_id': rec.id})
        except Exception:
            _logger.exception('Failed to set latest_decision_id on onboarding %s', rec.onboarding_id.id)
        return rec

    def action_lock(self, user=None):
        for rec in self:
            rec.locked = True
            rec.lock_date = fields.Datetime.now()
            rec.lock_by = user.id if user else self.env.uid
        return True

    def action_unlock(self, approver=None):
        # Unlock requires partner + quality approval in later check; here we just allow clearing if called
        for rec in self:
            # Only allow unlock if called by a user in Confidential or Manager group
            user = self.env.user
            allowed = user.has_group('qaco_client_onboarding.group_onboarding_confidential') or user.has_group('qaco_audit.group_audit_manager')
            if not allowed:
                raise ValidationError(_('Only authorized users can unlock a decision.'))
            rec.locked = False
            rec.lock_date = False
            rec.lock_by = False
            rec._log_action('Decision unlocked', notes=f'Unlocked by {approver and approver.name or self.env.user.name}')
        return True

    def write(self, vals):
        # Prevent editing locked decisions; require superseding decision instead
        for rec in self:
            if rec.locked:
                # Allow only setting superseded_by_id via admin or system
                if not any(k in vals for k in ('superseded_by_id',)):
                    raise ValidationError(_('Locked decision records cannot be modified. Create a superseding decision instead.'))
        return super(OnboardingDecision, self).write(vals)

    def _log_action(self, action, notes=''):
        # re-use onboarding audit trail
        for rec in self:
            try:
                self.env['qaco.onboarding.audit.trail'].create({
                    'onboarding_id': rec.onboarding_id.id,
                    'action': action,
                    'notes': notes,
                })
            except Exception:
                _logger.exception('Failed to log decision action for %s', rec.id)

    def action_generate_decision_memo(self):
        self.ensure_one()
        report = self.env.ref('qaco_client_onboarding.report_engagement_authorization', raise_if_not_found=False)
        # Reuse or create a dedicated report template if needed; for now use engagement authorization as base
        if not report:
            _logger.warning('Decision memo report missing')
            return False
        try:
            pdf = report._render_qweb_pdf([self.onboarding_id.id])[0]
            att = self.env['ir.attachment'].create({
                'name': f'engagement_decision_{self.onboarding_id.id}_v{self.version}.pdf',
                'type': 'binary',
                'datas': base64.b64encode(pdf).decode('ascii'),
                'res_model': 'qaco.onboarding.decision',
                'res_id': self.id,
                'mimetype': 'application/pdf',
            })
            self.auto_generated_certificate = att.id
            # Index into Document Vault final folder
            try:
                folder = self.onboarding_id.get_folder_by_code('08_Final_Authorization')
                if folder:
                    self.env['qaco.onboarding.document'].create({
                        'onboarding_id': self.onboarding_id.id,
                        'name': att.name,
                        'file': att.datas,
                        'file_name': att.name,
                        'state': 'final',
                        'folder_id': folder.id,
                    })
            except Exception:
                _logger.exception('Failed to index decision memo for onboarding %s', self.onboarding_id.id)
            return att
        except Exception:
            _logger.exception('Failed to render decision memo for onboarding %s', self.onboarding_id.id)
            return False

    def action_apply_decision(self):
        """Apply workflow effect: set onboarding state and trigger planning unlock/lock based on decision."""
        for rec in self:
            if rec.decision_type in ('accept', 'accept_conditions'):
                # set onboarding state to partner_approved if not already
                rec.onboarding_id.write({'state': 'partner_approved'})
                rec.onboarding_id._log_action('Engagement decision applied: %s' % rec.decision_type, notes=rec.decision_rationale)
                # Additional: if conditional and policy says planning locked, leave specific behavior for now
            elif rec.decision_type in ('decline', 'withdraw'):
                rec.onboarding_id.write({'state': 'locked'})
                rec.onboarding_id._log_action('Engagement decision applied: %s' % rec.decision_type, notes=rec.decision_rationale)
        return True


class DecisionDriver(models.Model):
    _name = 'qaco.onboarding.decision.driver'
    _description = 'Decision Risk Driver'

    code = fields.Char(string='Code', required=True)
    name = fields.Char(string='Driver', required=True)


# Constraints
@api.constrains('decision_type', 'risk_rating', 'onboarding_id')
def _check_decision_preconditions(self):
    for rec in self:
        if rec.decision_type in ('accept', 'accept_conditions'):
            # Run onboarding preconditions
            try:
                rec.onboarding_id._check_final_authorization_preconditions()
            except ValidationError as e:
                raise ValidationError(_('Cannot accept: %s') % (e,))
            # If prohibitive risk, require quality approval
            if rec.risk_rating == 'prohibitive' and not rec.quality_approval_id:
                raise ValidationError(_('Prohibitive risk requires Quality/Compliance approval to accept.'))

