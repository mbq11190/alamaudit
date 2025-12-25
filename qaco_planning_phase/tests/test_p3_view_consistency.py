# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestPlanningP3View(TransactionCase):
    def test_p3_view_and_fields_present(self):
        """Ensure the P-3 form view exists and key fields used by the view are defined on the model."""
        P3 = self.env["qaco.planning.p3.controls"]
        Audit = self.env["qaco.audit"]
        Partner = self.env["res.partner"]

        required_fields = ["flowchart_count", "walkthrough_doc_count", "process_flowchart_ids", "walkthrough_doc_ids"]
        for f in required_fields:
            self.assertIn(
                f,
                P3._fields,
                msg=f"Expected field '{f}' to be defined on qaco.planning.p3.controls",
            )

        view = self.env.ref(
            "qaco_planning_phase.view_planning_p3_controls_form", raise_if_not_found=False
        )
        self.assertTrue(view, "P-3 form view is missing from module data")

        # Create minimal records and ensure a P-3 can be created and fields are accessible
        partner = Partner.create({"name": "P3ViewTestClient"})
        audit = Audit.create({"client_id": partner.id})
        p3 = P3.create({"audit_id": audit.id})
        self.assertTrue(p3.exists())
        # Read stored counts default to zero
        self.assertEqual(p3.flowchart_count, 0)
        self.assertEqual(p3.walkthrough_doc_count, 0)
