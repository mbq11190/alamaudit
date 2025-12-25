# -*- coding: utf-8 -*-
from odoo import fields, models


class QacoPayroll(models.Model):
    _name = "qaco.payroll"
    _description = "QACO Payroll"

    employee_id = fields.Many2one("hr.employee", string="Employee", required=True)
    month_name = fields.Char(string="Month Name")
    date_from = fields.Date(string="Date From")
    date_to = fields.Date(string="Date To")
    state = fields.Selection([
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("approved", "Approved"),
    ], default="draft")


class QacoPayrollLine(models.Model):
    _name = "qaco.payroll.line"
    _description = "QACO Payroll Line"

    payroll_id = fields.Many2one("qaco.payroll", string="Payroll", required=True, ondelete="cascade")
    employee_id = fields.Many2one("hr.employee", string="Employee", required=True)
    department_id = fields.Many2one("hr.department", string="Department")
    designation_id = fields.Many2one("employee.designation", string="Designation")
    gross_salary = fields.Float(string="Gross Salary")
    allowance_amount = fields.Float(string="Allowance Amount")
    attendance_days = fields.Integer(string="Attendance Days")
    leave_deduction_amount = fields.Float(string="Leave Deduction Amount")
    net_salary = fields.Float(string="Net Salary")