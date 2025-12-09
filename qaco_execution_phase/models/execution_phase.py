# -*- coding: utf-8 -*-

from datetime import date
from typing import TYPE_CHECKING, Any

from odoo import api, fields, models  # type: ignore
from odoo.exceptions import UserError, ValidationError  # type: ignore[attr-defined]
try:  # pragma: no cover - fallback for type checking environments
    from odoo import _  # type: ignore
except Exception:  # pragma: no cover
    def _(message: str, *args: Any, **kwargs: Any) -> str:  # type: ignore
        return message


SUBTAB_STATUS = [
    ('red', 'Incomplete'),
    ('amber', 'In Progress'),
    ('green', 'Complete'),
]

CONTROL_FREQUENCY = [
    ('daily', 'Daily'),
    ('weekly', 'Weekly'),
    ('monthly', 'Monthly'),
    ('quarterly', 'Quarterly'),
    ('annual', 'Annual'),
    ('ad_hoc', 'Ad-hoc'),
]

ASSERTION_TYPES = [
    ('existence', 'Existence / Occurrence'),
    ('completeness', 'Completeness / Cut-off'),
    ('valuation', 'Valuation / Allocation'),
    ('rights', 'Rights & Obligations'),
    ('presentation', 'Presentation & Disclosure'),
]

AUDIT_AREAS = [
    ('revenue', 'Revenue & Receivables'),
    ('inventory', 'Inventory'),
    ('ppe', 'Property, Plant & Equipment'),
    ('cash', 'Cash & Bank'),
    ('investments', 'Investments'),
    ('payables', 'Purchases & Payables'),
    ('payroll', 'Payroll & HR'),
    ('taxation', 'Taxation'),
    ('provisions', 'Provisions & Contingencies'),
    ('other', 'Other'),
]

SAMPLING_METHODS = [
    ('random', 'Random'),
    ('systematic', 'Systematic'),
    ('mus', 'Monetary Unit Sampling'),
    ('haphazard', 'Haphazard (Documented)'),
]

EVIDENCE_TIERS = [
    ('external', 'External Source (High Reliability)'),
    ('internal', 'Internal Document (Medium Reliability)'),
    ('inquiry', 'Management Inquiry (Low Reliability)'),
]

WORKPAPER_TYPES = [
    ('lead', 'Lead Schedule'),
    ('support', 'Supporting Schedule'),
    ('memo', 'Technical Memo'),
]


