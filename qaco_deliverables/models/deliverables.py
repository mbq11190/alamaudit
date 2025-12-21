"""Deliverables workflow module for final audit phase."""

# -*- coding: utf-8 -*-

from typing import Any, List, TYPE_CHECKING

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError  # type: ignore[attr-defined]


SUBTAB_STATUS = [
    ('red', '❌ Incomplete'),
    ('amber', '🟡 In Progress'),
    ('green', '✅ Ready'),
]

OPINION_TYPES = [
    ('unmodified', 'Unmodified'),
    ('qualified', 'Qualified'),
    ('adverse', 'Adverse'),
    ('disclaimer', 'Disclaimer'),
]

ENTITY_TYPES = [
    ('listed', 'Listed Company'),
    ('non_listed', 'Non-listed Company'),
    ('psc', 'Public Sector Company'),
    ('welfare', 'Welfare Entity / NPO'),
    ('modaraba', 'Modaraba'),
    ('insurance', 'Insurance'),
    ('bank', 'Bank / DFIs'),
    ('broker', 'Securities Broker'),
    ('other', 'Other'),
]

FRAMEWORK_TYPES = [
    ('ifrs', 'IFRS'),
    ('ifrs_sme', 'IFRS for SMEs'),
    ('afrs_sse', 'AFRS for SSEs'),
    ('local', 'Local GAAP / Companies Act'),
    ('cash', 'Cash Basis'),
    ('contract', 'Contract Basis'),
    ('regulatory', 'Regulatory Framework'),
]

REPORT_TEMPLATE_TYPES = [
    ('form_35a', 'Form 35A - Companies Act'),
    ('form_35b', 'Form 35B - Foreign Bank Branches'),
    ('form_35c', 'Form 35C - Consolidated FS'),
    ('isa_700_listed', 'ISA 700 - Listed Entity'),
    ('isa_700_non_listed', 'ISA 700 - Non-listed Entity'),
    ('isa_705_qualified', 'ISA 705 - Qualified Opinion'),
    ('isa_705_adverse', 'ISA 705 - Adverse Opinion'),
    ('isa_705_disclaimer', 'ISA 705 - Disclaimer'),
    ('icap_circular', 'ICAP Circular Template'),
    ('insurance_life', 'Life Insurance Report'),
    ('insurance_non_life', 'Non-Life Insurance Report'),
    ('modaraba', 'Modaraba Report'),
    ('broker_net_capital', 'Broker - Net Capital Balance'),
    ('broker_liquid_capital', 'Broker - Liquid Capital'),
    ('broker_internal_control', 'Broker - Internal Control'),
    ('csr_assurance', 'CSR/Sustainability Assurance'),
    ('compliance_licensing', 'Licensing Conditions Compliance'),
    ('free_float', 'Free Float Certificate'),
]

DEFICIENCY_CLASSIFICATION = [
    ('significant', 'Significant Deficiency'),
    ('other', 'Other Deficiency'),
]

SEVERITY_SCALE = [
    ('high', 'High'),
    ('medium', 'Medium'),
    ('low', 'Low'),
]

OTHER_INFO_STATUS = [
    ('not_received', 'Not Received'),
    ('under_review', 'Received - Under Review'),
    ('cleared', 'Reviewed - No Misstatement'),
    ('misstatement', 'Reviewed - Material Misstatement'),
]

DISPATCH_METHODS = [
    ('email', 'Email'),
    ('courier', 'Courier / Hard Copy'),
    ('portal', 'SECP / PSX Portal'),
    ('in_person', 'In Person'),
]


