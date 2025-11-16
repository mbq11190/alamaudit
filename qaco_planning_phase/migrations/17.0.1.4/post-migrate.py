from psycopg2 import sql

from odoo import SUPERUSER_ID, api


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

    env = api.Environment(cr, SUPERUSER_ID, {})
    table = env["qaco.planning.phase"]._table

    for column, sql_type in field_defs.items():
        cr.execute(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = %s AND column_name = %s
            """,
            (table, column),
        )
        exists = cr.fetchone()
        if exists:
            continue

        cr.execute(
            sql.SQL("ALTER TABLE {} ADD COLUMN {} {}").format(
                sql.Identifier(table),
                sql.Identifier(column),
                sql.SQL(sql_type),
            )
        )
