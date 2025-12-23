import builtins

from odoo import fields
from odoo.tests.common import TransactionCase


class TestPredecessorNoMerger(TransactionCase):
    def setUp(self):
        super(TestPredecessorNoMerger, self).setUp()
        self.onboarding = self.env["qaco.client.onboarding"].create(
            {"name": "NoMergerCo"}
        )
        self.req = self.env["qaco.onboarding.predecessor.request"].create(
            {
                "onboarding_id": self.onboarding.id,
                "predecessor_firm": "OldAudit",
                "predecessor_email": "old@audit.example",
                "sent_date": fields.Datetime.now(),
            }
        )

    def test_generate_pack_without_merger(self):
        # Simulate missing pypdf and PyPDF2 by temporarily intercepting imports
        orig_import = builtins.__import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name in ("pypdf", "PyPDF2"):
                raise ImportError
            return orig_import(name, globals, locals, fromlist, level)

        builtins.__import__ = fake_import
        try:
            att = self.req.action_generate_pack_bundle()
            self.assertTrue(att)
            self.assertEqual(att.mimetype, "application/pdf")
            # When merger missing, attachment should contain base pack; size > 0
            self.assertTrue(att.datas)
        finally:
            builtins.__import__ = orig_import
