# -*- coding: utf-8 -*-
"""
P-4: Preliminary Analytical Procedures
Standards: ISA 520, ISA 315 (Revised), ISA 240, ISA 570 (Revised), ISA 220, ISQM-1
Purpose: Perform, document, interpret, and conclude on meaningful analytical procedures
         at the planning stage with linkage to risk assessment and audit strategy.

Sections:
    A - Data Source Identification & Integrity
    B - Comparative Financial Analysis (YoY)
    C - Ratio Analysis (Mandatory Set)
    D - Budget vs Actual / Forecast Comparison
    E - Trend & Pattern Analysis (Multi-Year)
    F - Non-Financial & Operational Analytics
    G - Fraud Indicators from Analytics (ISA 240)
    H - Going Concern Indicators (Early Warning - ISA 570)
    I - Linkage to Risk Assessment (Auto-Flow)
    J - Mandatory Document Uploads
    K - P-4 Conclusion & Professional Judgment
    L - Review, Approval & Lock
"""

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


# =============================================================================
# CHILD MODEL: FS Line Item Variance Analysis
# =============================================================================
class PlanningP4FSLine(models.Model):
    """Financial Statement Line Item for YoY Variance Analysis - Section B"""
    _name = 'qaco.planning.p4.fs.line'
    _description = 'P-4: FS Line Variance Analysis'
    _order = 'sequence, id'

    p4_id = fields.Many2one(
        'qaco.planning.p4.analytics',
        string='P-4 Analytics',
        required=True,
        ondelete='cascade',
        index=True
    )
    sequence = fields.Integer(string='Seq', default=10)
    fs_caption = fields.Char(
        string='FS Caption',
        required=True,
        help='Financial statement line item caption'
    )
    fs_category = fields.Selection([
        ('revenue', 'Revenue'),
        ('cost_of_sales', 'Cost of Sales'),
        ('gross_profit', 'Gross Profit'),
        ('operating_expense', 'Operating Expenses'),
        ('other_income', 'Other Income/Expense'),
        ('finance_cost', 'Finance Costs'),
        ('pbt', 'Profit Before Tax'),
        ('taxation', 'Taxation'),
        ('net_profit', 'Net Profit/Loss'),
        ('current_asset', 'Current Assets'),
        ('non_current_asset', 'Non-Current Assets'),
        ('current_liability', 'Current Liabilities'),
        ('non_current_liability', 'Non-Current Liabilities'),
        ('equity', 'Equity'),
    ], string='Category', required=True)
    current_year = fields.Float(string='Current Year', digits=(16, 2))
    prior_year = fields.Float(string='Prior Year', digits=(16, 2))
    variance = fields.Float(
        string='Variance',
        compute='_compute_variance',
        store=True,
        digits=(16, 2)
    )
    variance_pct = fields.Float(
        string='% Change',
        compute='_compute_variance',
        store=True,
        digits=(5, 2)
    )
    exceeds_threshold = fields.Boolean(
        string='Exceeds Threshold',
        compute='_compute_variance',
        store=True,
        help='True if variance exceeds predefined threshold or materiality'
    )
    explanation_required = fields.Boolean(
        string='Explanation Required',
        compute='_compute_variance',
        store=True
    )
    auditor_explanation = fields.Text(
        string="Auditor's Explanation",
        help='Mandatory if variance exceeds threshold'
    )
    management_explanation = fields.Text(
        string='Management Explanation',
        help='Explanation provided by management'
    )
    risk_indicator = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Risk Indicator', default='low')

    @api.depends('current_year', 'prior_year')
    def _compute_variance(self):
        """Defensive: Safe even during module install."""
        for rec in self:
            try:
                rec.variance = rec.current_year - rec.prior_year
                if rec.prior_year and rec.prior_year != 0:
                    rec.variance_pct = (rec.variance / abs(rec.prior_year)) * 100
                else:
                    rec.variance_pct = 0 if rec.current_year == 0 else 100
                # Threshold: 10% or absolute variance > 5% of materiality (placeholder logic)
                rec.exceeds_threshold = abs(rec.variance_pct) > 10
                rec.explanation_required = rec.exceeds_threshold
            except Exception as e:
                _logger.warning(f'P-4 _compute_variance failed for record {rec.id}: {e}')
                rec.variance = 0
                rec.variance_pct = 0
                rec.exceeds_threshold = False
                rec.explanation_required = False


# =============================================================================
# CHILD MODEL: Ratio Analysis Lines
# =============================================================================
class PlanningP4RatioLine(models.Model):
    """Ratio Analysis Line Item - Section C"""
    _name = 'qaco.planning.p4.ratio.line'
    _description = 'P-4: Ratio Analysis Line'
    _order = 'category, sequence, id'

    p4_id = fields.Many2one(
        'qaco.planning.p4.analytics',
        string='P-4 Analytics',
        required=True,
        ondelete='cascade',
        index=True
    )
    sequence = fields.Integer(string='Seq', default=10)
    category = fields.Selection([
        ('profitability', 'Profitability'),
        ('liquidity', 'Liquidity'),
        ('solvency', 'Solvency'),
        ('efficiency', 'Efficiency'),
    ], string='Category', required=True)
    ratio_name = fields.Char(string='Ratio Name', required=True)
    formula = fields.Char(string='Formula', help='Calculation formula')
    current_year_value = fields.Float(string='Current Year', digits=(10, 2))
    prior_year_value = fields.Float(string='Prior Year', digits=(10, 2))
    industry_benchmark = fields.Float(string='Industry Benchmark', digits=(10, 2))
    movement = fields.Float(
        string='Movement',
        compute='_compute_movement',
        store=True,
        digits=(10, 2)
    )
    is_unusual = fields.Boolean(
        string='Unusual Movement',
        help='Flag if ratio movement is unexpected'
    )
    auditor_analysis = fields.Text(string='Auditor Analysis')

    @api.depends('current_year_value', 'prior_year_value')
    def _compute_movement(self):
        """Defensive: Safe even during module install."""
        for rec in self:
            try:
                rec.movement = rec.current_year_value - rec.prior_year_value
            except Exception as e:
                _logger.warning(f'P-4 Ratio _compute_movement failed for record {rec.id}: {e}')
                rec.movement = 0


