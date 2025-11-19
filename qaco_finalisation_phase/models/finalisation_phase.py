# -*- coding: utf-8 -*-

from datetime import timedelta
from typing import TYPE_CHECKING, Any

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError  # type: ignore[attr-defined]


SUBTAB_STATUS = [
    ('red', '❌ Incomplete'),
    ('amber', '🟡 In Progress'),
    ('green', '✅ Complete'),
]

ASSERTION_TYPES = [
    ('existence', 'Existence / Occurrence'),
    ('completeness', 'Completeness / Cut-off'),
    ('valuation', 'Valuation / Allocation'),
    ('rights', 'Rights & Obligations'),
    ('presentation', 'Presentation & Disclosure'),
]

MISSTATEMENT_TYPES = [
    ('factual', 'Factual'),
    ('judgmental', 'Judgmental'),
    ('projected', 'Projected'),
]

MISSTATEMENT_STATUS = [
    ('corrected', 'Corrected'),
    ('uncorrected', 'Uncorrected'),
]

EVENT_CLASSIFICATION = [
    ('adjusting', 'Adjusting Event'),
    ('non_adjusting', 'Non-Adjusting (Disclosure)'),
]

PROCEDURE_CODES = [
    ('minutes', 'Review post year-end board minutes'),
    ('management_accounts', 'Review post year-end management accounts'),
    ('inquiry', 'Inquiry of management'),
    ('legal', 'Confirmation from legal counsel'),
    ('representation', 'Specific representation re subsequent events'),
]

GOING_CONCERN_CONCLUSION = [
    ('no_uncertainty', 'No material uncertainty'),
    ('material_uncertainty', 'Material uncertainty exists'),
    ('not_going_concern', 'Entity not a going concern'),
]

REGULATOR_CHOICES = [
    ('icap', 'ICAP'),
    ('secp', 'SECP'),
    ('aob', 'AOB'),
    ('sbp', 'State Bank of Pakistan'),
    ('insurance', 'Insurance Regulator'),
    ('other', 'Other'),
]

REVIEW_NOTE_STATES = [
    ('open', 'Open'),
    ('in_progress', 'In Progress'),
    ('resolved', 'Resolved'),
]

ALERT_SEVERITY = [
    ('info', 'Info'),
    ('warning', 'Warning'),
    ('critical', 'Critical'),
]


