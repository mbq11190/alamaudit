from odoo import exceptions
from odoo.tests.common import TransactionCase


class TestOwnershipGovernance(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Onboarding = self.env["qaco.client.onboarding"]
        self.Shareholder = self.env["qaco.onboarding.shareholder"]
        self.UBO = self.env["qaco.onboarding.ubo"]
        self.Component = self.env["qaco.onboarding.group.component"]
        self.RequiredDoc = self.env["qaco.onboarding.required.document"]
        self.Doc = self.env["qaco.onboarding.document"]
        firm = self.env["audit.firm.name"].create({"name": "TestFirm", "code": "TF"})
        client = self.env["res.partner"].create({"name": "OwnerClient"})
        audit = self.env["qaco.audit"].create(
            {"name": "A1", "client_id": client.id, "firm_name": firm.id}
        )
        self.onboarding = self.Onboarding.create(
            {
                "audit_id": audit.id,
                "legal_name": "OwnerClient",
                "principal_business_address": "Addr",
                "business_registration_number": "123",
            }
        )

    def test_shareholding_sum_constraint(self):
        # create shareholders summing to not 100 and assert validation on partner approval
        self.Shareholder.create(
            {"onboarding_id": self.onboarding.id, "name": "A", "percentage": 60}
        )
        self.Shareholder.create(
            {"onboarding_id": self.onboarding.id, "name": "B", "percentage": 30}
        )
        # no explanation, total 90 -> should raise on write of ubo_section or on constraint checking when trying to approve
        with self.assertRaises(exceptions.ValidationError):
            # simulate partner approval which triggers validation
            self.onboarding.write({"state": "partner_approved"})

    def test_ubo_basis_required_when_marked_complete(self):
        # create a ubo without basis
        self.UBO.create(
            {
                "onboarding_id": self.onboarding.id,
                "name": "UBO1",
                "ownership_percent": 100,
            }
        )
        with self.assertRaises(exceptions.ValidationError):
            self.onboarding.write({"ubo_section_complete": True})

    def test_group_status_requires_components(self):
        with self.assertRaises(exceptions.ValidationError):
            self.onboarding.write({"group_status": "parent"})

    def test_required_document_upload_indexes_into_document_vault(self):
        # ensure ownership templates exist
        cat = self.env["qaco.onboarding.template.category"].search(
            [("code", "=", "ownership")], limit=1
        )
        if not cat:
            cat = self.env["qaco.onboarding.template.category"].create(
                {"name": "Ownership", "code": "ownership"}
            )
        tpl = self.env["qaco.onboarding.template.document"].create(
            {
                "name": "Owner Profile",
                "category_id": cat.id,
                "stage": "pre_onboarding",
                "mandatory": "yes",
                "file_type": "docx",
            }
        )
        # populate ownership required docs
        self.onboarding.populate_ownership_required_documents_from_templates()
        r = self.onboarding.required_document_line_ids.filtered(
            lambda line: line.template_id.id == tpl.id
        )
        self.assertTrue(r, "Required document row should be created")
        r.write(
            {
                "uploaded_file": b"pdfcontent",
                "uploaded_filename": "owner.pdf",
                "status": "received",
            }
        )
        docs = self.Doc.search(
            [
                ("onboarding_id", "=", self.onboarding.id),
                ("file_name", "=", "owner.pdf"),
            ]
        )
        self.assertTrue(docs, "Uploaded file should be indexed into Document Vault")
