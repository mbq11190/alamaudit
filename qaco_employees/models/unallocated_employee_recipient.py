from odoo import fields, models


class UnallocatedEmployeeRecipient(models.Model):
    _name = "unallocated.employee.recipient"
    _description = "Unallocated Employee Email Recipient"
    _rec_name = "employee_id"

    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        required=True,
    )
