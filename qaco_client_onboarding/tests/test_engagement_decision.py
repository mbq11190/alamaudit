from odoo.tests.common import TransactionCase
from odoo import fields, exceptions

class TestEngagementDecision(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Onboarding = self.env['qaco.client.onboarding']
        self.Decision = self.env['qaco.onboarding.decision']
        firm = self.env['audit.firm.name'].create({'name': 'DecFirm', 'code': 'DF'})
        client = self.env['res.partner'].create({'name': 'DecClient'})
        audit = self.env['qaco.audit'].create({'name': 'A1', 'client_id': client.id, 'firm_name': firm.id})
        self.onboarding = self.Onboarding.create({'audit_id': audit.id, 'legal_name': 'DecClient', 'principal_business_address': 'Addr', 'business_registration_number': 'P123'})

    def test_preconditions_block_accept(self):
        # missing fee and partner assignment -> should block accept creation
        with self.assertRaises(exceptions.ValidationError):
            self.Decision.create({'onboarding_id': self.onboarding.id, 'decision_type': 'accept', 'decision_rationale': 'All good', 'risk_rating': 'low'})

    def test_acceptance_flow_creates_decision_and_memo(self):
        # satisfy required preconditions
        self.onboarding.reporting_period = fields.Date.today()
        self.onboarding.engagement_type = 'audit'
        self.onboarding.fit_proper_confirmed = True
        decl = self.env['qaco.onboarding.independence.declaration'].create({'onboarding_id': self.onboarding.id, 'user_id': self.env.uid, 'status': 'approved'})
        self.onboarding._compute_independence_status()
        self.onboarding.predecessor_auditor_name = False
        self.onboarding.proposed_audit_fee = 10000
        self.onboarding.engagement_partner_id = self.env['res.users'].browse(self.env.uid)
        self.onboarding.team_competence_confirmed = True
        self.onboarding.resources_timeline_confirmed = True
        # create decision
        dec = self.Decision.create({'onboarding_id': self.onboarding.id, 'decision_type': 'accept', 'decision_rationale': 'Clear', 'risk_rating': 'low'})
        self.assertEqual(dec.version, 1)
        # create superseding decision
        dec2 = self.Decision.create({'onboarding_id': self.onboarding.id, 'decision_type': 'accept_conditions', 'decision_rationale': 'Conditional', 'risk_rating': 'moderate'})
        self.assertEqual(dec2.version, 2)
        dec.refresh()
        self.assertEqual(dec.superseded_by_id.id, dec2.id)
        # onboarding.latest_decision_id should point to latest
        self.onboarding.refresh()
        self.assertEqual(self.onboarding.latest_decision_id.id, dec2.id)
        # generate memo
        att = dec2.action_generate_decision_memo()
        self.assertTrue(att, 'Decision memo should be generated and attached')
        # apply decision - should set onboarding to partner_approved
        dec2.action_apply_decision()
        self.onboarding.refresh()
        self.assertEqual(self.onboarding.state, 'partner_approved')

    def test_prohibitive_requires_quality_approval(self):
        # satisfy preconditions
        self.onboarding.reporting_period = fields.Date.today()
        self.onboarding.engagement_type = 'audit'
        self.onboarding.fit_proper_confirmed = True
        self.onboarding.proposed_audit_fee = 10000
        self.onboarding.engagement_partner_id = self.env['res.users'].browse(self.env.uid)
        self.onboarding.team_competence_confirmed = True
        self.onboarding.resources_timeline_confirmed = True
        with self.assertRaises(exceptions.ValidationError):
            self.Decision.create({'onboarding_id': self.onboarding.id, 'decision_type': 'accept', 'decision_rationale': 'Bad', 'risk_rating': 'prohibitive'})
        # With quality approval it should allow
        q = self.env['res.users'].create({'name': 'Quality', 'login': 'qual@example.com'})
        dec = self.Decision.create({'onboarding_id': self.onboarding.id, 'decision_type': 'accept', 'decision_rationale': 'Approved by quality', 'risk_rating': 'prohibitive', 'quality_approval_id': q.id})
        self.assertTrue(dec.id)

    def test_locked_records_prevent_write(self):
        # create minimal valid decision
        self.onboarding.reporting_period = fields.Date.today()
        self.onboarding.engagement_type = 'audit'
        self.onboarding.fit_proper_confirmed = True
        self.onboarding.proposed_audit_fee = 10000
        self.onboarding.engagement_partner_id = self.env['res.users'].browse(self.env.uid)
        self.onboarding.team_competence_confirmed = True
        self.onboarding.resources_timeline_confirmed = True
        dec = self.Decision.create({'onboarding_id': self.onboarding.id, 'decision_type': 'decline', 'decision_rationale': 'Reason', 'risk_rating': 'high'})
        dec.write({'locked': True})
        with self.assertRaises(exceptions.ValidationError):
            dec.write({'decision_rationale': 'Change attempt'})
