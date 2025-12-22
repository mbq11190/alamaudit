from odoo.tests.common import TransactionCase

class TestPredecessorReports(TransactionCase):
    def setUp(self):
        super().setUp()
        self.PreReq = self.env['qaco.onboarding.predecessor.request']

    def test_reports_registered(self):
        # Ensure report actions exist
        report_memo = self.env.ref('qaco_client_onboarding.report_predecessor_clearance_memo', raise_if_not_found=False)
        report_pack = self.env.ref('qaco_client_onboarding.report_predecessor_clearance_pack', raise_if_not_found=False)
        self.assertTrue(report_memo, 'Predecessor clearance memo report action should be registered')
        self.assertTrue(report_pack, 'Predecessor clearance pack report action should be registered')
