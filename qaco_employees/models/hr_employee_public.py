from odoo import fields, models


class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    designation_id = fields.Many2one(
        related="employee_id.designation_id",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    date_of_joining = fields.Date(
        related="employee_id.date_of_joining",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    date_of_articles_registration = fields.Date(
        related="employee_id.date_of_articles_registration",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    date_of_articles_end = fields.Date(
        related="employee_id.date_of_articles_end",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    date_of_leaving = fields.Date(
        related="employee_id.date_of_leaving",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    hiring_partner_id = fields.Many2one(
        related="employee_id.hiring_partner_id",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    referring_person_id = fields.Many2one(
        related="employee_id.referring_person_id",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    technical_supervisor_id = fields.Many2one(
        related="employee_id.technical_supervisor_id",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    previous_firm_id = fields.Many2one(
        related="employee_id.previous_firm_id",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    joining_reason_noc = fields.Text(
        related="employee_id.joining_reason_noc",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    leaves_already_availed = fields.Integer(
        related="employee_id.leaves_already_availed",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    date_of_noc_joining = fields.Date(
        related="employee_id.date_of_noc_joining",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    leaving_reason_noc = fields.Text(
        related="employee_id.leaving_reason_noc",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    leaves_availed_in_qaco = fields.Integer(
        related="employee_id.leaves_availed_in_qaco",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    crn_no = fields.Char(
        related="employee_id.crn_no",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    date_of_noc_leaving = fields.Date(
        related="employee_id.date_of_noc_leaving",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    noc_approving_partner_id = fields.Many2one(
        related="employee_id.noc_approving_partner_id",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    allocation = fields.Boolean(
        related="employee_id.allocation",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    region_id = fields.Many2one(
        related="employee_id.region_id",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    partner_id = fields.Many2one(
        related="employee_id.partner_id",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    was_unallocated = fields.Boolean(
        related="employee_id.was_unallocated",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    ca_qualification = fields.Selection(
        related="employee_id.ca_qualification",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    masters = fields.Selection(
        related="employee_id.masters",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    graduation = fields.Selection(
        related="employee_id.graduation",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    inter = fields.Selection(
        related="employee_id.inter",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    other_education = fields.Text(
        related="employee_id.other_education",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    conveyance = fields.Selection(
        related="employee_id.conveyance",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    reg_firm_name = fields.Selection(
        related="employee_id.reg_firm_name",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    reg_status = fields.Selection(
        related="employee_id.reg_status",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    allocation_status = fields.Selection(
        related="employee_id.allocation_status",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    residence = fields.Selection(
        related="employee_id.residence",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    latest_deputation_client_id = fields.Many2one(
        related="employee_id.latest_deputation_client_id",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
    is_absent_today = fields.Boolean(
        related="employee_id.is_absent_today",
        readonly=True,
        groups="qaco_employees.group_qaco_employee_trainee",
    )