class QacoExecutionPhase(models.Model):
    _name = 'qaco.execution.phase'
    _description = 'Execution Phase'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    if TYPE_CHECKING:
        def activity_schedule(self, *args: Any, **kwargs: Any) -> Any: ...

        def message_post(self, *args: Any, **kwargs: Any) -> Any: ...

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    audit_id = fields.Many2one('qaco.audit', string='Audit', required=True, ondelete='cascade')
    client_id = fields.Many2one('res.partner', string='Client Name', related='audit_id.client_id', readonly=True, store=True)
    planning_phase_id = fields.Many2one('qaco.planning.phase', string='Planning Phase', compute='_compute_planning_phase', store=True, readonly=False)
    company_currency_id = fields.Many2one('res.currency', string='Company Currency', related='audit_id.currency_id', store=True, readonly=True)

    # Status dashboard
    control_status = fields.Selection(SUBTAB_STATUS, default='red', tracking=True)
    substantive_status = fields.Selection(SUBTAB_STATUS, default='red', tracking=True)
    sampling_status = fields.Selection(SUBTAB_STATUS, default='red', tracking=True)
    evidence_status = fields.Selection(SUBTAB_STATUS, default='red', tracking=True)
    workpaper_status = fields.Selection(SUBTAB_STATUS, default='red', tracking=True)
    completion_status = fields.Selection(SUBTAB_STATUS, default='red', tracking=True)

    risk_coverage_percent = fields.Float(string='Risk Coverage %', compute='_compute_risk_metrics', digits=(3, 2))
    open_critical_risk_count = fields.Integer(string='Open Significant Risks', compute='_compute_risk_metrics')
    compliance_beacon_state = fields.Selection([
        ('green', 'All ISA/ICAP checkpoints satisfied'),
        ('amber', 'Pending required documentation'),
        ('red', 'Blocking deficiencies detected'),
    ], string='Compliance Beacon', compute='_compute_compliance_beacon', store=True)
    compliance_alert_message = fields.Html(string='Compliance Alerts', compute='_compute_compliance_beacon', store=True)

    # Relationships to execution artefacts
    execution_risk_line_ids = fields.One2many('qaco.exec.risk.coverage', 'execution_phase_id', string='Risk & Assertion Matrix')
    control_test_ids = fields.One2many('qaco.exec.control.test', 'execution_phase_id', string='Tests of Controls')
    substantive_area_ids = fields.One2many('qaco.exec.substantive.area', 'execution_phase_id', string='Substantive Procedures')
    sampling_request_ids = fields.One2many('qaco.exec.sampling.request', 'execution_phase_id', string='Sampling Requests')
    evidence_item_ids = fields.One2many('qaco.exec.evidence.item', 'execution_phase_id', string='Evidence Items')
    workpaper_ids = fields.One2many('qaco.exec.workpaper', 'execution_phase_id', string='Workpapers')

    # Checklists & gating flags
    checklist_controls_linked = fields.Boolean(string='All key controls linked to risks', tracking=True)
    checklist_walkthrough_documented = fields.Boolean(string='Walkthroughs documented & evidenced', tracking=True)
    checklist_exceptions_escalated = fields.Boolean(string='Control exceptions evaluated & communicated', tracking=True)
    checklist_substantive_assertions = fields.Boolean(string='Each significant assertion tested substantively', tracking=True)
    checklist_sampling_signed = fields.Boolean(string='Sampling rationale documented', tracking=True)
    checklist_evidence_sufficient = fields.Boolean(string='Evidence sufficiency meter green', tracking=True)
    checklist_workpapers_reviewed = fields.Boolean(string='All workpapers reviewed & signed', tracking=True)

    manager_signed_user_id = fields.Many2one('res.users', string='Manager Sign-off', tracking=True, copy=False, readonly=True)
    manager_signed_on = fields.Datetime(string='Manager Signed On', tracking=True, copy=False, readonly=True)
    partner_signed_user_id = fields.Many2one('res.users', string='Partner Sign-off', tracking=True, copy=False, readonly=True)
    partner_signed_on = fields.Datetime(string='Partner Signed On', tracking=True, copy=False, readonly=True)
    quality_reviewer_id = fields.Many2one('res.users', string='Quality Reviewer', tracking=True, copy=False, readonly=True)
    quality_reviewed_on = fields.Datetime(string='Quality Reviewed On', tracking=True, copy=False, readonly=True)

    execution_complete = fields.Boolean(string='Execution Phase Complete', tracking=True, copy=False)
    execution_completed_on = fields.Datetime(string='Execution Completed On', tracking=True, copy=False, readonly=True)
    phase_completion_certificate = fields.Boolean(string='Phase Completion Certificate Generated', tracking=True, copy=False)
    can_finalize_execution = fields.Boolean(string='Can Finalize Execution', compute='_compute_can_finalize', store=True)
    missing_requirements_note = fields.Html(string='Outstanding Requirements', compute='_compute_can_finalize', store=True)

    # Metadata
    compliance_notes = fields.Html(string='Compliance Notes / Regulator feedback')

    @api.depends('audit_id', 'client_id')
    def _compute_name(self):
        for record in self:
            if record.client_id:
                record.name = f"Execution - {record.client_id.name}"
            else:
                record.name = "Execution Phase"

    @api.depends('audit_id')
    def _compute_planning_phase(self):
        planning_model = self.env['qaco.planning.phase']
        for record in self:
            planning = False
            if record.audit_id:
                planning = planning_model.search([('audit_id', '=', record.audit_id.id)], limit=1)
            record.planning_phase_id = planning.id if planning else False

    @api.depends('execution_risk_line_ids.is_fully_addressed', 'execution_risk_line_ids.is_significant')
    def _compute_risk_metrics(self):
        for record in self:
            lines = record.execution_risk_line_ids
            total = len(lines)
            addressed = len(lines.filtered(lambda l: l.is_fully_addressed))
            record.risk_coverage_percent = (addressed / total * 100.0) if total else 0.0
            record.open_critical_risk_count = len(lines.filtered(lambda l: l.is_significant and not l.is_fully_addressed))

    @api.depends(
        'control_status', 'substantive_status', 'sampling_status', 'evidence_status', 'workpaper_status',
        'checklist_controls_linked', 'checklist_walkthrough_documented', 'checklist_exceptions_escalated',
        'checklist_substantive_assertions', 'checklist_sampling_signed', 'checklist_evidence_sufficient',
        'checklist_workpapers_reviewed'
    )
    def _compute_compliance_beacon(self):
        for record in self:
            alerts = []
            statuses = [
                record.control_status, record.substantive_status, record.sampling_status,
                record.evidence_status, record.workpaper_status
            ]
            checklist_ok = all([
                record.checklist_controls_linked,
                record.checklist_walkthrough_documented,
                record.checklist_exceptions_escalated,
                record.checklist_substantive_assertions,
                record.checklist_sampling_signed,
                record.checklist_evidence_sufficient,
                record.checklist_workpapers_reviewed,
            ])
            if all(status == 'green' for status in statuses) and checklist_ok:
                state = 'green'
                alerts.append(_('All ISA checkpoints satisfied.'))
            else:
                if any(status == 'red' for status in statuses):
                    alerts.append(_('Turn the red execution sub-tabs green before finalizing.'))
                if not checklist_ok:
                    alerts.append(_('Complete the mandatory execution checklists.'))
                if not alerts:
                    alerts.append(_('Execution compliance requirements are partially satisfied.'))
                state = 'amber' if not any(status == 'red' for status in statuses) else 'red'
            record.compliance_beacon_state = state
            record.compliance_alert_message = '<br/>'.join(alerts)

    @api.depends(
        'control_status', 'substantive_status', 'sampling_status', 'evidence_status', 'workpaper_status',
        'checklist_controls_linked', 'checklist_walkthrough_documented', 'checklist_exceptions_escalated',
        'checklist_substantive_assertions', 'checklist_sampling_signed', 'checklist_evidence_sufficient',
        'checklist_workpapers_reviewed', 'manager_signed_user_id', 'partner_signed_user_id'
    )
    def _compute_can_finalize(self):
        for record in self:
            statuses_ready = all([
                record.control_status == 'green',
                record.substantive_status == 'green',
                record.sampling_status == 'green',
                record.evidence_status == 'green',
                record.workpaper_status == 'green',
            ])
            checklist_ready = all([
                record.checklist_controls_linked,
                record.checklist_walkthrough_documented,
                record.checklist_exceptions_escalated,
                record.checklist_substantive_assertions,
                record.checklist_sampling_signed,
                record.checklist_evidence_sufficient,
                record.checklist_workpapers_reviewed,
            ])
            signoff_ready = bool(record.manager_signed_user_id and record.partner_signed_user_id)

            record.can_finalize_execution = statuses_ready and checklist_ready and signoff_ready

            pending = []
            if not statuses_ready:
                pending.append(_('Turn all execution sub-tabs green.'))
            if not checklist_ready:
                pending.append(_('Complete the mandatory execution checklists.'))
            if not signoff_ready:
                pending.append(_('Manager and partner sign-offs are required.'))
            record.missing_requirements_note = '<br/>'.join(pending) if pending else False

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._ensure_risk_matrix_alignment()
        return records

    def write(self, vals):
        res = super().write(vals)
        if any(field in vals for field in ['audit_id', 'planning_phase_id']) and self:
            self._ensure_risk_matrix_alignment()
        return res

    def _ensure_risk_matrix_alignment(self):
        risk_line_model = self.env['qaco.exec.risk.coverage']
        for record in self:
            if not record.planning_phase_id or not record.audit_id:
                continue
            planning_risks = record.planning_phase_id.risk_register_line_ids
            existing_links = record.execution_risk_line_ids.mapped('planning_risk_id')
            for planning_risk in planning_risks:
                if planning_risk in existing_links:
                    continue
                risk_line_model.create({
                    'execution_phase_id': record.id,
                    'planning_risk_id': planning_risk.id,
                    'risk_description': planning_risk.risk_description,
                    'risk_rating': planning_risk.risk_rating,
                    'assertion_type': planning_risk.assertion_type or 'existence',
                    'is_significant': planning_risk.is_significant_risk,
                })

    # === Actions ===
    def _ensure_statuses_green(self):
        self.ensure_one()
        if not all([
            self.control_status == 'green',
            self.substantive_status == 'green',
            self.sampling_status == 'green',
            self.evidence_status == 'green',
            self.workpaper_status == 'green',
        ]):
            raise UserError(_('All execution sub-tabs must be green before sign-off.'))

    def _ensure_checklists_complete(self):
        self.ensure_one()
        checklist_fields = [
            'checklist_controls_linked',
            'checklist_walkthrough_documented',
            'checklist_exceptions_escalated',
            'checklist_substantive_assertions',
            'checklist_sampling_signed',
            'checklist_evidence_sufficient',
            'checklist_workpapers_reviewed',
        ]
        if not all(getattr(self, field) for field in checklist_fields):
            raise UserError(_('Complete all execution checklists before continuing.'))

    def action_manager_sign(self):
        self.ensure_one()
        self._ensure_checklists_complete()
        self.manager_signed_user_id = self.env.user
        self.manager_signed_on = fields.Datetime.now()
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            note=_('Execution phase ready for partner review.'),
            user_id=self.partner_signed_user_id.id if self.partner_signed_user_id else self.env.user.id,
            summary=_('Partner review required'),
        )

    def action_partner_sign(self):
        self.ensure_one()
        if not self.manager_signed_user_id:
            raise UserError(_('Manager must sign before the partner.'))
        self._ensure_statuses_green()
        self.partner_signed_user_id = self.env.user
        self.partner_signed_on = fields.Datetime.now()

    def action_quality_review(self):
        self.ensure_one()
        self.quality_reviewer_id = self.env.user
        self.quality_reviewed_on = fields.Datetime.now()
        self.message_post(body=_('Quality review initiated by %s') % self.env.user.name)

    def action_mark_execution_complete(self):
        self.ensure_one()
        if not self.can_finalize_execution:
            raise UserError(self.missing_requirements_note or _('Execution prerequisites are incomplete.'))
        self._ensure_statuses_green()
        self._ensure_checklists_complete()
        self.execution_complete = True
        self.execution_completed_on = fields.Datetime.now()
        self.completion_status = 'green'
        self.message_post(body=_('Execution phase completed and locked.'))

    def action_generate_phase_certificate(self):
        self.ensure_one()
        if not self.can_finalize_execution:
            raise UserError(_('Complete execution tasks before generating the certificate.'))
        self.phase_completion_certificate = True
        self.message_post(body=_('Phase completion certificate generated for regulatory file.'))
        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content/qaco.execution.phase/{self.id}/phase_certificate",
            'target': 'new',
        }

    def action_export_execution_file(self):
        self.ensure_one()
        if not self.execution_complete:
            raise UserError(_('Complete the execution phase before exporting.'))
        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content/qaco.execution.phase/{self.id}/execution_archive",
            'target': 'new',
        }

    def action_backfill_exception_amounts(self):
        ir_model = self.env['ir.model']
        if not ir_model._get('qaco.finalisation.phase'):
            raise UserError('Install the finalisation phase module to backfill exceptions.')

        finalisation_model = self.env['qaco.finalisation.phase']
        SubProcedure = self.env['qaco.exec.substantive.procedure']
        total_updates = 0
        for record in self:
            if not record.audit_id:
                continue
            finalisation = finalisation_model.search([('audit_id', '=', record.audit_id.id)], limit=1)
            if not finalisation:
                continue
            updates = 0
            for misstatement in finalisation.misstatement_line_ids:
                if misstatement.source_model != 'qaco.exec.substantive.procedure' or not misstatement.source_reference:
                    continue
                _, _, proc_id_str = misstatement.source_reference.partition(':')
                if not proc_id_str:
                    continue
                try:
                    proc = SubProcedure.browse(int(proc_id_str))
                except ValueError:
                    continue
                if not proc.exists() or proc.execution_phase_id.id != record.id:
                    continue
                if proc.exception_amount != misstatement.amount:
                    proc.write({'exception_amount': misstatement.amount})
                    updates += 1
            if updates:
                record.message_post(body='Backfilled %s procedure(s) with quantified exceptions.' % updates)
                total_updates += updates
        if not total_updates:
            raise UserError('No linked misstatements were found to backfill. Run the finalisation sync first.')


