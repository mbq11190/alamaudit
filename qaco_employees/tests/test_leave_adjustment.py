from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import common


class LeaveAdjustmentSubmitTest(common.TransactionCase):
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

    def test_duplicate_adjustment_date_validation(self):
        Adjustment = self.env["leave.adjustment"]
        date = fields.Date.today()
        first = Adjustment.create(
            {
                "employee_id": self.employee.id,
                "adjustment_type": "positive",
                "adjustment": 1.0,
                "adjustment_date": date,
                "reason": "First",
            }
        )
        first.action_submit()

        second = Adjustment.create(
            {
                "employee_id": self.employee.id,
                "adjustment_type": "positive",
                "adjustment": 1.0,
                "adjustment_date": date,
                "reason": "Second",
            }
        )
        with self.assertRaises(ValidationError):
            second.action_submit()

    def test_past_adjustment_date_validation(self):
        Adjustment = self.env["leave.adjustment"]
        past_date = fields.Date.today() - timedelta(days=1)
        adj = Adjustment.create(
            {
                "employee_id": self.employee.id,
                "adjustment_type": "positive",
                "adjustment": 1.0,
                "adjustment_date": past_date,
                "reason": "Past Date",
            }
        )
        with self.assertRaises(ValidationError):
            adj.action_submit()