class Deliverables(models.Model):
    _name = 'qaco.deliverables'
    _description = 'Deliverables'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    if TYPE_CHECKING:
        def message_post(self, *args: Any, **kwargs: Any) -> Any: ...

    _sql_constraints = [
        ('unique_audit', 'unique(audit_id)', 'Deliverables already exist for this audit.'),
    ]

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    audit_id = fields.Many2one('qaco.audit', string='Audit', required=True, ondelete='cascade')
    client_id = fields.Many2one('res.partner', string='Client', related='audit_id.client_id', readonly=True, store=False)
    firm_name = fields.Many2one('audit.firm.name', string='Firm Name', related='audit_id.firm_name', readonly=True, store=False)
    finalisation_phase_id = fields.Many2one('qaco.finalisation.phase', string='Finalisation Phase', compute='_compute_related_phase', store=True, readonly=True)

    central_status = fields.Selection(SUBTAB_STATUS, compute='_compute_section_statuses', store=True, tracking=True)
    audit_report_status = fields.Selection(SUBTAB_STATUS, compute='_compute_section_statuses', store=True, tracking=True)
    management_letter_status = fields.Selection(SUBTAB_STATUS, compute='_compute_section_statuses', store=True, tracking=True)
    tcwg_status = fields.Selection(SUBTAB_STATUS, compute='_compute_section_statuses', store=True, tracking=True)
    other_info_status = fields.Selection(SUBTAB_STATUS, compute='_compute_section_statuses', store=True, tracking=True)
    dispatch_status = fields.Selection(SUBTAB_STATUS, compute='_compute_section_statuses', store=True, tracking=True)
    ready_for_dispatch = fields.Boolean(string='Ready for Dispatch', compute='_compute_ready', store=True)
    deliverables_locked = fields.Boolean(string='Deliverables Locked', tracking=True, copy=False)
    outstanding_items_log = fields.Html(string='Pre-Issuance Findings', copy=False)

    final_partner_id = fields.Many2one('res.users', string='Final Sign-off Partner', tracking=True, domain=[('share', '=', False)])
    final_manager_id = fields.Many2one('res.users', string='Final Sign-off Manager', tracking=True, domain=[('share', '=', False)])
    review_notes_cleared = fields.Boolean(string='All review notes cleared', tracking=True)
    final_fs_received = fields.Boolean(string='Final FS received & locked', tracking=True)
    final_fs_attachment_ids = fields.Many2many('ir.attachment', 'qaco_deliverables_fs_rel', 'deliverables_id', 'attachment_id', string='Final FS PDFs')
    eqcr_required = fields.Boolean(string='EQCR Required', tracking=True)
    eqcr_completed = fields.Boolean(string='EQCR Completed', tracking=True)
    eqcr_reviewer_id = fields.Many2one('res.users', string='EQCR Reviewer', tracking=True, domain=[('share', '=', False)])
    eqcr_signed_on = fields.Datetime(string='EQCR Signed On', tracking=True)
    independence_confirmed = fields.Boolean(string='Independence confirmed for team', tracking=True)
    independence_note = fields.Text(string='Independence confirmation notes')
    completion_checklist_signed = fields.Boolean(string='Completion checklist signed', tracking=True)
    audit_completion_scan_passed = fields.Boolean(string='Audit completion checklist 100% signed off', tracking=True)
    cold_review_completed = fields.Boolean(string='Cold Review Completed', tracking=True)
    technical_review_completed = fields.Boolean(string='Technical Review Completed', tracking=True)

    audit_report_ids = fields.One2many('qaco.deliverable.audit.report', 'deliverables_id', string='Auditor Reports')

    deficiency_ids = fields.One2many('qaco.deliverable.deficiency', 'deliverables_id', string='Deficiency Log')
    management_letter_attachment_ids = fields.Many2many('ir.attachment', 'qaco_deliverables_ml_rel', 'deliverables_id', 'attachment_id', string='Final Management Letter')
    management_response_attachment_ids = fields.Many2many('ir.attachment', 'qaco_deliverables_ml_resp_rel', 'deliverables_id', 'attachment_id', string='Management Response Form')
    management_letter_sent_date = fields.Date(string='Management Letter Sent Date')
    management_response_received_date = fields.Date(string='Management Response Received Date')

    tcwg_attachment_ids = fields.Many2many('ir.attachment', 'qaco_deliverables_tcwgl_rel', 'deliverables_id', 'attachment_id', string='TCWG Deck / Letter')
    tcwg_ack_attachment_ids = fields.Many2many('ir.attachment', 'qaco_deliverables_tcwga_rel', 'deliverables_id', 'attachment_id', string='Acknowledged Minutes')
    tcwg_meeting_date = fields.Date(string='TCWG Communication Date', tracking=True)
    tcwg_attendees = fields.Char(string='TCWG Attendees')
    tcwg_auditor_attendees = fields.Char(string='Audit Team Attendees')
    tcwg_topic_responsibilities = fields.Boolean(string='Auditor responsibility explained', tracking=True)
    tcwg_topic_significant_findings = fields.Boolean(string='Significant findings communicated', tracking=True)
    tcwg_topic_uncorrected = fields.Boolean(string='Uncorrected misstatements shared', tracking=True)
    tcwg_topic_scope = fields.Boolean(string='Scope & timing discussed', tracking=True)
    tcwg_topic_independence = fields.Boolean(string='Independence confirmation given', tracking=True)
    tcwg_topic_qualitative = fields.Boolean(string='Qualitative aspects discussed', tracking=True)
    tcwg_topic_going_concern = fields.Boolean(string='Going concern assessment discussed', tracking=True)
    tcwg_topic_related_parties = fields.Boolean(string='Related party transactions discussed', tracking=True)
    tcwg_communication_method = fields.Selection([
        ('meeting', 'In-Person Meeting'),
        ('virtual', 'Virtual Meeting'),
        ('written', 'Written Communication'),
        ('mixed', 'Mixed Methods'),
    ], string='Communication Method', default='meeting')

    other_info_line_ids = fields.One2many('qaco.deliverable.other.info', 'deliverables_id', string='Other Information Register')
    other_info_attachment_ids = fields.Many2many('ir.attachment', 'qaco_deliverables_other_rel', 'deliverables_id', 'attachment_id', string='Other Information Evidence')
    other_info_review_completed = fields.Boolean(string='Other Information Review Completed', tracking=True)
    other_info_misstatement_count = fields.Integer(string='Material Misstatements Found', compute='_compute_misstatement_count', store=True)

    dispatch_log_ids = fields.One2many('qaco.deliverable.dispatch', 'deliverables_id', string='Dispatch Log')
    deliverable_pack_attachment_ids = fields.Many2many('ir.attachment', 'qaco_deliverables_pack_rel', 'deliverables_id', 'attachment_id', string='Final Deliverables Pack')
    archive_confirmed = fields.Boolean(string='Archive confirmation logged', tracking=True)
    archive_date = fields.Datetime(string='Archive Date')
    archive_notes = fields.Text(string='Archive Notes')

    fs_consistency_check = fields.Boolean(string='FS Consistency Check Passed', tracking=True)
    regulatory_filing_required = fields.Boolean(string='Regulatory Filing Required', tracking=True)
    regulatory_filing_completed = fields.Boolean(string='Regulatory Filing Completed', tracking=True)
    zakat_deduction_verified = fields.Boolean(string='Zakat Deduction Verified', tracking=True)
    secp_portal_filing_date = fields.Date(string='SECP Portal Filing Date')
    psx_portal_filing_date = fields.Date(string='PSX Portal Filing Date')

    @api.depends('audit_id', 'client_id')
    def _compute_name(self):
        for record in self:
            if record.client_id:
                record.name = _('Deliverables - %s') % record.client_id.name
            else:
                record.name = _('Deliverables')

    @api.depends('audit_id')
    def _compute_related_phase(self):
        final_model = self.env['qaco.finalisation.phase']
        for record in self:
            finalisation = final_model.search([('audit_id', '=', record.audit_id.id)], limit=1)
            record.finalisation_phase_id = finalisation.id if finalisation else False

    @api.depends('other_info_line_ids.status')
    def _compute_misstatement_count(self):
        for record in self:
            record.other_info_misstatement_count = len(record.other_info_line_ids.filtered(lambda line: line.status == 'misstatement'))

    def _determine_status(self, completed: bool, started: bool) -> str:
        if completed:
            return 'green'
        if started:
            return 'amber'
        return 'red'

    @api.depends(
        'review_notes_cleared', 'final_fs_received', 'final_fs_attachment_ids',
        'eqcr_required', 'eqcr_completed', 'eqcr_reviewer_id', 'independence_confirmed',
        'completion_checklist_signed', 'audit_completion_scan_passed', 'cold_review_completed',
        'technical_review_completed', 'final_partner_id', 'final_manager_id',
        'audit_report_ids', 'audit_report_ids.readiness_flag',
        'deficiency_ids', 'management_letter_attachment_ids', 'management_response_attachment_ids',
        'management_letter_sent_date', 'management_response_received_date',
        'tcwg_topic_responsibilities', 'tcwg_topic_significant_findings', 'tcwg_topic_uncorrected',
        'tcwg_topic_scope', 'tcwg_topic_independence', 'tcwg_topic_qualitative',
        'tcwg_topic_going_concern', 'tcwg_topic_related_parties', 'tcwg_attachment_ids',
        'tcwg_ack_attachment_ids', 'tcwg_meeting_date',
        'other_info_line_ids.status', 'other_info_line_ids.escalated', 'other_info_review_completed',
        'dispatch_log_ids.status', 'deliverable_pack_attachment_ids', 'archive_confirmed',
        'fs_consistency_check', 'regulatory_filing_required', 'regulatory_filing_completed'
    )
    def _compute_section_statuses(self):
        for record in self:
            central_started = any([
                record.review_notes_cleared,
                record.final_fs_received,
                record.final_fs_attachment_ids,
                record.eqcr_completed,
                record.independence_confirmed,
                record.cold_review_completed,
                record.technical_review_completed,
            ])
            central_complete = all([
                record.review_notes_cleared,
                record.final_fs_received,
                bool(record.final_fs_attachment_ids),
                record.independence_confirmed,
                record.completion_checklist_signed,
                record.audit_completion_scan_passed,
                record.cold_review_completed,
                record.technical_review_completed,
                record.final_partner_id,
                record.final_manager_id,
                (not record.eqcr_required) or (record.eqcr_completed and record.eqcr_reviewer_id),
            ])
            record.central_status = record._determine_status(central_complete, central_started)

            audit_started = bool(record.audit_report_ids)
            audit_complete = bool(record.audit_report_ids.filtered('readiness_flag'))
            record.audit_report_status = record._determine_status(audit_complete, audit_started)

            mgmt_started = bool(record.deficiency_ids) or bool(record.management_letter_attachment_ids)
            mgmt_complete = all([
                bool(record.deficiency_ids),
                all(line.recommendation and line.action_owner for line in record.deficiency_ids),
                bool(record.management_letter_attachment_ids),
                record.management_letter_sent_date,
            ])
            record.management_letter_status = record._determine_status(mgmt_complete, mgmt_started)

            tcwg_started = any([
                record.tcwg_attachment_ids,
                record.tcwg_topic_responsibilities,
                record.tcwg_meeting_date,
            ])
            tcwg_complete = all([
                record.tcwg_topic_responsibilities,
                record.tcwg_topic_significant_findings,
                record.tcwg_topic_uncorrected,
                record.tcwg_topic_scope,
                record.tcwg_topic_independence,
                record.tcwg_topic_qualitative,
                record.tcwg_topic_going_concern,
                record.tcwg_topic_related_parties,
                bool(record.tcwg_attachment_ids),
                bool(record.tcwg_ack_attachment_ids),
                record.tcwg_meeting_date,
            ])
            record.tcwg_status = record._determine_status(tcwg_complete, tcwg_started)

            other_started = bool(record.other_info_line_ids) or record.other_info_review_completed
            other_complete = all([
                bool(record.other_info_line_ids),
                all(line.status in ('cleared', 'misstatement') for line in record.other_info_line_ids),
                not record.other_info_line_ids.filtered(lambda line: line.status == 'misstatement' and not line.escalated),
                record.other_info_review_completed,
            ])
            record.other_info_status = record._determine_status(other_complete, other_started)

            dispatch_started = any([
                record.dispatch_log_ids,
                record.deliverable_pack_attachment_ids,
                record.archive_confirmed,
            ])
            dispatch_complete = all([
                bool(record.dispatch_log_ids.filtered(lambda line: line.status in ('dispatched', 'acknowledged'))),
                bool(record.deliverable_pack_attachment_ids),
                record.archive_confirmed,
                record.fs_consistency_check,
                (not record.regulatory_filing_required) or record.regulatory_filing_completed,
            ])
            record.dispatch_status = record._determine_status(dispatch_complete, dispatch_started)

    @api.depends('central_status', 'audit_report_status', 'management_letter_status', 'tcwg_status', 'other_info_status', 'dispatch_status')
    def _compute_ready(self):
        for record in self:
            record.ready_for_dispatch = all([
                record.central_status == 'green',
                record.audit_report_status == 'green',
                record.management_letter_status == 'green',
                record.tcwg_status == 'green',
                record.other_info_status == 'green',
                record.dispatch_status == 'green',
            ])

    def _collect_gateway_findings(self) -> List[str]:
        self.ensure_one()
        findings: List[str] = []
        if not self.review_notes_cleared:
            findings.append(_('Outstanding review notes.'))
        if not self.final_fs_received or not self.final_fs_attachment_ids:
            findings.append(_('Final FS not attached/locked.'))
        if not self.independence_confirmed:
            findings.append(_('Team independence confirmation missing.'))
        if not self.completion_checklist_signed:
            findings.append(_('Completion checklist not signed.'))
        if not self.audit_completion_scan_passed:
            findings.append(_('Audit completion checklist not 100% signed off.'))
        if not self.cold_review_completed:
            findings.append(_('Cold review completion pending.'))
        if not self.technical_review_completed:
            findings.append(_('Technical review completion pending.'))
        if self.eqcr_required and (not self.eqcr_completed or not self.eqcr_reviewer_id):
            findings.append(_('EQCR sign-off pending.'))
        if self.finalisation_phase_id and self.finalisation_phase_id.completion_status != 'green':
            findings.append(_('Finalisation phase not locked.'))
        if not self.final_partner_id or not self.final_manager_id:
            findings.append(_('Assign final partner and manager.'))
        if not self.audit_report_ids.filtered('readiness_flag'):
            findings.append(_('No audit report marked ready.'))
        if not self.deficiency_ids:
            findings.append(_('Management letter deficiencies not logged.'))
        if self.deficiency_ids.filtered(lambda line: not line.recommendation or not line.action_owner):
            findings.append(_('Deficiencies missing recommendations/action owners.'))
        if not self.management_letter_attachment_ids or not self.management_letter_sent_date:
            findings.append(_('Management letter not attached/sent.'))
        if not self.tcwg_attachment_ids or not self.tcwg_ack_attachment_ids:
            findings.append(_('TCWG deck or acknowledgments missing.'))
        if self.other_info_line_ids.filtered(lambda line: line.status not in ('cleared', 'misstatement')):
            findings.append(_('Other information register has pending rows.'))
        if self.other_info_line_ids.filtered(lambda line: line.status == 'misstatement' and not line.escalated):
            findings.append(_('Material misstatements not escalated.'))
        if not self.other_info_review_completed:
            findings.append(_('Other information review completion pending.'))
        if not self.dispatch_log_ids:
            findings.append(_('No dispatch record logged.'))
        if not self.deliverable_pack_attachment_ids:
            findings.append(_('Deliverables pack not attached.'))
        if not self.fs_consistency_check:
            findings.append(_('FS consistency check not completed.'))
        if self.regulatory_filing_required and not self.regulatory_filing_completed:
            findings.append(_('Regulatory filing pending.'))
        if not self.archive_confirmed:
            findings.append(_('Archive confirmation missing.'))
        return findings

    def action_run_gateway_check(self):
        for record in self:
            findings = record._collect_gateway_findings()
            if findings:
                record.outstanding_items_log = '<br/>'.join(f"• {item}" for item in findings)
                raise UserError(_('Pre-issuance gateway blocked. Resolve outstanding items.'))
            record.outstanding_items_log = _('<p style="color:green;">Gateway cleared.</p>')
            record.message_post(body=_('Gateway checklist cleared. All prerequisites satisfied.'))

    def action_validate_deliverables(self):
        for record in self:
            record.action_run_gateway_check()
            blocking: List[str] = []
            if record.audit_report_status != 'green':
                blocking.append(_('Independent auditor report not ready.'))
            if record.management_letter_status != 'green':
                blocking.append(_('Management letter deficiencies incomplete.'))
            if record.tcwg_status != 'green':
                blocking.append(_('TCWG communication pending mandatory topics.'))
            if record.other_info_status != 'green':
                blocking.append(_('Other information register still open.'))
            if record.dispatch_status != 'green':
                blocking.append(_('Dispatch log/archiving incomplete.'))
            if blocking:
                raise UserError('\n'.join(blocking))
            record.message_post(body=_('All deliverables validated. Ready for dispatch.'))

    def action_lock_deliverables(self):
        self.action_validate_deliverables()
        for record in self:
            record.deliverables_locked = True
            record.archive_date = fields.Datetime.now()
            record.message_post(body=_('Deliverables tab locked. Final pack archived.'))

    def action_unlock_deliverables(self):
        for record in self:
            if not record.env.user.has_group('qaco_audit.group_audit_partner'):
                raise UserError(_('Only Audit Partners can unlock deliverables.'))
            record.deliverables_locked = False

    def action_mark_archive_confirmed(self):
        for record in self:
            if not record.deliverables_locked:
                raise UserError(_('Lock deliverables before archiving.'))
            if not record.deliverable_pack_attachment_ids:
                raise UserError(_('Deliverables pack attachment is required to archive.'))
            record.archive_confirmed = True
            record.archive_date = fields.Datetime.now()

    def action_generate_deliverables_pack(self):
        self.ensure_one()
        if not self.deliverable_pack_attachment_ids:
            raise UserError(_('Attach the deliverables pack (signed report, management letter, TCWG minutes) before dispatch.'))
        first_attachment = self.deliverable_pack_attachment_ids[0]
        return {
            'type': 'ir.actions.act_url',
            'name': _('Deliverables Pack'),
            'target': 'new',
            'url': f'/web/content/{first_attachment.id}?download=true',
        }