class ExecutionRiskCoverage(models.Model):
    _name = 'qaco.exec.risk.coverage'
    _description = 'Execution Risk & Assertion Coverage'
    _order = 'is_significant desc, id'

    execution_phase_id = fields.Many2one('qaco.execution.phase', string='Execution Phase', required=True, ondelete='cascade')
    planning_risk_id = fields.Many2one('qaco.risk.register.line', string='Planning Risk', readonly=True)
    risk_description = fields.Text(string='Risk Description')
    risk_rating = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], string='Risk Rating')
    assertion_type = fields.Selection(ASSERTION_TYPES, string='Assertion', default='existence')
    is_significant = fields.Boolean(string='Significant Risk')
    control_test_ids = fields.One2many('qaco.exec.control.test', 'risk_line_id', string='Control Tests')
    substantive_procedure_ids = fields.One2many('qaco.exec.substantive.procedure', 'risk_line_id', string='Substantive Procedures')
    coverage_percent = fields.Float(string='Coverage %', compute='_compute_coverage', digits=(3, 2))
    is_fully_addressed = fields.Boolean(string='Fully Addressed', compute='_compute_coverage', store=True)

    def _compute_coverage(self):
        for record in self:
            has_control = bool(record.control_test_ids.filtered(lambda t: t.test_status == 'green'))
            has_substantive = bool(record.substantive_procedure_ids.filtered(lambda s: s.status == 'green'))
            tests = record.control_test_ids | record.substantive_procedure_ids
            record.coverage_percent = min(len(tests) * 50.0, 100.0) if tests else 0.0
            record.is_fully_addressed = bool(has_control and has_substantive)


class ExecutionControlTest(models.Model):
    _name = 'qaco.exec.control.test'
    _description = 'Test of Controls'
    _inherit = ['mail.thread']
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    execution_phase_id = fields.Many2one('qaco.execution.phase', string='Execution Phase', required=True, ondelete='cascade')
    risk_line_id = fields.Many2one('qaco.exec.risk.coverage', string='Linked Risk', required=True, ondelete='cascade')
    assertion_type = fields.Selection(ASSERTION_TYPES, string='Assertion', default='existence')
    control_name = fields.Char(string='Control Name', required=True)
    process_name = fields.Char(string='Process / Cycle', required=True)
    control_owner = fields.Char(string='Control Owner')
    frequency = fields.Selection(CONTROL_FREQUENCY, string='Frequency', default='monthly')
    documentation_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_exec_control_doc_rel', 'control_id', 'attachment_id',
        string='Control Documentation'
    )
    walkthrough_narrative = fields.Html(string='Walkthrough Narrative')
    walkthrough_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_exec_control_walk_rel', 'control_id', 'attachment_id',
        string='Walkthrough Evidence'
    )
    design_effectiveness = fields.Selection([
        ('effective', 'Effective'),
        ('ineffective', 'Not Effective'),
    ], string='Design Evaluation', default='effective', tracking=True)
    design_comment = fields.Text(string='Design Comment')
    operating_effectiveness = fields.Selection([
        ('not_tested', 'Not Tested'),
        ('effective', 'Effective'),
        ('ineffective', 'Not Effective'),
    ], string='Operating Effectiveness', default='not_tested', tracking=True)
    planned_reliance_level = fields.Selection([
        ('high', 'High'),
        ('moderate', 'Moderate'),
        ('low', 'Low'),
    ], string='Planned Reliance', default='moderate')
    tolerable_deviation_rate = fields.Float(string='Tolerable Deviation %', default=5.0)
    expected_deviation_rate = fields.Float(string='Expected Deviation %', default=0.0)
    recommended_sample_size = fields.Integer(string='Recommended Sample Size', compute='_compute_sample_recommendation')
    selected_sample_size = fields.Integer(string='Selected Sample Size')
    testing_period_start = fields.Date(string='Testing Period From')
    testing_period_end = fields.Date(string='Testing Period To')
    population_description = fields.Char(string='Population Description')
    sampling_request_id = fields.Many2one('qaco.exec.sampling.request', string='Sampling Request', ondelete='set null')
    exception_ids = fields.One2many('qaco.exec.control.exception', 'control_test_id', string='Exceptions')
    exception_count = fields.Integer(string='Exceptions', compute='_compute_exception_count')
    conclusion = fields.Selection([
        ('rely', 'Can rely on controls'),
        ('no_rely', 'Cannot rely on controls'),
    ], string='Conclusion', compute='_compute_conclusion', store=True)
    test_status = fields.Selection(SUBTAB_STATUS, string='Status', default='red', tracking=True)
    checklist_signed = fields.Boolean(string='Checklist Signed', tracking=True)

    def _compute_sample_recommendation(self):
        for record in self:
            baseline = 5 if record.frequency in ('daily', 'weekly') else 3
            risk_multiplier = 2 if record.planned_reliance_level == 'high' else 1
            deviation_factor = max(record.tolerable_deviation_rate, 1.0)
            record.recommended_sample_size = int(round((baseline * risk_multiplier * 100) / deviation_factor))

    def _compute_exception_count(self):
        for record in self:
            record.exception_count = len(record.exception_ids)

    def _compute_conclusion(self):
        for record in self:
            if record.exception_count and record.exception_count > record.tolerable_deviation_rate:
                record.conclusion = 'no_rely'
            elif record.operating_effectiveness == 'effective' and record.design_effectiveness == 'effective':
                record.conclusion = 'rely'
            else:
                record.conclusion = False


class ExecutionControlException(models.Model):
    _name = 'qaco.exec.control.exception'
    _description = 'Control Test Exception Register'
    _order = 'id desc'

    control_test_id = fields.Many2one('qaco.exec.control.test', string='Control Test', required=True, ondelete='cascade')
    description = fields.Text(string='Exception Description', required=True)
    root_cause = fields.Selection([
        ('human_error', 'Human Error'),
        ('system_flaw', 'System Flaw'),
        ('fraud', 'Fraud / Override'),
        ('other', 'Other'),
    ], string='Root Cause', required=True)
    impact = fields.Text(string='Impact on Financial Statements', required=True)
    isa265_communicated = fields.Boolean(string='Communicated per ISA 265')
    communication_reference = fields.Char(string='Communication Reference')
    remediation_plan = fields.Text(string='Remediation / Compensating Procedure')


