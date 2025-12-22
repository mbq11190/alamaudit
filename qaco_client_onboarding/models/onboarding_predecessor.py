# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
import base64
import io

# PDF merging libraries: prefer pypdf (modern), fall back to PyPDF2
try:
    from pypdf import PdfMerger
except Exception:
    try:
        from PyPDF2 import PdfFileMerger as PdfMerger
    except Exception:
        PdfMerger = None

_logger = logging.getLogger(__name__)

RESPONSE_STATUS = [
    ('response_received', 'Response received'),
    ('no_response', 'No response after follow-ups'),
    ('not_applicable', 'Not applicable'),
]

FOLLOWUP_MODE = [
    ('email', 'Email'),
    ('courier', 'Courier'),
    ('hand', 'Hand delivery'),
    ('portal', 'Portal'),
    ('phone', 'Phone'),
]

CONCLUSION = [
    ('proceed', 'Proceed'),
    ('proceed_safeguards', 'Proceed with safeguards'),
    ('do_not_proceed', 'Do Not Proceed'),
]

IMPACT = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
]


class PredecessorRequest(models.Model):
    _name = 'qaco.onboarding.predecessor.request'
    _description = 'Predecessor clearance request record'

    onboarding_id = fields.Many2one('qaco.client.onboarding', required=True, ondelete='cascade', index=True)
    predecessor_firm = fields.Char(string='Predecessor firm')
    predecessor_partner = fields.Char(string='Predecessor partner')
    predecessor_email = fields.Char(string='Email')
    predecessor_phone = fields.Char(string='Phone')
    predecessor_address = fields.Text(string='Address')
    regulatory_ref = fields.Char(string='Regulatory reference')

    engagement_type = fields.Selection([('audit','Audit'),('review','Review'),('other','Other')], string='Engagement type')
    reporting_period = fields.Date(string='Reporting period')
    proposed_appointment_date = fields.Date(string='Proposed appointment date')
    reason_for_change = fields.Text(string='Reason for change of auditor')

    client_authorization = fields.Boolean(string='Client authorization obtained')
    authorization_attachment = fields.Many2one('ir.attachment', string='Authorization doc')

    sent_date = fields.Datetime(string='Request sent date')
    sent_mode = fields.Selection(FOLLOWUP_MODE, string='Mode')
    sent_by = fields.Many2one('res.users', string='Sent by')

    followup_line_ids = fields.One2many('qaco.onboarding.predecessor.followup', 'request_id', string='Follow-up attempts')
    response_id = fields.Many2one('qaco.onboarding.predecessor.response', string='Response')
    final_status = fields.Selection(RESPONSE_STATUS, string='Final status')
    final_conclusion = fields.Selection(CONCLUSION, string='Final conclusion')

    checklist_professional_reasons = fields.Boolean(string='Professional reasons not to accept?')
    checklist_disagreements = fields.Boolean(string='Disagreements with management?')
    checklist_scope_limitations = fields.Boolean(string='Scope limitations?')
    checklist_integrity_concerns = fields.Boolean(string='Integrity/ethics concerns?')
    checklist_outstanding_fees = fields.Boolean(string='Outstanding fees?')
    checklist_access_papers = fields.Boolean(string='Access to prior working papers requested')

    followup_count = fields.Integer(string='Follow-up attempts', compute='_compute_followup_count', store=True)

    @api.depends('followup_line_ids')
    def _compute_followup_count(self):
        for rec in self:
            rec.followup_count = len(rec.followup_line_ids)

    def action_generate_pack_bundle(self):
        """Generate the Clearance Correspondence Pack and merge small PDF attachments into a single bundle.

        Returns the created `ir.attachment` record for the merged bundle.
        Behavior:
        - Render the base pack PDF
        - Collect attachments related to the request and response
        - Only include attachments with mimetype 'application/pdf' and size <= threshold (KB)
        - Merge using pypdf/PyPDF2 PdfMerger; fallback to base pack only if merger missing
        """
        self.ensure_one()
        # Render base pack PDF
        report = self.env.ref('qaco_client_onboarding.report_predecessor_clearance_pack')
        try:
            pdf_base = report._render_qweb_pdf([self.id])[0]
        except Exception:
            # Fallback: try older API
            pdf_base = report.render_qweb_pdf([self.id])
        # Collect attachments
        threshold_kb = int(self.env['ir.config_parameter'].sudo().get_param('qaco_client_onboarding.pack_attachment_max_kb', default='512'))
        threshold_bytes = threshold_kb * 1024
        candidates = []
        # Authorization doc on request
        if self.authorization_attachment and self.authorization_attachment.mimetype == 'application/pdf':
            candidates.append(self.authorization_attachment)
        # Response attachment
        if self.response_id and self.response_id.attachment_id and self.response_id.attachment_id.mimetype == 'application/pdf':
            candidates.append(self.response_id.attachment_id)
        # Other attachments explicitly linked to this request
        other_attachments = self.env['ir.attachment'].search([('res_model', '=', 'qaco.onboarding.predecessor.request'), ('res_id', '=', self.id)])
        for att in other_attachments:
            if att.mimetype == 'application/pdf' and att not in candidates:
                candidates.append(att)
        # Filter by size
        to_merge = [a for a in candidates if (a.file_size or 0) <= threshold_bytes]
        skipped = [a for a in candidates if a not in to_merge]
        # Merge
        if PdfMerger:
            merger = PdfMerger()
            # Append base pack first
            merger.append(io.BytesIO(pdf_base))
            for att in to_merge:
                try:
                    data = base64.b64decode(att.datas or att.db_datas or '')
                    merger.append(io.BytesIO(data))
                except Exception as e:
                    _logger.exception('Failed to append attachment %s: %s', att.name, e)
            outbuf = io.BytesIO()
            try:
                merger.write(outbuf)
                merged_bytes = outbuf.getvalue()
            finally:
                try:
                    merger.close()
                except Exception:
                    pass
        else:
            # No merging library available; create bundle with base pack only
            _logger.warning('No PDF merger library available (pypdf/PyPDF2); creating pack with base document only.')
            merged_bytes = pdf_base
        # Create attachment record
        merged_name = 'clearance_pack_bundle_%s.pdf' % (self.id,)
        merged_att = self.env['ir.attachment'].create({
            'name': merged_name,
            'type': 'binary',
            'datas': base64.b64encode(merged_bytes).decode('ascii'),
            'res_model': 'qaco.onboarding.predecessor.request',
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })
        # For informational tracking, attach a note listing skipped attachments
        if skipped:
            notes = '\n'.join(['Skipped (size>threshold or non-PDF): %s' % (a.name,) for a in skipped])
            merged_att.write({'description': notes})
        # Attach merged bundle into the predecessor folder if available
        try:
            onboarding = self.onboarding_id
            folder = onboarding.get_folder_by_code('04_Predecessor')
            if folder:
                self.env['qaco.onboarding.document'].create({
                    'onboarding_id': onboarding.id,
                    'name': merged_name,
                    'file': base64.b64encode(merged_bytes).decode('ascii'),
                    'file_name': merged_name,
                    'state': 'final',
                    'folder_id': folder.id,
                })
        except Exception:
            _logger.exception('Failed to index merged predecessor pack into folder for request %s', self.id)
        return merged_att

