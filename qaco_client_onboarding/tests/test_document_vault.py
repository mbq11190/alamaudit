from odoo.tests.common import TransactionCase
from odoo import fields

class TestDocumentVault(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Onboarding = self.env['qaco.client.onboarding']
        self.Folder = self.env['qaco.onboarding.document.folder']
        firm = self.env['audit.firm.name'].create({'name': 'DocFirm', 'code': 'DF'})
        client = self.env['res.partner'].create({'name': 'DocClient'})
        audit = self.env['qaco.audit'].create({'name': 'A1', 'client_id': client.id, 'firm_name': firm.id})
        self.onboarding = self.Onboarding.create({'audit_id': audit.id, 'legal_name': 'DocClient', 'principal_business_address': 'Addr', 'business_registration_number': 'P123'})

    def test_folder_autocreation(self):
        self.assertTrue(self.onboarding.document_folder_ids, 'Default document folders should be created on onboarding creation')
        codes = self.onboarding.document_folder_ids.mapped('code')
        self.assertIn('04_Predecessor', codes)
        self.assertIn('08_Final_Authorization', codes)

    def test_predecessor_pack_indexed_to_folder(self):
        PreReq = self.env['qaco.onboarding.predecessor.request']
        PreResp = self.env['qaco.onboarding.predecessor.response']
        req = PreReq.create({'onboarding_id': self.onboarding.id, 'predecessor_firm': 'OldAuditor', 'sent_date': fields.Datetime.now(), 'sent_mode': 'email', 'sent_by': self.env.uid})
        resp = PreResp.create({'onboarding_id': self.onboarding.id, 'request_id': req.id, 'response_received': True, 'response_date': fields.Date.today(), 'conclusion': 'proceed'})
        req.response_id = resp.id
        # create small attachments and run bundle generation
        small_att = self.env['ir.attachment'].create({
            'name': 'auth.pdf',
            'type': 'binary',
            'datas': 'JVBERi0xLjE=',
            'mimetype': 'application/pdf',
        })
        req.authorization_attachment = small_att.id
        bundle = req.action_generate_pack_bundle()
        # Check there is a qaco.onboarding.document record in predecessor folder
        folder = self.onboarding.get_folder_by_code('04_Predecessor')
        docs = self.env['qaco.onboarding.document'].search([('onboarding_id','=', self.onboarding.id), ('folder_id','=', folder.id)])
        self.assertTrue(docs, 'Merged pack should be indexed into predecessor folder')
