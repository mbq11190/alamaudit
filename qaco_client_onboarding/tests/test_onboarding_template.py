from odoo import exceptions
from odoo.tests.common import TransactionCase


class TestOnboardingTemplate(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Template = self.env["qaco.onboarding.template.document"]
        self.Onboarding = self.env["qaco.client.onboarding"]
        self.Attached = self.env["qaco.onboarding.attached.template"]
        self.Doc = self.env["qaco.onboarding.document"]

    def test_mandatory_hard_stop_constraint(self):
        # creating a template with a hard-stop mandatory value but wrong stage should fail
        with self.assertRaises(exceptions.ValidationError):
            self.Template.create(
                {
                    "name": "Hard stop sample",
                    "category_id": self.env["qaco.onboarding.template.category"]
                    .create({"name": "T", "code": "T"})
                    .id,
                    "mandatory": "yes_hard_stop",
                    "stage": "throughout_onboarding",
                }
            )

    def test_attach_indexes_document_vault(self):
        # create onboarding and template with file and attach
        client = self.env["res.partner"].create({"name": "ACME Test"})
        onboarding = self.Onboarding.create(
            {
                "name": "T",
                "audit_id": self.env["qaco.audit"]
                .create(
                    {
                        "name": "A",
                        "client_id": client.id,
                        "firm_name": self.env["audit.firm.name"]
                        .create({"name": "F", "code": "F"})
                        .id,
                    }
                )
                .id,
            }
        )
        cat = self.env["qaco.onboarding.template.category"].create(
            {"name": "T2", "code": "t2"}
        )
        tpl = self.Template.create(
            {
                "name": "Sample",
                "category_id": cat.id,
                "template_file": b"test",
                "template_filename": "sample.pdf",
            }
        )
        tpl.with_context(onboarding_id=onboarding.id).action_attach_to_onboarding()
        docs = self.Doc.search([("onboarding_id", "=", onboarding.id)])
        self.assertTrue(docs, "Document Vault should contain the attached template")
