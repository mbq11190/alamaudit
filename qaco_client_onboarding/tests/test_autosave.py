# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestOnboardingAutosave(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Partner = self.env["res.partner"]
        self.Audit = self.env["qaco.audit"]
        self.Onb = self.env["qaco.client.onboarding"]

        self.partner = self.Partner.create({"name": "AutoSaveClient"})
        self.audit = self.Audit.create({"client_id": self.partner.id})
        # Required fields: audit_id, legal_name, principal_business_address, entity_type
        self.onb = self.Onb.create(
            {
                "audit_id": self.audit.id,
                "legal_name": "InitCorp",
                "principal_business_address": "Addr 1",
                "entity_type": "pic",
            }
        )

    def test_get_autosave_status_and_autosave(self):
        # Status should not be locked initially
        status = self.Onb.get_autosave_status([self.onb.id])
        self.assertFalse(status.get("is_locked"))

        # Perform autosave for a whitelisted field
        res = self.Onb.autosave(self.onb.id, {"legal_name": "SavedCorp", "entity_type": "lsc"})
        self.assertEqual(res.get("status"), "saved")
        self.onb.refresh()
        self.assertEqual(self.onb.legal_name, "SavedCorp")
        self.assertEqual(self.onb.entity_type, "lsc")

        # Non-whitelisted fields (e.g., state) should be ignored
        res = self.Onb.autosave(self.onb.id, {"state": "partner_approved", "legal_name": "SavedCorp2"})
        self.assertEqual(res.get("status"), "saved")
        self.onb.refresh()
        # legal_name should update, but state should remain unchanged
        self.assertEqual(self.onb.legal_name, "SavedCorp2")
        self.assertNotEqual(self.onb.state, "partner_approved")

        # When record is partner_approved, autosave returns 'locked'
        self.onb.state = "partner_approved"
        res = self.Onb.autosave(self.onb.id, {"legal_name": "ShouldNotSave"})
        self.assertEqual(res.get("status"), "locked")
        self.onb.refresh()
        self.assertNotEqual(self.onb.legal_name, "ShouldNotSave")
