from odoo.tests.common import TransactionCase


class TestIndependenceConflict(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Onboarding = self.env["qaco.client.onboarding"]
        self.Conflict = self.env["qaco.onboarding.conflict"]
        self.Threat = self.env["qaco.onboarding.independence.threat"]
        firm = self.env["audit.firm.name"].create({"name": "TestFirm", "code": "TF"})
        client = self.env["res.partner"].create({"name": "ClientX"})
        audit = self.env["qaco.audit"].create(
            {"name": "A1", "client_id": client.id, "firm_name": firm.id}
        )
        self.onboarding = self.Onboarding.create(
            {
                "audit_id": audit.id,
                "legal_name": "ClientX",
                "principal_business_address": "Addr",
                "business_registration_number": "B123",
            }
        )

    def test_conflict_and_threat_relations(self):
        # Create a conflict tied to the onboarding
        conf = self.Conflict.create({"onboarding_id": self.onboarding.id, "conflict_type": "related"})
        # Create a threat attached to the conflict (and to onboarding)
        t_conflict = self.Threat.create({
            "conflict_id": conf.id,
            "onboarding_id": self.onboarding.id,
            "description": "Conflict-linked threat",
        })
        # Create a threat attached directly to onboarding
        t_onboard = self.Threat.create({"onboarding_id": self.onboarding.id, "description": "Onboarding-only threat"})

        # Assertions
        self.assertIn(t_conflict.id, conf.threat_ids.ids, "Threat created with conflict_id must appear on conflict.threat_ids")
        self.assertEqual(t_conflict.conflict_id.id, conf.id, "Threat.conflict_id must point to created conflict")
        self.assertIn(t_conflict.id, self.onboarding.independence_threat_ids.ids, "Conflict-linked threat with onboarding_id should appear on onboarding.independence_threat_ids")
        self.assertIn(t_onboard.id, self.onboarding.independence_threat_ids.ids, "Onboarding-only threat should appear on onboarding.independence_threat_ids")
        self.assertFalse(t_onboard.conflict_id, "Onboarding-only threat should not have conflict_id set by default")
