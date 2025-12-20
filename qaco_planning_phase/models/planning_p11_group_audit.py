# -*- coding: utf-8 -*-
"""
P-11: Group Audit Planning - COMPLETE ISA 600 (Revised) Implementation
Standard: ISA 600 (Revised), ISA 315, ISA 330, ISA 220, ISA 240, ISA 570, ISQM-1
Purpose: Plan group audit strategy with comprehensive component assessment
Compliance: Companies Act 2017, ICAP QCR, AOB inspection framework
"""

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class PlanningP11GroupAudit(models.Model):
    """P-11: Group Audit Planning (ISA 600 Revised) - MASTER MODEL"""
    _name = 'qaco.planning.p11.group.audit'
    _description = 'P-11: Group Audit Planning (ISA 600)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'engagement_id'
    _order = 'id desc'

    # ============================================================================
    # CORE IDENTIFIERS
    # ============================================================================
    # Standard parent linkage (for qaco.planning.main orchestration)
    audit_id = fields.Many2one(
        'qaco.audit',
        string='Audit Engagement',
        required=True,
        ondelete='cascade',
        tracking=True,
        index=True,
        help='Primary link to audit engagement (standard field)'
    )
    planning_main_id = fields.Many2one(
        'qaco.planning.main',
        string='Planning Phase',
        ondelete='cascade',
        index=True,
        help='Link to planning orchestrator'
    )
    
    # Legacy fields (kept for backward compatibility)
    engagement_id = fields.Many2one(
        'qaco.audit',
        string='Legacy Engagement ID',
        compute='_compute_engagement_id',
        store=True,
        readonly=True,
        help='Computed from audit_id for backward compatibility'
    )
    name = fields.Char(
        string='Name',
        compute='_compute_name',
        store=True,
        readonly=True,
        help='Display name computed from engagement'
    )
    audit_year_id = fields.Many2one(
        'audit.year',
        string='Audit Year',
        tracking=True,
        help='Optional: Audit year reference'
    )
    client_id = fields.Many2one(
        'res.partner',
        string='Client',
        related='audit_id.client_id',
        store=True,
        readonly=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Engagement Partner',
        tracking=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self._get_default_currency()
    )
    
    # STATE MANAGEMENT
    state = fields.Selection([
        ('draft', 'Draft'),
        ('review', 'Manager Review'),
        ('partner', 'Partner Approval'),
        ('locked', 'Locked'),
    ], default='draft', tracking=True, copy=False)

    # Sequential Gating (ISA 300/220: Systematic Planning Approach)
    can_open = fields.Boolean(
        string='Can Open This Tab',
        compute='_compute_can_open',
        store=False,
        help='P-11 can only be opened after P-10 is approved'
    )

    @api.depends('audit_id')
    def _compute_can_open(self):
        """P-11 requires P-10 to be approved."""
        for rec in self:
            if not rec.audit_id:
                rec.can_open = False
                continue
            # Find P-10 for this audit
            p10 = self.env['qaco.planning.p10.related.parties'].search([
                ('audit_id', '=', rec.audit_id.id)
            ], limit=1)
            rec.can_open = p10.state == 'approved' if p10 else False

    @api.constrains('state')
    def _check_sequential_gating(self):
        """ISA 300/220: Enforce sequential planning approach."""
        for rec in self:
            if rec.state != 'draft' and not rec.can_open:
                raise UserError(
                    'ISA 300/220 & ISA 600 Violation: Sequential Planning Approach Required.\n\n'
                    'P-11 (Group Audit Considerations) cannot be started until P-10 (Related Parties) '
                    'has been Partner-approved.\n\n'
                    'Reason: Group audit scoping per ISA 600 requires complete related party '
                    'identification and understanding from P-10.\n\n'
                    'Action: Please complete and obtain Partner approval for P-10 first.'
                )

    # ============================================================================
    # SECTION A: DETERMINATION OF GROUP AUDIT APPLICABILITY
    # ============================================================================
    is_group_audit = fields.Boolean(
        string='Involves Group Financial Statements?',
        tracking=True,
        help='Does the engagement involve group financial statements per ISA 600.16?'
    )
    basis_of_consolidation = fields.Selection([
        ('subsidiary', 'Subsidiary'),
        ('associate', 'Associate'),
        ('joint_venture', 'Joint Venture'),
        ('branch', 'Branch'),
        ('multiple', 'Multiple Types'),
    ], string='Basis of Consolidation', tracking=True)
    
    reporting_framework = fields.Selection([
        ('ifrs', 'IFRS'),
        ('ifrs_sme', 'IFRS for SMEs'),
        ('other', 'Other Framework'),
    ], string='Reporting Framework', tracking=True)
    
    basis_for_conclusion = fields.Html(
        string='Basis for Group Audit Determination',
        required=True,
        help='Document the conclusion on whether this is a group audit (ISA 600.16-18)'
    )
    not_applicable_rationale = fields.Html(
        string='Rationale if Not Group Audit',
        help='Document why group audit considerations do not apply'
    )

    # ============================================================================
    # SECTION B: IDENTIFICATION OF COMPONENTS
    # ============================================================================
    component_ids = fields.One2many(
        'qaco.planning.p11.component',
        'p11_id',
        string='Components',
        tracking=True
    )
    total_component_count = fields.Integer(
        string='Total Components',
        compute='_compute_component_metrics',
        store=True
    )
    significant_component_count = fields.Integer(
        string='Significant Components',
        compute='_compute_component_metrics',
        store=True
    )
    component_count = fields.Integer(
        string='Component Count',
        compute='_compute_component_count',
        store=True,
        help='Alias for total_component_count for view compatibility'
    )
    
    # ============================================================================
    # SECTION C: COMPONENT RISK ASSESSMENT
    # ============================================================================
    component_risk_ids = fields.One2many(
        'qaco.planning.p11.component.risk',
        'p11_id',
        string='Component Risks',
        help='Risk assessment per component (ISA 600.27-31)'
    )
    significant_components_identified = fields.Boolean(
        string='Significant Financial Components Identified?',
        tracking=True
    )
    significant_risk_components_identified = fields.Boolean(
        string='Components with Significant Risks Identified?',
        tracking=True
    )
    component_risk_narrative = fields.Html(
        string='Component Risk Assessment Narrative',
        help='Overall assessment of risk profile across components'
    )
    
    # Significance Assessment HTML Fields (for view display)
    significance_criteria = fields.Html(
        string='Significance Criteria',
        compute='_compute_significance_assessment',
        store=True,
        help='HTML summary of significance criteria used'
    )
    significant_components = fields.Html(
        string='Significant Components',
        compute='_compute_significance_assessment',
        store=True,
        help='HTML list of significant components'
    )
    non_significant_components = fields.Html(
        string='Non-Significant Components',
        compute='_compute_significance_assessment',
        store=True,
        help='HTML list of non-significant components'
    )
    coverage_assessment = fields.Html(
        string='Coverage Assessment',
        compute='_compute_significance_assessment',
        store=True,
        help='HTML assessment of audit coverage across components'
    )

    # ============================================================================
    # SECTION D: COMPONENT AUDITOR EVALUATION
    # ============================================================================
    component_auditor_ids = fields.One2many(
        'qaco.planning.p11.component.auditor',
        'p11_id',
        string='Component Auditors',
        help='Evaluation of component auditors (ISA 600.19-26)'
    )
    component_auditors_involved = fields.Boolean(
        string='Component Auditors Involved?',
        compute='_compute_component_auditor_involvement',
        store=True
    )
    independence_confirmed_all = fields.Boolean(
        string='All Component Auditors Independence Confirmed?',
        compute='_compute_auditor_confirmations',
        store=True
    )
    competence_confirmed_all = fields.Boolean(
        string='All Component Auditors Competence Confirmed?',
        compute='_compute_auditor_confirmations',
        store=True
    )
    escalation_required = fields.Boolean(
        string='Partner Escalation Required',
        compute='_compute_auditor_confirmations',
        store=True,
        help='Set if any component auditor lacks independence or competence'
    )

    # ============================================================================
    # SECTION E: SCOPE OF WORK AT COMPONENT LEVEL
    # ============================================================================
    scope_determination_basis = fields.Html(
        string='Basis for Scope Determination',
        help='Document how scope was determined for each component (ISA 600.32-34)'
    )
    group_team_involvement_planned = fields.Boolean(
        string='Group Audit Team Involvement Planned?',
        tracking=True
    )
    involvement_details = fields.Html(
        string='Details of Group Team Involvement',
        help='Nature and extent of group team involvement in component work'
    )

    # ============================================================================
    # SECTION F: GROUP-WIDE RISKS & RESPONSES
    # ============================================================================
    group_wide_risks = fields.Html(
        string='Group-Wide Risks Identified',
        help='Risks that affect the group as a whole (ISA 600.35-37)'
    )
    fraud_risks_group_level = fields.Boolean(
        string='Fraud Risks at Group Level?',
        tracking=True,
        help='Link to P-7 (ISA 240)'
    )
    fraud_risk_details = fields.Html(
        string='Group-Level Fraud Risk Details'
    )
    going_concern_risks_group = fields.Boolean(
        string='Going Concern Risks from Group Structure?',
        tracking=True,
        help='Link to P-8 (ISA 570)'
    )
    going_concern_details = fields.Html(
        string='Group Going Concern Risk Details'
    )
    planned_group_responses = fields.Html(
        string='Planned Group-Wide Responses',
        required=True,
        help='Audit responses at group level (ISA 600.35)'
    )
    
    # Links to other planning phases
    p6_risk_ids = fields.Many2many(
        'qaco.planning.p6.risk.line',
        'p11_p6_risk_rel',
        'p11_id',
        'risk_id',
        string='Linked P-6 Risks',
        help='Auto-link group-wide risks to P-6 RMM'
    )
    p7_fraud_ids = fields.Many2many(
        'qaco.planning.p7.fraud.line',
        'p11_p7_fraud_rel',
        'p11_id',
        'fraud_id',
        string='Linked P-7 Fraud Risks'
    )

    # ============================================================================
    # SECTION G: COMMUNICATION WITH COMPONENT AUDITORS (ISA 600 CORE)
    # ============================================================================
    instructions_issued = fields.Boolean(
        string='Instructions Issued to Component Auditors?',
        tracking=True,
        help='ISA 600.40 requirement'
    )
    instructions_date = fields.Date(
        string='Instructions Issue Date'
    )
    areas_of_special_focus = fields.Html(
        string='Areas of Special Focus Communicated',
        help='Specific areas requiring component auditor attention'
    )
    materiality_thresholds_communicated = fields.Boolean(
        string='Materiality & Reporting Thresholds Communicated?',
        tracking=True
    )
    component_materiality_threshold = fields.Monetary(
        string='Component Materiality Threshold',
        currency_field='currency_id'
    )
    reporting_threshold_amount = fields.Monetary(
        string='Reporting Threshold',
        currency_field='currency_id',
        help='Threshold above which misstatements must be communicated'
    )
    timelines_agreed = fields.Boolean(
        string='Timelines Agreed with Component Auditors?',
        tracking=True
    )
    timeline_details = fields.Html(
        string='Timeline & Deadline Details'
    )
    instructions_documented = fields.Boolean(
        string='Instructions Documented?',
        help='Checklist: Instructions formally documented'
    )
    two_way_communication_planned = fields.Boolean(
        string='Two-Way Communication Planned?',
        help='Checklist: Ongoing communication mechanism established'
    )

    # ============================================================================
    # SECTION H: SUPERVISION, REVIEW & QUALITY MANAGEMENT
    # ============================================================================
    nature_of_involvement = fields.Selection([
        ('planning', 'Planning Only'),
        ('review', 'Review of Work'),
        ('onsite', 'On-Site Visits'),
        ('all', 'Planning, Review & On-Site'),
    ], string='Nature of Group Auditor Involvement', tracking=True)
    
    review_procedures_planned = fields.Html(
        string='Review Procedures Planned',
        help='Specific procedures to review component auditor work (ISA 600.42-44)'
    )
    quality_management_considerations = fields.Html(
        string='Quality Management Considerations',
        required=True,
        help='ISQM-1 and ISA 220 considerations for group audit'
    )
    high_risk_supervision = fields.Html(
        string='Enhanced Supervision for High-Risk Components',
        help='Additional supervision for components with significant risks'
    )
    site_visits_planned = fields.Boolean(
        string='Site Visits Planned?',
        tracking=True
    )
    site_visit_schedule = fields.Html(
        string='Site Visit Schedule & Details'
    )

    # ============================================================================
    # SECTION I: CONSOLIDATION PROCESS UNDERSTANDING
    # ============================================================================
    consolidation_adjustments_reviewed = fields.Boolean(
        string='Consolidation Adjustments Reviewed?',
        tracking=True
    )
    consolidation_review_notes = fields.Html(
        string='Consolidation Review Notes'
    )
    intercompany_eliminations_understood = fields.Boolean(
        string='Inter-Company Eliminations Understood?',
        tracking=True
    )
    elimination_details = fields.Html(
        string='Inter-Company Elimination Details'
    )
    uniform_policies_confirmed = fields.Boolean(
        string='Uniform Accounting Policies Confirmed?',
        tracking=True
    )
    policy_differences = fields.Html(
        string='Accounting Policy Differences Identified'
    )
    foreign_currency_issues = fields.Boolean(
        string='Foreign Currency Translation Issues?',
        tracking=True
    )
    currency_translation_details = fields.Html(
        string='Currency Translation Details'
    )

    # ============================================================================
    # SECTION J: MANDATORY DOCUMENT UPLOADS
    # ============================================================================
    group_structure_overview = fields.Html(
        string='Group Structure Overview',
        help='HTML description of the group structure and relationships'
    )
    group_chart = fields.Html(
        string='Group Chart',
        help='Visual representation of group structure in HTML format'
    )
    consolidation_process = fields.Html(
        string='Consolidation Process',
        help='Description of the consolidation process and procedures'
    )
    group_structure_attachments = fields.Many2many(
        'ir.attachment',
        'p11_group_structure_rel',
        'p11_id',
        'attachment_id',
        string='Group Structure / Organogram',
        help='Upload visual representation of group structure'
    )
    component_instructions_attachments = fields.Many2many(
        'ir.attachment',
        'p11_instructions_rel',
        'p11_id',
        'attachment_id',
        string='Component Auditor Instructions',
        help='Upload formal instructions issued to component auditors'
    )
    component_confirmations_attachments = fields.Many2many(
        'ir.attachment',
        'p11_confirmations_rel',
        'p11_id',
        'attachment_id',
        string='Component Auditor Confirmations',
        help='Independence and competence confirmations'
    )
    consolidation_workings_attachments = fields.Many2many(
        'ir.attachment',
        'p11_consolidation_rel',
        'p11_id',
        'attachment_id',
        string='Consolidation Workings',
        help='Upload consolidation schedules and workings'
    )
    prior_year_documentation_attachments = fields.Many2many(
        'ir.attachment',
        'p11_prior_year_rel',
        'p11_id',
        'attachment_id',
        string='Prior-Year Group Audit Documentation',
        help='Reference to prior year group audit files'
    )

    # ============================================================================
    # SECTION K: P-11 CONCLUSION & PROFESSIONAL JUDGMENT
    # ============================================================================
    conclusion_narrative = fields.Html(
        string='P-11 Conclusion',
        required=True,
        help='Mandatory professional judgment conclusion per ISA 600'
    )
    group_planning_completed = fields.Boolean(
        string='Group Audit Planning Completed?',
        help='Final confirmation: Group audit planning is complete'
    )
    component_risks_addressed = fields.Boolean(
        string='Component Risks Appropriately Addressed?',
        help='Final confirmation: All component risks have responses'
    )
    basis_established_strategy = fields.Boolean(
        string='Basis Established for Group Audit Strategy?',
        help='Final confirmation: Strategy is documented and defensible'
    )

    # ============================================================================
    # SECTION L: REVIEW, APPROVAL & LOCK
    # ============================================================================
    prepared_by = fields.Many2one(
        'res.users',
        string='Prepared By',
        tracking=True,
        readonly=True
    )
    prepared_by_role = fields.Char(
        string='Role',
        compute='_compute_preparer_role',
        store=True
    )
    prepared_on = fields.Datetime(
        string='Prepared On',
        readonly=True
    )
    
    reviewed_by = fields.Many2one(
        'res.users',
        string='Reviewed By (Manager)',
        tracking=True,
        readonly=True
    )
    reviewed_on = fields.Datetime(
        string='Reviewed On',
        readonly=True
    )
    review_notes = fields.Html(
        string='Manager Review Notes',
        help='Manager must document review findings'
    )
    
    partner_approved = fields.Boolean(
        string='Partner Approval',
        tracking=True,
        readonly=True,
        copy=False
    )
    partner_approved_by = fields.Many2one(
        'res.users',
        string='Partner Approved By',
        tracking=True,
        readonly=True
    )
    partner_approved_on = fields.Datetime(
        string='Partner Approved On',
        readonly=True
    )
    partner_comments = fields.Html(
        string='Partner Comments',
        help='MANDATORY: Partner must provide substantive comments'
    )
    
    locked = fields.Boolean(
        string='Locked',
        compute='_compute_locked',
        store=True,
        help='P-11 is locked when partner-approved'
    )
    
    # Audit trail
    version_history = fields.Text(
        string='Version History',
        readonly=True,
        help='ISO 230: Full audit trail preserved'
    )
    reviewer_timestamps = fields.Text(
        string='Reviewer Timestamps',
        readonly=True
    )

    # ISA Reference
    isa_reference = fields.Char(
        string='ISA Reference',
        default='ISA 600 (Revised), ISA 315, ISA 330, ISA 220, ISQM-1',
        readonly=True
    )

    # ============================================================================
    # SQL CONSTRAINTS
    # ============================================================================
    _sql_constraints = [
        ('engagement_unique', 'UNIQUE(audit_id)', 
         'Only one P-11 record per audit engagement is allowed.')
    ]

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends('audit_id')
    @api.depends('audit_id')
    def _compute_engagement_id(self):
        """Compute engagement_id from audit_id for backward compatibility."""
        for rec in self:
            # Map qaco.audit to audit.engagement if needed
            rec.engagement_id = rec.audit_id.id if rec.audit_id else False

    @api.depends('engagement_id')
    def _compute_name(self):
        """Compute display name from engagement."""
        for rec in self:
            if rec.engagement_id:
                rec.name = f"P-11: {rec.engagement_id.name}"
            else:
                rec.name = "P-11: Group Audit Planning"
    
    @api.depends('component_ids', 'component_ids.is_significant')
    def _compute_component_metrics(self):
        """Defensive: Safe even during module install."""
        for rec in self:
            try:
                if not rec.component_ids:
                    rec.total_component_count = 0
                    rec.significant_component_count = 0
                    continue
                
                rec.total_component_count = len(rec.component_ids)
                rec.significant_component_count = len(
                    rec.component_ids.filtered(lambda c: c.is_significant)
                )
            except Exception as e:
                _logger.warning(f'P-11 _compute_component_metrics failed for record {rec.id}: {e}')
                rec.total_component_count = 0
                rec.significant_component_count = 0

    @api.depends('total_component_count')
    def _compute_component_count(self):
        """Alias for total_component_count for view compatibility."""
        for rec in self:
            rec.component_count = rec.total_component_count

    @api.depends('component_ids', 'component_ids.is_significant', 'component_ids.component_name', 
                 'component_ids.percentage_group_assets', 'component_ids.percentage_group_revenue')
    def _compute_significance_assessment(self):
        """Generate HTML summaries for significance assessment display."""
        for rec in self:
            try:
                # Significance Criteria
                rec.significance_criteria = f"""
                <div class="significance-criteria">
                    <h5>Financial Significance Thresholds (ISA 600.7)</h5>
                    <ul>
                        <li>Assets: Components ≥ 10% of group total assets</li>
                        <li>Revenue: Components ≥ 10% of group total revenue</li>
                        <li>Additional factors: Risk profile, complexity, regulatory requirements</li>
                    </ul>
                </div>
                """
                
                if not rec.component_ids:
                    rec.significant_components = "<p>No components defined yet.</p>"
                    rec.non_significant_components = "<p>No components defined yet.</p>"
                    rec.coverage_assessment = "<p>Cannot assess coverage without component definitions.</p>"
                    continue
                
                # Significant Components
                significant_comps = rec.component_ids.filtered(lambda c: c.is_significant)
                if significant_comps:
                    sig_html = "<div class='significant-components'><h5>Significant Components Requiring Full Audit Coverage:</h5><ul>"
                    for comp in significant_comps:
                        sig_html += f"<li><strong>{comp.component_name}</strong> - Assets: {comp.percentage_group_assets}%, Revenue: {comp.percentage_group_revenue}%</li>"
                    sig_html += "</ul></div>"
                    rec.significant_components = sig_html
                else:
                    rec.significant_components = "<p>No significant components identified.</p>"
                
                # Non-Significant Components
                non_sig_comps = rec.component_ids.filtered(lambda c: not c.is_significant)
                if non_sig_comps:
                    non_sig_html = "<div class='non-significant-components'><h5>Non-Significant Components:</h5><ul>"
                    for comp in non_sig_comps:
                        non_sig_html += f"<li><strong>{comp.component_name}</strong> - Assets: {comp.percentage_group_assets}%, Revenue: {comp.percentage_group_revenue}%</li>"
                    non_sig_html += "</ul></div>"
                    rec.non_significant_components = non_sig_html
                else:
                    rec.non_significant_components = "<p>All components are significant.</p>"
                
                # Coverage Assessment
                total_comps = len(rec.component_ids)
                sig_count = len(significant_comps)
                coverage_pct = (sig_count / total_comps * 100) if total_comps > 0 else 0
                
                rec.coverage_assessment = f"""
                <div class="coverage-assessment">
                    <h5>Audit Coverage Assessment</h5>
                    <p><strong>Total Components:</strong> {total_comps}</p>
                    <p><strong>Significant Components:</strong> {sig_count} ({coverage_pct:.1f}%)</p>
                    <p><strong>Coverage Status:</strong> {'Full audit coverage required' if sig_count > 0 else 'No full audit coverage required'}</p>
                    <p><em>ISA 600.32-34: Scope determination based on significance and risk assessment</em></p>
                </div>
                """
                
            except Exception as e:
                _logger.warning(f'P-11 _compute_significance_assessment failed for record {rec.id}: {e}')
                rec.significance_criteria = "<p>Error generating significance criteria.</p>"
                rec.significant_components = "<p>Error generating significant components list.</p>"
                rec.non_significant_components = "<p>Error generating non-significant components list.</p>"
                rec.coverage_assessment = "<p>Error generating coverage assessment.</p>"

    @api.depends('component_auditor_ids')
    def _compute_component_auditor_involvement(self):
        """Defensive: Safe even during module install."""
        for rec in self:
            try:
                rec.component_auditors_involved = bool(rec.component_auditor_ids)
            except Exception as e:
                _logger.warning(f'P-11 _compute_component_auditor_involvement failed for record {rec.id}: {e}')
                rec.component_auditors_involved = False

    @api.depends('component_auditor_ids.independence_confirmed',
                 'component_auditor_ids.competence_adequate')
    def _compute_auditor_confirmations(self):
        """Defensive: Safe even during module install."""
        for rec in self:
            try:
                auditors = rec.component_auditor_ids
                if not auditors:
                    rec.independence_confirmed_all = False
                    rec.competence_confirmed_all = False
                    rec.escalation_required = False
                    continue
                
                rec.independence_confirmed_all = all(
                    a.independence_confirmed for a in auditors
                )
                rec.competence_confirmed_all = all(
                    a.competence_adequate for a in auditors
                )
                rec.escalation_required = (
                    not rec.independence_confirmed_all or 
                    not rec.competence_confirmed_all
                )
            except Exception as e:
                _logger.warning(f'P-11 _compute_auditor_confirmations failed for record {rec.id}: {e}')
                rec.independence_confirmed_all = False
                rec.competence_confirmed_all = False
                rec.escalation_required = False

    @api.depends('prepared_by')
    def _compute_preparer_role(self):
        for rec in self:
            if rec.prepared_by:
                # Attempt to determine role from groups
                if rec.prepared_by.has_group('qaco_audit.group_audit_partner'):
                    rec.prepared_by_role = 'Partner'
                elif rec.prepared_by.has_group('qaco_audit.group_audit_manager'):
                    rec.prepared_by_role = 'Manager'
                else:
                    rec.prepared_by_role = 'Senior/Trainee'
            else:
                rec.prepared_by_role = ''

    @api.depends('partner_approved')
    def _compute_locked(self):
        for rec in self:
            rec.locked = rec.partner_approved

    def _default_conclusion_narrative(self):
        return """
        <p><strong>P-11: Group Audit Planning Conclusion</strong></p>
        <p>Group components have been identified and assessed in accordance with ISA 600 (Revised). 
        Component auditors' competence and independence have been evaluated, appropriate scope and 
        responses determined, and communication and supervision procedures established.</p>
        <p><strong>Key Determinations:</strong></p>
        <ul>
            <li>Group audit applicability confirmed</li>
            <li>Significant components identified based on financial significance and risk</li>
            <li>Component auditor evaluations completed</li>
            <li>Group-wide risks linked to P-6 and P-7</li>
            <li>Communication and supervision framework established</li>
        </ul>
        """

    @api.model_create_multi
    def create(self, vals_list):
        """PROMPT 3: Set HTML defaults safely in create() instead of field defaults."""
        for vals in vals_list:
            if 'conclusion_narrative' not in vals:
                vals['conclusion_narrative'] = self._default_conclusion_narrative()
        return super().create(vals_list)

    # ============================================================================
    # VALIDATION & CONSTRAINTS
    # ============================================================================
    @api.constrains('component_ids', 'is_group_audit')
    def _check_components_if_group_audit(self):
        for rec in self:
            if rec.is_group_audit and not rec.component_ids:
                raise ValidationError(
                    _('If this is a group audit, you must identify at least one component.')
                )

    @api.constrains('component_auditor_ids', 'component_auditors_involved')
    def _check_component_auditor_completeness(self):
        for rec in self:
            if rec.component_auditors_involved and not rec.component_auditor_ids:
                raise ValidationError(
                    _('Component auditors are involved but none have been registered. '
                      'Please add component auditor details.')
                )

    @api.constrains('escalation_required', 'state')
    def _check_escalation_before_approval(self):
        for rec in self:
            if rec.escalation_required and rec.state in ['partner', 'locked']:
                raise ValidationError(
                    _('Partner escalation is required due to component auditor independence '
                      'or competence concerns. Cannot proceed to approval without resolution.')
                )

    # ============================================================================
    # PRE-CONDITIONS ENFORCEMENT
    # ============================================================================
    def _check_preconditions(self):
        """
        System-enforced pre-conditions:
        - P-10 (Related Parties) must be partner-approved and locked
        - P-6 (Risk Assessment) must be finalized
        - P-2 (Entity & group structure) must be completed
        """
        self.ensure_one()
        errors = []

        # Check P-10
        p10 = self.env['qaco.planning.p10.related.parties'].search([
            ('engagement_id', '=', self.engagement_id.id),
            ('audit_year_id', '=', self.audit_year_id.id),
        ], limit=1)
        if not p10 or p10.state != 'locked':
            errors.append('P-10 (Related Parties Planning) must be partner-approved and locked.')

        # Check P-6
        p6 = self.env['qaco.planning.p6.risk'].search([
            ('engagement_id', '=', self.engagement_id.id),
            ('audit_year_id', '=', self.audit_year_id.id),
        ], limit=1)
        if not p6 or p6.state not in ['partner', 'locked']:
            errors.append('P-6 (Risk Assessment) must be finalized.')

        # Check P-2
        p2 = self.env['qaco.planning.p2.entity'].search([
            ('engagement_id', '=', self.engagement_id.id),
            ('audit_year_id', '=', self.audit_year_id.id),
        ], limit=1)
        if not p2 or p2.state not in ['partner', 'locked']:
            errors.append('P-2 (Understanding Entity & Group Structure) must be completed.')

        if errors:
            raise UserError(
                _('P-11 Pre-Conditions Not Met:\n\n') + '\n'.join(['• ' + e for e in errors])
            )

    @api.model
    def create(self, vals):
        rec = super(AuditPlanningP11GroupAudit, self).create(vals)
        rec._check_preconditions()
        rec._log_version('Created')
        return rec

    def write(self, vals):
        result = super(AuditPlanningP11GroupAudit, self).write(vals)
        if any(key in vals for key in ['state', 'partner_approved']):
            self._log_version(f"Updated: {vals.get('state', 'state change')}")
        return result

    def _log_version(self, action):
        """Maintain audit trail per ISA 230"""
        for rec in self:
            timestamp = fields.Datetime.now()
            user = self.env.user.name
            log_entry = f"{timestamp} | {user} | {action}\n"
            rec.version_history = (rec.version_history or '') + log_entry

    # ============================================================================
    # MANDATORY FIELD VALIDATION
    # ============================================================================
    def _validate_mandatory_fields(self):
        """Validate all mandatory fields before progression"""
        self.ensure_one()
        errors = []

        # Section A
        if not self.basis_for_conclusion:
            errors.append('Section A: Basis for group audit determination is required')
        
        if self.is_group_audit:
            # Section B
            if not self.component_ids:
                errors.append('Section B: At least one component must be identified')
            
            # Section C
            if not self.component_risk_narrative:
                errors.append('Section C: Component risk assessment narrative is required')
            
            # Section E
            if not self.scope_determination_basis:
                errors.append('Section E: Basis for scope determination is required')
            
            # Section F
            if not self.planned_group_responses:
                errors.append('Section F: Planned group-wide responses are required')
            
            # Section G
            if not self.instructions_documented:
                errors.append('Section G: Component auditor instructions must be documented')
            
            # Section H
            if not self.quality_management_considerations:
                errors.append('Section H: Quality management considerations are required')
            
            # Section I
            if not self.consolidation_adjustments_reviewed:
                errors.append('Section I: Consolidation process review is required')
            
            # Section J - Attachments
            if not self.group_structure_attachments:
                errors.append('Section J: Group structure/organogram attachment is required')
            if self.component_auditors_involved and not self.component_instructions_attachments:
                errors.append('Section J: Component auditor instructions must be uploaded')
            
            # Section K
            if not self.group_planning_completed:
                errors.append('Section K: Confirm group audit planning is completed')
            if not self.component_risks_addressed:
                errors.append('Section K: Confirm component risks are addressed')
            if not self.basis_established_strategy:
                errors.append('Section K: Confirm basis for group strategy is established')
        
        else:
            # Not a group audit
            if not self.not_applicable_rationale:
                errors.append('Section A: Rationale for non-applicability is required')

        if errors:
            raise UserError(
                _('Cannot progress P-11. Missing requirements:\n\n') + 
                '\n'.join(['• ' + e for e in errors])
            )

    # ============================================================================
    # STATE MANAGEMENT ACTIONS
    # ============================================================================
    def action_start_work(self):
        """Start work on P-11 tab."""
        for rec in self:
            if rec.state != 'not_started':
                raise UserError("Can only start work on tabs that are 'Not Started'.")
            # Check prerequisites if needed
            rec.state = 'in_progress'
            rec.message_post(body="P-11 Group Audit work started.")

    def action_complete(self):
        """Mark P-11 as complete."""
        for rec in self:
            if rec.state != 'in_progress':
                raise UserError("Can only complete tabs that are 'In Progress'.")
            rec.state = 'completed'
            rec.message_post(body="P-11 Group Audit marked as complete.")

    def action_mark_complete(self):
        """Senior marks P-11 as complete"""
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Can only mark complete from Draft state.'))
            rec._validate_mandatory_fields()
            rec.write({
                'prepared_by': self.env.user.id,
                'prepared_on': fields.Datetime.now(),
                'state': 'review',
            })
            rec.message_post(body=_('P-11 marked complete and submitted for manager review.'))

    def action_manager_review(self):
        """Manager reviews and approves P-11"""
        for rec in self:
            if rec.state != 'review':
                raise UserError(_('Can only review from Review state.'))
            if not rec.review_notes:
                raise UserError(_('Manager review notes are mandatory.'))
            rec.write({
                'reviewed_by': self.env.user.id,
                'reviewed_on': fields.Datetime.now(),
                'state': 'partner',
            })
            rec.message_post(body=_('P-11 reviewed by manager and forwarded to partner.'))

    def action_partner_approve(self):
        """Partner approves and locks P-11"""
        for rec in self:
            if rec.state != 'partner':
                raise UserError(_('Can only approve from Partner state.'))
            if not rec.partner_comments:
                raise UserError(_('Partner comments are MANDATORY per ISA 220.'))
            if rec.escalation_required:
                raise UserError(
                    _('Cannot approve: Component auditor independence or competence '
                      'issues require resolution.')
                )
            rec.write({
                'partner_approved': True,
                'partner_approved_by': self.env.user.id,
                'partner_approved_on': fields.Datetime.now(),
                'state': 'locked',
            })
            rec.message_post(body=_('P-11 approved by partner and locked. P-12 is now unlocked.'))
            rec._unlock_p12()
            rec._auto_unlock_p12()

    def action_send_back(self):
        """Send back to draft for corrections"""
        for rec in self:
            if rec.state not in ['review', 'partner']:
                raise UserError(_('Can only send back from Review or Partner state.'))
            rec.state = 'draft'
            rec.message_post(body=_('P-11 sent back to draft for corrections.'))

    def action_partner_unlock(self):
        """Partner unlocks for amendments (exceptional)"""
        for rec in self:
            if rec.state != 'locked':
                raise UserError(_('Can only unlock from Locked state.'))
            if not self.env.user.has_group('qaco_audit.group_audit_partner'):
                raise UserError(_('Only partners can unlock P-11.'))
            rec.write({
                'partner_approved': False,
                'state': 'partner',
            })
            rec.message_post(body=_('P-11 unlocked by partner for amendment.'))

    def _unlock_p12(self):
        """Automatically unlock P-12 when P-11 is locked"""
        self.ensure_one()
        # This method will be called to signal P-12 can now be accessed
        # Implementation depends on P-12 gating logic
        self.message_post(
            body=_('P-11 locked successfully. P-12 (Audit Strategy & Plan) is now accessible.')
        )
    
    def _auto_unlock_p12(self):
        """Auto-unlock P-12 Audit Strategy when P-11 Group Audit is approved."""
        self.ensure_one()
        if not self.engagement_id:
            return
        
        # Find or create P-12 record
        P12 = self.env['qaco.planning.p12.strategy']
        p12_record = P12.search([('engagement_id', '=', self.engagement_id.id)], limit=1)
        
        if p12_record and p12_record.state == 'locked':
            p12_record.write({'state': 'draft'})
            p12_record.message_post(
                body='P-12 auto-unlocked after P-11 Group Audit approval.'
            )
            _logger.info(f'P-12 auto-unlocked for audit {self.engagement_id.id}')
        elif not p12_record:
            p12_record = P12.create({
                'engagement_id': self.engagement_id.id,
                'audit_year_id': self.audit_year_id.id,
                'partner_id': self.partner_id.id,
                'state': 'draft',
            })
            _logger.info(f'P-12 auto-created for audit {self.engagement_id.id}')