class ExecutionSubstantiveArea(models.Model):
    _name = 'qaco.exec.substantive.area'
    _description = 'Substantive Audit Area'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    execution_phase_id = fields.Many2one('qaco.execution.phase', string='Execution Phase', required=True, ondelete='cascade')
    area_code = fields.Selection(AUDIT_AREAS, string='Audit Area', required=True)
    focus_note = fields.Html(string='Area Focus / Planning Memo Link')
    risk_line_ids = fields.Many2many('qaco.exec.risk.coverage', 'qaco_exec_area_risk_rel', 'area_id', 'risk_id', string='Linked Risks')
    status = fields.Selection(SUBTAB_STATUS, string='Status', default='red', tracking=True)
    exception_count = fields.Integer(string='Exceptions', compute='_compute_exception_count')
    conclusion = fields.Selection([
        ('sufficient', 'Sufficient appropriate evidence obtained'),
        ('insufficient', 'Further work required'),
    ], string='Conclusion')
    procedure_ids = fields.One2many('qaco.exec.substantive.procedure', 'area_id', string='Procedures')

    def _compute_exception_count(self):
        for record in self:
            record.exception_count = len(record.procedure_ids.filtered(lambda p: p.result == 'exception'))


class ExecutionSubstantiveProcedure(models.Model):
    _name = 'qaco.exec.substantive.procedure'
    _description = 'Substantive Procedure'
    _order = 'area_id, sequence'

    sequence = fields.Integer(default=10)
    area_id = fields.Many2one('qaco.exec.substantive.area', string='Audit Area', required=True, ondelete='cascade')
    execution_phase_id = fields.Many2one(related='area_id.execution_phase_id', store=True)
    risk_line_id = fields.Many2one('qaco.exec.risk.coverage', string='Linked Risk', ondelete='set null')
    name = fields.Char(string='Procedure', required=True)
    assertion_type = fields.Selection(ASSERTION_TYPES, string='Assertion', default='existence')
    methodology_step = fields.Html(string='Detailed Steps / Reference')
    sample_size_planned = fields.Integer(string='Planned Sample Size')
    sample_size_tested = fields.Integer(string='Actual Sample Size')
    company_currency_id = fields.Many2one('res.currency', related='execution_phase_id.company_currency_id', store=True, readonly=True)
    exception_amount = fields.Monetary(string='Exception Amount', currency_field='company_currency_id')
    sampling_request_id = fields.Many2one('qaco.exec.sampling.request', string='Sampling Request', ondelete='set null')
    evidence_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_exec_substantive_evidence_rel', 'procedure_id', 'attachment_id',
        string='Evidence'
    )
    prepared_by = fields.Many2one('res.users', string='Prepared By', default=lambda self: self.env.user)
    prepared_on = fields.Datetime(string='Prepared On', default=fields.Datetime.now)
    reviewed_by = fields.Many2one('res.users', string='Reviewed By')
    reviewed_on = fields.Datetime(string='Reviewed On')
    result = fields.Selection([
        ('clear', 'No exception'),
        ('exception', 'Exception noted'),
        ('pending', 'Pending follow-up'),
    ], string='Result', default='pending')
    exception_note = fields.Text(string='Exception / Resolution Note')
    status = fields.Selection(SUBTAB_STATUS, string='Status', default='amber', tracking=True)


class ExecutionSamplingRequest(models.Model):
    _name = 'qaco.exec.sampling.request'
    _description = 'Sampling Request (ISA 530)'
    _order = 'id desc'

    name = fields.Char(string='Reference', required=True, default=lambda self: _('Sampling Request'))
    execution_phase_id = fields.Many2one('qaco.execution.phase', string='Execution Phase', required=True, ondelete='cascade')
    control_test_id = fields.Many2one('qaco.exec.control.test', string='Control Test', ondelete='set null')
    substantive_procedure_id = fields.Many2one('qaco.exec.substantive.procedure', string='Substantive Procedure', ondelete='set null')
    population_description = fields.Char(string='Population Description', required=True)
    population_amount = fields.Monetary(string='Population Value', currency_field='company_currency_id')
    population_size = fields.Integer(string='Population Size', required=True)
    tolerable_error = fields.Float(string='Tolerable Error %', default=5.0)
    expected_error = fields.Float(string='Expected Error %', default=0.0)
    risk_level = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], string='Risk Level', default='medium')
    method = fields.Selection(SAMPLING_METHODS, string='Sampling Method', default='random')
    sample_size = fields.Integer(string='Sample Size', compute='_compute_sample_size', store=True)
    sample_seed = fields.Char(string='Random Seed / Parameters')
    sample_file_id = fields.Many2one('ir.attachment', string='Sample Selection File')
    memo = fields.Html(string='Sampling Rationale Memo')
    company_currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('locked', 'Locked'),
    ], string='State', default='draft', tracking=True)

    @api.depends('population_size', 'tolerable_error', 'expected_error', 'risk_level')
    def _compute_sample_size(self):
        for record in self:
            if not record.population_size:
                record.sample_size = 0
                continue
            risk_multiplier = {'low': 0.5, 'medium': 1, 'high': 1.5}[record.risk_level]
            base = max(record.population_size * (record.tolerable_error / 100.0) * risk_multiplier, 1)
            record.sample_size = int(round(base))

    def action_lock_sampling(self):
        self.write({'state': 'locked'})


class ExecutionEvidenceItem(models.Model):
    _name = 'qaco.exec.evidence.item'
    _description = 'Evidence Item (ISA 500)'

    execution_phase_id = fields.Many2one('qaco.execution.phase', string='Execution Phase', required=True, ondelete='cascade')
    control_test_id = fields.Many2one('qaco.exec.control.test', string='Control Test', ondelete='set null')
    substantive_procedure_id = fields.Many2one('qaco.exec.substantive.procedure', string='Substantive Procedure', ondelete='set null')
    assertion_type = fields.Selection(ASSERTION_TYPES, string='Assertion', default='existence')
    evidence_type = fields.Selection(EVIDENCE_TIERS, string='Evidence Type', required=True, default='external')
    reliability_score = fields.Integer(string='Reliability Score', compute='_compute_reliability', store=True)
    attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_exec_evidence_rel', 'evidence_id', 'attachment_id',
        string='Attachments', required=True
    )
    description = fields.Char(string='Description', required=True)
    collected_by = fields.Many2one('res.users', string='Collected By', default=lambda self: self.env.user)
    collected_on = fields.Datetime(string='Collected On', default=fields.Datetime.now)
    isa_reference = fields.Char(string='ISA Reference', default='ISA 500')
    locked = fields.Boolean(string='Locked', default=False)

    def _compute_reliability(self):
        mapping = {'external': 3, 'internal': 2, 'inquiry': 1}
        for record in self:
            record.reliability_score = mapping.get(record.evidence_type, 1)


