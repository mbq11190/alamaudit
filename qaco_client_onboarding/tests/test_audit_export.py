from odoo.tests.common import TransactionCase

class TestAuditExport(TransactionCase):
    def setUp(self):
        super(TestAuditExport, self).setUp()
        self.onboarding = self.env['qaco.client.onboarding'].create({'name': 'ACME Co'})
        self.user = self.env.user
        self.trail = self.env['qaco.onboarding.audit.trail'].create({
            'onboarding_id': self.onboarding.id,
            'user_id': self.user.id,
            'action': 'test export',
            'action_type': 'activity',
        })

    def test_export_csv(self):
        wiz = self.env['qaco.onboarding.audit.export.wizard'].create({
            'export_format': 'csv',
        })
        action = wiz.action_export()
        # CSV returns a url action
        self.assertEqual(action.get('type'), 'ir.actions.act_url')
        self.assertIn('web/content', action.get('url', ''))

    def test_export_pdf_action(self):
        wiz = self.env['qaco.onboarding.audit.export.wizard'].create({
            'export_format': 'pdf',
            'action_type': 'activity',
        })
        action = wiz.action_export()
        # For pdf we expect a report action dict
        self.assertIsInstance(action, dict)
        self.assertTrue(action)

    def test_apply_resolution(self):
        wiz = self.env['qaco.onboarding.audit.resolution.wizard'].create({
            'audit_id': self.trail.id,
            'resolution': 'This was resolved',
            'mark_override': True,
        })
        wiz.action_apply_resolution()
        self.trail.refresh()
        self.assertEqual(self.trail.resolution, 'This was resolved')
        self.assertTrue(self.trail.is_override)
        # ensure a new audit entry logged on the onboarding
        entries = self.onboarding.audit_trail_ids.filtered(lambda t: t.action == 'audit resolution added')
        self.assertTrue(entries)

    def test_open_resolution_action(self):
        action = self.trail.action_open_resolution_wizard()
        self.assertIsInstance(action, dict)
        self.assertEqual(action.get('res_model'), 'qaco.onboarding.audit.resolution.wizard')