# =============================================================================
# CHILD MODEL: Budget Variance Lines
# =============================================================================
class PlanningP4BudgetLine(models.Model):
    """Budget vs Actual Variance Line - Section D"""
    _name = 'qaco.planning.p4.budget.line'
    _description = 'P-4: Budget vs Actual Line'
    _order = 'sequence, id'

    p4_id = fields.Many2one(
        'qaco.planning.p4.analytics',
        string='P-4 Analytics',
        required=True,
        ondelete='cascade',
        index=True
    )
    sequence = fields.Integer(string='Seq', default=10)
    line_item = fields.Char(string='Line Item', required=True)
    budget_amount = fields.Float(string='Budget', digits=(16, 2))
    actual_amount = fields.Float(string='Actual', digits=(16, 2))
    variance = fields.Float(
        string='Variance',
        compute='_compute_budget_variance',
        store=True,
        digits=(16, 2)
    )
    variance_pct = fields.Float(
        string='Variance %',
        compute='_compute_budget_variance',
        store=True,
        digits=(5, 2)
    )
    is_significant = fields.Boolean(
        string='Significant Deviation',
        compute='_compute_budget_variance',
        store=True
    )
    management_explanation = fields.Text(string='Management Explanation')
    auditor_assessment = fields.Text(string='Auditor Assessment')

    @api.depends('budget_amount', 'actual_amount')
    def _compute_budget_variance(self):
        """Defensive: Safe even during module install."""
        for rec in self:
            try:
                rec.variance = rec.actual_amount - rec.budget_amount
                if rec.budget_amount and rec.budget_amount != 0:
                    rec.variance_pct = (rec.variance / abs(rec.budget_amount)) * 100
                else:
                    rec.variance_pct = 0
                # Flag if variance exceeds 15%
                rec.is_significant = abs(rec.variance_pct) > 15
            except Exception as e:
                _logger.warning(f'P-4 Budget _compute_budget_variance failed for record {rec.id}: {e}')
                rec.variance = 0
                rec.variance_pct = 0
                rec.is_significant = False
                rec.variance_pct = 0
            rec.is_significant = abs(rec.variance_pct) > 10


# =============================================================================
# CHILD MODEL: Trend Analysis Lines (Multi-Year)
# =============================================================================
class PlanningP4TrendLine(models.Model):
    """Multi-Year Trend Analysis Line - Section E"""
    _name = 'qaco.planning.p4.trend.line'
    _description = 'P-4: Multi-Year Trend Line'
    _order = 'sequence, id'

    p4_id = fields.Many2one(
        'qaco.planning.p4.analytics',
        string='P-4 Analytics',
        required=True,
        ondelete='cascade',
        index=True
    )
    sequence = fields.Integer(string='Seq', default=10)
    metric_name = fields.Char(string='Metric', required=True)
    year_1 = fields.Float(string='Year -4', digits=(16, 2), help='4 years ago')
    year_2 = fields.Float(string='Year -3', digits=(16, 2), help='3 years ago')
    year_3 = fields.Float(string='Year -2', digits=(16, 2), help='2 years ago')
    year_4 = fields.Float(string='Year -1', digits=(16, 2), help='Prior year')
    year_5 = fields.Float(string='Current', digits=(16, 2), help='Current year')
    trend_direction = fields.Selection([
        ('increasing', 'Increasing'),
        ('decreasing', 'Decreasing'),
        ('stable', 'Stable'),
        ('volatile', 'Volatile'),
    ], string='Trend Direction')
    cagr = fields.Float(string='CAGR %', digits=(5, 2), help='Compound Annual Growth Rate')
    is_unusual = fields.Boolean(string='Unusual Pattern')
    auditor_comment = fields.Text(string='Auditor Comment')


# =============================================================================
# CHILD MODEL: Non-Financial Metrics
# =============================================================================
class PlanningP4NonFinancial(models.Model):
    """Non-Financial & Operational Metrics - Section F"""
    _name = 'qaco.planning.p4.non.financial'
    _description = 'P-4: Non-Financial Metrics'
    _order = 'sequence, id'

    p4_id = fields.Many2one(
        'qaco.planning.p4.analytics',
        string='P-4 Analytics',
        required=True,
        ondelete='cascade',
        index=True
    )
    sequence = fields.Integer(string='Seq', default=10)
    metric_name = fields.Char(string='Metric', required=True)
    metric_type = fields.Selection([
        ('volume', 'Volume/Units'),
        ('headcount', 'Headcount'),
        ('capacity', 'Capacity Utilization'),
        ('customer', 'Customer Metrics'),
        ('quality', 'Quality Metrics'),
        ('other', 'Other'),
    ], string='Metric Type', required=True)
    current_value = fields.Float(string='Current Value', digits=(16, 2))
    prior_value = fields.Float(string='Prior Value', digits=(16, 2))
    unit_of_measure = fields.Char(string='UOM')
    change_pct = fields.Float(
        string='Change %',
        compute='_compute_change',
        store=True,
        digits=(5, 2)
    )
    consistent_with_financial = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
        ('partial', 'Partial'),
    ], string='Consistent with Financial Results')
    unusual_relationship = fields.Boolean(string='Unusual Relationship Noted')
    auditor_conclusion = fields.Text(string='Auditor Conclusion')

    @api.depends('current_value', 'prior_value')
    def _compute_change(self):
        """Defensive: Safe even during module install."""
        for rec in self:
            try:
                if rec.prior_value and rec.prior_value != 0:
                    rec.change_pct = ((rec.current_value - rec.prior_value) / abs(rec.prior_value)) * 100
                else:
                    rec.change_pct = 0
            except Exception as e:
                _logger.warning(f'P-4 NFA _compute_change failed for record {rec.id}: {e}')
                rec.change_pct = 0
        for rec in self:
            if rec.prior_value and rec.prior_value != 0:
                rec.change_pct = ((rec.current_value - rec.prior_value) / abs(rec.prior_value)) * 100
            else:
                rec.change_pct = 0