class FinalisationPhase(models.Model):
    _name = 'qaco.finalisation.phase'
    _description = 'Finalisation Phase'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    if TYPE_CHECKING:
        def activity_schedule(self, *args: Any, **kwargs: Any) -> Any: ...

        def message_post(self, *args: Any, **kwargs: Any) -> Any: ...

    name = fields.Char(string='Reference', compute='_compute_name', store=True, readonly=True)
    audit_id = fields.Many2one('qaco.audit', string='Audit Engagement', required=True, ondelete='cascade')
    client_id = fields.Many2one('res.partner', string='Client', related='audit_id.client_id', readonly=True, store=True)
    planning_phase_id = fields.Many2one('qaco.planning.phase', string='Planning Phase', compute='_compute_related_phases', store=True, readonly=True)
    execution_phase_id = fields.Many2one('qaco.execution.phase', string='Execution Phase', compute='_compute_related_phases', store=True, readonly=True)

    misstatement_status = fields.Selection(SUBTAB_STATUS, compute='_compute_submodule_statuses', store=True, tracking=True)
    subsequent_status = fields.Selection(SUBTAB_STATUS, compute='_compute_submodule_statuses', store=True, tracking=True)
    going_concern_status = fields.Selection(SUBTAB_STATUS, compute='_compute_submodule_statuses', store=True, tracking=True)
    related_party_status = fields.Selection(SUBTAB_STATUS, compute='_compute_submodule_statuses', store=True, tracking=True)
    representation_status = fields.Selection(SUBTAB_STATUS, compute='_compute_submodule_statuses', store=True, tracking=True)
    analytics_status = fields.Selection(SUBTAB_STATUS, compute='_compute_submodule_statuses', store=True, tracking=True)
    completion_status = fields.Selection(SUBTAB_STATUS, compute='_compute_submodule_statuses', store=True, tracking=True)

    signoff_unlocked = fields.Boolean(string='Sign-off Submodule Available', compute='_compute_signoff_unlock', store=True)
    compliance_scan_passed = fields.Boolean(string='Compliance Scan Passed', tracking=True, copy=False)
    compliance_scan_log = fields.Html(string='Compliance Scan Findings', copy=False)
    final_file_locked = fields.Boolean(string='File Locked', tracking=True, copy=False)
    archive_deadline_date = fields.Date(string='Archive Deadline (ISA 230)', copy=False)
    regulatory_news = fields.Html(string='Regulatory Update Feed', compute='_compute_regulatory_feed', sanitize=False, copy=False)

    overall_materiality_ref = fields.Monetary(string='Overall Materiality Ref', currency_field='company_currency_id', compute='_compute_materiality_refs', store=True, readonly=True)
    performance_materiality_ref = fields.Monetary(string='Performance Materiality Ref', currency_field='company_currency_id', compute='_compute_materiality_refs', store=True, readonly=True)
    company_currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    misstatement_line_ids = fields.One2many('qaco.final.misstatement', 'finalisation_phase_id', string='Misstatements')
    misstatement_summary_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_final_misstatement_summary_rel', 'phase_id', 'attachment_id',
        string='Summary of Uncorrected Misstatements', help='Upload the final ISA 450 template.'
    )
    misstatement_support_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_final_misstatement_support_rel', 'phase_id', 'attachment_id',
        string='Detailed Working Papers'
    )
    misstatement_correspondence_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_final_misstatement_correspondence_rel', 'phase_id', 'attachment_id',
        string='Management Correspondence'
    )
    uncorrected_total = fields.Monetary(string='Uncorrected Misstatements', currency_field='company_currency_id', compute='_compute_misstatement_totals', store=True)
    corrected_total = fields.Monetary(string='Corrected Misstatements', currency_field='company_currency_id', compute='_compute_misstatement_totals', store=True)
    misstatement_threshold_percent = fields.Float(string='Threshold % of Materiality', default=70.0)
    threshold_breached = fields.Boolean(string='Threshold Breached', compute='_compute_threshold_breach', store=True)
    pervasiveness_memo = fields.Html(string='Conclusion on Pervasiveness Memo')
    partner_override_note = fields.Html(string='Partner Override Memo')
    management_followup_note = fields.Html(string='Management Follow-up Summary')
    checklist_misstatement_evaluated = fields.Boolean(string='All misstatements evaluated', tracking=True)
    checklist_cumulative_below_materiality = fields.Boolean(string='Cumulative impact below materiality', tracking=True)
    checklist_qualitative_considered = fields.Boolean(string='Qualitative impact considered', tracking=True)
    checklist_disclosures_reassessed = fields.Boolean(string='Disclosures reassessed', tracking=True)

    subsequent_procedure_ids = fields.One2many('qaco.final.subsequent.procedure', 'finalisation_phase_id', string='Subsequent Event Procedures')
    subsequent_event_ids = fields.One2many('qaco.final.subsequent.event', 'finalisation_phase_id', string='Identified Events')
    subsequent_minutes_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_final_subsequent_minutes_rel', 'phase_id', 'attachment_id',
        string='Post Year-end Minutes'
    )
    subsequent_legal_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_final_subsequent_legal_rel', 'phase_id', 'attachment_id',
        string='Legal Confirmations'
    )
    subsequent_checklist_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_final_subsequent_checklist_rel', 'phase_id', 'attachment_id',
        string='Subsequent Events Checklist'
    )
    checklist_sub_events_period_covered = fields.Boolean(string='Procedures cover up to report date', tracking=True)
    checklist_sub_events_adjusting = fields.Boolean(string='Adjusting events recorded', tracking=True)
    checklist_sub_events_disclosure = fields.Boolean(string='Non-adjusting events disclosed', tracking=True)

    going_concern_scenario_ids = fields.One2many('qaco.final.gc.scenario', 'finalisation_phase_id', string='Scenario Analysis')
    going_concern_covenant_ids = fields.One2many('qaco.final.gc.covenant', 'finalisation_phase_id', string='Covenant Calculator')
    going_concern_conclusion = fields.Selection(GOING_CONCERN_CONCLUSION, string='Final Going Concern Conclusion', required=True, default='no_uncertainty')
    emphasis_matter_required = fields.Boolean(string='Emphasis of Matter Needed', compute='_compute_emphasis_of_matter', store=True)
    going_concern_assessment_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_final_gc_assessment_rel', 'phase_id', 'attachment_id', string='Management Assessment'
    )
    going_concern_forecast_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_final_gc_forecast_rel', 'phase_id', 'attachment_id', string='Forecasts (12 months)'
    )
    going_concern_covenant_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_final_gc_covenant_rel', 'phase_id', 'attachment_id', string='Covenant Certificates'
    )
    going_concern_memo_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_final_gc_memo_rel', 'phase_id', 'attachment_id', string='Going Concern Memo'
    )
    checklist_gc_assessment_challenged = fields.Boolean(string='Management assessment challenged', tracking=True)
    checklist_gc_future_info_considered = fields.Boolean(string='Future info considered', tracking=True)
    checklist_gc_basis_appropriate = fields.Boolean(string='Basis of prep appropriate', tracking=True)
    checklist_gc_reporting_impact = fields.Boolean(string='Reporting impact evaluated', tracking=True)

    related_party_line_ids = fields.One2many('qaco.final.related.party', 'finalisation_phase_id', string='Related Party Register')
    non_compliance_log_ids = fields.One2many('qaco.final.noncompliance', 'finalisation_phase_id', string='Non-Compliance Log')
    related_party_register_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_final_related_register_rel', 'phase_id', 'attachment_id', string='Final RPT Register'
    )
    related_party_minutes_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_final_related_minutes_rel', 'phase_id', 'attachment_id', string='Board Approvals'
    )
    noncompliance_summary_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_final_noncompliance_summary_rel', 'phase_id', 'attachment_id', string='Non-compliance Summary'
    )
    checklist_related_complete = fields.Boolean(string='Register complete & accurate', tracking=True)
    checklist_related_authorised = fields.Boolean(string='Transactions authorised', tracking=True)
    checklist_related_disclosures_ok = fields.Boolean(string='Disclosures comply with IFRS', tracking=True)
    checklist_noncompliance_communicated = fields.Boolean(string='Non-compliance communicated to TCWG', tracking=True)

    representation_letter_template = fields.Html(string='Representation Letter Template', compute='_compute_representation_template', sanitize=False, store=True)
    representation_letter_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_final_rep_letter_rel', 'phase_id', 'attachment_id', string='Signed Representation Letter'
    )
    representation_letter_signed_on = fields.Date(string='Representation Letter Dated')
    checklist_rep_obtained = fields.Boolean(string='Signed letter obtained', tracking=True)
    checklist_rep_content_complete = fields.Boolean(string='Letter covers all representations', tracking=True)
    checklist_rep_date_valid = fields.Boolean(string='Letter appropriately dated', tracking=True)

    analytics_ratio_ids = fields.One2many('qaco.final.analytics.ratio', 'finalisation_phase_id', string='Analytics')
    analytics_variance_ids = fields.One2many('qaco.final.analytics.variance', 'finalisation_phase_id', string='Variance Flags')
    analytics_workbook_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_final_analytics_workbook_rel', 'phase_id', 'attachment_id', string='Analytical Review Workbook'
    )
    analytics_conclusion_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_final_analytics_conclusion_rel', 'phase_id', 'attachment_id', string='Overall Conclusion Memo'
    )
    checklist_analytics_corrob = fields.Boolean(string='Analytics corroborate conclusions', tracking=True)
    checklist_variances_resolved = fields.Boolean(string='Variance explanations documented', tracking=True)
    checklist_fs_compliant = fields.Boolean(string='FS form/content compliant', tracking=True)

    review_note_ids = fields.One2many('qaco.final.review.note', 'finalisation_phase_id', string='Review Notes')
    regulatory_alert_ids = fields.One2many('qaco.final.regulatory.alert', 'finalisation_phase_id', string='Regulatory Alerts')
    checklist_review_notes_cleared = fields.Boolean(string='Review notes cleared', tracking=True)
    checklist_compliance_scan = fields.Boolean(string='Compliance scan passed', tracking=True)
    checklist_partner_approval = fields.Boolean(string='Partner final approval obtained', tracking=True)
    checklist_archive_ready = fields.Boolean(string='File ready for archiving', tracking=True)
    completion_certificate_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_final_completion_certificate_rel', 'phase_id', 'attachment_id', string='File Completion Checklist'
    )

    audit_report_date = fields.Date(string='Audit Report Date', required=True, default=lambda self: fields.Date.context_today(self))
    final_opinion = fields.Selection([
        ('unmodified', 'Unmodified'),
        ('qualified', 'Qualified'),
        ('adverse', 'Adverse'),
        ('disclaimer', 'Disclaimer'),
    ], string='Final Opinion', required=True, default='unmodified')
    manager_signed_user_id = fields.Many2one('res.users', string='Manager Sign-off', tracking=True, copy=False, readonly=True)
    manager_signed_on = fields.Datetime(string='Manager Signed On', tracking=True, copy=False, readonly=True)
    partner_signed_user_id = fields.Many2one('res.users', string='Partner Sign-off', tracking=True, copy=False, readonly=True)
    partner_signed_on = fields.Datetime(string='Partner Signed On', tracking=True, copy=False, readonly=True)
    final_locked_on = fields.Datetime(string='File Locked On', tracking=True, copy=False, readonly=True)

    @api.depends('audit_id', 'client_id')
    def _compute_name(self):
        for record in self:
            if record.client_id:
                record.name = f"FINAL-{record.client_id.name}" if record.audit_id else f"Finalisation - {record.client_id.name}"
            else:
                record.name = 'Finalisation Phase'

    @api.depends('audit_id')
    def _compute_related_phases(self):
        planning_model = self.env['qaco.planning.phase']
        execution_model = self.env['qaco.execution.phase']
        for record in self:
            planning = execution = False
            if record.audit_id:
                planning = planning_model.search([('audit_id', '=', record.audit_id.id)], limit=1)
                execution = execution_model.search([('audit_id', '=', record.audit_id.id)], limit=1)
            record.planning_phase_id = planning.id if planning else False
            record.execution_phase_id = execution.id if execution else False

    @api.depends('planning_phase_id.overall_materiality', 'planning_phase_id.performance_materiality')
    def _compute_materiality_refs(self):
        for record in self:
            record.overall_materiality_ref = record.planning_phase_id.overall_materiality if record.planning_phase_id else 0.0
            record.performance_materiality_ref = record.planning_phase_id.performance_materiality if record.planning_phase_id else 0.0

    def _determine_status(self, completed: bool, started: bool) -> str:
        if completed:
            return 'green'
        if started:
            return 'amber'
        return 'red'

    def _build_dashboard_summary(self) -> str:
        status_labels = dict(SUBTAB_STATUS)
        status_rows = [
            (_('Misstatements'), self.misstatement_status),
            (_('Subsequent Events'), self.subsequent_status),
            (_('Going Concern'), self.going_concern_status),
            (_('Related Parties'), self.related_party_status),
            (_('Representations'), self.representation_status),
            (_('Analytics'), self.analytics_status),
            (_('Completion'), self.completion_status),
        ]
        human = lambda code: status_labels.get(code, _('n/a'))
        items = ''.join(f"<li><b>{label}:</b> {human(state)}</li>" for label, state in status_rows)
        regulatory_snippet = self.regulatory_news or _('<p>No regulator updates recorded.</p>')
        return ''.join([
            f"<p><b>{_('Status Snapshot')}</b></p>",
            f"<ul>{items}</ul>",
            f"<p><b>{_('Regulatory Feed')}</b></p>",
            regulatory_snippet,
        ])

    @api.depends(
        'misstatement_line_ids',
        'misstatement_summary_attachment_ids',
        'misstatement_support_attachment_ids',
        'misstatement_correspondence_attachment_ids',
        'checklist_misstatement_evaluated',
        'checklist_cumulative_below_materiality',
        'checklist_qualitative_considered',
        'checklist_disclosures_reassessed',
        'subsequent_procedure_ids',
        'subsequent_event_ids.resolved',
        'subsequent_checklist_attachment_ids',
        'checklist_sub_events_period_covered',
        'checklist_sub_events_adjusting',
        'checklist_sub_events_disclosure',
        'going_concern_scenario_ids',
        'going_concern_covenant_ids',
        'going_concern_assessment_attachment_ids',
        'going_concern_memo_attachment_ids',
        'checklist_gc_assessment_challenged',
        'checklist_gc_future_info_considered',
        'checklist_gc_basis_appropriate',
        'checklist_gc_reporting_impact',
        'related_party_line_ids',
        'non_compliance_log_ids',
        'related_party_register_attachment_ids',
        'related_party_minutes_attachment_ids',
        'noncompliance_summary_attachment_ids',
        'checklist_related_complete',
        'checklist_related_authorised',
        'checklist_related_disclosures_ok',
        'checklist_noncompliance_communicated',
        'representation_letter_attachment_ids',
        'representation_letter_signed_on',
        'checklist_rep_obtained',
        'checklist_rep_content_complete',
        'checklist_rep_date_valid',
        'analytics_ratio_ids',
        'analytics_variance_ids',
        'analytics_workbook_attachment_ids',
        'analytics_conclusion_attachment_ids',
        'checklist_analytics_corrob',
        'checklist_variances_resolved',
        'checklist_fs_compliant',
        'review_note_ids.state',
        'completion_certificate_attachment_ids',
        'checklist_review_notes_cleared',
        'checklist_compliance_scan',
        'checklist_partner_approval',
        'checklist_archive_ready',
        'compliance_scan_passed',
        'final_file_locked',
        'partner_signed_user_id'
    )
    def _compute_submodule_statuses(self):
        for record in self:
            misstatement_started = bool(
                record.misstatement_line_ids or record.misstatement_summary_attachment_ids or record.misstatement_support_attachment_ids
            )
            misstatement_complete = bool(record.misstatement_summary_attachment_ids) and bool(record.misstatement_support_attachment_ids) and all([
                record.checklist_misstatement_evaluated,
                record.checklist_cumulative_below_materiality,
                record.checklist_qualitative_considered,
                record.checklist_disclosures_reassessed,
            ])
            mis_status = record._determine_status(misstatement_complete, misstatement_started)

            events_all_resolved = all(record.subsequent_event_ids.mapped('resolved')) if record.subsequent_event_ids else True
            subseq_started = bool(
                record.subsequent_procedure_ids or record.subsequent_event_ids or record.subsequent_checklist_attachment_ids
            )
            subseq_complete = bool(record.subsequent_checklist_attachment_ids) and events_all_resolved and all([
                record.checklist_sub_events_period_covered,
                record.checklist_sub_events_adjusting,
                record.checklist_sub_events_disclosure,
            ])
            subseq_status = record._determine_status(subseq_complete, subseq_started)

            gc_started = bool(
                record.going_concern_scenario_ids or record.going_concern_covenant_ids or
                record.going_concern_assessment_attachment_ids or record.going_concern_memo_attachment_ids
            )
            gc_complete = bool(record.going_concern_assessment_attachment_ids) and bool(record.going_concern_memo_attachment_ids) and all([
                record.checklist_gc_assessment_challenged,
                record.checklist_gc_future_info_considered,
                record.checklist_gc_basis_appropriate,
                record.checklist_gc_reporting_impact,
            ])
            gc_status = record._determine_status(gc_complete, gc_started)

            related_started = bool(
                record.related_party_line_ids or record.non_compliance_log_ids or record.related_party_register_attachment_ids
            )
            related_complete = bool(record.related_party_register_attachment_ids) and all([
                record.checklist_related_complete,
                record.checklist_related_authorised,
                record.checklist_related_disclosures_ok,
                record.checklist_noncompliance_communicated,
            ])
            related_status = record._determine_status(related_complete, related_started)

            rep_started = bool(record.representation_letter_attachment_ids or record.representation_letter_signed_on)
            rep_complete = bool(record.representation_letter_attachment_ids) and all([
                record.checklist_rep_obtained,
                record.checklist_rep_content_complete,
                record.checklist_rep_date_valid,
            ])
            rep_status = record._determine_status(rep_complete, rep_started)

            analytics_started = bool(
                record.analytics_ratio_ids or record.analytics_variance_ids or record.analytics_workbook_attachment_ids
            )
            analytics_complete = bool(record.analytics_workbook_attachment_ids) and bool(record.analytics_conclusion_attachment_ids) and all([
                record.checklist_analytics_corrob,
                record.checklist_variances_resolved,
                record.checklist_fs_compliant,
            ])
            analytics_status = record._determine_status(analytics_complete, analytics_started)

            pending_review_notes = record.review_note_ids.filtered(lambda n: n.state != 'resolved')
            completion_started = any([
                mis_status == 'green',
                subseq_status == 'green',
                gc_status == 'green',
                related_status == 'green',
                rep_status == 'green',
                analytics_status == 'green',
                record.completion_certificate_attachment_ids,
                record.partner_signed_user_id,
            ])
            completion_complete = all([
                mis_status == 'green',
                subseq_status == 'green',
                gc_status == 'green',
                related_status == 'green',
                rep_status == 'green',
                analytics_status == 'green',
                record.compliance_scan_passed,
                record.checklist_review_notes_cleared,
                record.checklist_compliance_scan,
                record.checklist_partner_approval,
                record.checklist_archive_ready,
                not pending_review_notes,
                bool(record.completion_certificate_attachment_ids),
                record.final_file_locked,
            ])
            completion_status = record._determine_status(completion_complete, completion_started)

            record.misstatement_status = mis_status
            record.subsequent_status = subseq_status
            record.going_concern_status = gc_status
            record.related_party_status = related_status
            record.representation_status = rep_status
            record.analytics_status = analytics_status
            record.completion_status = completion_status

    @api.depends('misstatement_line_ids.amount', 'misstatement_line_ids.status')
    def _compute_misstatement_totals(self):
        for record in self:
            corrected = sum(line.amount for line in record.misstatement_line_ids.filtered(lambda l: l.status == 'corrected'))
            uncorrected = sum(line.amount for line in record.misstatement_line_ids.filtered(lambda l: l.status == 'uncorrected'))
            record.corrected_total = corrected
            record.uncorrected_total = uncorrected

    @api.depends('uncorrected_total', 'overall_materiality_ref', 'misstatement_threshold_percent')
    def _compute_threshold_breach(self):
        for record in self:
            threshold = (record.overall_materiality_ref or 0.0) * (record.misstatement_threshold_percent / 100.0)
            record.threshold_breached = bool(threshold and record.uncorrected_total > threshold)

    @api.depends(
        'regulatory_alert_ids.summary',
        'regulatory_alert_ids.reference_code',
        'regulatory_alert_ids.severity',
        'regulatory_alert_ids.effective_date',
        'regulatory_alert_ids.regulator'
    )
    def _compute_regulatory_feed(self):
        color_map = {
            'info': '#0d6efd',
            'warning': '#ffc107',
            'critical': '#dc3545',
        }
        for record in self:
            alerts = record.regulatory_alert_ids.sorted(lambda a: a.create_date or fields.Datetime.now(), reverse=True)[:5]
            if not alerts:
                record.regulatory_news = _('<p>No regulator updates recorded.</p>')
                continue
            rows = []
            for alert in alerts:
                color = color_map.get(alert.severity or 'info', '#0d6efd')
                date_label = alert.effective_date or (alert.create_date.date() if alert.create_date else False)
                date_text = fields.Date.to_string(date_label) if date_label else ''
                reference = f"{alert.reference_code}: " if alert.reference_code else ''
                link = f" <a href='{alert.link_url}' target='_blank'>{_('read')}</a>" if alert.link_url else ''
                rows.append(
                    f"<div class='o_qaco-reg-alert' style='margin-bottom:4px;'>"
                    f"<span style='color:{color};font-weight:600'>{alert.regulator.upper()}</span> "
                    f"<span>{reference}{alert.summary}</span>"
                    f" <span style='color:#6c757d;'>({date_text})</span>"
                    f"{link}"
                    f"</div>"
                )
            record.regulatory_news = ''.join(rows)

    @api.depends(
        'final_opinion',
        'going_concern_conclusion',
        'audit_report_date',
        'client_id.name',
        'regulatory_alert_ids.reference_code',
        'regulatory_alert_ids.summary'
    )
    def _compute_representation_template(self):
        for record in self:
            client_name = record.client_id.name or _('the Client')
            date_ref = record.audit_report_date or fields.Date.context_today(record)
            date_text = fields.Date.to_string(date_ref)

            conclusion_map = {
                'no_uncertainty': _('We confirm there are no events or conditions that may cast significant doubt on the entity\'s ability to continue as a going concern.'),
                'material_uncertainty': _('We have disclosed all material uncertainties related to events or conditions that may cast significant doubt on the entity\'s ability to continue as a going concern.'),
                'not_going_concern': _('We have prepared the financial statements on an alternative basis as the entity is not a going concern.'),
            }
            going_concern_clause = conclusion_map.get(record.going_concern_conclusion, conclusion_map['no_uncertainty'])

            alert_highlights = record.regulatory_alert_ids.sorted(lambda a: a.create_date or fields.Datetime.now(), reverse=True)[:3]
            regulator_section = ''
            if alert_highlights:
                bullet_items = ''.join(
                    f"<li>{alert.reference_code or _('Update')}: {alert.summary}</li>" for alert in alert_highlights
                )
                regulator_section = _('<p>We confirm consideration of the following regulator communications:</p><ul>%s</ul>') % bullet_items

            template = f"""
                <p>Date: {date_text}</p>
                <p>To the auditors of {client_name},</p>
                <p>This letter accompanies the issuance of an <strong>{record.final_opinion.title()}</strong> opinion on the financial statements.</p>
                <p>• We acknowledge our responsibility for the fair presentation of the financial statements in accordance with the applicable financial reporting framework.</p>
                <p>• We confirm that we have disclosed all known instances of fraud, suspected fraud, and non-compliance with laws and regulations that could impact the financial statements.</p>
                <p>• {going_concern_clause}</p>
                <p>• Subsequent events up to the audit report date have been evaluated and appropriately adjusted or disclosed.</p>
                <p>• All related party relationships and transactions have been recorded and disclosed.</p>
                <p>• We have communicated the qualitative and quantitative evaluation of uncorrected misstatements and confirm our view that they do not individually or cumulatively result in material misstatement.</p>
                {regulator_section}
                <p>Signed on behalf of management,</p>
            """
            record.representation_letter_template = template

    @api.depends(
        'misstatement_status', 'subsequent_status', 'going_concern_status',
        'related_party_status', 'representation_status', 'analytics_status',
        'checklist_misstatement_evaluated', 'checklist_cumulative_below_materiality',
        'checklist_sub_events_period_covered', 'checklist_gc_assessment_challenged',
        'checklist_related_complete', 'checklist_rep_obtained', 'checklist_analytics_corrob'
    )
    def _compute_signoff_unlock(self):
        for record in self:
            statuses_ready = all([
                record.misstatement_status == 'green',
                record.subsequent_status == 'green',
                record.going_concern_status == 'green',
                record.related_party_status == 'green',
                record.representation_status == 'green',
                record.analytics_status == 'green',
            ])
            checklist_ready = all([
                record.checklist_misstatement_evaluated,
                record.checklist_cumulative_below_materiality,
                record.checklist_sub_events_period_covered,
                record.checklist_gc_assessment_challenged,
                record.checklist_related_complete,
                record.checklist_rep_obtained,
                record.checklist_analytics_corrob,
            ])
            record.signoff_unlocked = statuses_ready and checklist_ready

    @api.depends('going_concern_conclusion')
    def _compute_emphasis_of_matter(self):
        for record in self:
            record.emphasis_matter_required = record.going_concern_conclusion in ('material_uncertainty', 'not_going_concern')

    def _ensure_threshold_controls(self):
        for record in self:
            if record.threshold_breached:
                missing = []
                if not record.pervasiveness_memo:
                    missing.append(_('pervasiveness memo'))
                if not record.partner_override_note:
                    missing.append(_('partner override memo'))
                if missing:
                    raise UserError(_('Threshold exceeded. Provide: %s') % ', '.join(missing))

    def _collect_compliance_findings(self):
        findings = []
        if not self.misstatement_summary_attachment_ids:
            findings.append(_('Upload the final summary of uncorrected misstatements.'))
        if not self.misstatement_support_attachment_ids:
            findings.append(_('Attach detailed misstatement workings.'))
        if not self.subsequent_checklist_attachment_ids:
            findings.append(_('Subsequent events checklist is missing.'))
        if not self.going_concern_assessment_attachment_ids:
            findings.append(_('Management going concern assessment not attached.'))
        if not self.related_party_register_attachment_ids:
            findings.append(_('Final related party register not attached.'))
        if not self.representation_letter_attachment_ids:
            findings.append(_('Signed management representation letter is mandatory.'))
        if not self.analytics_workbook_attachment_ids:
            findings.append(_('Upload the final analytical review workbook.'))
        if not self.completion_certificate_attachment_ids:
            findings.append(_('File completion checklist must be attached.'))
        if self.review_note_ids.filtered(lambda n: n.state != 'resolved'):
            findings.append(_('All review notes must be resolved.'))
        return findings

    def action_run_compliance_scan(self):
        for record in self:
            findings = record._collect_compliance_findings()
            record.compliance_scan_passed = not findings
            record.checklist_compliance_scan = record.compliance_scan_passed
            if findings:
                record.compliance_scan_log = '<br/>'.join(f"• {finding}" for finding in findings)
                raise UserError(_('Compliance scan failed. Resolve findings to proceed.'))
            record.compliance_scan_log = _('<p style="color:green;">All compliance gates passed.</p>')
            record.message_post(body=_('Compliance scan completed with zero findings.'))

    def action_sync_misstatements(self):
        for record in self:
            if not record.execution_phase_id:
                raise UserError(_('Link an execution phase to sync misstatements.'))
            procedures = record.execution_phase_id.substantive_area_ids.mapped('procedure_ids')
            existing_lines = {
                (line.source_reference, line.source_model): line for line in record.misstatement_line_ids if line.source_reference and line.source_model
            }
            created = 0
            updated = 0
            for procedure in procedures.filtered(lambda p: p.result == 'exception'):
                key = (f'procedure:{procedure.id}', 'qaco.exec.substantive.procedure')
                amount = procedure.exception_amount or 0.0
                rationale = procedure.exception_note or _('Exception noted in substantive procedure.')
                area_code = procedure.area_id.area_code
                assertion = procedure.assertion_type or 'existence'

                line = existing_lines.get(key)
                if line:
                    vals = {}
                    if line.amount != amount:
                        vals['amount'] = amount
                    if line.rationale != rationale:
                        vals['rationale'] = rationale
                    if line.area != area_code:
                        vals['area'] = area_code
                    if line.assertion != assertion:
                        vals['assertion'] = assertion
                    if vals:
                        line.write(vals)
                        updated += 1
                    continue

                self.env['qaco.final.misstatement'].create({
                    'finalisation_phase_id': record.id,
                    'area': area_code,
                    'assertion': assertion,
                    'misstatement_type': 'factual',
                    'status': 'uncorrected',
                    'amount': amount,
                    'rationale': rationale,
                    'source_reference': key[0],
                    'source_model': key[1],
                })
                created += 1

            if created or updated:
                parts = []
                if created:
                    parts.append(_('created %s') % created)
                if updated:
                    parts.append(_('updated %s') % updated)
                record.message_post(body=_('Misstatement register refreshed (%s).') % ', '.join(parts))
            else:
                record.message_post(body=_('No new execution exceptions found to sync.'))

    def action_run_readiness_check(self):
        for record in self:
            record.action_run_compliance_scan()
            summary = record._build_dashboard_summary()
            record.message_post(body=_('Readiness check completed.<br/>%s') % summary)

    def action_manager_sign(self):
        self.ensure_one()
        self._ensure_threshold_controls()
        self.manager_signed_user_id = self.env.user
        self.manager_signed_on = fields.Datetime.now()
        self.message_post(body=_('Manager sign-off recorded by %s.') % self.env.user.name)

    def action_partner_sign(self):
        self.ensure_one()
        if not self.manager_signed_user_id:
            raise UserError(_('Manager must sign before partner.'))
        if not self.signoff_unlocked:
            raise UserError(_('Complete all sub-modules before partner sign-off.'))
        if not self.compliance_scan_passed:
            raise UserError(_('Run and pass the compliance scan before final approval.'))
        self.partner_signed_user_id = self.env.user
        self.partner_signed_on = fields.Datetime.now()
        self.checklist_partner_approval = True
        self.message_post(body=_('Partner sign-off recorded by %s.') % self.env.user.name)

    def action_lock_final_file(self):
        self.ensure_one()
        if not self.partner_signed_user_id:
            raise UserError(_('Partner sign-off is required before locking the file.'))
        if self.review_note_ids.filtered(lambda n: n.state != 'resolved'):
            raise UserError(_('Resolve all review notes before locking.'))
        if not self.compliance_scan_passed:
            raise UserError(_('Compliance scan must pass before locking the file.'))
        self.final_file_locked = True
        self.final_locked_on = fields.Datetime.now()
        self.archive_deadline_date = self.audit_report_date + timedelta(days=60) if self.audit_report_date else False
        self.checklist_archive_ready = True
        self.message_post(body=_('File locked and archive timer started. Deadline: %s') % (self.archive_deadline_date or _('N/A')))

    def action_trigger_archive_alert(self):
        self.ensure_one()
        if not self.archive_deadline_date:
            raise UserError(_('Archive deadline date not set. Lock the file first.'))
        today = fields.Date.context_today(self)
        days_left = (self.archive_deadline_date - today).days
        if days_left < 0:
            raise UserError(_('Archive deadline already passed. Escalate to administrator.'))
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            user_id=self.env.user.id,
            note=_('Archive the audit file within %s day(s).') % days_left,
            summary=_('Pending archive - Finalisation Phase'),
            date_deadline=self.archive_deadline_date,
        )


