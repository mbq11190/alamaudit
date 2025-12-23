# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

THREAT_CATEGORIES = [
    ('self_interest', 'Self-interest'),
    ('self_review', 'Self-review'),
    ('advocacy', 'Advocacy'),
    ('familiarity', 'Familiarity'),
    ('intimidation', 'Intimidation'),
]

LIKELIHOOD = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
]

IMPACT = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
]

OVERALL_RATING = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
]

SAFEGUARD_OPTIONS = [
    ('separate_team', 'Separate team / Chinese wall'),
    ('second_partner_review', 'Second partner review / EQCR'),
    ('rotation_reassignment', 'Partner rotation / staff re-assignment'),
    ('independent_consult', 'Independent technical consultation'),
    ('additional_supervision', 'Additional supervision / review levels'),
    ('discontinue_service', 'Discontinue/limit non-audit service'),
    ('client_governance', 'Client governance communication and approvals'),
    ('withdrawal', 'Withdrawal from engagement'),
]

DECLARATION_STATUS = [
    ('pending', 'Pending'),
    ('submitted', 'Submitted'),
    ('returned', 'Returned for correction'),
    ('approved', 'Approved'),
]

CONFLICT_STATUS = [
    ('open', 'Open'),
    ('mitigated', 'Mitigated'),
    ('closed', 'Closed'),
    ('escalated', 'Escalated'),
    ('decline_required', 'Decline required'),
]

NAS_OUTCOMES = [
    ('allowed', 'Allowed'),
    ('allowed_safeguards', 'Allowed with safeguards'),
    ('prohibited', 'Prohibited'),
    ('resign', 'Must resign'),
]

GIFT_DECISIONS = [
    ('accepted', 'Accepted'),
    ('declined', 'Declined'),
]


class IndependenceDeclaration(models.Model):
    _name = 'qaco.onboarding.independence.declaration'
    _description = 'Independence Declaration (engagement team and firm level)'

    onboarding_id = fields.Many2one('qaco.client.onboarding', required=True, ondelete='cascade', index=True)
    user_id = fields.Many2one('res.users', string='User', required=True)
    role = fields.Char(string='Role')
    status = fields.Selection(DECLARATION_STATUS, default='pending')
    submitted_on = fields.Datetime(string='Submitted on')
    approved_on = fields.Datetime(string='Approved on')
    digital_signature = fields.Char(string='Digital signature', readonly=True)
    note = fields.Text(string='Notes')
    file_id = fields.Many2one('ir.attachment', string='Declaration file')


class IndependenceThreat(models.Model):
    _name = 'qaco.onboarding.independence.threat'
    _description = 'Independence Threat Record'

    onboarding_id = fields.Many2one('qaco.client.onboarding', required=True, ondelete='cascade', index=True)
    conflict_id = fields.Many2one('qaco.onboarding.conflict', string='Related Conflict', ondelete='cascade', index=True)
    category = fields.Selection(THREAT_CATEGORIES, string='Threat category')
    description = fields.Text(string='Description')
    likelihood = fields.Selection(LIKELIHOOD, string='Likelihood', default='low')
    impact = fields.Selection(IMPACT, string='Impact', default='low')
    overall = fields.Selection(OVERALL_RATING, string='Overall risk', compute='_compute_overall', store=True)
    safeguards = fields.Many2many('qaco.onboarding.safeguard', 'threat_safeguard_rel', 'threat_id', 'safeguard_id', string='Safeguards')
    safeguards_applied = fields.Text(string='Safeguards applied (details)')
    manual_override = fields.Selection(OVERALL_RATING, string='Manual override')
    override_reason = fields.Text(string='Override rationale')
    resolved = fields.Boolean(string='Resolved', default=False)
    resolution_notes = fields.Text(string='Resolution notes')

    @api.depends('likelihood', 'impact', 'manual_override')
    def _compute_overall(self):
        for rec in self:
            if rec.manual_override:
                rec.overall = rec.manual_override
                continue
            # Simple mapping: high if either likelihood or impact is high; medium if one medium else low
            levels = {'low': 1, 'medium': 2, 'high': 3}
            score = max(levels[rec.likelihood or 'low'], levels[rec.impact or 'low'])
            if score == 3:
                rec.overall = 'high'
            elif score == 2:
                rec.overall = 'medium'
            else:
                rec.overall = 'low'


