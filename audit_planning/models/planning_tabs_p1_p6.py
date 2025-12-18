# -*- coding: utf-8 -*-
"""
Abstract Base Model for Planning Tabs (P-1 through P-13)

Provides common fields and behavior for all tab sub-models.
"""
from odoo import api, fields, models, _


class PlanningTabMixin(models.AbstractModel):
    _name = "audit.planning.tab.mixin"
    _description = "Planning Tab Mixin"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    REVIEW_STATUS = [
        ("draft", "Draft"),
        ("prepared", "Prepared"),
        ("reviewed", "Reviewed"),
    ]

    # Link to parent planning
    planning_id = fields.Many2one(
        "audit.planning",
        string="Planning",
        required=True,
        ondelete="cascade",
        index=True,
    )

    # Standard fields per requirements
    notes = fields.Html(
        string="Working Notes",
        required=True,
        tracking=True,
        help="Mandatory documentation notes for this planning section.",
    )
    prepared_by = fields.Many2one(
        "res.users",
        string="Prepared By",
        default=lambda self: self.env.user,
        tracking=True,
    )
    prepared_on = fields.Datetime(
        string="Prepared On",
        default=fields.Datetime.now,
        tracking=True,
    )
    reviewed_by = fields.Many2one(
        "res.users",
        string="Reviewed By",
        tracking=True,
    )
    reviewed_on = fields.Datetime(
        string="Reviewed On",
        tracking=True,
    )
    review_status = fields.Selection(
        REVIEW_STATUS,
        string="Review Status",
        default="draft",
        tracking=True,
    )

    # Completion tracking
    is_complete = fields.Boolean(
        string="Is Complete",
        compute="_compute_is_complete",
        store=True,
    )

    # Attachments
    attachment_ids = fields.Many2many(
        "ir.attachment",
        string="Attachments",
        help="Supporting documents for this planning section.",
    )

    @api.depends("notes", "review_status")
    def _compute_is_complete(self):
        for record in self:
            record.is_complete = bool(record.notes) and record.review_status in ("prepared", "reviewed")

    def action_mark_prepared(self):
        """Mark tab as prepared by staff."""
        self.ensure_one()
        if not self.notes:
            from odoo.exceptions import UserError
            raise UserError(_("Complete the mandatory notes before marking as prepared."))
        self.prepared_by = self.env.user
        self.prepared_on = fields.Datetime.now()
        self.review_status = "prepared"
        return True

    def action_mark_reviewed(self):
        """Mark tab as reviewed by manager/partner."""
        self.ensure_one()
        if self.review_status != "prepared":
            from odoo.exceptions import UserError
            raise UserError(_("Tab must be prepared before review."))
        self.reviewed_by = self.env.user
        self.reviewed_on = fields.Datetime.now()
        self.review_status = "reviewed"
        return True


# ═══════════════════════════════════════════════════════════════════════
# P-1: Engagement Setup & Team Assignment (ISA 210, ISA 220, ISQM-1)
# ═══════════════════════════════════════════════════════════════════════
class PlanningP1Team(models.Model):
    _name = "audit.planning.p1.team"
    _description = "P-1: Engagement Setup & Team Assignment"
    _inherit = ["audit.planning.tab.mixin"]

    # Team Assignment Fields
    engagement_partner_id = fields.Many2one(
        "res.users",
        string="Engagement Partner",
        tracking=True,
        help="ISA 220: Partner responsible for the engagement.",
    )
    engagement_manager_id = fields.Many2one(
        "res.users",
        string="Engagement Manager",
        tracking=True,
    )
    eqcr_required = fields.Boolean(
        string="EQCR Required",
        help="ISQM-1: Whether Engagement Quality Control Review is required.",
    )
    eqcr_reviewer_id = fields.Many2one(
        "res.users",
        string="EQCR Reviewer",
        tracking=True,
    )
    team_member_ids = fields.Many2many(
        "res.users",
        "audit_planning_p1_team_members_rel",
        "p1_id",
        "user_id",
        string="Team Members",
    )
    
    # Engagement Letter
    engagement_letter_signed = fields.Boolean(
        string="Engagement Letter Signed",
        tracking=True,
        help="ISA 210: Confirmation that engagement letter is signed.",
    )
    engagement_letter_date = fields.Date(
        string="Engagement Letter Date",
    )
    engagement_letter_attachment_ids = fields.Many2many(
        "ir.attachment",
        "audit_planning_p1_engagement_letter_rel",
        "p1_id",
        "attachment_id",
        string="Engagement Letter",
    )
    
    # Independence & Ethics
    independence_confirmed = fields.Boolean(
        string="Independence Confirmed",
        tracking=True,
        help="IESBA Code: Team independence confirmation.",
    )
    independence_threats_identified = fields.Html(
        string="Independence Threats & Safeguards",
    )
    
    # Competence
    competence_assessment = fields.Html(
        string="Team Competence Assessment",
        help="ISA 220: Assessment of team competence for the engagement.",
    )
    
    # Supervision Plan
    supervision_plan = fields.Html(
        string="Direction, Supervision & Review Plan",
        help="ISA 220: Plan for direction, supervision, and review.",
    )

    @api.depends("notes", "review_status", "engagement_letter_signed", "independence_confirmed")
    def _compute_is_complete(self):
        for record in self:
            record.is_complete = (
                bool(record.notes) and
                record.engagement_letter_signed and
                record.independence_confirmed and
                record.review_status in ("prepared", "reviewed")
            )


