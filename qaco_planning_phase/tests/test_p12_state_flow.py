from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
import base64


class TestPlanningP12StateFlow(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Audit = self.env["qaco.audit"]
        self.P12 = self.env["qaco.planning.p12.strategy"]
        self.P11 = self.env["qaco.planning.p11.group.audit"]
        self.Att = self.env["ir.attachment"]

    def _create_audit(self):
        return self.Audit.create({"client_id": self.env.ref("base.res_partner_1").id})

    def test_p12_full_state_flow_and_p13_creation(self):
        audit = self._create_audit()
        # create a required attachment
        datas = base64.b64encode(b"dummy").decode()
        att = self.Att.create({"name": "memo.pdf", "type": "binary", "datas": datas})

        p12 = self.P12.create(
            {
                "audit_id": audit.id,
                "partner_id": self.env.ref("base.res_partner_1").id,
                "audit_approach": "substantive",
                "approach_rationale": "<p>reason</p>",
                "journal_entry_testing_approach": "<p>j</p>",
                "management_override_procedures": "<p>m</p>",
                "fieldwork_start_date": "2025-01-01",
                "fieldwork_end_date": "2025-01-31",
                "audit_strategy_memo_attachments": [(6, 0, [att.id])],
                "all_risks_addressed": True,
                "programs_finalized_confirmed": True,
                "strategy_approved_before_execution": True,
                "programs_finalized": True,
            }
        )

        # Mark complete -> review
        p12.action_mark_complete()
        self.assertEqual(p12.state, "review")
        self.assertTrue(p12.prepared_by)
        self.assertTrue(p12.prepared_on)

        # Send back from review to draft
        p12.action_send_back()
        self.assertEqual(p12.state, "draft")

        # Mark complete again and proceed through manager and partner flows
        p12.action_mark_complete()
        p12.review_notes = "Looks good"
        p12.action_manager_review()
        self.assertEqual(p12.state, "partner")

        # Partner approves -> locks and creates/updates P-13
        p12.partner_comments = "Approved"
        p12.action_partner_approve()
        self.assertEqual(p12.state, "locked")
        self.assertTrue(p12.partner_approved)
        # P-13 should exist for this audit
        p13 = self.env["qaco.planning.p13.approval"].search([("audit_id", "=", audit.id)], limit=1)
        self.assertTrue(p13)
        self.assertIn(p13.state, ("in_progress", "not_started", "completed", "reviewed", "approved"))

    def test_partner_unlock_requires_partner_group(self):
        audit = self._create_audit()
        att = self.Att.create({"name": "memo2.pdf", "type": "binary", "datas": base64.b64encode(b"d").decode()})
        p12 = self.P12.create(
            {
                "audit_id": audit.id,
                "partner_id": self.env.ref("base.res_partner_1").id,
                "audit_approach": "substantive",
                "approach_rationale": "<p>r</p>",
                "journal_entry_testing_approach": "<p>j</p>",
                "management_override_procedures": "<p>m</p>",
                "fieldwork_start_date": "2025-01-01",
                "fieldwork_end_date": "2025-01-31",
                "audit_strategy_memo_attachments": [(6, 0, [att.id])],
                "all_risks_addressed": True,
                "programs_finalized_confirmed": True,
                "strategy_approved_before_execution": True,
                "programs_finalized": True,
            }
        )
        # Move to locked state
        p12.action_mark_complete()
        p12.review_notes = "ok"
        p12.action_manager_review()
        p12.partner_comments = "ok"
        p12.action_partner_approve()
        self.assertEqual(p12.state, "locked")

        # Non-partner user should not be allowed to unlock
        with self.assertRaises(UserError):
            p12.action_partner_unlock()

        # Create a partner user and call unlock as that user
        partner_group = self.env.ref("qaco_audit.group_audit_partner")
        partner_user = self.env["res.users"].create(
            {"name": "Test Partner", "login": "test_partner", "groups_id": [(6, 0, [partner_group.id])]}
        )
        p12.with_user(partner_user).action_partner_unlock()
        self.assertEqual(p12.state, "partner")

    def test_p11_mark_complete_requires_prerequisites(self):
        audit = self._create_audit()
        p11 = self.P11.create({"audit_id": audit.id})
        with self.assertRaises(UserError):
            p11.action_mark_complete()
