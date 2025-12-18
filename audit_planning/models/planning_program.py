# -*- coding: utf-8 -*-
"""
Auto-Generated Audit Programs Model

Risk-based audit programs auto-generated from P-6 Risk Assessment.
"""
from odoo import api, fields, models, _


class AuditPlanningProgram(models.Model):
    _name = "audit.planning.program"
    _description = "Auto-Generated Audit Program"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "cycle, sequence"

    CYCLES = [
        ("revenue", "Revenue Cycle"),
        ("purchases", "Purchases & Payables Cycle"),
        ("payroll", "Payroll Cycle"),
        ("inventory", "Inventory Cycle"),
        ("fixed_assets", "Fixed Assets Cycle"),
        ("cash_bank", "Cash & Bank Cycle"),
        ("borrowings", "Borrowings Cycle"),
        ("related_parties", "Related Parties Cycle"),
    ]

    RISK_LEVELS = [
        ("low", "Low"),
        ("moderate", "Moderate"),
        ("high", "High"),
    ]

    # Link to Planning
    planning_id = fields.Many2one(
        "audit.planning",
        string="Planning",
        required=True,
        ondelete="cascade",
        index=True,
    )
    
    # Program Details
    name = fields.Char(string="Program Name", required=True)
    sequence = fields.Integer(default=10)
    cycle = fields.Selection(CYCLES, string="Audit Cycle", required=True)
    
    # Risk-Based Parameters
    risk_level = fields.Selection(RISK_LEVELS, string="Risk Level", required=True)
    risks_addressed = fields.Html(string="Risks Addressed")
    
    # Procedure Details
    objective = fields.Html(string="Audit Objective")
    nature_of_procedures = fields.Html(string="Nature of Procedures")
    timing_of_procedures = fields.Html(string="Timing of Procedures")
    extent_of_procedures = fields.Html(string="Extent of Procedures")
    
    # Sampling
    sample_size = fields.Integer(string="Sample Size")
    sample_size_logic = fields.Html(string="Sample Size Logic")
    
    # Procedures
    procedure_ids = fields.One2many(
        "audit.planning.program.procedure",
        "program_id",
        string="Audit Procedures",
    )
    
    # Review
    prepared_by = fields.Many2one("res.users", string="Prepared By")
    prepared_on = fields.Datetime(string="Prepared On")
    reviewed_by = fields.Many2one("res.users", string="Reviewed By")
    reviewed_on = fields.Datetime(string="Reviewed On")
    
    # Status
    status = fields.Selection([
        ("draft", "Draft"),
        ("finalized", "Finalized"),
    ], string="Status", default="draft")

    def action_finalize(self):
        """Finalize the audit program."""
        self.ensure_one()
        self.status = "finalized"
        self.reviewed_by = self.env.user
        self.reviewed_on = fields.Datetime.now()
        self.message_post(body=_("Audit program finalized."))
        return True

    @api.model
    def generate_for_planning(self, planning_id):
        """Generate all cycle programs for a planning record."""
        planning = self.env["audit.planning"].browse(planning_id)
        if not planning.exists():
            return False
        
        for cycle_code, cycle_name in self.CYCLES:
            existing = self.search([
                ("planning_id", "=", planning_id),
                ("cycle", "=", cycle_code),
            ])
            if existing:
                continue
            
            risk_level = planning._get_cycle_risk_level(cycle_code)
            self.create({
                "planning_id": planning_id,
                "name": f"{cycle_name} - Audit Program",
                "cycle": cycle_code,
                "risk_level": risk_level,
                "sample_size": planning._compute_sample_size(risk_level),
                "nature_of_procedures": planning._get_procedure_nature(risk_level),
                "timing_of_procedures": planning._get_procedure_timing(risk_level),
                "extent_of_procedures": planning._get_procedure_extent(risk_level),
                "objective": self._get_cycle_objective(cycle_code),
                "procedure_ids": [(0, 0, proc) for proc in self._get_default_procedures(cycle_code, risk_level)],
            })
        
        return True

    def _get_cycle_objective(self, cycle_code):
        """Get default audit objective for a cycle."""
        objectives = {
            "revenue": "To obtain sufficient appropriate audit evidence that revenue transactions are complete, accurate, and properly recorded in the correct period.",
            "purchases": "To obtain sufficient appropriate audit evidence that purchases and payables are complete, accurate, and represent valid obligations.",
            "payroll": "To obtain sufficient appropriate audit evidence that payroll costs and liabilities are complete, accurate, and properly authorized.",
            "inventory": "To obtain sufficient appropriate audit evidence that inventory exists, is properly valued, and is owned by the entity.",
            "fixed_assets": "To obtain sufficient appropriate audit evidence that fixed assets exist, are properly valued, and are owned by the entity.",
            "cash_bank": "To obtain sufficient appropriate audit evidence that cash and bank balances are complete, exist, and are properly disclosed.",
            "borrowings": "To obtain sufficient appropriate audit evidence that borrowings are complete, accurately recorded, and represent valid obligations.",
            "related_parties": "To obtain sufficient appropriate audit evidence that related party transactions are identified, properly disclosed, and at arm's length.",
        }
        return objectives.get(cycle_code, "")

    def _get_default_procedures(self, cycle_code, risk_level):
        """Get default procedures for a cycle based on risk level."""
        procedures = []
        
        # Base procedures for all cycles
        base_procedures = [
            {"name": "Obtain and document understanding of the cycle", "procedure_type": "understanding", "sequence": 10},
            {"name": "Perform walkthrough of key controls", "procedure_type": "walkthrough", "sequence": 20},
            {"name": "Perform substantive analytical procedures", "procedure_type": "analytical", "sequence": 30},
        ]
        
        # Risk-based additional procedures
        if risk_level == "high":
            base_procedures.extend([
                {"name": "Extended sample testing with increased sample size", "procedure_type": "substantive", "sequence": 40},
                {"name": "100% testing of items above materiality", "procedure_type": "substantive", "sequence": 50},
                {"name": "Additional inquiries of management", "procedure_type": "inquiry", "sequence": 60},
                {"name": "Year-end cut-off testing", "procedure_type": "cutoff", "sequence": 70},
            ])
        elif risk_level == "moderate":
            base_procedures.extend([
                {"name": "Sample testing of transactions", "procedure_type": "substantive", "sequence": 40},
                {"name": "Testing of items above performance materiality", "procedure_type": "substantive", "sequence": 50},
            ])
        else:  # low
            base_procedures.extend([
                {"name": "Limited sample testing", "procedure_type": "substantive", "sequence": 40},
            ])
        
        return base_procedures


