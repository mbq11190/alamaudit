from odoo import fields, models, _


class RiskAssessment(models.Model):
    """ISA 315/240/330 aligned risk assessment dossier."""

    _name = "qaco.risk.assessment"
    _description = "Risk Assessment (ISA 315, ISA 240, ISA 330)"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # Identification & tracking
    name = fields.Char(
        string="Assessment Reference",
        default=lambda self: self.env["ir.sequence"].next_by_code("qaco.risk.assessment") or _("New"),
        required=True,
        readonly=True,
        tracking=True,
    )

    # =============================================================
    # SECTION 1: RISK LEVELS (Inherent, Control, Detection)
    # =============================================================
    inherent_risk = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        string="Inherent Risk",
        tracking=True,
    )
    inherent_risk_basis = fields.Text(string="Inherent Risk Basis")
    control_risk = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        string="Control Risk",
        tracking=True,
    )
    control_risk_basis = fields.Text(string="Control Risk Basis")
    detection_risk = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        string="Detection Risk",
        tracking=True,
    )
    detection_risk_response = fields.Text(string="Detection Risk Response")
    overall_risk = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        string="Overall Risk Rating",
        tracking=True,
    )

    # =============================================================
    # SECTION 2: ENTITY LEVEL RISK ASSESSMENT – ISA 315
    # =============================================================
    governance_structure = fields.Text(string="Governance Structure")
    management_integrity = fields.Text(string="Management Integrity Assessment")
    management_competence = fields.Text(string="Management Competence")
    industry_risks = fields.Text(string="Industry Risks")
    regulatory_risks = fields.Text(string="Regulatory Risks")
    economic_factors = fields.Text(string="Economic / Economic Pressure Risks")
    competition_risks = fields.Text(string="Competition & Market Risks")
    business_processes = fields.Text(string="Key Business Processes")
    revenue_risks = fields.Text(string="Revenue Stream Risks")
    business_changes = fields.Text(string="Significant Business Changes")
    outsourcing_risks = fields.Text(string="Outsourcing Risks")

    # =============================================================
    # SECTION 3: FRAUD RISK ASSESSMENT (ISA 240)
    # =============================================================
    fraud_triangle_pressure = fields.Text(string="Fraud – Pressure")
    fraud_triangle_opportunity = fields.Text(string="Fraud – Opportunity")
    fraud_triangle_rationalization = fields.Text(string="Fraud – Rationalization")
    revenue_fraud_risk = fields.Selection(
        [("yes", "Yes – Significant Risk"), ("no", "No")],
        string="Revenue Fraud Risk (Mandatory under ISA 240)",
    )
    mgmt_override_risk = fields.Selection(
        [("yes", "Yes – Always Significant"), ("no", "No")],
        string="Management Override Risk (Mandatory)",
        tracking=True,
    )
    fraud_schemes_identified = fields.Text(string="Possible Fraud Schemes")
    journal_entry_risks = fields.Text(string="Journal Entry Risk Factors")
    asset_misappropriation_risk = fields.Text(string="Misappropriation of Assets Risk")
    anti_fraud_controls = fields.Text(string="Anti-Fraud Controls")
    fraud_inquiry_documentation = fields.Text(string="Fraud Inquiry Documentation")

    # =============================================================
    # SECTION 4: INTERNAL CONTROLS (ISA 315)
    # =============================================================
    control_environment = fields.Text(string="Control Environment")
    hr_practices = fields.Text(string="HR Practices")
    org_structure = fields.Text(string="Organizational Structure")
    authority_responsibility = fields.Text(string="Assignment of Authority")
    risk_assessment_process = fields.Text(string="Entity Risk Assessment Process")
    risk_response_process = fields.Text(string="How Risks Are Addressed")
    risk_documentation = fields.Text(string="Documentation of Risk Process")
    it_systems_used = fields.Text(string="IT Systems Used")
    change_management = fields.Text(string="IT Change Management")
    logical_access = fields.Text(string="Logical Access Controls")
    backup_recovery = fields.Text(string="Backup & Recovery (DRP/BCP)")
    interface_risks = fields.Text(string="Interface/API Risks")
    authorization_controls = fields.Text(string="Authorization Controls")
    reconciliations = fields.Text(string="Reconciliations")
    segregation_of_duties = fields.Text(string="Segregation of Duties")
    preventive_controls = fields.Text(string="Preventive Controls")
    detective_controls = fields.Text(string="Detective Controls")
    it_dependent_controls = fields.Text(string="IT Dependent Controls")
    monitoring_controls = fields.Text(string="Monitoring Controls")
    internal_audit_function = fields.Text(string="Internal Audit Function")
    board_oversight = fields.Text(string="Board / Audit Committee Oversight")
    corrective_actions = fields.Text(string="Corrective Actions Follow-up")
    control_deficiencies = fields.Text(string="Control Deficiencies Identified")

    # =============================================================
    # SECTION 5: ISA 330 – PLANNED RESPONSES
    # =============================================================
    planned_responses = fields.Text(string="Planned Responses to Significant Risks")
    tests_of_controls_planned = fields.Text(string="Tests of Controls Planned")
    substantive_analytics = fields.Text(string="Substantive Analytical Procedures")
    substantive_procedures = fields.Text(string="Substantive Procedures")
    extent_timing_nature = fields.Text(string="Extent / Timing / Nature")

    # =============================================================
    # SECTION 6: PROFESSIONAL JUDGEMENT – ISA 230
    # =============================================================
    basis_of_judgement = fields.Text(string="Basis for Risk Judgments")
    key_audit_judgements = fields.Text(string="Key Audit Judgments")

    # =============================================================
    # SECTION 7: SECP / AOB RISK AREAS
    # =============================================================
    listed_entity_flag = fields.Boolean(string="Listed Entity")
    pie_flag = fields.Boolean(string="PIE (Public Interest Entity)")
    aob_registration = fields.Char(string="AOB Registration No.")
    seccp_sros = fields.Text(string="Additional SECP SROs Applicable")
    aml_cft_risk = fields.Text(string="AML / CFT Risk Areas")

    # =============================================================
    # SECTION 8: RISK MATRIX (ONE2MANY)
    # =============================================================
    matrix_ids = fields.One2many(
        "qaco.risk.matrix",
        "risk_master_id",
        string="Risk Matrix",
    )


class RiskMatrix(models.Model):
    """Embedded risk matrix lines supporting ISA 315 documentation."""

    _name = "qaco.risk.matrix"
    _description = "Risk Matrix Line"

    risk_master_id = fields.Many2one(
        "qaco.risk.assessment",
        string="Risk Assessment",
        ondelete="cascade",
    )
    risk_reference = fields.Char(string="Risk ID / Reference")
    risk_description = fields.Text(string="Risk Description")
    fs_level = fields.Selection(
        [("yes", "FS-Level Risk"), ("no", "Assertion Level")],
        string="FS Level Risk",
    )
    affected_area = fields.Char(string="Financial Statement Impact")
    assertion = fields.Char(string="Relevant Assertions")
    likelihood = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        string="Likelihood",
    )
    impact = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        string="Impact",
    )
    combined_rating = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        string="Combined Rating",
    )
    significant_risk = fields.Boolean(string="Significant Risk")
    planned_response = fields.Text(string="Planned Response")
    controls_linked = fields.Text(string="Controls Mitigating Risk")
    reviewer_comments = fields.Text(string="Reviewer Comments")
