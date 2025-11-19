"""Quality Review workflow for statutory and other audits."""

# -*- coding: utf-8 -*-

from datetime import date as dt_date, timedelta
from typing import Any, Dict, List, Tuple, TYPE_CHECKING

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError  # type: ignore[attr-defined]


SUBTAB_STATUS = [
    ('red', '❌ Incomplete'),
    ('amber', '🟡 In Progress'),
    ('green', '✅ Complete'),
]

CHECKLIST_RESPONSES = [
    ('yes', 'Yes – satisfied'),
    ('no', 'No – action required'),
    ('na', 'Not applicable'),
]

CHECKLIST_TYPES = [
    ('eqr_trigger', 'Checklist_EQR_Trigger'),
    ('eqr_completion', 'Checklist_EQR_Completion'),
    ('remediation', 'Checklist_Remediation_Effectiveness'),
    ('pre_lock', 'Checklist_Pre_Lock_Compliance'),
    ('archiving', 'Checklist_Archiving'),
]

FINDING_SOURCES = [
    ('internal_hot', 'Internal Hot Review'),
    ('internal_cold', 'Internal Cold Review'),
    ('icap', 'ICAP QAD Inspection'),
    ('aob', 'Audit Oversight Board Review'),
    ('secp', 'SECP Inspection'),
    ('other', 'Other / Client Feedback'),
]

FINDING_SEVERITY = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
    ('critical', 'Critical'),
]

ROOT_CAUSE_CATEGORIES = [
    ('engagement', 'Engagement-Level lapse'),
    ('systemic', 'Firm-wide / Systemic'),
    ('training', 'Lack of Training / Guidance'),
    ('resourcing', 'Inadequate Resources / Supervision'),
    ('methodology', 'Methodology gap'),
    ('other', 'Other'),
]

ACTION_STATUS = [
    ('planned', 'Planned'),
    ('in_progress', 'In Progress'),
    ('completed', 'Completed'),
]

SCOPE_STATUSES = [
    ('planned', 'Planned'),
    ('in_progress', 'In Progress'),
    ('closed', 'Closed'),
]

REVIEW_NOTE_STATUS = [
    ('open', 'Open'),
    ('in_progress', 'In Progress'),
    ('cleared', 'Cleared'),
]

FINDING_STATUS = [
    ('open', 'Open'),
    ('action', 'Action Underway'),
    ('closed', 'Closed'),
]

RISK_RATINGS = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
]

QUALITY_PASS_THRESHOLD = 95.0
ASSEMBLY_DEADLINE_DAYS = 60

MASTER_CHECKLIST: Dict[str, List[Dict[str, Any]]] = {
    'eqr_trigger': [
        {
            'question': _('Entity meets regulatory trigger (listed, public interest).'),
            'blocking': True,
            'weight': 10,
            'guidance': _('Confirm if the engagement falls under listed/PIE definitions.'),
        },
        {
            'question': _('Team independence threats evaluated and documented.'),
            'blocking': True,
            'weight': 10,
            'guidance': _('Consider rotation breaches, familiarity threats and safeguards.'),
        },
        {
            'question': _('Complex estimates or going concern uncertainties identified.'),
            'blocking': False,
            'weight': 5,
            'guidance': _('Capture high-risk areas that require specialist review inputs.'),
        },
    ],
    'eqr_completion': [
        {
            'question': _('EQR partner reviewed significant judgements and conclusions.'),
            'blocking': True,
            'weight': 15,
        },
        {
            'question': _('Financial statements match reviewed version with no late changes.'),
            'blocking': True,
            'weight': 10,
        },
        {
            'question': _('Key audit matters / emphasis paragraphs evaluated for accuracy.'),
            'blocking': False,
            'weight': 10,
        },
    ],
    'remediation': [
        {
            'question': _('Prior inspection findings relevant to this client addressed.'),
            'blocking': True,
            'weight': 10,
        },
        {
            'question': _('Root causes captured with clear remediation actions.'),
            'blocking': False,
            'weight': 5,
        },
    ],
    'pre_lock': [
        {
            'question': _('Completion memo signed by engagement partner.'),
            'blocking': True,
            'weight': 10,
        },
        {
            'question': _('E-signature or wet signature evidence archived.'),
            'blocking': False,
            'weight': 5,
        },
    ],
    'archiving': [
        {
            'question': _('Assembly completed within 60-day ISA 230 window.'),
            'blocking': True,
            'weight': 15,
        },
        {
            'question': _('Archival location reference and retention calendar updated.'),
            'blocking': False,
            'weight': 10,
        },
    ],
}