class ExecutionWorkpaper(models.Model):
    _name = 'qaco.exec.workpaper'
    _description = 'Execution Workpaper'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    execution_phase_id = fields.Many2one('qaco.execution.phase', string='Execution Phase', required=True, ondelete='cascade')
    name = fields.Char(string='Workpaper Name', required=True)
    workpaper_type = fields.Selection(WORKPAPER_TYPES, string='Type', required=True)
    template_reference = fields.Char(string='Template / Methodology Reference')
    balance_amount = fields.Monetary(string='Final Balance', currency_field='company_currency_id')
    company_currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_exec_workpaper_rel', 'workpaper_id', 'attachment_id',
        string='Supporting Files'
    )
    preparer_id = fields.Many2one('res.users', string='Preparer', default=lambda self: self.env.user)
    prepared_on = fields.Datetime(string='Prepared On', default=fields.Datetime.now)
    reviewer_id = fields.Many2one('res.users', string='Reviewer')
    reviewed_on = fields.Datetime(string='Reviewed On')
    review_note_ids = fields.One2many('qaco.exec.workpaper.note', 'workpaper_id', string='Review Notes')
    has_open_notes = fields.Boolean(string='Open Review Notes', compute='_compute_open_notes', store=True)
    locked = fields.Boolean(string='Locked', default=False)

    def _compute_open_notes(self):
        for record in self:
            record.has_open_notes = any(note.state == 'open' for note in record.review_note_ids)

    def toggle_lock(self):
        for record in self:
            if record.has_open_notes:
                raise UserError(_('Resolve review notes before locking the workpaper.'))
            record.locked = not record.locked


class ExecutionWorkpaperNote(models.Model):
    _name = 'qaco.exec.workpaper.note'
    _description = 'Workpaper Review Note'
    _order = 'id desc'

    workpaper_id = fields.Many2one('qaco.exec.workpaper', string='Workpaper', required=True, ondelete='cascade')
    author_id = fields.Many2one('res.users', string='Author', default=lambda self: self.env.user)
    note = fields.Text(string='Review Note', required=True)
    state = fields.Selection([
        ('open', 'Open'),
        ('resolved', 'Resolved'),
    ], string='Status', default='open', tracking=True)


class ExecutionPhase(models.Model):
    _name = 'execution.phase'
    _description = 'Audit Execution Phase'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Reference',
        required=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('execution.phase') or 'New'
    )
    client_id = fields.Many2one('res.partner', string='Client', required=True, domain=[('is_company', '=', True)])
    audit_lead_id = fields.Many2one('res.users', string='Audit Lead', default=lambda self: self.env.user)
    date_start = fields.Date(string='Start Date', default=fields.Date.today)
    date_end = fields.Date(string='End Date')
    fiscal_year = fields.Char(string='Fiscal Year', compute='_compute_fiscal_year', store=True)
    selected_head_ids = fields.Many2many(
        'account.account',
        string='Selected Accounting Heads',
        domain=[('deprecated', '=', False)]
    )
    head_details_ids = fields.One2many('execution.head.details', 'execution_phase_id', string='Head-wise Details')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('under_review', 'Under Review'),
        ('completed', 'Completed'),
    ], string='Status', default='draft', tracking=True)
    overall_progress = fields.Float(string='Overall Progress', compute='_compute_overall_progress')
    completed_heads_count = fields.Integer(string='Completed Heads', compute='_compute_progress_metrics')
    total_heads_count = fields.Integer(string='Total Heads', compute='_compute_progress_metrics')

    @api.depends('date_start')
    def _compute_fiscal_year(self):
        for record in self:
            if record.date_start:
                date_value = fields.Date.to_date(record.date_start)
                record.fiscal_year = str(date_value.year) if date_value else False
            else:
                record.fiscal_year = False

    @api.depends('head_details_ids.progress')
    def _compute_overall_progress(self):
        for record in self:
            progresses = record.head_details_ids.mapped('progress')
            record.overall_progress = (sum(progresses) / len(progresses)) if progresses else 0.0

    @api.depends('head_details_ids', 'head_details_ids.state')
    def _compute_progress_metrics(self):
        for record in self:
            record.total_heads_count = len(record.head_details_ids)
            record.completed_heads_count = len(record.head_details_ids.filtered(lambda h: h.state == 'completed'))

    def action_confirm_heads(self):
        for record in self:
            if not record.selected_head_ids:
                raise UserError('Please select at least one accounting head to proceed.')
            record.head_details_ids.unlink()
            for head in record.selected_head_ids:
                self.env['execution.head.details'].create({
                    'execution_phase_id': record.id,
                    'account_head_id': head.id,
                    'name': f"{record.name} - {head.name}",
                })
            record.state = 'in_progress'

    def action_mark_review(self):
        self.write({'state': 'under_review'})

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})


