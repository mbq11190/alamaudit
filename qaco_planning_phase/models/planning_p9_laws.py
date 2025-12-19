# -*- coding: utf-8 -*-
"""
P-9: Laws & Regulations (Compliance Risk Assessment)
ISA 250/315/330/240/570/220/ISQM-1/Companies Act 2017/ICAP QCR/AOB
Court-defensible, fully integrated with planning workflow.
"""
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)

# =============================
# Parent Model: Laws & Regulations Assessment
# =============================
class AuditPlanningP9LawsRegulations(models.Model):
    _name = 'audit.planning.p9.laws_regulations'
    _description = 'P-9: Laws & Regulations (Compliance Risk Assessment)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    engagement_id = fields.Many2one('qaco.audit', string='Audit Engagement', required=True, ondelete='cascade', index=True, tracking=True)
    audit_year = fields.Many2one('qaco.audit.year', string='Audit Year', required=True, ondelete='cascade', index=True)
    partner_id = fields.Many2one('res.users', string='Engagement Partner', required=True)
    planning_main_id = fields.Many2one('qaco.planning.main', string='Planning Phase', ondelete='cascade', index=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('prepared', 'Prepared'),
        ('reviewed', 'Reviewed'),
        ('locked', 'Locked'),
    ], string='Status', default='draft', tracking=True, copy=False)
    compliance_line_ids = fields.One2many('audit.planning.p9.compliance_line', 'laws_regulations_id', string='Compliance Lines', required=True)
    # Section A: Identification of Applicable Laws & Regulations
    law_companies_act = fields.Boolean(string='Companies Act, 2017')
    law_income_tax = fields.Boolean(string='Income Tax Ordinance, 2001')
    law_sales_tax = fields.Boolean(string='Sales Tax Act / Federal Excise Act')
    law_zakat = fields.Boolean(string='Zakat & Ushr Ordinance, 1980')
    law_secp = fields.Boolean(string='SECP Regulations / SBP Prudential Regulations')
    law_sector_specific = fields.Char(string='Sector-specific Laws')
    law_ngo_donor = fields.Boolean(string='NGO / Donor Regulations')
    law_foreign = fields.Boolean(string='Foreign Regulations')
    all_laws_identified = fields.Boolean(string='All relevant laws identified?')
    industry_regulations_covered = fields.Boolean(string='Industry-specific regulations covered?')
    # Section C: Regulatory Authorities & Oversight
    regulator_id = fields.Many2one('res.partner', string='Primary Regulator')
    inspection_frequency = fields.Char(string='Frequency of Inspections')
    last_inspection_date = fields.Date(string='Last Inspection Date')
    last_inspection_findings = fields.Text(string='Findings from Last Inspection')
    outstanding_regulatory_matters = fields.Boolean(string='Outstanding Regulatory Matters?')
    oversight_understood = fields.Boolean(string='Oversight understood?')
    prior_findings_considered = fields.Boolean(string='Prior findings considered?')
    # Section D: Compliance History & Known Non-Compliance
    known_non_compliance = fields.Boolean(string='Known Instances of Non-Compliance?')
    non_compliance_nature = fields.Text(string='Nature of Non-Compliance')
    non_compliance_periods = fields.Char(string='Period(s) Affected')
    non_compliance_status = fields.Selection([
        ('resolved', 'Resolved'),
        ('ongoing', 'Ongoing'),
        ('disputed', 'Disputed'),
    ], string='Status')
    non_compliance_impact = fields.Char(string='Financial Impact (Actual/Potential)')
    # Section F: Fraud & Illegal Acts Consideration
    illegal_acts_indicators = fields.Boolean(string='Indicators of Illegal Acts Identified?')
    mgmt_involvement_suspected = fields.Boolean(string='Management Involvement Suspected?')
    whistleblower_complaints = fields.Boolean(string='Whistleblower Complaints / Media Reports?')
    fraud_risk_impact = fields.Text(string='Impact on Fraud Risk Assessment')
    # Section G: Management Representations & Inquiries
    mgmt_representations_obtained = fields.Boolean(string='Management Representations Obtained?')
    inquiry_results_summary = fields.Text(string='Inquiry Results Summary')
    contradictions_identified = fields.Boolean(string='Contradictions Identified?')
    legal_counsel_needed = fields.Boolean(string='Need for Legal Counsel Involvement?')
    inquiries_documented = fields.Boolean(string='Inquiries documented?')
    responses_evaluated = fields.Boolean(string='Responses evaluated?')
    # Section H: Audit Responses to Compliance Risks
    planned_substantive_testing = fields.Boolean(string='Planned Substantive Testing?')
    planned_legal_confirmations = fields.Boolean(string='Planned Legal Confirmations?')
    planned_regulatory_review = fields.Boolean(string='Planned Regulatory Correspondence Review?')
    response_nature_timing_extent = fields.Text(string='Nature, Timing, Extent')
    specialist_involvement = fields.Boolean(string='Specialist Involvement Required?')
    # Section I: Impact on Going Concern & Reporting
    non_compliance_impacts_gc = fields.Boolean(string='Non-compliance Impacts GC?')
    disclosure_required = fields.Boolean(string='Disclosure Required?')
    reporting_modification = fields.Boolean(string='Possible Reporting Modification?')
    gc_reporting_basis = fields.Text(string='Basis for Conclusion')
    # Section J: Mandatory Document Uploads
    attachment_ids = fields.Many2many('ir.attachment', 'audit_p9_laws_attachment_rel', 'laws_id', 'attachment_id', string='Required Attachments', help='Statutory filings, regulatory correspondence, legal opinions, compliance letters, mgmt rep drafts')
    mandatory_upload_check = fields.Boolean(string='Mandatory uploads present?')
    # Section K: Conclusion & Professional Judgment
    conclusion_narrative = fields.Text(string='Conclusion Narrative', required=True, default="Relevant laws and regulations applicable to the entity have been identified and considered in accordance with ISA 250. Risks of material non-compliance have been assessed, and appropriate audit responses and reporting implications have been determined.")
    laws_considered = fields.Boolean(string='Laws & regulations adequately considered?')
    compliance_risks_assessed = fields.Boolean(string='Compliance risks assessed and linked?')
    audit_response_basis = fields.Boolean(string='Basis established for audit responses?')
    # Section L: Review, Approval & Lock
    prepared_by = fields.Many2one('res.users', string='Prepared By')
    prepared_by_role = fields.Char(string='Prepared By Role')
    prepared_date = fields.Datetime(string='Prepared Date')
    reviewed_by = fields.Many2one('res.users', string='Reviewed By')
    review_notes = fields.Text(string='Review Notes')
    partner_approved = fields.Boolean(string='Partner Approved?')
    partner_comments = fields.Text(string='Partner Comments (Mandatory)')
    locked = fields.Boolean(string='Locked', compute='_compute_locked', store=True)
    # Outputs
    laws_memo_pdf = fields.Binary(string='Laws & Regulations Compliance Assessment Memorandum (PDF)')
    compliance_risk_register = fields.Binary(string='Compliance Risk Register')
    # Audit trail
    version_history = fields.Text(string='Version History')
    reviewer_timestamps = fields.Text(string='Reviewer Timestamps')

    @api.depends('partner_approved')
    def _compute_locked(self):
        for rec in self:
            rec.locked = bool(rec.partner_approved)

    def action_prepare(self):
        self.state = 'prepared'
        self.prepared_by = self.env.user.id
        self.prepared_by_role = self.env.user.groups_id.mapped('name')
        self.prepared_date = fields.Datetime.now()
        self.message_post(body="P-9 prepared.")

    def action_review(self):
        self.state = 'reviewed'
        self.reviewed_by = self.env.user.id
        self.message_post(body="P-9 reviewed.")

    def action_partner_approve(self):
        if not self.partner_comments:
            raise ValidationError("Partner comments are mandatory for approval.")
        self.state = 'locked'
        self.partner_approved = True
        self.message_post(body="P-9 partner approved and locked.")

    @api.constrains('attachment_ids')
    def _check_mandatory_uploads(self):
        for rec in self:
            if not rec.attachment_ids:
                raise ValidationError("Mandatory compliance assessment documents must be uploaded.")

    @api.constrains('compliance_line_ids')
    def _check_compliance_lines(self):
        for rec in self:
            if not rec.compliance_line_ids:
                raise ValidationError("At least one compliance line must be entered.")

    # Pre-conditions enforcement
    @api.model
    def create(self, vals):
        planning = self.env['qaco.planning.main'].browse(vals.get('planning_main_id'))
        if not planning or not planning.p8_partner_locked:
            raise UserError("P-9 cannot be started until P-8 is partner-approved and locked.")
        if not planning.p6_finalized or not planning.p2_completed:
            raise UserError("P-9 requires finalized P-6 and completed P-2.")
        return super().create(vals)

