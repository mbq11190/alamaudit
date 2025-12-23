from odoo import fields, models


class EmployeeDesignation(models.Model):
    _name = "employee.designation"
    _description = "Employee Designation"

    name = fields.Char(string="Designation", required=True)
