# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestRelationalComodelsRegistered(TransactionCase):
    def test_relational_comodels_resolve(self):
        """Ensure all relational fields reference registered comodels.
        This prevents _unknown model situations that lead to ValueError: Invalid field 'id' on model '_unknown'.
        """
        env = self.env
        missing = []
        # Check models belonging to qaco modules
        for model_name in sorted(env.registry.models):
            # Limit scope to audit & qaco modules to keep test focused & fast
            if not (model_name.startswith("qaco") or model_name.startswith("audit")):
                continue
            model = env[model_name]
            for fname, field in model._fields.items():
                if field.type in ("one2many", "many2one", "many2many"):
                    comodel = getattr(field, "comodel_name", None)
                    if comodel:
                        if comodel not in env.registry.models:
                            missing.append((model_name, fname, comodel))
        self.assertFalse(missing, msg=("Found relational fields referencing missing comodels: %s" % missing))
