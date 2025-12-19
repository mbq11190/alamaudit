# -*- coding: utf-8 -*-
"""
P-4: Preliminary Analytical Procedures
Standard: ISA 520
Purpose: Identify unusual trends and risk indicators.
"""

from odoo import api, fields, models
from odoo.exceptions import UserError


class PlanningP4Analytics(models.Model):
    """P-4: Preliminary Analytical Procedures (ISA 520)"""
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
        tracking=True
    )
    planning_main_id = fields.Many2one(
        'qaco.planning.main',
        string='Planning Phase',
        ondelete='cascade'
    )
    client_id = fields.Many2one(
        'res.partner',
        string='Client Name',
        related='audit_id.client_id',
        readonly=True,
        store=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )

    # ===== Financial Year Dates =====
    current_year_end = fields.Date(
        string='Current Year End',
        help='End date of the current financial year under audit'
    )
    prior_year_end = fields.Date(
        string='Prior Year End',
        help='End date of the prior financial year for comparison'
    )

    # ===== Financial Data Input - XML Compatible Field Names =====
    # Current Year (short names for XML view compatibility)
    current_total_assets = fields.Monetary(string='Total Assets (Current Year)', currency_field='currency_id')
    current_total_liabilities = fields.Monetary(string='Total Liabilities (Current Year)', currency_field='currency_id')
    current_equity = fields.Monetary(string='Equity (Current Year)', currency_field='currency_id')
    current_revenue = fields.Monetary(string='Revenue (Current Year)', currency_field='currency_id')
    current_cost_of_sales = fields.Monetary(string='Cost of Sales (Current Year)', currency_field='currency_id')
    current_gross_profit = fields.Monetary(string='Gross Profit (Current Year)', currency_field='currency_id')

    # Prior Year (short names for XML view compatibility)
    prior_total_assets = fields.Monetary(string='Total Assets (Prior Year)', currency_field='currency_id')
    prior_total_liabilities = fields.Monetary(string='Total Liabilities (Prior Year)', currency_field='currency_id')
    prior_equity = fields.Monetary(string='Equity (Prior Year)', currency_field='currency_id')
    prior_revenue = fields.Monetary(string='Revenue (Prior Year)', currency_field='currency_id')
    prior_cost_of_sales = fields.Monetary(string='Cost of Sales (Prior Year)', currency_field='currency_id')
    prior_gross_profit = fields.Monetary(string='Gross Profit (Prior Year)', currency_field='currency_id')

    # ===== Financial Data Input =====
    # Current Year
    current_year_revenue = fields.Monetary(string='Current Year Revenue', currency_field='currency_id')
    current_year_cost_of_sales = fields.Monetary(string='Current Year Cost of Sales', currency_field='currency_id')
    current_year_gross_profit = fields.Monetary(string='Current Year Gross Profit', currency_field='currency_id')
    current_year_operating_expenses = fields.Monetary(string='Current Year Operating Expenses', currency_field='currency_id')
    current_year_pbt = fields.Monetary(string='Current Year PBT', currency_field='currency_id')
    current_year_net_profit = fields.Monetary(string='Current Year Net Profit', currency_field='currency_id')
    current_year_total_assets = fields.Monetary(string='Current Year Total Assets', currency_field='currency_id')
    current_year_total_liabilities = fields.Monetary(string='Current Year Total Liabilities', currency_field='currency_id')
    current_year_equity = fields.Monetary(string='Current Year Equity', currency_field='currency_id')

    # Prior Year
    prior_year_revenue = fields.Monetary(string='Prior Year Revenue', currency_field='currency_id')
    prior_year_cost_of_sales = fields.Monetary(string='Prior Year Cost of Sales', currency_field='currency_id')
    prior_year_gross_profit = fields.Monetary(string='Prior Year Gross Profit', currency_field='currency_id')
    prior_year_operating_expenses = fields.Monetary(string='Prior Year Operating Expenses', currency_field='currency_id')
    prior_year_pbt = fields.Monetary(string='Prior Year PBT', currency_field='currency_id')
    prior_year_net_profit = fields.Monetary(string='Prior Year Net Profit', currency_field='currency_id')
    prior_year_total_assets = fields.Monetary(string='Prior Year Total Assets', currency_field='currency_id')
    prior_year_total_liabilities = fields.Monetary(string='Prior Year Total Liabilities', currency_field='currency_id')
    prior_year_equity = fields.Monetary(string='Prior Year Equity', currency_field='currency_id')

    # Budget
    budget_revenue = fields.Monetary(string='Budgeted Revenue', currency_field='currency_id')
    budget_net_profit = fields.Monetary(string='Budgeted Net Profit', currency_field='currency_id')

    # ===== Variance Analysis =====
    revenue_variance_pct = fields.Float(string='Revenue Variance %', compute='_compute_variances', store=True)
    gross_profit_variance_pct = fields.Float(string='Gross Profit Variance %', compute='_compute_variances', store=True)
    net_profit_variance_pct = fields.Float(string='Net Profit Variance %', compute='_compute_variances', store=True)
    assets_variance_pct = fields.Float(string='Total Assets Variance %', compute='_compute_variances', store=True)
    budget_revenue_variance_pct = fields.Float(string='Budget Revenue Variance %', compute='_compute_variances', store=True)

    # ===== YoY Change Percentages (XML View Compatible) =====
    revenue_change_pct = fields.Float(string='Revenue Change %', compute='_compute_change_pct', store=True)
    asset_change_pct = fields.Float(string='Asset Change %', compute='_compute_change_pct', store=True)
    equity_change_pct = fields.Float(string='Equity Change %', compute='_compute_change_pct', store=True)
    profit_change_pct = fields.Float(string='Profit Change %', compute='_compute_change_pct', store=True)
    liability_change_pct = fields.Float(string='Liability Change %', compute='_compute_change_pct', store=True)

    # ===== Ratio Analysis =====
    current_year_gross_margin = fields.Float(string='CY Gross Margin %', compute='_compute_ratios', store=True)
    prior_year_gross_margin = fields.Float(string='PY Gross Margin %', compute='_compute_ratios', store=True)
    current_year_net_margin = fields.Float(string='CY Net Margin %', compute='_compute_ratios', store=True)
    prior_year_net_margin = fields.Float(string='PY Net Margin %', compute='_compute_ratios', store=True)
    current_year_roa = fields.Float(string='CY Return on Assets %', compute='_compute_ratios', store=True)
    current_year_roe = fields.Float(string='CY Return on Equity %', compute='_compute_ratios', store=True)
    current_year_debt_ratio = fields.Float(string='CY Debt Ratio %', compute='_compute_ratios', store=True)

    # ===== Liquidity Ratios (XML View Compatible) =====
    current_ratio = fields.Float(string='Current Ratio')
    quick_ratio = fields.Float(string='Quick Ratio')
    cash_ratio = fields.Float(string='Cash Ratio')
    working_capital = fields.Monetary(string='Working Capital', currency_field='currency_id')

    # ===== Profitability Ratios (XML View Compatible) =====
    gross_margin_pct = fields.Float(string='Gross Margin %')
    net_margin_pct = fields.Float(string='Net Margin %')
    return_on_assets = fields.Float(string='Return on Assets %')
    return_on_equity = fields.Float(string='Return on Equity %')

    # ===== Leverage Ratios (XML View Compatible) =====
    debt_to_equity = fields.Float(string='Debt to Equity')
    debt_ratio = fields.Float(string='Debt Ratio %')
    interest_coverage = fields.Float(string='Interest Coverage')

    # ===== Efficiency Ratios (XML View Compatible) =====
    inventory_turnover = fields.Float(string='Inventory Turnover')
    receivable_days = fields.Float(string='Receivable Days')
    payable_days = fields.Float(string='Payable Days')
    asset_turnover = fields.Float(string='Asset Turnover')

    # ===== Trend Analysis =====
    trend_analysis = fields.Html(
        string='3-5 Year Trend Analysis',
        help='Trend analysis over multiple years'
    )
    trend_observations = fields.Html(
        string='Trend Observations',
        help='Key observations from trend analysis'
    )
    seasonal_patterns = fields.Html(
        string='Seasonal Patterns',
        help='Monthly/quarterly pattern analysis'
    )
    industry_comparison = fields.Html(
        string='Industry Comparison',
        help='Comparison with industry benchmarks'
    )

    # ===== Industry Comparison (XML View Compatible) =====
    industry_benchmark = fields.Html(
        string='Industry Benchmarks',
        help='Key industry benchmark data'
    )
    peer_comparison = fields.Html(
        string='Peer Comparison',
        help='Comparison with peer companies'
    )
    industry_deviations = fields.Html(
        string='Industry Deviations',
        help='Deviations from industry norms'
    )

    # ===== Anomaly Detection =====
    anomaly_flags = fields.Html(
        string='Automated Anomaly Flags',
        help='System-identified unusual items'
    )
    anomalies_identified = fields.Html(
        string='Anomalies Identified',
        help='List of identified anomalies'
    )
    significant_fluctuations = fields.Html(
        string='Significant Fluctuations (>10%)',
        help='Items with fluctuations exceeding 10% or materiality'
    )
    unusual_transactions = fields.Html(
        string='Unusual Transactions Identified',
        help='Transactions requiring further investigation'
    )
    fraud_indicators = fields.Html(
        string='Fraud Indicators',
        help='Potential fraud risk indicators identified'
    )
    audit_focus_areas = fields.Html(
        string='Audit Focus Areas',
        help='Areas requiring enhanced audit procedures'
    )

    # ===== Management Inquiry (XML View Compatible) =====
    management_explanations = fields.Html(
        string='Management Explanations',
        help='Explanations provided by management'
    )
    management_questions = fields.Html(
        string='Questions for Management',
        help='Questions to be discussed with management'
    )
    responses_received = fields.Html(
        string='Responses Received',
        help='Responses received from management'
    )

    # ===== Analytical Review Lines (One2Many) =====
    analytical_line_ids = fields.One2many(
        'qaco.planning.p4.analytics.line',
        'p4_analytics_id',
        string='Analytical Review Items'
    )

    # ===== Auditor Observations =====
    auditor_observations = fields.Html(
        string='Auditor Observations',
        help='Key observations and concerns from analytical review'
    )
    areas_requiring_attention = fields.Html(
        string='Areas Requiring Attention',
        help='Areas identified for enhanced audit procedures'
    )
    risk_linkage = fields.Html(
        string='Risk Linkage',
        help='Link to P-6 Risk Assessment findings'
    )

    # ===== Attachments =====
    prior_year_fs_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p4_prior_fs_rel',
        'p4_id',
        'attachment_id',
        string='Prior Year Financial Statements'
    )
    current_year_tb_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p4_current_tb_rel',
        'p4_id',
        'attachment_id',
        string='Current Year Trial Balance'
    )
    analytical_summary_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p4_analytical_summary_rel',
        'p4_id',
        'attachment_id',
        string='Analytical Summary Sheets'
    )

    # ===== Attachments (XML View Compatible) =====
    financial_statement_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p4_financial_stmt_rel',
        'p4_id',
        'attachment_id',
        string='Financial Statements'
    )
    trial_balance_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p4_trial_balance_rel',
        'p4_id',
        'attachment_id',
        string='Trial Balance'
    )
    analysis_attachment_ids = fields.Many2many(
        'ir.attachment',
        'qaco_p4_analysis_attach_rel',
        'p4_id',
        'attachment_id',
        string='Supporting Analysis'
    )

    # ===== Summary Output =====
    analytical_review_summary = fields.Html(
        string='Analytical Review Report',
        help='Summary of analytical procedures per ISA 520'
    )
    analytics_conclusion = fields.Html(
        string='Analytical Review Conclusion',
        help='Final conclusion from analytical review'
    )
    impact_on_audit_plan = fields.Html(
        string='Impact on Audit Plan',
        help='How analytical review findings impact the audit plan'
    )
    isa_reference = fields.Char(
        string='ISA Reference',
        default='ISA 520',
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
        ('audit_unique', 'UNIQUE(audit_id)', 'Only one P-4 record per Audit Engagement is allowed.')
    ]

    @api.depends('audit_id', 'client_id')
    def _compute_name(self):
        for record in self:
            if record.client_id:
                record.name = f"P4-{record.client_id.name[:15]}"
            else:
                record.name = 'P-4: Analytical Procedures'

    @api.depends(
        'current_year_revenue', 'prior_year_revenue', 'budget_revenue',
        'current_year_gross_profit', 'prior_year_gross_profit',
        'current_year_net_profit', 'prior_year_net_profit',
        'current_year_total_assets', 'prior_year_total_assets'
    )
    def _compute_variances(self):
        for record in self:
            # Revenue YoY variance
            if record.prior_year_revenue and record.prior_year_revenue != 0:
                record.revenue_variance_pct = ((record.current_year_revenue - record.prior_year_revenue) / record.prior_year_revenue) * 100
            else:
                record.revenue_variance_pct = 0

            # Gross Profit variance
            if record.prior_year_gross_profit and record.prior_year_gross_profit != 0:
                record.gross_profit_variance_pct = ((record.current_year_gross_profit - record.prior_year_gross_profit) / record.prior_year_gross_profit) * 100
            else:
                record.gross_profit_variance_pct = 0

            # Net Profit variance
            if record.prior_year_net_profit and record.prior_year_net_profit != 0:
                record.net_profit_variance_pct = ((record.current_year_net_profit - record.prior_year_net_profit) / record.prior_year_net_profit) * 100
            else:
                record.net_profit_variance_pct = 0

            # Total Assets variance
            if record.prior_year_total_assets and record.prior_year_total_assets != 0:
                record.assets_variance_pct = ((record.current_year_total_assets - record.prior_year_total_assets) / record.prior_year_total_assets) * 100
            else:
                record.assets_variance_pct = 0

            # Budget variance
            if record.budget_revenue and record.budget_revenue != 0:
                record.budget_revenue_variance_pct = ((record.current_year_revenue - record.budget_revenue) / record.budget_revenue) * 100
            else:
                record.budget_revenue_variance_pct = 0

    @api.depends(
        'current_year_revenue', 'current_year_gross_profit', 'current_year_net_profit',
        'current_year_total_assets', 'current_year_equity', 'current_year_total_liabilities',
        'prior_year_revenue', 'prior_year_gross_profit', 'prior_year_net_profit'
    )
    def _compute_ratios(self):
        for record in self:
            # Gross margin
            if record.current_year_revenue and record.current_year_revenue != 0:
                record.current_year_gross_margin = (record.current_year_gross_profit / record.current_year_revenue) * 100
                record.current_year_net_margin = (record.current_year_net_profit / record.current_year_revenue) * 100
            else:
                record.current_year_gross_margin = 0
                record.current_year_net_margin = 0

            if record.prior_year_revenue and record.prior_year_revenue != 0:
                record.prior_year_gross_margin = (record.prior_year_gross_profit / record.prior_year_revenue) * 100
                record.prior_year_net_margin = (record.prior_year_net_profit / record.prior_year_revenue) * 100
            else:
                record.prior_year_gross_margin = 0
                record.prior_year_net_margin = 0

            # ROA
            if record.current_year_total_assets and record.current_year_total_assets != 0:
                record.current_year_roa = (record.current_year_net_profit / record.current_year_total_assets) * 100
            else:
                record.current_year_roa = 0

            # ROE
            if record.current_year_equity and record.current_year_equity != 0:
                record.current_year_roe = (record.current_year_net_profit / record.current_year_equity) * 100
            else:
                record.current_year_roe = 0

            # Debt Ratio
            if record.current_year_total_assets and record.current_year_total_assets != 0:
                record.current_year_debt_ratio = (record.current_year_total_liabilities / record.current_year_total_assets) * 100
            else:
                record.current_year_debt_ratio = 0

    def _validate_mandatory_fields(self):
        """Validate mandatory fields before completing P-4."""
        self.ensure_one()
        errors = []
        if not self.auditor_observations:
            errors.append('Auditor observations must be documented')
        if not self.analytical_review_summary:
            errors.append('Analytical review summary is required')
        if errors:
            raise UserError('Cannot complete P-4. Missing requirements:\n• ' + '\n• '.join(errors))

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


