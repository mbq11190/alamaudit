# -*- coding: utf-8 -*-

import logging

from odoo import _, api, exceptions, fields, models
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)


# Corporate model
class Qacoaudit(models.Model):
    _name = "qaco.audit"
    _rec_name = "client_id"
    # Order of the records will be based on priority, sequence, and date_deadline
    _order = "create_date desc, seq_code desc"
    # Inherit from mail.thread for messaging and mail.activity.mixin for activities
    _inherit = ["mail.thread", "mail.activity.mixin", "mail.tracking.duration.mixin"]
    _description = "QACO Audit Work Portal"
    # Not Used yet, but I will use it later to Track Duration of each stage
    _track_duration_field = "stage_id"

    # I am defining all fields in my model here
    client_id = fields.Many2one("res.partner", required=True, string="Client Name")
    # This field is used to assign multiple users to a task
    user_ids = fields.Many2many(
        "res.users", string="Users", group_expand="_group_expand_user_ids"
    )
    contact = fields.Char(string="Phone", related="client_id.phone", readonly=True)
    referral = fields.Many2one("res.partner", string="Referral")
    audit_year = fields.Many2many("audit.year", string="Audit Year")
    repeat = fields.Selection(
        [("New Client", "New Client"), ("Repeat Client", "Repeat Client")],
        string="Recurring",
    )
    folder = fields.Char(
        string="Folder Path",
    )
    qaco_assigning_partner = fields.Many2one(
        "hr.employee",
        string="Assigning Partner",
        # domain="[('designation_id.name', '=', 'Partner')]",  # Temporarily disabled - requires qaco_employees
    )
    documents_info = fields.Char(
        string="Docs More Info/Location",
    )
    documents = fields.Selection(
        [
            ("Received", "Received"),
            ("Not Received", "Not Received"),
            ("Partially Received", "Partially Received"),
        ],
        string="Documents Status",
    )
    firm_name = fields.Many2one(
        "audit.firm.name", string="Firm Name", ondelete="set null"
    )
    report_type = fields.Selection(
        [
            ("UDIN", "UDIN"),
            ("Agreed Upon Procedures", "Agreed upon Procedures"),
            ("Internal Audit", "Internal Audit"),
            ("3rd Party Audits", "3rd Party Audits"),
        ],
        string="Audit Type",
    )
    udin_no = fields.Char(
        string="UDIN No",
    )
    share_capital = fields.Monetary(
        string="Paid-up Share Capital", currency_field="currency_id"
    )
    currency_id = fields.Many2one("res.currency", string="Currency")
    turnover = fields.Monetary(string="Turnover", currency_field="currency_id")
    bank_balance = fields.Monetary(string="Bank Balance", currency_field="currency_id")
    qaco_audit_partner = fields.Many2one(
        "hr.employee",
        string="Audit Partner",
        # domain="[('designation_id.name', '=', 'Partner')]",  # Temporarily disabled - requires qaco_employees
    )
    no_of_persons = fields.Integer(
        string="No of Persons Required",
    )
    scanned = fields.Selection(
        [("Done/Saved", "Done/Saved"), ("Not Yet", "Not Yet"), ("NA", "NA")],
        string="Data Scan Status",
    )
    original_file = fields.Selection(
        [
            ("Stored In Office", "Stored In Office"),
            ("Returned", "Returned"),
            ("NA", "NA"),
        ],
        string="Client Original Documents",
    )
    employee_id = fields.Many2one(
        "hr.employee", string="Team Lead", ondelete="cascade", index=True
    )
    team_id = fields.Many2many(
        "hr.employee", string="Team Members", ondelete="cascade", index=True
    )
    description = fields.Text()
    # This field is used to set priority of a task
    priority = fields.Selection(
        [
            ("0", "Na"),
            ("1", "Low"),
            ("2", "Mid"),
            ("3", "High"),
        ],
        default="0",
        index=True,
        string="Priority",
        tracking=True,
    )
    stage_id = fields.Many2one(
        "audit.stages",
        default=lambda self: self._get_default_stage_id(),
        string="Stage",
        store=True,
        readonly=True,
        ondelete="restrict",
        index=True,
        tracking=True,
        group_expand="_group_expand_stage_ids",
    )
    color = fields.Integer(string="Color Index")
    state = fields.Selection(
        [
            ("Pending Client Side", "Pending Client Side"),
            ("Working on it", "Working on it"),
            ("Client Confirmed", "Client Confirmed"),
        ],
        string="Client Status",
    )
    pending_reason = fields.Char(
        string="Pending Reason",
        default="Write Pending Reason in the Chatter Below",
        readonly=True,
    )
    # This field is used to hide or show a record, but it is not added to views yet
    active = fields.Boolean("Active", default=True)
    sequence = fields.Integer(default=1)
    date_deadline = fields.Datetime(
        string="Deadline", index=True, copy=False, tracking=True
    )
    create_date = fields.Datetime("Created On", readonly=True, index=True)
    write_date = fields.Datetime("Last Updated On", readonly=True)
    date_end = fields.Datetime(string="Ending Date", index=True, copy=False)
    date_assign = fields.Datetime(
        string="Assigning Date",
        copy=False,
        readonly=True,
        help="Date on which this task was last assigned (or unassigned). Based on this, you can get statistics on the time it usually takes to assign tasks.",
    )
    date_last_stage_update = fields.Datetime(
        string="Last Stage Update",
        index=True,
        copy=False,
        readonly=True,
        help="Date on which the state of your task has last been modified.\n"
        "Based on this information you can identify tasks that are stalling and get statistics on the time it usually takes to move tasks from one stage/state to another.",
    )
    allocated_hours = fields.Float("Allocated Time", tracking=True)
    manager_review = fields.Selection(
        [
            ("Okay to Print", "Okay to Print"),
            ("Revision Required", "Revision Required"),
            ("Review Pending", "Review Pending"),
        ],
        string="Manager Review",
    )
    client_review = fields.Selection(
        [
            ("Client Confirmed", "Client Confirmed"),
            ("Pending Confirmation", "Pending Confirmation"),
        ],
        string="Client Review",
    )
    client_signature = fields.Selection(
        [
            ("Signed Accounts Received", "Signed Accounts Received"),
            ("Sent to Client", "Sent to Client"),
            ("Pending Signature", "Pending Signature"),
        ],
        string="Client Signature",
    )
    file_attachments = fields.One2many(
        "audit.attachment", "audit_id", string="File Attachments"
    )
    is_favourite = fields.Boolean(
        "Favourite",
        help="Mark this task as a favorite to easily find it again",
        tracking=True,
    )
    # Smart button counts removed - only keeping fields for modules that exist
    audit_count = fields.Integer(compute="compute_audit_count")

    def _get_default_seq_code(self):
        return "New"

    seq_code = fields.Char(
        string="Seq Number",
        required=True,
        copy=False,
        readonly=False,
        index=True,
        default=_get_default_seq_code,
    )
    # Engagement master fields (single source of truth)
    engagement_type = fields.Selection(
        [
            ("statutory", "Statutory"),
            ("special", "Special"),
            ("group", "Group"),
            ("pie", "Public Interest Entity (PIE)"),
            ("listed", "Listed"),
        ],
        string="Engagement Type",
    )
    reporting_framework = fields.Selection(
        [("ifrs", "IFRS"), ("ifrs_smes", "IFRS for SMEs"), ("ifas", "IFAS")],
        string="Reporting Framework",
    )
    auditing_standard_ids = fields.Many2many(
        "audit.standard.library", string="Applicable Auditing Standards"
    )
    regulator_ids = fields.Many2many(
        "qaco.regulator",
        "qaco_audit_regulator_rel",
        "audit_id",
        "regulator_id",
        string="Regulators in Scope",
    )

    engagement_status = fields.Selection(
        [
            ("draft", "Draft"),
            ("prepared", "Prepared"),
            ("reviewed", "Reviewed"),
            ("partner_approved", "Partner Approved"),
            ("locked", "Locked"),
        ],
        string="Engagement Status",
        default="draft",
        tracking=True,
    )

    # Computed flag to control visibility of Client Onboarding top tab/button
    show_onboarding_tab = fields.Boolean(
        string="Show Onboarding Tab",
        compute="_compute_show_onboarding_tab",
        store=True,
    )

    @api.depends("engagement_status", "stage_id", "stage_id.name")
    def _compute_show_onboarding_tab(self):
        """Show the onboarding tab when engagement is in draft OR the audit stage
        matches assignment/planning stages. Using a computed boolean keeps view
        logic simple and stable across UI changes."""
        for rec in self:
            is_draft_status = rec.engagement_status == "draft"
            stage_name = (rec.stage_id.name or "").strip().lower() if rec.stage_id else ""
            is_assign_or_planning = stage_name in ("assign", "planning")
            rec.show_onboarding_tab = is_draft_status or is_assign_or_planning

    lock_reason = fields.Text(string="Lock / Unlock Rationale")
    locked_on = fields.Datetime(string="Locked On")
    locked_by = fields.Many2one("res.users", string="Locked By")

    # Role assignments (for segregation of duties)
    preparer_id = fields.Many2one("res.users", string="Preparer")
    reviewer_id = fields.Many2one("res.users", string="Reviewer")
    engagement_partner_user_id = fields.Many2one(
        "res.users", string="Engagement Partner"
    )
    eqcr_partner_user_id = fields.Many2one("res.users", string="EQCR Partner")
    quality_partner_user_id = fields.Many2one("res.users", string="Quality Partner")
    managing_partner_user_id = fields.Many2one("res.users", string="Managing Partner")

    def action_set_status_prepared(self):
        for rec in self:
            rec.engagement_status = "prepared"
            rec.message_post(body="Status set to Prepared")

    def action_set_status_reviewed(self):
        for rec in self:
            rec.engagement_status = "reviewed"
            rec.message_post(body="Status set to Reviewed")

    def action_partner_approve(self):
        for rec in self:
            # maker-checker: reviewer must not be same as preparer
            if (
                rec.reviewer_id
                and rec.preparer_id
                and rec.reviewer_id == rec.preparer_id
            ):
                raise exceptions.ValidationError(
                    _(
                        "Reviewer must be different from Preparer (Maker-Checker violation)"
                    )
                )
            rec.engagement_status = "partner_approved"
            rec.message_post(body="Partner Approved")

    def action_lock_engagement(self, reason=None):
        for rec in self:
            if rec.engagement_status != "partner_approved":
                raise exceptions.ValidationError(
                    _("Engagement must be partner approved before locking.")
                )
            rec.engagement_status = "locked"
            rec.lock_reason = reason or rec.lock_reason
            rec.locked_on = fields.Datetime.now()
            rec.locked_by = self.env.user
            rec.message_post(
                body=f"Engagement locked by {self.env.user.name}: {rec.lock_reason}"
            )

    def action_unlock_engagement(self, reason=None):
        for rec in self:
            # First: if caller is a manager, allow immediate unlock
            if self.user_has_groups("qaco_audit.group_audit_manager"):
                rec.engagement_status = "partner_approved"
                rec.lock_reason = reason or rec.lock_reason
                rec.locked_on = False
                rec.locked_by = False
                rec.message_post(
                    body=f"Engagement unlocked by {self.env.user.name}: {rec.lock_reason}"
                )
                continue
            # Otherwise, look for an approved lock approval that has not been applied
            approval = self.env["qaco.audit.lock.approval"].search(
                [
                    ("audit_id", "=", rec.id),
                    ("status", "=", "approved"),
                    ("applied", "=", False),
                ],
                limit=1,
                order="approved_on desc",
            )
            if approval:
                rec.engagement_status = "partner_approved"
                rec.lock_reason = (
                    reason or rec.lock_reason or f"Unlock via approval {approval.id}"
                )
                rec.locked_on = False
                rec.locked_by = approval.approver_id or rec.locked_by
                rec.message_post(
                    body=f"Engagement unlocked via approved override {approval.id}: {approval.requestor_id.name} requested on {approval.requested_on}"
                )
                approval.applied = True
                continue
            raise exceptions.AccessError(
                _(
                    "Only managing partners may unlock engagements, or an approved override must exist."
                )
            )

    # Function to Show Empty Stages in Kanban View
    def _group_expand_stage_ids(self, stages, domain, order):
        """Read group customization in order to display all the stages in the
        Kanban view, even if they are empty.
        """
        stage_ids = stages._search([], order=order)
        return stages.browse(stage_ids)

    # Function to show all users in Kanban grouping
    def _group_expand_user_ids(self, users, domain, order):
        """Return all users so Kanban grouping by user shows empty groups."""
        user_ids = users._search([], order=order)
        return users.browse(user_ids)

    # Function to get default stage id as first stage
    def _get_default_stage_id(self):
        return self.env["audit.stages"].search([("name", "=", "New")], limit=1).id

    # Function to Move to Next Stage and Add constraints to move to next stage
    def move_to_next_stage(self):
        next_stage = self.env["audit.stages"].search(
            [("sequence", ">", self.stage_id.sequence)], order="sequence", limit=1
        )
        if not next_stage:
            return

        missing_fields = []

        if next_stage.id == 3:
            if not self.employee_id:
                missing_fields.append(self._fields["employee_id"].string)
            if not self.team_id:
                missing_fields.append(self._fields["team_id"].string)

        if next_stage.id == 4:
            for field in ["folder", "qaco_audit_partner"]:
                if not getattr(self, field):
                    missing_fields.append(self._fields[field].string)

        if next_stage.id == 2:
            for field in [
                "client_id",
                "contact",
                "audit_year",
                "firm_name",
                "report_type",
            ]:
                if not getattr(self, field):
                    missing_fields.append(self._fields[field].string)

        if missing_fields:
            raise exceptions.ValidationError(
                _(
                    "Please fill the following fields before moving to the next stage: %s"
                )
                % ", ".join(missing_fields)
            )

        if next_stage.name == "Invoiced" and not self.user_has_groups(
            "base.group_system"
        ):
            raise exceptions.ValidationError(
                "Only Partner may move it to the next stage."
            )

        # Gateway control: do not allow entering Execution unless Planning is complete
        if "execution" in (next_stage.name or "").lower():
            planning = self.env["qaco.planning.phase"].search(
                [("audit_id", "=", self.id), ("planning_complete", "=", True)], limit=1
            )
            if not planning:
                raise exceptions.ValidationError(
                    _(
                        "Planning phase must be completed and partner-signed before starting Execution."
                    )
                )

        if next_stage.name == "Done":
            return {
                "name": _("Audit Done"),
                "type": "ir.actions.act_window",
                "view_id": self.env.ref("qaco_audit.audit_done_form_view").id,
                "res_model": "audit.done",
                "view_mode": "form",
                "target": "new",
                "context": {
                    "active_id": self.ids[0],
                },
            }

        self.stage_id = next_stage

    def move_to_previous_stage(self):
        previous_stage = self.env["audit.stages"].search(
            [("sequence", "<", self.stage_id.sequence)], order="sequence desc", limit=1
        )
        if previous_stage:
            self.stage_id = previous_stage

    # Function to Archive Record

    def action_archive(self):
        if not self.user_has_groups(
            "qaco_audit.group_audit_partner,qaco_audit.group_audit_administrator"
        ):
            raise AccessError(_("You do not have permission to perform this action."))
        self.write({"active": False})

    # Function to Override default Duplicate/copy function

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        if not self.user_has_groups(
            "qaco_audit.group_audit_partner,qaco_audit.group_audit_administrator"
        ):
            raise AccessError(_("You do not have permission to perform this action."))
        default = default or {}
        default["audit_year"] = False
        default["repeat"] = False
        default["employee_id"] = False
        default["team_id"] = False
        default["qaco_audit_partner"] = False
        default["share_capital"] = False
        default["udin_no"] = False
        default["turnover"] = False
        default["client_signature"] = False
        default["bank_balance"] = False
        default["state"] = False
        default["manager_review"] = False
        default["pending_reason"] = False
        default["file_attachments"] = False
        # default['documents'] = False
        # default['scanned'] = False
        default["original_file"] = False
        default["date_deadline"] = False
        default["documents_info"] = False
        default["stage_id"] = 1
        new_record = super(Qacoaudit, self).copy(default)
        new_record.message_post(
            body="This record is duplicated from record with ID %s" % self.id
        )
        return new_record

    def write(self, vals):
        """Unified write: logs changes and keeps message subscribers in sync.

        - Records field-level changes into `qaco.audit.changelog`.
        - When `employee_id` or `team_id` are updated, unsubscribe old partners
          before the write and subscribe new partners after the write.
        """
        logs = []

        # Build changelog entries pre-write (capture old values)
        for rec in self:
            for field, new in vals.items():
                if field not in rec._fields:
                    continue
                old = getattr(rec, field)

                def val_to_str(v):
                    if v is None:
                        return ""
                    if hasattr(v, "ids"):
                        try:
                            return ",".join(map(str, v.mapped("name") or v.ids))
                        except Exception:
                            return str(v.ids)
                    return str(v)

                old_str = val_to_str(old)
                new_str = val_to_str(new)
                if old_str != new_str:
                    logs.append(
                        {
                            "audit_id": rec.id,
                            "field_name": field,
                            "old_value": old_str,
                            "new_value": new_str,
                            "changed_by": self.env.uid,
                        }
                    )

        # If team/employee being changed, unsubscribe old partners first
        if "employee_id" in vals or "team_id" in vals:
            for record in self:
                old_partners = []
                if (
                    "employee_id" in vals
                    and record.employee_id
                    and record.employee_id.user_id
                    and record.employee_id.user_id.partner_id
                ):
                    old_partners.append(record.employee_id.user_id.partner_id.id)
                if "team_id" in vals:
                    old_partners += [
                        emp.user_id.partner_id.id
                        for emp in record.team_id
                        if emp.user_id and emp.user_id.partner_id
                    ]
                if old_partners:
                    record.message_unsubscribe(partner_ids=list(set(old_partners)))

        # Perform actual write
        res = super(Qacoaudit, self).write(vals)

        # Persist changelogs and post messages
        if logs:
            try:
                self.env["qaco.audit.changelog"].create(logs)
                for log in logs:
                    self.message_post(
                        body="Change logged: %s: %s -> %s"
                        % (log["field_name"], log["old_value"], log["new_value"])
                    )
            except Exception:
                _logger.exception("Failed to create changelog records")

        # Subscribe new partners if team/employee changed
        if "employee_id" in vals or "team_id" in vals:
            for record in self:
                new_partners = []
                if (
                    record.employee_id
                    and record.employee_id.user_id
                    and record.employee_id.user_id.partner_id
                ):
                    new_partners.append(record.employee_id.user_id.partner_id.id)
                new_partners += [
                    emp.user_id.partner_id.id
                    for emp in record.team_id
                    if emp.user_id and emp.user_id.partner_id
                ]
                if new_partners:
                    record.message_subscribe(partner_ids=list(set(new_partners)))

        return res

    def unlink(self):
        if not self.user_has_groups(
            "qaco_audit.group_audit_partner,qaco_audit.group_audit_administrator"
        ):
            raise AccessError(_("You do not have permission to perform this action."))
        return super(Qacoaudit, self).unlink()

    # Function to add sequence number automatically

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("seq_code", "New") == "New":
                seq_code = (
                    self.env["ir.sequence"].next_by_code(
                        "audit.sequence", sequence_date=fields.Date.today()
                    )
                    or "New"
                )
                vals["seq_code"] = seq_code

        records = super().create(vals_list)

        followers = self.env["qaco_audit.auto.follower"].search([])
        partner_ids = followers.mapped("employee_id.user_id.partner_id.id")
        partner_ids = [pid for pid in partner_ids if pid]
        if partner_ids:
            records.message_subscribe(partner_ids=list(set(partner_ids)))
        return records



    def remove_all_attachments(self):
        attachments = self.env["ir.attachment"].search(
            [("res_model", "=", "qaco.audit"), ("res_id", "=", self.id)]
        )
        if attachments:
            attachments.unlink()

    @api.depends("client_id")
    def compute_audit_count(self):
        for record in self:
            record.audit_count = (
                self.env["qaco.audit"]
                .sudo()
                .search_count(
                    [("client_id", "=", record.client_id.id), ("active", "=", True)]
                )
            )

    # ==================
    # Action Methods
    # ==================
    def get_audit(self):
        return self._open_related_records("qaco.audit", "Audit")

    # ==================
    # Helper Method
    # ==================
    def _open_related_records(self, model_name, name):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": name,
            "view_mode": "tree,form",
            "res_model": model_name,
            "domain": [("client_id", "=", self.client_id.id)],
            "context": {"create": False},
        }

    def action_open_client_onboarding(self):
        """Open or create client onboarding record for this audit"""
        self.ensure_one()
        onboarding = self.env["qaco.client.onboarding"].search(
            [("audit_id", "=", self.id)], limit=1
        )
        if not onboarding:
            onboarding = self.env["qaco.client.onboarding"].create(
                {
                    "audit_id": self.id,
                }
            )
        view = self.env.ref('qaco_client_onboarding.view_client_onboarding_form', raise_if_not_found=False)
        action = {
            "type": "ir.actions.act_window",
            "name": "Client Onboarding",
            "res_model": "qaco.client.onboarding",
            "res_id": onboarding.id,
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_audit_id": self.id,
                "default_partner_id": self.client_id.id if self.client_id else False,
                "default_company_id": self.env.company.id,
            },
        }
        if view:
            action["views"] = [(view.id, "form")]
        return action

    def action_open_planning_phase(self):
        """Open or create planning phase record for this audit"""
        self.ensure_one()
        planning = self.env["qaco.planning.phase"].search(
            [("audit_id", "=", self.id)], limit=1
        )
        if not planning:
            planning = self.env["qaco.planning.phase"].create(
                {
                    "audit_id": self.id,
                }
            )
        return {
            "type": "ir.actions.act_window",
            "name": "Planning Phase",
            "res_model": "qaco.planning.phase",
            "res_id": planning.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_open_planning_dashboard(self):
        """Open planning progress dashboard for this audit (Session 6A)"""
        self.ensure_one()
        planning_main = self.env["qaco.planning.main"].search(
            [("audit_id", "=", self.id)], limit=1
        )
        if not planning_main:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("No Planning Phase"),
                    "message": _(
                        "Planning phase has not been initialized for this audit yet."
                    ),
                    "type": "warning",
                    "sticky": False,
                },
            }
        return {
            "type": "ir.actions.act_window",
            "name": _("Planning Progress Dashboard"),
            "res_model": "qaco.planning.main",
            "res_id": planning_main.id,
            "view_mode": "form",
            "views": [
                (
                    self.env.ref(
                        "qaco_planning_phase.view_planning_main_dashboard_kanban"
                    ).id,
                    "kanban",
                )
            ],
            "target": "current",
            "context": {"create": False, "edit": False},
        }
