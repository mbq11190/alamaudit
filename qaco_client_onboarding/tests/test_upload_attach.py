from odoo.tests.common import TransactionCase
import base64


class TestUploadAttach(TransactionCase):
    def setUp(self):
        super().setUp()
        self.onboarding_model = self.env['qaco.client.onboarding']
        self.Template = self.env['qaco.onboarding.template.document']
        self.Attached = self.env['qaco.onboarding.attached.template']
        # minimal onboarding
        self.audit = self.env['qaco.audit'].create({'client_id': self.env.ref('base.res_partner_1').id})
        self.onb = self.onboarding_model.create({'audit_id': self.audit.id, 'legal_name': 'T', 'principal_business_address': 'A', 'business_registration_number': 'B', 'entity_type': 'pic', 'primary_regulator': 'secp', 'financial_framework': 'ifrs', 'management_integrity_rating': 'medium'})

    def test_upload_and_attach(self):
        # prepare a small file
        content = b'Hello world'
        b64 = base64.b64encode(content).decode('utf-8')
        res = self.onb.upload_and_attach('test.txt', b64)
        # check attached created
        attached = self.Attached.search([('onboarding_id', '=', self.onb.id), ('attached_filename', '=', 'test.txt')])
        self.assertTrue(attached, 'Attached template should be created')
