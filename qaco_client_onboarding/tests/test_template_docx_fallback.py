from odoo.tests.common import TransactionCase
import builtins

from qaco_client_onboarding.controllers.template_download_controller import FitProperTemplateController

class TestDocxFallback(TransactionCase):
    def test_create_word_doc_without_docx(self):
        ctrl = FitProperTemplateController()
        orig_import = builtins.__import__
        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == 'docx' or name.startswith('docx.'):
                raise ImportError
            return orig_import(name, globals, locals, fromlist, level)
        builtins.__import__ = fake_import
        try:
            with self.assertRaises(RuntimeError):
                ctrl._create_word_document({'entity_name': 'X'})
        finally:
            builtins.__import__ = orig_import