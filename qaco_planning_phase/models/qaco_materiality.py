import csv
import json
import logging
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP, getcontext

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

getcontext().prec = 28

_logger = logging.getLogger(__name__)


def _decimal(value):
    """Convert to Decimal safely for internal arithmetic."""
    try:
        if value is None:
            return Decimal("0")
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def _round_to_nearest(amount, rounding):
    """Round numeric amount to nearest rounding unit."""
    try:
        unit = int(rounding)
    except Exception:
        unit = 1000
    if not unit or unit <= 0:
        return amount
    try:
        dec = _decimal(amount)
        quotient = (dec / Decimal(unit)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return quotient * Decimal(unit)
    except Exception:
        try:
            return round(float(amount) / unit) * unit
        except Exception:
            return amount


class QacoMaterialityComponent(models.Model):
    _name = "qaco.materiality.component"
    _description = "Materiality Component"
    _order = "id asc"

    materiality_id = fields.Many2one(
        "qaco.materiality",
        string="Materiality Worksheet",
        required=True,
        ondelete="cascade",
        index=True,
    )
    name = fields.Char(string="Component Name", required=True)
    component_type = fields.Selection(
        [
            ("subsidiary", "Subsidiary"),
            ("branch", "Branch"),
            ("division", "Division"),
            ("other", "Other"),
        ],
        string="Type",
        default="subsidiary",
    )
    component_benchmark = fields.Monetary(string="Component Benchmark", currency_field="currency_id")
    method = fields.Selection(
        [
            ("percentage_of_group", "% of Group Materiality"),
            ("benchmark_percent", "% of Component Benchmark"),
            ("absolute", "Absolute Amount"),
        ],
        default="percentage_of_group",
    )
    value_percent_or_amount = fields.Float(
        string="Percent / Amount",
        digits=(12, 6),
        help="If method is percent, provide percent (e.g. 40 for 40%). For absolute, provide the amount.",
    )
    notes = fields.Text(string="Notes / Rationale")

    computed_materiality = fields.Monetary(
        string="Computed Materiality",
        compute="_compute_computed_materiality",
        store=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="materiality_id.currency_id",
        store=True,
        readonly=True,
    )

    @api.depends("component_benchmark", "method", "value_percent_or_amount", "materiality_id.materiality_amount")
    def _compute_computed_materiality(self):
        for rec in self:
            try:
                group_mat = _decimal(rec.materiality_id.materiality_amount or 0.0)
                value = _decimal(rec.value_percent_or_amount or 0.0)
                if rec.method == "percentage_of_group":
                    result = group_mat * value / Decimal(100.0)
                elif rec.method == "benchmark_percent":
                    result = _decimal(rec.component_benchmark or 0.0) * value / Decimal(100.0)
                elif rec.method == "absolute":
                    result = value
                else:
                    result = Decimal("0")
                rec.computed_materiality = rec.currency_id.round(result) if rec.currency_id else float(result)
            except Exception:
                rec.computed_materiality = 0.0


class QacoMaterialityTolerance(models.Model):
    _name = "qaco.materiality.tolerance"
    _description = "Materiality Tolerance"
    _order = "id asc"

    materiality_id = fields.Many2one(
        "qaco.materiality",
        string="Materiality Worksheet",
        required=True,
        ondelete="cascade",
        index=True,
    )
    account_name = fields.Char(string="Account / Area", required=True)
    basis = fields.Text(string="Basis / Rationale")
    percent = fields.Float(string="Percent of Overall Materiality (%)", digits=(12, 6))
    absolute_amount = fields.Monetary(string="Absolute Amount", currency_field="currency_id")
    computed_amount = fields.Monetary(
        string="Computed Tolerance Amount",
        compute="_compute_computed_amount",
        store=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="materiality_id.currency_id",
        store=True,
        readonly=True,
    )

    @api.depends("percent", "absolute_amount", "materiality_id.materiality_amount")
    def _compute_computed_amount(self):
        for rec in self:
            try:
                group_mat = _decimal(rec.materiality_id.materiality_amount or 0.0)
                if rec.absolute_amount and float(rec.absolute_amount) > 0:
                    result = _decimal(rec.absolute_amount)
                elif rec.percent and rec.percent > 0 and group_mat:
                    result = group_mat * _decimal(rec.percent) / Decimal(100.0)
                else:
                    result = Decimal("0")
                rec.computed_amount = rec.currency_id.round(result) if rec.currency_id else float(result)
            except Exception:
                rec.computed_amount = 0.0


class QacoMaterialityHistory(models.Model):
    _name = "qaco.materiality.history"
    _description = "Materiality - Change History"

    materiality_id = fields.Many2one(
        "qaco.materiality",
        string="Materiality Worksheet",
        ondelete="cascade",
        required=True,
    )
    changed_by = fields.Many2one("res.users", string="Changed by")
    changed_date = fields.Datetime(string="Changed on", default=fields.Datetime.now)
    old_values = fields.Text(string="Old values (JSON)")
    note = fields.Text(string="Note")


class QacoMateriality(models.Model):
    _name = "qaco.materiality"
    _description = "Audit Materiality Worksheet"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    planning_id = fields.Many2one("qaco.planning.phase", string="Planning Phase", ondelete="cascade")
    audit_id = fields.Many2one("qaco.audit", string="Audit Reference", ondelete="cascade")
    name = fields.Char(string="Reference", readonly=True, copy=False)
    date_prepared = fields.Date(string="Date prepared", default=fields.Date.context_today)
    prepared_by = fields.Many2one("res.users", string="Prepared by", default=lambda self: self.env.user)
    reviewed_by = fields.Many2one("res.users", string="Reviewed by")
    status = fields.Selection(
        [
            ("draft", "Draft"),
            ("approved", "Approved"),
            ("superseded", "Superseded"),
            ("archived", "Archived"),
        ],
        default="draft",
        tracking=True,
    )

    benchmark_type = fields.Selection(
        [
            ("pbt", "Profit before tax"),
            ("revenue", "Total revenue"),
            ("assets", "Total assets"),
            ("equity", "Equity"),
            ("other", "Other"),
        ],
        string="Benchmark",
        default="pbt",
        required=True,
        tracking=True,
    )
    benchmark_amount = fields.Monetary(string="Benchmark amount", currency_field="currency_id")
    benchmark_auto_pulled = fields.Boolean(
        string="Benchmark auto-pulled",
        compute="_compute_benchmark_auto_pulled",
        store=True,
    )
    base_source_type = fields.Selection(
        [
            ("tb_snapshot", "Trial balance snapshot"),
            ("account_move", "Accounting module"),
            ("manual", "Manual entry"),
        ],
        string="Source Type",
        default="manual",
    )
    base_source_reference = fields.Char(string="Source Reference")

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )

    applied_percent = fields.Float(string="Applied %", digits=(12, 6))
    materiality_amount = fields.Monetary(
        string="Materiality amount",
        compute="_compute_materiality",
        store=True,
        currency_field="currency_id",
    )
    performance_percent = fields.Float(string="Performance %", default=75.0, digits=(12, 6))
    performance_materiality_amount = fields.Monetary(
        string="Performance materiality",
        compute="_compute_materiality",
        store=True,
        currency_field="currency_id",
    )
    trivial_percent = fields.Float(string="Clearly trivial %", default=5.0, digits=(12, 6))
    trivial_amount = fields.Monetary(
        string="Clearly trivial amount",
        compute="_compute_materiality",
        store=True,
        currency_field="currency_id",
    )
    rounding = fields.Selection(
        [("10", "10"), ("100", "100"), ("1000", "1,000"), ("10000", "10,000")],
        string="Rounding",
        default="1000",
    )

    aggregation_allowance = fields.Monetary(string="Aggregation allowance", currency_field="currency_id", default=0.0)
    qualitative_adjustments = fields.Text(string="Qualitative adjustments / Considerations")
    low_sensitivity_percent = fields.Float(string="Low sensitivity %", default=0.0, digits=(12, 6))
    high_sensitivity_percent = fields.Float(string="High sensitivity %", default=0.0, digits=(12, 6))
    low_sensitivity_amount = fields.Monetary(
        string="Low sensitivity amount",
        compute="_compute_sensitivity",
        store=True,
        currency_field="currency_id",
    )
    high_sensitivity_amount = fields.Monetary(
        string="High sensitivity amount",
        compute="_compute_sensitivity",
        store=True,
        currency_field="currency_id",
    )

    component_ids = fields.One2many("qaco.materiality.component", "materiality_id", string="Components")
    tolerance_ids = fields.One2many("qaco.materiality.tolerance", "materiality_id", string="Tolerances")
    history_ids = fields.One2many("qaco.materiality.history", "materiality_id", string="Revision History")

    revision_of_id = fields.Many2one("qaco.materiality", string="Revision of")
    approved_by = fields.Many2one("res.users", string="Approved by", readonly=True)
    approved_date = fields.Datetime(string="Approved date", readonly=True)

    rationale = fields.Text(
        string="Rationale / Basis",
        help="Explain choice of benchmark and applied % with reference to ISA 320 and ISA 450.",
    )
    notes = fields.Text(string="Notes / Working Comments")
    attachment_count = fields.Integer(string="Attachments", compute="_compute_attachment_count", compute_sudo=True)

    _sql_constraints = [
        ("qaco_materiality_name_uniq", "unique(name)", "Reference must be unique."),
    ]

    @api.model
    def create(self, vals):
        if not vals.get("name"):
            seq = self.env["ir.sequence"].sudo().next_by_code("qaco.materiality") or _("MAT/PLAN/0000")
            vals["name"] = seq
        if vals.get("planning_id") and not vals.get("audit_id"):
            planning = self.env["qaco.planning.phase"].browse(vals["planning_id"])
            vals["audit_id"] = planning.audit_id.id
        record = super().create(vals)
        record._compute_materiality()
        return record

    def write(self, vals):
        restricted = {
            "benchmark_type",
            "benchmark_amount",
            "applied_percent",
            "materiality_amount",
            "performance_percent",
            "performance_materiality_amount",
            "trivial_percent",
            "trivial_amount",
        }
        for rec in self:
            if rec.status == "approved" and any(field in vals for field in restricted):
                if not self._context.get("allow_write_approved"):
                    raise ValidationError(
                        _("Cannot modify critical materiality fields on an approved worksheet. Use Supersede."),
                    )
        result = super().write(vals)
        self._compute_materiality()
        return result

    @api.depends("audit_id", "benchmark_type")
    def _compute_benchmark_auto_pulled(self):
        for rec in self:
            pulled = False
            if rec.audit_id:
                attr_map = {
                    "pbt": "tb_pbt",
                    "revenue": "tb_revenue",
                    "assets": "tb_assets",
                    "equity": "tb_equity",
                }
                attr_name = attr_map.get(rec.benchmark_type)
                if attr_name and hasattr(rec.audit_id, attr_name):
                    value = getattr(rec.audit_id, attr_name)
                    if value:
                        pulled = True
                        if not rec.benchmark_amount:
                            try:
                                rec.benchmark_amount = value
                            except Exception:
                                _logger.exception("Failed to auto-populate benchmark amount for %s", rec.id)
            rec.benchmark_auto_pulled = pulled

    @api.depends(
        "benchmark_amount",
        "applied_percent",
        "performance_percent",
        "trivial_percent",
        "rounding",
        "currency_id",
        "aggregation_allowance",
        "component_ids.computed_materiality",
        "tolerance_ids.computed_amount",
    )
    def _compute_materiality(self):
        for rec in self:
            base = _decimal(rec.benchmark_amount or 0.0)
            applied = _decimal(rec.applied_percent or 0.0)
            perf = float(rec.performance_percent or 0.0)
            trivial = float(rec.trivial_percent or 0.0)

            if applied:
                mat_amount = (base * applied) / Decimal("100")
            else:
                mat_amount = Decimal("0")

            rounded = _round_to_nearest(mat_amount, rec.rounding)
            rounded_dec = _decimal(rounded or 0.0)
            allowance = _decimal(rec.aggregation_allowance or 0.0)
            final_dec = rounded_dec - allowance
            if final_dec < 0:
                final_dec = Decimal("0")
            final_float = float(final_dec)

            if rec.currency_id:
                rec.materiality_amount = rec.currency_id.round(final_float)
                rec_performance_base = rec.materiality_amount or 0.0
                rec.performance_materiality_amount = (
                    rec.currency_id.round(rec_performance_base * perf / 100.0)
                    if perf
                    else 0.0
                )
                rec.trivial_amount = (
                    rec.currency_id.round(rec_performance_base * trivial / 100.0)
                    if trivial
                    else 0.0
                )
            else:
                rec.materiality_amount = round(final_float)
                base_amount = rec.materiality_amount or 0.0
                rec.performance_materiality_amount = round(base_amount * perf / 100.0) if perf else 0.0
                rec.trivial_amount = round(base_amount * trivial / 100.0) if trivial else 0.0

            rec.component_ids._compute_computed_materiality()
            rec.tolerance_ids._compute_computed_amount()

    @api.depends("applied_percent", "benchmark_amount", "currency_id")
    def _compute_sensitivity(self):
        for rec in self:
            applied = float(rec.applied_percent or 0.0)
            rec.low_sensitivity_percent = round(applied * 0.75, 6) if applied else 0.0
            rec.high_sensitivity_percent = round(applied * 1.25, 6) if applied else 0.0
            base = float(rec.benchmark_amount or 0.0)
            low_amount = base * (rec.low_sensitivity_percent or 0.0) / 100.0 if rec.low_sensitivity_percent else 0.0
            high_amount = base * (rec.high_sensitivity_percent or 0.0) / 100.0 if rec.high_sensitivity_percent else 0.0
            if rec.currency_id:
                rec.low_sensitivity_amount = rec.currency_id.round(low_amount)
                rec.high_sensitivity_amount = rec.currency_id.round(high_amount)
            else:
                rec.low_sensitivity_amount = round(low_amount)
                rec.high_sensitivity_amount = round(high_amount)

    def _compute_attachment_count(self):
        Attachment = self.env["ir.attachment"]
        for rec in self:
            if not rec.id:
                rec.attachment_count = 0
                continue
            domain = [("res_model", "=", self._name), ("res_id", "=", rec.id)]
            rec.attachment_count = Attachment.search_count(domain)

    @api.constrains("applied_percent", "performance_percent", "trivial_percent")
    def _check_percentages(self):
        for rec in self:
            if rec.applied_percent is None or rec.applied_percent <= 0 or rec.applied_percent > 100:
                raise ValidationError(_("Applied % must be greater than 0 and less than or equal to 100."))
            if rec.performance_percent is None or rec.performance_percent <= 0 or rec.performance_percent >= 100:
                raise ValidationError(_("Performance % must be greater than 0 and less than 100."))
            if rec.trivial_percent is None or rec.trivial_percent <= 0:
                raise ValidationError(_("Clearly trivial % must be greater than 0."))
            if rec.trivial_percent >= rec.performance_percent:
                raise ValidationError(_("Clearly trivial % must be less than Performance %."))
            if rec.trivial_percent >= rec.applied_percent:
                raise ValidationError(_("Clearly trivial % should be less than Applied %."))

    @api.onchange("audit_id", "benchmark_type")
    def _onchange_audit_or_benchmark(self):
        for rec in self:
            if not rec.audit_id:
                continue
            attr_map = {
                "pbt": "tb_pbt",
                "revenue": "tb_revenue",
                "assets": "tb_assets",
                "equity": "tb_equity",
            }
            attr_name = attr_map.get(rec.benchmark_type)
            if attr_name and hasattr(rec.audit_id, attr_name):
                try:
                    value = getattr(rec.audit_id, attr_name)
                    if value:
                        rec.benchmark_amount = value
                        rec.benchmark_auto_pulled = True
                except Exception:
                    rec.benchmark_auto_pulled = False
            else:
                rec.benchmark_auto_pulled = False

    def button_apply_defaults(self):
        defaults = {
            "pbt": 5.0,
            "revenue": 0.5,
            "assets": 0.5,
            "equity": 1.0,
            "other": 1.0,
        }
        for rec in self:
            rec.applied_percent = defaults.get(rec.benchmark_type, 1.0)
            rec.performance_percent = 75.0
            rec.trivial_percent = 5.0
            rec._compute_materiality()

    def button_approve(self):
        for rec in self:
            if rec.status == "approved":
                continue
            if not rec.rationale or not rec.prepared_by or not rec.reviewed_by:
                raise ValidationError(
                    _("Cannot approve. Rationale, Prepared by and Reviewed by are required."),
                )
            snapshot = {
                "benchmark_type": rec.benchmark_type,
                "benchmark_amount": float(rec.benchmark_amount or 0.0),
                "applied_percent": float(rec.applied_percent or 0.0),
                "materiality_amount": float(rec.materiality_amount or 0.0),
                "performance_percent": float(rec.performance_percent or 0.0),
                "performance_materiality_amount": float(rec.performance_materiality_amount or 0.0),
                "trivial_percent": float(rec.trivial_percent or 0.0),
                "trivial_amount": float(rec.trivial_amount or 0.0),
            }
            self.env["qaco.materiality.history"].create(
                {
                    "materiality_id": rec.id,
                    "changed_by": self.env.user.id,
                    "old_values": json.dumps(snapshot),
                    "note": _("Approved by %s") % self.env.user.name,
                }
            )
            rec.status = "approved"
            rec.approved_by = self.env.user
            rec.approved_date = fields.Datetime.now()
            rec.message_post(
                body=_("Materiality worksheet approved by %s on %s")
                % (self.env.user.name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            if rec.planning_id:
                rec.planning_id.materiality_ready = True
                rec.planning_id._log_evidence(
                    name=_("Materiality approved"),
                    action_type="approval",
                    note=rec.rationale or _("Materiality approved"),
                    standard_reference="ISA 320",
                )

    def button_supersede(self):
        Attachment = self.env["ir.attachment"]
        new_records = self.env["qaco.materiality"]
        for rec in self:
            copy_vals = {
                "planning_id": rec.planning_id.id,
                "audit_id": rec.audit_id.id,
                "benchmark_type": rec.benchmark_type,
                "benchmark_amount": rec.benchmark_amount,
                "currency_id": rec.currency_id.id,
                "applied_percent": rec.applied_percent,
                "performance_percent": rec.performance_percent,
                "trivial_percent": rec.trivial_percent,
                "rounding": rec.rounding,
                "rationale": rec.rationale,
                "notes": rec.notes,
                "prepared_by": rec.prepared_by.id if rec.prepared_by else False,
                "reviewed_by": rec.reviewed_by.id if rec.reviewed_by else False,
                "revision_of_id": rec.id,
                "base_source_type": rec.base_source_type,
                "base_source_reference": rec.base_source_reference,
                "aggregation_allowance": rec.aggregation_allowance,
                "qualitative_adjustments": rec.qualitative_adjustments,
            }
            new_rec = self.with_context(allow_write_approved=True).create(copy_vals)
            component_commands = [
                (
                    0,
                    0,
                    {
                        "name": comp.name,
                        "component_type": comp.component_type,
                        "component_benchmark": comp.component_benchmark,
                        "method": comp.method,
                        "value_percent_or_amount": comp.value_percent_or_amount,
                        "notes": comp.notes,
                    },
                )
                for comp in rec.component_ids
            ]
            if component_commands:
                new_rec.component_ids = component_commands
            tolerance_commands = [
                (
                    0,
                    0,
                    {
                        "account_name": tol.account_name,
                        "basis": tol.basis,
                        "percent": tol.percent,
                        "absolute_amount": tol.absolute_amount,
                    },
                )
                for tol in rec.tolerance_ids
            ]
            if tolerance_commands:
                new_rec.tolerance_ids = tolerance_commands
            rec.with_context(allow_write_approved=True).write({"status": "superseded"})
            self.env["qaco.materiality.history"].create(
                {
                    "materiality_id": rec.id,
                    "changed_by": self.env.user.id,
                    "old_values": json.dumps({"superseded_by": new_rec.name}),
                    "note": _("Superseded by %s") % new_rec.name,
                }
            )
            attachments = Attachment.search([("res_model", "=", self._name), ("res_id", "=", rec.id)])
            for attachment in attachments:
                try:
                    attachment.write({"res_id": new_rec.id})
                except Exception:
                    _logger.exception("Failed to reassign attachment %s during supersede", attachment.id)
            new_records |= new_rec
        return new_records

    def button_reset_to_draft(self):
        for rec in self:
            rec.status = "draft"
            rec.approved_by = False
            rec.approved_date = False
            rec.message_post(body=_("Materiality reset to draft by %s") % self.env.user.name)

    def name_get(self):
        result = []
        for rec in self:
            label = rec.name or "/"
            if rec.materiality_amount:
                try:
                    symbol = rec.currency_id.symbol or ""
                    label = "%s [%s%s]" % (label, symbol, int(rec.materiality_amount))
                except Exception:
                    label = "%s [%s]" % (label, rec.materiality_amount)
            result.append((rec.id, label))
        return result

    def action_revise(self, changed_by_user=None, new_applied_percent=None, new_benchmark_amount=None, reason=None):
        changed_by = changed_by_user or self.env.user
        for rec in self:
            old_snapshot = {
                "benchmark_type": rec.benchmark_type,
                "benchmark_amount": float(rec.benchmark_amount or 0.0),
                "applied_percent": float(rec.applied_percent or 0.0),
                "materiality_amount": float(rec.materiality_amount or 0.0),
                "performance_percent": float(rec.performance_percent or 0.0),
                "performance_materiality_amount": float(rec.performance_materiality_amount or 0.0),
                "trivial_percent": float(rec.trivial_percent or 0.0),
                "trivial_amount": float(rec.trivial_amount or 0.0),
            }
            vals = {}
            if new_applied_percent is not None:
                vals["applied_percent"] = float(new_applied_percent)
            if new_benchmark_amount is not None:
                vals["benchmark_amount"] = new_benchmark_amount
            rec.with_context(allow_write_approved=True).write(vals)
            new_snapshot = {
                "benchmark_type": rec.benchmark_type,
                "benchmark_amount": float(rec.benchmark_amount or 0.0),
                "applied_percent": float(rec.applied_percent or 0.0),
                "materiality_amount": float(rec.materiality_amount or 0.0),
                "performance_percent": float(rec.performance_percent or 0.0),
                "performance_materiality_amount": float(rec.performance_materiality_amount or 0.0),
                "trivial_percent": float(rec.trivial_percent or 0.0),
                "trivial_amount": float(rec.trivial_amount or 0.0),
            }
            self.env["qaco.materiality.history"].create(
                {
                    "materiality_id": rec.id,
                    "changed_by": changed_by.id if hasattr(changed_by, "id") else changed_by,
                    "old_values": json.dumps(old_snapshot),
                    "note": reason or _("Materiality revised"),
                }
            )
        return True

    def evaluate_misstatements(self, misstatements):
        self.ensure_one()
        total_identified = Decimal("0")
        total_uncorrected = Decimal("0")
        per_account = {}
        for item in misstatements:
            amount = _decimal(item.get("amount", 0))
            corrected = bool(item.get("corrected", False))
            account = item.get("account", "Unknown")
            total_identified += amount
            if not corrected:
                total_uncorrected += amount
            per_account.setdefault(account, Decimal("0"))
            per_account[account] += amount

        mat_amt = _decimal(self.materiality_amount or 0)
        perf_amt = _decimal(self.performance_materiality_amount or 0)
        exceeds_materiality = total_uncorrected > mat_amt
        exceeds_performance = total_uncorrected > perf_amt

        tolerance_flags = []
        for tol in self.tolerance_ids:
            tol_amt = _decimal(tol.computed_amount or 0)
            acct_mis = per_account.get(tol.account_name, Decimal("0"))
            if acct_mis > tol_amt:
                tolerance_flags.append(
                    {
                        "account": tol.account_name,
                        "misstatement": float(acct_mis),
                        "tolerance": float(tol_amt),
                        "exceeds": True,
                    }
                )

        return {
            "materiality_amount": float(mat_amt),
            "performance_materiality": float(perf_amt),
            "total_identified": float(total_identified),
            "total_uncorrected": float(total_uncorrected),
            "exceeds_materiality": bool(exceeds_materiality),
            "exceeds_performance": bool(exceeds_performance),
            "per_account": {k: float(v) for k, v in per_account.items()},
            "tolerance_flags": tolerance_flags,
        }

    def export_to_json(self):
        self.ensure_one()
        data = {
            "reference": self.name,
            "prepared_by": self.prepared_by.name if self.prepared_by else False,
            "reviewed_by": self.reviewed_by.name if self.reviewed_by else False,
            "date_prepared": fields.Date.to_string(self.date_prepared),
            "benchmark_type": self.benchmark_type,
            "benchmark_amount": float(self.benchmark_amount or 0.0),
            "applied_percent": float(self.applied_percent or 0.0),
            "aggregation_allowance": float(self.aggregation_allowance or 0.0),
            "materiality_amount": float(self.materiality_amount or 0.0),
            "performance_percent": float(self.performance_percent or 0.0),
            "performance_materiality_amount": float(self.performance_materiality_amount or 0.0),
            "trivial_percent": float(self.trivial_percent or 0.0),
            "trivial_amount": float(self.trivial_amount or 0.0),
            "components": [
                {
                    "name": c.name,
                    "component_type": c.component_type,
                    "component_benchmark": float(c.component_benchmark or 0.0),
                    "method": c.method,
                    "value_percent_or_amount": float(c.value_percent_or_amount or 0.0),
                    "computed_materiality": float(c.computed_materiality or 0.0),
                    "notes": c.notes,
                }
                for c in self.component_ids
            ],
            "tolerances": [
                {
                    "account_name": t.account_name,
                    "basis": t.basis,
                    "percent": float(t.percent or 0.0),
                    "absolute_amount": float(t.absolute_amount or 0.0),
                    "computed_amount": float(t.computed_amount or 0.0),
                }
                for t in self.tolerance_ids
            ],
            "history": [
                {
                    "changed_by": h.changed_by.name if h.changed_by else False,
                    "changed_date": fields.Datetime.to_string(h.changed_date) if h.changed_date else False,
                    "old_values": json.loads(h.old_values) if h.old_values else {},
                    "note": h.note,
                }
                for h in self.history_ids
            ],
            "notes": self.notes or "",
            "qualitative_adjustments": self.qualitative_adjustments or "",
        }
        return json.dumps(data, indent=2, default=str, ensure_ascii=False)

    def export_to_csv(self, filepath):
        self.ensure_one()
        header_rows = [
            ("Reference", self.name),
            ("Prepared by", self.prepared_by.name if self.prepared_by else ""),
            ("Reviewed by", self.reviewed_by.name if self.reviewed_by else ""),
            ("Date prepared", fields.Date.to_string(self.date_prepared) if self.date_prepared else ""),
            ("Benchmark type", self.benchmark_type),
            ("Benchmark amount", float(self.benchmark_amount or 0.0)),
            ("Applied %", float(self.applied_percent or 0.0)),
            ("Aggregation allowance", float(self.aggregation_allowance or 0.0)),
            ("Materiality amount", float(self.materiality_amount or 0.0)),
            ("Performance %", float(self.performance_percent or 0.0)),
            ("Performance materiality", float(self.performance_materiality_amount or 0.0)),
            ("Trivial %", float(self.trivial_percent or 0.0)),
            ("Trivial amount", float(self.trivial_amount or 0.0)),
        ]
        with open(filepath, mode="w", newline="", encoding="utf-8") as export_file:
            writer = csv.writer(export_file)
            writer.writerow(["Materiality Worksheet Export"])
            for row in header_rows:
                writer.writerow(row)
            writer.writerow([])
            writer.writerow(["Components"])
            writer.writerow(["Name", "Type", "Component Benchmark", "Method", "ValuePercentOrAmount", "ComputedMateriality", "Notes"])
            for component in self.component_ids:
                writer.writerow(
                    [
                        component.name,
                        component.component_type,
                        float(component.component_benchmark or 0.0),
                        component.method,
                        float(component.value_percent_or_amount or 0.0),
                        float(component.computed_materiality or 0.0),
                        component.notes or "",
                    ]
                )
            writer.writerow([])
            writer.writerow(["Tolerances"])
            writer.writerow(["Account", "Basis", "Percent", "AbsoluteAmount", "ComputedAmount"])
            for tolerance in self.tolerance_ids:
                writer.writerow(
                    [
                        tolerance.account_name,
                        tolerance.basis or "",
                        float(tolerance.percent or 0.0),
                        float(tolerance.absolute_amount or 0.0),
                        float(tolerance.computed_amount or 0.0),
                    ]
                )
            writer.writerow([])
            writer.writerow(["History"])
            writer.writerow(["ChangedDate", "ChangedBy", "OldValues", "Note"])
            for history in self.history_ids:
                writer.writerow(
                    [
                        fields.Datetime.to_string(history.changed_date) if history.changed_date else "",
                        history.changed_by.name if history.changed_by else "",
                        history.old_values or "",
                        history.note or "",
                    ]
                )
        return True

    @api.model
    def import_from_json(self, json_str):
        data = json.loads(json_str)
        vals = {
            "planning_id": False,
            "audit_id": False,
            "benchmark_type": data.get("benchmark_type", "pbt"),
            "benchmark_amount": data.get("benchmark_amount", 0.0),
            "currency_id": self.env.company.currency_id.id,
            "applied_percent": data.get("applied_percent", 0.0),
            "performance_percent": data.get("performance_percent", 75.0),
            "trivial_percent": data.get("trivial_percent", 5.0),
            "aggregation_allowance": data.get("aggregation_allowance", 0.0),
            "rationale": data.get("rationale", ""),
            "notes": data.get("notes", ""),
        }
        rec = self.create(vals)
        component_commands = [
            (
                0,
                0,
                {
                    "name": comp.get("name"),
                    "component_type": comp.get("component_type", "subsidiary"),
                    "component_benchmark": comp.get("component_benchmark", 0.0),
                    "method": comp.get("method", "percentage_of_group"),
                    "value_percent_or_amount": comp.get("value_percent_or_amount", 0.0),
                    "notes": comp.get("notes", ""),
                },
            )
            for comp in data.get("components", [])
        ]
        if component_commands:
            rec.component_ids = component_commands
        tolerance_commands = [
            (
                0,
                0,
                {
                    "account_name": tol.get("account_name"),
                    "basis": tol.get("basis", ""),
                    "percent": tol.get("percent", 0.0),
                    "absolute_amount": tol.get("absolute_amount", 0.0),
                },
            )
            for tol in data.get("tolerances", [])
        ]
        if tolerance_commands:
            rec.tolerance_ids = tolerance_commands
        rec._compute_materiality()
        return rec

    def _display_materiality_label(self):
        self.ensure_one()
        symbol = self.currency_id.symbol or ""
        amount = int(self.materiality_amount or 0.0)
        return "%s - %s%s" % ((self.name or "/"), symbol, amount)
