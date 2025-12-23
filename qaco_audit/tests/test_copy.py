from odoo.tests import common


class AuditCopyPartnerUnsetTest(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_user = self.env["res.users"].create(
            {
                "name": "Partner",
                "login": "partner@example.com",
                "groups_id": [
                    (6, 0, [self.env.ref("qaco_audit.group_audit_partner").id])
                ],
            }
        )
        self.partner_employee = self.env["hr.employee"].create(
            {
                "name": "Partner Employee",
                "user_id": self.partner_user.id,
            }
        )
        self.client = self.env["res.partner"].create({"name": "Client"})

    def test_copy_unsets_audit_partner(self):
        audit = (
            self.env["qaco.audit"]
            .with_user(self.partner_user)
            .create(
                {
                    "client_id": self.client.id,
                    "qaco_audit_partner": self.partner_employee.id,
                }
            )
        )
        duplicate = audit.with_user(self.partner_user).copy()
        self.assertFalse(duplicate.qaco_audit_partner)
