from odoo import fields, models, _


class AuditCompletionReview(models.Model):
    _name = 'audit.completion.review'
    _description = 'Audit Completion & Review'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'audit.ai.helper.mixin', 'audit.collaboration.mixin']

    name = fields.Char(default=lambda self: _('Completion Review'), tracking=True)
    subsequent_events_review = fields.Text(tracking=True)
    going_concern_assessment = fields.Text(tracking=True)
    final_analytics = fields.Text(tracking=True)
    misstatement_summary_file = fields.Many2many(
        'ir.attachment',
        'audit_completion_attachment_rel',
        'review_id',
        'attachment_id',
        string='Misstatement Schedules',
    )
    partner_review_notes = fields.Text(tracking=True)
    management_rep_letter_pdf = fields.Binary(string='Management Representation Letter')
    tcwg_report_html = fields.Html(string='TCWG Report')
    assigned_user_ids = fields.Many2many('res.users', string='Assigned Team', tracking=True)

    def ai_generate_management_rep_letter(self):
        for record in self:
            prompt = f"""
                Draft a management representation letter referencing ISA 580 and Pakistan corporate regulations.
                Key Areas: Going concern ({record.going_concern_assessment}), misstatements summary attachments.
            """
            record.partner_review_notes = record._call_openai(prompt)
        return True

    def ai_review_misstatements_materiality(self):
        for record in self:
            prompt = f"""
                Review aggregated misstatements and assess materiality impact.
                Final analytics: {record.final_analytics}
                Subsequent events: {record.subsequent_events_review}
            """
            record.final_analytics = record._call_openai(prompt)
        return True

    def ai_generate_TCWG_report(self):
        for record in self:
            prompt = f"""
                Prepare a governance communication to TCWG referencing ISA 260.
                Include misstatement status, going concern view, and key findings.
            """
            record.tcwg_report_html = record._call_openai(prompt)
        return True
