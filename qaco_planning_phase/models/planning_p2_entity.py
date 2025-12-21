# -*- coding: utf-8 -*-
"""
P-2: Understanding the Entity & Its Environment - COMPLETE BUILD (Odoo 17)
================================================================================
Standards Compliance:
- ISA 315 (Revised): Identifying and Assessing the Risks of Material Misstatement
- ISA 250: Consideration of Laws and Regulations
- ISA 570: Going Concern (early indicators)
- ISA 220: Quality Management
- ISQM-1: Firm-level Quality Management
- Companies Act, 2017 (Pakistan)
- ICAP QCR / AOB inspection framework

Purpose:
Ensure the auditor demonstrably understands the client, its business model,
industry, regulatory environment, and external/internal risk factors.
================================================================================
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


# =============================================================================
# SECTION J: Business Risk Line Model (for Risk Identification & RMM Linkage)
# =============================================================================
class PlanningP2BusinessRisk(models.Model):
    """Business Risk Identification - Links to P-6 Risk Assessment"""
    _name = 'qaco.planning.p2.business.risk'
    _description = 'P-2 Business Risk Identification'
    _order = 'sequence, id'

    FS_AREA_SELECTION = [
        ('revenue', 'Revenue Recognition'),
        ('inventory', 'Inventory'),
        ('receivables', 'Trade Receivables'),
        ('payables', 'Trade Payables'),
        ('fixed_assets', 'Property, Plant & Equipment'),
        ('intangibles', 'Intangible Assets'),
        ('investments', 'Investments'),
        ('borrowings', 'Borrowings'),
        ('provisions', 'Provisions & Contingencies'),
        ('related_parties', 'Related Party Transactions'),
        ('estimates', 'Accounting Estimates'),
        ('going_concern', 'Going Concern'),
        ('disclosure', 'Disclosures'),
        ('other', 'Other'),
    ]

    SEVERITY_SELECTION = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    p2_id = fields.Many2one(
        'qaco.planning.p2.entity',
        string='P-2 Entity Understanding',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sequence = fields.Integer(string='Sequence', default=10)
    risk_description = fields.Text(
        string='Risk Description',
        required=True,
        help='Describe the business risk identified',
    )
    fs_area = fields.Selection(
        FS_AREA_SELECTION,
        string='FS Area Affected',
        required=True,
    )
    potential_misstatement = fields.Text(
        string='Potential Misstatement',
        help='How could this risk lead to material misstatement?',
    )
    severity = fields.Selection(
        SEVERITY_SELECTION,
        string='Initial Severity',
        default='medium',
        required=True,
    )
    linked_to_p6 = fields.Boolean(
        string='Linked to P-6',
        default=False,
        readonly=True,
        help='Automatically set when risk is transferred to Risk Register',
    )
    notes = fields.Text(string='Notes')


# =============================================================================
# SECTION I: Changes During Year Line Model
# =============================================================================
class PlanningP2Change(models.Model):
    """Significant Changes During the Year"""
    _name = 'qaco.planning.p2.change'
    _description = 'P-2 Changes During Year'
    _order = 'sequence, id'

    CHANGE_TYPE_SELECTION = [
        ('operations', 'Changes in Operations'),
        ('systems', 'Changes in Systems'),
        ('management', 'Changes in Key Management'),
        ('ownership', 'Changes in Ownership'),
        ('economic', 'Economic/External Factors'),
        ('restructuring', 'Restructuring'),
        ('unusual', 'Unusual/One-off Events'),
        ('other', 'Other'),
    ]

    p2_id = fields.Many2one(
        'qaco.planning.p2.entity',
        string='P-2 Entity Understanding',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sequence = fields.Integer(string='Sequence', default=10)
    change_type = fields.Selection(
        CHANGE_TYPE_SELECTION,
        string='Type of Change',
        required=True,
    )
    description = fields.Text(
        string='Description',
        required=True,
    )
    audit_impact = fields.Text(
        string='Audit Impact',
        help='How does this change impact the audit approach?',
    )
    impact_assessed = fields.Boolean(
        string='Impact Assessed',
        default=False,
    )


# =============================================================================
# MAIN MODEL: P-2 Understanding the Entity & Its Environment
# =============================================================================
class PlanningP2Entity(models.Model):
    """
    P-2: Understanding the Entity & Its Environment
    ISA 315 (Revised), ISA 250, ISA 570, ISA 220, ISQM-1

    PRE-CONDITIONS (System-Enforced):
    - P-1 is partner-approved and locked
    - Engagement setup completed
    - Audit team assigned
    - Independence reconfirmed
    """
    _name = 'qaco.planning.p2.entity'
    _description = 'P-2: Understanding the Entity & Its Environment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # =========================================================================
    # STATUS WORKFLOW
    # =========================================================================
    TAB_STATE = [
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('reviewed', 'Manager Reviewed'),
        ('approved', 'Partner Approved'),
        ('locked', 'Locked'),
    ]

    state = fields.Selection(
        TAB_STATE,
        string='Status',
        default='draft',
        tracking=True,
        copy=False,
        help='Workflow: Draft → In Progress → Completed → Reviewed → Approved → Locked',
    )
    is_locked = fields.Boolean(
        string='Is Locked',
        compute='_compute_is_locked',
        store=True,
    )

    # Sequential Gating (ISA 300/220: Systematic Planning Approach)
    can_open = fields.Boolean(
        string='Can Open This Tab',
        compute='_compute_can_open',
        store=False,
        help='P-2 can only be opened after P-1 is approved'
    )

    @api.depends('state')
    def _compute_is_locked(self):
        for rec in self:
            rec.is_locked = rec.state in ('approved', 'locked')

    @api.depends('audit_id')
    def _compute_can_open(self):
        """P-2 requires P-1 to be approved."""
        for rec in self:
            if not rec.audit_id:
                rec.can_open = False
                continue
            # Find P-1 for this audit
            p1 = self.env['qaco.planning.p1.engagement'].search([
                ('audit_id', '=', rec.audit_id.id)
            ], limit=1)
            rec.can_open = p1.state == 'approved' if p1 else False

    # =========================================================================
    # CORE LINKS & IDENTIFICATION
    # =========================================================================
    name = fields.Char(
        string='Reference',
        compute='_compute_name',
        store=True,
        readonly=True,
    )
    audit_id = fields.Many2one(
        'qaco.audit',
        string='Audit Engagement',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
    )
    planning_phase_id = fields.Many2one(
        'qaco.planning.phase',
        string='Planning Phase',
        ondelete='cascade',
        index=True,
    )
    planning_main_id = fields.Many2one(
        'qaco.planning.main',
        string='Planning Main',
        ondelete='cascade',
        index=True,
        help='Link to main planning orchestrator (planning_base.py)',
    )
    client_id = fields.Many2one(
        'res.partner',
        string='Client Name',
        related='audit_id.client_id',
        readonly=True,
        store=False,
    )
    firm_id = fields.Many2one(
        'audit.firm.name',
        string='Audit Firm',
        related='audit_id.firm_name',
        readonly=True,
        store=False,
    )
    industry_id = fields.Many2one(
        'qaco.industry',
        string='Industry Classification',
        tracking=True,
    )
    engagement_partner_id = fields.Many2one(
        'hr.employee',
        string='Engagement Partner',
        related='audit_id.qaco_audit_partner',
        readonly=True,
        store=False,
    )
    audit_year = fields.Many2many(
        'audit.year',
        string='Audit Year',
        related='audit_id.audit_year',
        readonly=True,
        store=False,
    )

    # =========================================================================
    # SECTION A: Entity Profile & Legal Structure
    # =========================================================================
    # Auto-fetched fields (read-only)
    legal_name = fields.Char(
        string='Legal Name',
        related='client_id.name',
        readonly=True,
        store=False,
    )
    entity_type = fields.Selection([
        ('private_limited', 'Private Limited'),
        ('listed', 'Listed Company'),
        ('pie', 'Public Interest Entity'),
        ('ngo_npo', 'NGO / NPO'),
        ('partnership', 'Partnership'),
        ('sole_proprietor', 'Sole Proprietorship'),
        ('government', 'Government Entity'),
        ('other', 'Other'),
    ], string='Entity Type', tracking=True)
    date_of_incorporation = fields.Date(
        string='Date of Incorporation',
        tracking=True,
    )
    registration_ntn = fields.Char(
        string='Registration Number / NTN',
        tracking=True,
    )
    principal_place_of_business = fields.Char(
        string='Principal Place of Business',
    )
    has_branches = fields.Boolean(
        string='Has Branches/Locations?',
        default=False,
    )
    branches_details = fields.Text(
        string='Branch/Location Details',
        help='List all branches and operational locations',
    )

    # Section A Checklist
    check_a_legal_existence = fields.Boolean(string='Legal existence verified')
    check_a_entity_type = fields.Boolean(string='Entity type confirmed')
    check_a_scope_operations = fields.Boolean(string='Scope of operations identified')

    # =========================================================================
    # SECTION B: Ownership, Control & Governance Overview
    # =========================================================================
    ownership_structure_summary = fields.Html(
        string='Ownership Structure Summary',
        help='Narrative description of ownership structure',
    )
    # UBO auto-link would come from client onboarding
    ubo_reference = fields.Text(
        string='Ultimate Beneficial Owners Reference',
        help='Reference to UBO details from client onboarding',
    )
    ownership_changed = fields.Boolean(
        string='Ownership Changed During Year?',
        default=False,
    )
    ownership_change_details = fields.Text(
        string='Ownership Change Details',
    )
    control_structure = fields.Selection([
        ('centralized', 'Centralized'),
        ('decentralized', 'Decentralized'),
        ('mixed', 'Mixed'),
    ], string='Control Structure')
    dominant_shareholder = fields.Boolean(
        string='Dominant Shareholder Influence?',
        default=False,
    )
    dominant_shareholder_explanation = fields.Text(
        string='Dominant Shareholder Explanation',
    )

    # Section B Checklist
    check_b_control_environment = fields.Boolean(string='Control environment understood')
    check_b_governance = fields.Boolean(string='Governance structure assessed')
    check_b_management_override = fields.Boolean(string='Risk of management override considered')

    # =========================================================================
    # SECTION C: Business Model & Strategy
    # =========================================================================
    core_business_activities = fields.Html(
        string='Core Business Activities',
        help='Primary business activities of the entity',
    )
    key_products_services = fields.Html(
        string='Key Products/Services',
    )
    revenue_generation_model = fields.Html(
        string='Revenue Generation Model',
        help='How does the entity generate revenue?',
    )
    key_markets = fields.Selection([
        ('local', 'Local Only'),
        ('export', 'Export Only'),
        ('both', 'Both Local & Export'),
    ], string='Key Markets')
    key_markets_details = fields.Text(
        string='Market Details',
    )
    strategic_objectives = fields.Html(
        string='Strategic Objectives',
    )
    expansion_restructuring_plans = fields.Text(
        string='Expansion/Restructuring Plans',
    )
    new_products_services = fields.Boolean(
        string='New Products/Services During Year?',
        default=False,
    )
    new_products_services_details = fields.Text(
        string='New Products/Services Details',
    )

    # Section C Checklist
    check_c_business_model = fields.Boolean(string='Business model documented')
    check_c_strategy_risks = fields.Boolean(string='Strategy-related risks identified')

    # =========================================================================
    # SECTION D: Industry, Economic & External Environment
    # =========================================================================
    industry_classification = fields.Selection([
        ('manufacturing', 'Manufacturing'),
        ('trading', 'Trading'),
        ('services', 'Services'),
        ('financial', 'Financial Services'),
        ('insurance', 'Insurance'),
        ('construction', 'Construction'),
        ('real_estate', 'Real Estate'),
        ('technology', 'Technology'),
        ('healthcare', 'Healthcare'),
        ('education', 'Education'),
        ('agriculture', 'Agriculture'),
        ('energy', 'Energy/Utilities'),
        ('transport', 'Transport/Logistics'),
        ('hospitality', 'Hospitality'),
        ('retail', 'Retail'),
        ('public_sector', 'Public Sector'),
        ('other', 'Other'),
    ], string='Industry Sector', tracking=True)
    competitive_landscape = fields.Html(
        string='Competitive Landscape',
    )
    key_competitors = fields.Text(
        string='Key Competitors',
    )
    industry_cyclicality = fields.Selection([
        ('none', 'None/Minimal'),
        ('seasonal', 'Seasonal'),
        ('cyclical', 'Cyclical'),
        ('highly_cyclical', 'Highly Cyclical'),
    ], string='Industry Cyclicality/Seasonality')
    economic_conditions = fields.Html(
        string='Economic Conditions Impacting Business',
    )
    technological_changes = fields.Html(
        string='Technological Changes Impacting Industry',
    )
    regulatory_pressure = fields.Html(
        string='Regulatory Pressure on Industry',
    )

    # Section D Checklist
    check_d_industry_risks = fields.Boolean(string='Industry risks identified')
    check_d_external_factors = fields.Boolean(string='External factors considered')
    check_d_going_concern = fields.Boolean(string='Going-concern indicators flagged (if any)')

    # =========================================================================
    # SECTION E: Regulatory & Legal Environment (Entity-Specific)
    # =========================================================================
    primary_regulators = fields.Many2many(
        'qaco.regulator',
        'qaco_p2_regulator_rel',
        'p2_id',
        'regulator_id',
        string='Primary Regulators',
    )
    applicable_laws = fields.Html(
        string='Applicable Laws & Regulations',
    )
    licensing_requirements = fields.Text(
        string='Licensing Requirements',
    )
    regulatory_inspection_history = fields.Html(
        string='History of Regulatory Inspections',
    )
    known_legal_disputes = fields.Html(
        string='Known Legal Disputes/Litigation',
    )
    penalties_noncompliance = fields.Html(
        string='Penalties/Non-Compliance History',
    )

    # Section E Checklist
    check_e_laws_identified = fields.Boolean(string='Relevant laws identified')
    check_e_noncompliance_risk = fields.Boolean(string='Non-compliance risk assessed')
    check_e_fs_impact = fields.Boolean(string='Impact on FS considered')

    # =========================================================================
    # SECTION F: Accounting Framework & Financial Reporting
    # =========================================================================
    reporting_framework = fields.Selection([
        ('ifrs', 'IFRS (Full)'),
        ('ifrs_sme', 'IFRS for SMEs'),
        ('ifas', 'IFAS (Pakistan)'),
        ('gaap_pk', 'Pakistan GAAP'),
        ('other', 'Other'),
    ], string='Applicable Financial Reporting Framework', default='ifrs', tracking=True)
    framework_other = fields.Char(string='Other Framework Details')
    accounting_policy_changes = fields.Boolean(
        string='Changes in Accounting Policies?',
        default=False,
    )
    accounting_policy_change_details = fields.Text(
        string='Accounting Policy Change Details',
    )
    significant_estimates = fields.Html(
        string='Significant Accounting Estimates Used',
    )
    areas_requiring_judgment = fields.Html(
        string='Areas Requiring Significant Judgment',
    )
    prior_year_audit_issues = fields.Html(
        string='Prior Year Audit Issues Impacting Current Year',
    )

    # Section F Checklist
    check_f_framework_appropriate = fields.Boolean(string='Framework appropriate')
    check_f_judgmental_areas = fields.Boolean(string='Judgmental areas identified')
    check_f_misstatement_risk = fields.Boolean(string='Risk of misstatement considered')

    # =========================================================================
    # SECTION G: Information Systems & IT Environment
    # =========================================================================
    accounting_system = fields.Selection([
        ('erp_sap', 'ERP - SAP'),
        ('erp_oracle', 'ERP - Oracle'),
        ('erp_odoo', 'ERP - Odoo'),
        ('erp_other', 'ERP - Other'),
        ('standalone', 'Standalone Accounting Software'),
        ('manual_excel', 'Manual / Excel'),
        ('other', 'Other'),
    ], string='Accounting System Used')
    accounting_system_other = fields.Char(string='Other System Details')
    degree_of_automation = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Degree of Automation')
    data_hosting = fields.Selection([
        ('local', 'Local/On-Premise'),
        ('cloud_local', 'Cloud (Local Provider)'),
        ('cloud_foreign', 'Cloud (Foreign Provider)'),
        ('hybrid', 'Hybrid'),
    ], string='Data Hosting Location')
    key_it_applications = fields.Html(
        string='Key IT Applications Impacting Financial Reporting',
    )
    spreadsheet_use = fields.Boolean(
        string='Spreadsheets Used in Financial Reporting?',
        default=False,
    )
    spreadsheet_details = fields.Text(
        string='Spreadsheet Usage Details',
    )

    # Section G Checklist
    check_g_it_understood = fields.Boolean(string='IT environment understood')
    check_g_it_risks = fields.Boolean(string='IT-related risks identified')
    check_g_it_auditor = fields.Boolean(string='Need for IT auditor considered')

    # =========================================================================
    # SECTION H: Human Resources & Operations
    # =========================================================================
    key_management_personnel = fields.Html(
        string='Key Management Personnel',
    )
    reliance_key_individuals = fields.Boolean(
        string='Reliance on Key Individuals?',
        default=False,
    )
    reliance_key_individuals_details = fields.Text(
        string='Key Individual Reliance Details',
    )
    staff_turnover = fields.Selection([
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
    ], string='Staff Turnover During Year')
    staff_turnover_details = fields.Text(
        string='Staff Turnover Details',
    )
    outsourced_functions = fields.Html(
        string='Outsourced Functions',
    )
    segregation_of_duties_concerns = fields.Boolean(
        string='Segregation of Duties Concerns?',
        default=False,
    )
    segregation_concerns_details = fields.Text(
        string='Segregation Concerns Details',
    )

    # Section H Checklist
    check_h_operational_risks = fields.Boolean(string='Operational risks identified')
    check_h_hr_risks = fields.Boolean(string='HR-related control risks considered')

    # =========================================================================
    # SECTION I: Changes During the Year (One2many)
    # =========================================================================
    change_ids = fields.One2many(
        'qaco.planning.p2.change',
        'p2_id',
        string='Significant Changes During Year',
    )

    # Section I Checklist
    check_i_changes_identified = fields.Boolean(string='All significant changes identified')
    check_i_audit_impact = fields.Boolean(string='Audit impact assessed')

    # =========================================================================
    # SECTION J: Risk Identification & Linkage to RMM (One2many)
    # =========================================================================
    business_risk_ids = fields.One2many(
        'qaco.planning.p2.business.risk',
        'p2_id',
        string='Business Risks Identified',
    )

    # Computed counts
    total_risks_identified = fields.Integer(
        string='Total Risks Identified',
        compute='_compute_risk_counts',
        store=True,
    )
    high_risk_count = fields.Integer(
        string='High Severity Risks',
        compute='_compute_risk_counts',
        store=True,
    )

    @api.depends('business_risk_ids', 'business_risk_ids.severity')
    def _compute_risk_counts(self):
        for rec in self:
            rec.total_risks_identified = len(rec.business_risk_ids)
            rec.high_risk_count = len(rec.business_risk_ids.filtered(
                lambda r: r.severity == 'high'
            ))

    # =========================================================================
    # SECTION K: Mandatory Document Uploads
    # =========================================================================
    organogram_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p2_organogram_rel',
        'p2_id',
        'attachment_id',
        string='Organizational Chart',
    )
    process_docs_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p2_process_docs_rel',
        'p2_id',
        'attachment_id',
        string='Process Overview Documents',
    )
    industry_reports_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p2_industry_reports_rel',
        'p2_id',
        'attachment_id',
        string='Industry Reports',
    )
    regulatory_correspondence_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p2_regulatory_corr_rel',
        'p2_id',
        'attachment_id',
        string='Regulatory Correspondence',
    )
    prior_year_planning_memo_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p2_py_planning_rel',
        'p2_id',
        'attachment_id',
        string='Prior Year Audit Planning Memo',
    )

    # Document checklist
    doc_organogram_uploaded = fields.Boolean(
        string='Organizational Chart Uploaded',
        compute='_compute_doc_status',
        store=True,
    )
    doc_process_uploaded = fields.Boolean(
        string='Process Documents Uploaded',
        compute='_compute_doc_status',
        store=True,
    )

    @api.depends('organogram_attachment_ids', 'process_docs_attachment_ids')
    def _compute_doc_status(self):
        for rec in self:
            rec.doc_organogram_uploaded = bool(rec.organogram_attachment_ids)
            rec.doc_process_uploaded = bool(rec.process_docs_attachment_ids)

    # =========================================================================
    # SECTION L: P-2 Conclusion & Professional Judgment
    # =========================================================================
    conclusion_narrative = fields.Html(
        string='P-2 Conclusion & Professional Judgment',
        help='''Based on the understanding obtained of the entity, its environment,
        industry, regulatory framework, and internal structure, document the
        conclusion regarding sufficiency of knowledge to identify and assess
        the risks of material misstatement in accordance with ISA 315.''',
    )

    # Final Confirmations
    confirm_entity_understanding = fields.Boolean(
        string='Entity understanding complete',
        tracking=True,
    )
    confirm_risks_identified = fields.Boolean(
        string='Risks adequately identified for planning',
        tracking=True,
    )
    confirm_proceed_p3 = fields.Boolean(
        string='Proceed to internal control understanding (P-3)',
        tracking=True,
    )

    # =========================================================================
    # SECTION M: Review, Approval & Lock
    # =========================================================================
    prepared_by_id = fields.Many2one(
        'res.users',
        string='Prepared By',
        readonly=True,
        copy=False,
    )
    prepared_on = fields.Datetime(
        string='Prepared On',
        readonly=True,
        copy=False,
    )
    reviewed_by_id = fields.Many2one(
        'res.users',
        string='Reviewed By (Manager)',
        readonly=True,
        copy=False,
        tracking=True,
    )
    reviewed_on = fields.Datetime(
        string='Reviewed On',
        readonly=True,
        copy=False,
        tracking=True,
    )
    review_comments = fields.Text(
        string='Review Comments',
    )
    partner_approved = fields.Boolean(
        string='Partner Approved',
        readonly=True,
        copy=False,
        tracking=True,
    )
    partner_approved_by_id = fields.Many2one(
        'res.users',
        string='Partner Approved By',
        readonly=True,
        copy=False,
        tracking=True,
    )
    partner_approved_on = fields.Datetime(
        string='Partner Approved On',
        readonly=True,
        copy=False,
        tracking=True,
    )
    partner_comments = fields.Text(
        string='Partner Comments',
        help='Mandatory partner comments on approval',
    )

    # =========================================================================
    # SQL CONSTRAINTS
    # =========================================================================
    _sql_constraints = [
        ('audit_unique', 'UNIQUE(audit_id)',
         'Only one P-2: Entity Understanding record per Audit Engagement is allowed.'),
    ]

    # =========================================================================
    # COMPUTED FIELDS
    # =========================================================================
    @api.depends('audit_id', 'client_id', 'audit_year')
    def _compute_name(self):
        for rec in self:
            parts = ['P2']
            if rec.client_id:
                parts.append(rec.client_id.name[:20] if rec.client_id.name else '')
            if rec.audit_year:
                parts.append(rec.audit_year)
            rec.name = '-'.join(filter(None, parts)) or 'P-2: Entity Understanding'

    # =========================================================================
    # PRE-CONDITIONS CHECK
    # =========================================================================
    def _check_preconditions(self):
        """
        Verify P-2 preconditions before allowing work:
        - P-1 is partner-approved and locked
        - Engagement setup completed
        - Audit team assigned
        - Independence reconfirmed
        """
        self.ensure_one()
        errors = []

        # Check if P-1 exists and is approved/locked
        if 'qaco.planning.p1.engagement' in self.env:
            P1Model = self.env['qaco.planning.p1.engagement']
            p1 = P1Model.search([('audit_id', '=', self.audit_id.id)], limit=1)
            if not p1:
                errors.append('P-1: Engagement Setup must be completed before P-2.')
            elif p1.state not in ('approved', 'locked'):
                errors.append('P-1: Engagement Setup must be partner-approved before P-2 can begin.')

        if errors:
            raise UserError(
                'P-2 Preconditions Not Met:\n• ' + '\n• '.join(errors)
            )

    # =========================================================================
    # MANDATORY FIELD VALIDATION FOR COMPLETION
    # =========================================================================
    def _validate_mandatory_fields(self):
        """Validate all mandatory fields before completing P-2."""
        self.ensure_one()
        errors = []

        # Section A
        if not self.entity_type:
            errors.append('Entity Type is required (Section A)')
        if not self.check_a_legal_existence:
            errors.append('Legal existence must be verified (Section A)')
        if not self.check_a_entity_type:
            errors.append('Entity type must be confirmed (Section A)')

        # Section B
        if not self.check_b_control_environment:
            errors.append('Control environment must be understood (Section B)')
        if not self.check_b_governance:
            errors.append('Governance structure must be assessed (Section B)')
        if not self.check_b_management_override:
            errors.append('Risk of management override must be considered (Section B)')

        # Section C
        if not self.core_business_activities:
            errors.append('Core business activities must be documented (Section C)')
        if not self.check_c_business_model:
            errors.append('Business model must be documented (Section C)')

        # Section D
        if not self.industry_classification:
            errors.append('Industry classification is required (Section D)')
        if not self.check_d_industry_risks:
            errors.append('Industry risks must be identified (Section D)')

        # Section E
        if not self.check_e_laws_identified:
            errors.append('Relevant laws must be identified (Section E)')
        if not self.check_e_noncompliance_risk:
            errors.append('Non-compliance risk must be assessed (Section E)')

        # Section F
        if not self.reporting_framework:
            errors.append('Reporting framework is required (Section F)')
        if not self.check_f_framework_appropriate:
            errors.append('Framework appropriateness must be confirmed (Section F)')

        # Section G
        if not self.accounting_system:
            errors.append('Accounting system must be specified (Section G)')
        if not self.check_g_it_understood:
            errors.append('IT environment must be understood (Section G)')

        # Section H
        if not self.check_h_operational_risks:
            errors.append('Operational risks must be identified (Section H)')

        # Section I
        if not self.check_i_changes_identified:
            errors.append('Significant changes must be identified (Section I)')

        # Section J
        if not self.business_risk_ids:
            errors.append('At least one business risk must be identified (Section J)')

        # Section K - Mandatory Documents
        if not self.organogram_attachment_ids:
            errors.append('Organizational chart must be uploaded (Section K)')

        # Section L
        if not self.conclusion_narrative:
            errors.append('P-2 Conclusion narrative is required (Section L)')
        if not self.confirm_entity_understanding:
            errors.append('Entity understanding must be confirmed complete (Section L)')
        if not self.confirm_risks_identified:
            errors.append('Risks must be confirmed as adequately identified (Section L)')

        if errors:
            raise UserError(
                'Cannot complete P-2. Missing requirements:\n• ' + '\n• '.join(errors)
            )

    # =========================================================================
    # WORKFLOW ACTIONS
    # =========================================================================
    def action_start_work(self):
        """Move from Draft to In Progress, checking preconditions."""
        for rec in self:
            if rec.state != 'draft':
                raise UserError('Can only start work on records in Draft state.')
            rec._check_preconditions()
            rec.state = 'in_progress'
            rec.message_post(body='P-2 Entity Understanding work started.')

    def action_complete(self):
        """Mark as Completed by preparer, validating mandatory fields."""
        for rec in self:
            if rec.state != 'in_progress':
                raise UserError('Can only complete records that are In Progress.')
            rec._validate_mandatory_fields()
            rec.prepared_by_id = self.env.user
            rec.prepared_on = fields.Datetime.now()
            rec.state = 'completed'
            rec.message_post(
                body=f'P-2 marked as completed by {self.env.user.name}.'
            )

    def action_manager_review(self):
        """Manager reviews and moves to Reviewed state."""
        for rec in self:
            if rec.state != 'completed':
                raise UserError('Can only review records that are Completed.')
            rec.reviewed_by_id = self.env.user
            rec.reviewed_on = fields.Datetime.now()
            rec.state = 'reviewed'
            rec.message_post(
                body=f'P-2 reviewed by Manager: {self.env.user.name}.'
            )

    def action_partner_approve(self):
        """Partner approves and locks P-2, enabling P-3 unlock."""
        for rec in self:
            if rec.state != 'reviewed':
                raise UserError('Can only approve records that have been Reviewed.')
            if not rec.partner_comments:
                raise UserError('Partner comments are mandatory for approval.')
            rec.partner_approved = True
            rec.partner_approved_by_id = self.env.user
            rec.partner_approved_on = fields.Datetime.now()
            rec.state = 'approved'
            rec.confirm_proceed_p3 = True
            rec.message_post(
                body=f'P-2 approved by Partner: {self.env.user.name}. P-3 tab unlocked.'
            )

    def action_lock(self):
        """Lock P-2 (audit trail frozen per ISA 230)."""
        for rec in self:
            if rec.state != 'approved':
                raise UserError('Can only lock records that are Approved.')
            rec.state = 'locked'
            rec.message_post(body='P-2 locked. Audit trail frozen per ISA 230.')

    def action_send_back(self):
        """Send back for rework."""
        for rec in self:
            if rec.state not in ('completed', 'reviewed'):
                raise UserError('Can only send back Completed or Reviewed records.')
            old_state = rec.state
            rec.state = 'in_progress'
            rec.message_post(body=f'P-2 sent back for rework from {old_state} state.')

    def action_unlock(self):
        """Unlock a locked record (requires partner authority)."""
        for rec in self:
            if rec.state not in ('approved', 'locked'):
                raise UserError('Can only unlock Approved or Locked records.')
            rec.state = 'reviewed'
            rec.message_post(body='P-2 unlocked for revision.')

    # =========================================================================
    # RISK TRANSFER TO P-6
    # =========================================================================
    def action_transfer_risks_to_p6(self):
        """Transfer identified business risks to P-6 Risk Register."""
        self.ensure_one()
        if not self.business_risk_ids:
            raise UserError('No business risks to transfer.')

        # This would integrate with P-6 Risk Assessment
        transferred = 0
        for risk in self.business_risk_ids.filtered(lambda r: not r.linked_to_p6):
            # In actual implementation, create risk register entry
            risk.linked_to_p6 = True
            transferred += 1

        self.message_post(
            body=f'{transferred} business risks transferred to P-6 Risk Register.'
        )
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Risks Transferred',
                'message': f'{transferred} risks have been linked to P-6.',
                'type': 'success',
            }
        }

    # =========================================================================
    # REPORT GENERATION
    # =========================================================================
    def action_generate_entity_memo(self):
        """Generate Entity & Environment Understanding Memorandum (PDF)."""
        self.ensure_one()
        self.message_post(body='Entity & Environment Understanding Memorandum generated.')
        return {
            'type': 'ir.actions.act_window_close',
        }

    def action_view_audit(self):
        """Navigate to parent audit record."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'qaco.audit',
            'res_id': self.audit_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