# ============================================================================
# CHILD MODEL: COMPONENTS
# ============================================================================
class PlanningP11Component(models.Model):
    """Component Register for Group Audit"""
    _name = 'qaco.planning.p11.component'
    _description = 'Group Audit Component'
    _order = 'is_significant desc, component_name'

    p11_id = fields.Many2one(
        'qaco.planning.p11.group.audit',
        string='P-11 Group Audit',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    # Component Identification
    component_name = fields.Char(
        string='Component Name',
        required=True,
        tracking=True
    )
    component_type = fields.Selection([
        ('subsidiary', 'Subsidiary'),
        ('associate', 'Associate'),
        ('joint_venture', 'Joint Venture'),
        ('branch', 'Branch'),
        ('other', 'Other'),
    ], string='Type', required=True)
    
    jurisdiction = fields.Char(
        string='Jurisdiction/Location',
        required=True
    )
    
    # Financial Significance (Section B)
    percentage_group_assets = fields.Float(
        string='% of Group Assets',
        digits=(5, 2),
        help='Percentage of total group assets'
    )
    percentage_group_revenue = fields.Float(
        string='% of Group Revenue',
        digits=(5, 2),
        help='Percentage of total group revenue'
    )
    is_significant = fields.Boolean(
        string='Financially Significant Component?',
        compute='_compute_financial_significance',
        store=True,
        help='Auto-computed based on materiality thresholds from P-5'
    )
    financial_significance_threshold = fields.Float(
        string='Significance Threshold (%)',
        default=10.0,
        help='Threshold percentage for financial significance (default 10%)'
    )
    
    # Risk Profile (Section C)
    has_significant_risks = fields.Boolean(
        string='Contains Significant Risks?',
        help='Does this component have significant risks (ISA 315)?'
    )
    risk_profile = fields.Selection([
        ('low', 'Low Risk'),
        ('moderate', 'Moderate Risk'),
        ('high', 'High Risk'),
    ], string='Risk Profile', required=True, default='moderate')
    
    risk_rationale = fields.Html(
        string='Risk Assessment Rationale',
        help='Explain why this component has this risk profile'
    )
    
    # Scope of Work (Section E)
    type_of_work = fields.Selection([
        ('full_audit', 'Full Scope Audit'),
        ('specified_procedures', 'Specified Audit Procedures'),
        ('review', 'Review'),
        ('analytical', 'Analytical Procedures Only'),
        ('no_work', 'No Work Required'),
    ], string='Type of Work', required=True)
    
    scope_basis = fields.Html(
        string='Basis for Scope Decision',
        help='Document why this scope was selected'
    )
    
    group_team_involvement = fields.Boolean(
        string='Group Audit Team Involvement?',
        help='Will the group audit team be involved in this component work?'
    )
    
    # Component Auditor
    component_auditor_id = fields.Many2one(
        'qaco.planning.p11.component.auditor',
        string='Component Auditor',
        help='Link to component auditor if applicable'
    )
    component_auditor_name = fields.Char(
        string='Component Auditor',
        help='Name of component auditor firm (if different from group auditor)'
    )
    
    # Materiality
    currency_id = fields.Many2one(
        'res.currency',
        related='p11_id.currency_id',
        store=True
    )
    component_materiality = fields.Monetary(
        string='Component Materiality',
        currency_field='currency_id',
        help='Materiality level for this component'
    )
    
    # Status & Reporting
    reporting_deadline = fields.Date(
        string='Reporting Deadline',
        help='Deadline for component work completion'
    )
    status = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ], string='Status', default='pending', tracking=True)
    
    notes = fields.Text(string='Notes')

    @api.depends('percentage_group_assets', 'percentage_group_revenue', 
                 'financial_significance_threshold')
    def _compute_financial_significance(self):
        """Auto-compute financial significance based on threshold"""
        for comp in self:
            threshold = comp.financial_significance_threshold or 10.0
            comp.is_significant = (
                comp.percentage_group_assets >= threshold or 
                comp.percentage_group_revenue >= threshold
            )

    @api.constrains('percentage_group_assets', 'percentage_group_revenue')
    def _check_percentages(self):
        for comp in self:
            if comp.percentage_group_assets < 0 or comp.percentage_group_assets > 100:
                raise ValidationError(_('Percentage of group assets must be between 0 and 100.'))
            if comp.percentage_group_revenue < 0 or comp.percentage_group_revenue > 100:
                raise ValidationError(_('Percentage of group revenue must be between 0 and 100.'))