class DeliverableAuditReport(models.Model):
    _name = 'qaco.deliverable.audit.report'
    _description = 'Independent Auditor Report'
    _order = 'id desc'

    deliverables_id = fields.Many2one('qaco.deliverables', string='Deliverables', required=True, ondelete='cascade')
    client_id = fields.Many2one(related='deliverables_id.client_id', store=False, readonly=True)
    period_end = fields.Date(string='Reporting Period End', required=True)
    framework = fields.Selection(FRAMEWORK_TYPES, string='Framework', required=True)
    opinion_type = fields.Selection(OPINION_TYPES, string='Opinion Type', required=True, default='unmodified')
    entity_type = fields.Selection(ENTITY_TYPES, string='Entity Type', required=True, default='non_listed')
    report_template_type = fields.Selection(REPORT_TEMPLATE_TYPES, string='Template Type', required=True, default='isa_700_non_listed')
    report_version = fields.Char(string='Report Version / Rev')
    report_date = fields.Date(string='Report Date')
    report_location = fields.Char(string='Signing Location')
    report_reference_number = fields.Char(string='Report Reference / Tracking #')
    drn_number = fields.Char(string='Dispatch Ref (DRN)')
    eqcr_reference = fields.Char(string='EQCR Reference')
    regulatory_submission_required = fields.Boolean(string='Regulatory Submission Required')
    regulatory_deadline = fields.Date(string='Regulatory Deadline')
    regulatory_tracking_reference = fields.Char(string='Regulatory Tracking #')
    signing_partner_id = fields.Many2one('res.users', string='Signing Partner', domain=[('share', '=', False)])
    signing_manager_id = fields.Many2one('res.users', string='Signing Director/Manager', domain=[('share', '=', False)])
    kam_required = fields.Boolean(string='KAMs Required', default=False)
    kam_override_reason = fields.Char(string='KAM Override Reason')
    eom_required = fields.Boolean(string='EOM/OM Included')
    eom_reason = fields.Char(string='EOM / OM Reason')
    gc_uncertainty = fields.Boolean(string='GC - Material Uncertainty Exists?')
    gc_disclosure_adequate = fields.Boolean(string='GC Disclosure Adequate')
    basis_text = fields.Html(string='Basis for Opinion Section')
    basis_template = fields.Html(string='Basis Template', compute='_compute_basis_template', sanitize=False)
    template_recommendation = fields.Char(string='Suggested Template', compute='_compute_template', store=True)
    draft_report_attachment_ids = fields.Many2many('ir.attachment', 'qaco_deliverables_report_draft_rel', 'report_id', 'attachment_id', string='Draft Reports w/Comments')
    final_report_attachment_ids = fields.Many2many('ir.attachment', 'qaco_deliverables_report_signed_rel', 'report_id', 'attachment_id', string='Final Signed Reports')
    support_attachment_ids = fields.Many2many('ir.attachment', 'qaco_deliverables_report_support_rel', 'report_id', 'attachment_id', string='Supporting Memos')
    kam_line_ids = fields.One2many('qaco.deliverable.kam', 'audit_report_id', string='KAMs')
    eom_line_ids = fields.One2many('qaco.deliverable.eom', 'audit_report_id', string='EOM/OM')
    readiness_flag = fields.Boolean(string='Ready for Dispatch', compute='_compute_readiness', store=True)

    @api.depends('entity_type', 'framework', 'report_template_type')
    def _compute_template(self):
        template_dict = dict(REPORT_TEMPLATE_TYPES)
        mapping = {
            ('listed', 'ifrs'): 'isa_700_listed',
            ('listed', 'regulatory'): 'form_35a',
            ('bank', 'regulatory'): 'form_35b',
            ('insurance', 'regulatory'): 'insurance_non_life',
            ('broker', 'regulatory'): 'broker_internal_control',
            ('non_listed', 'ifrs'): 'isa_700_non_listed',
        }
        for record in self:
            suggested_key = mapping.get((record.entity_type, record.framework)) or record.report_template_type or ''
            fallback_key = record.report_template_type or ''
            template_value = template_dict.get(suggested_key) or template_dict.get(fallback_key, '')
            record.template_recommendation = template_value

    @api.depends('opinion_type')
    def _compute_basis_template(self):
        template_map = {
            'unmodified': _('<p>We conducted our audit in accordance with International Standards on Auditing...</p>'),
            'qualified': _('<p>Basis for Qualified Opinion...</p>'),
            'adverse': _('<p>Basis for Adverse Opinion...</p>'),
            'disclaimer': _('<p>Basis for Disclaimer of Opinion...</p>'),
        }
        for record in self:
            record.basis_template = template_map.get(record.opinion_type, '')

    @api.depends('final_report_attachment_ids', 'report_date', 'signing_partner_id', 'signing_manager_id', 'opinion_type')
    def _compute_readiness(self):
        for record in self:
            record.readiness_flag = bool(
                record.final_report_attachment_ids
                and record.report_date
                and record.signing_partner_id
                and record.signing_manager_id
                and record.opinion_type
            )

    @api.constrains('kam_required', 'kam_line_ids')
    def _check_kam_requirements(self):
        for record in self:
            if record.kam_required and not record.kam_line_ids:
                raise ValidationError(_('At least one KAM entry is required when KAMs are flagged as required.'))

    @api.constrains('entity_type', 'kam_required')
    def _enforce_listed_kam(self):
        for record in self:
            if record.entity_type == 'listed' and not record.kam_required:
                raise ValidationError(_('KAMs cannot be disabled for listed entities.'))

    @api.constrains('eom_required', 'eom_line_ids')
    def _check_eom_requirements(self):
        for record in self:
            if record.eom_required and not record.eom_line_ids:
                raise ValidationError(_('Provide at least one EOM/OM paragraph when marked as required.'))

    def action_mark_ready(self):
        for record in self:
            if not record.final_report_attachment_ids:
                raise ValidationError(_('Attach the signed report before marking it ready.'))
            if not record.report_date:
                raise ValidationError(_('Specify the report date.'))
            record.readiness_flag = True


