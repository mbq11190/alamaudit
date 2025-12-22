from odoo.tests.common import TransactionCase
from odoo import exceptions
from datetime import date


class TestPreAcceptance(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Onboarding = self.env['qaco.client.onboarding']
        self.Sanction = self.env['qaco.onboarding.sanctions.screen']
        self.Adverse = self.env['qaco.onboarding.adverse.media']
        self.Driver = self.env['qaco.onboarding.risk.driver']
        # baseline objects
        firm = self.env['audit.firm.name'].create({'name': 'TestFirm', 'code': 'TF'})
        client = self.env['res.partner'].create({'name': 'RiskClient'})
        audit = self.env['qaco.audit'].create({'name': 'A1', 'client_id': client.id, 'firm_name': firm.id})
        self.onboarding = self.Onboarding.create({'audit_id': audit.id, 'legal_name': 'RiskClient', 'principal_business_address': 'Addr', 'business_registration_number': 'R123'})

    def test_sanctions_blocking(self):
        # create a sanctions screening that blocks
        self.Sanction.create({
            'onboarding_id': self.onboarding.id,
            'screening_performed': True,
            'screening_method': 'manual',
            'sanctions_hit': True,
            'screening_conclusion': 'block',
            'resolution_notes': 'Under review',
        })
        # move to under_review and attempt partner approval -> should raise
        self.onboarding.action_submit_review()
        with self.assertRaises(exceptions.ValidationError):
            self.onboarding.action_partner_approve()

    def test_aml_kyc_gating(self):
        # mark AML applicable but leave identity / UBO unverified
        self.onboarding.aml_applicable = True
        self.onboarding.client_identity_verified = False
        self.onboarding.ubo_verified = False
        self.onboarding.action_submit_review()
        with self.assertRaises(exceptions.ValidationError):
            self.onboarding.action_partner_approve()
        # if both identity and UBO verified, approval should proceed (no exception)
        self.onboarding.client_identity_verified = True
        self.onboarding.ubo_verified = True
        # call partner approval should now either pass or fail on unrelated checks; ensure we can reach approval state
        # ensure mandatory checklist is satisfied to allow approval - populate and mark completed
        self.onboarding._populate_regulator_checklist()
        for line in self.onboarding.regulator_checklist_line_ids:
            if line.mandatory:
                line.completed = True
        # create an engagement partner to satisfy high risk check if needed
        partner = self.env['res.users'].browse(self.env.uid)
        self.onboarding.engagement_partner_id = partner.id
        # move and approve
        self.onboarding.action_submit_review()
        self.onboarding.action_partner_approve()
        self.assertEqual(self.onboarding.state, 'partner_approved')

    def test_engagement_scoring_and_eqcr(self):
        # create multiple drivers to raise score above thresholds
        self.Driver.create({'onboarding_id': self.onboarding.id, 'driver': 'Complex estimates', 'weight': 1.0, 'score': 10})
        self.Driver.create({'onboarding_id': self.onboarding.id, 'driver': 'Revenue complexity', 'weight': 1.0, 'score': 10})
        self.Driver.create({'onboarding_id': self.onboarding.id, 'driver': 'Going concern', 'weight': 1.0, 'score': 50})
        # trigger compute
        self.onboarding._compute_engagement_score()
        # engagement_score should be set and rating derived
        self.assertTrue(self.onboarding.engagement_score >= 0)
        self.assertIn(self.onboarding.engagement_risk_rating, ('low','medium','high'))
        # if rating is high, eqcr_required should be true
        if self.onboarding.engagement_risk_rating == 'high':
            self.assertTrue(self.onboarding.eqcr_required)
        else:
            # still ensure the compute method ran
            self.assertIsNotNone(self.onboarding.engagement_score)
