# -*- coding: utf-8 -*-
"""
Audit Assertion Tags and Materiality Settings Models
ISA 315 - Assertions | ISA 320 - Materiality
"""
from odoo import fields, models


class AuditAssertionTag(models.Model):
    _name = "audit.assertion.tag"
    _description = "Audit Assertion"
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

    _sql_constraints = [
        ("assertion_code_unique", "unique(code)", "Assertion code must be unique."),
    ]


class MaterialityBenchmark(models.Model):
    """Materiality benchmark configuration per ISA 320."""
    _name = "audit.materiality.benchmark"
    _description = "Materiality Benchmark"
    _order = "sequence, name"

    name = fields.Char(string="Benchmark Name", required=True)
    code = fields.Char(string="Code", required=True)
    default_percentage = fields.Float(string="Default %", default=5.0)
    min_percentage = fields.Float(string="Min %", default=0.5)
    max_percentage = fields.Float(string="Max %", default=10.0)
    description = fields.Text(string="Description")
    entity_types = fields.Char(string="Applicable Entity Types", 
                               help="Comma-separated list: manufacturing,trading,services,financial,public,nonprofit")
    isa_guidance = fields.Text(string="ISA Guidance")
    sequence = fields.Integer(default=10)

    _sql_constraints = [
        ("benchmark_code_unique", "unique(code)", "Benchmark code must be unique."),
    ]


class MaterialitySetting(models.Model):
    """Materiality settings for performance materiality and trivial threshold."""
    _name = "audit.materiality.setting"
    _description = "Materiality Setting"
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


class MaterialityConsideration(models.Model):
    """Pakistan-specific materiality considerations."""
    _name = "audit.materiality.consideration"
    _description = "Materiality Consideration (Pakistan)"
    _order = "consideration_type, name"

    CONSIDERATION_TYPES = [
        ("regulatory", "Regulatory"),
        ("industry", "Industry-Specific"),
        ("risk", "Risk-Based"),
        ("qualitative", "Qualitative"),
    ]

    name = fields.Char(string="Consideration", required=True)
    consideration_type = fields.Selection(CONSIDERATION_TYPES, string="Type", required=True)
    description = fields.Text(string="Description")
    recommended_adjustment = fields.Float(string="Recommended Adjustment %",
                                         help="Positive increases materiality, negative decreases it")
    applicable_entity_types = fields.Char(string="Applicable Entity Types")
    regulatory_reference = fields.Char(string="Regulatory Reference")
