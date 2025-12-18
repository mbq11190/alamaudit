# -*- coding: utf-8 -*-
"""
Planning Tab Models P-7 through P-13

P-7: Fraud Risk Assessment (ISA 240)
P-8: Going Concern (ISA 570)
P-9: Laws & Regulations (ISA 250)
P-10: Related Parties Planning (ISA 550)
P-11: Group Audit Planning (ISA 600)
P-12: Audit Strategy & Audit Plan (ISA 300)
P-13: Planning Review & Approval (ISA 220, ISQM-1)
"""
from odoo import api, fields, models, _
from odoo.exceptions import UserError


# ═══════════════════════════════════════════════════════════════════════
# P-7: Fraud Risk Assessment (ISA 240)
# ═══════════════════════════════════════════════════════════════════════
class PlanningP7Fraud(models.Model):
    _name = "audit.planning.p7.fraud"
    _description = "P-7: Fraud Risk Assessment"
    _inherit = ["audit.planning.tab.mixin"]

    # Fraud Risk Factors - Incentives/Pressures
    fraud_incentives = fields.Html(
        string="Incentives/Pressures",
        help="ISA 240: Conditions creating incentive or pressure to commit fraud.",
    )
    
    # Fraud Risk Factors - Opportunities
    fraud_opportunities = fields.Html(
        string="Opportunities",
        help="Circumstances providing opportunity for fraud.",
    )
    
    # Fraud Risk Factors - Attitudes/Rationalizations
    fraud_attitudes = fields.Html(
        string="Attitudes/Rationalizations",
        help="Attitudes or rationalizations that may justify fraudulent behavior.",
    )
    
    # Team Discussion
    fraud_discussion_date = fields.Date(
        string="Team Discussion Date",
        help="ISA 240: Date of engagement team discussion on fraud risks.",
    )
    fraud_discussion_participants = fields.Many2many(
        "res.users",
        "audit_planning_p7_discussion_rel",
        "p7_id",
        "user_id",
        string="Discussion Participants",
    )
    fraud_discussion_summary = fields.Html(
        string="Discussion Summary",
        help="Summary of team brainstorming on fraud susceptibility.",
    )
    
    # Presumed Risks
    revenue_recognition_risk = fields.Boolean(
        string="Revenue Recognition Risk",
        default=True,
        help="ISA 240: Presumed significant risk unless rebutted.",
    )
    revenue_recognition_rebutted = fields.Boolean(
        string="Revenue Recognition Rebutted",
    )
    revenue_rebuttal_justification = fields.Html(
        string="Rebuttal Justification",
    )
    
    management_override_risk = fields.Boolean(
        string="Management Override Risk",
        default=True,
        help="ISA 240: Cannot be rebutted - always a significant risk.",
    )
    
    # Identified Fraud Risks
    fraud_risk_ids = fields.One2many(
        "audit.planning.p7.fraud.risk",
        "p7_id",
        string="Identified Fraud Risks",
    )
    
    # Responses
    fraud_responses = fields.Html(
        string="Overall Fraud Risk Responses",
        help="Planned responses to assessed fraud risks.",
    )
    
    # Journal Entry Testing Plan
    journal_entry_testing_plan = fields.Html(
        string="Journal Entry Testing Plan",
        help="ISA 240: Mandatory testing of journal entries.",
    )


