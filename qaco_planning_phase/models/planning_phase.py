import logging
from typing import Any, TYPE_CHECKING

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError  # type: ignore[attr-defined]

_logger = logging.getLogger(__name__)


class PlanningPhase(models.Model):
	_name = 'qaco.planning.phase'
	_description = 'Planning Phase - Statutory Audit Pakistan'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_order = 'create_date desc'

	if TYPE_CHECKING:
		def activity_schedule(self, *args: Any, **kwargs: Any) -> Any: ...

		def message_post(self, *args: Any, **kwargs: Any) -> Any: ...

	SUBTAB_STATUS = [
		('red', '❌ Incomplete'),
		('amber', '🟡 In Progress'),
		('green', '✅ Complete'),
	]
	RISK_RATING = [
		('low', '🟢 Low'),
		('medium', '🟡 Medium'),
		('high', '🔴 High'),
	]
	CONTROL_RATING = [
		('none', '❌ Does Not Exist'),
		('weak', '🔴 Weak'),
		('moderate', '🟡 Moderate'),
		('strong', '🟢 Strong'),
	]
	ASSERTION_TYPES = [
		('existence', 'Existence/Occurrence'),
		('completeness', 'Completeness/Cut-off'),
		('valuation', 'Valuation/Allocation'),
		('rights', 'Rights & Obligations'),
		('presentation', 'Presentation & Disclosure'),
	]
	MATERIALITY_BENCHMARKS = [
		('pbt', 'Profit Before Tax (PBT)'),
		('revenue', 'Revenue/Turnover'),
		('assets', 'Total Assets'),
		('equity', 'Equity'),
		('expenses', 'Total Expenses'),
		('custom', 'Custom Benchmark'),
	]
	INDUSTRY_TYPES = [
		('manufacturing', 'Manufacturing'),
		('trading', 'Trading'),
		('services', 'Services'),
		('financial', 'Financial Services'),
		('insurance', 'Insurance'),
		('nfbc', 'NFBC'),
		('public_sector', 'Public Sector Entity'),
		('sme', 'SME'),
		('other', 'Other'),
	]
	AUDIT_TYPES = [
		('statutory', 'Statutory Audit'),
		('special', 'Special Audit'),
		('tax', 'Tax Audit'),
		('internal', 'Internal Audit'),
		('agm', 'AGM Review'),
		('other', 'Other'),
	]

	name = fields.Char(string='Planning Reference', compute='_compute_name', store=True, readonly=True)
	audit_id = fields.Many2one('qaco.audit', string='Audit Engagement', required=True, ondelete='cascade', index=True)
	client_id = fields.Many2one('res.partner', string='Client Name', related='audit_id.client_id', readonly=True, store=False, index=True)
	firm_name = fields.Many2one('audit.firm.name', string='Firm Name', related='audit_id.firm_name', readonly=True, store=False, index=True)
	understanding_status = fields.Selection(SUBTAB_STATUS, default='red', tracking=True, string='Entity Understanding Status')
	analytics_status = fields.Selection(SUBTAB_STATUS, default='red', tracking=True, string='Analytics Status')
	materiality_status = fields.Selection(SUBTAB_STATUS, default='red', tracking=True, string='Materiality Status')
	control_status = fields.Selection(SUBTAB_STATUS, default='red', tracking=True, string='Controls Status')
	risk_status = fields.Selection(SUBTAB_STATUS, default='red', tracking=True, string='Risk Assessment Status')
	completion_status = fields.Selection(SUBTAB_STATUS, default='red', tracking=True, string='Completion Status')

	audit_type = fields.Selection(AUDIT_TYPES, string='Type of Audit', required=True, default='statutory')
	audit_period_from = fields.Date(string='Audit Period From')
	audit_period_to = fields.Date(string='Audit Period To')
	financial_year_end = fields.Date(string='Financial Year End')
	previous_auditor = fields.Char(string='Previous Auditor')
	audit_tenure_years = fields.Integer(string='Audit Tenure (Years)', compute='_compute_audit_tenure')

	industry_id = fields.Many2one('qaco.industry', string='Industry Classification', tracking=True)
	industry_type = fields.Selection(INDUSTRY_TYPES, string='Industry Sector', default='other')
	business_model = fields.Html(string='Business Model & Revenue Sources')
	organizational_structure = fields.Html(string='Organizational Structure & Key Personnel')
	operational_locations = fields.Html(string='Operational Locations & Branches')
	key_contracts = fields.Html(string='Key Contractual Arrangements')
	applicable_regulators = fields.Many2many('qaco.regulator', string='Applicable Regulators')
	regulatory_filings_status = fields.Selection([
		('compliant', '✅ Fully Compliant'),
		('pending', '🟡 Some Filings Pending'),
		('non_compliant', '🔴 Non-Compliant'),
	], string='Regulatory Filings Status', tracking=True)
	regulatory_penalties = fields.Html(string='Regulatory Penalties/Litigations History')
	compliance_certificates = fields.Html(string='Compliance Certificates Status')
	related_parties_summary = fields.Html(string='Related Parties Identification')
	group_structure = fields.Html(string='Group Structure & Ownership')
	intra_group_transactions = fields.Html(string='Intra-group Transactions')
	fraud_incentives = fields.Html(string='Incentives/Pressures for Fraud')
	fraud_opportunities = fields.Html(string='Opportunities for Fraud')
	fraud_attitudes = fields.Html(string='Attitudes/Rationalizations for Fraud')
	fraud_risk_assessment = fields.Html(string='Overall Fraud Risk Assessment')

	prior_year_fs_attachment_ids = fields.Many2many(
		'ir.attachment',
		'qaco_planning_phase_prior_fs_rel',
		'planning_phase_id',
		'attachment_id',
		string='Prior Year Financial Statements'
	)
	current_year_tb_attachment_ids = fields.Many2many(
		'ir.attachment',
		'qaco_planning_phase_current_tb_rel',
		'planning_phase_id',
		'attachment_id',
		string='Current Year Trial Balance & Draft FS'
	)
	industry_benchmarks = fields.Html(string='Industry Benchmarks & Comparisons')
	significant_fluctuations = fields.Html(string='Significant Fluctuations Analysis (>10% or Materiality)')
	ratio_analysis_summary = fields.Html(string='Ratio Analysis Summary')
	trend_analysis = fields.Html(string='3-5 Year Trend Analysis')
	going_concern_assessment = fields.Html(string='Going Concern Assessment (ISA 570)')
	analytical_expectations = fields.Html(string='Analytical Expectations vs Actual')

	materiality_benchmark = fields.Selection(MATERIALITY_BENCHMARKS, string='Materiality Benchmark', default='pbt')
	materiality_percentage = fields.Float(string='Materiality Percentage (%)', default=5.0)
	materiality_justification = fields.Html(string='Benchmark Selection Justification')
	custom_benchmark_value = fields.Monetary(string='Custom Benchmark Value', currency_field='company_currency_id')
	overall_materiality = fields.Monetary(string='Overall Materiality', currency_field='company_currency_id', readonly=True)
	performance_materiality = fields.Monetary(string='Performance Materiality', currency_field='company_currency_id', readonly=True)
	clearly_trivial_threshold = fields.Monetary(string='Clearly Trivial Threshold', currency_field='company_currency_id', readonly=True)
	company_currency_id = fields.Many2one('res.currency', string='Reporting Currency', default=lambda self: self._get_default_currency())

	control_environment_rating = fields.Selection(CONTROL_RATING, string='Control Environment', default='none')
	entity_level_controls_rating = fields.Selection(CONTROL_RATING, string='Entity-Level Controls', default='none')
	risk_assessment_rating = fields.Selection(CONTROL_RATING, string='Risk Assessment Process', default='none')
	itgc_rating = fields.Selection(CONTROL_RATING, string='IT General Controls', default='none')
	control_activities_rating = fields.Selection(CONTROL_RATING, string='Control Activities', default='none')
	monitoring_controls_rating = fields.Selection(CONTROL_RATING, string='Monitoring of Controls', default='none')
	reliance_on_controls = fields.Boolean(string='Planned Reliance on Controls', compute='_compute_reliance_strategy', store=True, readonly=True)
	control_assessment_summary = fields.Html(string='Control Assessment Summary')
	internal_audit_function = fields.Selection([
		('none', 'No Internal Audit'),
		('weak', 'Weak Internal Audit'),
		('moderate', 'Moderate Internal Audit'),
		('strong', 'Strong Internal Audit'),
	], string='Internal Audit Function Assessment')

	risk_register_line_ids = fields.One2many('qaco.risk.register.line', 'planning_phase_id', string='Risk Register')
	audit_approach = fields.Html(string='Overall Audit Approach & Strategy')
	use_of_experts = fields.Boolean(string='Use of Experts Required (ISA 620)')
	experts_details = fields.Html(string='Experts Scope & Details')
	use_of_caats = fields.Boolean(string='Use of CAATs/Data Analytics')
	caats_details = fields.Html(string='CAATs/Data Analytics Plan')
	component_auditors_involved = fields.Boolean(string='Component Auditors Involved (ISA 600)')
	component_auditors_details = fields.Html(string='Component Auditors Coordination Plan')
	staffing_plan = fields.Html(string='Staffing Plan & Timelines')
	audit_timeline = fields.Html(string='Detailed Audit Timeline')
	budget_hours = fields.Float(string='Planned Budget Hours')
	significant_risks_identified = fields.Integer(string='Significant Risks Count', compute='_compute_significant_risks')

	planning_memo_summary = fields.Html(string='Planning Memorandum Executive Summary')
	icap_compliance_check = fields.Boolean(string='ICAP Standards Compliance Verified', default=False)
	secp_requirements_met = fields.Boolean(string='SECP Requirements Addressed', default=False)
	aob_guidelines_considered = fields.Boolean(string='AOB Guidelines Considered', default=False)

	organogram_attachment_ids = fields.Many2many(
		'ir.attachment',
		'qaco_planning_phase_organogram_rel',
		'planning_phase_id',
		'attachment_id',
		string='Organogram Files'
	)
	engagement_letter_attachment_ids = fields.Many2many(
		'ir.attachment',
		'qaco_planning_phase_engagement_letter_rel',
		'planning_phase_id',
		'attachment_id',
		string='Signed Engagement Letters'
	)
	board_minutes_attachment_ids = fields.Many2many(
		'ir.attachment',
		'qaco_planning_phase_board_minutes_rel',
		'planning_phase_id',
		'attachment_id',
		string='BOD/Audit Committee Minutes'
	)
	process_flow_attachment_ids = fields.Many2many(
		'ir.attachment',
		'qaco_planning_phase_process_flow_rel',
		'planning_phase_id',
		'attachment_id',
		string='Process Flowcharts'
	)
	related_party_attachment_ids = fields.Many2many(
		'ir.attachment',
		'qaco_planning_phase_related_party_rel',
		'planning_phase_id',
		'attachment_id',
		string='Related Party Schedules'
	)
	materiality_worksheet_attachment_ids = fields.Many2many(
		'ir.attachment',
		'qaco_planning_phase_materiality_worksheet_rel',
		'planning_phase_id',
		'attachment_id',
		string='Materiality Worksheets'
	)
	analytical_summary_attachment_ids = fields.Many2many(
		'ir.attachment',
		'qaco_planning_phase_analytical_summary_rel',
		'planning_phase_id',
		'attachment_id',
		string='Analytical Summary Sheets'
	)
	risk_register_attachment_ids = fields.Many2many(
		'ir.attachment',
		'qaco_planning_phase_risk_register_rel',
		'planning_phase_id',
		'attachment_id',
		string='Risk Register Files'
	)
	audit_strategy_attachment_ids = fields.Many2many(
		'ir.attachment',
		'qaco_planning_phase_audit_strategy_rel',
		'planning_phase_id',
		'attachment_id',
		string='Audit Strategy Documentation'
	)
	internal_control_attachment_ids = fields.Many2many(
		'ir.attachment',
		'qaco_planning_phase_internal_control_rel',
		'planning_phase_id',
		'attachment_id',
		string='Internal Control Documentation'
	)
	legal_compliance_attachment_ids = fields.Many2many(
		'ir.attachment',
		'qaco_planning_phase_legal_compliance_rel',
		'planning_phase_id',
		'attachment_id',
		string='Legal & Compliance Documents'
	)
	previous_audit_reports_attachment_ids = fields.Many2many(
		'ir.attachment',
		'qaco_planning_phase_previous_audit_reports_rel',
		'planning_phase_id',
		'attachment_id',
		string='Previous Audit Reports'
	)

	checklist_engagement_letter = fields.Boolean(string='✓ Engagement Letter Executed & Uploaded', tracking=True)
	checklist_entity_understanding = fields.Boolean(string='✓ Entity Understanding Complete (ISA 315)', tracking=True)
	checklist_fraud_brainstormed = fields.Boolean(string='✓ Fraud Brainstorming Documented (ISA 240)', tracking=True)
	checklist_analytics_performed = fields.Boolean(string='✓ Analytical Procedures Performed (ISA 520)', tracking=True)
	checklist_materiality_finalized = fields.Boolean(string='✓ Materiality Finalized & Justified (ISA 320)', tracking=True)
	checklist_controls_assessed = fields.Boolean(string='✓ Internal Controls Assessed (ISA 315)', tracking=True)
	checklist_risks_linked = fields.Boolean(string='✓ Risks Linked to Audit Programs', tracking=True)
	checklist_strategy_signed = fields.Boolean(string='✓ Audit Strategy Memo Approved', tracking=True)
	checklist_independence_confirmed = fields.Boolean(string='✓ Independence Confirmed (Code of Ethics)', tracking=True)
	checklist_partner_manager_review = fields.Boolean(string='✓ Partner/Manager Review Completed', tracking=True)
	checklist_icap_standards = fields.Boolean(string='✓ ICAP Standards Compliance Verified', tracking=True)
	checklist_secp_requirements = fields.Boolean(string='✓ SECP Requirements Addressed', tracking=True)
	checklist_aob_guidelines = fields.Boolean(string='✓ AOB Guidelines Considered', tracking=True)

	manager_signed_user_id = fields.Many2one('res.users', string='Manager Signature', tracking=True, copy=False, readonly=True)
	manager_signed_on = fields.Datetime(string='Manager Signed On', tracking=True, copy=False, readonly=True)
	partner_signed_user_id = fields.Many2one('res.users', string='Partner Signature', tracking=True, copy=False, readonly=True)
	partner_signed_on = fields.Datetime(string='Partner Signed On', tracking=True, copy=False, readonly=True)
	quality_reviewer_id = fields.Many2one('res.users', string='Quality Reviewer', tracking=True, copy=False, readonly=True)
	quality_reviewed_on = fields.Datetime(string='Quality Reviewed On', tracking=True, copy=False, readonly=True)

	planning_complete = fields.Boolean(string='Planning Phase Complete', default=False, tracking=True, copy=False)
	planning_completed_on = fields.Datetime(string='Planning Completed On', tracking=True, copy=False, readonly=True)
	can_finalize_planning = fields.Boolean(string='Can Finalize Planning', compute='_compute_can_finalize', store=True)
	missing_requirements_note = fields.Html(string='Outstanding Planning Requirements', compute='_compute_can_finalize', store=True)

	@api.depends('audit_id', 'client_id', 'create_date')
	def _compute_name(self):
		"""Defensive: Safe even during module install."""
		for record in self:
			try:
				if record.client_id and record.create_date:
					record.name = f"PLAN-{record.client_id.name}-{record.create_date.strftime('%Y%m%d')}"
				else:
					record.name = 'Planning Phase - Draft'
			except Exception as e:
				_logger.warning(f'Planning Phase _compute_name failed for record {record.id}: {e}')
				record.name = 'Planning Phase - Draft'

	@api.depends('audit_period_from', 'audit_period_to')
	def _compute_audit_tenure(self):
		"""Defensive: Safe even during module install."""
		for record in self:
			try:
				if record.audit_period_from and record.audit_period_to:
					delta = record.audit_period_to - record.audit_period_from
					record.audit_tenure_years = delta.days // 365
				else:
					record.audit_tenure_years = 0
			except Exception as e:
				_logger.warning(f'Planning Phase _compute_audit_tenure failed for record {record.id}: {e}')
				record.audit_tenure_years = 0

	@api.depends('control_environment_rating', 'control_activities_rating', 'itgc_rating')
	def _compute_reliance_strategy(self):
		"""Defensive: Safe even during module install."""
		for record in self:
			try:
				record.reliance_on_controls = (
					record.control_environment_rating in ['moderate', 'strong']
					and record.control_activities_rating in ['moderate', 'strong']
					and record.itgc_rating in ['moderate', 'strong']
				)
			except Exception as e:
				_logger.warning(f'Planning Phase _compute_reliance_strategy failed for record {record.id}: {e}')
				record.reliance_on_controls = False

	@api.depends('risk_register_line_ids', 'risk_register_line_ids.is_significant_risk')
	def _compute_significant_risks(self):
		"""Defensive: Safe even during module install."""
		for record in self:
			try:
				if not record.risk_register_line_ids:
					record.significant_risks_identified = 0
					continue
				
				record.significant_risks_identified = len(record.risk_register_line_ids.filtered(lambda r: r.is_significant_risk))
			except Exception as e:
				_logger.warning(f'Planning Phase _compute_significant_risks failed for record {record.id}: {e}')
				record.significant_risks_identified = 0

	@api.depends(
		'understanding_status', 'analytics_status', 'materiality_status', 'control_status',
		'risk_status', 'completion_status',
		'checklist_engagement_letter', 'checklist_entity_understanding', 'checklist_fraud_brainstormed',
		'checklist_analytics_performed', 'checklist_materiality_finalized', 'checklist_controls_assessed',
		'checklist_risks_linked', 'checklist_strategy_signed', 'checklist_independence_confirmed',
		'checklist_partner_manager_review', 'checklist_icap_standards', 'checklist_secp_requirements',
		'checklist_aob_guidelines', 'manager_signed_user_id', 'partner_signed_user_id',
		'organogram_attachment_ids', 'engagement_letter_attachment_ids', 'board_minutes_attachment_ids',
		'process_flow_attachment_ids', 'related_party_attachment_ids', 'materiality_worksheet_attachment_ids',
		'analytical_summary_attachment_ids', 'risk_register_attachment_ids', 'audit_strategy_attachment_ids'
	)
	def _compute_can_finalize(self):
		status_fields = ['understanding_status', 'analytics_status', 'materiality_status', 'control_status', 'risk_status']
		attachment_fields = [
			'organogram_attachment_ids', 'engagement_letter_attachment_ids',
			'board_minutes_attachment_ids', 'process_flow_attachment_ids',
			'related_party_attachment_ids', 'materiality_worksheet_attachment_ids'
		]
		checklist_fields = [
			'checklist_engagement_letter', 'checklist_entity_understanding', 'checklist_fraud_brainstormed',
			'checklist_analytics_performed', 'checklist_materiality_finalized', 'checklist_controls_assessed',
			'checklist_risks_linked', 'checklist_strategy_signed', 'checklist_independence_confirmed',
			'checklist_partner_manager_review', 'checklist_icap_standards', 'checklist_secp_requirements'
		]
		for record in self:
			statuses_ready = all(getattr(record, field) == 'green' for field in status_fields)
			attachments_ready = all(bool(getattr(record, field)) for field in attachment_fields)
			checklist_ready = all(getattr(record, field) for field in checklist_fields)
			signoffs_ready = bool(record.manager_signed_user_id and record.partner_signed_user_id)
			record.can_finalize_planning = statuses_ready and attachments_ready and checklist_ready and signoffs_ready
			pending = []
			if not statuses_ready:
				missing = [field for field in status_fields if getattr(record, field) != 'green']
				pending.append(f"Complete these sub-tabs: {', '.join(missing)}")
			if not attachments_ready:
				missing = [field for field in attachment_fields if not getattr(record, field)]
				pending.append(f"Upload mandatory attachments: {', '.join(missing)}")
			if not checklist_ready:
				missing = [field for field in checklist_fields if not getattr(record, field)]
				pending.append(f"Complete checklist items: {len(missing)} remaining")
			if not signoffs_ready:
				pending.append('Obtain manager and partner e-signatures')
			if pending:
				record.missing_requirements_note = '<ul>' + ''.join(f'<li>{item}</li>' for item in pending) + '</ul>'
			else:
				record.missing_requirements_note = "<p style='color: green;'>✅ All planning requirements satisfied. Ready for finalization.</p>"

	@api.onchange('materiality_benchmark', 'materiality_percentage', 'custom_benchmark_value')
	def _compute_materiality_values(self):
		for record in self:
			if record.materiality_benchmark and record.materiality_percentage > 0:
				if record.materiality_benchmark == 'custom' and record.custom_benchmark_value:
					benchmark_value = record.custom_benchmark_value
				else:
					benchmark_value = 1_000_000
				record.overall_materiality = benchmark_value * (record.materiality_percentage / 100.0)
				record.performance_materiality = record.overall_materiality * 0.75
				record.clearly_trivial_threshold = record.overall_materiality * 0.05

	@api.model
	def _get_default_currency(self):
		"""Safe currency default that won't crash during module install/cron."""
		try:
			return self.env.company.currency_id.id if self.env.company else False
		except Exception as e:
			_logger.warning(f'_get_default_currency failed: {e}')
			return False

	def _ensure_statuses_green(self):
		self.ensure_one()
		incomplete = [
			field for field in ['understanding_status', 'analytics_status', 'materiality_status', 'control_status', 'risk_status']
			if getattr(self, field) != 'green'
		]
		if incomplete:
			raise UserError(f"Complete these sub-tabs before sign-off: {', '.join(incomplete)}")

	def _validate_materiality_parameters(self):
		self.ensure_one()
		if not self.materiality_benchmark:
			raise UserError('Materiality benchmark must be selected as per ISA 320.')
		if not self.materiality_justification:
			raise UserError('Justification for benchmark selection is mandatory for audit documentation.')
		if not self.materiality_percentage or self.materiality_percentage <= 0:
			raise UserError('Valid materiality percentage must be specified (typically 1-10%).')
		if self.materiality_benchmark == 'custom' and not self.custom_benchmark_value:
			raise UserError('Custom benchmark value is required when using custom benchmark.')

	def _validate_risk_assessment(self):
		self.ensure_one()
		if not self.risk_register_line_ids:
			raise UserError('Risk register must contain at least one identified risk as per ISA 315.')
		if not any(line.is_significant_risk for line in self.risk_register_line_ids):
			raise UserError('At least one significant risk must be identified in the risk register.')
		if not self.audit_approach:
			raise UserError('Overall audit approach must be documented as per ISA 300.')

	def action_manager_sign(self):
		self.ensure_one()
		self._ensure_statuses_green()
		self._validate_materiality_parameters()
		self._validate_risk_assessment()
		self.manager_signed_user_id = self.env.user
		self.manager_signed_on = fields.Datetime.now()
		self.activity_schedule(
			'mail.mail_activity_data_todo',
			note='Planning phase ready for partner review and sign-off',
			user_id=self.partner_signed_user_id.id if self.partner_signed_user_id else self.env.user.id,
			summary='Partner Review Required - Planning Phase'
		)

	def action_partner_sign(self):
		self.ensure_one()
		if not self.manager_signed_user_id:
			raise UserError('Manager must sign before the partner can sign.')
		self._ensure_statuses_green()
		self._validate_materiality_parameters()
		self._validate_risk_assessment()
		self.partner_signed_user_id = self.env.user
		self.partner_signed_on = fields.Datetime.now()

	def action_mark_planning_complete(self):
		self.ensure_one()
		if not self.can_finalize_planning:
			raise UserError('Cannot complete planning - all prerequisites must be satisfied.')
		self._validate_materiality_parameters()
		self._validate_risk_assessment()
		self.planning_complete = True
		self.planning_completed_on = fields.Datetime.now()
		self.completion_status = 'green'
		message = f"Planning Phase completed successfully on {self.planning_completed_on}. Ready for execution phase."
		self.message_post(body=message)
		return {
			'type': 'ir.actions.client',
			'tag': 'display_notification',
			'params': {
				'title': 'Planning Phase Complete',
				'message': 'Planning phase has been successfully completed and locked for execution.',
				'type': 'success',
				'sticky': True,
			}
		}

	def action_generate_planning_memo(self):
		self.ensure_one()
		return {
			'type': 'ir.actions.act_url',
			'url': f'/web/content/qaco.planning.phase/{self.id}/planning_memo',
			'target': 'new',
		}

	def action_quality_review(self):
		self.ensure_one()
		self.quality_reviewer_id = self.env.user
		self.quality_reviewed_on = fields.Datetime.now()
		return {
			'type': 'ir.actions.client',
			'tag': 'display_notification',
			'params': {
				'title': 'Quality Review Initiated',
				'message': 'Planning phase has been marked for quality review.',
				'type': 'warning',
				'sticky': False,
			}
		}

	def action_view_audit(self):
		"""Open the related audit engagement record."""
		self.ensure_one()
		return {
			'type': 'ir.actions.act_window',
			'name': 'Audit Engagement',
			'res_model': 'qaco.audit',
			'view_mode': 'form',
			'res_id': self.audit_id.id,
			'target': 'current',
		}

	@api.constrains('materiality_percentage')
	def _check_materiality_percentage(self):
		for record in self:
			if record.materiality_percentage and not (0.1 <= record.materiality_percentage <= 20):
				raise ValidationError('Materiality percentage should typically be between 0.1% and 20% as per ISA guidance.')

	@api.constrains('audit_period_from', 'audit_period_to')
	def _check_audit_period(self):
		for record in self:
			if record.audit_period_from and record.audit_period_to:
				if record.audit_period_from >= record.audit_period_to:
					raise ValidationError('Audit period "From" date must be before "To" date.')
				if (record.audit_period_to - record.audit_period_from).days > 366:
					raise ValidationError('Audit period should not exceed 12 months.')

	@api.constrains('planning_complete')
	def _check_planning_complete_guard(self):
		for record in self:
			if record.planning_complete and not record.can_finalize_planning:
				raise ValidationError('Planning cannot be marked complete until every prerequisite is satisfied for zero-deficiency compliance.')


