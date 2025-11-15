# Copyright 2025
# Prepared referencing ISA 300 para 11 and ICAP QCR guidance.
from __future__ import annotations

from typing import Any, Dict, Optional

from odoo import api, fields, models, _


class AuditEvidenceLog(models.Model):
    """Immutable audit trail entries for planning artefacts.

    The log structure fulfils ISA 300 para 11 (documentation of key planning
    decisions) and ICAP QCR documentation expectations by capturing the user,
    timestamp, before/after snapshot, and authoritative citation for each
    significant action. Entries are export-ready for SECP / PSX reviews.
    """

    _name = "audit.evidence.log"
    _description = "Audit Evidence Log"
    _order = "create_date desc"

    name = fields.Char(string="Reference", required=True)
    model_name = fields.Char(string="Model")
    res_id = fields.Integer(string="Record ID")
    field_name = fields.Char(string="Field")
    action_type = fields.Selection(
        [
            ("create", "Create"),
            ("update", "Update"),
            ("state", "State Change"),
            ("approval", "Approval"),
            ("export", "Export"),
            ("reminder", "Reminder"),
        ],
        string="Action",
        required=True,
    )
    before_value = fields.Text(string="Before Snapshot")
    after_value = fields.Text(string="After Snapshot")
    note = fields.Text(string="Justification / Narrative")
    standard_reference = fields.Char(
        string="Authority Reference",
        help="Stores citations such as 'ISA 300 para 11' to maintain traceability.",
    )
    user_id = fields.Many2one("res.users", string="Performed By", default=lambda self: self.env.user)
    exported = fields.Boolean(string="Included in Latest Export", default=False)

    @api.model
    def log_event(
        self,
        name: str,
        model_name: str,
        res_id: int,
        action_type: str,
        note: str,
        standard_reference: str,
        field_name: Optional[str] = None,
        before_value: Optional[str] = None,
        after_value: Optional[str] = None,
    ) -> "AuditEvidenceLog":
        """Central helper to keep audit trail creation consistent.

        Args:
            name: Short reference displayed to reviewers.
            model_name: Technical model name.
            res_id: Target record database identifier.
            action_type: Category of change, e.g., 'state'.
            note: Human-readable explanation citing the judgement exercised.
            standard_reference: Citation satisfying ISA/ICAP/SECP traceability.
            field_name: Optional field reference.
            before_value: Optional snapshot before change.
            after_value: Optional snapshot after change.
        """

        return self.sudo().create(
            {
                "name": name,
                "model_name": model_name,
                "res_id": res_id,
                "action_type": action_type,
                "note": note,
                "standard_reference": standard_reference,
                "field_name": field_name,
                "before_value": before_value,
                "after_value": after_value,
            }
        )

    def export_payload(self) -> Dict[str, Any]:
        """Return a regulator-ready payload structure.

        This helper aggregates the evidence record in a machine readable
        dictionary that can be consumed by SECP / PSX APIs once wired. Keeping
        the method local simplifies future connector work (# TODO)."""

        self.ensure_one()
        return {
            "reference": self.name,
            "model": self.model_name,
            "res_id": self.res_id,
            "action": self.action_type,
            "note": self.note,
            "standard": self.standard_reference,
            "timestamp": fields.Datetime.to_string(self.create_date),
            "user": self.user_id.name,
        }
