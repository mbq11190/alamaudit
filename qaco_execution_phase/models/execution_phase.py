# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


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


class ExecutionPhase(models.Model):
    _name = 'qaco.execution.phase'
    _description = 'Execution Phase'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    audit_id = fields.Many2one('qaco.audit', string='Audit', required=True, ondelete='cascade')
    client_id = fields.Many2one('res.partner', string='Client Name', related='audit_id.client_id', readonly=True, store=True)
    planning_phase_id = fields.Many2one('qaco.planning.phase', string='Planning Phase', compute='_compute_planning_phase', store=True, readonly=False)

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
            statuses = [record.control_status, record.substantive_status, record.sampling_status,
                        record.evidence_status, record.workpaper_status]
            checklist_ok = all([
                record.checklist_controls_linked,
                record.checklist_walkthrough_documented,
                record.checklist_exceptions_escalated,
                record.checklist_substantive_assertions,
                record.checklist_sampling_signed,
                record.checklist_evidence_sufficient,
                record.checklist_workpapers_reviewed,
            ])
            if any(status == 'red' for status in statuses) or not checklist_ok:
                state = 'red'
                if not record.checklist_evidence_sufficient:
                    alerts.append(_('Evidence sufficiency meter still red.'))
                if record.open_critical_risk_count:
                    alerts.append(_('Open significant risks pending conclusion.'))
                if not record.checklist_sampling_signed:
                    alerts.append(_('Sampling rationales need documentation.'))
            elif any(status == 'amber' for status in statuses):
                state = 'amber'
                alerts.append(_('Some execution sub-tabs still amber; finalize workpapers.'))
            else:
                state = 'green'
                alerts.append(_('All ISA checkpoints satisfied.'))
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