class FinalMisstatement(models.Model):
    _name = 'qaco.final.misstatement'
    _description = 'Finalisation Misstatement Register'
    _order = 'is_significant desc, amount desc'

    finalisation_phase_id = fields.Many2one('qaco.finalisation.phase', string='Finalisation Phase', required=True, ondelete='cascade')
    area = fields.Selection([
        ('revenue', 'Revenue'),
        ('purchases', 'Purchases'),
        ('inventory', 'Inventory'),
        ('ppe', 'Property, Plant & Equipment'),
        ('cash', 'Cash & Bank'),
        ('investments', 'Investments'),
        ('payroll', 'Payroll'),
        ('taxation', 'Taxation'),
        ('financial_statement', 'Financial Statements'),
        ('other', 'Other'),
    ], string='Area', required=True)
    assertion = fields.Selection(ASSERTION_TYPES, string='Assertion', required=True)
    misstatement_type = fields.Selection(MISSTATEMENT_TYPES, string='Type', required=True)
    status = fields.Selection(MISSTATEMENT_STATUS, string='Status', required=True, default='uncorrected')
    amount = fields.Monetary(string='Amount', currency_field='company_currency_id', required=True)
    rationale = fields.Text(string='Rationale / Non-correction Justification', required=True)
    source_reference = fields.Char(string='Source Reference')
    source_model = fields.Char(string='Source Model')
    impact_notes = fields.Text(string='Impact on FS / Disclosures')
    management_response = fields.Text(string='Management Response')
    is_significant = fields.Boolean(string='Significant Misstatement')
    attachments_ids = fields.Many2many(
        'ir.attachment', 'qaco_final_misstatement_line_rel', 'misstatement_id', 'attachment_id', string='Supporting Attachments'
    )
    company_currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    @api.constrains('amount')
    def _check_amount_positive(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError(_('Misstatement amount must be greater than zero.'))


class FinalSubsequentProcedure(models.Model):
    _name = 'qaco.final.subsequent.procedure'
    _description = 'Subsequent Events Procedure (ISA 560)'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    finalisation_phase_id = fields.Many2one('qaco.finalisation.phase', required=True, ondelete='cascade')
    procedure_code = fields.Selection(PROCEDURE_CODES, string='Procedure', required=True)
    description = fields.Char(string='Description')
    performed_by = fields.Many2one('res.users', string='Performed By')
    performed_on = fields.Date(string='Performed On')
    status = fields.Selection(SUBTAB_STATUS, string='Status', default='amber')
    notes = fields.Text(string='Observations')
    attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_final_sub_proc_rel', 'procedure_id', 'attachment_id', string='Evidence'
    )


