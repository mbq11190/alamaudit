from odoo import models, fields, api



class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Add new fields
    designation_id = fields.Many2one('employee.designation', string='Designation', tracking=True)
    date_of_joining = fields.Date(string='Date of Joining', tracking=True)
    date_of_articles_registration = fields.Date(string='Date of Articles Registration', tracking=True)
    date_of_articles_end = fields.Date(string='Date of Articles End', tracking=True)
    date_of_leaving = fields.Date(string='Date of Leaving', tracking=True)
    hiring_partner_id = fields.Many2one('res.partner', string='Hiring Partner', tracking=True)
    referring_person_id = fields.Many2one('res.partner', string='Referring Person', tracking=True)
    technical_supervisor_id = fields.Many2one('res.partner', string='Technical Supervisor', tracking=True)
    previous_firm_id = fields.Many2one('res.partner', string='Previous Firm', tracking=True)
    joining_reason_noc = fields.Text(string='Reason of NOC (Joining)', tracking=True)
    leaves_already_availed = fields.Integer(string='No of Leaves Already Availed', tracking=True)
    date_of_noc_joining = fields.Date(string='Date of NOC Joining', tracking=True)
    leaving_reason_noc = fields.Text(string='Reason of NOC (Leaving)', tracking=True)
    leaves_availed_in_qaco = fields.Integer(string='No of Leaves Availed in QACO', tracking=True)
    crn_no = fields.Char(string='CRN No', tracking=True)
    date_of_noc_leaving = fields.Date(string='Date of NOC Leaving', tracking=True)
    noc_approving_partner_id = fields.Many2one('res.partner', string='NOC Approving Partner Name', tracking=True)
    family_reference_ids = fields.One2many('employee.family.reference', 'employee_id', string='Family/References', tracking=True)
    docs_ids = fields.One2many('employee.docs', 'employee_id', string='Employee Docs')
    allocation = fields.Boolean(string='Available for Allocation', tracking=True)
    region_id = fields.Many2one('qaco.region', 'Residence Area', tracking=True)
    partner_id = fields.Many2one('hr.employee', string='Employee Partner', tracking=True)  # New field for Partner
    was_unallocated = fields.Boolean(string="Previously Unallocated", default=False, tracking=True)
    address_id = fields.Many2one(
        'res.partner',
        string="Deputation Address",
        tracking=True  # Enables tracking for chatter messages
    )
    department_id = fields.Many2one(
        'hr.department',
        string="Department",
        tracking=True  # Enables tracking for chatter messages
    )

    # Add new fields for Education
    ca_qualification = fields.Selection([
        ('caf_passed', 'CAF Passed'),
        ('caf_not_passed', 'CAF Not Passed'),
        ('cfap_qualified', 'CFAP Qualified'),
        ('ca_qualified', 'CA Qualified'),
    ], string='CA Qualification', tracking=True)

    masters = fields.Selection([
        ('ma', 'MA'),
        ('mcom', 'MCOM'),
        ('msc', 'MSC'),
        ('other', 'Other'),
    ], string='Masters', tracking=True)

    graduation = fields.Selection([
        ('ba', 'BA'),
        ('bcom', 'BCOM'),
        ('other', 'Other'),
    ], string='Graduation', tracking=True)

    inter = fields.Selection([
        ('fa', 'FA'),
        ('fsc', 'FSC'),
        ('a_levels', 'A Levels'),
        ('other', 'Other'),
    ], string='Inter', tracking=True)

    other_education = fields.Text(string='Other', tracking=True)

    # Add new fields for Experience
    experience_ids = fields.One2many('employee.experience', 'employee_id', string='Experience', tracking=True)

    conveyance = fields.Selection([
        ('metro', 'Metro'),
        ('bike', 'Bike'),
        ('car', 'Car'),
    ], string='Conveyance', tracking=True)

    reg_firm_name = fields.Selection([
        ('QACO', 'QACO'),
        ('Bakertilly', 'Bakertilly'),
    ], string='Registration Firm Name', tracking=True)

    reg_status = fields.Selection([
        ('Registered', 'Registered'),
        ('Registration Submitted', 'Registration Submitted'),
        ('Un-Registered', 'Un-Registered'),
    ], string='Registration Status', tracking=True)

    allocation_status = fields.Selection([
        ('Allocated', 'Allocated'),
        ('Un-Allocated', 'Un-Allocated'),
    ], string='Allocation Status', tracking=True)

    residence = fields.Selection([
        ('house', 'House'),
        ('hostel', 'Hostel'),
    ], string='Residence', tracking=True)

    transfer_ids = fields.One2many(
        'hr.employee.transfer',
        'employee_id',
        string="Transfers History"
    )
    latest_deputation_client_id = fields.Many2one(
        'res.partner',
        string="Current Deputation Client",
        compute='_compute_latest_deputation_client',
        store=True
    )

    @api.depends('transfer_ids', 'transfer_ids.state', 'transfer_ids.transfer_date_from',
                 'transfer_ids.transfer_date_to', 'transfer_ids.to_client_id')
    def _compute_latest_deputation_client(self):
        transfers = self.env['hr.employee.transfer'].search([
            ('employee_id', 'in', self.ids),
            ('state', 'in', ['approved', 'returned'])
        ], order='id desc')
        latest_map = {}
        for tr in transfers:
            latest_map.setdefault(tr.employee_id.id, tr)

        unallocated_client = self.env['res.partner'].search([('name', '=', 'UNALLOCATED')], limit=1)

        for employee in self:
            tr = latest_map.get(employee.id)
            if not tr:
                employee.latest_deputation_client_id = False
            elif tr.state == 'approved':
                employee.latest_deputation_client_id = tr.to_client_id.id
            else:
                employee.latest_deputation_client_id = unallocated_client.id if unallocated_client else False

    on_leave_today = fields.Boolean(string="On Leave Today", compute='_compute_on_leave_today', store=False)


    @api.depends_context('uid')
    def _compute_on_leave_today(self):
        today = fields.Date.today()
        leaves = self.env['hr.leave'].search([
            ('employee_id', 'in', self.ids),
            ('state', '=', 'validate'),
            ('request_date_from', '<=', today),
            ('request_date_to', '>=', today),
        ])
        leave_map = {l.employee_id.id: True for l in leaves}
        for emp in self:
            emp.on_leave_today = leave_map.get(emp.id, False)

