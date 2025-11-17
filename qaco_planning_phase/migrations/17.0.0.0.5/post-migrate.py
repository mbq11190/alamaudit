from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    fields_to_update = ["materiality_basis", "materiality_benchmark_rationale"]
    field_model = env["ir.model.fields"].sudo()
    for field_name in fields_to_update:
        field = field_model.search(
            [
                ("model", "=", "qaco.planning.phase"),
                ("name", "=", field_name),
            ],
            limit=1,
        )
        if field and field.required:
            field.write({"required": False})

    # Ensure legacy records have sensible defaults so the UI stops complaining
    planning_model = env["qaco.planning.phase"].sudo()
    records = planning_model.search([
        "|",
        ("materiality_basis", "=", False),
        ("materiality_benchmark_rationale", "=", False),
    ])
    for rec in records:
        vals = {}
        if not rec.materiality_basis:
            vals["materiality_basis"] = rec.materiality_base or "profit_before_tax"
        if not rec.materiality_benchmark_rationale:
            vals["materiality_benchmark_rationale"] = "Benchmark rationale pending update"
        if vals:
            rec.write(vals)