class DeliverableKAM(models.Model):
    _name = 'qaco.deliverable.kam'
    _description = 'Key Audit Matter'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    audit_report_id = fields.Many2one('qaco.deliverable.audit.report', string='Audit Report', required=True, ondelete='cascade')
    title = fields.Char(string='KAM Title', required=True)
    risk_reference = fields.Char(string='Risk Reference')
    isa701_reference = fields.Char(string='ISA 701 Reference')
    tcwg_reference = fields.Char(string='TCWG Reference / Minutes')
    wp_reference = fields.Char(string='Workpaper Reference')
    description = fields.Html(string='Why it is a KAM?')
    audit_response = fields.Html(string='Audit Response Summary')
    conclusion = fields.Text(string='Conclusion / Outcome')
    impact_on_fs = fields.Char(string='Impact on FS area')
    ready_for_report = fields.Boolean(string='Ready to include', default=False)
    attachment_ids = fields.Many2many('ir.attachment', 'qaco_deliverables_kam_rel', 'kam_id', 'attachment_id', string='Supporting Evidence')

    @api.constrains('description', 'audit_response')
    def _check_lengths(self):
        for record in self:
            if len((record.description or '').strip()) < 30:
                raise ValidationError(_('Provide sufficient detail in the KAM description.'))
            if len((record.audit_response or '').strip()) < 30:
                raise ValidationError(_('Provide sufficient detail for the audit response.'))


