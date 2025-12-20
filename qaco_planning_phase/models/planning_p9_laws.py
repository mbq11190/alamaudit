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

    # Sequential Gating (ISA 300/220: Systematic Planning Approach)
    can_open = fields.Boolean(
        string='Can Open This Tab',
        compute='_compute_can_open',
        store=False,
        help='P-9 can only be opened after P-8 is approved'
    )

    @api.depends('audit_id', 'audit_id.id')
    def _compute_can_open(self):
        """P-9 requires P-8 to be approved."""
        for rec in self:
            if not rec.audit_id:
                rec.can_open = False
                continue
            # Find P-8 for this audit
            p8 = self.env['qaco.planning.p8.going.concern'].search([
                ('audit_id', '=', rec.audit_id.id)
            ], limit=1)
            rec.can_open = p8.state == 'approved' if p8 else False

    @api.constrains('state')
    def _check_sequential_gating(self):
        """ISA 300/220: Enforce sequential planning approach."""
        for rec in self:
            if rec.state != 'not_started' and not rec.can_open:
                raise UserError(
                    'ISA 300/220 & ISA 250 Violation: Sequential Planning Approach Required.\n\n'
                    'P-9 (Laws & Regulations) cannot be started until P-8 (Going Concern) '
                    'has been Partner-approved.\n\n'
                    'Reason: Compliance risk assessment per ISA 250 requires understanding of '
                    'going concern issues and overall risk context from P-8.\n\n'
                    'Action: Please complete and obtain Partner approval for P-8 first.'
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

    # ===== Section A: Additional Applicable Laws (Master Prompt) =====
    sector_specific_laws = fields.Text(
        string='Sector-Specific Laws (Mandatory)',
        help='Identify sector-specific laws applicable to the entity (e.g., banking, insurance, telecom)'
    )
    ngo_donor_regulations = fields.Boolean(
        string='NGO / Donor Regulations Applicable',
        help='Applicable if entity is an NGO or receives donor funding'
    )
    ngo_donor_details = fields.Html(
        string='NGO / Donor Compliance Details',
        help='Details of NGO/donor regulations and compliance status'
    )
    foreign_regulations_applicable = fields.Boolean(
        string='Foreign Regulations Applicable',
        help='Applicable if entity has cross-border operations'
    )
    foreign_regulations_details = fields.Html(
        string='Foreign Regulations Details',
        help='Details of foreign regulations and compliance requirements'
    )

    # Section A: Confirmations (ISA 250)
    confirm_laws_identified = fields.Boolean(
        string='☐ All relevant laws identified',
        help='Confirm all applicable laws and regulations have been identified',
        tracking=True
    )
    confirm_industry_regulations_covered = fields.Boolean(
        string='☐ Industry-specific regulations covered',
        help='Confirm industry-specific regulations have been considered',
        tracking=True
    )

    # ===== Section G: Management Representations & Inquiries =====
    management_representations_obtained = fields.Boolean(
        string='Management Representations Obtained?',
        tracking=True,
        help='ISA 250.15 - Have written representations been obtained from management?'
    )
    inquiry_results_summary = fields.Html(
        string='Inquiry Results Summary',
        help='Summary of inquiries made to management regarding laws and regulations'
    )
    contradictions_identified = fields.Boolean(
        string='Contradictions Identified?',
        tracking=True,
        help='Have contradictions been identified between management responses and other evidence?'
    )
    legal_counsel_required = fields.Boolean(
        string='Need for Legal Counsel Involvement?',
        tracking=True,
        help='Is involvement of legal counsel or specialist required?'
    )

    # Section G: Confirmations
    confirm_inquiries_documented = fields.Boolean(
        string='☐ Inquiries documented',
        help='Confirm all inquiries to management have been documented'
    )
    confirm_responses_evaluated = fields.Boolean(
        string='☐ Responses evaluated',
        help='Confirm management responses have been evaluated for consistency'
    )

    # ===== Section H: Audit Responses to Compliance Risks (ISA 330) =====
    # Planned Procedure Checkboxes
    procedure_substantive_testing = fields.Boolean(
        string='☐ Substantive Testing',
        help='Substantive testing of compliance with key laws/regulations'
    )
    procedure_legal_confirmations = fields.Boolean(
        string='☐ Legal Confirmations',
        help='Obtain confirmations from legal counsel'
    )
    procedure_correspondence_review = fields.Boolean(
        string='☐ Regulatory Correspondence Review',
        help='Review of correspondence with regulatory authorities'
    )
    audit_response_narrative = fields.Html(
        string='Nature, Timing, Extent of Procedures',
        help='Detailed description of audit procedures, timing, and extent per ISA 330'
    )
    specialist_involvement_required = fields.Boolean(
        string='Specialist Involvement Required?',
        tracking=True,
        help='Is involvement of legal or regulatory specialist required?'
    )
    specialist_details = fields.Html(
        string='Specialist Details',
        help='Details of specialist involvement (if required)'
    )

    # Section H: System Rule - Auto-Flow to P-12
    responses_linked_to_p12 = fields.Boolean(
        string='Responses Linked to P-12 (Audit Strategy)',
        help='Indicate if compliance audit responses have been incorporated into P-12',
        tracking=True
    )

    # ===== Compliance Procedures (Existing Fields - Retained) =====
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

    # ===== Section C: Regulatory Authorities & Oversight =====
    primary_regulators = fields.Text(
        string='Primary Regulator(s)',
        help='SECP / SBP / FBR / Others',
        default='SECP (Securities and Exchange Commission of Pakistan)'
    )
    inspection_frequency = fields.Selection([
        ('annual', 'Annual'),
        ('biennial', 'Biennial'),
        ('triennial', 'Triennial'),
        ('as_needed', 'As Needed'),
        ('none', 'No Regular Inspections'),
    ], string='Frequency of Regulatory Inspections')
    last_inspection_date = fields.Date(
        string='Last Inspection Date',
        help='Date of last regulatory inspection'
    )
    last_inspection_findings = fields.Html(
        string='Findings from Last Inspection',
        help='Key findings from last regulatory inspection (if any)'
    )
    outstanding_regulatory_matters = fields.Boolean(
        string='Outstanding Regulatory Matters',
        help='Are there any outstanding regulatory matters or unresolved findings?',
        tracking=True
    )
    outstanding_matters_details = fields.Html(
        string='Outstanding Matters Details',
        help='Details of outstanding regulatory matters'
    )

    # Section C: Confirmations
    confirm_oversight_understood = fields.Boolean(
        string='☐ Regulatory oversight understood',
        help='Confirm understanding of regulatory oversight framework'
    )
    confirm_prior_findings_considered = fields.Boolean(
        string='☐ Prior inspection findings considered',
        help='Confirm prior regulatory findings have been considered'
    )

    # ===== Section D: Compliance History & Known Non-Compliance =====
    non_compliance_identified = fields.Boolean(
        string='Known Non-Compliance Identified?',
        tracking=True,
        help='ISA 250.14 - Has the entity disclosed any known instances of non-compliance?'
    )
    non_compliance_nature = fields.Text(
        string='Nature of Non-Compliance',
        help='Describe the nature and circumstances of non-compliance'
    )
    non_compliance_period = fields.Char(
        string='Period(s) Affected',
        help='Financial period(s) affected by non-compliance (e.g., FY 2023-24)'
    )
    non_compliance_status = fields.Selection([
        ('resolved', '🟢 Resolved'),
        ('ongoing', '🟡 Ongoing'),
        ('disputed', '🔴 Disputed'),
    ], string='Status of Non-Compliance', tracking=True)
    non_compliance_financial_impact = fields.Monetary(
        string='Financial Impact (Actual/Potential)',
        currency_field='currency_id',
        help='Quantified financial impact of non-compliance'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    non_compliance_details = fields.Html(
        string='Non-Compliance Details',
        help='Comprehensive details of identified or suspected non-compliance per ISA 250'
    )
    non_compliance_impact = fields.Html(
        string='Impact on Financial Statements',
        help='Assessment of impact on FS and audit opinion'
    )
    non_compliance_response = fields.Html(
        string='Audit Response',
        help='Planned audit procedures to address non-compliance'
    )

    # Section D: System Rule - Auto-Flag
    disclosure_risk_from_noncompliance = fields.Boolean(
        string='Disclosure Risk Flagged',
        compute='_compute_noncompliance_flags',
        store=True,
        help='Auto-flagged if known non-compliance exists (system rule)'
    )
    rmm_impact_flagged = fields.Boolean(
        string='RMM Impact Flagged',
        compute='_compute_noncompliance_flags',
        store=True,
        help='Auto-flagged if non-compliance impacts risk assessment (P-6 linkage)'
    )
    # ===== Section E: Risk of Material Non-Compliance =====
    compliance_risk_level = fields.Selection([
        ('low', '🟢 Low Risk'),
        ('moderate', '🟡 Moderate Risk'),
        ('high', '🔴 High Risk'),
    ], string='Overall Compliance Risk Level', tracking=True, help='Overall assessment of compliance risk per ISA 315')
    high_risk_areas = fields.Text(
        string='High Risk Areas Identified',
        help='List areas with high risk of material non-compliance'
    )
    compliance_risk_assessment_narrative = fields.Html(
        string='Compliance Risk Assessment Narrative',
        help='Detailed risk assessment of material non-compliance (ISA 315 linkage)'
    )

    # Section E: System Rule - High Risk Auto-Escalation
    high_risk_requires_escalation = fields.Boolean(
        string='High Risk Requires RMM Escalation',
        compute='_compute_compliance_risk_escalation',
        store=True,
        help='Auto-flagged if high compliance risk must increase FS-level RMM in P-6'
    )

    # ===== Section F: Fraud & Illegal Acts Consideration (ISA 240 Link) =====
    indicators_illegal_acts = fields.Boolean(
        string='Indicators of Illegal Acts Identified?',
        tracking=True,
        help='ISA 240.24 - Have indicators of illegal acts or non-compliance been identified?'
    )
    management_involvement_suspected = fields.Boolean(
        string='Management Involvement Suspected?',
        tracking=True,
        help='ISA 250.29 - Is management involvement in illegal acts suspected?'
    )
    whistleblower_complaints = fields.Boolean(
        string='Whistleblower Complaints / Media Reports?',
        tracking=True,
        help='Have there been whistleblower complaints or adverse media reports?'
    )
    fraud_impact_narrative = fields.Html(
        string='Impact on Fraud Risk Assessment',
        help='How identified non-compliance impacts fraud risk assessment (P-7 linkage)'
    )

    # Section F: System Rule - Auto-Link to P-7 Fraud
    fraud_linkage_required = fields.Boolean(
        string='Fraud Linkage Required (P-7)',
        compute='_compute_fraud_linkage',
        store=True,
        help='Auto-flagged if illegal acts indicators require P-7 fraud risk update'
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

    # ===== Section I: Impact on Going Concern & Reporting =====
    noncompliance_impacts_gc = fields.Boolean(
        string='Non-Compliance Impacts Going Concern?',
        tracking=True,
        help='ISA 570 linkage - Does non-compliance cast doubt on going concern?'
    )
    disclosure_required = fields.Boolean(
        string='Disclosure Required in Financial Statements?',
        tracking=True,
        help='Is disclosure of non-compliance required in financial statements?'
    )
    reporting_modification_possible = fields.Boolean(
        string='Possible Reporting Modification?',
        tracking=True,
        help='Is audit report modification (qualification/adverse) possible?'
    )
    gc_reporting_conclusion_basis = fields.Html(
        string='Basis for Going Concern & Reporting Conclusion',
        help='Detailed basis for conclusion on GC and reporting implications per ISA 250.26'
    )

    # Section I: System Rule - Auto-Link to P-8
    gc_linkage_required = fields.Boolean(
        string='P-8 Going Concern Linkage Required',
        compute='_compute_gc_linkage',
        store=True,
        help='Auto-flagged if non-compliance impacts P-8 going concern assessment'
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
        help='Is reporting to regulatory authorities required per Auditors Reporting Obligations Regulations 2018?'
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

    # ===== Section J: Mandatory Document Uploads =====
    statutory_filings_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p9_statutory_filings_rel',
        'p9_id',
        'attachment_id',
        string='☐ Statutory Filings / Returns (MANDATORY)',
        help='Annual returns, tax returns, regulatory filings'
    )
    regulatory_correspondence_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p9_regulatory_correspondence_rel',
        'p9_id',
        'attachment_id',
        string='☐ Regulatory Correspondence (MANDATORY)',
        help='Correspondence with SECP, SBP, FBR, or other regulators'
    )
    legal_opinion_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p9_legal_opinion_rel',
        'p9_id',
        'attachment_id',
        string='☐ Legal Opinions (if any)',
        help='Legal opinions obtained regarding compliance matters'
    )
    prior_year_compliance_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p9_prior_compliance_rel',
        'p9_id',
        'attachment_id',
        string='☐ Prior-Year Compliance Letters (MANDATORY)',
        help='Compliance letters issued in prior years'
    )
    mgmt_representation_draft_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p9_mgmt_rep_rel',
        'p9_id',
        'attachment_id',
        string='☐ Management Representation Drafts (MANDATORY)',
        help='Draft management representation letters regarding compliance'
    )

    # ===== Attachments (Existing - Retained for XML Compatibility) =====
    compliance_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p9_compliance_rel',
        'p9_id',
        'attachment_id',
        string='Compliance Documents'
    )
    # XML view compatible alias
    regulatory_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p9_regulatory_rel',
        'p9_id',
        'attachment_id',
        string='Regulatory Correspondence'
    )

    # ===== Section K: P-9 Conclusion & Professional Judgment =====
    compliance_summary = fields.Html(
        string='Legal & Regulatory Compliance Summary (MANDATORY)',
        help='Consolidated compliance assessment per ISA 250',
        default=lambda self: '''
<p><strong>P-9: Laws & Regulations Compliance Assessment (ISA 250)</strong></p>
<p>Relevant laws and regulations applicable to the entity have been identified and considered in accordance with ISA 250. Risks of material non-compliance have been assessed, and appropriate audit responses and reporting implications have been determined.</p>
<ol>
<li><strong>Applicable Laws:</strong> [Summarize Category A and B laws]</li>
<li><strong>Compliance Assessment:</strong> [Overall compliance status]</li>
<li><strong>Risks Identified:</strong> [Key compliance risks and non-compliance items]</li>
<li><strong>Audit Responses:</strong> [Planned procedures per ISA 330]</li>
<li><strong>Reporting Implications:</strong> [Impact on audit report and disclosures]</li>
</ol>
<p><strong>Conclusion:</strong> [State overall conclusion on compliance risk and audit strategy implications]</p>
'''
    )
    # XML view compatible alias
    laws_conclusion = fields.Html(
        string='Laws & Regulations Conclusion',
        related='compliance_summary',
        readonly=False
    )

    # Section K: Final Confirmations (Mandatory Before Approval)
    confirm_laws_considered = fields.Boolean(
        string='☐ Laws & regulations adequately considered',
        help='Confirm all relevant laws and regulations have been adequately considered per ISA 250',
        tracking=True
    )
    confirm_risks_assessed_linked = fields.Boolean(
        string='☐ Compliance risks assessed and linked',
        help='Confirm compliance risks assessed and linked to P-6 (RMM) and P-12 (Audit Strategy)',
        tracking=True
    )
    confirm_basis_established = fields.Boolean(
        string='☐ Basis established for audit responses',
        help='Confirm basis established for audit responses and reporting implications',
        tracking=True
    )

    isa_reference = fields.Char(
        string='ISA Reference',
        default='ISA 250 (Revised)',
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
            errors.append('Compliance summary is required (Section K)')
        if self.non_compliance_identified and not self.non_compliance_details:
            errors.append('Non-compliance details must be documented (Section D)')
        
        # Section K: Mandatory confirmations before approval
        if not self.confirm_laws_considered:
            errors.append('Section K: Confirm all laws & regulations adequately considered')
        if not self.confirm_risks_assessed_linked:
            errors.append('Section K: Confirm compliance risks assessed and linked to P-6/P-12')
        if not self.confirm_basis_established:
            errors.append('Section K: Confirm basis established for audit responses')
        
        # Section J: Mandatory document uploads
        if not self.statutory_filings_attachment_ids:
            errors.append('Section J: Statutory filings/returns must be uploaded')
        if not self.prior_year_compliance_attachment_ids:
            errors.append('Section J: Prior-year compliance letters must be uploaded')
        if not self.mgmt_representation_draft_attachment_ids:
            errors.append('Section J: Management representation drafts must be uploaded')
        
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
            record.message_post(body='P-9 Laws & Regulations approved by Partner.')
            # Section L: Auto-unlock P-10 Related Parties Planning
            record._auto_unlock_p10()

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

    def _auto_unlock_p10(self):
        """Section L: Auto-unlock P-10 Related Parties Planning when P-9 is approved."""
        self.ensure_one()
        if not self.audit_id:
            return
        
        # Find or create P-10 record
        P10 = self.env['qaco.planning.p10.related.parties']
        p10_record = P10.search([('audit_id', '=', self.audit_id.id)], limit=1)
        
        if p10_record and p10_record.state == 'locked':
            p10_record.write({'state': 'not_started'})
            p10_record.message_post(
                body='P-10 Related Parties Planning auto-unlocked after P-9 Laws & Regulations approval.'
            )
            _logger.info(f'P-10 auto-unlocked for audit {self.audit_id.name}')
        elif not p10_record:
            # Create new P-10 record if doesn't exist
            p10_record = P10.create({
                'audit_id': self.audit_id.id,
                'state': 'not_started',
            })
            _logger.info(f'P-10 auto-created for audit {self.audit_id.name}')

    # ===== COMPUTE METHODS: System Rules =====

    @api.depends('non_compliance_identified', 'non_compliance_status', 'non_compliance_financial_impact')
    def _compute_noncompliance_flags(self):
        """Section D: Auto-flag disclosure risk and RMM impact if known non-compliance exists."""
        for record in self:
            # Disclosure risk if non-compliance identified and unresolved
            record.disclosure_risk_from_noncompliance = (
                record.non_compliance_identified and
                record.non_compliance_status in ['ongoing', 'disputed']
            )
            # RMM impact if non-compliance is material (financial impact significant)
            record.rmm_impact_flagged = (
                record.non_compliance_identified and
                record.non_compliance_financial_impact > 0
            )

    @api.depends('compliance_risk_level')
    def _compute_compliance_risk_escalation(self):
        """Section E: Auto-flag if high compliance risk requires RMM escalation to P-6."""
        for record in self:
            record.high_risk_requires_escalation = (record.compliance_risk_level == 'high')

    @api.depends('indicators_illegal_acts', 'management_involvement_suspected', 'whistleblower_complaints')
    def _compute_fraud_linkage(self):
        """Section F: Auto-flag if illegal acts indicators require P-7 fraud risk update."""
        for record in self:
            record.fraud_linkage_required = any([
                record.indicators_illegal_acts,
                record.management_involvement_suspected,
                record.whistleblower_complaints
            ])

    @api.depends('noncompliance_impacts_gc')
    def _compute_gc_linkage(self):
        """Section I: Auto-flag if non-compliance impacts P-8 going concern assessment."""
        for record in self:
            record.gc_linkage_required = record.noncompliance_impacts_gc


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
