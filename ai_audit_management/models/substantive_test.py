from odoo import fields, models, _


class AuditSubstantiveTest(models.Model):
    _name = 'audit.substantive.test'
    _description = 'Substantive Procedures'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'audit.ai.helper.mixin', 'audit.collaboration.mixin']

    name = fields.Char(default=lambda self: _('Substantive Test'), tracking=True)
    account_head = fields.Selection([
        ('cash', 'Cash & Bank'),
        ('receivables', 'Trade Receivables'),
        ('inventory', 'Inventory'),
        ('payables', 'Trade Payables'),
        ('revenue', 'Revenue'),
        ('expenses', 'Expenses'),
        ('tax', 'Taxation (FBR)'),
        ('related_party', 'Related Parties'),
    ], required=True, tracking=True)
    procedure_template = fields.Selection([
        ('tax_verification', 'Tax Verification (FBR)'),
        ('bank_confirmation', 'Bank Confirmations'),
        ('related_party_testing', 'Related Party Testing'),
        ('inventory_count', 'Inventory Count Procedures'),
        ('custom', 'Custom'),
    ], default='custom', tracking=True)
    assertion = fields.Selection([
        ('existence', 'Existence'),
        ('completeness', 'Completeness'),
        ('valuation', 'Valuation'),
        ('rights', 'Rights & Obligations'),
    ], required=True, tracking=True)
    test_description = fields.Text(tracking=True)
    sampling_method = fields.Char()
    evidence_document_ids = fields.Many2many(
        'ir.attachment',
        'audit_substantive_evidence_rel',
        'test_id',
        'attachment_id',
        string='Evidence Uploads',
    )
    results = fields.Text()
    conclusion_status = fields.Selection([
        ('draft', 'Draft'),
        ('satisfactory', 'Satisfactory'),
        ('exceptions', 'Exceptions Noted'),
    ], default='draft', tracking=True)
    assigned_user_ids = fields.Many2many('res.users', string='Assigned Team', tracking=True)

    def ai_design_test_of_details(self):
        for record in self:
            prompt = f"""
                Design detailed substantive procedures for {record.account_head} ({record.procedure_template}).
                Assertion: {record.assertion}.
                Provide sampling guidance referencing Pakistan audit practices and ISA 500.
            """
            record.test_description = record._call_openai(prompt)
        return True

    def ai_review_evidence_and_summarize(self):
        for record in self:
            evidence_list = ', '.join(record.evidence_document_ids.mapped('name'))
            prompt = f"""
                Summarize audit evidence for {record.account_head}.
                Documents: {evidence_list}.
                Provide conclusion recommendation.
            """
            record.results = record._call_openai(prompt)
        return True

    def ai_flag_inconsistencies(self):
        for record in self:
            prompt = f"""
                Highlight potential inconsistencies or fraud indicators for {record.account_head}.
                Current Findings: {record.results}
            """
            addition = record._call_openai(prompt)
            existing = record.results or ''
            record.results = ((existing + '\n') if existing else '') + addition
        return True
