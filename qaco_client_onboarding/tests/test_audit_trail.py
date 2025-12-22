from odoo.tests.common import TransactionCase

class TestAuditTrail(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Onboarding = self.env['qaco.client.onboarding']
        firm = self.env['audit.firm.name'].create({'name': 'ATFirm', 'code': 'AT'})
        client = self.env['res.partner'].create({'name': 'ATClient'})
        audit = self.env['qaco.audit'].create({'name': 'A1', 'client_id': client.id, 'firm_name': firm.id})
        self.onboarding = self.Onboarding.create({'audit_id': audit.id, 'legal_name': 'ATClient', 'principal_business_address': 'Addr', 'business_registration_number': 'P123'})

    def test_log_action_creates_entry(self):
        self.onboarding._log_action('test_action', notes='a note', action_type='user')
        entries = self.onboarding.audit_trail_ids.filtered(lambda t: t.action == 'test_action')
        self.assertTrue(entries, 'Audit entry should be created')
        self.assertEqual(entries[0].action_type, 'user')

    def test_override_logging(self):
        self.onboarding._log_action('override_action', notes='override noted', action_type='override', is_override=True, resolution='Resolved by partner')
        entries = self.onboarding.audit_trail_ids.filtered(lambda t: t.action == 'override_action')
        self.assertTrue(entries)
        self.assertTrue(entries[0].is_override)
        self.assertEqual(entries[0].resolution, 'Resolved by partner')