# =============================
# Child Model: Compliance Line
# =============================
class AuditPlanningP9ComplianceLine(models.Model):
    _name = 'audit.planning.p9.compliance_line'
    _description = 'P-9: Compliance Line'
    _order = 'id desc'

    laws_regulations_id = fields.Many2one('audit.planning.p9.laws_regulations', string='Laws & Regulations Assessment', required=True, ondelete='cascade', index=True)
    law = fields.Char(string='Law / Regulation', required=True)
    direct_effect = fields.Boolean(string='Direct Effect on FS?')
    indirect_effect = fields.Boolean(string='Indirect Effect?')
    effect_basis = fields.Text(string='Basis')
    area_affected = fields.Char(string='Area Affected')
    nature_of_risk = fields.Text(string='Nature of Risk')
    likelihood = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Likelihood')
    impact = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Impact')
    compliance_risk_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Compliance Risk Level')
    # Audit trail
    change_log = fields.Text(string='Change Log')
    version_history = fields.Text(string='Version History')
    reviewer_timestamps = fields.Text(string='Reviewer Timestamps')

    def write(self, vals):
        self.message_post(body=f"Compliance line updated: {vals}")
        return super().write(vals)

    def unlink(self):
        self.message_post(body="Compliance line deleted.")
        return super().unlink()
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
