from odoo.tests.common import TransactionCase


class TestIndependenceSeed(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Safeguard = self.env["qaco.onboarding.safeguard"]
        self.Settings = self.env["res.config.settings"]
        self.Icp = self.env["ir.config_parameter"].sudo()

    def test_safeguard_master_records_loaded(self):
        codes = [
            "SEPARATE_TEAM",
            "SECOND_PARTNER",
            "ROTATION",
            "INDEPENDENT_CONSULT",
            "SUPERVISION",
            "DISCONTINUE_SERVICE",
            "CLIENT_GOVERNANCE",
            "WITHDRAWAL",
        ]
        found = self.Safeguard.search([("code", "in", codes)])
        found_codes = set(found.mapped("code"))
        for c in codes:
            self.assertIn(
                c, found_codes, "Expected safeguard code %s to be present" % c
            )

    def test_gift_threshold_seeded_in_ir_config(self):
        val = self.Icp.get_param(
            "qaco_client_onboarding.gift_auto_decline_threshold", default=None
        )
        self.assertIsNotNone(
            val,
            "Expected gift auto-decline threshold to be seeded in ir.config_parameter",
        )
        # stored as string in ir.config_parameter
        self.assertEqual(str(int(float(val))), "5000")

    def test_onboarding_settings_view_and_action_present(self):
        view = self.env.ref(
            "qaco_client_onboarding.view_res_config_settings_onboarding",
            raise_if_not_found=False,
        )
        self.assertTrue(view, "Onboarding settings view should exist")
        action = self.env.ref(
            "qaco_client_onboarding.action_onboarding_settings",
            raise_if_not_found=False,
        )
        self.assertTrue(action, "Onboarding settings action should exist")
        # the Onboarding menu should now be nested under admin Settings → Audit
        menu = self.env.ref(
            "qaco_client_onboarding.menu_onboarding_settings", raise_if_not_found=False
        )
        self.assertTrue(menu, "Onboarding settings menu should exist")
        parent = menu.parent_id
        # Use ir.model.data to verify the xml id of the parent menu
        if parent:
            xmlid = self.env["ir.model.data"].xmlid_from_object(parent)
        else:
            xmlid = None
        self.assertEqual(
            xmlid,
            "qaco_client_onboarding.menu_admin_audit",
            "Onboarding menu parent should be the Audit settings group",
        )
        # audit menu should have an icon and a smaller sequence
        audit_menu = self.env.ref(
            "qaco_client_onboarding.menu_admin_audit", raise_if_not_found=False
        )
        self.assertTrue(audit_menu, "Audit menu should exist")
        self.assertEqual(audit_menu.sequence, 70)
        self.assertEqual(audit_menu.web_icon, "qaco_audit,static/description/icon.png")
        self.assertEqual(menu.sequence, 5)

    def test_settings_set_values_updates_icp(self):
        # use the transient settings to change the threshold
        s = self.Settings.create({"gift_auto_decline_threshold": 1234.5})
        s.set_values()
        val = self.Icp.get_param("qaco_client_onboarding.gift_auto_decline_threshold")
        self.assertEqual(str(int(float(val))), "1234")
