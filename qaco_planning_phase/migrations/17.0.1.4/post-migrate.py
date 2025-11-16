from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """Add newly introduced client context columns to existing databases."""
    if not version:
        return

    field_defs = {
        "client_year_end": "DATE",
        "client_regulator": "VARCHAR",
        "client_listing_exchange": "VARCHAR",
        "client_ownership_structure": "TEXT",
        "client_governance_notes": "TEXT",
        "client_objectives_strategies": "TEXT",
        "client_measurement_basis": "TEXT",
        "client_it_environment": "TEXT",
        "client_compliance_matters": "TEXT",
    }

    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        table = env["qaco.planning.phase"]._table

    for column, sql_type in field_defs.items():
        cr.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_name = %s
                      AND column_name = %s
                ) THEN
                    ALTER TABLE %s ADD COLUMN %s %s;
                END IF;
            END$$
            """,
            (table, column, table, column, sql_type),
        )