class ExecutionHeadDetails(models.Model):
    _name = 'execution.head.details'
    _description = 'Head-wise Execution Details'
    _inherit = ['mail.thread']
    _order = 'sequence'

    name = fields.Char(string='Reference', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    execution_phase_id = fields.Many2one('execution.phase', string='Execution Phase', required=True, ondelete='cascade')
    account_head_id = fields.Many2one('account.account', string='Accounting Head', required=True)
    account_code = fields.Char(string='Account Code', related='account_head_id.code', store=True)
    current_year_amount = fields.Float(string='Current Year Amount', digits=(16, 2))
    previous_year_amount = fields.Float(string='Previous Year Amount', digits=(16, 2))
    variance_amount = fields.Float(string='Variance Amount', compute='_compute_variance', digits=(16, 2))
    variance_percentage = fields.Float(string='Variance Percentage', compute='_compute_variance', digits=(16, 2))
    population_size = fields.Integer(string='Population Size')
    sample_size = fields.Integer(string='Sample Size')
    sampling_method = fields.Selection([
        ('random', 'Random Sampling'),
        ('systematic', 'Systematic Sampling'),
        ('monetary', 'Monetary Unit Sampling'),
        ('haphazard', 'Haphazard Sampling'),
    ], string='Sampling Method')
    population_amount = fields.Float(string='Population Amount', digits=(16, 2))
    sample_amount_tested = fields.Float(string='Sample Amount Tested', digits=(16, 2))
    coverage_percentage = fields.Float(string='Coverage Percentage', compute='_compute_coverage', digits=(16, 2))
    tested_percentage = fields.Float(string='Tested Percentage', compute='_compute_tested_percentage', digits=(16, 2), store=True)
    fully_tested = fields.Boolean(string='Fully Tested', compute='_compute_fully_tested', store=True)
    tolerable_error = fields.Float(string='Tolerable Error', digits=(16, 2))
    confidence_level = fields.Float(string='Confidence Level', default=95.0)
    nature = fields.Selection([
        ('revenue', 'Revenue'),
        ('expense', 'Expense'),
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
    ], string='Nature', compute='_compute_nature', store=True)
    risk_nature = fields.Selection([
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('significant', 'Significant Risk'),
    ], string='Risk Nature')
    risk_rating = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('significant', 'Significant'),
    ], string='Risk Rating', default='medium')
    significant_risk = fields.Boolean(string='Significant Risk Flag')
    inherent_risk = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Inherent Risk')
    control_risk = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Control Risk')
    detection_risk = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Detection Risk')
    risk_strength = fields.Selection([
        ('weak', 'Weak Controls'),
        ('moderate', 'Moderate Controls'),
        ('strong', 'Strong Controls'),
    ], string='Control Strength')
    overall_risk_assessment = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Overall Risk Assessment', compute='_compute_overall_risk')
    assertion_ids = fields.Many2many(
        'audit.assertion',
        'execution_head_assertion_rel',
        'head_id',
        'assertion_id',
        string='Assertions'
    )
    risk_description = fields.Html(string='Risk Description')
    relying_on_controls = fields.Boolean(string='Relying on Controls')
    control_design_effective = fields.Boolean(string='Control Design Effective')
    control_operating_effective = fields.Boolean(string='Control Operating Effective')
    state = fields.Selection([
        ('draft', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ], string='Status', default='draft')
    progress = fields.Float(string='Progress', compute='_compute_progress')
    audit_procedure_ids = fields.One2many('audit.procedure', 'head_details_id', string='Audit Procedures')
    test_of_details_ids = fields.One2many('test.of.details', 'head_details_id', string='Test of Details')
    test_of_controls_ids = fields.One2many('test.of.controls', 'head_details_id', string='Test of Controls')
    evidence_ids = fields.One2many('audit.evidence', 'head_details_id', string='Evidences')
    analytical_procedure_ids = fields.One2many('execution.analytical.procedure', 'head_details_id', string='Analytical Procedures')

    @api.depends('current_year_amount', 'previous_year_amount')
    def _compute_variance(self):
        for record in self:
            if record.previous_year_amount:
                record.variance_amount = record.current_year_amount - record.previous_year_amount
                record.variance_percentage = (record.variance_amount / record.previous_year_amount) * 100
            else:
                record.variance_amount = 0.0
                record.variance_percentage = 0.0

    @api.depends('population_amount', 'sample_amount_tested')
    def _compute_coverage(self):
        for record in self:
            if record.population_amount:
                record.coverage_percentage = (record.sample_amount_tested / record.population_amount) * 100
            else:
                record.coverage_percentage = 0.0

    @api.depends('sample_amount_tested', 'population_amount')
    def _compute_tested_percentage(self):
        for record in self:
            if record.population_amount:
                record.tested_percentage = (record.sample_amount_tested / record.population_amount) * 100
            else:
                record.tested_percentage = 0.0

    @api.depends('tested_percentage')
    def _compute_fully_tested(self):
        for record in self:
            record.fully_tested = record.tested_percentage >= 95.0

    @api.depends('account_head_id.account_type')
    def _compute_nature(self):
        mapping = {
            'income': 'revenue',
            'income_other': 'revenue',
            'expense': 'expense',
            'expense_depreciation': 'expense',
            'expense_direct_cost': 'expense',
            'asset_receivable': 'asset',
            'asset_cash': 'asset',
            'asset_current': 'asset',
            'asset_non_current': 'asset',
            'asset_prepayments': 'asset',
            'asset_fixed': 'asset',
            'liability_payable': 'liability',
            'liability_credit_card': 'liability',
            'liability_current': 'liability',
            'liability_non_current': 'liability',
            'equity': 'equity',
            'equity_unaffected': 'equity',
        }
        for record in self:
            record.nature = mapping.get(record.account_head_id.account_type, False) if record.account_head_id else False

    @api.depends('inherent_risk', 'control_risk', 'detection_risk')
    def _compute_overall_risk(self):
        for record in self:
            risks = [record.inherent_risk, record.control_risk, record.detection_risk]
            if 'high' in risks:
                record.overall_risk_assessment = 'high'
            elif 'medium' in risks:
                record.overall_risk_assessment = 'medium'
            else:
                record.overall_risk_assessment = 'low'

    @api.depends('state', 'audit_procedure_ids', 'audit_procedure_ids.is_completed')
    def _compute_progress(self):
        for record in self:
            if record.state == 'completed':
                record.progress = 100.0
            elif record.state == 'in_progress' and record.audit_procedure_ids:
                total = len(record.audit_procedure_ids)
                completed = len(record.audit_procedure_ids.filtered(lambda p: p.is_completed))
                record.progress = (completed / total) * 100 if total else 0.0
            else:
                record.progress = 0.0

    def action_start_execution(self):
        self.write({'state': 'in_progress'})

    def action_complete_head(self):
        self.write({'state': 'completed'})

    def action_reset_head(self):
        self.write({'state': 'draft'})


class AuditProcedure(models.Model):
    _name = 'audit.procedure'
    _description = 'Audit Procedure'
    _order = 'sequence'

    sequence = fields.Integer(string='Sequence', default=10)
    head_details_id = fields.Many2one('execution.head.details', string='Head Details', ondelete='cascade')
    head_execution_id = fields.Many2one('audit.head.execution', string='Head Execution', ondelete='cascade')
    procedure_template_id = fields.Many2one('audit.procedure.template', string='Procedure Template')
    procedure_name = fields.Char(string='Procedure Name', required=True)
    procedure_description = fields.Html(string='Description', related='procedure_template_id.description', store=True)
    procedure_type = fields.Selection([
        ('risk_assessment', 'Risk Assessment'),
        ('test_of_controls', 'Test of Controls'),
        ('substantive', 'Substantive Procedure'),
        ('analytical', 'Analytical Procedure'),
    ], string='Procedure Type', required=True)
    risk_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Risk Level', default='medium')
    is_completed = fields.Boolean(string='Completed')
    performed_by = fields.Many2one('res.users', string='Performed By')
    performed_date = fields.Date(string='Performed Date')
    result = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('unsatisfactory', 'Unsatisfactory'),
        ('not_applicable', 'Not Applicable'),
    ], string='Result')
    findings = fields.Html(string='Findings')
    notes = fields.Text(string='Notes')


class TestOfDetails(models.Model):
    _name = 'test.of.details'
    _description = 'Test of Details'
    _order = 'sequence'

    sequence = fields.Integer(string='Sequence', default=10)
    head_details_id = fields.Many2one('execution.head.details', string='Head Details', ondelete='cascade')
    head_execution_id = fields.Many2one('audit.head.execution', string='Head Execution', ondelete='cascade')
    test_objective = fields.Char(string='Test Objective', required=True)
    assertion_tested = fields.Selection([
        ('existence', 'Existence'),
        ('completeness', 'Completeness'),
        ('valuation', 'Valuation'),
        ('rights_obligations', 'Rights and Obligations'),
        ('presentation', 'Presentation and Disclosure'),
    ], string='Assertion Tested', required=True)
    test_method = fields.Selection([
        ('inspection', 'Inspection'),
        ('observation', 'Observation'),
        ('confirmation', 'Confirmation'),
        ('recalculation', 'Recalculation'),
        ('reperformance', 'Reperformance'),
        ('analytical', 'Analytical Procedures'),
    ], string='Test Method', required=True)
    test_details = fields.Html(string='Test Details')
    population_size = fields.Integer(string='Population Size')
    sample_size = fields.Integer(string='Sample Size')
    sampling_method = fields.Selection([
        ('random', 'Random Sampling'),
        ('systematic', 'Systematic Sampling'),
        ('monetary', 'Monetary Unit Sampling'),
        ('haphazard', 'Haphazard Sampling'),
    ], string='Sampling Method')
    population_amount = fields.Float(string='Population Amount', digits=(16, 2))
    sample_amount = fields.Float(string='Sample Amount', digits=(16, 2))
    coverage_percentage = fields.Float(string='Coverage %', compute='_compute_coverage_percentage', digits=(6, 2), store=True)
    sample_items_tested = fields.Integer(string='Sample Items Tested')
    exceptions_found = fields.Integer(string='Exceptions Found')
    test_result = fields.Selection([
        ('satisfactory', 'Satisfactory'),
        ('unsatisfactory', 'Unsatisfactory'),
        ('qualified', 'Qualified'),
    ], string='Test Result')
    conclusion = fields.Text(string='Conclusion')


