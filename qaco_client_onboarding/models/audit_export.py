# -*- coding: utf-8 -*-
import base64
import csv
import io
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class AuditExportWizard(models.TransientModel):
    _name = "qaco.onboarding.audit.export.wizard"
    _description = "Export Audit Trail"

    date_from = fields.Date(string="From")
    date_to = fields.Date(string="To")
    action_type = fields.Selection(
        [
            ("activity", "Activity"),
            ("override", "Override"),
            ("system", "System"),
            ("user", "User"),
        ],
        string="Action type",
    )
    user_id = fields.Many2one("res.users", string="User")
    include_overrides = fields.Boolean(string="Include overrides", default=True)
    export_format = fields.Selection(
        [("csv", "CSV"), ("pdf", "PDF")], string="Export format", default="csv"
    )

    def _build_domain(self):
        domain = []
        if self.date_from:
            domain.append(("create_date", ">=", self.date_from))
        if self.date_to:
            # include end of day
            domain.append(("create_date", "<=", self.date_to))
        if self.action_type:
            domain.append(("action_type", "=", self.action_type))
        if self.user_id:
            domain.append(("user_id", "=", self.user_id.id))
        if not self.include_overrides:
            domain.append(("is_override", "=", False))
        return domain

    def action_export(self):
        domain = self._build_domain()
        entries = self.env["qaco.onboarding.audit.trail"].search(
            domain, order="create_date"
        )
        if self.export_format == "csv":
            return self._export_csv(entries)
        else:
            return self._export_pdf(entries)

    def _export_csv(self, entries):
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "Timestamp",
                "User",
                "Action",
                "Type",
                "Override",
                "Resolution",
                "Notes",
                "Onboarding",
                "Related model",
                "Related id",
            ]
        )
        for e in entries:
            writer.writerow(
                [
                    e.create_date,
                    e.user_id.name or "",
                    e.action or "",
                    e.action_type or "",
                    "Yes" if e.is_override else "No",
                    e.resolution or "",
                    e.notes or "",
                    e.onboarding_id.name or "",
                    e.related_model or "",
                    e.related_res_id or "",
                ]
            )
        csv_data = output.getvalue().encode("utf-8")
        name = "onboarding_audit_export_%s.csv" % (
            fields.Date.context_today(self).strftime("%Y%m%d")
        )
        att = self.env["ir.attachment"].create(
            {
                "name": name,
                "type": "binary",
                "datas": base64.b64encode(csv_data).decode("ascii"),
                "mimetype": "text/csv",
            }
        )
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/%s?download=true" % att.id,
            "target": "self",
        }

    def _export_pdf(self, entries):
        data = {"entry_ids": entries.ids}
        return self.env.ref(
            "qaco_client_onboarding.report_audit_snapshot"
        ).report_action(entries, data=data)


class AuditResolutionWizard(models.TransientModel):
    _name = "qaco.onboarding.audit.resolution.wizard"
    _description = "Add Resolution to Audit Entry"

    audit_id = fields.Many2one("qaco.onboarding.audit.trail", required=True)
    resolution = fields.Text(string="Resolution / Notes", required=True)
    mark_override = fields.Boolean(string="Mark as override", default=True)

    def action_apply_resolution(self):
        self.ensure_one()
        audit = self.audit_id
        audit.write({"resolution": self.resolution, "is_override": self.mark_override})
        # add audit entry to trail documenting the resolution action
        audit.onboarding_id._log_action(
            "audit resolution added",
            notes=self.resolution,
            action_type="override",
            is_override=True,
            related_model="qaco.onboarding.audit.trail",
            related_res_id=audit.id,
        )
        return {"type": "ir.actions.act_window_close"}
