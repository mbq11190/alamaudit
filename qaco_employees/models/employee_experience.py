from odoo import api, fields, models


class EmployeeExperience(models.Model):
    _name = "employee.experience"
    _description = "Employee Experience"

    organisation_id = fields.Many2one("res.partner", string="Organisation")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    no_of_years = fields.Float(
        compute="_compute_no_of_years", string="No of Years"
    )  # Change this line
    employee_id = fields.Many2one("hr.employee", string="Employee")

    @api.depends("start_date", "end_date")
    def _compute_no_of_years(self):
        for record in self:
            if record.start_date and record.end_date:
                record.no_of_years = (record.end_date - record.start_date).days / 365.0
            else:
                record.no_of_years = 0.0