class TestOfControls(models.Model):
    _name = 'test.of.controls'
    _description = 'Test of Controls'

    head_details_id = fields.Many2one('execution.head.details', string='Head Details', ondelete='cascade')
    head_execution_id = fields.Many2one('audit.head.execution', string='Head Execution', ondelete='cascade')
    control_objective = fields.Char(string='Control Objective', required=True)
    control_activity = fields.Text(string='Control Activity', required=True)
    frequency = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
    ], string='Frequency', required=True)
    control_testing_details = fields.Html(string='Testing Details')
    sample_size = fields.Integer(string='Sample Size')
    sample_method = fields.Selection([
        ('random', 'Random Sampling'),
        ('systematic', 'Systematic Sampling'),
        ('judgmental', 'Judgmental Sampling')
    ], string='Sampling Method')
    exceptions_found = fields.Integer(string='Exceptions Found')
    deviations = fields.Integer(string='Deviations Found')
    control_effectiveness = fields.Selection([
        ('effective', 'Effective'),
        ('partially_effective', 'Partially Effective'),
        ('ineffective', 'Ineffective'),
    ], string='Control Effectiveness')
    control_effective = fields.Boolean(string='Control Effective')
    control_conclusion = fields.Text(string='Conclusion')


class AuditEvidence(models.Model):
    _name = 'audit.evidence'
    _description = 'Audit Evidence'

    head_details_id = fields.Many2one('execution.head.details', string='Head Details', ondelete='cascade')
    head_execution_id = fields.Many2one('audit.head.execution', string='Head Execution', ondelete='cascade')
    evidence_type = fields.Selection([
        ('physical', 'Physical Examination'),
        ('documentary', 'Documentary Evidence'),
        ('analytical', 'Analytical Evidence'),
        ('oral', 'Oral Evidence'),
        ('electronic', 'Electronic Evidence'),
        ('confirmation', 'External Confirmation'),
    ], string='Evidence Type', required=True)
    description = fields.Text(string='Description', required=True)
    reliability = fields.Selection([
        ('high', 'High Reliability'),
        ('medium', 'Medium Reliability'),
        ('low', 'Low Reliability'),
    ], string='Reliability', required=True)
    collected_by = fields.Many2one('res.users', string='Collected By', default=lambda self: self.env.user)
    collection_date = fields.Date(string='Collection Date', default=fields.Date.today)
    attachment_id = fields.Many2one('ir.attachment', string='Attachment')
    evidence_notes = fields.Text(string='Notes')


class ExecutionAnalyticalProcedure(models.Model):
    _name = 'execution.analytical.procedure'
    _description = 'Execution Analytical Procedure'
    _order = 'sequence'

    sequence = fields.Integer(string='Sequence', default=10)
    head_details_id = fields.Many2one('execution.head.details', string='Head Details', ondelete='cascade')
    head_execution_id = fields.Many2one('audit.head.execution', string='Head Execution', ondelete='cascade')
    procedure_description = fields.Char(string='Procedure Description', required=True)
    procedure_type = fields.Selection([
        ('ratio', 'Ratio Analysis'),
        ('trend', 'Trend Analysis'),
        ('comparison', 'Comparison Analysis'),
        ('reasonableness', 'Reasonableness Test'),
    ], string='Procedure Type', required=True)
    current_year_amount = fields.Float(string='Current Year Amount', digits=(16, 2))
    previous_year_amount = fields.Float(string='Previous Year Amount', digits=(16, 2))
    budget_amount = fields.Float(string='Budget Amount', digits=(16, 2))
    industry_average = fields.Float(string='Industry Average', digits=(16, 2))
    variance_cy_py = fields.Float(string='Variance CY vs PY', compute='_compute_variances', digits=(16, 2))
    variance_cy_budget = fields.Float(string='Variance CY vs Budget', compute='_compute_variances', digits=(16, 2))
    variance_percentage = fields.Float(string='Variance %', compute='_compute_variances', digits=(16, 2))
    expectation_met = fields.Boolean(string='Expectation Met')
    unusual_fluctuation = fields.Boolean(string='Unusual Fluctuation')
    investigation_required = fields.Boolean(string='Investigation Required')
    analysis_notes = fields.Text(string='Analysis Notes')
    follow_up_actions = fields.Text(string='Follow-up Actions')

    @api.depends('current_year_amount', 'previous_year_amount', 'budget_amount')
    def _compute_variances(self):
        for record in self:
            record.variance_cy_py = (record.current_year_amount - record.previous_year_amount) if record.previous_year_amount else 0.0
            record.variance_cy_budget = (record.current_year_amount - record.budget_amount) if record.budget_amount else 0.0
            if record.previous_year_amount:
                record.variance_percentage = ((record.current_year_amount - record.previous_year_amount) / record.previous_year_amount) * 100
            else:
                record.variance_percentage = 0.0


class AuditExecutionMaster(models.Model):
    _name = 'audit.execution.master'
    _description = 'Audit Execution Master Dashboard'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence asc, create_date desc'

    name = fields.Char(
        string='Execution Reference',
        required=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('audit.execution.master') or 'New',
    )
    sequence = fields.Integer(string='Sequence', default=10)
    client_id = fields.Many2one('res.partner', string='Client', required=True, domain=[('is_company', '=', True)])
    audit_engagement_id = fields.Many2one('qaco.audit.engagement', string='Audit Engagement')
    audit_lead_id = fields.Many2one('res.users', string='Audit Lead', default=lambda self: self.env.user)
    team_member_ids = fields.Many2many('res.users', string='Team Members')
    date_start = fields.Date(string='Start Date', default=fields.Date.today)
    date_end = fields.Date(string='End Date')
    fiscal_year = fields.Char(string='Fiscal Year', compute='_compute_fiscal_year', store=True)
    state = fields.Selection([
        ('draft', '📝 Draft'),
        ('planning', '📋 Planning'),
        ('in_progress', '🔄 In Progress'),
        ('under_review', '👀 Under Review'),
        ('completed', '✅ Completed')
    ], string='Status', default='draft', tracking=True)
    overall_progress = fields.Float(string='Overall Progress', compute='_compute_overall_progress')
    risk_coverage = fields.Float(string='Risk Coverage %', compute='_compute_risk_coverage')
    testing_completion = fields.Float(string='Testing Completion %', compute='_compute_testing_completion')
    selected_head_ids = fields.Many2many('account.account', string='Selected Accounting Heads', domain=[('deprecated', '=', False)])
    head_execution_ids = fields.One2many('audit.head.execution', 'master_id', string='Head-wise Executions')
    total_heads_count = fields.Integer(string='Total Heads', compute='_compute_summary_metrics', store=True)
    completed_heads_count = fields.Integer(string='Completed Heads', compute='_compute_summary_metrics', store=True)
    high_risk_heads_count = fields.Integer(string='High Risk Heads', compute='_compute_summary_metrics', store=True)
    significant_risks_count = fields.Integer(string='Significant Risks', compute='_compute_summary_metrics', store=True)

    @api.depends('date_start')
    def _compute_fiscal_year(self):
        for record in self:
            if record.date_start:
                record.fiscal_year = str(record.date_start.year)
            else:
                record.fiscal_year = str(date.today().year)

    @api.depends('head_execution_ids.progress')
    def _compute_overall_progress(self):
        for record in self:
            if record.head_execution_ids:
                total_progress = sum(head.progress for head in record.head_execution_ids)
                record.overall_progress = total_progress / len(record.head_execution_ids)
            else:
                record.overall_progress = 0.0

    @api.depends('head_execution_ids.risk_coverage')
    def _compute_risk_coverage(self):
        for record in self:
            if record.head_execution_ids:
                total_coverage = sum(head.risk_coverage for head in record.head_execution_ids)
                record.risk_coverage = total_coverage / len(record.head_execution_ids)
            else:
                record.risk_coverage = 0.0

    @api.depends('head_execution_ids.testing_completion')
    def _compute_testing_completion(self):
        for record in self:
            if record.head_execution_ids:
                total_completion = sum(head.testing_completion for head in record.head_execution_ids)
                record.testing_completion = total_completion / len(record.head_execution_ids)
            else:
                record.testing_completion = 0.0

    @api.depends('head_execution_ids')
    def _compute_summary_metrics(self):
        for record in self:
            record.total_heads_count = len(record.head_execution_ids)
            record.completed_heads_count = len(record.head_execution_ids.filtered(lambda h: h.state == 'completed'))
            record.high_risk_heads_count = len(record.head_execution_ids.filtered(lambda h: h.risk_rating in ['high', 'significant']))
            record.significant_risks_count = len(record.head_execution_ids.filtered(lambda h: h.significant_risk))

    def action_confirm_planning(self):
        for record in self:
            if not record.selected_head_ids:
                raise UserError("Please select accounting heads before confirming planning!")
            existing_heads = record.head_execution_ids.mapped('account_head_id')
            for head in record.selected_head_ids:
                if head not in existing_heads:
                    self.env['audit.head.execution'].create({
                        'master_id': record.id,
                        'account_head_id': head.id,
                        'name': f"{record.name} - {head.name}",
                    })
            record.state = 'planning'

    def action_start_execution(self):
        self.state = 'in_progress'

    def action_send_review(self):
        self.state = 'under_review'

    def action_complete(self):
        self.state = 'completed'

    def action_reset_draft(self):
        self.state = 'draft'