class FinalSubsequentEvent(models.Model):
    _name = 'qaco.final.subsequent.event'
    _description = 'Subsequent Event Register'

    finalisation_phase_id = fields.Many2one('qaco.finalisation.phase', required=True, ondelete='cascade')
    name = fields.Char(string='Event', required=True)
    event_date = fields.Date(string='Event Date', required=True)
    classification = fields.Selection(EVENT_CLASSIFICATION, string='Classification', required=True)
    financial_effect = fields.Text(string='Financial Effect / Disclosure')
    resolved = fields.Boolean(string='Resolved in FS')
    attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_final_sub_event_rel', 'event_id', 'attachment_id', string='Supporting Documents'
    )


class FinalGoingConcernScenario(models.Model):
    _name = 'qaco.final.gc.scenario'
    _description = 'Going Concern Scenario Analysis'

    finalisation_phase_id = fields.Many2one('qaco.finalisation.phase', required=True, ondelete='cascade')
    name = fields.Char(string='Scenario', required=True)
    revenue_growth = fields.Float(string='Revenue Growth %')
    gross_margin = fields.Float(string='Gross Margin %')
    interest_rate = fields.Float(string='Interest Rate %')
    liquidity_buffer_months = fields.Float(string='Liquidity Buffer (Months)')
    outcome_summary = fields.Html(string='Outcome Summary')
    indicates_failure = fields.Boolean(string='Indicates Going Concern Failure')