class LeaveAdjustmentApprovalRightsTest(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.manager_user = self.env["res.users"].create(
            {
                "name": "Manager",
                "login": "manager@example.com",
                "groups_id": [
                    (
                        6,
                        0,
                        [self.env.ref("qaco_employees.group_qaco_employee_manager").id],
                    )
                ],
            }
        )
        self.manager_employee = self.env["hr.employee"].create(
            {
                "name": "Manager Emp",
                "user_id": self.manager_user.id,
            }
        )
        self.employee_user = self.env["res.users"].create(
            {
                "name": "Employee",
                "login": "emp@example.com",
                "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
            }
        )
        self.employee = self.env["hr.employee"].create(
            {
                "name": "Employee",
                "user_id": self.employee_user.id,
                "parent_id": self.manager_employee.id,
            }
        )

        self.partner_user = self.env["res.users"].create(
            {
                "name": "Partner",
                "login": "partner@example.com",
                "groups_id": [
                    (
                        6,
                        0,
                        [self.env.ref("qaco_employees.group_qaco_employee_partner").id],
                    )
                ],
            }
        )
        self.partner_employee = self.env["hr.employee"].create(
            {
                "name": "Partner Emp",
                "user_id": self.partner_user.id,
            }
        )
        self.employee.partner_id = self.partner_employee.id

        self.admin_user = self.env["res.users"].create(
            {
                "name": "Admin",
                "login": "admin@example.com",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref(
                                "qaco_employees.group_qaco_employee_administrator"
                            ).id,
                        ],
                    )
                ],
            }
        )

    def test_manager_can_approve(self):
        Adjustment = self.env["leave.adjustment"].with_user(self.employee_user)
        adj = Adjustment.create(
            {
                "employee_id": self.employee.id,
                "adjustment_type": "positive",
                "adjustment": 1.0,
                "adjustment_date": fields.Date.today(),
                "reason": "Request",
            }
        )
        adj.action_submit()

        adj.with_user(self.manager_user).action_approve()
        self.assertEqual(adj.state, "approved")

    def test_manager_and_partner_approve(self):
        Adjustment = self.env["leave.adjustment"].with_user(self.employee_user)
        adj = Adjustment.create(
            {
                "employee_id": self.employee.id,
                "adjustment_type": "positive",
                "adjustment": 1.0,
                "adjustment_date": fields.Date.today(),
                "reason": "Request",
                "approval_ids": [
                    (0, 0, {"validating_users_id": self.manager_user.id}),
                    (0, 0, {"validating_users_id": self.manager_user.id}),
                    (0, 0, {"validating_users_id": self.partner_user.id}),
                ],
            }
        )
        adj.action_submit()
        self.assertEqual(len(adj.approval_ids), 2)

        adj.with_user(self.manager_user).action_approve()
        adj.with_user(self.partner_user).action_approve()
        self.assertEqual(adj.state, "approved")

    def test_manager_and_partner_same_user(self):
        """action_submit should not create duplicate approvals when manager and
        partner are the same user"""
        # Partner is the same as manager
        self.employee.partner_id = self.manager_employee.id

        Adjustment = self.env["leave.adjustment"].with_user(self.employee_user)
        adj = Adjustment.create(
            {
                "employee_id": self.employee.id,
                "adjustment_type": "positive",
                "adjustment": 1.0,
                "adjustment_date": fields.Date.today(),
                "reason": "Request",
                "approval_ids": [(5, 0, 0)],
            }
        )

        # Remove any default approval lines to simulate a record without them
        adj.approval_ids.unlink()

        adj.action_submit()
        self.assertEqual(len(adj.approval_ids), 1)

    def test_admin_can_approve(self):
        Adjustment = self.env["leave.adjustment"].with_user(self.employee_user)
        adj = Adjustment.create(
            {
                "employee_id": self.employee.id,
                "adjustment_type": "positive",
                "adjustment": 1.0,
                "adjustment_date": fields.Date.today(),
                "reason": "Request",
                "approval_ids": [
                    (0, 0, {"validating_users_id": self.manager_user.id}),
                    (0, 0, {"validating_users_id": self.partner_user.id}),
                ],
            }
        )
        adj.action_submit()
        self.assertEqual(len(adj.approval_ids), 2)

        adj.with_user(self.admin_user).action_approve()

        self.assertEqual(adj.state, "approved")
        self.assertTrue(all(line.is_validation_status for line in adj.approval_ids))

    def test_deduplicate_on_write(self):
        Adjustment = self.env["leave.adjustment"].with_user(self.employee_user)
        adj = Adjustment.create(
            {
                "employee_id": self.employee.id,
                "adjustment_type": "positive",
                "adjustment": 1.0,
                "adjustment_date": fields.Date.today(),
                "reason": "Request",
            }
        )

        # attempt to add duplicate approver line via write
        adj.write(
            {"approval_ids": [(0, 0, {"validating_users_id": self.manager_user.id})]}
        )
        self.assertEqual(len(adj.approval_ids), 2)

    def test_duplicate_approvals_on_create(self):
        """Creating with duplicate approval lines should keep only one"""
        Adjustment = self.env["leave.adjustment"].with_user(self.employee_user)
        adj = Adjustment.create(
            {
                "employee_id": self.employee.id,
                "adjustment_type": "positive",
                "adjustment": 1.0,
                "adjustment_date": fields.Date.today(),
                "reason": "Request",
                "approval_ids": [
                    (0, 0, {"validating_users_id": self.manager_user.id}),
                    (0, 0, {"validating_users_id": self.manager_user.id}),
                ],
            }
        )
        self.assertEqual(len(adj.approval_ids), 1)

    def test_admin_can_create_for_other_employee(self):
        Adjustment = self.env["leave.adjustment"].with_user(self.admin_user)
        adj = Adjustment.create(
            {
                "employee_id": self.employee.id,
                "adjustment_type": "positive",
                "adjustment": 1.0,
                "adjustment_date": fields.Date.today(),
                "reason": "Admin Request",
            }
        )
        adj.action_submit()
        self.assertEqual(adj.state, "submitted")
        self.assertEqual(adj.employee_id, self.employee)

    def test_regular_employee_cannot_create_for_others(self):
        Adjustment = self.env["leave.adjustment"].with_user(self.employee_user)
        with self.assertRaises(UserError):
            Adjustment.create(
                {
                    "employee_id": self.manager_employee.id,
                    "adjustment_type": "positive",
                    "adjustment": 1.0,
                    "adjustment_date": fields.Date.today(),
                    "reason": "Invalid",
                }
            )
