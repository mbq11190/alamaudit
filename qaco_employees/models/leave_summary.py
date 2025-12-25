# File: models/leave_summary.py
import calendar
import logging
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.tools import format_date

_logger = logging.getLogger(__name__)


class LeaveSummary(models.Model):
    _name = "leave.summary"
    _description = "Monthly Leave Summary"
    _order = "event_date desc"
    _rec_name = "sequence"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    employee_id = fields.Many2one("hr.employee", string="Employee", required=True)
    event_date = fields.Date(
        string="Event Date", required=True, default=fields.Date.context_today
    )
    sequence = fields.Char(default="/", readonly=True)

    opening_leaves = fields.Float(string="Opening Leaves")

    leave_adjustment = fields.Float(string="Adjustment", store=True)
    active = fields.Boolean("Active", default=True)
    create_date = fields.Datetime("Created On", readonly=True, index=True)
    write_date = fields.Datetime("Last Updated On", readonly=True)
    closing_leaves = fields.Float(
        string="Closing Leaves", compute="_compute_closing_leaves", store=True
    )
    allowed_leaves = fields.Float(
        string="Allowed Leaves", compute="_compute_allowed_leaves", store=True
    )
    remaining_leaves = fields.Float(
        string="Remaining Leaves", compute="_compute_remaining_leaves", store=True
    )
    approved_leaves = fields.Float(string="Approved Leaves")
    absent_days = fields.Float(
        string="Absences", compute="_compute_absent_days", store=True
    )
    adjustment_ref_id = fields.Many2one("leave.adjustment", string="Adjustment Ref")
    allowance_ref_id = fields.Many2one("leave.allowance", string="Allowance Ref")
    is_monthly_summary = fields.Boolean(string="Is Monthly Summary", default=False)
    _sql_constraints = [
        (
            "unique_employee_event",
            "unique(employee_id, event_date, is_monthly_summary)",
            "Employee already has a summary for this date!",
        ),
        (
            "unique_adjustment_ref",
            "unique(adjustment_ref_id)",
            "Each adjustment can create only one summary!",
        ),
        (
            "unique_allowance_ref",
            "unique(allowance_ref_id)",
            "Each allowance can create only one summary!",
        ),
    ]

    def action_archive(self):
        self.write({"active": False})

    def action_recompute(self):
        """Manual recompute of key fields for HR/Admin.
        - Recomputes opening, allowed, approved (if monthly), absences, closing, remaining
        - Persists values and cascades to future months
        Supports multi-selection (recordset)."""
        for record in self.sudo():
            # Opening may change if previous records changed
            record._set_opening_based_on_previous()
            # Allowed leaves might change due to allowance updates
            record._compute_allowed_leaves()
            # Monthly summaries include approved leave days
            if record.is_monthly_summary:
                record._compute_approved_leaves()
            # Always recompute absences
            record._compute_absent_days()
            # Totals
            record._compute_closing_leaves()
            record._compute_remaining_leaves()

            # Persist stored values with skip_cascade to avoid duplicate cascading
            record.with_context(skip_cascade=True).write(
                {
                    "opening_leaves": record.opening_leaves,
                    "closing_leaves": record.closing_leaves,
                    "remaining_leaves": record.remaining_leaves,
                }
            )

            # Optional log for traceability
            try:
                record.message_post(body="Leave summary recomputed by user")
            except Exception:
                # In case chatter is not available in some contexts
                _logger.info("Leave summary %s recomputed", record.id)

        # Propagate recalculations to future months for impacted employees (once at the end)
        self._cascade_update_future_months()
        return True

    @api.depends("employee_id", "event_date")
    def _compute_approved_leaves(self):
        for record in self:
            if not record.is_monthly_summary:
                record.approved_leaves = 0.0
                continue

            month_start = record.event_date.replace(day=1)
            month_end = (month_start + relativedelta(months=1)) - timedelta(days=1)

            # Workdays in the month (Mon–Fri)
            workdays = set(
                month_start + timedelta(days=i)
                for i in range((month_end - month_start).days + 1)
                if (month_start + timedelta(days=i)).weekday() < 5
            )
            # Exclude approved public holidays from workdays
            holiday_dates = {
                h.date
                for h in self.env["hr.public.holiday"].search(
                    [
                        ("date", ">=", month_start),
                        ("date", "<=", month_end),
                        ("state", "=", "approved"),
                    ]
                )
            }
            workdays = {d for d in workdays if d not in holiday_dates}

            # Expand already counted days from non-monthly leave summaries
            existing_events = (
                self.env["leave.summary"]
                .sudo()
                .search(
                    [
                        ("employee_id", "=", record.employee_id.id),
                        ("is_monthly_summary", "=", False),
                        ("event_date", ">=", month_start),
                        ("event_date", "<=", month_end),
                        ("approved_leaves", ">", 0),
                    ]
                )
            )
            already_counted_dates = set()
            for ev in existing_events:
                # Expand to working dates starting from the event date, skipping weekends/holidays
                remaining = int(ev.approved_leaves)
                cur = ev.event_date
                while remaining > 0 and cur <= month_end:
                    if cur in workdays:
                        already_counted_dates.add(cur)
                        remaining -= 1
                    cur += timedelta(days=1)

            leaves = self.env["hr.leave"].search(
                [
                    ("employee_id", "=", record.employee_id.id),
                    ("state", "=", "validate"),
                    ("request_date_from", "<=", month_end),
                    ("request_date_to", ">=", month_start),
                ]
            )

            total_days = 0.0
            for leave in leaves:
                start = max(leave.request_date_from, month_start)
                end = min(leave.request_date_to, month_end)
                leave_dates = set(
                    start + timedelta(days=i) for i in range((end - start).days + 1)
                )

                # Count only working days not already counted by event-level summaries
                to_count = (leave_dates & workdays) - already_counted_dates
                total_days += len(to_count)

            record.approved_leaves = total_days

    @api.depends("employee_id", "event_date")
    def _compute_absent_days(self):
        Attendance = self.env["hr.attendance"]
        Leave = self.env["hr.leave"]

        for record in self:
            # ⛔ Skip computing absences unless it's a monthly summary
            if not record.is_monthly_summary:
                record.absent_days = 0.0
                continue

            if not record.employee_id or not record.event_date:
                record.absent_days = 0.0
                continue

            start_date = record.event_date.replace(day=1)
            last_day = calendar.monthrange(start_date.year, start_date.month)[1]
            end_date = start_date.replace(day=last_day)

            leave_days = set()
            approved_leaves = Leave.search(
                [
                    ("employee_id", "=", record.employee_id.id),
                    ("state", "=", "validate"),
                    ("request_date_from", "<=", end_date),
                    ("request_date_to", ">=", start_date),
                ]
            )
            for leave in approved_leaves:
                current = max(start_date, leave.request_date_from)
                while current <= min(end_date, leave.request_date_to):
                    leave_days.add(current)
                    current += timedelta(days=1)

            attendance_days = set(
                att.check_in.date()
                for att in Attendance.search(
                    [
                        ("employee_id", "=", record.employee_id.id),
                        ("check_in", ">=", start_date),
                        ("check_in", "<", end_date + timedelta(days=1)),
                    ]
                )
            )

            holiday_dates = {
                h.date
                for h in self.env["hr.public.holiday"].search(
                    [
                        ("date", ">=", start_date),
                        ("date", "<=", end_date),
                        ("state", "=", "approved"),
                    ]
                )
            }

            working_days = {
                (start_date + timedelta(days=i))
                for i in range((end_date - start_date).days + 1)
                if (start_date + timedelta(days=i)).weekday() < 5
                and (start_date + timedelta(days=i)) not in holiday_dates
            }

            # If there is a check-in for a working day, never count it as absent
            # Count exact number of absent working days (no artificial multiplier)
            actual_absents = working_days - attendance_days - leave_days
            record.absent_days = float(len(actual_absents))

    def _compute_closing_leaves(self):
        for record in self:
            opening = record.opening_leaves or 0.0
            approved = record.approved_leaves or 0.0
            absent = record.absent_days or 0.0
            adjustment = record.leave_adjustment or 0.0

            # Closing leaves should reflect only utilized days and adjustments
            record.closing_leaves = opening + adjustment + approved + absent

    @api.depends("event_date")
    def _compute_allowed_leaves(self):
        for record in self:
            if not record.event_date:
                record.allowed_leaves = 0.0
                continue

            allowance_records = self.env["leave.allowance"].search(
                [
                    ("employee_id", "=", record.employee_id.id),
                    ("state", "=", "approved"),
                ]
            )
            allowance_days = allowance_records.mapped("allowed_leaves")
            record.allowed_leaves = sum(allowance_days) if allowance_days else 0.0

    def _compute_remaining_leaves(self):
        for record in self:
            allowed = record.allowed_leaves or 0.0
            closing = record.closing_leaves or 0.0
            record.remaining_leaves = allowed - closing

    @api.model
    def create_monthly_summaries(self):
        today = fields.Date.context_today(self)
        last_month = today.replace(day=1) - relativedelta(months=1)
        month_start = last_month
        month_end = (month_start + relativedelta(months=1)) - timedelta(days=1)

        employees = self.env["hr.employee"].search([])

        for emp in employees:
            # Check if summary for this employee/month already exists
            existing = (
                self.env["leave.summary"]
                .sudo()
                .search(
                    [
                        ("employee_id", "=", emp.id),
                        ("is_monthly_summary", "=", True),
                        ("event_date", ">=", month_start),
                        ("event_date", "<=", month_end),
                    ],
                    limit=1,
                )
            )

            if existing:
                continue

            # Calculate workdays (Mon–Fri)
            holiday_dates = {
                h.date
                for h in self.env["hr.public.holiday"].search(
                    [
                        ("date", ">=", month_start),
                        ("date", "<=", month_end),
                        ("state", "=", "approved"),
                    ]
                )
            }

            workdays = set(
                month_start + timedelta(days=i)
                for i in range((month_end - month_start).days + 1)
                if (month_start + timedelta(days=i)).weekday() < 5
                and (month_start + timedelta(days=i)) not in holiday_dates
            )

            # Attended days (inclusive of the last day)
            attended_days = set(
                att.check_in.date()
                for att in self.env["hr.attendance"].search(
                    [
                        ("employee_id", "=", emp.id),
                        ("check_in", ">=", month_start),
                        ("check_in", "<", month_end + timedelta(days=1)),
                    ]
                )
            )

            # Approved leave days
            leave_days = set()
            approved_leaves = self.env["hr.leave"].search(
                [
                    ("employee_id", "=", emp.id),
                    ("state", "=", "validate"),
                    ("request_date_from", "<=", month_end),
                    ("request_date_to", ">=", month_start),
                ]
            )
            for leave in approved_leaves:
                start = max(leave.request_date_from, month_start)
                end = min(leave.request_date_to, month_end)
                leave_days |= set(
                    start + timedelta(days=i) for i in range((end - start).days + 1)
                )

            # Calculate absents
            absent_days = workdays - attended_days - leave_days

            if absent_days:
                self.env["leave.summary"].sudo().create(
                    {
                        "employee_id": emp.id,
                        "event_date": month_end,
                        "absent_days": len(absent_days),
                        "is_monthly_summary": True,
                    }
                )

    def _cascade_update_future_months(self):
        """
        Cascade updates to future leave summaries for the same employee.
        Optimized to batch process updates and prevent infinite recursion.
        """
        for record in self:
            if not record.event_date or not record.employee_id:
                continue

            # Fetch all future summaries at once
            future_summaries = self.sudo().search(
                [
                    ("employee_id", "=", record.employee_id.id),
                    ("event_date", ">", record.event_date),
                ],
                order="event_date",
            )

            if not future_summaries:
                continue

            # Process in batches to avoid long-running transactions
            batch_size = 50  # Process 50 records at a time
            previous = record

            for i in range(0, len(future_summaries), batch_size):
                batch = future_summaries[i : i + batch_size]

                for summary in batch:
                    summary.opening_leaves = previous.closing_leaves
                    if hasattr(summary, "_compute_allowed_leaves"):
                        summary._compute_allowed_leaves()

                    if summary.is_monthly_summary:
                        summary._compute_approved_leaves()

                    summary._compute_absent_days()
                    summary._compute_closing_leaves()
                    summary._compute_remaining_leaves()

                    # ✅ Use skip_cascade context to prevent infinite recursion
                    summary.with_context(skip_cascade=True).write(
                        {
                            "opening_leaves": summary.opening_leaves,
                            "closing_leaves": summary.closing_leaves,
                            "remaining_leaves": summary.remaining_leaves,
                        }
                    )

                    previous = summary

                # Commit after each batch (implicit via ORM)
                self.env.cr.commit()

    def write(self, vals):
        result = super().write(vals)

        for record in self:
            if (
                not record.is_monthly_summary
                and record.approved_leaves == 0
                and not record.absent_days
                and not vals.get("skip_cascade")
            ):
                # Clean-up action could be added here if desired
                pass

        if not self.env.context.get("skip_cascade"):
            self._cascade_update_future_months()

        return result

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("sequence", "/") == "/":
                vals["sequence"] = (
                    self.env["ir.sequence"].next_by_code("leave.summary.seq") or "/"
                )

        records = super().create(vals_list)
        for record, vals in zip(records, vals_list):
            employee_id = vals.get("employee_id")
            event_date = fields.Date.to_date(vals.get("event_date"))

            record_sudo = record.sudo()

            # 🔁 Step 1: Set initial values
            record_sudo._set_opening_based_on_previous()
            record_sudo._compute_allowed_leaves()
            if record_sudo.is_monthly_summary:
                record_sudo._compute_approved_leaves()
            record_sudo._compute_absent_days()
            record_sudo._compute_closing_leaves()
            record_sudo._compute_remaining_leaves()

            # ✅ Save the updated values with skip_cascade to prevent duplicate cascading
            record_sudo.with_context(skip_cascade=True).write(
                {
                    "opening_leaves": record_sudo.opening_leaves,
                    "closing_leaves": record_sudo.closing_leaves,
                    "remaining_leaves": record_sudo.remaining_leaves,
                }
            )

            # 🔁 Step 2: Cascade to future summaries
            future_summaries = self.sudo().search(
                [
                    ("employee_id", "=", employee_id),
                    ("event_date", ">", event_date),
                ],
                order="event_date",
            )

            previous = record_sudo
            for summary in future_summaries:
                summary.opening_leaves = previous.closing_leaves
                summary._compute_allowed_leaves()
                if summary.is_monthly_summary:
                    summary._compute_approved_leaves()
                summary._compute_absent_days()
                summary._compute_closing_leaves()
                summary._compute_remaining_leaves()
                # ✅ Use skip_cascade to prevent recursive cascading
                summary.with_context(skip_cascade=True).write(
                    {
                        "opening_leaves": summary.opening_leaves,
                        "closing_leaves": summary.closing_leaves,
                        "remaining_leaves": summary.remaining_leaves,
                    }
                )
                previous = summary

        return records

    def unlink(self):
        affected_employees = {}
        for record in self:
            if record.employee_id and record.event_date:
                affected_employees.setdefault(record.employee_id.id, []).append(
                    record.event_date
                )

        res = super().unlink()

        for emp_id, event_dates in affected_employees.items():
            min_date = min(event_dates)
            future_summaries = (
                self.env["leave.summary"]
                .sudo()
                .search(
                    [("employee_id", "=", emp_id), ("event_date", ">", min_date)],
                    order="event_date",
                )
            )

            previous = (
                self.env["leave.summary"]
                .sudo()
                .search(
                    [("employee_id", "=", emp_id), ("event_date", "<", min_date)],
                    order="event_date desc",
                    limit=1,
                )
            )

            for summary in future_summaries:
                summary.opening_leaves = previous.closing_leaves if previous else 0.0
                summary._compute_allowed_leaves()
                if summary.is_monthly_summary:
                    summary._compute_approved_leaves()
                summary._compute_absent_days()
                summary._compute_closing_leaves()
                summary._compute_remaining_leaves()
                previous = summary

        return res

    def _set_opening_based_on_previous(self):
        for record in self:
            previous = self.sudo().search(
                [
                    ("employee_id", "=", record.employee_id.id),
                    "|",
                    ("event_date", "<", record.event_date),
                    "&",
                    ("event_date", "=", record.event_date),
                    ("id", "<", record.id),
                ],
                order="event_date desc, id desc",
                limit=1,
            )

            record.opening_leaves = previous.closing_leaves if previous else 0.0

    @api.model
    def _send_monthly_leave_summary_emails(self):
        today = fields.Date.today()
        last_month = today.replace(day=1) - relativedelta(months=1)
        month_name = last_month.strftime("%B %Y")
        month_start = last_month
        month_end = last_month.replace(
            day=calendar.monthrange(last_month.year, last_month.month)[1]
        )

        # Employees with any summary last month
        last_month_summaries = (
            self.env["leave.summary"]
            .sudo()
            .search(
                [
                    ("event_date", ">=", month_start),
                    ("event_date", "<=", month_end),
                ]
            )
        )
        employees = last_month_summaries.mapped("employee_id")

        mail_values = []
        Mail = self.env["mail.mail"]

        for employee in employees:
            user = employee.user_id
            if not user or not user.email or not user.active:
                continue

            # Fetch all leave summaries
            summaries = (
                self.env["leave.summary"]
                .sudo()
                .search(
                    [
                        ("employee_id", "=", employee.id),
                    ],
                    order="event_date asc, id asc",
                )
            )

            if not summaries:
                continue

            latest = summaries[-1]
            remaining_leaves = f"{latest.remaining_leaves:.1f}" if latest else "N/A"

            # Build colorful table
            table_rows = ""
            for i, rec in enumerate(reversed(summaries)):
                row_color = "#e8f0fe" if i % 2 == 0 else "#ffffff"
                reason = rec.adjustment_ref_id.reason if rec.adjustment_ref_id else "-"
                table_rows += f"""
                    <tr style="background-color: {row_color}; text-align: center;">
                        <td>{format_date(self.env, rec.event_date)}</td>
                        <td>{rec.allowed_leaves:.1f}</td>
                        <td>{rec.approved_leaves:.1f}</td>
                        <td>{rec.absent_days:.1f}</td>
                        <td>{rec.leave_adjustment:.1f}</td>
                        <td>{rec.closing_leaves:.1f}</td>
                        <td>{rec.remaining_leaves:.1f}</td>
                        <td>{reason}</td>
                    </tr>
                """

            html_body = f"""
            <p>Dear {employee.name},</p>
            <p>Your current <strong>Remaining Leaves</strong> as of today: <strong>{remaining_leaves}</strong></p>
            <p>Below is your complete leave summary:</p>

            <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; font-size: 13px;">
                <thead>
                    <tr style="background-color: #4285f4; color: white; text-align: center;">
                        <th>Date</th>
                        <th>Allowed</th>
                        <th>Approved</th>
                        <th>Absences</th>
                        <th>Adjustment</th>
                        <th>Closing</th>
                        <th>Remaining</th>
                        <th>Reason</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>

            <p style="margin-top: 20px;">If you notice any discrepancies, please contact HR.</p>
            <p>Regards,<br/>HR Department</p>
            """

            mail_values.append(
                {
                    "subject": f"Your Leave Summary – {month_name}",
                    "email_to": user.email,
                    "body_html": html_body,
                }
            )

        if mail_values:
            Mail.create(mail_values)