class FinalGoingConcernCovenant(models.Model):
    _name = 'qaco.final.gc.covenant'
    _description = 'Going Concern Covenant Calculator'

    finalisation_phase_id = fields.Many2one('qaco.finalisation.phase', required=True, ondelete='cascade')
    covenant_name = fields.Char(string='Covenant', required=True)
    ratio_required = fields.Float(string='Required Threshold')
    ratio_actual = fields.Float(string='Actual Ratio')
    result = fields.Selection([
        ('compliant', 'Compliant'),
        ('breach', 'Breach'),
    ], string='Result', compute='_compute_result', store=True)
    breach_note = fields.Text(string='Breach Commentary')

    @api.depends('ratio_required', 'ratio_actual')
    def _compute_result(self):
        for record in self:
            if not record.ratio_required:
                record.result = False
                continue
            record.result = 'compliant' if record.ratio_actual >= record.ratio_required else 'breach'


class FinalRelatedPartyLine(models.Model):
    _name = 'qaco.final.related.party'
    _description = 'Final Related Party Register'

    finalisation_phase_id = fields.Many2one('qaco.finalisation.phase', required=True, ondelete='cascade')
    party_name = fields.Char(string='Party', required=True)
    relationship = fields.Char(string='Relationship', required=True)
    transaction_nature = fields.Char(string='Nature of Transaction', required=True)
    balance_amount = fields.Monetary(string='Balance Amount', currency_field='company_currency_id')
    disclosure_reference = fields.Char(string='Disclosure Note Reference')
    authorised = fields.Boolean(string='Approved by TCWG')
    documentation_attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_final_related_line_rel', 'line_id', 'attachment_id', string='Supporting Docs'
    )
    company_currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)