class DeliverableEOM(models.Model):
    _name = 'qaco.deliverable.eom'
    _description = 'Emphasis / Other Matters'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    audit_report_id = fields.Many2one('qaco.deliverable.audit.report', string='Audit Report', required=True, ondelete='cascade')
    type = fields.Selection([
        ('eom', 'Emphasis of Matter'),
        ('om', 'Other Matter'),
        ('kam', 'Linkage with KAM'),
    ], string='Type', required=True, default='eom')
    isa_reference = fields.Char(string='ISA Reference / Law')
    trigger = fields.Char(string='Trigger / Circumstance')
    disclosure_reference = fields.Char(string='Financial Statement Reference')
    narrative = fields.Html(string='Paragraph Narrative')
    include_in_report = fields.Boolean(string='Include in Report', default=True)
    regulator_mandated = fields.Boolean(string='Regulator Mandated')
    ready_for_report = fields.Boolean(string='Ready to include', default=True)


class DeliverableDeficiency(models.Model):
    _name = 'qaco.deliverable.deficiency'
    _description = 'Management Letter Deficiency'
    _order = 'id desc'

    deliverables_id = fields.Many2one('qaco.deliverables', string='Deliverables', required=True, ondelete='cascade')
    reference = fields.Char(string='Reference', readonly=True, copy=False)
    classification = fields.Selection(DEFICIENCY_CLASSIFICATION, string='Classification', required=True, default='significant')
    area = fields.Char(string='Area / Process')
    control_ref = fields.Char(string='Control / WP Reference')
    condition = fields.Text(string='Condition / Issue', required=True)
    criteria = fields.Text(string='Criteria / Benchmark')
    cause = fields.Text(string='Cause / Root Cause')
    effect = fields.Text(string='Effect / Impact')
    recommendation = fields.Text(string='Recommendation / Remediation Plan', required=True)
    management_response = fields.Text(string='Management Response')
    severity = fields.Selection(SEVERITY_SCALE, string='Severity', default='medium')
    action_owner = fields.Char(string='Management Action Owner')
    action_plan = fields.Text(string='Action Plan / Next Steps')
    target_date = fields.Date(string='Target Completion Date')
    follow_up_required = fields.Boolean(string='Follow-up Required')
    follow_up_status = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ], string='Follow-up Status', default='pending')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('shared', 'Shared with Management'),
        ('responded', 'Response Received'),
        ('closed', 'Closed'),
    ], default='draft', string='Status')
    status_notes = fields.Text(string='Status Notes')
    wp_reference = fields.Char(string='WP Ref')
    attachment_ids = fields.Many2many('ir.attachment', 'qaco_deliverables_def_rel', 'deficiency_id', 'attachment_id', string='Evidence')

    @api.model
    def create(self, vals):
        if not vals.get('reference') and vals.get('deliverables_id'):
            deliverable = self.env['qaco.deliverables'].browse(vals['deliverables_id'])
            count = len(deliverable.deficiency_ids) + 1
            vals['reference'] = '%s-DEF-%02d' % (deliverable.audit_id.name or 'AUD', count)
        return super().create(vals)


