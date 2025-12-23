from odoo import exceptions
from odoo.tests.common import TransactionCase


class TestIndependenceEthics(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Onboarding = self.env["qaco.client.onboarding"]
        self.Decl = self.env["qaco.onboarding.independence.declaration"]
        self.Threat = self.env["qaco.onboarding.independence.threat"]
        # baseline objects
        firm = self.env["audit.firm.name"].create({"name": "TestFirm", "code": "TF"})
        client = self.env["res.partner"].create({"name": "IndClient"})
        audit = self.env["qaco.audit"].create(
            {"name": "A1", "client_id": client.id, "firm_name": firm.id}
        )
        self.onboarding = self.Onboarding.create(
            {
                "audit_id": audit.id,
                "legal_name": "IndClient",
                "principal_business_address": "Addr",
                "business_registration_number": "I123",
            }
        )

    def test_missing_declarations_block_approval(self):
        # Create a pending declaration
        self.Decl.create(
            {
                "onboarding_id": self.onboarding.id,
                "user_id": self.env.uid,
                "role": "Partner",
                "status": "pending",
            }
        )
        self.onboarding.action_submit_review()
        with self.assertRaises(exceptions.ValidationError):
            self.onboarding.action_partner_approve()

    def test_unresolved_threat_blocks_approval(self):
        # Add an approved declaration so declarations aren't the blocker
        self.Decl.create(
            {
                "onboarding_id": self.onboarding.id,
                "user_id": self.env.uid,
                "role": "Partner",
                "status": "approved",
            }
        )
        # Add a high likelihood/impact threat unresolved
        self.Threat.create(
            {
                "onboarding_id": self.onboarding.id,
                "category": "self_review",
                "likelihood": "high",
                "impact": "high",
                "resolved": False,
            }
        )
        self.onboarding.action_submit_review()
        with self.assertRaises(exceptions.ValidationError):
            self.onboarding.action_partner_approve()

    def test_resolved_threat_allows_approval(self):
        # Approve declarations and resolve threats
        self.Decl.create(
            {
                "onboarding_id": self.onboarding.id,
                "user_id": self.env.uid,
                "role": "Partner",
                "status": "approved",
            }
        )
        t = self.Threat.create(
            {
                "onboarding_id": self.onboarding.id,
                "category": "self_review",
                "likelihood": "high",
                "impact": "high",
                "resolved": False,
            }
        )
        # Resolve threat
        t.resolved = True
        # ensure checklist populated and completed
        self.onboarding._populate_regulator_checklist()
        for line in self.onboarding.regulator_checklist_line_ids:
            if line.mandatory:
                line.completed = True
        # set partner
        self.onboarding.engagement_partner_id = self.env["res.users"].browse(
            self.env.uid
        )
        self.onboarding.action_submit_review()
        self.onboarding.action_partner_approve()
        self.assertEqual(self.onboarding.state, "partner_approved")
