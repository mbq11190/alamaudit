from datetime import date, timedelta

from odoo import exceptions
from odoo.tests.common import TransactionCase


class TestRegulatoryCompliance(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Onboarding = self.env["qaco.client.onboarding"]
        self.License = self.env["qaco.onboarding.license"]
        self.Filing = self.env["qaco.onboarding.filing"]
        self.RequiredDoc = self.env["qaco.onboarding.required.document"]
        self.Doc = self.env["qaco.onboarding.document"]
        # prepare baseline audit and onboarding
        firm = self.env["audit.firm.name"].create({"name": "TestFirm", "code": "TF"})
        client = self.env["res.partner"].create({"name": "RegClient"})
        audit = self.env["qaco.audit"].create(
            {"name": "A1", "client_id": client.id, "firm_name": firm.id}
        )
        self.onboarding = self.Onboarding.create(
            {
                "audit_id": audit.id,
                "legal_name": "RegClient",
                "principal_business_address": "Addr",
                "business_registration_number": "123",
            }
        )

    def test_license_required_constraint(self):
        # creating a license marked required without expiry should raise ValidationError
        with self.assertRaises(exceptions.ValidationError):
            self.License.create(
                {
                    "onboarding_id": self.onboarding.id,
                    "license_type": "Operating",
                    "required": True,
                }
            )

    def test_required_document_populate_and_upload_index(self):
        # ensure templates category exists and populate required docs
        cat = self.env["qaco.onboarding.template.category"].search(
            [("code", "=", "regulatory")], limit=1
        )
        if not cat:
            cat = self.env["qaco.onboarding.template.category"].create(
                {"name": "Regulatory", "code": "regulatory"}
            )
        tpl = self.env["qaco.onboarding.template.document"].create(
            {
                "name": "Reg Profile",
                "category_id": cat.id,
                "stage": "pre_onboarding",
                "mandatory": "yes",
                "file_type": "docx",
            }
        )
        # populate required documents
        self.onboarding.populate_required_documents_from_templates()
        self.assertTrue(
            self.onboarding.required_document_line_ids,
            "Required documents should be populated from templates",
        )
        r = self.onboarding.required_document_line_ids.filtered(
            lambda line: line.template_id.id == tpl.id
        )
        # upload a file and verify it gets indexed into Document Vault
        r.write(
            {
                "uploaded_file": b"1234",
                "uploaded_filename": "evidence.pdf",
                "status": "received",
            }
        )
        docs = self.Doc.search(
            [
                ("onboarding_id", "=", self.onboarding.id),
                ("file_name", "=", "evidence.pdf"),
            ]
        )
        self.assertTrue(
            docs, "Uploaded required document should be indexed into Document Vault"
        )

    def test_overdue_filings_block_partner_approval(self):
        # create an overdue filing
        past = date.today() - timedelta(days=30)
        self.Filing.create(
            {
                "onboarding_id": self.onboarding.id,
                "filing_name": "Annual Return",
                "authority": "SECP",
                "period_covered": "2023",
                "statutory_due_date": past,
                "status": "due",
            }
        )
        # attempt partner approval must raise ValidationError
        with self.assertRaises(exceptions.ValidationError):
            self.onboarding.action_partner_approve()
