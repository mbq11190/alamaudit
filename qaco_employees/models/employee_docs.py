from odoo import fields, models


class EmployeeDocs(models.Model):
    _name = "employee.docs"
    _description = "Employee Docs"

    document_name = fields.Selection(
        [
            ("cv", "Employee CV"),
            ("id_card", "Employee Id Card"),
            ("education_certificates", "Education Certificates"),
            ("experience_certificates", "Experience Certificates"),
            ("icap_contract", "ICAP Contract"),
            ("show_cause", "Employee Show Cause"),
            ("resignation", "Employee Resignation"),
            ("noc", "Employee NOC"),
            ("handing_taking_document", "Handing/Taking Document"),
            ("experience_letter", "Experience Letter from QACO"),
        ],
        string="Document Name",
        required=True,
    )
    attachment_ids = fields.Many2many("ir.attachment", string="Attachments")
    no_of_documents = fields.Integer(
        compute="_compute_no_of_documents", string="No of Documents"
    )

    def _compute_no_of_documents(self):
        for record in self:
            record.no_of_documents = len(record.attachment_ids)

    employee_id = fields.Many2one("hr.employee", string="Employee")