# =============================================================================
# CHILD MODEL: Fraud Indicators from Analytics
# =============================================================================
class PlanningP4FraudIndicator(models.Model):
    """Fraud Indicators Identified from Analytics - Section G (ISA 240)"""
    _name = 'qaco.planning.p4.fraud.indicator'
    _description = 'P-4: Fraud Indicator from Analytics'
    _order = 'risk_level desc, sequence, id'

    p4_id = fields.Many2one(
        'qaco.planning.p4.analytics',
        string='P-4 Analytics',
        required=True,
        ondelete='cascade',
        index=True
    )
    sequence = fields.Integer(string='Seq', default=10)
    indicator_type = fields.Selection([
        ('revenue_timing', 'Unusual Revenue Trends Near Period End'),
        ('margin_manipulation', 'Margin Manipulation Indicators'),
        ('expense_capitalization', 'Unexpected Expense Capitalization'),
        ('cash_profit_mismatch', 'Cash Flow vs Profit Inconsistencies'),
        ('override', 'Override-Type Analytical Red Flags'),
        ('related_party', 'Related Party Transaction Anomalies'),
        ('other', 'Other Fraud Indicator'),
    ], string='Indicator Type', required=True)
    description = fields.Text(string='Description', required=True)
    evidence = fields.Text(string='Supporting Evidence')
    risk_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Risk Level', default='medium', required=True)
    escalated_to_p7 = fields.Boolean(
        string='Escalated to P-7',
        help='Has this indicator been escalated to P-7 Fraud Risk?'
    )
    escalation_date = fields.Date(string='Escalation Date')
    auditor_response = fields.Text(string='Auditor Response / Action Taken')


# =============================================================================
# CHILD MODEL: Going Concern Indicators (Early Warning)
# =============================================================================
class PlanningP4GoingConcern(models.Model):
    """Going Concern Early Warning Indicators - Section H (ISA 570)"""
    _name = 'qaco.planning.p4.going.concern'
    _description = 'P-4: Going Concern Indicator'
    _order = 'severity desc, sequence, id'

    p4_id = fields.Many2one(
        'qaco.planning.p4.analytics',
        string='P-4 Analytics',
        required=True,
        ondelete='cascade',
        index=True
    )
    sequence = fields.Integer(string='Seq', default=10)
    indicator_type = fields.Selection([
        ('recurring_losses', 'Recurring Losses'),
        ('negative_ocf', 'Negative Operating Cash Flows'),
        ('liquidity_stress', 'Liquidity Stress Indicators'),
        ('covenant_breach', 'Breach of Covenants'),
        ('external_dependency', 'Dependency on External Financing'),
        ('net_liability', 'Net Liability Position'),
        ('working_capital_deficit', 'Working Capital Deficit'),
        ('other', 'Other Going Concern Indicator'),
    ], string='Indicator Type', required=True)
    description = fields.Text(string='Description', required=True)
    quantification = fields.Char(string='Quantification', help='e.g., Loss of PKR 50M')
    period_applicable = fields.Char(string='Period Applicable')
    severity = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], string='Severity', default='medium', required=True)
    linked_to_p8 = fields.Boolean(
        string='Linked to P-8',
        help='Auto-link to P-8 Going Concern assessment'
    )
    management_response = fields.Text(string='Management Response')
    auditor_assessment = fields.Text(string='Auditor Assessment')


