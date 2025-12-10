import types

from odoo import exceptions, fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAIAuditWorkflows(TransactionCase):
    def setUp(self):
        super().setUp()
        # Ensure a settings record exists
        settings = self.env['audit.ai.settings'].sudo().search([], limit=1)
        if not settings:
            self.env['audit.ai.settings'].sudo().create({'openai_api_key': 'sk-test'})
        else:
            settings.write({'openai_api_key': 'sk-test'})

    def _patch_openai(self, content):
        from odoo.addons.ai_audit_management.models import ai_helper
        ai_helper.openai = types.SimpleNamespace(
            ChatCompletion=types.SimpleNamespace(
                create=lambda **kwargs: {'choices': [{'message': {'content': content}}]}
            )
        )

    def test_ai_plan_generation_with_stub(self):
        self._patch_openai('{"scope": "Minimal"}')
        plan = self.env['audit.plan'].create({'financial_year': 'FY25'})
        plan.ai_generate_audit_plan()
        self.assertIsInstance(plan.planned_procedures_json, dict)
        self.assertIn('scope', plan.planned_procedures_json)

    def test_ai_helper_requires_key(self):
        from odoo.addons.ai_audit_management.models import ai_helper
        self._patch_openai('ok')
        settings = self.env['audit.ai.settings'].sudo().search([], limit=1)
        settings.write({'openai_api_key': False})
        plan = self.env['audit.plan'].create({'financial_year': 'FY25'})
        with self.assertRaises(exceptions.UserError):
            plan._call_openai('hello')

    def test_evidence_index_generation(self):
        self._patch_openai('Evidence summary')
        index = self.env['audit.evidence.index'].create({'name': 'Index Demo'})
        index.action_generate_index()
        self.assertTrue(index.ai_summary)

    def test_archival_lock_guard(self):
        archival = self.env['audit.archival'].create({
            'file_index': 'TEST-LOCK',
            'locked_status': True,
        })
        with self.assertRaises(exceptions.UserError):
            archival.write({'qc_comments': 'ok', 'retention_period': 10})

    def test_archival_cron_autolock(self):
        archival = self.env['audit.archival'].create({
            'file_index': 'TEST-CRON',
            'archival_date': fields.Date.to_date('2024-01-01'),
            'locked_status': False,
        })
        self.env['audit.archival'].cron_lock_archival_files()
        archival.refresh()
        self.assertTrue(archival.locked_status)

    def test_reports_actions_exist(self):
        # Ensure report actions are registered to avoid missing ID issues
        self.assertTrue(self.env.ref('ai_audit_management.report_engagement_letter', raise_if_not_found=False))
        self.assertTrue(self.env.ref('ai_audit_management.report_management_rep_letter', raise_if_not_found=False))
        self.assertTrue(self.env.ref('ai_audit_management.report_tcw_report', raise_if_not_found=False))
        self.assertTrue(self.env.ref('ai_audit_management.report_audit_final', raise_if_not_found=False))

    def test_qweb_render_minimal(self):
        # Render engagement letter report on a minimal record
        letter = self.env['audit.engagement.letter'].create({
            'name': 'Test Letter',
            'scope_of_audit': 'Test scope',
        })
        action = self.env.ref('ai_audit_management.report_engagement_letter').report_action(letter)
        self.assertEqual(action.get('res_model'), 'audit.engagement.letter')