class FinalNonComplianceLog(models.Model):
    _name = 'qaco.final.noncompliance'
    _description = 'Non-compliance with Laws & Regulations'

    finalisation_phase_id = fields.Many2one('qaco.finalisation.phase', required=True, ondelete='cascade')
    description = fields.Text(string='Description', required=True)
    law_reference = fields.Char(string='Law / Regulation')
    severity = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Severity', default='medium')
    financial_impact = fields.Monetary(string='Financial Impact', currency_field='company_currency_id')
    reporting_obligation = fields.Text(string='Reporting Obligation')
    communicated_tcwg = fields.Boolean(string='Communicated to TCWG')
    attachment_ids = fields.Many2many(
        'ir.attachment', 'qaco_final_noncompliance_rel', 'noncompliance_id', 'attachment_id', string='Evidence'
    )
    company_currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)


class FinalAnalyticsRatio(models.Model):
    _name = 'qaco.final.analytics.ratio'
    _description = 'Final Analytical Ratio'

    finalisation_phase_id = fields.Many2one('qaco.finalisation.phase', required=True, ondelete='cascade')
    metric = fields.Char(string='Metric', required=True)
    current_value = fields.Float(string='Current Period', required=True)
    prior_value = fields.Float(string='Prior Period')
    expectation_value = fields.Float(string='Planning Expectation')
    variance_percent = fields.Float(string='Variance %', compute='_compute_variance', store=True)
    explanation = fields.Text(string='Explanation / Corroboration')
    resolved = fields.Boolean(string='Variance Resolved')

    @api.depends('current_value', 'prior_value')
    def _compute_variance(self):
        for record in self:
            base = record.prior_value or 0.0
            if base:
                record.variance_percent = ((record.current_value - base) / base) * 100.0
            else:
                record.variance_percent = 0.0


