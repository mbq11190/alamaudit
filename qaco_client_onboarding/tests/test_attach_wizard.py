from odoo.tests.common import TransactionCase


class TestAttachWizard(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Onboarding = self.env['qaco.client.onboarding']
        self.Template = self.env['qaco.onboarding.template.document']
        self.Attached = self.env['qaco.onboarding.attached.template']

        # create a minimal onboarding and templates
        self.onboarding = self.Onboarding.create({
            'audit_id': self.env['qaco.audit'].create({'client_id': self.env.ref('base.res_partner_1').id}).id,
            'entity_type': 'pic',
            'legal_name': 'Test Co',
            'principal_business_address': 'Addr',
            'business_registration_number': 'BRN-1',
            'primary_regulator': 'secp',
        })
        self.tpl1 = self.Template.create({'name': 'T1', 'category_id': self.env['qaco.onboarding.template.category'].create({'name':'C','code':'C1'}).id, 'template_file': b'foo', 'template_filename': 'foo.docx'})
        self.tpl2 = self.Template.create({'name': 'T2', 'category_id': self.tpl1.category_id.id})

    def test_action_open_attach_wizard_with_templates(self):
        action = self.onboarding.action_open_attach_wizard_with_templates([self.tpl1.id, self.tpl2.id])
        ctx = action.get('context', {})
        self.assertIn('default_template_ids', ctx)
        # Expect template ids to be present in default
        default_templates = ctx['default_template_ids'][0][2]
        self.assertEqual(sorted(default_templates), sorted([self.tpl1.id, self.tpl2.id]))
        self.assertEqual(ctx.get('default_onboarding_id'), self.onboarding.id)

    def test_wizard_attach_creates_attached(self):
        wiz = self.env['qaco.onboarding.attach.templates.wizard'].create({'onboarding_id': self.onboarding.id, 'template_ids': [(6,0,[self.tpl1.id, self.tpl2.id])]})
        wiz.action_attach()
        attached = self.Attached.search([('onboarding_id','=',self.onboarding.id)])
        self.assertEqual(len(attached), 2)
        self.assertTrue(attached.filtered(lambda r: r.template_id == self.tpl1))
        self.assertTrue(attached.filtered(lambda r: r.template_id == self.tpl2))