class IndependenceSafeguard(models.Model):
    _name = 'qaco.onboarding.safeguard'
    _description = 'Independence Safeguard master'

    code = fields.Char(string='Code', required=True)
    name = fields.Char(string='Safeguard', required=True)
    description = fields.Text(string='Description')


class IndependenceConflict(models.Model):
    _name = 'qaco.onboarding.conflict'
    _description = 'Conflict of Interest Register'

    onboarding_id = fields.Many2one('qaco.client.onboarding', required=True, ondelete='cascade', index=True)
    conflict_type = fields.Char(string='Conflict type')
    parties_involved = fields.Char(string='Parties involved')
    description = fields.Text(string='Description')
    threat_ids = fields.One2many('qaco.onboarding.independence.threat', 'conflict_id', string='Threats')
    proposed_resolution = fields.Text(string='Proposed resolution and safeguards')
    approver_id = fields.Many2one('res.users', string='Approver')
    status = fields.Selection(CONFLICT_STATUS, default='open')
    evidence_attachment = fields.Many2one('ir.attachment', string='Evidence')


class OnboardingNonAuditService(models.Model):
    _name = 'qaco.onboarding.non.audit'
    _description = 'Non-Audit Service record'

    onboarding_id = fields.Many2one('qaco.client.onboarding', required=True, ondelete='cascade', index=True)
    service_category = fields.Char(string='Service category')
    service_from = fields.Date(string='From')
    service_to = fields.Date(string='To')
    fee = fields.Monetary(string='Fee')
    currency_id = fields.Many2one('res.currency')
    performed_by = fields.Char(string='Performed by')
    same_team = fields.Boolean(string='Performed by same team')
    self_review_indicator = fields.Boolean(string='Self-review risk indicator')
    management_responsibility = fields.Boolean(string='Management responsibility risk')
    pre_approval = fields.Boolean(string='Client governance pre-approval obtained')
    pre_approval_attachment = fields.Many2one('ir.attachment')
    safeguards_applied = fields.Text(string='Safeguards applied')
    outcome = fields.Selection(NAS_OUTCOMES, default='allowed')


class OnboardingGiftLog(models.Model):
    _name = 'qaco.onboarding.gift'
    _description = 'Gifts & Hospitality Log'

    onboarding_id = fields.Many2one('qaco.client.onboarding', required=True, ondelete='cascade', index=True)
    date = fields.Date(string='Date')
    offered_by = fields.Char(string='Offered by')
    offered_to = fields.Char(string='Offered to')
    nature = fields.Selection([('gift','Gift'),('meal','Meal'),('travel','Travel'),('entertainment','Entertainment')], string='Nature')
    estimated_value = fields.Monetary(string='Estimated value')
    currency_id = fields.Many2one('res.currency')
    rationale = fields.Text(string='Business rationale')
    decision = fields.Selection(GIFT_DECISIONS, string='Decision')
    approval_required = fields.Boolean(string='Approval required')
    approver_id = fields.Many2one('res.users')
    evidence = fields.Many2one('ir.attachment')


