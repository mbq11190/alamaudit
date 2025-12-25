# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ISA315Understanding(models.Model):
    _name = "qaco.isa315.understanding"
    _description = "ISA 315 – Understanding the Entity & Its Environment"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="Engagement Reference",
        required=True,
        tracking=True,
        help="Unique reference for audit engagement / planning file.",
    )

    # 1. Entity Profile & Legal Structure
    legal_name = fields.Char(help="Registered legal name as per SECP / Trust Deed / Partnership.")
    ntn = fields.Char(string="NTN", help="National Tax Number as issued by FBR.")
    strn = fields.Char(string="STRN", help="Sales Tax Registration Number, if applicable.")
    entity_type = fields.Selection(
        [
            ("private", "Private Limited"),
            ("public", "Public Limited"),
            ("listed", "Listed Company"),
            ("section42", "Section 42 / NPO"),
            ("partnership", "Partnership"),
            ("ngo", "NGO / Trust"),
        ],
        help="Legal form under Pakistani law.",
    )
    incorporation_date = fields.Date(help="Date of incorporation / registration.")
    ownership_structure = fields.Text(help="Shareholding pattern and Ultimate Beneficial Ownership (UBO).")
    group_structure = fields.Text(help="Holding, subsidiaries, associates, and group relationships.")
    board_kmp = fields.Text(help="Board of Directors and Key Management Personnel.")

    # 2. Industry, Regulatory & External Environment
    industry_overview = fields.Text(help="Industry characteristics, trends, and risk profile.")
    competition_level = fields.Text(help="Competitive landscape and market position.")
    regulatory_environment = fields.Text(help="Applicable regulators: SECP, SBP, NEPRA, OGRA, PTA, DRAP, etc.")
    economic_factors = fields.Text(help="Inflation, FX exposure, interest rates, and economic conditions.")

    # 3. Nature of Business Operations
    products_services = fields.Text(help="Principal products and services offered.")
    revenue_streams = fields.Text(help="Revenue sources and pricing mechanisms.")
    key_customers_suppliers = fields.Text(help="Major customers and suppliers with concentration risk.")
    contractual_arrangements = fields.Text(help="Long-term contracts, MOUs, and agreements.")
    related_parties = fields.Text(help="Related-party relationships as per IAS 24.")

    # 4. Governance Structure & Ethical Environment
    governance_framework = fields.Text(help="Corporate governance framework and oversight.")
    ethics_policies = fields.Text(help="Code of conduct, ethics policies, and compliance culture.")
    audit_committee = fields.Text(help="Audit committee composition and effectiveness.")
    past_issues = fields.Text(help="History of fraud, litigation, or regulatory penalties.")

    # 5. Accounting Framework & Policies
    reporting_framework = fields.Char(
        default="IFRS as adopted in Pakistan",
        help="Applicable financial reporting framework.",
    )
    significant_policies = fields.Text(help="Significant accounting policies.")
    accounting_estimates = fields.Text(help="Key estimates and management judgments.")
    high_risk_areas = fields.Text(help="Impairment, provisions, fair value measurements.")

    # 6. Objectives, Strategies & Business Risks
    business_objectives = fields.Text(help="Entity objectives and strategic plans.")
    future_plans = fields.Text(help="Expansion, restructuring, or financing plans.")
    business_risks = fields.Text(help="Business risks that may lead to risk of material misstatement (ISA 315 linkage).")

    # 7. Measurement & Financial Performance
    kpis = fields.Text(help="Key performance indicators used by management.")
    budgeting_process = fields.Text(help="Budgeting, forecasting, and variance analysis.")
    performance_metrics = fields.Text(help="Financial and non-financial performance measures.")

    # 8. Internal Control System (High-Level)
    control_environment = fields.Text(help="Overall control environment and tone at the top.")
    entity_level_controls = fields.Text(help="Entity-level controls relevant to audit.")
    segregation_of_duties = fields.Text(help="Assessment of segregation of duties.")
    internal_audit = fields.Text(help="Existence and role of internal audit function.")

    # 9. Information Systems & IT Environment
    accounting_system = fields.Char(help="Accounting / ERP system used (e.g., Odoo, SAP).")
    it_controls = fields.Text(help="Access controls, user roles, and IT general controls.")
    cybersecurity = fields.Text(help="Backup, cybersecurity, and data protection measures.")

    # 10. Compliance With Laws & Regulations
    tax_compliance = fields.Text(help="Income tax, sales tax, PRA/SRB/KPRA/BRA compliance.")
    secp_compliance = fields.Text(help="SECP filings and statutory compliance.")
    labor_laws = fields.Text(help="EOBI, SESSI, labor and employment law compliance.")
    litigation = fields.Text(help="Pending litigation, tax audits, or notices.")

    # 11. Fraud Risk Considerations
    fraud_incentives = fields.Text(help="Incentives or pressures on management.")
    fraud_opportunities = fields.Text(help="Opportunities due to weak controls.")
    fraud_attitude = fields.Text(help="Management attitude and rationalization.")
    fraud_brainstorming = fields.Text(help="Results of fraud brainstorming session.")

    # 12. Prior-Year Audit & Engagement Intelligence
    prior_audit_issues = fields.Text(help="Prior-year audit issues and management letters.")
    unadjusted_misstatements = fields.Text(help="Unadjusted misstatements from prior audits.")
    auditor_change = fields.Text(help="Issues with previous auditors, if any.")

    audit_id = fields.Many2one(
        "qaco.audit",
        string="Audit Engagement",
        help="Link to audit engagement (helps in automated naming and traceability)",
        index=True,
    )

    planning_main_id = fields.Many2one(
        "qaco.planning.main",
        string="Planning Main",
        help="Optional link to planning main orchestrator",
        index=True,
    )

    @api.model
    def create(self, vals):
        # Auto-populate name if missing for traceability
        if not vals.get("name") and vals.get("audit_id"):
            audit = self.env["qaco.audit"].browse(vals.get("audit_id"))
            vals["name"] = f"ISA315: {audit.client_id.name if audit and audit.client_id else 'Draft'}"
        return super().create(vals)
