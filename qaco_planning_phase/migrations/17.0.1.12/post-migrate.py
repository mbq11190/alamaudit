from odoo import api, SUPERUSER_ID


def post_migrate(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    model_name = "qaco.planning.phase"
    fields_to_update = ["materiality_basis", "materiality_benchmark_rationale"]

    for field_name in fields_to_update:
        field = env["ir.model.fields"].search(
            [
                ("model", "=", model_name),
                ("name", "=", field_name),
            ],
            limit=1,
        )
        if field and field.required:
            field.required = False

    phases = env[model_name].search([])
    phases.filtered(lambda record: not record.materiality_basis).write({"materiality_basis": "profit_before_tax"})
    phases.filtered(lambda record: not record.materiality_benchmark_rationale).write(
        {"materiality_benchmark_rationale": "Materiality benchmark rationale to be confirmed."}
    )
