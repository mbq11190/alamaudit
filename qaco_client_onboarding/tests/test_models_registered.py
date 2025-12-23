from odoo.tests.common import TransactionCase


class TestOnboardingModels(TransactionCase):
    def test_onboarding_models_registered(self):
        # Check a couple of onboarding models are loaded
        self.assertIn('qaco.client.onboarding', self.env.registry.models)
        self.assertIn('qaco.onboarding.conflict', self.env.registry.models)
        self.assertIn('qaco.onboarding.independence.threat', self.env.registry.models)
