import base64

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestLegalIdentity(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Template = self.env["qaco.onboarding.template.document"]
        self.Onboarding = self.env["qaco.client.onboarding"]
        self.Doc = self.env["qaco.onboarding.document"]
        # create a simple template with a small file
        self.template = self.Template.create(
            {
                "name": "Test Incorp",
                "category_id": self.env.ref(
                    "qaco_client_onboarding.template_category_client_onboarding"
                ).id,
                "file_type": "docx",
                "template_file": base64.b64encode(b"doc").decode("utf-8"),
            }
        )

    def test_attach_indexes_document(self):
        onboarding = self.Onboarding.create(
            {
                "audit_id": self.env["qaco.audit"]
                .create(
                    {
                        "name": "A",
                        "client_id": self.env["res.partner"].create({"name": "X"}),
                    }
                )
                .id,
                "legal_name": "X Ltd",
                "entity_type": "pic",
                "principal_business_address": "Addr",
                "business_registration_number": "123",
            }
        )
        # action_attach_to_onboarding should create an attached template and index a document
        self.template.action_attach_to_onboarding() if self.template else None
        # use context to attach
        self.template.with_context(
            onboarding_id=onboarding.id
        ).action_attach_to_onboarding()
        docs = self.Doc.search([("onboarding_id", "=", onboarding.id)])
        self.assertTrue(docs, "Document should be indexed after attaching template")

    def test_company_requires_documents_on_approval(self):
        onboarding = self.Onboarding.create(
            {
                "audit_id": self.env["qaco.audit"]
                .create(
                    {
                        "name": "A2",
                        "client_id": self.env["res.partner"].create({"name": "Y"}),
                    }
                )
                .id,
                "legal_name": "Y Ltd",
                "entity_type": "pic",
                "principal_business_address": "Addr",
                "business_registration_number": "456",
            }
        )
        # No docs attached, setting state to partner_approved should raise
        with self.assertRaises(ValidationError):
            onboarding.state = "partner_approved"