class AuditHeadExecution(models.Model):
    _name = 'audit.head.execution'
    _description = 'Head-wise Audit Execution'
    _inherit = ['mail.thread']
    _order = 'sequence asc'

    name = fields.Char(string='Reference', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    master_id = fields.Many2one('audit.execution.master', string='Master Execution', required=True, ondelete='cascade')
    account_head_id = fields.Many2one('account.account', string='Accounting Head', required=True)
    account_code = fields.Char(string='Account Code', related='account_head_id.code', store=True)
    nature = fields.Selection([
        ('revenue', '💰 Revenue'),
        ('expense', '💸 Expense'),
        ('asset', '🏦 Asset'),
        ('liability', '📋 Liability'),
        ('equity', '📊 Equity')
    ], string='Nature', compute='_compute_nature', store=True)
    assertion_ids = fields.Many2many('audit.assertion', string='Assertions', required=True)
    risk_rating = fields.Selection([
        ('low', '🟢 Low'),
        ('medium', '🟡 Medium'),
        ('high', '🔴 High'),
        ('significant', '⚠️ Significant')
    ], string='Risk Rating', required=True, default='medium')
    significant_risk = fields.Boolean(string='Significant Risk')
    risk_description = fields.Html(string='Risk Description')
    relying_on_controls = fields.Boolean(string='Relying on Entity Controls')
    control_design_effective = fields.Boolean(string='Control Design Effective')
    control_operating_effective = fields.Boolean(string='Control Operating Effective')
    current_year_amount = fields.Float(string='Current Year Amount', digits=(16, 2))
    previous_year_amount = fields.Float(string='Previous Year Amount', digits=(16, 2))
    variance_amount = fields.Float(string='Variance Amount', compute='_compute_variance', digits=(16, 2))
    variance_percentage = fields.Float(string='Variance %', compute='_compute_variance', digits=(16, 2))
    population_size = fields.Integer(string='Population Size')
    sample_size = fields.Integer(string='Sample Size')
    sampling_method = fields.Selection([
        ('random', '🎲 Random Sampling'),
        ('systematic', '📊 Systematic Sampling'),
        ('monetary', '💰 Monetary Unit Sampling'),
        ('haphazard', '🎯 Haphazard Sampling')
    ], string='Sampling Method')
    population_amount = fields.Float(string='Population Amount', digits=(16, 2))
    sample_amount_tested = fields.Float(string='Sample Amount Tested', digits=(16, 2))
    coverage_percentage = fields.Float(string='Coverage %', compute='_compute_coverage_percentage')
    state = fields.Selection([
        ('draft', '📝 Not Started'),
        ('in_progress', '🔄 In Progress'),
        ('completed', '✅ Completed')
    ], string='Status', default='draft')
    progress = fields.Float(string='Progress %', compute='_compute_progress')
    risk_coverage = fields.Float(string='Risk Coverage %', compute='_compute_risk_coverage')
    testing_completion = fields.Float(string='Testing Completion %', compute='_compute_testing_completion')
    procedure_ids = fields.One2many('audit.procedure', 'head_execution_id', string='Audit Procedures')
    test_of_controls_ids = fields.One2many('test.of.controls', 'head_execution_id', string='Test of Controls')
    test_of_details_ids = fields.One2many('test.of.details', 'head_execution_id', string='Test of Details')
    analytical_ids = fields.One2many('execution.analytical.procedure', 'head_execution_id', string='Analytical Procedures')
    evidence_ids = fields.One2many('audit.evidence', 'head_execution_id', string='Evidences')

    @api.depends('account_head_id')
    def _compute_nature(self):
        mapping = {
            'income': 'revenue',
            'expense': 'expense',
            'asset': 'asset',
            'liability': 'liability',
            'equity': 'equity',
        }
        for record in self:
            record.nature = mapping.get(record.account_head_id.user_type_id.type, False) if record.account_head_id else False

    @api.depends('current_year_amount', 'previous_year_amount')
    def _compute_variance(self):
        for record in self:
            if record.previous_year_amount:
                record.variance_amount = record.current_year_amount - record.previous_year_amount
                record.variance_percentage = (record.variance_amount / record.previous_year_amount) * 100
            else:
                record.variance_amount = 0.0
                record.variance_percentage = 0.0

    @api.depends('population_amount', 'sample_amount_tested')
    def _compute_coverage_percentage(self):
        for record in self:
            if record.population_amount:
                record.coverage_percentage = (record.sample_amount_tested / record.population_amount) * 100
            else:
                record.coverage_percentage = 0.0

    @api.depends('state', 'procedure_ids.is_completed')
    def _compute_progress(self):
        for record in self:
            if record.state == 'completed':
                record.progress = 100.0
            elif record.procedure_ids:
                completed = len(record.procedure_ids.filtered(lambda p: p.is_completed))
                total = len(record.procedure_ids)
                record.progress = (completed / total) * 100 if total > 0 else 0.0
            else:
                record.progress = 0.0

    @api.depends('test_of_details_ids.coverage_percentage')
    def _compute_risk_coverage(self):
        for record in self:
            if record.test_of_details_ids:
                total_coverage = sum(test.coverage_percentage for test in record.test_of_details_ids)
                record.risk_coverage = total_coverage / len(record.test_of_details_ids)
            else:
                record.risk_coverage = 0.0

    @api.depends('procedure_ids.is_completed', 'test_of_details_ids', 'test_of_controls_ids')
    def _compute_testing_completion(self):
        for record in self:
            total_tests = len(record.procedure_ids) + len(record.test_of_details_ids) + len(record.test_of_controls_ids)
            if total_tests > 0:
                completed_tests = (
                    len(record.procedure_ids.filtered(lambda p: p.is_completed)) +
                    len(record.test_of_details_ids.filtered(lambda t: t.test_result == 'satisfactory')) +
                    len(record.test_of_controls_ids.filtered(lambda c: c.control_effectiveness == 'effective'))
                )
                record.testing_completion = (completed_tests / total_tests) * 100
            else:
                record.testing_completion = 0.0

    def action_start_head(self):
        self.state = 'in_progress'

    def action_complete_head(self):
        self.state = 'completed'
