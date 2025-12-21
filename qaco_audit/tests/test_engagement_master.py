from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestEngagementMaster(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Audit = self.env['qaco.audit']
        self.User = self.env['res.users']

    def test_engagement_code_generated(self):
        audit = self.Audit.create({
            'client_id': self.env.ref('base.res_partner_1').id,
        })
        self.assertTrue(audit.engagement_code, 'Engagement code should be generated')

    def test_maker_checker_enforced(self):
        u = self.env.user
        audit = self.Audit.create({
            'client_id': self.env.ref('base.res_partner_1').id,
            'preparer_id': u.id,
            'reviewer_id': u.id,
        })
        with self.assertRaises(ValidationError):
            audit.action_partner_approve()