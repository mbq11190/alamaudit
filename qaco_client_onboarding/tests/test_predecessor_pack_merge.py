from odoo.tests.common import TransactionCase
from odoo import fields
import base64

MINIMAL_PDF = b"%PDF-1.1\n1 0 obj<<>>endobj\ntrailer\n<<>>\n%%EOF\n"

class TestPredecessorPackMerge(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Onboarding = self.env['qaco.client.onboarding']
        self.PreReq = self.env['qaco.onboarding.predecessor.request']
        self.PreResp = self.env['qaco.onboarding.predecessor.response']
        # baseline objects
        firm = self.env['audit.firm.name'].create({'name': 'TestFirm', 'code': 'TF'})
        client = self.env['res.partner'].create({'name': 'PredClient'})
        audit = self.env['qaco.audit'].create({'name': 'A1', 'client_id': client.id, 'firm_name': firm.id})
        self.onboarding = self.Onboarding.create({'audit_id': audit.id, 'legal_name': 'PredClient', 'principal_business_address': 'Addr', 'business_registration_number': 'P123', 'predecessor_auditor_name': 'OldAuditor'})

    def _create_pdf_attachment(self, name='small.pdf', size=None):
        data = MINIMAL_PDF
        if size and size > len(data):
            data = data + b"\n" * (size - len(data))
        attach = self.env['ir.attachment'].create({
            'name': name,
            'type': 'binary',
            'datas': base64.b64encode(data).decode('ascii'),
            'mimetype': 'application/pdf',
            'public': False,
        })
        # Some tests rely on file_size being set; set it manually if available
        try:
            attach.file_size = len(data)
        except Exception:
            pass
        return attach

    def test_merge_small_pdf_attachments_into_bundle(self):
        # create request and response
        req = self.PreReq.create({'onboarding_id': self.onboarding.id, 'predecessor_firm': 'OldAuditor', 'sent_date': fields.Datetime.now(), 'sent_mode': 'email', 'sent_by': self.env.uid})
        # create small pdf attachments (below threshold)
        small_att = self._create_pdf_attachment('auth.pdf', size=1024)
        req.authorization_attachment = small_att.id
        resp = self.PreResp.create({'onboarding_id': self.onboarding.id, 'request_id': req.id, 'response_received': True, 'response_date': fields.Date.today(), 'conclusion': 'proceed'})
        resp.attachment_id = self._create_pdf_attachment('resp.pdf', size=1024).id
        req.response_id = resp.id
        # ensure threshold is large enough
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_param('qaco_client_onboarding.pack_attachment_max_kb', '512')
        # generate bundle
        bundle = req.action_generate_pack_bundle()
        self.assertTrue(bundle, 'Bundle attachment should be created')
        self.assertEqual(bundle.mimetype, 'application/pdf')
        self.assertTrue(int(bundle.file_size) > 0)

    def test_skip_large_attachments(self):
        req = self.PreReq.create({'onboarding_id': self.onboarding.id, 'predecessor_firm': 'OldAuditor', 'sent_date': fields.Datetime.now(), 'sent_mode': 'email', 'sent_by': self.env.uid})
        large_att = self._create_pdf_attachment('large.pdf', size=600 * 1024)  # 600 KB
        req.authorization_attachment = large_att.id
        resp = self.PreResp.create({'onboarding_id': self.onboarding.id, 'request_id': req.id, 'response_received': True, 'response_date': fields.Date.today(), 'conclusion': 'proceed'})
        resp.attachment_id = self._create_pdf_attachment('resp2.pdf', size=600 * 1024).id
        req.response_id = resp.id
        icp = self.env['ir.config_parameter'].sudo()
        icp.set_param('qaco_client_onboarding.pack_attachment_max_kb', '512')
        bundle = req.action_generate_pack_bundle()
        # the created bundle should exist but its description should note skipped files
        self.assertTrue(bundle.description and 'Skipped' in bundle.description)
