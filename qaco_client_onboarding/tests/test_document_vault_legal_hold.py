from odoo.tests.common import TransactionCase
from odoo import fields, exceptions

class TestDocumentVaultLegalHold(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Onboarding = self.env['qaco.client.onboarding']
        firm = self.env['audit.firm.name'].create({'name': 'HoldFirm', 'code': 'HF'})
        client = self.env['res.partner'].create({'name': 'HoldClient'})
        audit = self.env['qaco.audit'].create({'name': 'A1', 'client_id': client.id, 'firm_name': firm.id})
        self.onboarding = self.Onboarding.create({'audit_id': audit.id, 'legal_name': 'HoldClient', 'principal_business_address': 'Addr', 'business_registration_number': 'P123'})

    def test_legal_hold_blocks_deletion(self):
        doc = self.env['qaco.onboarding.document'].create({'onboarding_id': self.onboarding.id, 'name': 'TestDoc', 'file': 'dGVzdA==', 'file_name': 'test.txt'})
        doc.action_set_legal_hold(True)
        with self.assertRaises(exceptions.ValidationError):
            doc.unlink()