DEFAULT_SCOPE_TEMPLATE: List[Dict[str, Any]] = [
    {
        'focus_area': _('Revenue recognition & cut-off'),
        'risk_rating': 'high',
        'procedures': _('<ul><li>Review significant contracts</li><li>Inspect manual JE overrides</li></ul>'),
    },
    {
        'focus_area': _('Going concern & liquidity'),
        'risk_rating': 'medium',
        'procedures': _('<ul><li>Challenge cash flow forecasts</li><li>Inspect covenant letters</li></ul>'),
    },
    {
        'focus_area': _('Financial statement presentation'),
        'risk_rating': 'medium',
        'procedures': _('<ul><li>Cross-check disclosure checklist</li><li>Trace subsequent events</li></ul>'),
    },
]


class QualityReview(models.Model):
    _name = 'qaco.quality.review'
    _description = 'Quality Review'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    if TYPE_CHECKING:
        def message_post(self, *args: Any, **kwargs: Any) -> Any: ...

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    audit_id = fields.Many2one('qaco.audit', string='Audit', required=True, ondelete='cascade')
    client_id = fields.Many2one('res.partner', string='Client Name', related='audit_id.client_id', readonly=True, store=True)
    eqr_partner_employee_id = fields.Many2one('hr.employee', string='EQR Partner', tracking=True, domain="[('designation_id.name', '=', 'Partner')]")
    eqr_required = fields.Boolean(string='EQR Required', tracking=True)
    eqr_engine_reason = fields.Text(string='Trigger Engine Notes', tracking=True)
    eqr_override_option = fields.Selection([
        ('default', 'Default (engine result)'),
        ('force_on', 'Force On'),
        ('force_off', 'Force Off'),
    ], string='Override', default='default', tracking=True)
    eqr_override_reason = fields.Text(string='Override Rationale')
    eqr_scope_definition = fields.Html(string='Scope Narrative')
    eqr_scope_line_ids = fields.One2many('qaco.quality.eqr.scope', 'quality_review_id', string='Scope Areas')
    checklist_line_ids = fields.One2many('qaco.quality.checklist.line', 'quality_review_id', string='Checklist')

    trigger_status = fields.Selection(SUBTAB_STATUS, string='Trigger Status', compute='_compute_dashboard', store=True)
    procedures_status = fields.Selection(SUBTAB_STATUS, string='Procedures Status', compute='_compute_dashboard', store=True)
    monitoring_status = fields.Selection(SUBTAB_STATUS, string='Monitoring Status', compute='_compute_dashboard', store=True)
    locking_status = fields.Selection(SUBTAB_STATUS, string='Locking Status', compute='_compute_dashboard', store=True)
    overall_status = fields.Selection(SUBTAB_STATUS, string='Overall Status', compute='_compute_dashboard', store=True)

    significant_judgments_reviewed = fields.Boolean(string='Judgements Reviewed', tracking=True)
    financial_statements_eval = fields.Boolean(string='FS Evaluated', tracking=True)
    opinion_appropriate = fields.Boolean(string='Opinion Appropriate', tracking=True)
    kams_description_adequate = fields.Boolean(string='KAMs Adequate', tracking=True)
    compliance_confirmed = fields.Boolean(string='Independence & Compliance confirmed', tracking=True)
    eqr_concluded = fields.Boolean(string='EQR Concluded', tracking=True)
    eqr_conclusion_text = fields.Html(string='EQR Conclusion Memo')
    eqr_conclusion_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_quality_eqr_conclusion_rel', 'review_id', 'attachment_id',
        string='Conclusion Attachments')

    eqr_review_note_ids = fields.One2many('qaco.quality.review.note', 'quality_review_id', string='Review Notes')
    finding_ids = fields.One2many('qaco.quality.finding', 'quality_review_id', string='Findings')
    monitoring_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_quality_monitoring_rel', 'review_id', 'attachment_id',
        string='Monitoring Evidence')

    quality_score = fields.Float(string='Quality Score', compute='_compute_quality_score', store=True)
    quality_gate_passed = fields.Boolean(string='Quality Gate Passed', tracking=True)
    quality_gate_validated_on = fields.Datetime(string='Quality Gate Timestamp', readonly=True)

    open_review_note_count = fields.Integer(string='Open Notes', compute='_compute_badges', store=True)
    open_finding_count = fields.Integer(string='Open Findings', compute='_compute_badges', store=True)

    file_completion_date = fields.Date(string='Completion Date')
    file_assembly_date = fields.Date(string='Assembly Date')
    file_lock_date = fields.Date(string='File Lock Date', tracking=True)
    file_lock_user_id = fields.Many2one('res.users', string='Locked By', tracking=True)
    archiving_location = fields.Char(string='Archive Location Reference')
    archiving_link = fields.Char(string='Archive Link / Path')
    retention_years = fields.Integer(string='Retention (years)', default=10)
    retention_expiry_date = fields.Date(string='Retention Expiry', compute='_compute_retention', store=True)
    archiving_completed = fields.Boolean(string='Archiving Completed', tracking=True)
    archiving_completed_on = fields.Date(string='Archived On', tracking=True)
    locking_alerts_html = fields.Html(string='Locking Alerts', compute='_compute_locking_alerts')
    eqr_checklist_attachment_ids = fields.Many2many('ir.attachment', 'qaco_quality_eqr_check_rel', 'review_id', 'attachment_id', string='Checklist Evidence')
    file_lock_certificate_attachment_ids = fields.Many2many('ir.attachment', 'qaco_quality_lock_cert_rel', 'review_id', 'attachment_id', string='Lock Certificates')
    archiving_evidence_attachment_ids = fields.Many2many('ir.attachment', 'qaco_quality_archive_rel', 'review_id', 'attachment_id', string='Archiving Evidence')

    locking_status_message = fields.Text(string='Locking Message', compute='_compute_locking_alerts')

    def _compute_name(self):
        for record in self:
            if record.client_id:
                record.name = _('Quality Review - %s') % record.client_id.name
            elif record.audit_id:
                record.name = _('Quality Review - Audit %s') % record.audit_id.id
            else:
                record.name = _('Quality Review')

    @api.depends('checklist_line_ids.response', 'checklist_line_ids.weight', 'checklist_line_ids.checklist_type')
    def _compute_quality_score(self):
        for record in self:
            total_weight = 0.0
            earned = 0.0
            for line in record.checklist_line_ids:
                if line.weight <= 0:
                    continue
                if line.response == 'na':
                    continue
                total_weight += line.weight
                if line.response == 'yes':
                    earned += line.weight
            record.quality_score = round((earned / total_weight * 100.0), 2) if total_weight else 0.0

    @api.depends('eqr_review_note_ids.status', 'finding_ids.status')
    def _compute_badges(self):
        for record in self:
            record.open_review_note_count = len(record.eqr_review_note_ids.filtered(lambda n: n.status != 'cleared'))
            record.open_finding_count = len(record.finding_ids.filtered(lambda f: f.status != 'closed'))

    @api.depends('archiving_completed_on', 'file_lock_date', 'retention_years')
    def _compute_retention(self):
        for record in self:
            base_date = record.archiving_completed_on or record.file_lock_date
            if base_date and record.retention_years:
                record.retention_expiry_date = base_date + timedelta(days=record.retention_years * 365)
            else:
                record.retention_expiry_date = False

    @api.depends(
        'eqr_required', 'eqr_partner_employee_id', 'eqr_scope_line_ids.status',
        'eqr_concluded', 'significant_judgments_reviewed', 'finding_ids.status',
        'quality_gate_passed', 'file_lock_date', 'archiving_completed',
        'open_review_note_count', 'open_finding_count'
    )
    def _compute_dashboard(self):
        for record in self:
            trigger_complete = bool(record.eqr_engine_reason)
            if record.eqr_required:
                trigger_complete = trigger_complete and bool(record.eqr_partner_employee_id)
            trigger_started = bool(record.eqr_engine_reason or record.eqr_required)
            record.trigger_status = self._status_from_flags(trigger_complete, trigger_started)

            procedures_started = record.eqr_required or bool(record.eqr_scope_line_ids)
            scope_closed = all(line.status == 'closed' for line in record.eqr_scope_line_ids)
            completion_checks = all([
                record.significant_judgments_reviewed,
                record.financial_statements_eval,
                record.opinion_appropriate,
                record.compliance_confirmed,
            ])
            procedures_complete = scope_closed and (not record.eqr_required or record.eqr_concluded) and completion_checks and not record.open_review_note_count
            record.procedures_status = self._status_from_flags(procedures_complete, procedures_started)

            monitoring_started = bool(record.finding_ids or record.monitoring_attachment_ids)
            monitoring_complete = not record.open_finding_count
            record.monitoring_status = self._status_from_flags(monitoring_complete, monitoring_started)

            locking_started = bool(record.file_completion_date or record.file_assembly_date)
            locking_complete = bool(record.file_lock_date and record.archiving_completed)
            record.locking_status = self._status_from_flags(locking_complete, locking_started)

            if all(status == 'green' for status in [record.trigger_status, record.procedures_status, record.monitoring_status, record.locking_status]) and record.quality_gate_passed:
                record.overall_status = 'green'
            elif any(status == 'red' for status in [record.trigger_status, record.procedures_status, record.monitoring_status, record.locking_status]):
                record.overall_status = 'red'
            else:
                record.overall_status = 'amber'

    @api.depends('file_completion_date', 'file_assembly_date', 'file_lock_date', 'archiving_completed', 'archiving_completed_on')
    def _compute_locking_alerts(self):
        for record in self:
            alerts: List[str] = []
            if record.file_completion_date and not record.file_assembly_date:
                alerts.append(_('Assembly date missing. ISA 230 requires completion within 60 days.'))
            if record.file_completion_date and record.file_assembly_date:
                delta = (record.file_assembly_date - record.file_completion_date).days
                if delta > ASSEMBLY_DEADLINE_DAYS:
                    alerts.append(_('Assembly exceeded %s day limit by %s day(s).') % (ASSEMBLY_DEADLINE_DAYS, delta - ASSEMBLY_DEADLINE_DAYS))
            if record.file_lock_date and not record.archiving_completed:
                alerts.append(_('File locked but archive confirmation pending.'))
            if not alerts:
                record.locking_alerts_html = _('<p style="color:green;">No locking alerts.</p>')
                record.locking_status_message = False
            else:
                formatted = '<br/>'.join('• %s' % alert for alert in alerts)
                record.locking_alerts_html = formatted
                record.locking_status_message = '\n'.join(alerts)

    @staticmethod
    def _status_from_flags(complete: bool, started: bool) -> str:
        if complete:
            return 'green'
        if started:
            return 'amber'
        return 'red'

    @api.model_create_multi
    def create(self, vals_list: List[Dict[str, Any]]):
        records = super().create(vals_list)
        records._seed_master_checklist()
        records._seed_default_scope()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'checklist_line_ids' not in vals:
            self._seed_master_checklist()
        return res

    # ------------------------------------------------------------------
    # Initialization helpers
    # ------------------------------------------------------------------
    def _seed_master_checklist(self):
        for record in self:
            existing_keys = {(line.checklist_type, line.question) for line in record.checklist_line_ids}
            commands: List[Tuple[int, int, Dict[str, Any]]] = []
            for checklist_type, items in MASTER_CHECKLIST.items():
                seq = 10
                for item in items:
                    key = (checklist_type, item['question'])
                    if key in existing_keys:
                        seq += 10
                        continue
                    commands.append((0, 0, {
                        'sequence': seq,
                        'question': item['question'],
                        'guidance': item.get('guidance'),
                        'checklist_type': checklist_type,
                        'blocking': item.get('blocking', False),
                        'weight': item.get('weight', 5),
                    }))
                    seq += 10
            if commands:
                record.write({'checklist_line_ids': commands})

    def _seed_default_scope(self):
        for record in self.filtered(lambda r: not r.eqr_scope_line_ids):
            commands = [
                (0, 0, {
                    'sequence': (index + 1) * 10,
                    'focus_area': template['focus_area'],
                    'risk_rating': template['risk_rating'],
                    'procedures': template['procedures'],
                    'status': 'planned',
                })
                for index, template in enumerate(DEFAULT_SCOPE_TEMPLATE)
            ]
            if commands:
                record.write({'eqr_scope_line_ids': commands})

    # ------------------------------------------------------------------
    # Trigger engine logic
    # ------------------------------------------------------------------
    def action_run_trigger_engine(self):
        for record in self:
            required, reasons = record._evaluate_trigger_rules()
            if record.eqr_override_option == 'force_on':
                required = True
                reasons.append(_('Partner override applied: forced ON.'))
            elif record.eqr_override_option == 'force_off':
                required = False
                reasons.append(_('Partner override applied: forced OFF.'))
                if not record.eqr_override_reason:
                    raise UserError(_('Provide an override reason when forcing the EQR off.'))

            record.write({
                'eqr_required': required,
                'eqr_engine_reason': '\n'.join(reasons) if reasons else _('No trigger breached. EQR optional.'),
            })

            if required:
                record._seed_default_scope()

        return True

    def _evaluate_trigger_rules(self) -> Tuple[bool, List[str]]:
        self.ensure_one()
        reasons: List[str] = []
        audit = self.audit_id
        if not audit:
            return False, [(_('No audit linked; unable to evaluate triggers.'))]

        if audit.legal_entity in ('Public Company', 'Govt Organisation'):
            reasons.append(_('Entity classified as public interest.'))
        if audit.share_capital and audit.share_capital > 1_000_000_000:
            reasons.append(_('Share capital exceeds PKR 1bn threshold.'))
        if audit.turnover and audit.turnover > 5_000_000_000:
            reasons.append(_('Turnover exceeds PKR 5bn threshold.'))
        if audit.qaco_audit_partner and audit.qaco_assigning_partner and audit.qaco_audit_partner == audit.qaco_assigning_partner:
            reasons.append(_('Engagement and assigning partner are the same person.'))
        if audit.priority == '3':
            reasons.append(_('Audit flagged as High priority.'))
        if audit.repeat == 'New Client':
            reasons.append(_('First-year engagement requires heightened oversight.'))

        return bool(reasons), reasons

    # ------------------------------------------------------------------
    # Completion / gating actions
    # ------------------------------------------------------------------
    def action_finalize_eqr(self):
        for record in self:
            if not record.eqr_required:
                raise UserError(_('EQR is not required for this engagement.'))
            if record.eqr_concluded:
                continue
            record._ensure_procedural_checks()
            record.write({'eqr_concluded': True})
            record.message_post(body=_('EQR concluded by %s.') % self.env.user.name)
        return True

    def action_validate_quality_gate(self):
        for record in self:
            record._run_quality_gate_checks()
            record.write({
                'quality_gate_passed': True,
                'quality_gate_validated_on': fields.Datetime.now(),
            })
            record.message_post(body=_('Quality gate validated at score %.2f%%.') % record.quality_score)
        return True

    def action_lock_file(self):
        today = fields.Date.context_today(self)
        for record in self:
            if record.file_lock_date:
                raise UserError(_('File is already locked.'))
            if not record.quality_gate_passed:
                raise UserError(_('Run and pass the quality gate validation before locking the file.'))
            if not record.file_completion_date:
                raise UserError(_('Set the completion date before locking.'))
            if not record.file_assembly_date:
                record.file_assembly_date = today
            delta = (record.file_assembly_date - record.file_completion_date).days if record.file_completion_date and record.file_assembly_date else 0
            if delta > ASSEMBLY_DEADLINE_DAYS:
                raise UserError(_('Assembly exceeded the %s day limit. Provide remediation before locking.') % ASSEMBLY_DEADLINE_DAYS)
            record.write({
                'file_lock_date': today,
                'file_lock_user_id': self.env.user.id,
            })
            record.message_post(body=_('File locked on %s.') % today)
        return True

    def action_mark_archived(self):
        today = fields.Date.context_today(self)
        for record in self:
            if not record.file_lock_date:
                raise UserError(_('Lock the file before marking it archived.'))
            record.write({
                'archiving_completed': True,
                'archiving_completed_on': today,
            })
            record.message_post(body=_('Archive confirmed on %s.') % today)
        return True

    def action_open_review_notes(self):
        self.ensure_one()
        return self._open_related_tree('qaco.quality.review.note', _('Review Notes'), [('quality_review_id', '=', self.id)])

    def action_open_findings(self):
        self.ensure_one()
        return self._open_related_tree('qaco.quality.finding', _('Findings'), [('quality_review_id', '=', self.id)])

    def _open_related_tree(self, model: str, name: str, domain: List[Tuple[str, str, Any]]):
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'view_mode': 'tree,form',
            'res_model': model,
            'domain': domain,
            'context': {'default_quality_review_id': self.id},
        }

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------
    def _ensure_procedural_checks(self):
        self.ensure_one()
        missing = []
        if not self.eqr_partner_employee_id:
            missing.append(_('Assign an EQR partner.'))
        if not self.significant_judgments_reviewed:
            missing.append(_('Confirm significant judgements review.'))
        if not self.financial_statements_eval:
            missing.append(_('Confirm financial statements evaluation.'))
        if not self.opinion_appropriate:
            missing.append(_('Confirm opinion appropriateness.'))
        if self.open_review_note_count:
            missing.append(_('Resolve outstanding review notes (%s pending).') % self.open_review_note_count)
        eqr_checklist_lines = self.checklist_line_ids.filtered(lambda l: l.checklist_type == 'eqr_completion')
        blocking_failures = eqr_checklist_lines.filtered(lambda l: l.blocking and l.response != 'yes')
        if blocking_failures:
            missing.append(_('All blocking completion checklist items must be marked Yes.'))
        if missing:
            raise UserError('\n'.join(missing))

    def _run_quality_gate_checks(self):
        self.ensure_one()
        errors = []
        if self.eqr_required and not self.eqr_concluded:
            errors.append(_('EQR conclusion is pending.'))
        blocking_lines = self.checklist_line_ids.filtered(lambda l: l.blocking and l.response not in ('yes', 'na'))
        if blocking_lines:
            errors.append(_('Complete all blocking checklist items before validation.'))
        if self.open_finding_count:
            errors.append(_('Close outstanding findings (%s pending).') % self.open_finding_count)
        if self.quality_score < QUALITY_PASS_THRESHOLD:
            errors.append(_('Quality score %.2f is below the %.2f%% threshold.') % (self.quality_score, QUALITY_PASS_THRESHOLD))
        if not self.file_completion_date:
            errors.append(_('Capture the file completion date.'))
        if errors:
            raise ValidationError('\n'.join(errors))