class RiskRegisterLine(models.Model):
	_name = 'qaco.risk.register.line'
	_description = 'Risk Register Line - Detailed Risk Assessment'
	_order = 'risk_rating desc, sequence'
	_rec_name = 'risk_description'

	planning_phase_id = fields.Many2one('qaco.planning.phase', string='Planning Phase', required=True, ondelete='cascade')
	sequence = fields.Integer(string='Sequence', default=10)
	account_cycle = fields.Selection([
		('revenue', 'Revenue & Receivables'),
		('purchases', 'Purchases & Payables'),
		('inventory', 'Inventory & Cost of Sales'),
		('payroll', 'Payroll & Human Resources'),
		('fixed_assets', 'Fixed Assets & Depreciation'),
		('investments', 'Investments & Securities'),
		('cash', 'Cash & Bank'),
		('taxation', 'Taxation'),
		('provisions', 'Provisions & Contingencies'),
		('equity', 'Equity & Financing'),
		('fs_level', 'Financial Statement Level'),
		('other', 'Other'),
	], string='Account/Cycle', required=True)
	risk_description = fields.Html(string='Risk Description')
	fs_level_risk = fields.Boolean(string='Financial Statement Level Risk')
	assertion_type = fields.Selection(PlanningPhase.ASSERTION_TYPES, string='Assertion Level Risk')
	risk_rating = fields.Selection(PlanningPhase.RISK_RATING, string='Risk Rating', required=True)
	is_significant_risk = fields.Boolean(string='Significant Risk')
	root_cause = fields.Html(string='Root Cause Analysis')
	impact_on_fs = fields.Html(string='Impact on Financial Statements')
	likelihood = fields.Selection([
		('remote', 'Remote'),
		('possible', 'Possible'),
		('probable', 'Probable'),
		('likely', 'Likely'),
	], string='Likelihood')
	magnitude = fields.Selection([
		('immaterial', 'Immaterial'),
		('material', 'Material'),
		('significant', 'Significant'),
		('critical', 'Critical'),
	], string='Magnitude')
	isa_240_risk = fields.Boolean(string='ISA 240 - Fraud Risk')
	isa_540_risk = fields.Boolean(string='ISA 540 - Accounting Estimates')
	isa_550_risk = fields.Boolean(string='ISA 550 - Related Parties')
	isa_570_risk = fields.Boolean(string='ISA 570 - Going Concern')
	planned_procedures = fields.Html(string='Planned Audit Procedures')
	nature_of_procedures = fields.Selection([
		('test_of_controls', 'Test of Controls'),
		('substantive_analytical', 'Substantive Analytical'),
		('test_of_details', 'Test of Details'),
		('combination', 'Combination'),
	], string='Nature of Procedures')
	timing_of_procedures = fields.Selection([
		('interim', 'Interim'),
		('year_end', 'Year-end'),
		('both', 'Both Interim & Year-end'),
	], string='Timing of Procedures')
	extent_of_procedures = fields.Html(string='Extent of Procedures')
	link_to_audit_program = fields.Char(string='Link to Audit Program Section')