class PredecessorFollowup(models.Model):
    _name = 'qaco.onboarding.predecessor.followup'
    _description = 'Predecessor follow-up attempt'

    onboarding_id = fields.Many2one('qaco.client.onboarding', required=True, ondelete='cascade', index=True)
    request_id = fields.Many2one('qaco.onboarding.predecessor.request', required=True, ondelete='cascade')
    attempt_number = fields.Integer(string='Attempt #')
    date = fields.Datetime(string='Date')
    mode = fields.Selection(FOLLOWUP_MODE, string='Mode')
    outcome = fields.Char(string='Outcome')
    notes = fields.Text(string='Notes')


class PredecessorResponse(models.Model):
    _name = 'qaco.onboarding.predecessor.response'
    _description = 'Predecessor response / issues log'

    onboarding_id = fields.Many2one('qaco.client.onboarding', required=True, ondelete='cascade', index=True)
    request_id = fields.Many2one('qaco.onboarding.predecessor.request', required=True, ondelete='cascade')
    response_received = fields.Boolean(string='Response received')
    response_date = fields.Date(string='Response date')
    response_summary = fields.Text(string='Response summary')
    attachment_id = fields.Many2one('ir.attachment', string='Attachment')

    issue_fee_dispute = fields.Boolean(string='Fee dispute / unpaid fees')
    issue_integrity = fields.Boolean(string='Management integrity concerns')
    issue_disagreements = fields.Boolean(string='Disagreements on accounting policies')
    issue_scope_limit = fields.Boolean(string='Scope limitation / access restriction')
    issue_going_concern = fields.Boolean(string='Going concern concerns')
    issue_related_party = fields.Boolean(string='Related parties / fraud indicators')
    issue_noclar = fields.Boolean(string='NOCLAR indicators')
    other_issue = fields.Text(string='Other issue')

    impact = fields.Selection(IMPACT, string='Impact')
    required_safeguards = fields.Text(string='Required safeguards')
    conclusion = fields.Selection(CONCLUSION, string='Conclusion')

    partner_signoff = fields.Many2one('res.users', string='Partner sign-off')
    partner_signoff_date = fields.Date(string='Partner sign-off date')
    quality_approval = fields.Many2one('res.users', string='Quality/Compliance approver')
    quality_approval_date = fields.Date(string='Quality approval date')

    def is_adverse(self):
        # Adverse if any serious flags or conclusion is do_not_proceed
        return bool(self.issue_integrity or self.issue_scope_limit or self.issue_fee_dispute or self.conclusion == 'do_not_proceed')


