"""Utility helpers for qaco_client_onboarding.
Keep utilities free of Odoo imports so they can be imported safely in tests and pre-commit hooks.
"""

from .onboarding_hints import ONBOARDING_HINTS

__all__ = ["ONBOARDING_HINTS"]
