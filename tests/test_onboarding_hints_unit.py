import importlib.util
import pathlib

spec = importlib.util.spec_from_file_location(
    "onboarding_hints",
    pathlib.Path(__file__).resolve().parents[1] / "qaco_client_onboarding" / "utils" / "onboarding_hints.py",
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
ONBOARDING_HINTS = module.ONBOARDING_HINTS


def test_hint_keys_present():
    assert isinstance(ONBOARDING_HINTS, dict)
    expected_keys = [
        "legal_name",
        "beneficial_owners",
        "source_of_funds",
        "independence_confirmation",
        "engagement_risks",
        "pending_documents",
        "acceptance_decision",
    ]
    for k in expected_keys:
        assert k in ONBOARDING_HINTS
        assert isinstance(ONBOARDING_HINTS[k], str)
        assert len(ONBOARDING_HINTS[k]) > 0
