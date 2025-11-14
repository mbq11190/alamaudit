## QACO Employees

This module manages employee records and includes leave adjustment workflows.

### Changes
- Approval lines are no longer deduplicated when submitting or editing a leave adjustment.
- The unique constraint on `leave_adjustment_approval` has been removed to allow multiple approval lines for the same user.