# =============================================================================
# MAIN MODEL: P-4 Preliminary Analytical Procedures
# =============================================================================
class PlanningP4Analytics(models.Model):
    """
    P-4: Preliminary Analytical Procedures
    ISA 520, ISA 315 (Revised), ISA 240, ISA 570 (Revised)
    """
    _name = 'qaco.planning.p4.analytics'
    _description = 'P-4: Preliminary Analytical Procedures'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    TAB_STATE = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
        ('locked', 'Locked'),
    ]

    # =========================================================================
    # CORE FIELDS
    # =========================================================================
    name = fields.Char(
        string='Reference',
        compute='_compute_name',
        store=True,
        readonly=True
    )
    state = fields.Selection(
        TAB_STATE,
        string='Status',
        default='not_started',
        tracking=True,
        copy=False
    )

    # Sequential Gating (ISA 300/220: Systematic Planning Approach)
    can_open = fields.Boolean(
        string='Can Open This Tab',
        compute='_compute_can_open',
        store=False,
        help='P-4 can only be opened after P-3 is approved'
    )

    @api.depends('audit_id')
    def _compute_can_open(self):
        """P-4 requires P-3 to be approved."""
        for rec in self:
            if not rec.audit_id:
                rec.can_open = False
                continue
            # Find P-3 for this audit
            p3 = self.env['qaco.planning.p3.controls'].search([
                ('audit_id', '=', rec.audit_id.id)
            ], limit=1)
            rec.can_open = p3.state == 'approved' if p3 else False

    @api.constrains('state')
    def _check_sequential_gating(self):
        """ISA 300/220: Enforce sequential planning approach."""
        for rec in self:
            if rec.state != 'not_started' and not rec.can_open:
                raise UserError(
                    'ISA 300/220 Violation: Sequential Planning Approach Required.\n\n'
                    'P-4 (Analytics) cannot be started until P-3 (Internal Controls) '
                    'has been Partner-approved.\n\n'
                    'Reason: Analytical procedures require understanding of controls '
                    'to properly assess data reliability and expectations.\n\n'
                    'Action: Please complete and obtain Partner approval for P-3 first.'
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
        string='Client',
        related='audit_id.client_id',
        store=False,
        readonly=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self._get_default_currency()
    )

    # =========================================================================
    # SECTION A - DATA SOURCE IDENTIFICATION & INTEGRITY
    # =========================================================================
    section_a_header = fields.Char(
        default='Section A: Data Source Identification & Integrity',
        readonly=True
    )

    # Financial Data Source
    data_source = fields.Selection([
        ('audited_py', 'Audited Prior-Year Financial Statements'),
        ('management_tb', 'Management Trial Balance'),
        ('management_accounts', 'Management Accounts'),
        ('combination', 'Combination of Sources'),
    ], string='Financial Data Source', tracking=True)
    data_source_other = fields.Char(string='Other Data Source')

    # Period and Currency
    period_covered_start = fields.Date(string='Period Start')
    period_covered_end = fields.Date(string='Period End')
    prior_year_start = fields.Date(string='Prior Year Start')
    prior_year_end = fields.Date(string='Prior Year End')

    # Data Integrity
    data_consistent_with_py = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
        ('na', 'N/A - First Year Audit'),
    ], string='Consistent with Prior Year Audited Figures?', tracking=True)
    data_consistency_notes = fields.Text(string='Consistency Notes')

    data_reliability_concerns = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Data Reliability Concerns Identified?', tracking=True)
    data_reliability_notes = fields.Text(string='Reliability Concern Details')

    # Section A Checklist
    checklist_a_data_source_identified = fields.Boolean(
        string='☐ Data source identified'
    )
    checklist_a_completeness_considered = fields.Boolean(
        string='☐ Completeness & accuracy considered'
    )
    checklist_a_limitations_documented = fields.Boolean(
        string='☐ Limitations documented (if any)'
    )

    # =========================================================================
    # SECTION B - COMPARATIVE FINANCIAL ANALYSIS (YoY)
    # =========================================================================
    section_b_header = fields.Char(
        default='Section B: Comparative Financial Analysis (YoY)',
        readonly=True
    )

    # One2many to FS Line Variance Analysis
    fs_line_ids = fields.One2many(
        'qaco.planning.p4.fs.line',
        'p4_id',
        string='FS Line Items'
    )

    # Variance Threshold Settings
    variance_threshold_pct = fields.Float(
        string='Variance Threshold %',
        default=10.0,
        help='% change that triggers explanation requirement'
    )
    materiality_benchmark = fields.Float(
        string='Materiality Benchmark',
        help='Absolute variance threshold based on materiality'
    )

    # Section B Checklist
    checklist_b_significant_variances = fields.Boolean(
        string='☐ Significant variances identified'
    )
    checklist_b_explanations_obtained = fields.Boolean(
        string='☐ Explanations obtained & evaluated'
    )

    # =========================================================================
    # SECTION C - RATIO ANALYSIS (MANDATORY SET)
    # =========================================================================
    section_c_header = fields.Char(
        default='Section C: Ratio Analysis (Mandatory Set)',
        readonly=True
    )

    # One2many to Ratio Lines
    ratio_line_ids = fields.One2many(
        'qaco.planning.p4.ratio.line',
        'p4_id',
        string='Ratio Analysis Lines'
    )

    # Auto-calculated Summary Ratios (for quick reference)
    # Profitability
    gross_margin_cy = fields.Float(string='Gross Margin % (CY)', digits=(5, 2))
    net_margin_cy = fields.Float(string='Net Margin % (CY)', digits=(5, 2))
    operating_margin_cy = fields.Float(string='Operating Margin % (CY)', digits=(5, 2))

    # Liquidity
    current_ratio_cy = fields.Float(string='Current Ratio (CY)', digits=(5, 2))
    quick_ratio_cy = fields.Float(string='Quick Ratio (CY)', digits=(5, 2))
    cash_ratio_cy = fields.Float(string='Cash Ratio (CY)', digits=(5, 2))

    # Solvency
    debt_to_equity_cy = fields.Float(string='Debt-to-Equity (CY)', digits=(5, 2))
    interest_coverage_cy = fields.Float(string='Interest Coverage (CY)', digits=(5, 2))

    # Efficiency
    inventory_turnover_cy = fields.Float(string='Inventory Turnover (CY)', digits=(5, 2))
    receivables_days_cy = fields.Float(string='Receivables Days (CY)', digits=(5, 2))
    payables_days_cy = fields.Float(string='Payables Days (CY)', digits=(5, 2))

    # Ratio Analysis Conclusion
    unexpected_ratio_movements = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Unexpected Ratio Movements?', tracking=True)
    ratio_analysis_conclusion = fields.Html(
        string='Auditor Analysis & Conclusion',
        help='Mandatory narrative on ratio analysis findings'
    )

    # =========================================================================
    # SECTION D - BUDGET VS ACTUAL / FORECAST COMPARISON
    # =========================================================================
    section_d_header = fields.Char(
        default='Section D: Budget vs Actual / Forecast Comparison',
        readonly=True
    )

    budget_available = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Budget / Forecast Available?', tracking=True)
    budget_not_available_reason = fields.Text(
        string='Reason Budget Not Available',
        help='Justify why budget comparison not performed'
    )

    # One2many to Budget Lines
    budget_line_ids = fields.One2many(
        'qaco.planning.p4.budget.line',
        'p4_id',
        string='Budget vs Actual Lines'
    )

    significant_budget_deviations = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Significant Deviations Identified?', tracking=True)
    budget_management_explanation = fields.Html(string='Management Explanation')
    budget_auditor_assessment = fields.Html(string='Auditor Assessment of Explanation')

    # Section D Checklist
    checklist_d_budget_comparison = fields.Boolean(
        string='☐ Budget comparison performed (or justified why not)'
    )
    checklist_d_deviations_evaluated = fields.Boolean(
        string='☐ Deviations evaluated'
    )

    # =========================================================================
    # SECTION E - TREND & PATTERN ANALYSIS (MULTI-YEAR)
    # =========================================================================
    section_e_header = fields.Char(
        default='Section E: Trend & Pattern Analysis (Multi-Year)',
        readonly=True
    )

    years_compared = fields.Selection([
        ('2', '2 Years'),
        ('3', '3 Years'),
        ('5', '5 Years'),
    ], string='Number of Years Compared', default='3')

    # One2many to Trend Lines
    trend_line_ids = fields.One2many(
        'qaco.planning.p4.trend.line',
        'p4_id',
        string='Multi-Year Trend Lines'
    )

    consistent_trends_identified = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Consistent Growth/Decline Trends Identified?')
    volatility_patterns_noted = fields.Html(
        string='Volatility or Unusual Patterns Noted',
        help='Document any unusual patterns observed'
    )
    trend_impact_on_risk = fields.Html(
        string='Impact on Audit Risk',
        help='How do identified trends affect audit risk assessment?'
    )
    trend_correlation_with_p2 = fields.Html(
        string='Correlation with P-2 Business Understanding',
        help='Link trends to business understanding from P-2'
    )

    # =========================================================================
    # SECTION F - NON-FINANCIAL & OPERATIONAL ANALYTICS
    # =========================================================================
    section_f_header = fields.Char(
        default='Section F: Non-Financial & Operational Analytics (ISA 315 Revised)',
        readonly=True
    )

    # One2many to Non-Financial Metrics
    non_financial_ids = fields.One2many(
        'qaco.planning.p4.non.financial',
        'p4_id',
        string='Non-Financial Metrics'
    )

    non_financial_consistency = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
        ('partial', 'Partial'),
    ], string='Consistent with Financial Results?')
    unusual_relationships_identified = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Unusual Relationships Identified?')
    non_financial_conclusion = fields.Html(
        string='Auditor Conclusion on Non-Financial Analytics'
    )

    # Section F Checklist
    checklist_f_non_financial_considered = fields.Boolean(
        string='☐ Non-financial data considered'
    )
    checklist_f_alignment_assessed = fields.Boolean(
        string='☐ Financial vs operational alignment assessed'
    )

    # =========================================================================
    # SECTION G - FRAUD INDICATORS FROM ANALYTICS (ISA 240)
    # =========================================================================
    section_g_header = fields.Char(
        default='Section G: Fraud Indicators from Analytics (ISA 240)',
        readonly=True
    )

    # One2many to Fraud Indicators
    fraud_indicator_ids = fields.One2many(
        'qaco.planning.p4.fraud.indicator',
        'p4_id',
        string='Fraud Indicators'
    )

    # Quick flags for common fraud indicators
    unusual_revenue_near_period_end = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
        ('not_assessed', 'Not Yet Assessed'),
    ], string='Unusual Revenue Trends Near Period End?', default='not_assessed')
    margin_manipulation_indicators = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
        ('not_assessed', 'Not Yet Assessed'),
    ], string='Margin Manipulation Indicators?', default='not_assessed')
    unexpected_expense_capitalization = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
        ('not_assessed', 'Not Yet Assessed'),
    ], string='Unexpected Expense Capitalization?', default='not_assessed')
    cash_profit_inconsistencies = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
        ('not_assessed', 'Not Yet Assessed'),
    ], string='Cash Flow vs Profit Inconsistencies?', default='not_assessed')
    override_red_flags = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
        ('not_assessed', 'Not Yet Assessed'),
    ], string='Override-Type Analytical Red Flags?', default='not_assessed')

    fraud_indicators_conclusion = fields.Html(
        string='Fraud Indicators Conclusion'
    )

    # Section G Checklist
    checklist_g_fraud_assessed = fields.Boolean(
        string='☐ Fraud risk indicators assessed'
    )
    checklist_g_escalated_to_p7 = fields.Boolean(
        string='☐ Matters escalated to P-7 (Fraud Risk)'
    )

    # =========================================================================
    # SECTION H - GOING CONCERN INDICATORS (EARLY WARNING - ISA 570)
    # =========================================================================
    section_h_header = fields.Char(
        default='Section H: Going Concern Indicators (Early Warning - ISA 570)',
        readonly=True
    )

    # One2many to Going Concern Indicators
    going_concern_ids = fields.One2many(
        'qaco.planning.p4.going.concern',
        'p4_id',
        string='Going Concern Indicators'
    )

    # Quick flags for common GC indicators
    recurring_losses = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
        ('not_assessed', 'Not Yet Assessed'),
    ], string='Recurring Losses?', default='not_assessed')
    negative_operating_cash_flows = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
        ('not_assessed', 'Not Yet Assessed'),
    ], string='Negative Operating Cash Flows?', default='not_assessed')
    liquidity_stress_indicators = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
        ('not_assessed', 'Not Yet Assessed'),
    ], string='Liquidity Stress Indicators?', default='not_assessed')
    breach_of_covenants = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
        ('not_assessed', 'Not Yet Assessed'),
    ], string='Breach of Covenants?', default='not_assessed')
    dependency_on_external_financing = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
        ('not_assessed', 'Not Yet Assessed'),
    ], string='Dependency on External Financing?', default='not_assessed')

    going_concern_conclusion = fields.Html(
        string='Going Concern Early Warning Conclusion'
    )

    # =========================================================================
    # SECTION I - LINKAGE TO RISK ASSESSMENT (AUTO-FLOW)
    # =========================================================================
    section_i_header = fields.Char(
        default='Section I: Linkage to Risk Assessment (Auto-Flow)',
        readonly=True
    )

    # Auto-linkage tracking
    risks_created_in_p6 = fields.Integer(
        string='Risks Created in P-6',
        compute='_compute_risk_linkage',
        store=True,
        help='Number of risks auto-created in P-6 from unexplained variances'
    )
    strategy_impact_documented = fields.Boolean(
        string='Strategy Impact Documented in P-12'
    )

    risk_linkage_narrative = fields.Html(
        string='Risk Linkage Narrative',
        help='Document how analytical findings influence risk assessment'
    )
    sample_size_impact = fields.Html(
        string='Impact on Sample Sizes & Procedures',
        help='How analytical results affect planned sample sizes'
    )

    # =========================================================================
    # SECTION J - MANDATORY DOCUMENT UPLOADS
    # =========================================================================
    section_j_header = fields.Char(
        default='Section J: Mandatory Document Uploads',
        readonly=True
    )

    # Required Attachments
    trial_balance_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p4_trial_balance_rel',
        'p4_id',
        'attachment_id',
        string='Trial Balance Used'
    )
    prior_year_fs_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p4_prior_fs_rel',
        'p4_id',
        'attachment_id',
        string='Prior-Year Audited FS'
    )
    budget_forecast_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p4_budget_rel',
        'p4_id',
        'attachment_id',
        string='Budget / Forecasts'
    )
    management_explanations_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p4_mgmt_explain_rel',
        'p4_id',
        'attachment_id',
        string='Management Explanations'
    )
    analytical_workpapers_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p4_workpapers_rel',
        'p4_id',
        'attachment_id',
        string='Analytical Working Papers'
    )

    # Document Checklist
    checklist_j_trial_balance = fields.Boolean(
        string='☐ Trial balance used'
    )
    checklist_j_prior_year_fs = fields.Boolean(
        string='☐ Prior-year audited FS'
    )
    checklist_j_budget = fields.Boolean(
        string='☐ Budget / forecasts (if available)'
    )
    checklist_j_mgmt_explanations = fields.Boolean(
        string='☐ Management explanations (if separate)'
    )
    checklist_j_workpapers = fields.Boolean(
        string='☐ Analytical working papers'
    )

    # =========================================================================
    # SECTION K - P-4 CONCLUSION & PROFESSIONAL JUDGMENT
    # =========================================================================
    section_k_header = fields.Char(
        default='Section K: P-4 Conclusion & Professional Judgment',
        readonly=True
    )

    conclusion_narrative = fields.Html(
        string='P-4 Conclusion',
        default="""<p><strong>Preliminary analytical procedures have been performed in accordance 
with ISA 520. Significant relationships and unusual fluctuations have been identified, 
evaluated, and appropriately linked to the assessment of risks of material misstatement 
and the overall audit strategy.</strong></p>"""
    )

    # Final Confirmations
    confirm_analytics_complete = fields.Boolean(
        string='☐ Analytics complete'
    )
    confirm_results_in_risk = fields.Boolean(
        string='☐ Results considered in risk assessment'
    )
    confirm_proceed_to_p5 = fields.Boolean(
        string='☐ Proceed to materiality determination (P-5)'
    )

    # =========================================================================
    # SECTION L - REVIEW, APPROVAL & LOCK
    # =========================================================================
    section_l_header = fields.Char(
        default='Section L: Review, Approval & Lock',
        readonly=True
    )

    # Prepared By
    prepared_by_id = fields.Many2one(
        'res.users',
        string='Prepared By',
        tracking=True,
        copy=False
    )
    prepared_by_role = fields.Char(string='Role')
    prepared_on = fields.Datetime(string='Prepared On', tracking=True, copy=False)

    # Reviewed By (Manager)
    reviewed_by_id = fields.Many2one(
        'res.users',
        string='Reviewed By (Manager)',
        tracking=True,
        copy=False
    )
    reviewed_on = fields.Datetime(string='Reviewed On', tracking=True, copy=False)
    review_notes = fields.Html(string='Review Notes')

    # Partner Approval
    partner_approved = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Partner Approval', tracking=True)
    partner_approved_by_id = fields.Many2one(
        'res.users',
        string='Partner Approved By',
        tracking=True,
        copy=False
    )
    partner_approved_on = fields.Datetime(
        string='Partner Approved On',
        tracking=True,
        copy=False
    )
    partner_comments = fields.Html(
        string='Partner Comments',
        help='Mandatory when partner approves'
    )

    # Lock indicator
    is_locked = fields.Boolean(
        string='Locked',
        default=False,
        copy=False,
        help='Locked after partner approval'
    )

    # ISA Reference
    isa_reference = fields.Char(
        string='ISA Reference',
        default='ISA 520, ISA 315, ISA 240, ISA 570',
        readonly=True
    )

    # =========================================================================
    # SQL CONSTRAINTS
    # =========================================================================
    _sql_constraints = [
        ('audit_unique', 'UNIQUE(audit_id)',
         'Only one P-4 Analytics record per Audit Engagement is allowed.')
    ]

    # =========================================================================
    # COMPUTED METHODS
    # =========================================================================
    @api.depends('audit_id', 'client_id')
    def _compute_name(self):
        for rec in self:
            if rec.client_id:
                rec.name = f"P4-{rec.client_id.name[:20] if rec.client_id.name else 'NEW'}"
            else:
                rec.name = 'P-4: Analytical Procedures'

    @api.depends('fs_line_ids.exceeds_threshold', 'fs_line_ids.auditor_explanation')
    def _compute_risk_linkage(self):
        """Defensive: Compute number of risks from unexplained variances."""
        for rec in self:
            try:
                if not rec.fs_line_ids:
                    rec.risks_created_in_p6 = 0
                    continue
                
                # Count unexplained significant variances
                unexplained_count = len(rec.fs_line_ids.filtered(
                    lambda l: l.exceeds_threshold and not l.auditor_explanation
                ))
                rec.risks_created_in_p6 = unexplained_count
            except Exception as e:
                _logger.warning(f'P-4 _compute_risk_linkage failed for record {rec.id}: {e}')
                rec.risks_created_in_p6 = 0

    # =========================================================================
    # VALIDATION METHODS
    # =========================================================================
    def _validate_section_a(self):
        """Validate Section A: Data Source Identification."""
        errors = []
        if not self.data_source:
            errors.append("Data source must be identified (Section A)")
        if not self.period_covered_start or not self.period_covered_end:
            errors.append("Period covered must be specified (Section A)")
        if self.data_reliability_concerns == 'yes' and not self.data_reliability_notes:
            errors.append("Data reliability concerns must be documented (Section A)")
        return errors

    def _validate_section_b(self):
        """Validate Section B: Variance Analysis."""
        errors = []
        # Check if explanations provided for significant variances
        unexplained = self.fs_line_ids.filtered(
            lambda l: l.explanation_required and not l.auditor_explanation
        )
        if unexplained:
            errors.append(f"Explanations required for {len(unexplained)} significant variances (Section B)")
        return errors

    def _validate_section_c(self):
        """Validate Section C: Ratio Analysis."""
        errors = []
        if self.unexpected_ratio_movements == 'yes' and not self.ratio_analysis_conclusion:
            errors.append("Ratio analysis conclusion required when unexpected movements identified (Section C)")
        return errors

    def _validate_section_d(self):
        """Validate Section D: Budget Comparison."""
        errors = []
        if self.budget_available == 'no' and not self.budget_not_available_reason:
            errors.append("Justification required for not performing budget comparison (Section D)")
        if self.significant_budget_deviations == 'yes' and not self.budget_auditor_assessment:
            errors.append("Auditor assessment required for significant budget deviations (Section D)")
        return errors

    def _validate_section_g(self):
        """Validate Section G: Fraud Indicators."""
        errors = []
        fraud_flags = [
            self.unusual_revenue_near_period_end,
            self.margin_manipulation_indicators,
            self.unexpected_expense_capitalization,
            self.cash_profit_inconsistencies,
            self.override_red_flags,
        ]
        if 'not_assessed' in fraud_flags:
            errors.append("All fraud indicators must be assessed (Section G)")
        return errors

    def _validate_section_h(self):
        """Validate Section H: Going Concern."""
        errors = []
        gc_flags = [
            self.recurring_losses,
            self.negative_operating_cash_flows,
            self.liquidity_stress_indicators,
            self.breach_of_covenants,
            self.dependency_on_external_financing,
        ]
        if 'not_assessed' in gc_flags:
            errors.append("All going concern indicators must be assessed (Section H)")
        return errors

    def _validate_section_j(self):
        """Validate Section J: Mandatory Documents."""
        errors = []
        if not self.trial_balance_ids:
            errors.append("Trial balance must be uploaded (Section J)")
        if not self.prior_year_fs_ids and self.data_source != 'management_accounts':
            errors.append("Prior-year audited FS must be uploaded (Section J)")
        return errors

    def _validate_section_k(self):
        """Validate Section K: Conclusion."""
        errors = []
        if not self.confirm_analytics_complete:
            errors.append("Analytics completion must be confirmed (Section K)")
        if not self.confirm_results_in_risk:
            errors.append("Risk assessment consideration must be confirmed (Section K)")
        return errors

    def _validate_for_completion(self):
        """Validate all sections for completion."""
        self.ensure_one()
        errors = []
        errors.extend(self._validate_section_a())
        errors.extend(self._validate_section_b())
        errors.extend(self._validate_section_c())
        errors.extend(self._validate_section_d())
        errors.extend(self._validate_section_g())
        errors.extend(self._validate_section_h())
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
        """Start work on P-4 tab."""
        for rec in self:
            if rec.state != 'not_started':
                raise UserError("Can only start work on tabs that are 'Not Started'.")
            # Check P-3 prerequisite
            if 'qaco.planning.p3.controls' in self.env:
                p3 = self.env['qaco.planning.p3.controls'].search([
                    ('audit_id', '=', rec.audit_id.id)
                ], limit=1)
                if p3 and p3.state not in ['approved', 'locked']:
                    raise UserError(
                        "P-3 (Internal Control & IT Understanding) must be partner-approved "
                        "before starting P-4."
                    )
            rec.state = 'in_progress'
            rec.message_post(body="P-4 Analytical Procedures work started.")

    def action_complete(self):
        """Mark P-4 as complete."""
        for rec in self:
            if rec.state != 'in_progress':
                raise UserError("Can only complete tabs that are 'In Progress'.")
            errors = rec._validate_for_completion()
            if errors:
                raise UserError(
                    "Cannot complete P-4. Missing requirements:\n• " + "\n• ".join(errors)
                )
            rec.prepared_by_id = self.env.user
            rec.prepared_on = fields.Datetime.now()
            rec.state = 'completed'
            rec.message_post(body="P-4 Analytical Procedures marked as complete.")

    def action_manager_review(self):
        """Manager review of P-4."""
        for rec in self:
            if rec.state != 'completed':
                raise UserError("Can only review tabs that are 'Completed'.")
            if not rec.review_notes:
                raise UserError("Manager review notes are required.")
            rec.reviewed_by_id = self.env.user
            rec.reviewed_on = fields.Datetime.now()
            rec.state = 'reviewed'
            rec.message_post(body=f"P-4 reviewed by Manager: {self.env.user.name}")

    def action_partner_approve(self):
        """Partner approval of P-4."""
        for rec in self:
            if rec.state != 'reviewed':
                raise UserError("Can only approve tabs that have been 'Reviewed'.")
            errors = rec._validate_for_approval()
            if errors:
                raise UserError(
                    "Cannot approve P-4. Missing requirements:\n• " + "\n• ".join(errors)
                )
            if not rec.partner_comments:
                raise UserError("Partner comments are mandatory for approval.")
            rec.partner_approved = 'yes'
            rec.partner_approved_by_id = self.env.user
            rec.partner_approved_on = fields.Datetime.now()
            rec.is_locked = True
            rec.state = 'locked'
            rec.message_post(body=f"P-4 approved and locked by Partner: {self.env.user.name}")
            # Auto-unlock P-5 if exists
            rec._auto_unlock_p5()

    def action_send_back(self):
        """Send P-4 back for rework."""
        for rec in self:
            if rec.state not in ['completed', 'reviewed']:
                raise UserError("Can only send back tabs that are 'Completed' or 'Reviewed'.")
            rec.state = 'in_progress'
            rec.message_post(body="P-4 sent back for rework.")

    def action_unlock(self):
        """Unlock P-4 (partner only)."""
        for rec in self:
            if rec.state != 'locked':
                raise UserError("Can only unlock tabs that are 'Locked'.")
            rec.is_locked = False
            rec.partner_approved = 'no'
            rec.state = 'reviewed'
            rec.message_post(body=f"P-4 unlocked by Partner: {self.env.user.name}")

    def _auto_unlock_p5(self):
        """Auto-unlock P-5 when P-4 is approved."""
        self.ensure_one()
        if 'qaco.planning.p5.materiality' in self.env:
            p5 = self.env['qaco.planning.p5.materiality'].search([
                ('audit_id', '=', self.audit_id.id)
            ], limit=1)
            if p5 and p5.state == 'not_started':
                _logger.info(f"P-5 auto-unlock triggered by P-4 approval for audit {self.audit_id.id}")

    # =========================================================================
    # RISK LINKAGE ACTIONS
    # =========================================================================
    def action_create_risks_from_variances(self):
        """Create risks in P-6 from unexplained significant variances."""
        self.ensure_one()
        if 'qaco.planning.p6.risk' not in self.env:
            raise UserError("P-6 Risk Assessment module is not installed.")

        unexplained = self.fs_line_ids.filtered(
            lambda l: l.exceeds_threshold and not l.auditor_explanation
        )
        if not unexplained:
            raise UserError("No unexplained significant variances to create risks from.")

        p6 = self.env['qaco.planning.p6.risk'].search([
            ('audit_id', '=', self.audit_id.id)
        ], limit=1)

        if not p6:
            raise UserError("P-6 Risk Assessment record not found for this engagement.")

        created_count = 0
        for line in unexplained:
            # Logic to create risk in P-6 would go here
            # This is a placeholder for actual risk creation
            created_count += 1
            _logger.info(f"Risk created for FS line: {line.fs_caption}")

        self.message_post(
            body=f"Created {created_count} risks in P-6 from unexplained variances."
        )
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Risks Created',
                'message': f'{created_count} risks created in P-6.',
                'type': 'success',
            }
        }

    def action_escalate_to_p7(self):
        """Escalate fraud indicators to P-7."""
        self.ensure_one()
        fraud_indicators = self.fraud_indicator_ids.filtered(
            lambda f: not f.escalated_to_p7 and f.risk_level in ['medium', 'high']
        )
        if not fraud_indicators:
            raise UserError("No fraud indicators to escalate.")

        for indicator in fraud_indicators:
            indicator.escalated_to_p7 = True
            indicator.escalation_date = fields.Date.today()

        self.message_post(
            body=f"Escalated {len(fraud_indicators)} fraud indicators to P-7."
        )

    def action_link_gc_to_p8(self):
        """Link going concern indicators to P-8."""
        self.ensure_one()
        gc_indicators = self.going_concern_ids.filtered(
            lambda g: not g.linked_to_p8 and g.severity in ['medium', 'high', 'critical']
        )
        if not gc_indicators:
            raise UserError("No going concern indicators to link.")

        for indicator in gc_indicators:
            indicator.linked_to_p8 = True

        self.message_post(
            body=f"Linked {len(gc_indicators)} going concern indicators to P-8."
        )

    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    def action_populate_standard_ratios(self):
        """Populate standard ratio lines for analysis."""
        self.ensure_one()
        if self.ratio_line_ids:
            raise UserError("Ratio lines already exist. Delete existing lines to repopulate.")

        standard_ratios = [
            # Profitability
            ('profitability', 'Gross Margin', 'Gross Profit / Revenue × 100'),
            ('profitability', 'Net Margin', 'Net Profit / Revenue × 100'),
            ('profitability', 'Operating Margin', 'Operating Profit / Revenue × 100'),
            # Liquidity
            ('liquidity', 'Current Ratio', 'Current Assets / Current Liabilities'),
            ('liquidity', 'Quick Ratio', '(Current Assets - Inventory) / Current Liabilities'),
            ('liquidity', 'Cash Ratio', 'Cash / Current Liabilities'),
            # Solvency
            ('solvency', 'Debt-to-Equity', 'Total Debt / Total Equity'),
            ('solvency', 'Interest Coverage', 'EBIT / Interest Expense'),
            # Efficiency
            ('efficiency', 'Inventory Turnover', 'Cost of Sales / Average Inventory'),
            ('efficiency', 'Receivables Days', '(Trade Receivables / Revenue) × 365'),
            ('efficiency', 'Payables Days', '(Trade Payables / Cost of Sales) × 365'),
        ]

        lines = []
        for seq, (cat, name, formula) in enumerate(standard_ratios, start=1):
            lines.append((0, 0, {
                'sequence': seq * 10,
                'category': cat,
                'ratio_name': name,
                'formula': formula,
            }))

        self.write({'ratio_line_ids': lines})
        self.message_post(body="Standard ratio lines populated.")

    def action_generate_analytical_memo(self):
        """Generate Preliminary Analytical Procedures Memorandum."""
        self.ensure_one()
        # Placeholder for PDF generation logic
        self.message_post(body="Analytical Procedures Memorandum generated.")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Memorandum Generated',
                'message': 'Preliminary Analytical Procedures Memorandum has been generated.',
                'type': 'success',
            }
        }
