from odoo.tests.common import TransactionCase


class TestDocumentVaultAccessRules(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Onboarding = self.env["qaco.client.onboarding"]
        self.Doc = self.env["qaco.onboarding.document"]
        firm = self.env["audit.firm.name"].create({"name": "ARFirm", "code": "AR"})
        client = self.env["res.partner"].create({"name": "ARClient"})
        audit = self.env["qaco.audit"].create(
            {"name": "A1", "client_id": client.id, "firm_name": firm.id}
        )
        self.onboarding = self.Onboarding.create(
            {
                "audit_id": audit.id,
                "legal_name": "ARClient",
                "principal_business_address": "Addr",
                "business_registration_number": "P123",
            }
        )
        # find a folder for testing
        self.folder_restricted = self.onboarding.get_folder_by_code("02_KYC")
        self.folder_client = self.onboarding.get_folder_by_code("01_01_Client_Master")

    def test_trainee_cannot_see_restricted(self):
        # create a restricted doc
        doc = self.Doc.create(
            {
                "onboarding_id": self.onboarding.id,
                "name": "RestrDoc",
                "file": "dGVzdA==",
                "file_name": "r.pdf",
                "sensitivity": "restricted",
                "folder_id": self.folder_restricted.id,
            }
        )
        # create a trainee user
        trainee = self.env["res.users"].create(
            {"name": "Trainee", "login": "trainee@example.com"}
        )
        trainee.write(
            {"groups_id": [(4, self.env.ref("qaco_audit.group_audit_trainee").id)]}
        )
        found = self.Doc.with_user(trainee.id).search([("id", "=", doc.id)])
        self.assertFalse(found, "Trainee should not see restricted documents")

    def test_confidential_group_sees_highly_restricted(self):
        doc = self.Doc.create(
            {
                "onboarding_id": self.onboarding.id,
                "name": "HighDoc",
                "file": "dGVzdA==",
                "file_name": "h.pdf",
                "sensitivity": "highly_restricted",
                "folder_id": self.folder_restricted.id,
            }
        )
        user = self.env["res.users"].create(
            {"name": "ConfUser", "login": "conf@example.com"}
        )
        user.write(
            {
                "groups_id": [
                    (
                        4,
                        self.env.ref(
                            "qaco_client_onboarding.group_onboarding_confidential"
                        ).id,
                    )
                ]
            }
        )
        found = self.Doc.with_user(user.id).search([("id", "=", doc.id)])
        self.assertTrue(
            found, "Confidential group member should see highly restricted documents"
        )

    def test_portal_user_sees_client_upload_in_client_folder(self):
        # create a portal user
        portal_user = self.env["res.users"].create(
            {"name": "PortalUser", "login": "portal@example.com"}
        )
        portal_user.write({"groups_id": [(4, self.env.ref("base.group_portal").id)]})
        # create a document marked as client upload in client-visible folder
        doc = self.Doc.create(
            {
                "onboarding_id": self.onboarding.id,
                "name": "ClientDoc",
                "file": "dGVzdA==",
                "file_name": "c.pdf",
                "is_client_upload": True,
                "sensitivity": "normal",
                "folder_id": self.folder_client.id,
            }
        )
        found = self.Doc.with_user(portal_user.id).search([("id", "=", doc.id)])
        self.assertTrue(
            found, "Portal user should see client upload in client-visible folder"
        )
