from odoo.tests.common import TransactionCase


class TestPlanningP12View(TransactionCase):
    def setUp(self):
        super().setUp()
        self.view = self.env.ref("qaco_planning_phase.view_planning_p12_strategy_form")

    def test_view_has_buttons_and_safe_attrs(self):
        arch = self.view.arch_db or ""
        # Buttons should be present
        self.assertIn("action_mark_complete", arch)
        self.assertIn("action_manager_review", arch)
        self.assertIn("action_partner_approve", arch)
        # Ensure we replaced risky inline expressions
        self.assertNotIn("state not in", arch)
        self.assertNotIn("not interim_audit_planned", arch)
        self.assertIn("attrs=", arch)

    def test_action_mark_complete_requires_mandatory_fields(self):
        Audit = self.env["qaco.audit"]
        audit = Audit.create({"client_id": self.env.ref("base.res_partner_1").id})
        P12 = self.env["qaco.planning.p12.strategy"]
        p12 = P12.create(
            {
                "audit_id": audit.id,
                "partner_id": self.env.ref("base.res_partner_1").id,
                "audit_approach": "substantive",
                "approach_rationale": "<p>reason</p>",
                "journal_entry_testing_approach": "<p>j</p>",
                "management_override_procedures": "<p>m</p>",
                "fieldwork_start_date": "2025-01-01",
                "fieldwork_end_date": "2025-01-31",
            }
        )
        # _validate_mandatory_fields should still fail because attachments/confirmations are missing
        with self.assertRaises(Exception) as cm:
            p12.action_mark_complete()
        self.assertIn("Cannot progress P-12", str(cm.exception) or "")
