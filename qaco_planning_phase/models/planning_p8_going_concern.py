# -*- coding: utf-8 -*-
"""
P-8: Going Concern (Preliminary Assessment)
ISA 570/315/330/240/220/ISQM-1/Companies Act 2017/ICAP QCR/AOB
Court-defensible, fully integrated with planning workflow.
"""
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


# =============================
# Parent Model: Going Concern Assessment
# =============================
class PlanningP8GoingConcern(models.Model):
    """P-8: Going Concern - Preliminary Assessment (ISA 570)"""

    _name = "qaco.planning.p8.going.concern"
    _description = "P-8: Preliminary Analytical Procedures"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    TAB_STATE = [
        ("not_started", "Not Started"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("reviewed", "Reviewed"),
        ("approved", "Approved"),
    ]

    state = fields.Selection(
        TAB_STATE,
        string="Status",
        default="not_started",
        tracking=True,
        copy=False,
    )

    # Sequential Gating (ISA 300/220: Systematic Planning Approach)
    can_open = fields.Boolean(
        string="Can Open This Tab",
        compute="_compute_can_open",
        store=False,
        help="P-8 can only be opened after P-7 is approved",
    )

    @api.depends("audit_id")
    def _compute_can_open(self):
        """P-8 requires P-7 to be approved."""
        for rec in self:
            if not rec.audit_id:
                rec.can_open = False
                continue
            # Find P-7 for this audit
            p7 = self.env["qaco.planning.p7.fraud"].search(
                [("audit_id", "=", rec.audit_id.id)], limit=1
            )
            rec.can_open = p7.state == "approved" if p7 else False

    @api.constrains("state")
    def _check_sequential_gating(self):
        """ISA 300/220: Enforce sequential planning approach."""
        for rec in self:
            if rec.state != "not_started" and not rec.can_open:
                raise UserError(
                    "ISA 300/220 & ISA 570 Violation: Sequential Planning Approach Required.\n\n"
                    "P-8 (Going Concern) cannot be started until P-7 (Fraud Assessment) "
                    "has been Partner-approved.\n\n"
                    "Reason: Going concern assessment per ISA 570 requires consideration of "
                    "fraud risks and overall risk environment from P-7.\n\n"
                    "Action: Please complete and obtain Partner approval for P-7 first."
                )

    name = fields.Char(
        string="Reference", compute="_compute_name", store=True, readonly=True
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
        string="Client Name",
        related="audit_id.client_id",
        readonly=True,
        store=False,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self._get_default_currency(),
    )

    # ===== Financial Indicators =====
    financial_indicators_header = fields.Char(
        string="Financial Indicators",
        default="ISA 570.A3 - Financial Indicators",
        readonly=True,
    )
    # XML view compatible narrative field
    financial_indicators = fields.Html(
        string="Financial Indicators",
        help="Narrative assessment of financial indicators",
    )
    net_liability_position = fields.Boolean(
        string="Net Liability/Negative Working Capital",
        help="Net liability or net current liability position",
    )
    negative_operating_cash = fields.Boolean(
        string="Negative Operating Cash Flows",
        help="Negative operating cash flows indicated by historical or forecast statements",
    )
    # XML view compatible alias
    negative_operating_cash_flow = fields.Boolean(
        string="Negative Operating Cash Flow",
        related="negative_operating_cash",
        readonly=False,
    )
    loan_defaults = fields.Boolean(
        string="Loan Defaults/Breaches",
        help="Default on loan agreements or inability to pay creditors on due dates",
    )
    inability_pay_dividends = fields.Boolean(
        string="Inability to Pay Dividends",
        help="Arrears or discontinuance of dividends",
    )
    adverse_financial_ratios = fields.Boolean(
        string="Adverse Financial Ratios", help="Adverse key financial ratios"
    )
    # XML view compatible alias
    adverse_key_ratios = fields.Boolean(
        string="Adverse Key Ratios", related="adverse_financial_ratios", readonly=False
    )
    substantial_losses = fields.Boolean(string="Substantial Operating Losses")
    # XML view compatible alias
    substantial_operating_losses = fields.Boolean(
        string="Substantial Operating Losses",
        related="substantial_losses",
        readonly=False,
    )
    recurring_operating_losses = fields.Boolean(
        string="Recurring Operating Losses",
        help="History of recurring operating losses",
    )
    deteriorating_liquidity_ratios = fields.Boolean(
        string="Deteriorating Liquidity Ratios",
        help="Current ratio, quick ratio declining",
    )
    covenant_breaches = fields.Boolean(
        string="Loan Covenant Breaches",
        help="Actual or potential breaches of loan covenants",
    )
    financing_difficulty = fields.Boolean(string="Difficulty Obtaining Financing")
    # XML view compatible aliases
    inability_to_pay_creditors = fields.Boolean(
        string="Inability to Pay Creditors", related="loan_defaults", readonly=False
    )
    inability_to_obtain_financing = fields.Boolean(
        string="Inability to Obtain Financing",
        related="financing_difficulty",
        readonly=False,
    )
    financial_indicators_notes = fields.Html(string="Financial Indicators Analysis")
    # XML view compatible alias
    financial_indicator_assessment = fields.Html(
        string="Financial Indicator Assessment",
        related="financial_indicators_notes",
        readonly=False,
    )

    # ===== Operating Indicators =====
    operating_indicators_header = fields.Char(
        string="Operating Indicators",
        default="ISA 570.A3 - Operating Indicators",
        readonly=True,
    )
    # XML view compatible narrative field
    operating_indicators = fields.Html(
        string="Operating Indicators",
        help="Narrative assessment of operating indicators",
    )
    management_intent_liquidate = fields.Boolean(
        string="Management Intent to Liquidate/Cease",
        help="Management intentions to liquidate or cease operations",
    )
    # XML view compatible alias
    management_intentions = fields.Boolean(
        string="Management Intentions",
        related="management_intent_liquidate",
        readonly=False,
    )
    loss_key_management = fields.Boolean(
        string="Loss of Key Management",
        help="Loss of key management without replacement",
    )
    # XML view compatible alias
    loss_of_key_management = fields.Boolean(
        string="Loss of Key Management", related="loss_key_management", readonly=False
    )
    loss_major_market = fields.Boolean(
        string="Loss of Major Market/Customer/Supplier",
        help="Loss of major market, customer, franchise, license, or principal supplier",
    )
    # XML view compatible alias
    loss_of_major_market = fields.Boolean(
        string="Loss of Major Market", related="loss_major_market", readonly=False
    )
    labor_difficulties = fields.Boolean(
        string="Labor Difficulties", help="Labor difficulties"
    )
    shortage_supplies = fields.Boolean(
        string="Shortage of Important Supplies", help="Shortages of important supplies"
    )
    # XML view compatible alias
    shortage_of_supplies = fields.Boolean(
        string="Shortage of Supplies", related="shortage_supplies", readonly=False
    )
    powerful_competitor = fields.Boolean(string="Emergence of Powerful Competitor")
    # XML view compatible alias
    emergence_of_competitor = fields.Boolean(
        string="Emergence of Competitor", related="powerful_competitor", readonly=False
    )
    obsolete_idle_capacity = fields.Boolean(
        string="Obsolete Inventory / Idle Capacity",
        help="Obsolete inventory or significant idle production capacity",
    )
    dependence_key_individuals = fields.Boolean(
        string="Dependence on Key Individuals",
        help="Heavy dependence on success of particular individuals",
    )
    high_employee_attrition = fields.Boolean(
        string="High Employee Attrition",
        help="Unusually high staff turnover or difficulty retaining key staff",
    )
    operating_indicators_notes = fields.Html(string="Operating Indicators Analysis")
    # XML view compatible alias
    operating_indicator_assessment = fields.Html(
        string="Operating Indicator Assessment",
        related="operating_indicators_notes",
        readonly=False,
    )

    # ===== Other Indicators (includes Legal/Regulatory) =====
    other_indicators_header = fields.Char(
        string="Other Indicators",
        default="ISA 570.A3 - Other Indicators",
        readonly=True,
    )
    # XML view compatible narrative fields
    legal_indicators = fields.Html(
        string="Legal/Regulatory Indicators",
        help="Assessment of legal and regulatory indicators",
    )
    other_indicators = fields.Html(
        string="Other Indicators", help="Assessment of other going concern indicators"
    )
    non_compliance_capital = fields.Boolean(
        string="Non-compliance with Capital Requirements",
        help="Non-compliance with capital or other statutory or regulatory requirements",
    )
    pending_litigation = fields.Boolean(
        string="Pending Litigation/Claims",
        help="Pending legal or regulatory proceedings that may result in claims",
    )
    # XML view compatible alias
    pending_legal_proceedings = fields.Boolean(
        string="Pending Legal Proceedings", related="pending_litigation", readonly=False
    )
    changes_legislation = fields.Boolean(
        string="Changes in Legislation/Policy",
        help="Changes in law/regulation or government policy expected to adversely affect entity",
    )
    # XML view compatible alias
    changes_in_law = fields.Boolean(
        string="Changes in Law", related="changes_legislation", readonly=False
    )
    license_revocation = fields.Boolean(
        string="License Revocation Risk", help="Risk of license or permit revocation"
    )
    uninsured_catastrophes = fields.Boolean(
        string="Uninsured/Underinsured Catastrophes"
    )
    other_indicators_notes = fields.Html(string="Other Indicators Analysis")
    # XML view compatible alias
    legal_indicator_assessment = fields.Html(
        string="Legal Indicator Assessment",
        related="other_indicators_notes",
        readonly=False,
    )
    industry_economic_factors = fields.Html(
        string="Industry/Economic Factors",
        help="Industry and economic factors affecting going concern",
    )
    pandemic_impact = fields.Html(
        string="Pandemic Impact",
        help="Assessment of pandemic (COVID-19) impact on operations",
    )

    # ===== SECTION D: Financing & Liquidity Indicators =====
    financing_facilities_available = fields.Selection(
        [
            ("adequate", "Adequate"),
            ("limited", "Limited"),
            ("none", "None"),
        ],
        string="Availability of Financing Facilities",
    )
    reliance_short_term_borrowing = fields.Boolean(
        string="Heavy Reliance on Short-Term Borrowing",
        help="Entity relies heavily on short-term debt to finance long-term assets",
    )
    ability_refinance_debt = fields.Selection(
        [
            ("able", "Able to Refinance"),
            ("uncertain", "Uncertain"),
            ("unable", "Unable to Refinance"),
        ],
        string="Ability to Refinance Maturing Debt",
    )
    dependence_shareholder_support = fields.Boolean(
        string="Dependence on Shareholder/Related Party Support",
        help="Going concern dependent on shareholder loans or support",
    )
    dependence_donor_funding = fields.Boolean(
        string="Dependence on Government/Donor Funding (NGOs)",
        help="For NGOs/non-profits: dependence on uncertain donor funding",
    )
    financing_assessment = fields.Html(
        string="Financing & Liquidity Assessment",
        help="Overall assessment of financing and liquidity position",
    )

    # Section D: Confirmations
    confirm_financing_sources_assessed = fields.Boolean(
        string="☐ Financing sources assessed",
        help="All financing sources have been evaluated",
    )
    confirm_liquidity_stress_evaluated = fields.Boolean(
        string="☐ Liquidity stress evaluated",
        help="Liquidity stress scenarios have been considered",
    )

    # ===== SECTION E: Legal, Regulatory & External Indicators =====
    material_litigation_impact = fields.Boolean(
        string="Pending Litigation with Material Impact",
        help="Litigation that could materially impact going concern",
    )
    regulatory_actions_penalties = fields.Boolean(
        string="Regulatory Actions / Penalties",
        help="Regulatory enforcement actions or significant penalties",
    )
    adverse_market_conditions = fields.Boolean(
        string="Adverse Market or Economic Conditions",
        help="Significant adverse market or economic conditions",
    )
    political_policy_uncertainty = fields.Boolean(
        string="Political / Policy Uncertainty",
        help="Political instability or policy changes (Pakistan context)",
    )
    legal_regulatory_assessment = fields.Html(
        string="Legal & Regulatory Risk Assessment",
        help="Assessment of legal and regulatory risks to going concern",
    )

    # Section E: System Rule
    disclosure_risk_flagged = fields.Boolean(
        string="Disclosure Risk Flagged",
        compute="_compute_disclosure_risk",
        store=True,
        help="Auto-flagged if significant legal/regulatory issues exist",
    )

    # ===== SECTION F: Management's Going-Concern Assessment =====
    management_performed_assessment = fields.Boolean(
        string="Has Management Performed GC Assessment?",
        help="ISA 570.16 - Inquire of management regarding GC assessment",
    )
    management_assessment_basis = fields.Html(
        string="Basis of Management Assessment",
        help="Basis and methodology used by management for GC assessment",
    )
    management_key_assumptions = fields.Html(
        string="Key Assumptions Used by Management",
        help="Critical assumptions in management's GC assessment",
    )
    management_period_covered = fields.Integer(
        string="Period Covered by Management (Months)",
        help="Time period covered by management's GC assessment",
    )
    consistency_auditor_understanding = fields.Selection(
        [
            ("consistent", "Consistent"),
            ("inconsistent", "Inconsistent"),
            ("not_assessed", "Not Yet Assessed"),
        ],
        string="Consistency with Auditor Understanding",
        default="not_assessed",
        help="Is management's assessment consistent with auditor's understanding?",
    )

    # Section F: Confirmations
    confirm_management_assessment_obtained = fields.Boolean(
        string="☐ Management assessment obtained",
        help="Management's GC assessment has been obtained",
    )
    confirm_assumptions_evaluated = fields.Boolean(
        string="☐ Assumptions evaluated for reasonableness",
        help="Management's assumptions have been critically evaluated",
    )

    # ===== SECTION G: Management Plans to Mitigate Risks =====
    management_plans = fields.Html(
        string="Management's Mitigation Plans",
        help="Document management's plans to address going concern issues per ISA 570.17",
    )
    management_plans = fields.Html(
        string="Management's Plans",
        help="Document management's plans to address going concern issues",
    )
    plans_feasibility = fields.Html(
        string="Feasibility of Plans",
        help="Assessment of the feasibility of management's plans",
    )
    plans_supporting_docs = fields.Html(
        string="Supporting Documentation",
        help="Documentation supporting management's plans",
    )
    plans_audit_procedures = fields.Html(
        string="Audit Procedures on Management Plans",
        help="Audit procedures performed on management's plans",
    )
    plans_likelihood = fields.Selection(
        [
            ("unlikely", "🔴 Unlikely to be Successful"),
            ("uncertain", "🟡 Uncertain"),
            ("likely", "🟢 Likely to be Successful"),
        ],
        string="Likelihood of Success",
    )

    # ===== SECTION A: Basis of Assessment & Period Covered =====
    assessment_period_months = fields.Integer(
        string="Assessment Period (Months)",
        default=12,
        help="Period covered by management's assessment (≥ 12 months per ISA 570)",
    )
    assessment_date = fields.Date(
        string="Assessment Date",
        help="Date of going concern assessment",
        default=fields.Date.today,
    )
    reporting_date = fields.Date(
        string="Financial Statement Reporting Date",
        help="Reporting date for financial statements",
    )
    fs_basis = fields.Selection(
        [
            ("going_concern", "Going Concern"),
            ("liquidation", "Liquidation Basis"),
            ("other", "Other"),
        ],
        string="Financial Statement Basis",
        default="going_concern",
    )
    assessment_timing = fields.Selection(
        [
            ("planning", "Planning Stage"),
            ("interim", "Interim"),
            ("year_end", "Year-End"),
        ],
        string="Assessment Timing",
        default="planning",
    )

    # Section A: Sources Used (Checklists)
    source_management_accounts = fields.Boolean(
        string="☐ Management Accounts",
        help="Used management accounts for GC assessment",
    )
    source_cash_flow_forecasts = fields.Boolean(
        string="☐ Cash Flow Forecasts", help="Used cash flow forecasts"
    )
    source_financing_agreements = fields.Boolean(
        string="☐ Financing Agreements", help="Reviewed financing agreements"
    )
    source_budgets_plans = fields.Boolean(
        string="☐ Budgets/Business Plans", help="Reviewed budgets and business plans"
    )

    # Section A: Confirmations
    confirm_period_adequate = fields.Boolean(
        string="☐ Period adequate per ISA 570",
        help="Assessment period is ≥ 12 months from reporting date",
    )
    confirm_sources_appropriate = fields.Boolean(
        string="☐ Sources identified and appropriate",
        help="All relevant sources have been considered",
    )

    assessment_period_adequacy = fields.Html(
        string="Assessment Period Adequacy",
        help="Assessment of whether management's period is adequate per ISA 570",
    )
    events_beyond_period = fields.Html(
        string="Events Beyond Assessment Period",
        help="Consideration of events beyond the assessment period",
    )

    # ===== Inquiries & Procedures =====
    management_inquiries = fields.Html(
        string="Management Inquiries",
        help="Inquiries of management regarding going concern",
    )
    audit_procedures_performed = fields.Html(
        string="Audit Procedures Performed",
        help="Audit procedures performed for going concern assessment",
    )
    written_representations = fields.Html(
        string="Written Representations",
        help="Written representations obtained from management",
    )

    # ===== SECTION H: Preliminary Going-Concern Conclusion =====
    material_uncertainty_identified = fields.Boolean(
        string="Material Uncertainty Identified?",
        tracking=True,
        help="ISA 570.18 - Material uncertainty related to going concern",
    )
    significant_doubt_exists = fields.Boolean(
        string="Significant Doubt Exists?",
        tracking=True,
        help="Significant doubt about entity's ability to continue as going concern",
    )
    gc_risk_identified = fields.Boolean(
        string="Going Concern Risk Identified", tracking=True
    )
    # XML view compatible alias
    material_uncertainty_exists = fields.Boolean(
        string="Material Uncertainty Exists",
        related="material_uncertainty_identified",
        readonly=False,
    )
    preliminary_conclusion = fields.Selection(
        [
            ("no_concern", "🟢 No Significant Going Concern Issues"),
            ("uncertainty_exists", "🟡 Material Uncertainty May Exist"),
            ("inappropriate_basis", "🔴 Going Concern Basis May Be Inappropriate"),
        ],
        string="Preliminary Conclusion",
        tracking=True,
    )
    # XML view compatible alias
    going_concern_conclusion = fields.Selection(
        string="Going Concern Conclusion",
        related="preliminary_conclusion",
        readonly=False,
    )
    conclusion_basis_narrative = fields.Html(
        string="Basis for Conclusion (MANDATORY)",
        help="Detailed rationale for preliminary going concern conclusion per ISA 570",
    )
    conclusion_rationale = fields.Html(
        string="Conclusion Rationale",
        help="Rationale for the preliminary going concern conclusion",
    )
    disclosure_implications_identified = fields.Boolean(
        string="Disclosure Implications Identified?",
        help="Have disclosure implications been identified?",
    )

    # ===== SECTION I: Linkage to Risk Assessment & Audit Strategy =====
    gc_risks_linked_to_p6 = fields.Boolean(
        string="GC Risks Linked to P-6 (RMM)",
        help="Going concern risks have been incorporated into P-6 Risk Assessment",
    )
    gc_risks_linked_to_p12 = fields.Boolean(
        string="GC Risks Linked to P-12 (Audit Strategy)",
        help="Going concern implications documented in P-12 Audit Strategy",
    )
    extended_procedures_required = fields.Boolean(
        string="Extended Procedures Required",
        help="Extended audit procedures required for going concern",
    )
    cash_flow_testing_required = fields.Boolean(
        string="Cash Flow Testing Required", help="Detailed cash flow testing required"
    )
    subsequent_events_focus = fields.Boolean(
        string="Subsequent Events Focus Required",
        help="Enhanced focus on subsequent events review",
    )
    linkage_narrative = fields.Html(
        string="Linkage to Risk Assessment & Strategy",
        help="How GC risks flow to P-6 and P-12",
    )

    # ===== Disclosure Requirements =====
    disclosure_required = fields.Boolean(
        string="Disclosure Required",
        help="Is going concern disclosure required in financial statements?",
    )
    disclosure_assessment = fields.Html(
        string="Disclosure Assessment", help="Assessment of adequacy of disclosures"
    )
    material_uncertainty_disclosure = fields.Html(
        string="Material Uncertainty Disclosure",
        help="Assessment of material uncertainty disclosure",
    )
    reporting_implications = fields.Html(
        string="Reporting Implications", help="Implications for auditor's report"
    )
    report_modification = fields.Boolean(
        string="Report Modification Required",
        help="Is modification of audit report required?",
    )
    emphasis_of_matter = fields.Boolean(
        string="Emphasis of Matter Required",
        help="Is emphasis of matter paragraph required?",
    )

    # ===== Further Procedures =====
    further_procedures = fields.Html(
        string="Further Procedures Planned",
        help="Additional audit procedures to be performed",
    )
    management_representations = fields.Html(
        string="Management Representations Required",
        help="Specific representations to be obtained from management",
    )

    # ===== Attachments =====
    gc_analysis_attachment_ids = fields.Many2many(
        "ir.attachment",
        "qaco_p8_gc_analysis_rel",
        "p8_id",
        "attachment_id",
        string="Going Concern Analysis",
    )
    # XML view compatible alias
    going_concern_attachment_ids = fields.Many2many(
        "ir.attachment",
        "qaco_p8_gc_attachment_rel",
        "p8_id",
        "attachment_id",
        string="Going Concern Documentation",
    )
    cash_flow_forecast_attachment_ids = fields.Many2many(
        "ir.attachment",
        "qaco_p8_cash_flow_rel",
        "p8_id",
        "attachment_id",
        string="Cash Flow Forecasts",
    )
    representation_attachment_ids = fields.Many2many(
        "ir.attachment",
        "qaco_p8_representation_rel",
        "p8_id",
        "attachment_id",
        string="Management Representations",
    )

    # ===== SECTION K: P-8 Conclusion & Professional Judgment =====
    going_concern_summary = fields.Html(
        string="Going Concern Summary (MANDATORY)",
        help="Consolidated going concern assessment per ISA 570",
    )

    # Section K: Final Confirmations
    confirm_gc_assessment_completed = fields.Boolean(
        string="☐ GC assessment completed",
        help="Going concern assessment has been completed per ISA 570",
    )
    confirm_risks_classified = fields.Boolean(
        string="☐ Risks appropriately classified",
        help="GC risks have been appropriately classified and documented",
    )
    confirm_strategy_implications = fields.Boolean(
        string="☐ Audit strategy implications identified",
        help="Implications for P-12 audit strategy have been identified",
    )

    isa_reference = fields.Char(
        string="ISA Reference", default="ISA 570 (Revised)", readonly=True
    )

    # ===== Sign-off Fields =====
    senior_signed_user_id = fields.Many2one(
        "res.users",
        string="Senior Completed By",
        tracking=True,
        copy=False,
        readonly=True,
    )
    senior_signed_on = fields.Datetime(
        string="Senior Completed On", tracking=True, copy=False, readonly=True
    )
    manager_reviewed_user_id = fields.Many2one(
        "res.users",
        string="Manager Reviewed By",
        tracking=True,
        copy=False,
        readonly=True,
    )
    manager_reviewed_on = fields.Datetime(
        string="Manager Reviewed On", tracking=True, copy=False, readonly=True
    )
    partner_approved_user_id = fields.Many2one(
        "res.users",
        string="Partner Approved By",
        tracking=True,
        copy=False,
        readonly=True,
    )
    partner_approved_on = fields.Datetime(
        string="Partner Approved On", tracking=True, copy=False, readonly=True
    )
    reviewer_notes = fields.Html(string="Reviewer Notes")
    approval_notes = fields.Html(string="Approval Notes")

    _sql_constraints = [
        (
            "audit_unique",
            "UNIQUE(audit_id)",
            "Only one P-8 record per Audit Engagement is allowed.",
        )
    ]

    # ============================================================================
    # PROMPT 3: Safe HTML Default Template (Set in create, not field default)
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Set HTML defaults safely in create() to avoid registry crashes."""
        gc_summary_template = """
<p><strong>Preliminary Going Concern Assessment (ISA 570 Revised)</strong></p>
<p>Based on the preliminary assessment performed in accordance with ISA 570 (Revised), indicators of going-concern risk have been identified and evaluated. Management's assessment and plans have been considered, and appropriate implications for audit strategy and reporting have been determined.</p>
<ol>
<li><strong>Assessment Period:</strong> [State period covered]</li>
<li><strong>Indicators Identified:</strong> [Summarize key financial, operating, legal indicators]</li>
<li><strong>Management's Assessment & Plans:</strong> [Summarize management's response]</li>
<li><strong>Preliminary Conclusion:</strong> [State conclusion]</li>
<li><strong>Audit Strategy Implications:</strong> [Link to P-12]</li>
</ol>
"""
        for vals in vals_list:
            if "going_concern_summary" not in vals:
                vals["going_concern_summary"] = gc_summary_template
        return super().create(vals_list)

    @api.depends("audit_id", "client_id")
    def _compute_name(self):
        for record in self:
            if record.client_id:
                record.name = f"P8-{record.client_id.name[:15]}"
            else:
                record.name = "P-8: Going Concern"

    @api.depends(
        "material_litigation_impact",
        "regulatory_actions_penalties",
        "adverse_market_conditions",
        "political_policy_uncertainty",
    )
    def _compute_disclosure_risk(self):
        """Auto-flag disclosure risk if significant legal/regulatory issues"""
        for record in self:
            record.disclosure_risk_flagged = any(
                [
                    record.material_litigation_impact,
                    record.regulatory_actions_penalties,
                    record.adverse_market_conditions
                    and record.political_policy_uncertainty,
                ]
            )

    @api.depends("plans_feasibility_auditor", "dependency_third_party")
    def _compute_unsupported_plans(self):
        """Defensive: Auto-flag if management plans are unsupported or not feasible."""
        for record in self:
            try:
                record.unsupported_plans_flag = (
                    record.plans_feasibility_auditor == "not_feasible"
                    or (
                        record.dependency_third_party
                        and record.plans_feasibility_auditor != "feasible"
                    )
                )
            except Exception as e:
                _logger.warning(
                    f"P-8 _compute_unsupported_plans failed for record {record.id}: {e}"
                )
                record.unsupported_plans_flag = False

    def _validate_mandatory_fields(self):
        """Validate mandatory fields before completing P-8."""
        self.ensure_one()
        errors = []
        if not self.preliminary_conclusion:
            errors.append("Preliminary going concern conclusion is required")
        if not self.conclusion_rationale:
            errors.append("Conclusion rationale must be documented")
        if self.gc_risk_identified and not self.management_plans:
            errors.append("Management's plans must be documented if GC risk exists")
        if not self.going_concern_summary:
            errors.append("Going concern summary is required")
        if errors:
            raise UserError(
                "Cannot complete P-8. Missing requirements:\n• " + "\n• ".join(errors)
            )

    def action_start_work(self):
        for record in self:
            if record.state != "not_started":
                raise UserError("Can only start work on tabs that are Not Started.")
            record.state = "in_progress"

    def action_complete(self):
        for record in self:
            if record.state != "in_progress":
                raise UserError("Can only complete tabs that are In Progress.")
            record._validate_mandatory_fields()
            record.senior_signed_user_id = self.env.user
            record.senior_signed_on = fields.Datetime.now()
            record.state = "completed"

    def action_review(self):
        for record in self:
            if record.state != "completed":
                raise UserError("Can only review tabs that are Completed.")
            record.manager_reviewed_user_id = self.env.user
            record.manager_reviewed_on = fields.Datetime.now()
            record.state = "reviewed"

    def action_approve(self):
        for record in self:
            if record.state != "reviewed":
                raise UserError("Can only approve tabs that have been Reviewed.")
            record.partner_approved_user_id = self.env.user
            record.partner_approved_on = fields.Datetime.now()
            record.state = "approved"
            record.message_post(
                body="P-8 Going Concern Assessment approved by Partner."
            )
            # Auto-unlock P-9: Laws & Regulations
            record._auto_unlock_p9()

    def _auto_unlock_p9(self):
        """Auto-unlock P-9 Laws & Regulations when P-8 is approved"""
        self.ensure_one()
        if not self.audit_id:
            return

        # Find or create P-9 record
        P9 = self.env["qaco.planning.p9.laws.regulations"]
        p9_record = P9.search([("audit_id", "=", self.audit_id.id)], limit=1)

        if p9_record and p9_record.state == "locked":
            p9_record.write({"state": "not_started"})
            p9_record.message_post(
                body="P-9 Laws & Regulations auto-unlocked after P-8 Going Concern approval."
            )
            _logger.info(f"P-9 auto-unlocked for audit {self.audit_id.name}")
        elif not p9_record:
            # Create new P-9 record if doesn't exist
            p9_record = P9.create(
                {
                    "audit_id": self.audit_id.id,
                    "state": "not_started",
                }
            )
            _logger.info(f"P-9 auto-created for audit {self.audit_id.name}")

    def action_send_back(self):
        for record in self:
            if record.state not in ["completed", "reviewed"]:
                raise UserError(
                    "Can only send back tabs that are Completed or Reviewed."
                )
            record.state = "in_progress"

    def action_unlock(self):
        for record in self:
            if record.state != "approved":
                raise UserError("Can only unlock Approved tabs.")
            record.partner_approved_user_id = False
            record.partner_approved_on = False
            record.state = "reviewed"
