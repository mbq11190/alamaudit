"""Standard onboarding hint dictionary for QACO Client Onboarding

This module contains neutral, non-judgemental guidance strings that may be
used as placeholders or helper text in onboarding forms. The values are
examples only and must never be saved automatically.

Design rules:
- Hints are examples / guidance only
- Language is neutral and professionally defensible
- No defaults or computed values that would auto-save
- Accessible: short and concise

Aligned with ISA, AML/KYC, ICAP ethics and Companies Act 2017 where relevant.
"""

ONBOARDING_HINTS = {
    # SECTION 1 — ENTITY & LEGAL PROFILE
    "legal_name": "As per Certificate of Incorporation or constitutional documents",
    "entity_type": "e.g. Private Limited Company, Public Limited Company, LLP, AOP, Trust",
    "registration_number": "SECP Company Registration No. / Trust Deed No.",
    "date_of_incorporation": "As stated in incorporation documents",
    "registered_address": "Registered office address as per statutory records",
    "nature_of_business": "Brief description of principal business activities",
    "authorized_share_capital": "As per Memorandum of Association",
    "paid_up_capital": "Paid-up share capital as at onboarding date",

    # SECTION 2 — OWNERSHIP & GOVERNANCE
    "directors_details": "List current directors as per Form A / statutory records",
    "shareholders_details": "Major shareholders holding 10% or more",
    "beneficial_owners": "Individuals exercising ultimate control or ownership",
    "group_structure": "Outline holding, subsidiaries, or associated entities",
    "key_management_personnel": "CEO, CFO, COO or equivalent roles",

    # SECTION 3 — AML / KYC & CLIENT INTEGRITY
    "source_of_funds": "e.g. Operating revenues, shareholder injections, loans",
    "source_of_wealth": "General origin of owners’ wealth (business, employment, inheritance)",
    "politically_exposed_person": "Indicate if any director or owner is a PEP",
    "sanctions_screening": "Confirm screening against sanctions / watchlists",
    "high_risk_jurisdictions": "Any dealings with FATF high-risk jurisdictions",

    # SECTION 4 — ETHICS & INDEPENDENCE
    "independence_confirmation": "Confirm no prohibited relationships exist",
    "conflict_of_interest": "Identify any actual or potential conflicts",
    "non_audit_services": "Any non-audit services provided to the client",
    "partner_rotation": "Confirm partner rotation requirements, if applicable",
    "ethics_threats": "Self-interest, familiarity, advocacy, intimidation threats",

    # SECTION 5 — ENGAGEMENT ACCEPTANCE
    "reason_for_engagement": "Purpose of engagement and client expectations",
    "scope_of_services": "Audit, review, advisory, or other services",
    "financial_reporting_framework": "IFRS, IFRS for SMEs, IPSAS, or other",
    "engagement_risks": "Complex estimates, related parties, going concern issues",
    "prior_auditor_issues": "Any disagreements or qualifications by previous auditors",

    # SECTION 6 — RISK ASSESSMENT
    "business_risk_factors": "Market volatility, regulatory changes, competition",
    "fraud_risk_indicators": "Revenue recognition, management override risks",
    "internal_control_environment": "Tone at the top and governance effectiveness",
    "it_environment": "ERP usage, access controls, data integrity considerations",

    # SECTION 7 — DOCUMENTATION & EVIDENCE
    "pending_documents": "List documents yet to be received from client",
    "document_reliability": "Assess reliability of provided information",
    "external_confirmations": "Bank, legal, or third-party confirmations required",

    # SECTION 8 — FINAL DECISION & APPROVAL
    "acceptance_decision": "Accept, accept with conditions, or decline",
    "decision_rationale": "Brief justification supporting the acceptance decision",
    "conditions_if_any": "Conditions to be fulfilled before proceeding",
    "approval_notes": "Partner or EQCR remarks, if applicable",
}

__all__ = ["ONBOARDING_HINTS"]
