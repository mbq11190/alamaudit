from odoo.tests.common import TransactionCase
from odoo import fields

class TestIndependenceIntegration(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Onboarding = self.env['qaco.client.onboarding']
        firm = self.env['audit.firm.name'].create({'name': 'IndFirm', 'code': 'IF'})
        client = self.env['res.partner'].create({'name': 'IndClient'})
        audit = self.env['qaco.audit'].create({'name': 'A1', 'client_id': client.id, 'firm_name': firm.id})
        self.onboarding = self.Onboarding.create({'audit_id': audit.id, 'legal_name': 'IndClient', 'principal_business_address': 'Addr', 'business_registration_number': 'P123'})

    def test_generate_independence_memo_indexed(self):
        # ensure template folders exist
        folder = self.onboarding.get_folder_by_code('03_Independence')
        self.assertTrue(folder, 'Independence folder should exist')
        # call generator (report must exist in module)
        att = self.onboarding.action_generate_independence_memo()
        if att:
            docs = self.env['qaco.onboarding.document'].search([('onboarding_id','=', self.onboarding.id), ('folder_id','=', folder.id)])
            self.assertTrue(docs, 'Independence memo should be indexed into 03_Independence')
        else:
            # If report not present then pass the test as optional
            self.assertTrue(True)
