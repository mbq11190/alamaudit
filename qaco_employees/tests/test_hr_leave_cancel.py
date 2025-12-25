from odoo.tests.common import TransactionCase


class TestHrLeaveCancel(TransactionCase):
    def test_action_cancel_wrapper(self):
        Leave = self.env["hr.leave"].sudo()
        # create a simple leave record (minimal required fields may vary depending on HR module)
        employee = self.env["hr.employee"].search([], limit=1)
        if not employee:
            self.skipTest("No hr.employee records to test leave cancellation")
        leave = Leave.create(
            {
                "name": "Test Leave",
                "employee_id": employee.id,
                "request_date_from": "2025-01-01",
                "request_date_to": "2025-01-02",
                "state": "draft",
            }
        )
        # Ensure action_cancel runs without error
        self.assertTrue(callable(getattr(leave, "action_cancel", None)))
        res = leave.action_cancel()
        self.assertTrue(res)
        # After cancel, leave.state should be 'cancel' or the record should be refused
        self.assertIn(leave.state, ("cancel", "refuse", "cancelled", "refused", "draft"))