# ═══════════════════════════════════════════════════════════════════════
# P-2: Understanding the Entity & Environment (ISA 315)
# ═══════════════════════════════════════════════════════════════════════
class PlanningP2Entity(models.Model):
    _name = "audit.planning.p2.entity"
    _description = "P-2: Understanding the Entity & Environment"
    _inherit = ["audit.planning.tab.mixin"]

    # Industry & External Factors
    industry_conditions = fields.Html(
        string="Industry Conditions",
        help="ISA 315: Market conditions, competition, technology, etc.",
    )
    regulatory_environment = fields.Html(
        string="Regulatory Environment",
        help="Applicable laws, regulations, and regulatory bodies.",
    )
    economic_conditions = fields.Html(
        string="Economic Conditions",
        help="Interest rates, inflation, currency, economic trends.",
    )
    
    # Entity Nature
    business_operations = fields.Html(
        string="Nature of Business Operations",
        help="Products, services, markets, customers, suppliers.",
    )
    ownership_governance = fields.Html(
        string="Ownership & Governance Structure",
        help="Shareholders, board composition, governance framework.",
    )
    organizational_structure = fields.Html(
        string="Organizational Structure",
        help="Management structure, reporting lines, key personnel.",
    )
    
    # Accounting Policies
    accounting_policies = fields.Html(
        string="Accounting Policies",
        help="Key accounting policies and practices.",
    )
    accounting_framework = fields.Selection([
        ("ifrs", "IFRS"),
        ("local_gaap", "Local GAAP"),
        ("other", "Other"),
    ], string="Accounting Framework")
    
    # Objectives & Strategies
    entity_objectives = fields.Html(
        string="Entity Objectives & Strategies",
        help="Business objectives, strategies, and related risks.",
    )
    
    # Financial Performance
    financial_performance = fields.Html(
        string="Financial Performance Measures",
        help="KPIs, budgets, forecasts, variance analysis.",
    )
    
    # Related Attachments
    organogram_attachment_ids = fields.Many2many(
        "ir.attachment",
        "audit_planning_p2_organogram_rel",
        "p2_id",
        "attachment_id",
        string="Organogram",
    )
    moa_aoa_attachment_ids = fields.Many2many(
        "ir.attachment",
        "audit_planning_p2_moa_rel",
        "p2_id",
        "attachment_id",
        string="MOA/AOA/Constitution",
    )


