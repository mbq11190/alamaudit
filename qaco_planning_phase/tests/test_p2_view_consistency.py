# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestPlanningP2View(TransactionCase):
    def test_p2_view_and_fields_present(self):
        """Ensure the P-2 (Entity) form view and required fields are present."""
        P2 = self.env["qaco.planning.p2.entity"]
        Audit = self.env["qaco.audit"]
        Partner = self.env["res.partner"]

        required_fields = ["legal_name", "entity_type", "registration_ntn", "principal_place_of_business"]
        for f in required_fields:
            self.assertIn(
                f,
                P2._fields,
                msg=f"Expected field '{f}' to be defined on qaco.planning.p2.entity",
            )

        view = self.env.ref(
            "qaco_planning_phase.view_planning_p2_entity_form", raise_if_not_found=False
        )
        self.assertTrue(view, "P-2 form view is missing from module data")

        partner = Partner.create({"name": "P2ViewTestClient"})
        audit = Audit.create({"client_id": partner.id})
        p2 = P2.create({"audit_id": audit.id})
        self.assertTrue(p2.exists())
        # Defaults / stored counts
        self.assertEqual(p2.total_risks_identified, 0)
        self.assertFalse(p2.doc_organogram_uploaded)
