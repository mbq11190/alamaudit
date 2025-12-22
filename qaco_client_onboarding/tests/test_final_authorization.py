from odoo.tests.common import TransactionCase
from odoo import fields, exceptions
import base64

class TestFinalAuthorization(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Onboarding = self.env['qaco.client.onboarding']
        self.PreReq = self.env['qaco.onboarding.predecessor.request']
        self.PreResp = self.env['qaco.onboarding.predecessor.response']
        firm = self.env['audit.firm.name'].create({'name': 'TestFirm', 'code': 'TF'})
        client = self.env['res.partner'].create({'name': 'FinalClient'})
        audit = self.env['qaco.audit'].create({'name': 'A1', 'client_id': client.id, 'firm_name': firm.id})
        self.onboarding = self.Onboarding.create({'audit_id': audit.id, 'legal_name': 'FinalClient', 'principal_business_address': 'Addr', 'business_registration_number': 'P123'})

    def test_block_finalization_when_missing_checks(self):
        # not submitted for review yet
        with self.assertRaises(exceptions.ValidationError):
            # try to call the check directly
            self.onboarding._check_final_authorization_preconditions()

    def test_acceptance_flow_creates_authorization_and_certificate(self):
        # set required fields and checks
        self.onboarding.reporting_period = fields.Date.today()
        self.onboarding.engagement_type = 'audit'
        self.onboarding.fit_proper_confirmed = True
        # independence
        # create an approved declaration to mark compliant (simplified)
        decl = self.env['qaco.onboarding.independence.declaration'].create({'onboarding_id': self.onboarding.id, 'user_id': self.env.uid, 'status': 'approved'})
        # set independence status by computing
        self.onboarding._compute_independence_status()
        # predecessor: set no predecessor name to be treated as NA
        self.onboarding.predecessor_auditor_name = False
        # set fee and assign partner and competence flags
        self.onboarding.proposed_audit_fee = 10000
        self.onboarding.engagement_partner_id = self.env['res.users'].browse(self.env.uid)
        self.onboarding.team_competence_confirmed = True
        self.onboarding.resources_timeline_confirmed = True
        # submit for review then finalize via the wizard
        self.onboarding.action_submit_review()
        # create wizard and confirm
        wiz = self.env['qaco.onboarding.final.authorization.wizard'].create({
            'onboarding_id': self.onboarding.id,
            'decision': 'accept',
            'decision_rationale': 'All checks OK',
            'team_competence_confirmed': True,
            'resources_timeline_confirmed': True,
            'generate_certificate': True,
            'include_summary_pack': True,
        })
        wiz.action_confirm_authorization()
        # After confirmation, state should be partner_approved
        self.assertEqual(self.onboarding.state, 'partner_approved')
        # Acceptance certificate should exist as an attachment
        att = self.env['ir.attachment'].search([('res_model', '=', 'qaco.client.onboarding'), ('res_id', '=', self.onboarding.id), ('mimetype','=','application/pdf')], limit=1)
        self.assertTrue(att, 'A certificate or summary PDF should be attached after authorization')