# ═══════════════════════════════════════════════════════════════════════
# P-3: Internal Control Understanding (ISA 315)
# ═══════════════════════════════════════════════════════════════════════
class PlanningP3Controls(models.Model):
    _name = "audit.planning.p3.controls"
    _description = "P-3: Internal Control Understanding"
    _inherit = ["audit.planning.tab.mixin"]

    # Control Environment
    control_environment = fields.Html(
        string="Control Environment",
        help="Communication of integrity, ethical values, governance oversight.",
    )
    control_environment_rating = fields.Selection([
        ("effective", "Effective"),
        ("partially_effective", "Partially Effective"),
        ("ineffective", "Ineffective"),
    ], string="Control Environment Rating")
    
    # Entity Risk Assessment
    entity_risk_assessment = fields.Html(
        string="Entity's Risk Assessment Process",
        help="How entity identifies and addresses business risks.",
    )
    
    # Information System
    information_system = fields.Html(
        string="Information System",
        help="Systems for recording, processing, reporting transactions.",
    )
    it_environment = fields.Html(
        string="IT Environment",
        help="IT systems, applications, databases, general IT controls.",
    )
    
    # Control Activities
    control_activities = fields.Html(
        string="Control Activities",
        help="Policies and procedures addressing significant risks.",
    )
    
    # Monitoring
    monitoring_activities = fields.Html(
        string="Monitoring of Controls",
        help="Ongoing and separate evaluations of internal control.",
    )
    internal_audit_function = fields.Boolean(
        string="Internal Audit Function Exists",
    )
    internal_audit_assessment = fields.Html(
        string="Internal Audit Assessment",
        help="Assessment of internal audit function if applicable.",
    )
    
    # Control Deficiencies
    control_deficiencies = fields.Html(
        string="Identified Control Deficiencies",
    )
    
    # Control Reliance Decision
    reliance_on_controls = fields.Boolean(
        string="Plan to Rely on Controls",
        help="Whether to adopt a control reliance strategy.",
    )
    reliance_justification = fields.Html(
        string="Control Reliance Justification",
    )
    
    # Attachments
    control_questionnaire_ids = fields.Many2many(
        "ir.attachment",
        "audit_planning_p3_questionnaire_rel",
        "p3_id",
        "attachment_id",
        string="Control Questionnaires",
    )
    process_flowchart_ids = fields.Many2many(
        "ir.attachment",
        "audit_planning_p3_flowchart_rel",
        "p3_id",
        "attachment_id",
        string="Process Flowcharts",
    )


# ═══════════════════════════════════════════════════════════════════════
# P-4: Preliminary Analytical Procedures (ISA 520)
# ═══════════════════════════════════════════════════════════════════════
class PlanningP4Analytics(models.Model):
    _name = "audit.planning.p4.analytics"
    _description = "P-4: Preliminary Analytical Procedures"
    _inherit = ["audit.planning.tab.mixin"]

    # Prior Year Data
    prior_year_revenue = fields.Float(string="Prior Year Revenue")
    prior_year_assets = fields.Float(string="Prior Year Total Assets")
    prior_year_profit = fields.Float(string="Prior Year Profit/Loss")
    prior_year_equity = fields.Float(string="Prior Year Equity")
    
    # Current Year Data
    current_year_revenue = fields.Float(string="Current Year Revenue (Draft)")
    current_year_assets = fields.Float(string="Current Year Total Assets (Draft)")
    current_year_profit = fields.Float(string="Current Year Profit/Loss (Draft)")
    current_year_equity = fields.Float(string="Current Year Equity (Draft)")
    
    # Trend Analysis
    trend_analysis = fields.Html(
        string="Trend Analysis",
        help="3-5 year trend analysis of key financial data.",
    )
    
    # Ratio Analysis
    ratio_analysis = fields.Html(
        string="Ratio Analysis",
        help="Liquidity, profitability, solvency, efficiency ratios.",
    )
    
    # Industry Comparison
    industry_comparison = fields.Html(
        string="Industry Comparison",
        help="Comparison with industry benchmarks and peers.",
    )
    
    # Significant Fluctuations
    significant_fluctuations = fields.Html(
        string="Significant Fluctuations",
        help="Variances >10% or exceeding materiality requiring investigation.",
    )
    
    # Analytical Expectations
    analytical_expectations = fields.Html(
        string="Analytical Expectations",
        help="Expected relationships and predictable patterns.",
    )
    
    # Conclusions
    analytics_conclusions = fields.Html(
        string="Analytical Procedures Conclusions",
        help="Overall conclusions from preliminary analytics.",
    )
    
    # Attachments
    trial_balance_ids = fields.Many2many(
        "ir.attachment",
        "audit_planning_p4_tb_rel",
        "p4_id",
        "attachment_id",
        string="Trial Balance",
    )
    prior_year_fs_ids = fields.Many2many(
        "ir.attachment",
        "audit_planning_p4_prior_fs_rel",
        "p4_id",
        "attachment_id",
        string="Prior Year Financial Statements",
    )


