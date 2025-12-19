# -*- coding: utf-8 -*-
"""
P-9: Laws & Regulations
Standard: ISA 250
Purpose: Identify compliance risks.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError


class PlanningP9Laws(models.Model):
    """P-9: Laws & Regulations (ISA 250)"""
    _name = 'qaco.planning.p9.laws'
    _description = 'P-9: Going Concern – Preliminary Assessment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    TAB_STATE = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
    ]

    state = fields.Selection(
        TAB_STATE,
        string='Status',
        default='not_started',
        tracking=True,
        copy=False,
    )

    name = fields.Char(
        string='Reference',
        compute='_compute_name',
        store=True,
        readonly=True
    )
    audit_id = fields.Many2one(
        'qaco.audit',
        string='Audit Engagement',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True
    )
    planning_main_id = fields.Many2one(
        'qaco.planning.main',
        string='Planning Phase',
        ondelete='cascade',
        index=True
    )
    client_id = fields.Many2one(
        'res.partner',
        string='Client Name',
        related='audit_id.client_id',
        readonly=True,
        store=True
    )

    # ===== Applicable Laws & Regulations =====
    applicable_laws_ids = fields.One2many(
        'qaco.planning.p9.law.line',
        'p9_laws_id',
        string='Applicable Laws & Regulations'
    )
    # XML view compatible alias
    law_line_ids = fields.One2many(
        'qaco.law.line',
        'p9_laws_id',
        string='Laws Register'
    )

    # ===== Overall Assessment (XML compatible) =====
    compliance_assessment = fields.Selection([
        ('compliant', '🟢 Compliant'),
        ('partial', '🟡 Partially Compliant'),
        ('non_compliant', '🔴 Non-Compliant'),
        ('not_assessed', '⚪ Not Yet Assessed'),
    ], string='Overall Compliance Assessment', tracking=True)

    # ===== Category A Laws (Direct Effect on FS) =====
    category_a_laws = fields.Html(
        string='Category A Laws',
        help='Laws with direct effect on determination of amounts and disclosures (ISA 250.6(a))'
    )
    # XML view compatible alias
    direct_effect_laws = fields.Html(
        string='Direct Effect Laws',
        related='category_a_laws',
        readonly=False
    )
    category_a_compliance = fields.Selection([
        ('compliant', '🟢 Compliant'),
        ('partial', '🟡 Partially Compliant'),
        ('non_compliant', '🔴 Non-Compliant'),
        ('not_assessed', '⚪ Not Yet Assessed'),
    ], string='Category A Compliance Status')

    # ===== Category B Laws (Other Laws) =====
    category_b_laws = fields.Html(
        string='Category B Laws',
        help='Other laws where non-compliance may have a material effect (ISA 250.6(b))'
    )
    # XML view compatible alias
    indirect_effect_laws = fields.Html(
        string='Indirect Effect Laws',
        related='category_b_laws',
        readonly=False
    )
    category_b_compliance = fields.Selection([
        ('compliant', '🟢 Compliant'),
        ('partial', '🟡 Partially Compliant'),
        ('non_compliant', '🔴 Non-Compliant'),
        ('not_assessed', '⚪ Not Yet Assessed'),
    ], string='Category B Compliance Status')

    # ===== Pakistan-Specific Regulations =====
    companies_act_applicable = fields.Boolean(string='Companies Act 2017 Applicable', default=True)
    companies_act_compliance = fields.Html(string='Companies Act Compliance Assessment')

    secp_regulations_applicable = fields.Boolean(string='SECP Regulations Applicable')
    secp_compliance = fields.Html(string='SECP Compliance Assessment')

    sbp_regulations_applicable = fields.Boolean(string='SBP Regulations Applicable')
    sbp_compliance = fields.Html(string='SBP Compliance Assessment')

    fbr_compliance_applicable = fields.Boolean(string='FBR/Tax Compliance Applicable', default=True)
    fbr_compliance = fields.Html(string='FBR Compliance Assessment')

    pra_regulations_applicable = fields.Boolean(string='PRA/Provincial Tax Applicable')
    pra_compliance = fields.Html(string='PRA Compliance Assessment')

    # XML view compatible - AOB Requirements
    aob_compliance = fields.Html(string='AOB Requirements Compliance')

    labor_laws_applicable = fields.Boolean(string='Labor Laws Applicable')
    labor_compliance = fields.Html(string='Labor Laws Compliance Assessment')

    environmental_laws_applicable = fields.Boolean(string='Environmental Laws Applicable')
    environmental_compliance = fields.Html(string='Environmental Compliance Assessment')
    # XML view compatible alias
    environmental_regulations = fields.Html(
        string='Environmental Regulations',
        related='environmental_compliance',
        readonly=False
    )

    industry_specific_regulations = fields.Html(string='Industry-Specific Regulations')
    # XML view compatible aliases
    industry_regulations = fields.Html(
        string='Industry Regulations',
        related='industry_specific_regulations',
        readonly=False
    )
    licensing_requirements = fields.Html(
        string='Licensing Requirements',
        help='Licensing requirements applicable to the entity'
    )

    # ===== Compliance Procedures =====
    entity_compliance_framework = fields.Html(
        string='Entity Compliance Framework',
        help='Understanding of entity\'s compliance framework'
    )
    audit_procedures_planned = fields.Html(
        string='Audit Procedures Planned',
        help='Audit procedures planned for compliance assessment'
    )
    inquiries_made = fields.Html(
        string='Inquiries Made',
        help='Inquiries made regarding compliance'
    )
    correspondence_inspection = fields.Html(
        string='Correspondence Inspection',
        help='Inspection of regulatory correspondence'
    )

    # ===== Identified Non-Compliance =====
    non_compliance_identified = fields.Boolean(
        string='Non-Compliance Identified',
        tracking=True
    )
    non_compliance_details = fields.Html(
        string='Non-Compliance Details',
        help='Details of identified or suspected non-compliance'
    )
    non_compliance_impact = fields.Html(
        string='Impact on Financial Statements',
        help='Assessment of impact on FS and audit opinion'
    )
    non_compliance_response = fields.Html(
        string='Audit Response',
        help='Planned audit procedures to address non-compliance'
    )
    # XML view compatible fields
    non_compliance_line_ids = fields.One2many(
        'qaco.non.compliance.line',
        'p9_laws_id',
        string='Non-Compliance Items'
    )
    non_compliance_assessment = fields.Html(
        string='Non-Compliance Assessment',
        help='Overall assessment of non-compliance items'
    )

    # ===== Communication & Reporting =====
    management_communication = fields.Html(
        string='Communication to Management',
        help='Matters to be communicated to management'
    )
    tcwg_communication = fields.Html(
        string='Communication to TCWG',
        help='Matters to be communicated to those charged with governance'
    )
    regulatory_reporting = fields.Boolean(
        string='Regulatory Reporting Required',
        help='Is reporting to regulatory authorities required?'
    )
    regulatory_reporting_details = fields.Html(
        string='Regulatory Reporting Details'
    )
    # XML view compatible aliases
    regulator_reporting = fields.Html(
        string='Reporting to Regulators',
        related='regulatory_reporting_details',
        readonly=False
    )
    audit_report_impact = fields.Html(
        string='Impact on Audit Report',
        help='Assessment of impact on audit report'
    )

    # ===== Attachments =====
    compliance_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p9_compliance_rel',
        'p9_id',
        'attachment_id',
        string='Compliance Documents'
    )
    legal_opinion_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p9_legal_opinion_rel',
        'p9_id',
        'attachment_id',
        string='Legal Opinions'
    )
    # XML view compatible alias
    regulatory_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p9_regulatory_rel',
        'p9_id',
        'attachment_id',
        string='Regulatory Correspondence'
    )

    # ===== Summary =====
    compliance_summary = fields.Html(
        string='Legal & Regulatory Compliance Summary',
        help='Consolidated compliance assessment per ISA 250'
    )
    # XML view compatible alias
    laws_conclusion = fields.Html(
        string='Laws & Regulations Conclusion',
        related='compliance_summary',
        readonly=False
    )
    isa_reference = fields.Char(
        string='ISA Reference',
        default='ISA 250',
        readonly=True
    )

    # ===== Sign-off Fields =====
    senior_signed_user_id = fields.Many2one('res.users', string='Senior Completed By', tracking=True, copy=False, readonly=True)
    senior_signed_on = fields.Datetime(string='Senior Completed On', tracking=True, copy=False, readonly=True)
    manager_reviewed_user_id = fields.Many2one('res.users', string='Manager Reviewed By', tracking=True, copy=False, readonly=True)
    manager_reviewed_on = fields.Datetime(string='Manager Reviewed On', tracking=True, copy=False, readonly=True)
    partner_approved_user_id = fields.Many2one('res.users', string='Partner Approved By', tracking=True, copy=False, readonly=True)
    partner_approved_on = fields.Datetime(string='Partner Approved On', tracking=True, copy=False, readonly=True)
    reviewer_notes = fields.Html(string='Reviewer Notes')
    approval_notes = fields.Html(string='Approval Notes')

    _sql_constraints = [
        ('audit_unique', 'UNIQUE(audit_id)', 'Only one P-9 record per Audit Engagement is allowed.')
    ]

    @api.depends('audit_id', 'client_id')
    def _compute_name(self):
        for record in self:
            if record.client_id:
                record.name = f"P9-{record.client_id.name[:15]}"
            else:
                record.name = 'P-9: Laws & Regulations'

    def _validate_mandatory_fields(self):
        """Validate mandatory fields before completing P-9."""
        self.ensure_one()
        errors = []
        if not self.category_a_compliance:
            errors.append('Category A compliance status must be assessed')
        if not self.compliance_summary:
            errors.append('Compliance summary is required')
        if self.non_compliance_identified and not self.non_compliance_details:
            errors.append('Non-compliance details must be documented')
        if errors:
            raise UserError('Cannot complete P-9. Missing requirements:\n• ' + '\n• '.join(errors))

    def action_start_work(self):
        for record in self:
            if record.state != 'not_started':
                raise UserError('Can only start work on tabs that are Not Started.')
            record.state = 'in_progress'

    def action_complete(self):
        for record in self:
            if record.state != 'in_progress':
                raise UserError('Can only complete tabs that are In Progress.')
            record._validate_mandatory_fields()
            record.senior_signed_user_id = self.env.user
            record.senior_signed_on = fields.Datetime.now()
            record.state = 'completed'

    def action_review(self):
        for record in self:
            if record.state != 'completed':
                raise UserError('Can only review tabs that are Completed.')
            record.manager_reviewed_user_id = self.env.user
            record.manager_reviewed_on = fields.Datetime.now()
            record.state = 'reviewed'

    def action_approve(self):
        for record in self:
            if record.state != 'reviewed':
                raise UserError('Can only approve tabs that have been Reviewed.')
            record.partner_approved_user_id = self.env.user
            record.partner_approved_on = fields.Datetime.now()
            record.state = 'approved'

    def action_send_back(self):
        for record in self:
            if record.state not in ['completed', 'reviewed']:
                raise UserError('Can only send back tabs that are Completed or Reviewed.')
            record.state = 'in_progress'

    def action_unlock(self):
        for record in self:
            if record.state != 'approved':
                raise UserError('Can only unlock Approved tabs.')
            record.partner_approved_user_id = False
            record.partner_approved_on = False
            record.state = 'reviewed'


class PlanningP9LawLine(models.Model):
    """Applicable Law/Regulation Line Item."""
    _name = 'qaco.planning.p9.law.line'
    _description = 'Applicable Law/Regulation'
    _order = 'category, sequence'

    p9_laws_id = fields.Many2one(
        'qaco.planning.p9.laws',
        string='P-9 Laws',
        required=True,
        ondelete='cascade'
    )
    sequence = fields.Integer(string='Sequence', default=10)
    category = fields.Selection([
        ('a', 'Category A - Direct Effect'),
        ('b', 'Category B - Other Laws'),
    ], string='Category', required=True)
    law_name = fields.Char(
        string='Law/Regulation Name',
        required=True
    )
    regulator = fields.Char(
        string='Regulatory Body'
    )
    relevance = fields.Text(
        string='Relevance to Entity',
        help='Why this law is applicable to the entity'
    )
    compliance_status = fields.Selection([
        ('compliant', '🟢 Compliant'),
        ('partial', '🟡 Partially Compliant'),
        ('non_compliant', '🔴 Non-Compliant'),
        ('not_assessed', '⚪ Not Yet Assessed'),
    ], string='Compliance Status', required=True, default='not_assessed')
    assessment_notes = fields.Text(
        string='Assessment Notes'
    )
    audit_procedures = fields.Text(
        string='Planned Audit Procedures'
    )


class LawLine(models.Model):
    """Law Line Item for XML view compatibility."""
    _name = 'qaco.law.line'
    _description = 'Law Line'
    _order = 'law_type, sequence'

    p9_laws_id = fields.Many2one(
        'qaco.planning.p9.laws',
        string='P-9 Laws',
        required=True,
        ondelete='cascade'
    )
    sequence = fields.Integer(string='Sequence', default=10)
    law_name = fields.Char(
        string='Law/Regulation Name',
        required=True
    )
    law_type = fields.Selection([
        ('direct', 'Direct Effect'),
        ('indirect', 'Indirect Effect'),
    ], string='Law Type', required=True, default='direct')
    regulator = fields.Char(
        string='Regulatory Body'
    )
    compliance_status = fields.Selection([
        ('compliant', '🟢 Compliant'),
        ('partial', '🟡 Partially Compliant'),
        ('non_compliant', '🔴 Non-Compliant'),
        ('not_assessed', '⚪ Not Yet Assessed'),
    ], string='Compliance Status', default='not_assessed')
    audit_procedures = fields.Text(
        string='Audit Procedures'
    )
    findings = fields.Text(
        string='Findings'
    )


class NonComplianceLine(models.Model):
    """Non-Compliance Item Line for XML view compatibility."""
    _name = 'qaco.non.compliance.line'
    _description = 'Non-Compliance Item'
    _order = 'sequence'

    p9_laws_id = fields.Many2one(
        'qaco.planning.p9.laws',
        string='P-9 Laws',
        required=True,
        ondelete='cascade'
    )
    sequence = fields.Integer(string='Sequence', default=10)
    law_reference = fields.Char(
        string='Law/Regulation Reference',
        required=True
    )
    description = fields.Text(
        string='Description of Non-Compliance'
    )
    nature = fields.Selection([
        ('actual', 'Actual Non-Compliance'),
        ('suspected', 'Suspected Non-Compliance'),
    ], string='Nature', default='actual')
    materiality = fields.Selection([
        ('material', 'Material'),
        ('immaterial', 'Immaterial'),
        ('to_assess', 'To Be Assessed'),
    ], string='Materiality', default='to_assess')
    action_taken = fields.Text(
        string='Action Taken'
    )
    reporting_impact = fields.Selection([
        ('none', 'No Impact'),
        ('disclosure', 'Disclosure Required'),
        ('qualification', 'Report Qualification'),
        ('adverse', 'Adverse Opinion'),
    ], string='Reporting Impact', default='none')