class Industry(models.Model):
	_name = 'qaco.industry'
	_description = 'Industry Classification - Pakistan Context'
	_order = 'name'

	name = fields.Char(string='Industry Name', required=True)
	code = fields.Char(string='Industry Code', required=True)
	description = fields.Html(string='Industry Description')
	common_risks = fields.Html(string='Common Industry Risks')
	applicable_regulations = fields.Html(string='Applicable Regulations')
	key_performance_indicators = fields.Html(string='Key Performance Indicators')
	icap_guidance = fields.Html(string='ICAP Specific Guidance')


class Regulator(models.Model):
	_name = 'qaco.regulator'
	_description = 'Regulatory Body - Pakistan'
	_order = 'name'

	name = fields.Char(string='Regulator Name', required=True)
	code = fields.Char(string='Regulator Code', required=True)
	description = fields.Html(string='Regulator Description')
	website = fields.Char(string='Website')
	jurisdiction = fields.Selection([
		('federal', 'Federal'),
		('provincial', 'Provincial'),
		('both', 'Federal & Provincial'),
	], string='Jurisdiction', required=True)
	key_regulations = fields.Html(string='Key Regulations & Requirements')
	filing_deadlines = fields.Html(string='Filing Deadlines')
	contact_information = fields.Html(string='Contact Information')