class PlanningP7FraudRisk(models.Model):
    _name = "audit.planning.p7.fraud.risk"
    _description = "Identified Fraud Risk"
    _order = "sequence, id"

    p7_id = fields.Many2one(
        "audit.planning.p7.fraud",
        string="Fraud Assessment",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(default=10)
    name = fields.Char(string="Risk Description", required=True)
    fraud_type = fields.Selection([
        ("fraudulent_reporting", "Fraudulent Financial Reporting"),
        ("misappropriation", "Misappropriation of Assets"),
    ], string="Fraud Type", required=True)
    affected_account = fields.Char(string="Affected Account/Assertion")
    risk_level = fields.Selection([
        ("moderate", "Moderate"),
        ("high", "High"),
    ], string="Risk Level", default="high")
    is_significant = fields.Boolean(string="Significant Risk", default=True)
    planned_response = fields.Text(string="Planned Response")


# ═══════════════════════════════════════════════════════════════════════
# P-8: Going Concern (ISA 570)
# ═══════════════════════════════════════════════════════════════════════
class PlanningP8GoingConcern(models.Model):
    _name = "audit.planning.p8.going_concern"
    _description = "P-8: Going Concern (Preliminary)"
    _inherit = ["audit.planning.tab.mixin"]

    # Initial Assessment
    going_concern_indicators = fields.Html(
        string="Going Concern Indicators",
        help="Financial, operating, and other indicators.",
    )
    
    # Financial Indicators
    financial_indicators = fields.Html(
        string="Financial Indicators",
        help="Net liability position, negative operating cash flows, etc.",
    )
    financial_indicator_present = fields.Boolean(
        string="Financial Indicators Present",
    )
    
    # Operating Indicators
    operating_indicators = fields.Html(
        string="Operating Indicators",
        help="Loss of key management, labor difficulties, key customer loss, etc.",
    )
    operating_indicator_present = fields.Boolean(
        string="Operating Indicators Present",
    )
    
    # Other Indicators
    other_indicators = fields.Html(
        string="Other Indicators",
        help="Non-compliance with capital requirements, pending litigation, etc.",
    )
    other_indicator_present = fields.Boolean(
        string="Other Indicators Present",
    )
    
    # Management's Assessment
    management_assessment_obtained = fields.Boolean(
        string="Management Assessment Obtained",
    )
    management_assessment_period = fields.Char(
        string="Assessment Period",
        help="Period covered by management's assessment.",
    )
    management_assessment_review = fields.Html(
        string="Review of Management's Assessment",
    )
    
    # Preliminary Conclusion
    preliminary_conclusion = fields.Selection([
        ("no_concern", "No Material Uncertainty"),
        ("uncertainty", "Material Uncertainty Exists"),
        ("inadequate_disclosure", "Inadequate Disclosure"),
        ("further_procedures", "Further Procedures Required"),
    ], string="Preliminary Conclusion")
    
    conclusion_notes = fields.Html(
        string="Conclusion Notes",
    )


# ═══════════════════════════════════════════════════════════════════════
# P-9: Laws & Regulations (ISA 250)
# ═══════════════════════════════════════════════════════════════════════
class PlanningP9Compliance(models.Model):
    _name = "audit.planning.p9.compliance"
    _description = "P-9: Laws & Regulations"
    _inherit = ["audit.planning.tab.mixin"]

    # Laws with Direct Effect
    direct_effect_laws = fields.Html(
        string="Laws with Direct Effect on FS",
        help="ISA 250: Laws directly affecting financial statement amounts.",
    )
    
    # Other Laws
    other_laws = fields.Html(
        string="Other Applicable Laws & Regulations",
        help="Laws that may affect operations but not directly FS amounts.",
    )
    
    # Pakistan-Specific Compliance
    companies_act_compliance = fields.Html(
        string="Companies Act 2017 Compliance",
    )
    income_tax_ordinance = fields.Html(
        string="Income Tax Ordinance 2001",
    )
    sales_tax_act = fields.Html(
        string="Sales Tax Act 1990",
    )
    secp_regulations = fields.Html(
        string="SECP Regulations",
    )
    sbp_regulations = fields.Html(
        string="SBP Regulations (if applicable)",
    )
    
    # Industry-Specific
    industry_specific_laws = fields.Html(
        string="Industry-Specific Regulations",
    )
    
    # Identified Non-Compliance
    non_compliance_ids = fields.One2many(
        "audit.planning.p9.non_compliance",
        "p9_id",
        string="Identified Non-Compliance",
    )
    
    # Procedures
    planned_procedures = fields.Html(
        string="Planned Procedures",
        help="Procedures to identify non-compliance.",
    )


class PlanningP9NonCompliance(models.Model):
    _name = "audit.planning.p9.non_compliance"
    _description = "Identified Non-Compliance"
    _order = "id"

    p9_id = fields.Many2one(
        "audit.planning.p9.compliance",
        string="Compliance Assessment",
        required=True,
        ondelete="cascade",
    )
    law_regulation = fields.Char(string="Law/Regulation", required=True)
    nature_of_noncompliance = fields.Text(string="Nature of Non-Compliance")
    potential_impact = fields.Text(string="Potential Impact on FS")
    management_response = fields.Text(string="Management Response")
    audit_response = fields.Text(string="Audit Response")


# ═══════════════════════════════════════════════════════════════════════
# P-10: Related Parties Planning (ISA 550)
# ═══════════════════════════════════════════════════════════════════════
class PlanningP10RelatedParty(models.Model):
    _name = "audit.planning.p10.related_party"
    _description = "P-10: Related Parties Planning"
    _inherit = ["audit.planning.tab.mixin"]

    # Understanding
    related_party_understanding = fields.Html(
        string="Understanding of Related Party Relationships",
        help="ISA 550: Nature and business rationale of RP relationships.",
    )
    
    # Identification
    related_party_ids = fields.One2many(
        "audit.planning.p10.related_party.line",
        "p10_id",
        string="Identified Related Parties",
    )
    
    # Transactions
    significant_transactions = fields.Html(
        string="Significant RP Transactions Identified",
        help="Transactions outside normal course of business.",
    )
    
    # Risk Assessment
    rp_risk_assessment = fields.Html(
        string="Related Party Risk Assessment",
    )
    rp_risk_level = fields.Selection([
        ("low", "Low"),
        ("moderate", "Moderate"),
        ("high", "High"),
    ], string="RP Risk Level")
    
    # Fraud Consideration
    rp_fraud_consideration = fields.Html(
        string="RP Fraud Risk Consideration",
        help="ISA 550/240: Fraud risk related to RP transactions.",
    )
    
    # Procedures
    planned_procedures = fields.Html(
        string="Planned RP Procedures",
    )
    
    # Attachments
    rp_schedule_ids = fields.Many2many(
        "ir.attachment",
        "audit_planning_p10_schedule_rel",
        "p10_id",
        "attachment_id",
        string="RP Schedules",
    )


class PlanningP10RelatedPartyLine(models.Model):
    _name = "audit.planning.p10.related_party.line"
    _description = "Related Party"
    _order = "id"

    p10_id = fields.Many2one(
        "audit.planning.p10.related_party",
        string="RP Planning",
        required=True,
        ondelete="cascade",
    )
    name = fields.Char(string="Related Party Name", required=True)
    relationship = fields.Selection([
        ("subsidiary", "Subsidiary"),
        ("associate", "Associate"),
        ("joint_venture", "Joint Venture"),
        ("key_management", "Key Management Personnel"),
        ("director", "Director"),
        ("shareholder", "Major Shareholder"),
        ("family", "Family Member"),
        ("other", "Other"),
    ], string="Relationship Type", required=True)
    nature_of_transactions = fields.Text(string="Nature of Transactions")
    balance_outstanding = fields.Float(string="Balance Outstanding")
    transactions_volume = fields.Float(string="Transaction Volume (Year)")


# ═══════════════════════════════════════════════════════════════════════
# P-11: Group Audit Planning (ISA 600)
# ═══════════════════════════════════════════════════════════════════════
class PlanningP11Group(models.Model):
    _name = "audit.planning.p11.group"
    _description = "P-11: Group Audit Planning"
    _inherit = ["audit.planning.tab.mixin"]

    # Applicability
    is_group_audit = fields.Boolean(
        string="Group Audit Applicable",
        help="Whether this is a group audit engagement.",
    )
    not_applicable_reason = fields.Html(
        string="Reason Not Applicable",
    )
    
    # Group Structure
    group_structure = fields.Html(
        string="Group Structure",
        help="Description of group structure and components.",
    )
    
    # Components
    component_ids = fields.One2many(
        "audit.planning.p11.component",
        "p11_id",
        string="Components",
    )
    
    # Component Auditors
    component_auditors_involved = fields.Boolean(
        string="Component Auditors Involved",
    )
    component_auditor_assessment = fields.Html(
        string="Component Auditor Assessment",
        help="Assessment of component auditor competence and independence.",
    )
    
    # Group Materiality
    group_materiality = fields.Float(string="Group Materiality")
    component_materiality = fields.Html(
        string="Component Materiality",
        help="Materiality levels for components.",
    )
    
    # Instructions
    group_instructions = fields.Html(
        string="Group Audit Instructions",
        help="Instructions to be issued to component auditors.",
    )
    
    # Consolidation
    consolidation_procedures = fields.Html(
        string="Consolidation Procedures",
    )

    @api.depends("notes", "review_status", "is_group_audit", "not_applicable_reason")
    def _compute_is_complete(self):
        for record in self:
            if record.is_group_audit:
                record.is_complete = (
                    bool(record.notes) and
                    record.review_status in ("prepared", "reviewed")
                )
            else:
                # If not a group audit, just need notes explaining why
                record.is_complete = (
                    bool(record.not_applicable_reason) and
                    record.review_status in ("prepared", "reviewed")
                )


class PlanningP11Component(models.Model):
    _name = "audit.planning.p11.component"
    _description = "Group Component"
    _order = "significance desc, name"

    p11_id = fields.Many2one(
        "audit.planning.p11.group",
        string="Group Planning",
        required=True,
        ondelete="cascade",
    )
    name = fields.Char(string="Component Name", required=True)
    significance = fields.Selection([
        ("significant", "Significant"),
        ("not_significant", "Not Significant"),
    ], string="Significance", required=True)
    component_auditor = fields.Char(string="Component Auditor")
    work_to_perform = fields.Selection([
        ("full", "Full Scope Audit"),
        ("specified", "Specified Procedures"),
        ("analytical", "Analytical Procedures Only"),
        ("none", "No Work"),
    ], string="Work to be Performed")
    materiality = fields.Float(string="Component Materiality")


# ═══════════════════════════════════════════════════════════════════════
# P-12: Audit Strategy & Audit Plan (ISA 300)
# ═══════════════════════════════════════════════════════════════════════
class PlanningP12Strategy(models.Model):
    _name = "audit.planning.p12.strategy"
    _description = "P-12: Audit Strategy & Audit Plan"
    _inherit = ["audit.planning.tab.mixin"]

    # Overall Audit Strategy
    audit_strategy_summary = fields.Html(
        string="Overall Audit Strategy",
        help="ISA 300: Summary of overall audit strategy.",
    )
    
    # Scope
    audit_scope = fields.Html(
        string="Audit Scope",
        help="Scope of the audit, reporting framework, locations.",
    )
    
    # Timing
    audit_timing = fields.Html(
        string="Audit Timing",
        help="Key dates, interim procedures, year-end procedures.",
    )
    interim_procedures_date = fields.Date(string="Interim Procedures Date")
    year_end_procedures_date = fields.Date(string="Year-End Procedures Date")
    report_deadline = fields.Date(string="Report Deadline")
    
    # Direction
    audit_direction = fields.Html(
        string="Nature, Timing & Extent of Resources",
        help="Resources, team deployment, supervision requirements.",
    )
    
    # Audit Approach by Cycle
    revenue_approach = fields.Html(string="Revenue Cycle Approach")
    purchases_approach = fields.Html(string="Purchases Cycle Approach")
    payroll_approach = fields.Html(string="Payroll Cycle Approach")
    inventory_approach = fields.Html(string="Inventory Approach")
    fixed_assets_approach = fields.Html(string="Fixed Assets Approach")
    cash_bank_approach = fields.Html(string="Cash & Bank Approach")
    borrowings_approach = fields.Html(string="Borrowings Approach")
    equity_approach = fields.Html(string="Equity Approach")
    
    # Budget
    budgeted_hours = fields.Float(string="Budgeted Hours")
    budget_breakdown = fields.Html(string="Budget Breakdown")
    
    # Attachments
    audit_plan_attachment_ids = fields.Many2many(
        "ir.attachment",
        "audit_planning_p12_plan_rel",
        "p12_id",
        "attachment_id",
        string="Detailed Audit Plan",
    )


# ═══════════════════════════════════════════════════════════════════════
# P-13: Planning Review & Approval (ISA 220, ISQM-1)
# ═══════════════════════════════════════════════════════════════════════
class PlanningP13Review(models.Model):
    _name = "audit.planning.p13.review"
    _description = "P-13: Planning Review & Approval"
    _inherit = ["audit.planning.tab.mixin"]

    # Review Summary
    review_summary = fields.Html(
        string="Planning Review Summary",
        help="Overall summary of planning review.",
    )
    
    # Manager Review
    manager_review_notes = fields.Html(
        string="Manager Review Notes",
    )
    manager_reviewed = fields.Boolean(string="Manager Reviewed")
    manager_reviewed_by = fields.Many2one("res.users", string="Manager Reviewed By")
    manager_reviewed_on = fields.Datetime(string="Manager Reviewed On")
    
    # Partner Review
    partner_review_notes = fields.Html(
        string="Partner Review Notes",
    )
    partner_reviewed = fields.Boolean(string="Partner Reviewed")
    partner_reviewed_by = fields.Many2one("res.users", string="Partner Reviewed By")
    partner_reviewed_on = fields.Datetime(string="Partner Reviewed On")
    
    # EQCR
    eqcr_required = fields.Boolean(string="EQCR Required")
    eqcr_review_notes = fields.Html(string="EQCR Review Notes")
    eqcr_reviewed = fields.Boolean(string="EQCR Completed")
    eqcr_reviewed_by = fields.Many2one("res.users", string="EQCR Reviewed By")
    eqcr_reviewed_on = fields.Datetime(string="EQCR Reviewed On")
    
    # Outstanding Issues
    outstanding_issues = fields.Html(
        string="Outstanding Issues",
        help="Issues requiring resolution before execution.",
    )
    issues_resolved = fields.Boolean(string="All Issues Resolved")
    
    # Final Approval
    planning_approved = fields.Boolean(string="Planning Approved")
    approved_by = fields.Many2one("res.users", string="Approved By")
    approved_on = fields.Datetime(string="Approved On")
    
    # Execution Authorization
    execution_authorized = fields.Boolean(
        string="Execution Phase Authorized",
        help="Authorization to proceed with execution phase.",
    )

    def action_manager_review(self):
        """Manager completes review."""
        self.ensure_one()
        self.manager_reviewed = True
        self.manager_reviewed_by = self.env.user
        self.manager_reviewed_on = fields.Datetime.now()
        return True

    def action_partner_review(self):
        """Partner completes review."""
        self.ensure_one()
        if not self.manager_reviewed:
            raise UserError(_("Manager must review before partner."))
        self.partner_reviewed = True
        self.partner_reviewed_by = self.env.user
        self.partner_reviewed_on = fields.Datetime.now()
        return True

    def action_eqcr_review(self):
        """EQCR completes review."""
        self.ensure_one()
        if not self.eqcr_required:
            raise UserError(_("EQCR is not required for this engagement."))
        self.eqcr_reviewed = True
        self.eqcr_reviewed_by = self.env.user
        self.eqcr_reviewed_on = fields.Datetime.now()
        return True

    def action_approve_planning(self):
        """Final approval of planning."""
        self.ensure_one()
        if not self.partner_reviewed:
            raise UserError(_("Partner must review before approval."))
        if self.eqcr_required and not self.eqcr_reviewed:
            raise UserError(_("EQCR must complete review before approval."))
        if self.outstanding_issues and not self.issues_resolved:
            raise UserError(_("Resolve all outstanding issues before approval."))
        
        self.planning_approved = True
        self.approved_by = self.env.user
        self.approved_on = fields.Datetime.now()
        self.execution_authorized = True
        self.review_status = "reviewed"
        
        # Update parent planning record
        if self.planning_id:
            self.planning_id.action_approve_planning()
        
        return True

    @api.depends("notes", "review_status", "planning_approved")
    def _compute_is_complete(self):
        for record in self:
            record.is_complete = (
                bool(record.notes) and
                record.planning_approved and
                record.review_status == "reviewed"
            )
