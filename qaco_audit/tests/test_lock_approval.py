from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestLockApproval(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Audit = self.env["qaco.audit"]
        self.Lock = self.env["qaco.audit.lock.approval"]
        self.manager = self.env.ref("qaco_audit.group_audit_manager")

    def test_request_and_approve_unlock(self):
        audit = self.Audit.create(
            {
                "client_id": self.env.ref("base.res_partner_1").id,
                "engagement_status": "locked",
            }
        )
        # request as normal user
        approval = self.Lock.create(
            {"audit_id": audit.id, "reason": "Emergency unlock required for file error"}
        )
        self.assertEqual(approval.status, "pending")
        # approve as manager user
        manager_user = self.env["res.users"].search(
            [("groups_id", "in", self.manager.id)], limit=1
        )
        self.env.user = manager_user
        approval.action_approve()
        approval.refresh()
        self.assertEqual(approval.status, "approved")
        audit.refresh()
        self.assertEqual(audit.engagement_status, "partner_approved")

    def test_non_manager_cannot_approve(self):
        audit = self.Audit.create(
            {
                "client_id": self.env.ref("base.res_partner_1").id,
                "engagement_status": "locked",
            }
        )
        approval = self.Lock.create({"audit_id": audit.id, "reason": "Test unlock"})
        # current env user is not manager by default in tests -> Approve should raise
        with self.assertRaises(AccessError):
            approval.action_approve()