# Methods on qaco.client.onboarding to enforce gates
class ClientOnboardingPredecessor(models.Model):
    _inherit = 'qaco.client.onboarding'

    predecessor_request_ids = fields.One2many('qaco.onboarding.predecessor.request', 'onboarding_id', string='Predecessor requests')
    predecessor_response_ids = fields.One2many('qaco.onboarding.predecessor.response', 'onboarding_id', string='Predecessor responses')
    predecessor_escalated = fields.Boolean(string='Predecessor Escalated', compute='_compute_predecessor_escalated', store=True)
    predecessor_locked = fields.Boolean(string='Predecessor locked (Do Not Proceed)', default=False)

    @api.depends('predecessor_response_ids')
    def _compute_predecessor_escalated(self):
        for rec in self:
            rec.predecessor_escalated = any(r.is_adverse() for r in rec.predecessor_response_ids)
            rec.predecessor_locked = any(r.conclusion == 'do_not_proceed' for r in rec.predecessor_response_ids)

    def _check_predecessor_before_approval(self):
        """Enforce predecessor clearance gate before partner approval."""
        for rec in self:
            # If no predecessor firm recorded, treat as Not Applicable
            if not rec.predecessor_auditor_name:
                continue
            # There must be at least one request
            if not rec.predecessor_request_ids:
                raise ValidationError(_('A predecessor clearance request must be issued when a predecessor exists.'))
            # Either response received or >=1 followup attempts documented
            req = rec.predecessor_request_ids[-1]
            has_response = bool(req.response_id and req.response_id.response_received)
            has_followups = req.followup_count and req.followup_count > 0
            if not (has_response or has_followups):
                raise ValidationError(_('A predecessor response or follow-up attempts must be recorded before partner approval.'))
            # If there's an adverse response, escalate and block unless Quality approved
            if rec.predecessor_escalated and not any(r.quality_approval for r in rec.predecessor_response_ids if r.is_adverse()):
                raise ValidationError(_('Adverse predecessor response requires Quality/Compliance approval before partner approval.'))
            # If any response concluded "Do Not Proceed", block approval
            if rec.predecessor_locked:
                raise ValidationError(_('The predecessor response concluded "Do Not Proceed"; engagement creation/acceptance is blocked.'))

    def action_check_predecessor_before_approval(self):
        for rec in self:
            rec._check_predecessor_before_approval()

    def action_generate_predecessor_pack_bundle(self):
        """Convenience button on onboarding: generate pack bundle for the latest predecessor request and open the resulting attachment."""
        self.ensure_one()
        if not self.predecessor_request_ids:
            raise ValidationError(_('No predecessor request exists to generate a pack from.'))
        req = self.predecessor_request_ids[-1]
        att = req.action_generate_pack_bundle()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'res_id': att.id,
            'view_mode': 'form',
            'target': 'current',
        }