class HrLeave(models.Model):
    _inherit = "hr.leave"
    _description = "HR Leave extensions: create leave summary events"

    def create_leave_summary_event(self):
        today = fields.Date.context_today(self)

        for leave in self:
            if leave.state != "validate":
                _logger.debug("⛔ Skipping non-validated leave: %s", leave.name)
                continue

            employee = leave.employee_id
            leave_start = leave.request_date_from
            leave_end = leave.request_date_to

            if not leave_start or not leave_end:
                _logger.warning(
                    "❗ Leave missing dates: %s (From=%s To=%s)",
                    leave.name,
                    leave_start,
                    leave_end,
                )
                continue

            if leave_end < (today - relativedelta(months=3)):
                _logger.debug("⏳ Skipping old leave: %s", leave.name)
                continue

            # Compute working leave days (Mon-Fri) excluding public holidays
            holiday_dates = {
                h.date
                for h in self.env["hr.public.holiday"].search(
                    [
                        ("date", ">=", leave_start),
                        ("date", "<=", leave_end),
                        ("state", "=", "approved"),
                    ]
                )
            }
            work_leave_days = 0
            current = leave_start
            while current <= leave_end:
                if current.weekday() < 5 and current not in holiday_dates:
                    work_leave_days += 1
                current += timedelta(days=1)
            leave_days = work_leave_days
            if leave_days <= 0:
                _logger.warning(
                    "❌ Invalid leave duration: %s (%d days)", leave.name, leave_days
                )
                continue

            _logger.info(
                "🔁 Processing leave for %s | %s → %s (%d days)",
                employee.name,
                leave_start,
                leave_end,
                leave_days,
            )

            # Skip duplicate summary
            if (
                self.env["leave.summary"]
                .sudo()
                .search(
                    [
                        ("employee_id", "=", employee.id),
                        ("event_date", "=", leave_start),
                        ("approved_leaves", "=", leave_days),
                        ("is_monthly_summary", "=", False),
                    ],
                    limit=1,
                )
            ):
                _logger.debug(
                    "⚠️ Summary already exists for %s on %s", employee.name, leave_start
                )
                continue

            # Create event summary
            summary = (
                self.env["leave.summary"]
                .sudo()
                .create(
                    {
                        "employee_id": employee.id,
                        "event_date": leave_start,
                        "approved_leaves": leave_days,
                        "is_monthly_summary": False,
                    }
                )
            )

            summary_sudo = summary.sudo()

            # ✅ Trigger cascade to future summaries
            summary_sudo._cascade_update_future_months()

            # Continue with recomputes
            summary_sudo._set_opening_based_on_previous()
            summary_sudo._compute_allowed_leaves()
            summary_sudo._compute_absent_days()
            summary_sudo._compute_closing_leaves()
            summary_sudo._compute_remaining_leaves()

            _logger.info(
                "✅ Created leave.summary for %s (%d days)", employee.name, leave_days
            )

            # Update monthly summaries (if any overlap)
            affected_months = (
                self.env["leave.summary"]
                .sudo()
                .search(
                    [
                        ("employee_id", "=", employee.id),
                        ("is_monthly_summary", "=", True),
                        ("event_date", ">=", leave_start.replace(day=1)),
                        ("event_date", "<=", leave_end.replace(day=1)),
                    ]
                )
            )

            for summary in affected_months:
                _logger.info(
                    "🔄 Updating monthly summary: %s for %s",
                    summary.event_date,
                    employee.name,
                )
                summary._compute_absent_days()
                summary._compute_closing_leaves()
                summary._compute_remaining_leaves()
                summary._cascade_update_future_months()

                summary.message_post(
                    body=(
                        f"🟡 Auto-adjusted due to backdated leave "
                        f"({leave_start.strftime('%d-%b-%Y')} → {leave_end.strftime('%d-%b-%Y')})"
                    ),
                    message_type="notification",
                    subtype_xmlid="mail.mt_note",
                )
