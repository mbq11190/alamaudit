from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests import common


class LeaveAllowancePermissionTest(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.user = self.env["res.users"].create(
            {
                "name": "User",
                "login": "user@example.com",
                "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
            }
        )
        self.employee = self.env["hr.employee"].create(
            {
                "name": "Employee",
                "user_id": self.user.id,
            }
        )
        self.allowance = self.env["leave.allowance"].create(
            {
                "employee_id": self.employee.id,
                "time_off_type": "ca_130",
                "from_date": fields.Date.today(),
                "to_date": fields.Date.today(),
                "allowed_leaves": 10.0,
                "state": "approved",
            }
        )

    def test_button_not_visible_for_unauthorized_users(self):
        view = (
            self.env["leave.allowance"]
            .with_user(self.user)
            .fields_view_get(
                view_id=self.env.ref("qaco_employees.view_leave_allowance_form").id,
                view_type="form",
            )
        )
        self.assertNotIn("action_reset_to_draft", view["arch"])

    def test_unauthorized_user_cannot_reset(self):
        with self.assertRaises(AccessError):
            self.allowance.with_user(self.user).action_reset_to_draft()