# ============================================================================
# CHILD MODEL: COMPONENT RISKS
# ============================================================================
class PlanningP11ComponentRisk(models.Model):
    """Component-Level Risk Assessment"""
    _name = 'qaco.planning.p11.component.risk'
    _description = 'Component Risk Assessment'
    _order = 'risk_level desc, component_id'

    p11_id = fields.Many2one(
        'qaco.planning.p11.group.audit',
        string='P-11 Group Audit',
        required=True,
        ondelete='cascade',
        index=True
    )
    component_id = fields.Many2one(
        'qaco.planning.p11.component',
        string='Component',
        required=True,
        ondelete='cascade'
    )
    
    # Risk Details
    risk_description = fields.Html(
        string='Risk Description',
        required=True,
        help='Describe the specific risk at component level'
    )
    risk_level = fields.Selection([
        ('low', 'Low'),
        ('moderate', 'Moderate'),
        ('high', 'High'),
        ('significant', 'Significant Risk'),
    ], string='Risk Level', required=True, default='moderate')
    
    # Link to P-6 (RMM)
    p6_risk_id = fields.Many2one(
        'qaco.planning.p6.risk.line',
        string='Linked P-6 Risk',
        help='Link to group-level risk in P-6 Risk Assessment'
    )
    
    # Planned Response
    planned_response = fields.Html(
        string='Planned Audit Response',
        required=True,
        help='How will this risk be addressed? (ISA 330)'
    )
    response_responsibility = fields.Selection([
        ('group_team', 'Group Audit Team'),
        ('component_team', 'Component Audit Team'),
        ('both', 'Both Teams'),
    ], string='Response Responsibility', required=True)
    
    notes = fields.Text(string='Notes')


