from odoo import fields, models, _


class AuditInternalControl(models.Model):
    _name = 'audit.internal.control'
    _description = 'Internal Control Evaluation'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'audit.ai.helper.mixin', 'audit.collaboration.mixin']

    name = fields.Char(default=lambda self: _('Control Cycle Review'), tracking=True)
    cycle = fields.Selection([
        ('revenue', 'Revenue'),
        ('purchases', 'Purchases'),
        ('payroll', 'Payroll'),
        ('inventory', 'Inventory'),
        ('financial_reporting', 'Financial Reporting'),
    ], required=True, tracking=True)
    narratives = fields.Text(tracking=True)
    control_design_assessment = fields.Selection([
        ('strong', 'Strong'),
        ('adequate', 'Adequate'),
        ('weak', 'Weak'),
    ], default='adequate', tracking=True)
    implementation_status = fields.Selection([
        ('implemented', 'Implemented'),
        ('partial', 'Partially Implemented'),
        ('not_implemented', 'Not Implemented'),
    ], default='implemented', tracking=True)
    walkthrough_notes = fields.Text()
    test_of_controls_results = fields.Text()
    deficiency_classification = fields.Selection([
        ('none', 'No Deficiency'),
        ('significant', 'Significant Deficiency'),
        ('material', 'Material Weakness'),
    ], default='none', tracking=True)
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'audit_control_attachment_rel',
        'control_id',
        'attachment_id',
        string='Control Documents',
    )
    assigned_user_ids = fields.Many2many('res.users', string='Assigned Team', tracking=True)

    def ai_evaluate_internal_control_design(self):
        for record in self:
            prompt = f"""
                Evaluate the internal control design for the {record.cycle} cycle.
                Narratives: {record.narratives}
                Walkthrough: {record.walkthrough_notes}
                Test Results: {record.test_of_controls_results}
                Classify deficiency and recommend improvements referencing ISA 330.
            """
            record.test_of_controls_results = record._call_openai(prompt)
        return True
