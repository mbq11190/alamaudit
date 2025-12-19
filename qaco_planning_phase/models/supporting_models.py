# -*- coding: utf-8 -*-
"""
Supporting Models for Planning Phase
- Assertion Tags (ISA 315)
- Materiality Benchmarks (ISA 320)
- Planning Checklists
"""
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class QacoAssertionTag(models.Model):
    """ISA 315 Financial Statement Assertions"""
    _name = "qaco.assertion.tag"
    _description = "Audit Assertion (ISA 315)"
    _order = "category, sequence, name"

    CATEGORIES = [
        ("transactions", "Classes of Transactions & Events"),
        ("balances", "Account Balances"),
        ("disclosure", "Presentation & Disclosure"),
    ]

    name = fields.Char(string="Assertion", required=True)
    code = fields.Char(string="Code", required=True)
    category = fields.Selection(CATEGORIES, string="Category", required=True)
    description = fields.Text(string="Description")
    isa_reference = fields.Char(string="ISA Reference")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("assertion_code_unique", "unique(code)", "Assertion code must be unique."),
    ]


class QacoMaterialityBenchmark(models.Model):
    """Materiality benchmark configuration per ISA 320."""
    _name = "qaco.materiality.benchmark"
    _description = "Materiality Benchmark (ISA 320)"
    _order = "sequence, name"

    name = fields.Char(string="Benchmark Name", required=True)
    code = fields.Char(string="Code", required=True)
    default_percentage = fields.Float(string="Default %", default=5.0)
    min_percentage = fields.Float(string="Min %", default=0.5)
    max_percentage = fields.Float(string="Max %", default=10.0)
    description = fields.Text(string="Description")
    entity_types = fields.Char(
        string="Applicable Entity Types",
        help="Comma-separated list: manufacturing,trading,services,financial,public,nonprofit"
    )
    isa_guidance = fields.Text(string="ISA Guidance")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("benchmark_code_unique", "unique(code)", "Benchmark code must be unique."),
    ]


class QacoMaterialitySetting(models.Model):
    """Materiality settings for performance materiality and trivial threshold."""
    _name = "qaco.materiality.setting"
    _description = "Materiality Setting (ISA 320)"
    _order = "setting_type, name"

    SETTING_TYPES = [
        ("performance_materiality", "Performance Materiality"),
        ("trivial_threshold", "Clearly Trivial Threshold"),
        ("specific_materiality", "Specific Materiality"),
    ]

    name = fields.Char(string="Setting Name", required=True)
    setting_type = fields.Selection(SETTING_TYPES, string="Type", required=True)
    default_percentage = fields.Float(string="Default %", default=75.0)
    min_percentage = fields.Float(string="Min %", default=50.0)
    max_percentage = fields.Float(string="Max %", default=75.0)
    description = fields.Text(string="Description")
    isa_guidance = fields.Text(string="ISA Guidance")
    active = fields.Boolean(default=True)


class QacoPlanningChecklist(models.Model):
    """Planning checklist items template and instance tracking"""
    _name = "qaco.planning.checklist"
    _description = "Audit Planning Checklist"
    _order = "planning_main_id, sequence, id"

    planning_main_id = fields.Many2one(
        "qaco.planning.main",
        string="Planning Phase",
        ondelete="cascade",
        index=True,
    )
    name = fields.Char(string="Item", required=True)
    isa_reference = fields.Char(string="ISA Reference")
    is_mandatory = fields.Boolean(string="Mandatory", default=True)
    completed = fields.Boolean(string="Completed", default=False)
    completed_by = fields.Many2one("res.users", string="Completed By")
    completed_on = fields.Datetime(string="Completed On")
    is_template = fields.Boolean(
        string="Template Item",
        default=False,
        help="Template rows copied into new plans."
    )
    sequence = fields.Integer(default=10)

    @api.onchange("completed")
    def _onchange_completed(self):
        if self.completed and not self.completed_by:
            self.completed_by = self.env.user
            self.completed_on = fields.Datetime.now()
        elif not self.completed:
            self.completed_by = False
            self.completed_on = False

    @api.constrains("planning_main_id", "is_template")
    def _check_planning_required(self):
        for rec in self:
            if not rec.is_template and not rec.planning_main_id:
                raise ValidationError("Checklist rows must belong to a planning phase unless marked as template.")