class DeliverableOtherInformation(models.Model):
    _name = 'qaco.deliverable.other.info'
    _description = 'Other Information Register'
    _order = 'id desc'

    deliverables_id = fields.Many2one('qaco.deliverables', string='Deliverables', required=True, ondelete='cascade')
    document_name = fields.Char(string='Document Name', required=True)
    doc_type = fields.Selection([
        ('ars', 'Annual Report Section'),
        ('chairman', "Chairman's Review"),
        ('ceo', 'CEO Message'),
        ('csr', 'CSR Report'),
        ('marketing', 'Marketing Material'),
        ('other', 'Other'),
    ], default='ars', string='Document Type')
    status = fields.Selection(OTHER_INFO_STATUS, default='not_received', string='Status', tracking=True)
    responsible_person = fields.Char(string='Responsible (Client)')
    received_on = fields.Date(string='Received On')
    review_completed_on = fields.Date(string='Review Completed On')
    reviewer_id = fields.Many2one('res.users', string='Reviewer')
    comments = fields.Text(string='Comments / Notes')
    status_comments = fields.Text(string='Status Comments')
    escalated = fields.Boolean(string='Escalated to Partner')
    escalation_notes = fields.Text(string='Escalation Notes')
    misstatement_communicated = fields.Boolean(string='Misstatement Communicated to Management')
    resolution_reference = fields.Char(string='Resolution Reference / Minutes')
    attachment_ids = fields.Many2many('ir.attachment', 'qaco_deliverables_otherinfo_rel', 'otherinfo_id', 'attachment_id', string='Evidence')