# ============================================================================
# CHILD MODEL: COMPONENT AUDITORS
# ============================================================================
class PlanningP11ComponentAuditor(models.Model):
    """Component Auditor Evaluation"""
    _name = 'qaco.planning.p11.component.auditor'
    _description = 'Component Auditor Assessment'
    _rec_name = 'auditor_name'
    _order = 'auditor_name'

    p11_id = fields.Many2one(
        'qaco.planning.p11.group.audit',
        string='P-11 Group Audit',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    # Auditor Identification (Section D)
    auditor_name = fields.Char(
        string='Auditor Name / Firm',
        required=True,
        tracking=True
    )
    firm_affiliation = fields.Char(
        string='Firm / Network Affiliation',
        help='E.g., network member, correspondent firm, independent'
    )
    jurisdiction = fields.Char(
        string='Jurisdiction',
        required=True,
        help='Country/location of component auditor'
    )
    
    # Independence Evaluation (ISA 600.19-20)
    independence_confirmed = fields.Boolean(
        string='Independence Confirmed?',
        tracking=True,
        help='Has component auditor confirmed independence per ISA 600.20?'
    )
    independence_confirmation_date = fields.Date(
        string='Independence Confirmation Date'
    )
    independence_notes = fields.Html(
        string='Independence Evaluation Notes'
    )
    
    # Competence & Resources (ISA 600.21-23)
    competence_adequate = fields.Boolean(
        string='Competence & Resources Adequate?',
        tracking=True,
        help='ISA 600.21: Professional competence and resources'
    )
    competence_basis = fields.Html(
        string='Basis for Competence Assessment',
        help='Document basis for competence determination'
    )
    
    # Regulatory Environment (ISA 600.24-26)
    regulatory_environment_assessed = fields.Boolean(
        string='Regulatory Environment Assessed?',
        tracking=True,
        help='ISA 600.25: Component auditor operates under appropriate regulatory environment'
    )
    regulatory_environment_notes = fields.Html(
        string='Regulatory Environment Details',
        help='Document the regulatory framework and any concerns'
    )
    
    # Communication & Access
    access_to_work_granted = fields.Boolean(
        string='Access to Work Granted?',
        help='Has component auditor granted unrestricted access to work papers?'
    )
    communication_protocol = fields.Html(
        string='Communication Protocol',
        help='Document the agreed communication mechanism'
    )
    
    # Escalation Flag
    escalation_flag = fields.Boolean(
        string='Escalation Required?',
        compute='_compute_escalation_flag',
        store=True,
        help='Automatically flagged if independence or competence not confirmed'
    )
    
    notes = fields.Text(string='Additional Notes')

    @api.depends('independence_confirmed', 'competence_adequate')
    def _compute_escalation_flag(self):
        for auditor in self:
            auditor.escalation_flag = (
                not auditor.independence_confirmed or 
                not auditor.competence_adequate
            )

    @api.constrains('independence_confirmed', 'competence_adequate')
    def _check_mandatory_confirmations(self):
        """Warn if confirmations missing"""
        for auditor in self:
            if auditor.p11_id.state in ['partner', 'locked']:
                if not auditor.independence_confirmed:
                    raise ValidationError(
                        _('Component auditor "%s": Independence must be confirmed before approval.') 
                        % auditor.auditor_name
                    )
                if not auditor.competence_adequate:
                    raise ValidationError(
                        _('Component auditor "%s": Competence must be confirmed before approval.') 
                        % auditor.auditor_name
                    )