class FinalAnalyticsVariance(models.Model):
    _name = 'qaco.final.analytics.variance'
    _description = 'Variance Flag'

    finalisation_phase_id = fields.Many2one('qaco.finalisation.phase', required=True, ondelete='cascade')
    description = fields.Char(string='Variance / Unusual Relationship', required=True)
    threshold_trigger = fields.Selection([
        ('gt_10', '>10% movement'),
        ('gt_materiality', '>Materiality'),
        ('qualitative', 'Qualitative driver'),
    ], string='Trigger', required=True)
    resolution_comment = fields.Text(string='Resolution Comment')
    resolved = fields.Boolean(string='Resolved', default=False)


class FinalReviewNote(models.Model):
    _name = 'qaco.final.review.note'
    _description = 'Finalisation Review Note'
    _inherit = ['mail.thread']

    finalisation_phase_id = fields.Many2one('qaco.finalisation.phase', required=True, ondelete='cascade')
    description = fields.Text(string='Review Note', required=True)
    assigned_to = fields.Many2one('res.users', string='Assigned To')
    due_date = fields.Date(string='Due Date')
    state = fields.Selection(REVIEW_NOTE_STATES, string='Status', default='open', tracking=True)
    resolution_reference = fields.Char(string='Resolution Reference')


class FinalRegulatoryAlert(models.Model):
    _name = 'qaco.final.regulatory.alert'
    _description = 'Regulatory Update Hub'

    finalisation_phase_id = fields.Many2one('qaco.finalisation.phase', required=True, ondelete='cascade')
    regulator = fields.Selection(REGULATOR_CHOICES, string='Regulator', required=True)
    reference_code = fields.Char(string='Reference / Circular #', required=True)
    summary = fields.Char(string='Summary', required=True)
    link_url = fields.Char(string='Reference URL')
    severity = fields.Selection(ALERT_SEVERITY, string='Severity', default='info')
    effective_date = fields.Date(string='Effective Date')
