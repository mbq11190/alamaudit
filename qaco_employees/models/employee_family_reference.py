from odoo import fields, models


class EmployeeFamilyReference(models.Model):
    _name = "employee.family.reference"
    _description = "Employee Family/Reference"

    relation = fields.Selection(
        [
            ("father", "Father"),
            ("mother", "Mother"),
            ("brother", "Brother"),
            ("sister", "Sister"),
            ("referring_person", "Referring Person"),
            ("wife", "Wife"),
            ("husband", "Husband"),
        ],
        string="Relation",
        required=True,
    )
    partner_id = fields.Many2one("res.partner", string="Name", required=True)
    occupation = fields.Char(string="Occupation")
    contact_no = fields.Char(
        related="partner_id.phone", string="Contact No", readonly=True
    )
    employee_id = fields.Many2one("hr.employee", string="Employee")
    designation = fields.Char(string="Designation")