# ═══════════════════════════════════════════════════════════════════════
# P-5: Materiality & Performance Materiality (ISA 320)
# ═══════════════════════════════════════════════════════════════════════
class PlanningP5Materiality(models.Model):
    _name = "audit.planning.p5.materiality"
    _description = "P-5: Materiality & Performance Materiality"
    _inherit = ["audit.planning.tab.mixin"]

    # Benchmark Selection
    benchmark = fields.Selection([
        ("revenue", "Revenue"),
        ("total_assets", "Total Assets"),
        ("profit_before_tax", "Profit Before Tax"),
        ("equity", "Equity"),
        ("total_expenses", "Total Expenses"),
        ("custom", "Custom Benchmark"),
    ], string="Materiality Benchmark", required=True)
    
    benchmark_amount = fields.Float(
        string="Benchmark Amount",
        required=True,
    )
    benchmark_justification = fields.Html(
        string="Benchmark Selection Justification",
        required=True,
        help="ISA 320: Justify why this benchmark is appropriate.",
    )
    
    # Materiality Percentages
    materiality_percentage = fields.Float(
        string="Materiality Percentage (%)",
        default=5.0,
        help="Percentage applied to benchmark (typically 0.5% - 10%).",
    )
    
    # Calculated Values
    overall_materiality = fields.Float(
        string="Overall Materiality",
        compute="_compute_materiality",
        store=True,
    )
    performance_materiality = fields.Float(
        string="Performance Materiality",
        compute="_compute_materiality",
        store=True,
        help="Typically 50-75% of overall materiality.",
    )
    performance_materiality_percentage = fields.Float(
        string="PM Percentage (%)",
        default=75.0,
        help="Percentage of overall materiality for PM.",
    )
    trivial_threshold = fields.Float(
        string="Clearly Trivial Threshold",
        compute="_compute_materiality",
        store=True,
        help="Typically 3-5% of overall materiality.",
    )
    trivial_percentage = fields.Float(
        string="Trivial Percentage (%)",
        default=5.0,
    )
    
    # Specific Materiality
    specific_materiality_required = fields.Boolean(
        string="Specific Materiality Required",
    )
    specific_materiality_items = fields.Html(
        string="Items Requiring Specific Materiality",
        help="Related party transactions, director remuneration, etc.",
    )
    
    # Revision Consideration
    revision_factors = fields.Html(
        string="Factors Requiring Materiality Revision",
        help="Circumstances that may require revision during the audit.",
    )

    @api.depends("benchmark_amount", "materiality_percentage", "performance_materiality_percentage", "trivial_percentage")
    def _compute_materiality(self):
        for record in self:
            record.overall_materiality = record.benchmark_amount * (record.materiality_percentage / 100.0)
            record.performance_materiality = record.overall_materiality * (record.performance_materiality_percentage / 100.0)
            record.trivial_threshold = record.overall_materiality * (record.trivial_percentage / 100.0)


# ═══════════════════════════════════════════════════════════════════════
# P-6: Risk Assessment - Risk of Material Misstatement (ISA 315)
# ═══════════════════════════════════════════════════════════════════════
class PlanningP6Risk(models.Model):
    _name = "audit.planning.p6.risk"
    _description = "P-6: Risk Assessment (RMM)"
    _inherit = ["audit.planning.tab.mixin"]

    # Risk Assessment Approach
    risk_assessment_approach = fields.Html(
        string="Risk Assessment Approach",
        help="Methodology for identifying and assessing risks.",
    )
    
    # FS-Level Risks
    fs_risk_ids = fields.One2many(
        "audit.planning.p6.risk.fs",
        "p6_id",
        string="Financial Statement Level Risks",
    )
    
    # Assertion-Level Risks
    assertion_risk_ids = fields.One2many(
        "audit.planning.p6.risk.assertion",
        "p6_id",
        string="Assertion Level Risks",
    )
    
    # Significant Risks
    significant_risk_summary = fields.Html(
        string="Significant Risks Summary",
        help="Summary of identified significant risks.",
    )
    
    # Risk Response Overview
    risk_response_overview = fields.Html(
        string="Overall Risk Response",
        help="High-level response to identified risks.",
    )
    
    # Aggregated Risk Level
    aggregated_risk_level = fields.Selection([
        ("low", "Low"),
        ("moderate", "Moderate"),
        ("high", "High"),
    ], string="Aggregated RoMM", compute="_compute_aggregated_risk", store=True)

    @api.depends("fs_risk_ids.risk_level", "assertion_risk_ids.risk_level")
    def _compute_aggregated_risk(self):
        for record in self:
            levels = []
            levels.extend(record.fs_risk_ids.mapped("risk_level"))
            levels.extend(record.assertion_risk_ids.mapped("risk_level"))
            if "high" in levels:
                record.aggregated_risk_level = "high"
            elif "moderate" in levels:
                record.aggregated_risk_level = "moderate"
            else:
                record.aggregated_risk_level = "low"