class QualityChecklistLine(models.Model):
    _name = 'qaco.quality.checklist.line'
    _description = 'Quality Review Checklist Line'
    _order = 'sequence, id'

    quality_review_id = fields.Many2one('qaco.quality.review', string='Quality Review', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    question = fields.Char(required=True)
    guidance = fields.Text()
    checklist_type = fields.Selection(CHECKLIST_TYPES, required=True, default='eqr_trigger')
    blocking = fields.Boolean(string='Blocking?')
    response = fields.Selection(CHECKLIST_RESPONSES, string='Response', default='na')
    comments = fields.Text()
    weight = fields.Float(default=5.0)


class QualityEQRSscope(models.Model):
    _name = 'qaco.quality.eqr.scope'
    _description = 'EQR Scope Line'
    _order = 'sequence, id'

    quality_review_id = fields.Many2one('qaco.quality.review', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    focus_area = fields.Char(required=True)
    risk_rating = fields.Selection(RISK_RATINGS, default='medium')
    procedures = fields.Html(string='Planned Procedures')
    reviewer_notes = fields.Text()
    status = fields.Selection(SCOPE_STATUSES, default='planned')


class QualityReviewNote(models.Model):
    _name = 'qaco.quality.review.note'
    _description = 'Quality Review Note'
    _order = 'create_date desc'

    quality_review_id = fields.Many2one('qaco.quality.review', required=True, ondelete='cascade')
    reference = fields.Char(string='Reference')
    description = fields.Text(required=True)
    response = fields.Text(string='Response')
    raised_by_id = fields.Many2one('res.users', string='Raised By', default=lambda self: self.env.user)
    assigned_to_id = fields.Many2one('res.users', string='Assigned To')
    status = fields.Selection(REVIEW_NOTE_STATUS, default='open', tracking=True)
    cleared_on = fields.Datetime(string='Cleared On', tracking=True)
    attachment_ids = fields.Many2many('ir.attachment', 'qaco_quality_review_note_rel', 'note_id', 'attachment_id')

    @api.onchange('status')
    def _onchange_status(self):
        for record in self:
            if record.status == 'cleared' and not record.cleared_on:
                record.cleared_on = fields.Datetime.now()


class QualityFinding(models.Model):
    _name = 'qaco.quality.finding'
    _description = 'Quality Monitoring Finding'
    _order = 'severity desc, due_date, id'

    quality_review_id = fields.Many2one('qaco.quality.review', required=True, ondelete='cascade')
    source = fields.Selection(FINDING_SOURCES, required=True)
    description = fields.Text(required=True)
    severity = fields.Selection(FINDING_SEVERITY, default='medium')
    status = fields.Selection(FINDING_STATUS, default='open', tracking=True)
    action_owner_id = fields.Many2one('res.users', string='Action Owner')
    due_date = fields.Date()
    recurrence_flag = fields.Boolean(string='Recurring issue')
    root_cause_category = fields.Selection(ROOT_CAUSE_CATEGORIES)
    root_cause_notes = fields.Text()
    attachment_ids = fields.Many2many('ir.attachment', 'qaco_quality_finding_rel', 'finding_id', 'attachment_id')
    action_ids = fields.One2many('qaco.quality.finding.action', 'finding_id', string='Action Plan')

    @api.constrains('status', 'action_ids')
    def _check_actions_before_close(self):
        for record in self:
            if record.status == 'closed' and record.action_ids.filtered(lambda a: a.status != 'completed'):
                raise ValidationError(_('All remediation actions must be completed before closing a finding.'))


class QualityFindingAction(models.Model):
    _name = 'qaco.quality.finding.action'
    _description = 'Quality Finding Action'
    _order = 'due_date, id'

    finding_id = fields.Many2one('qaco.quality.finding', required=True, ondelete='cascade')
    task = fields.Char(required=True)
    responsible_id = fields.Many2one('res.users', string='Responsible')
    due_date = fields.Date()
    status = fields.Selection(ACTION_STATUS, default='planned')

