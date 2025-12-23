from odoo.tests.common import TransactionCase


class TestRegistryModels(TransactionCase):
    def test_hr_employee_transfer_model_registered(self):
        # Ensure the hr.employee.transfer model exists in the registry
        self.assertTrue(
            'hr.employee.transfer' in self.env.registry.models,
            'hr.employee.transfer model must be registered',
        )

    def test_res_users_field_is_redirect_home(self):
        # Check that res.users has the is_redirect_home field provided by web_responsive
        fields = self.env['ir.model.fields'].search([
            ('model', '=', 'res.users'),
            ('name', '=', 'is_redirect_home'),
        ])
        self.assertTrue(fields, 'res.users.is_redirect_home field should exist')