# Extend client onboarding with independence relations and computed fields
class ClientOnboardingIndependence(models.Model):
    _inherit = 'qaco.client.onboarding'

    independence_declaration_ids = fields.One2many('qaco.onboarding.independence.declaration', 'onboarding_id', string='Independence declarations')
    independence_threat_ids = fields.One2many('qaco.onboarding.independence.threat', 'onboarding_id', string='Threat records')
    independence_safeguard_ids = fields.Many2many('qaco.onboarding.safeguard', string='Applicable safeguards')
    conflict_ids = fields.One2many('qaco.onboarding.conflict', 'onboarding_id', string='Conflicts register')
    non_audit_service_ids = fields.One2many('qaco.onboarding.non.audit', 'onboarding_id', string='Non-audit services')
    gift_ids = fields.One2many('qaco.onboarding.gift', 'onboarding_id', string='Gifts & hospitality')

    independence_status = fields.Selection([('compliant','Compliant'),('not_compliant','Not Compliant'),('pending','Pending'),('escalated','Escalated')], string='Independence status', compute='_compute_independence_status', store=True)
    independence_unresolved_threats = fields.Integer(string='Unresolved threats', compute='_compute_unresolved_threats', store=True)

    # Configurable thresholds (read from ir.config_parameter via res.config.settings)
    gift_auto_decline_threshold = fields.Float(string='Gift auto-decline threshold', readonly=True)

    # Additional UI fields referenced by views
    manager_id = fields.Many2one('res.users', string='Manager')
    prior_services_summary = fields.Text(string='Prior services summary', readonly=True)
    long_association_years = fields.Integer(string='Long association years', readonly=True)
    independence_status_feedback = fields.Char(string='Independence summary', compute='_compute_independence_feedback')

    @api.depends('independence_status','independence_unresolved_threats')
    def _compute_independence_feedback(self):
        for rec in self:
            if rec.independence_status == 'compliant':
                rec.independence_status_feedback = 'No unresolved threats, declarations complete.'
            elif rec.independence_status == 'pending':
                rec.independence_status_feedback = 'Pending declarations.'
            elif rec.independence_status == 'escalated':
                rec.independence_status_feedback = 'Unresolved threats require escalation.'
            elif rec.independence_status == 'not_compliant':
                rec.independence_status_feedback = 'Not compliant: withdrawal/decline decision required.'
            else:
                rec.independence_status_feedback = ''

    @api.depends('independence_threat_ids.resolved')
    def _compute_unresolved_threats(self):
        for rec in self:
            rec.independence_unresolved_threats = len(rec.independence_threat_ids.filtered(lambda t: not t.resolved and t.overall in ('high','medium')))

    @api.depends('independence_declaration_ids.status','independence_threat_ids.overall','independence_threat_ids.resolved')
    def _compute_independence_status(self):
        for rec in self:
            # If any unresolved high/medium threats -> pending/escalated
            unresolved = rec.independence_threat_ids.filtered(lambda t: not t.resolved and t.overall in ('high','medium'))
            # Declarations: ensure all required declarations are submitted and approved
            pending_decls = rec.independence_declaration_ids.filtered(lambda d: d.status != 'approved')
            if pending_decls:
                rec.independence_status = 'pending'
            elif unresolved:
                rec.independence_status = 'escalated'
            else:
                rec.independence_status = 'compliant'

    def _check_independence_compliance(self):
        """Raise a ValidationError if independence gating prevents approval."""
        for rec in self:
            # All declarations approved
            if rec.independence_declaration_ids and any(d.status != 'approved' for d in rec.independence_declaration_ids):
                raise ValidationError(_('All required independence declarations must be approved before partner approval.'))
            # Threats: if unresolved medium/high threats exist, prevent approval unless an approved 'Not Compliant' workflow with withdrawal exists
            unresolved = rec.independence_threat_ids.filtered(lambda t: not t.resolved and t.overall in ('high','medium'))
            if unresolved:
                # If status is not 'not_compliant' with a withdrawal memo attached and approved by a quality partner, block
                if rec.independence_status != 'not_compliant' and rec.independence_status != 'escalated':
                    raise ValidationError(_('Unresolved independence threats block partner approval. Resolve or escalate to Quality/Compliance.'))

    # Hook into existing partner approve flow by providing a convenience method to be called
    def action_check_independence_before_approval(self):
        for rec in self:
            rec._check_independence_compliance()


# Settings for Independence thresholds and behavior
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    gift_auto_decline_threshold = fields.Float(string='Gift Auto-Decline Threshold')
    pack_attachment_max_kb = fields.Integer(string='Pack attachments max size (KB)', help='Attachments larger than this (KB) will not be merged into the Clearance Pack; they will be referenced instead.')

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        icp = self.env['ir.config_parameter'].sudo()
        res.update(
            gift_auto_decline_threshold=float(icp.get_param('qaco_client_onboarding.gift_auto_decline_threshold', default='0.0')),
            pack_attachment_max_kb=int(icp.get_param('qaco_client_onboarding.pack_attachment_max_kb', default='512')),
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_param('qaco_client_onboarding.gift_auto_decline_threshold', self.gift_auto_decline_threshold or 0.0)
        icp.set_param('qaco_client_onboarding.pack_attachment_max_kb', int(self.pack_attachment_max_kb or 512))