class DeliverableDispatch(models.Model):
    _name = 'qaco.deliverable.dispatch'
    _description = 'Deliverables Dispatch Log'
    _order = 'dispatch_date desc, id desc'

    deliverables_id = fields.Many2one('qaco.deliverables', string='Deliverables', required=True, ondelete='cascade')
    recipient_name = fields.Char(string='Recipient Name', required=True)
    recipient_role = fields.Char(string='Recipient Role / Capacity')
    method = fields.Selection(DISPATCH_METHODS, string='Dispatch Method', required=True)
    dispatch_date = fields.Datetime(string='Dispatch Date/Time', required=True, default=fields.Datetime.now)
    acknowledged_date = fields.Datetime(string='Acknowledged On')
    tracking_reference = fields.Char(string='Tracking Reference / Portal Ack')
    portal_submission_reference = fields.Char(string='Portal Submission ID')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('dispatched', 'Dispatched'),
        ('acknowledged', 'Acknowledged'),
    ], default='draft', string='Status')
    notes = fields.Text(string='Notes / Remarks')
    attachment_ids = fields.Many2many('ir.attachment', 'qaco_deliverables_dispatch_rel', 'dispatch_id', 'attachment_id', string='Proof of Dispatch')
    acknowledgment_attachment_ids = fields.Many2many('ir.attachment', 'qaco_deliverables_dispatch_ack_rel', 'dispatch_id', 'attachment_id', string='Acknowledgment Proof')

    @api.constrains('status', 'acknowledged_date')
    def _check_acknowledgment(self):
        for record in self:
            if record.status == 'acknowledged' and not record.acknowledged_date:
                raise ValidationError(_('Capture the acknowledgment date/time when status is acknowledged.'))



