from odoo import fields, models


class PlanningPhaseMateriality(models.Model):
    _inherit = "qaco.planning.phase"

    materiality_ids = fields.One2many(
        "qaco.materiality",
        "planning_id",
        string="Materiality Worksheets",
    )
