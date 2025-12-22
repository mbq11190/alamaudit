from odoo.tests.common import TransactionCase
from odoo import exceptions
from datetime import date

class TestPredecessorAuditor(TransactionCase):
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

    def test_missing_request_blocks_approval(self):
        self.onboarding.action_submit_review()
        with self.assertRaises(exceptions.ValidationError):
            self.onboarding.action_partner_approve()

    def test_request_and_response_allows_approval(self):
        # create request
        req = self.PreReq.create({'onboarding_id': self.onboarding.id, 'predecessor_firm': 'OldAuditor', 'sent_date': fields.Datetime.now(), 'sent_mode': 'email', 'sent_by': self.env.uid})
        # add response
        resp = self.PreResp.create({'onboarding_id': self.onboarding.id, 'request_id': req.id, 'response_received': True, 'response_date': date.today(), 'conclusion': 'proceed'})
        req.response_id = resp.id
        # ensure checklist and partner assigned
        self.onboarding._populate_regulator_checklist()
        for line in self.onboarding.regulator_checklist_line_ids:
            if line.mandatory:
                line.completed = True
        self.onboarding.engagement_partner_id = self.env['res.users'].browse(self.env.uid)
        self.onboarding.action_submit_review()
        self.onboarding.action_partner_approve()
        self.assertEqual(self.onboarding.state, 'partner_approved')

    def test_adverse_response_triggers_escalation_and_blocks(self):
        req = self.PreReq.create({'onboarding_id': self.onboarding.id, 'predecessor_firm': 'OldAuditor', 'sent_date': fields.Datetime.now(), 'sent_mode': 'email', 'sent_by': self.env.uid})
        resp = self.PreResp.create({'onboarding_id': self.onboarding.id, 'request_id': req.id, 'response_received': True, 'response_date': date.today(), 'conclusion': 'do_not_proceed', 'issue_integrity': True})
        req.response_id = resp.id
        # attempt approval should raise because do_not_proceed
        self.onboarding.action_submit_review()
        with self.assertRaises(exceptions.ValidationError):
            self.onboarding.action_partner_approve()
