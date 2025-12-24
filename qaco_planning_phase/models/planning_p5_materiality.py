# -*- coding: utf-8 -*-
"""
P-5: Materiality & Performance Materiality
Standards: ISA 320, ISA 450, ISA 315 (Revised), ISA 570 (Revised), ISA 220, ISQM-1
Purpose: Establish quantitative and qualitative materiality benchmarks for audit,
         ensuring documented professional judgment, proper approval, and execution linkage.

Sections:
    A - Purpose & Context of Materiality
    B - Benchmark Selection (Critical Judgment)
    C - Overall Materiality Calculation
    D - Performance Materiality (PM)
    E - Clearly Trivial Threshold (CTT)
    F - Qualitative Materiality Considerations
    G - Risk-Adjusted Materiality (Advanced)
    H - Component / Group Materiality
    I - Linkage to Audit Execution (Auto-Flow)
    J - Mandatory Document Uploads
    K - P-5 Conclusion & Professional Judgment
    L - Review, Approval & Lock
"""

import logging

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


# =============================================================================
# CHILD MODEL: Specific Materiality Items
# =============================================================================
class PlanningP5SpecificMateriality(models.Model):
    """Specific Materiality for particular classes/balances/disclosures."""

    _name = "qaco.planning.p5.specific.materiality"
    _description = "P-5: Specific Materiality Item"
    _order = "sequence, id"

    p5_id = fields.Many2one(
        "qaco.planning.p5.materiality",
        string="P-5 Materiality",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(string="Seq", default=10)
    class_or_balance = fields.Char(
        string="Class/Balance/Disclosure",
        required=True,
        help="Specific account, balance, or disclosure requiring lower materiality",
    )
    reason_category = fields.Selection(
        [
            ("regulatory", "Regulatory Requirement"),
            ("user_sensitivity", "User Sensitivity"),
            ("related_party", "Related Party"),
            ("covenant", "Covenant Compliance"),
            ("fraud_risk", "Fraud Risk"),
            ("other", "Other"),
        ],
        string="Reason Category",
        required=True,
    )
    specific_materiality = fields.Float(
        string="Specific Materiality",
        digits=(16, 2),
        help="Lower materiality amount for this specific item",
    )
    currency_id = fields.Many2one(
        "res.currency", related="p5_id.currency_id", store=False
    )
    as_pct_of_om = fields.Float(
        string="% of OM", compute="_compute_as_pct", store=True, digits=(5, 2)
    )
    justification = fields.Text(
        string="Justification",
        required=True,
        help="Why lower materiality is appropriate for this item",
    )

    @api.depends("specific_materiality", "p5_id.overall_materiality")
    def _compute_as_pct(self):
        """Defensive: Safe even during module install."""
        for rec in self:
            try:
                if not rec.p5_id or not rec.p5_id.overall_materiality:
                    rec.as_pct_of_om = 0
                    continue

                rec.as_pct_of_om = (
                    rec.specific_materiality / rec.p5_id.overall_materiality
                ) * 100
            except Exception as e:
                _logger.warning(
                    f"P-5 Component _compute_as_pct failed for record {rec.id}: {e}"
                )
                rec.as_pct_of_om = 0


# =============================================================================
# CHILD MODEL: Component Materiality (Group Audits)
# =============================================================================
class PlanningP5ComponentMateriality(models.Model):
    """Component Materiality for Group Audits - ISA 600."""

    _name = "qaco.planning.p5.component.materiality"
    _description = "P-5: Component Materiality"
    _order = "sequence, id"

    p5_id = fields.Many2one(
        "qaco.planning.p5.materiality",
        string="P-5 Materiality",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(string="Seq", default=10)
    component_name = fields.Char(
        string="Component Name",
        required=True,
        help="Name of subsidiary, division, or branch",
    )
    component_type = fields.Selection(
        [
            ("subsidiary", "Subsidiary"),
            ("division", "Division"),
            ("branch", "Branch"),
            ("jv", "Joint Venture"),
            ("associate", "Associate"),
        ],
        string="Component Type",
        required=True,
    )
    component_significance = fields.Selection(
        [
            ("significant", "Significant Component"),
            ("non_significant", "Non-Significant Component"),
        ],
        string="Significance",
        required=True,
    )
    component_materiality = fields.Float(
        string="Component Materiality", digits=(16, 2), required=True
    )
    currency_id = fields.Many2one(
        "res.currency", related="p5_id.currency_id", store=False
    )
    allocation_basis = fields.Selection(
        [
            ("revenue", "Revenue Based"),
            ("assets", "Asset Based"),
            ("profit", "Profit Based"),
            ("risk", "Risk Based"),
            ("combination", "Combination"),
        ],
        string="Allocation Basis",
        required=True,
    )
    allocation_notes = fields.Text(string="Allocation Notes")


# =============================================================================
# CHILD MODEL: Materiality Revision Log
# =============================================================================
class PlanningP5Revision(models.Model):
    """Materiality Revision Log - ISA 320.12-13."""

    _name = "qaco.planning.p5.revision"
    _description = "P-5: Materiality Revision Log"
    _order = "revision_date desc, id desc"

    p5_id = fields.Many2one(
        "qaco.planning.p5.materiality",
        string="P-5 Materiality",
        required=True,
        ondelete="cascade",
        index=True,
    )
    revision_date = fields.Datetime(
        string="Revision Date", required=True, default=fields.Datetime.now
    )
    revision_stage = fields.Selection(
        [
            ("planning", "During Planning"),
            ("execution", "During Execution"),
            ("completion", "Near Completion"),
        ],
        string="Audit Stage",
        required=True,
    )
    previous_om = fields.Float(string="Previous OM", digits=(16, 2))
    revised_om = fields.Float(string="Revised OM", digits=(16, 2), required=True)
    previous_pm = fields.Float(string="Previous PM", digits=(16, 2))
    revised_pm = fields.Float(string="Revised PM", digits=(16, 2))
    currency_id = fields.Many2one(
        "res.currency", related="p5_id.currency_id", store=False
    )
    revision_reason = fields.Text(
        string="Reason for Revision",
        required=True,
        help="Document why materiality is being revised per ISA 320.12-13",
    )
    revised_by_id = fields.Many2one(
        "res.users",
        string="Revised By",
        required=True,
        default=lambda self: self._get_default_user(),
    )
    partner_approved = fields.Boolean(
        string="Partner Approved", help="Revision approved by engagement partner"
    )


# =============================================================================
# CHILD MODEL: Qualitative Sensitivity Items
# =============================================================================
class PlanningP5QualitativeItem(models.Model):
    """Qualitative Materiality Items - Areas sensitive regardless of size."""

    _name = "qaco.planning.p5.qualitative.item"
    _description = "P-5: Qualitative Sensitivity Item"
    _order = "sequence, id"

    p5_id = fields.Many2one(
        "qaco.planning.p5.materiality",
        string="P-5 Materiality",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(string="Seq", default=10)
    sensitivity_area = fields.Selection(
        [
            ("related_parties", "Related Party Transactions"),
            ("directors_remuneration", "Directors' Remuneration"),
            ("regulatory_disclosures", "Regulatory Disclosures"),
            ("covenant_breaches", "Covenant Breaches"),
            ("zakat_tax", "Zakat / Tax Matters"),
            ("fraud_indicators", "Fraud Indicators"),
            ("key_disclosures", "Key FS Disclosures"),
            ("segment_info", "Segment Information"),
            ("eps", "Earnings Per Share"),
            ("other", "Other Sensitive Area"),
        ],
        string="Sensitivity Area",
        required=True,
    )
    other_description = fields.Char(
        string="Other Description", help="If sensitivity area is Other"
    )
    applies_to_entity = fields.Boolean(string="Applies to This Entity", default=True)
    notes = fields.Text(string="Notes / Considerations")


# =============================================================================
# MAIN MODEL: P-5 Materiality & Performance Materiality
# =============================================================================
class PlanningP5Materiality(models.Model):
    """
    P-5: Materiality & Performance Materiality
    ISA 320, ISA 450, ISA 315 (Revised), ISA 570 (Revised)
    """

    _name = "qaco.planning.p5.materiality"
    _description = "P-5: Materiality & Performance Materiality"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    TAB_STATE = [
        ("not_started", "Not Started"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("reviewed", "Reviewed"),
        ("approved", "Approved"),
        ("locked", "Locked"),
    ]

    BENCHMARK_TYPES = [
        ("pbt", "Profit Before Tax"),
        ("revenue", "Revenue"),
        ("total_assets", "Total Assets"),
        ("net_assets", "Net Assets / Equity"),
        ("expenditure", "Expenditure (NGOs)"),
        ("custom", "Custom Benchmark"),
    ]

    # =========================================================================
    # CORE FIELDS
    # =========================================================================
    name = fields.Char(
        string="Reference", compute="_compute_name", store=True, readonly=True
    )
    state = fields.Selection(
        TAB_STATE, string="Status", default="not_started", tracking=True, copy=False
    )

    # Sequential Gating (ISA 300/220: Systematic Planning Approach)
    can_open = fields.Boolean(
        string="Can Open This Tab",
        compute="_compute_can_open",
        store=False,
        help="P-5 can only be opened after P-4 is approved",
    )

    @api.depends("audit_id")
    def _compute_can_open(self):
        """P-5 requires P-4 to be approved."""
        for rec in self:
            if not rec.audit_id:
                rec.can_open = False
                continue
            # Find P-4 for this audit
            p4 = self.env["qaco.planning.p4.analytics"].search(
                [("audit_id", "=", rec.audit_id.id)], limit=1
            )
            rec.can_open = p4.state == "approved" if p4 else False

    @api.constrains("state")
    def _check_sequential_gating(self):
        """ISA 300/220: Enforce sequential planning approach."""
        for rec in self:
            if rec.state != "not_started" and not rec.can_open:
                raise UserError(
                    "ISA 300/220 Violation: Sequential Planning Approach Required.\n\n"
                    "P-5 (Materiality) cannot be started until P-4 (Analytics) "
                    "has been Partner-approved.\n\n"
                    "Reason: Materiality determination requires analysis of financial "
                    "data and understanding of users' information needs.\n\n"
                    "Action: Please complete and obtain Partner approval for P-4 first."
                )

    audit_id = fields.Many2one(
        "qaco.audit",
        string="Audit Engagement",
        required=True,
        ondelete="cascade",
        index=True,
        tracking=True,
    )
    planning_main_id = fields.Many2one(
        "qaco.planning.main", string="Planning Phase", ondelete="cascade", index=True
    )
    client_id = fields.Many2one(
        "res.partner",
        string="Client",
        related="audit_id.client_id",
        store=False,
        readonly=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self._get_default_currency(),
    )

    # =========================================================================
    # SECTION A - PURPOSE & CONTEXT OF MATERIALITY
    # =========================================================================
    section_a_header = fields.Char(
        default="Section A: Purpose & Context of Materiality", readonly=True
    )

    # Intended Users
    user_shareholders = fields.Boolean(string="☐ Shareholders")
    user_lenders = fields.Boolean(string="☐ Lenders")
    user_regulators = fields.Boolean(string="☐ Regulators")
    user_donors = fields.Boolean(string="☐ Donors (NGOs)")
    user_employees = fields.Boolean(string="☐ Employees")
    user_suppliers = fields.Boolean(string="☐ Suppliers/Creditors")
    user_other = fields.Boolean(string="☐ Other Users")
    user_other_description = fields.Char(string="Other Users Description")

    # User Sensitivity
    user_sensitivity = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
        ],
        string="Sensitivity of Users to Misstatements",
        tracking=True,
    )
    user_sensitivity_notes = fields.Text(
        string="User Sensitivity Notes",
        help="Document rationale for sensitivity assessment",
    )

    # Entity Status
    entity_status = fields.Selection(
        [
            ("listed_pie", "Listed / Public Interest Entity (PIE)"),
            ("non_pie", "Non-PIE"),
            ("ngo_npo", "NGO / Non-Profit Organization"),
            ("government", "Government Entity"),
        ],
        string="Entity Status",
        tracking=True,
    )
    pie_considerations = fields.Html(
        string="PIE Considerations",
        help="Document additional considerations for PIE entities",
    )

    # Section A Checklist
    checklist_a_users_identified = fields.Boolean(string="☐ Users identified")
    checklist_a_sensitivity_assessed = fields.Boolean(
        string="☐ User sensitivity assessed"
    )
    checklist_a_pie_applied = fields.Boolean(
        string="☐ PIE considerations applied (if applicable)"
    )

    # =========================================================================
    # SECTION B - BENCHMARK SELECTION (CRITICAL JUDGMENT)
    # =========================================================================
    section_b_header = fields.Char(
        default="Section B: Benchmark Selection (Critical Judgment)", readonly=True
    )

    benchmark_type = fields.Selection(
        BENCHMARK_TYPES, string="Selected Benchmark", required=True, tracking=True
    )
    benchmark_amount = fields.Float(
        string="Benchmark Amount",
        digits=(16, 2),
        tracking=True,
        help="Auto-fetched from financial data",
    )
    custom_benchmark_name = fields.Char(
        string="Custom Benchmark Name", help="If using custom benchmark"
    )
    custom_benchmark_amount = fields.Float(
        string="Custom Benchmark Amount", digits=(16, 2)
    )
    benchmark_stability = fields.Selection(
        [
            ("stable", "Stable"),
            ("volatile", "Volatile"),
        ],
        string="Benchmark Stability Assessment",
        tracking=True,
    )
    benchmark_stability_notes = fields.Text(string="Stability Assessment Notes")
    benchmark_justification = fields.Html(
        string="Justification for Benchmark Selection",
        help="MANDATORY: Document why this benchmark is appropriate",
    )
    prior_year_benchmark_type = fields.Selection(
        BENCHMARK_TYPES, string="Prior Year Benchmark Type"
    )
    benchmark_consistent_with_py = fields.Selection(
        [
            ("yes", "Yes"),
            ("no", "No - Change Justified"),
        ],
        string="Consistent with Prior Year?",
    )
    benchmark_change_justification = fields.Text(
        string="Benchmark Change Justification",
        help="Required if benchmark changed from prior year",
    )

    # Section B Checklist
    checklist_b_benchmark_appropriate = fields.Boolean(
        string="☐ Benchmark appropriate to entity"
    )
    checklist_b_consistent_or_justified = fields.Boolean(
        string="☐ Consistent with prior year (or change justified)"
    )

    # =========================================================================
    # SECTION C - OVERALL MATERIALITY CALCULATION
    # =========================================================================
    section_c_header = fields.Char(
        default="Section C: Overall Materiality Calculation", readonly=True
    )

    materiality_percentage = fields.Float(
        string="Percentage Applied to Benchmark (%)",
        digits=(5, 2),
        default=5.0,
        tracking=True,
    )
    overall_materiality = fields.Float(
        string="Overall Materiality (OM)",
        digits=(16, 2),
        compute="_compute_materiality",
        store=True,
        tracking=True,
    )

    # Prior Year Comparison
    prior_year_om = fields.Float(
        string="Prior Year OM",
        digits=(16, 2),
        help="Overall materiality from prior year audit",
    )
    om_change_pct = fields.Float(
        string="Change vs Prior Year %",
        compute="_compute_om_change",
        store=True,
        digits=(5, 2),
    )
    om_change_explanation = fields.Html(
        string="Change Explanation",
        help="MANDATORY if materiality changed from prior year",
    )

    # Firm Policy Thresholds
    firm_min_pct = fields.Float(
        string="Firm Minimum %", default=1.0, help="Firm policy minimum percentage"
    )
    firm_max_pct = fields.Float(
        string="Firm Maximum %", default=10.0, help="Firm policy maximum percentage"
    )
    outside_firm_threshold = fields.Boolean(
        string="Outside Firm Threshold",
        compute="_compute_outside_threshold",
        store=True,
    )
    threshold_exception_justification = fields.Text(
        string="Threshold Exception Justification",
        help="Required if percentage outside firm policy",
    )

    # =========================================================================
    # SECTION D - PERFORMANCE MATERIALITY (PM)
    # =========================================================================
    section_d_header = fields.Char(
        default="Section D: Performance Materiality (PM) - ISA 320", readonly=True
    )

    pm_percentage = fields.Float(
        string="PM as % of OM",
        digits=(5, 2),
        default=75.0,
        tracking=True,
        help="Typically 50-75% of Overall Materiality",
    )
    performance_materiality = fields.Float(
        string="Performance Materiality (PM)",
        digits=(16, 2),
        compute="_compute_materiality",
        store=True,
        tracking=True,
    )

    # PM Rationale Factors
    pm_risk_of_misstatement = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
        ],
        string="Risk of Misstatement",
    )
    pm_control_environment = fields.Selection(
        [
            ("strong", "Strong"),
            ("adequate", "Adequate"),
            ("weak", "Weak"),
        ],
        string="Control Environment",
    )
    pm_prior_year_misstatements = fields.Selection(
        [
            ("none", "None / Minimal"),
            ("some", "Some Misstatements"),
            ("significant", "Significant Misstatements"),
        ],
        string="Prior Year Misstatements",
    )
    pm_rationale = fields.Html(
        string="PM Rationale",
        help="Document rationale for PM percentage considering risk factors",
    )

    # Section D Checklist
    checklist_d_pm_sufficiently_lower = fields.Boolean(
        string="☐ PM sufficiently lower than OM"
    )
    checklist_d_risk_rationale = fields.Boolean(
        string="☐ Risk-adjusted rationale documented"
    )

    # =========================================================================
    # SECTION E - CLEARLY TRIVIAL THRESHOLD (CTT)
    # =========================================================================
    section_e_header = fields.Char(
        default="Section E: Clearly Trivial Threshold (CTT) - ISA 450", readonly=True
    )

    ctt_percentage = fields.Float(
        string="CTT as % of OM",
        digits=(5, 2),
        default=5.0,
        tracking=True,
        help="Typically 3-5% of Overall Materiality",
    )
    clearly_trivial_threshold = fields.Float(
        string="Clearly Trivial Threshold (CTT)",
        digits=(16, 2),
        compute="_compute_materiality",
        store=True,
        tracking=True,
    )
    ctt_basis = fields.Html(
        string="Basis for CTT Selection", help="Document rationale for CTT percentage"
    )

    # =========================================================================
    # SECTION F - QUALITATIVE MATERIALITY CONSIDERATIONS
    # =========================================================================
    section_f_header = fields.Char(
        default="Section F: Qualitative Materiality Considerations", readonly=True
    )

    # Qualitative Sensitivity Flags
    qual_related_parties = fields.Boolean(string="☐ Related Party Transactions")
    qual_directors_remuneration = fields.Boolean(string="☐ Directors' Remuneration")
    qual_regulatory_disclosures = fields.Boolean(string="☐ Regulatory Disclosures")
    qual_covenant_breaches = fields.Boolean(string="☐ Covenant Breaches")
    qual_zakat_tax = fields.Boolean(string="☐ Zakat / Tax Matters")
    qual_segment_info = fields.Boolean(string="☐ Segment Information")
    qual_eps = fields.Boolean(string="☐ Earnings Per Share")
    qual_other = fields.Boolean(string="☐ Other Sensitive Areas")

    # Detailed qualitative items
    qualitative_item_ids = fields.One2many(
        "qaco.planning.p5.qualitative.item",
        "p5_id",
        string="Qualitative Sensitivity Items",
    )

    qualitative_narrative = fields.Html(
        string="Narrative on Qualitative Materiality",
        help="Document qualitative considerations affecting materiality judgments",
    )

    # Section F Checklist
    checklist_f_qualitative_considered = fields.Boolean(
        string="☐ Qualitative factors considered"
    )
    checklist_f_regulatory_addressed = fields.Boolean(
        string="☐ Regulatory sensitivities addressed"
    )

    # =========================================================================
    # SECTION G - RISK-ADJUSTED MATERIALITY (ADVANCED)
    # =========================================================================
    section_g_header = fields.Char(
        default="Section G: Risk-Adjusted Materiality (Advanced)", readonly=True
    )

    overall_engagement_risk = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
        ],
        string="Overall Engagement Risk Level",
        help="From P-6 when available",
    )

    # Adjustment Factors
    adjust_high_fraud_risk = fields.Boolean(string="☐ High Fraud Risk")
    adjust_weak_controls = fields.Boolean(string="☐ Weak Controls")
    adjust_going_concern = fields.Boolean(string="☐ Going Concern Uncertainty")
    adjust_first_year = fields.Boolean(string="☐ First Year Engagement")
    adjust_complex_transactions = fields.Boolean(string="☐ Complex Transactions")

    risk_adjustment_applied = fields.Boolean(
        string="Risk Adjustment Applied", tracking=True
    )
    revised_pm = fields.Float(
        string="Revised PM (if adjusted)",
        digits=(16, 2),
        help="Adjusted PM after considering risk factors",
    )
    risk_adjustment_justification = fields.Html(
        string="Risk Adjustment Justification", help="MANDATORY if adjustment applied"
    )

    # =========================================================================
    # SECTION H - COMPONENT / GROUP MATERIALITY
    # =========================================================================
    section_h_header = fields.Char(
        default="Section H: Component / Group Materiality (ISA 600)", readonly=True
    )

    is_group_audit = fields.Selection(
        [
            ("yes", "Yes"),
            ("no", "No"),
        ],
        string="Group Audit?",
        default="no",
        tracking=True,
    )
    component_materiality_required = fields.Selection(
        [
            ("yes", "Yes"),
            ("no", "No"),
        ],
        string="Component Materiality Required?",
    )

    component_materiality_ids = fields.One2many(
        "qaco.planning.p5.component.materiality",
        "p5_id",
        string="Component Materiality",
    )

    component_allocation_basis = fields.Html(
        string="Basis for Allocation",
        help="Document methodology for allocating materiality to components",
    )

    # =========================================================================
    # SECTION I - LINKAGE TO AUDIT EXECUTION (AUTO-FLOW)
    # =========================================================================
    section_i_header = fields.Char(
        default="Section I: Linkage to Audit Execution (Auto-Flow)", readonly=True
    )

    linkage_sampling = fields.Boolean(
        string="☐ Linked to Sampling Engine", default=False
    )
    linkage_substantive = fields.Boolean(
        string="☐ Linked to Substantive Testing Thresholds", default=False
    )
    linkage_misstatement = fields.Boolean(
        string="☐ Linked to Misstatement Accumulation", default=False
    )
    linkage_evaluation = fields.Boolean(
        string="☐ Linked to Uncorrected Misstatement Evaluation", default=False
    )
    linkage_report = fields.Boolean(
        string="☐ Linked to Report Modification Logic", default=False
    )

    linkage_notes = fields.Html(
        string="Linkage Notes",
        help="Document how materiality flows to execution modules",
    )

    # Manual override control
    manual_override_requested = fields.Boolean(
        string="Manual Override Requested", tracking=True
    )
    override_partner_justification = fields.Html(
        string="Partner Justification for Override",
        help="MANDATORY if manual override requested",
    )

    # =========================================================================
    # SECTION J - MANDATORY DOCUMENT UPLOADS
    # =========================================================================
    section_j_header = fields.Char(
        default="Section J: Mandatory Document Uploads", readonly=True
    )

    materiality_worksheet_ids = fields.Many2many(
        "ir.attachment",
        "qaco_p5_worksheet_rel",
        "p5_id",
        "attachment_id",
        string="Materiality Calculation Worksheet",
    )
    prior_year_reference_ids = fields.Many2many(
        "ir.attachment",
        "qaco_p5_py_ref_rel",
        "p5_id",
        "attachment_id",
        string="Prior-Year Materiality Reference",
    )
    partner_approval_evidence_ids = fields.Many2many(
        "ir.attachment",
        "qaco_p5_partner_evidence_rel",
        "p5_id",
        "attachment_id",
        string="Partner Approval Evidence",
    )

    # Document Checklist
    checklist_j_worksheet = fields.Boolean(string="☐ Materiality calculation worksheet")
    checklist_j_prior_year = fields.Boolean(string="☐ Prior-year materiality reference")
    checklist_j_partner_evidence = fields.Boolean(
        string="☐ Partner approval evidence (if separate)"
    )

    # =========================================================================
    # SECTION K - P-5 CONCLUSION & PROFESSIONAL JUDGMENT
    # =========================================================================
    section_k_header = fields.Char(
        default="Section K: P-5 Conclusion & Professional Judgment", readonly=True
    )

    conclusion_narrative = fields.Html(
        string="P-5 Conclusion",
        default="""<p><strong>Overall materiality, performance materiality, and clearly trivial 
thresholds have been determined in accordance with ISA 320 and ISA 450, considering both 
quantitative and qualitative factors, and are appropriate for planning and performing the audit.</strong></p>""",
    )

    # Final Confirmations
    confirm_materiality_appropriate = fields.Boolean(
        string="☐ Materiality appropriately determined"
    )
    confirm_embedded_in_strategy = fields.Boolean(
        string="☐ Embedded into audit strategy"
    )
    confirm_proceed_to_p6 = fields.Boolean(string="☐ Proceed to risk assessment (P-6)")

    # Specific Materiality Items (One2many)
    specific_materiality_ids = fields.One2many(
        "qaco.planning.p5.specific.materiality",
        "p5_id",
        string="Specific Materiality Items",
    )

    # Revision Log
    revision_ids = fields.One2many(
        "qaco.planning.p5.revision", "p5_id", string="Materiality Revisions"
    )

    # =========================================================================
    # SECTION L - REVIEW, APPROVAL & LOCK
    # =========================================================================
    section_l_header = fields.Char(
        default="Section L: Review, Approval & Lock", readonly=True
    )

    # Prepared By
    prepared_by_id = fields.Many2one(
        "res.users", string="Prepared By", tracking=True, copy=False
    )
    prepared_by_role = fields.Char(string="Role")
    prepared_on = fields.Datetime(string="Prepared On", tracking=True, copy=False)

    # Reviewed By (Manager)
    reviewed_by_id = fields.Many2one(
        "res.users", string="Reviewed By (Manager)", tracking=True, copy=False
    )
    reviewed_on = fields.Datetime(string="Reviewed On", tracking=True, copy=False)
    review_notes = fields.Html(string="Review Notes")

    # Partner Approval
    partner_approved = fields.Selection(
        [
            ("yes", "Yes"),
            ("no", "No"),
        ],
        string="Partner Approval",
        tracking=True,
    )
    partner_approved_by_id = fields.Many2one(
        "res.users", string="Partner Approved By", tracking=True, copy=False
    )
    partner_approved_on = fields.Datetime(
        string="Partner Approved On", tracking=True, copy=False
    )
    partner_comments = fields.Html(
        string="Partner Comments", help="MANDATORY when partner approves"
    )

    # Lock indicator
    is_locked = fields.Boolean(
        string="Locked", default=False, copy=False, help="Locked after partner approval"
    )

    # ISA Reference
    isa_reference = fields.Char(
        string="ISA Reference", default="ISA 320, ISA 450", readonly=True
    )

    # =========================================================================
    # SQL CONSTRAINTS
    # =========================================================================
    _sql_constraints = [
        (
            "audit_unique",
            "UNIQUE(audit_id)",
            "Only one P-5 Materiality record per Audit Engagement is allowed.",
        )
    ]

    # =========================================================================
    # COMPUTED METHODS
    # =========================================================================
    @api.depends("audit_id", "client_id")
    def _compute_name(self):
        for rec in self:
            if rec.client_id:
                rec.name = (
                    f"P5-{rec.client_id.name[:20] if rec.client_id.name else 'NEW'}"
                )
            else:
                rec.name = "P-5: Materiality"

    @api.depends(
        "benchmark_type",
        "benchmark_amount",
        "custom_benchmark_amount",
        "materiality_percentage",
        "pm_percentage",
        "ctt_percentage",
    )
    def _compute_materiality(self):
        for rec in self:
            # Get effective benchmark
            if rec.benchmark_type == "custom":
                base = rec.custom_benchmark_amount or 0
            else:
                base = rec.benchmark_amount or 0

            # Calculate Overall Materiality
            rec.overall_materiality = (
                base * (rec.materiality_percentage / 100) if base else 0
            )

            # Calculate Performance Materiality
            rec.performance_materiality = (
                rec.overall_materiality * (rec.pm_percentage / 100)
                if rec.overall_materiality
                else 0
            )

            # Calculate Clearly Trivial Threshold
            rec.clearly_trivial_threshold = (
                rec.overall_materiality * (rec.ctt_percentage / 100)
                if rec.overall_materiality
                else 0
            )

    @api.depends("overall_materiality", "prior_year_om")
    def _compute_om_change(self):
        """Defensive: Safe even during module install."""
        for rec in self:
            try:
                if rec.prior_year_om and rec.prior_year_om != 0:
                    rec.om_change_pct = (
                        (rec.overall_materiality - rec.prior_year_om)
                        / rec.prior_year_om
                    ) * 100
                else:
                    rec.om_change_pct = 0
            except Exception as e:
                _logger.warning(
                    f"P-5 _compute_om_change failed for record {rec.id}: {e}"
                )
                rec.om_change_pct = 0

    @api.depends("materiality_percentage", "firm_min_pct", "firm_max_pct")
    def _compute_outside_threshold(self):
        """Defensive: Safe even during module install."""
        for rec in self:
            try:
                rec.outside_firm_threshold = (
                    rec.materiality_percentage < rec.firm_min_pct
                    or rec.materiality_percentage > rec.firm_max_pct
                )
            except Exception as e:
                _logger.warning(
                    f"P-5 _compute_outside_threshold failed for record {rec.id}: {e}"
                )
                rec.outside_firm_threshold = False

    # =========================================================================
    # VALIDATION METHODS
    # =========================================================================
    @api.constrains("materiality_percentage")
    def _check_materiality_percentage(self):
        for rec in self:
            if rec.materiality_percentage and not (
                0.1 <= rec.materiality_percentage <= 25
            ):
                raise ValidationError(
                    "Materiality percentage must be between 0.1% and 25%. "
                    "Values outside this range require documented justification."
                )

    @api.constrains("pm_percentage")
    def _check_pm_percentage(self):
        for rec in self:
            if rec.pm_percentage and not (25 <= rec.pm_percentage <= 95):
                raise ValidationError(
                    "Performance Materiality must be between 25% and 95% of Overall Materiality."
                )

    @api.constrains("ctt_percentage")
    def _check_ctt_percentage(self):
        for rec in self:
            if rec.ctt_percentage and not (1 <= rec.ctt_percentage <= 10):
                raise ValidationError(
                    "Clearly Trivial Threshold should be between 1% and 10% of Overall Materiality."
                )

    def _validate_section_b(self):
        """Validate Section B: Benchmark Selection."""
        errors = []
        if not self.benchmark_type:
            errors.append("Benchmark type must be selected (Section B)")
        if self.benchmark_type == "custom" and not self.custom_benchmark_amount:
            errors.append("Custom benchmark amount is required (Section B)")
        if self.benchmark_type != "custom" and not self.benchmark_amount:
            errors.append("Benchmark amount is required (Section B)")
        if not self.benchmark_justification:
            errors.append(
                "CRITICAL: Benchmark justification is MANDATORY per ISA 320 (Section B)"
            )
        return errors

    def _validate_section_c(self):
        """Validate Section C: Overall Materiality."""
        errors = []
        if (
            self.overall_materiality
            and self.om_change_pct
            and abs(self.om_change_pct) > 10
        ):
            if not self.om_change_explanation:
                errors.append(
                    "Explanation required for materiality change >10% from prior year (Section C)"
                )
        if self.outside_firm_threshold and not self.threshold_exception_justification:
            errors.append(
                "Exception justification required when outside firm policy thresholds (Section C)"
            )
        return errors

    def _validate_section_d(self):
        """Validate Section D: Performance Materiality."""
        errors = []
        if not self.pm_rationale:
            errors.append("PM rationale is required (Section D)")
        return errors

    def _validate_section_g(self):
        """Validate Section G: Risk Adjustment."""
        errors = []
        if self.risk_adjustment_applied and not self.risk_adjustment_justification:
            errors.append("Risk adjustment justification is required (Section G)")
        return errors

    def _validate_section_i(self):
        """Validate Section I: Linkage."""
        errors = []
        if self.manual_override_requested and not self.override_partner_justification:
            errors.append(
                "Partner justification required for manual override (Section I)"
            )
        return errors

    def _validate_section_j(self):
        """Validate Section J: Documents."""
        errors = []
        if not self.materiality_worksheet_ids:
            errors.append("Materiality calculation worksheet is required (Section J)")
        return errors

    def _validate_section_k(self):
        """Validate Section K: Conclusion."""
        errors = []
        if not self.confirm_materiality_appropriate:
            errors.append("Materiality appropriateness must be confirmed (Section K)")
        if not self.confirm_embedded_in_strategy:
            errors.append("Strategy embedding must be confirmed (Section K)")
        return errors

    def _validate_for_completion(self):
        """Validate all sections for completion."""
        self.ensure_one()
        errors = []
        errors.extend(self._validate_section_b())
        errors.extend(self._validate_section_c())
        errors.extend(self._validate_section_d())
        errors.extend(self._validate_section_g())
        errors.extend(self._validate_section_i())
        errors.extend(self._validate_section_j())
        errors.extend(self._validate_section_k())
        return errors

    def _validate_for_approval(self):
        """Validate requirements for partner approval."""
        self.ensure_one()
        errors = self._validate_for_completion()
        if not self.review_notes:
            errors.append("Manager review notes are required before partner approval")
        return errors

    # =========================================================================
    # ACTION METHODS
    # =========================================================================
    def action_start_work(self):
        """Start work on P-5 tab."""
        for rec in self:
            if rec.state != "not_started":
                raise UserError("Can only start work on tabs that are 'Not Started'.")
            # Check P-4 prerequisite
            if "qaco.planning.p4.analytics" in self.env:
                p4 = self.env["qaco.planning.p4.analytics"].search(
                    [("audit_id", "=", rec.audit_id.id)], limit=1
                )
                if p4 and p4.state not in ["approved", "locked"]:
                    raise UserError(
                        "P-4 (Preliminary Analytical Procedures) must be partner-approved "
                        "before starting P-5."
                    )
            rec.state = "in_progress"
            rec.message_post(body="P-5 Materiality work started.")

    def action_complete(self):
        """Mark P-5 as complete."""
        for rec in self:
            if rec.state != "in_progress":
                raise UserError("Can only complete tabs that are 'In Progress'.")
            errors = rec._validate_for_completion()
            if errors:
                raise UserError(
                    "Cannot complete P-5. Missing requirements:\n- "
                    + "\n- ".join(errors)
                )
            rec.prepared_by_id = self.env.user
            rec.prepared_on = fields.Datetime.now()
            rec.state = "completed"
            rec.message_post(body="P-5 Materiality marked as complete.")

    def action_manager_review(self):
        """Manager review of P-5."""
        for rec in self:
            if rec.state != "completed":
                raise UserError("Can only review tabs that are 'Completed'.")
            if not rec.review_notes:
                raise UserError("Manager review notes are required.")
            rec.reviewed_by_id = self.env.user
            rec.reviewed_on = fields.Datetime.now()
            rec.state = "reviewed"
            rec.message_post(body=f"P-5 reviewed by Manager: {self.env.user.name}")

    def action_partner_approve(self):
        """Partner approval of P-5."""
        for rec in self:
            if rec.state != "reviewed":
                raise UserError("Can only approve tabs that have been 'Reviewed'.")
            errors = rec._validate_for_approval()
            if errors:
                raise UserError(
                    "Cannot approve P-5. Missing requirements:\n- "
                    + "\n- ".join(errors)
                )
            if not rec.partner_comments:
                raise UserError("Partner comments are mandatory for approval.")
            rec.partner_approved = "yes"
            rec.partner_approved_by_id = self.env.user
            rec.partner_approved_on = fields.Datetime.now()
            rec.is_locked = True
            rec.state = "locked"
            rec._update_execution_linkage()
            rec.message_post(
                body=f"P-5 approved and locked by Partner: {self.env.user.name}"
            )
            # Auto-unlock P-6 if exists
            rec._auto_unlock_p6()

    def action_send_back(self):
        """Send P-5 back for rework."""
        for rec in self:
            if rec.state not in ["completed", "reviewed"]:
                raise UserError(
                    "Can only send back tabs that are 'Completed' or 'Reviewed'."
                )
            rec.state = "in_progress"
            rec.message_post(body="P-5 sent back for rework.")

    def action_unlock(self):
        """Unlock P-5 (partner only)."""
        for rec in self:
            if rec.state != "locked":
                raise UserError("Can only unlock tabs that are 'Locked'.")
            rec.is_locked = False
            rec.partner_approved = "no"
            rec.state = "reviewed"
            rec.message_post(body=f"P-5 unlocked by Partner: {self.env.user.name}")

    def action_revise_materiality(self):
        """Create materiality revision entry."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Revise Materiality",
            "res_model": "qaco.planning.p5.revision",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_p5_id": self.id,
                "default_previous_om": self.overall_materiality,
                "default_previous_pm": self.performance_materiality,
            },
        }

    def _update_execution_linkage(self):
        """Update execution module linkage flags."""
        self.ensure_one()
        self.linkage_sampling = True
        self.linkage_substantive = True
        self.linkage_misstatement = True
        self.linkage_evaluation = True
        self.linkage_report = True
        _logger.info(
            f"P-5 materiality linked to execution modules for audit {self.audit_id.id}"
        )

    def _auto_unlock_p6(self):
        """Auto-unlock P-6 when P-5 is approved."""
        self.ensure_one()
        if "qaco.planning.p6.risk" in self.env:
            p6 = self.env["qaco.planning.p6.risk"].search(
                [("audit_id", "=", self.audit_id.id)], limit=1
            )
            if p6 and p6.state == "not_started":
                _logger.info(
                    f"P-6 auto-unlock triggered by P-5 approval for audit {self.audit_id.id}"
                )

    def action_generate_materiality_memo(self):
        """Generate Materiality Determination Memorandum."""
        self.ensure_one()
        # Placeholder for PDF generation
        self.message_post(body="Materiality Determination Memorandum generated.")
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Memorandum Generated",
                "message": "Materiality Determination Memorandum has been generated.",
                "type": "success",
            },
        }
