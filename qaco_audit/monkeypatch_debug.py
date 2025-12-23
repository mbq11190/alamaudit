import logging

from odoo import models

_logger = logging.getLogger(__name__)

# Monkeypatch to log more context when order->sql fails (temporary debug aid)
_orig = models.Model._order_field_to_sql


def _order_field_to_sql_debug(self, alias, field_name, sql_direction, sql_nulls, query):
    try:
        return _orig(self, alias, field_name, sql_direction, sql_nulls, query)
    except Exception:
        _logger.exception(
            "DEBUG _order_field_to_sql failure: model=%s field=%s alias=%s direction=%s",
            self._name,
            field_name,
            alias,
            sql_direction,
        )
        raise


models.Model._order_field_to_sql = _order_field_to_sql_debug