class PlanningP6RiskFS(models.Model):
    _name = "audit.planning.p6.risk.fs"
    _description = "FS-Level Risk"
    _order = "sequence, id"

    p6_id = fields.Many2one(
        "audit.planning.p6.risk",
        string="Risk Assessment",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(default=10)
    name = fields.Char(string="Risk Description", required=True)
    risk_category = fields.Selection([
        ("pervasive", "Pervasive"),
        ("specific", "Specific"),
    ], string="Category")
    risk_level = fields.Selection([
        ("low", "Low"),
        ("moderate", "Moderate"),
        ("high", "High"),
    ], string="Risk Level", required=True)
    is_significant = fields.Boolean(string="Significant Risk")
    response = fields.Text(string="Planned Response")


class PlanningP6RiskAssertion(models.Model):
    _name = "audit.planning.p6.risk.assertion"
    _description = "Assertion-Level Risk"
    _order = "account_cycle, assertion_type"

    p6_id = fields.Many2one(
        "audit.planning.p6.risk",
        string="Risk Assessment",
        required=True,
        ondelete="cascade",
    )
    account_cycle = fields.Selection([
        ("revenue", "Revenue"),
        ("purchases", "Purchases & Payables"),
        ("payroll", "Payroll"),
        ("inventory", "Inventory"),
        ("fixed_assets", "Fixed Assets"),
        ("cash_bank", "Cash & Bank"),
        ("borrowings", "Borrowings"),
        ("related_parties", "Related Parties"),
        ("equity", "Equity"),
        ("other", "Other"),
    ], string="Account/Cycle", required=True)
    assertion_type = fields.Selection([
        ("existence", "Existence/Occurrence"),
        ("completeness", "Completeness"),
        ("accuracy", "Accuracy/Valuation"),
        ("cutoff", "Cut-off"),
        ("classification", "Classification"),
        ("rights", "Rights & Obligations"),
        ("presentation", "Presentation & Disclosure"),
    ], string="Assertion", required=True)
    risk_description = fields.Text(string="Risk Description")
    inherent_risk = fields.Selection([
        ("low", "Low"),
        ("moderate", "Moderate"),
        ("high", "High"),
    ], string="Inherent Risk", default="moderate")
    control_risk = fields.Selection([
        ("low", "Low"),
        ("moderate", "Moderate"),
        ("high", "High"),
    ], string="Control Risk", default="moderate")
    risk_level = fields.Selection([
        ("low", "Low"),
        ("moderate", "Moderate"),
        ("high", "High"),
    ], string="RoMM", compute="_compute_risk_level", store=True)
    is_significant = fields.Boolean(string="Significant Risk")
    planned_procedures = fields.Text(string="Planned Audit Procedures")

    @api.depends("inherent_risk", "control_risk")
    def _compute_risk_level(self):
        risk_matrix = {
            ("high", "high"): "high",
            ("high", "moderate"): "high",
            ("high", "low"): "moderate",
            ("moderate", "high"): "high",
            ("moderate", "moderate"): "moderate",
            ("moderate", "low"): "low",
            ("low", "high"): "moderate",
            ("low", "moderate"): "low",
            ("low", "low"): "low",
        }
        for record in self:
            key = (record.inherent_risk or "moderate", record.control_risk or "moderate")
            record.risk_level = risk_matrix.get(key, "moderate")