class AuditPlanningProgramProcedure(models.Model):
    _name = "audit.planning.program.procedure"
    _description = "Audit Program Procedure"
    _order = "sequence, id"

    program_id = fields.Many2one(
        "audit.planning.program",
        string="Program",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(default=10)
    name = fields.Char(string="Procedure", required=True)
    procedure_type = fields.Selection([
        ("understanding", "Understanding"),
        ("walkthrough", "Walkthrough"),
        ("test_of_control", "Test of Control"),
        ("analytical", "Analytical Procedure"),
        ("substantive", "Substantive Testing"),
        ("inquiry", "Inquiry"),
        ("inspection", "Inspection"),
        ("observation", "Observation"),
        ("confirmation", "Confirmation"),
        ("recalculation", "Recalculation"),
        ("reperformance", "Reperformance"),
        ("cutoff", "Cut-off Testing"),
    ], string="Procedure Type")
    assertion = fields.Selection([
        ("existence", "Existence/Occurrence"),
        ("completeness", "Completeness"),
        ("accuracy", "Accuracy/Valuation"),
        ("cutoff", "Cut-off"),
        ("classification", "Classification"),
        ("rights", "Rights & Obligations"),
        ("presentation", "Presentation & Disclosure"),
    ], string="Assertion Addressed")
    sample_size = fields.Integer(string="Sample Size")
    timing = fields.Selection([
        ("interim", "Interim"),
        ("year_end", "Year-End"),
        ("both", "Both"),
    ], string="Timing", default="year_end")
    assigned_to = fields.Many2one("res.users", string="Assigned To")
    
    # Execution (for later use)
    status = fields.Selection([
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("not_applicable", "N/A"),
    ], string="Status", default="pending")
    conclusion = fields.Text(string="Conclusion")
    workpaper_ref = fields.Char(string="Workpaper Reference")
