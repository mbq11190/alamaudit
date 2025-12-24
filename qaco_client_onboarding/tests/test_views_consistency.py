# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestClientOnboardingView(TransactionCase):
    def test_onboarding_view_and_fields_present(self):
        """Ensure the Client Onboarding form view and required fields are present
        and that the audit action returns a valid form action for an onboarding record.
        This prevents regressions where views reference non-existent fields or actions
        that fail at runtime.
        """
        Onboarding = self.env["qaco.client.onboarding"]
        Audit = self.env["qaco.audit"]
        Partner = self.env["res.partner"]

        # Fields that the view depends on
        required_fields = ["engagement_status", "audit_id", "progress_percentage"]
        for f in required_fields:
            self.assertIn(
                f,
                Onboarding._fields,
                msg=f"Expected field '{f}' to be defined on qaco.client.onboarding",
            )

        # The form view record should exist
        view = self.env.ref(
            "qaco_client_onboarding.view_client_onboarding_form", raise_if_not_found=False
        )
        self.assertTrue(view, "Client Onboarding form view is missing from module data")

        # Create minimal records and ensure the audit helper opens the onboarding form
        partner = Partner.create({"name": "ViewTestClient"})
        audit = Audit.create({"client_id": partner.id})
        # The action should return the onboarding record in form mode
        action = audit.action_open_client_onboarding()
        self.assertEqual(action.get("res_model"), "qaco.client.onboarding")
        self.assertIn("view_mode", action)
        self.assertEqual(action.get("view_mode"), "form")
        # Ensure a res_id was returned and an onboarding record exists
        self.assertTrue(action.get("res_id"))
        created_onb = Onboarding.browse(action.get("res_id"))
        self.assertTrue(created_onb.exists())
        self.assertEqual(created_onb.audit_id.id, audit.id)