class PlanningP4AnalyticsLine(models.Model):
    """Analytical Review Line Items for detailed analysis."""
    _name = 'qaco.planning.p4.analytics.line'
    _description = 'Analytical Review Line Item'
    _order = 'sequence, id'

    p4_analytics_id = fields.Many2one(
        'qaco.planning.p4.analytics',
        string='P-4 Analytics',
        required=True,
        ondelete='cascade'
    )
    sequence = fields.Integer(string='Sequence', default=10)
    account_category = fields.Selection([
        ('revenue', 'Revenue'),
        ('cost_of_sales', 'Cost of Sales'),
        ('operating_expenses', 'Operating Expenses'),
        ('other_income', 'Other Income'),
        ('finance_costs', 'Finance Costs'),
        ('taxation', 'Taxation'),
        ('assets_current', 'Current Assets'),
        ('assets_non_current', 'Non-Current Assets'),
        ('liabilities_current', 'Current Liabilities'),
        ('liabilities_non_current', 'Non-Current Liabilities'),
        ('equity', 'Equity'),
    ], string='Category', required=True)
    description = fields.Char(string='Description', required=True)
    current_year_amount = fields.Float(string='Current Year')
    prior_year_amount = fields.Float(string='Prior Year')
    variance_amount = fields.Float(string='Variance', compute='_compute_variance', store=True)
    variance_pct = fields.Float(string='Variance %', compute='_compute_variance', store=True)
    is_significant = fields.Boolean(string='Significant', compute='_compute_variance', store=True)
    explanation = fields.Text(string='Explanation')
    auditor_comment = fields.Text(string='Auditor Comment')

    @api.depends('current_year_amount', 'prior_year_amount')
    def _compute_variance(self):
        for record in self:
            record.variance_amount = record.current_year_amount - record.prior_year_amount
            if record.prior_year_amount and record.prior_year_amount != 0:
                record.variance_pct = (record.variance_amount / record.prior_year_amount) * 100
            else:
                record.variance_pct = 0
            # Flag as significant if variance > 10%
            record.is_significant = abs(record.variance_pct) > 10
