{
    "name": "Audit Planning Phase - Pakistan Statutory Audit",
    "summary": "Zero-deficiency planning workflow for statutory audits in Pakistan",
    "version": "17.0.1.1.0",
    "author": "QACO",
    "website": "https://alamaudit.thinkoptimise.com",
    "license": "LGPL-3",
    "category": "Audit",
    "depends": [
        "base",
        "mail",
        "web",
        "qaco_audit",
        "qaco_client_onboarding",
    ],
    "data": [
        "security/planning_phase_security.xml",
        "security/ir.model.access.csv",
        "views/planning_phase_views.xml",
        "views/supporting_views.xml",
        "views/planning_phase_actions.xml",
        "views/audit_smart_button.xml",
        "data/industry_data.xml",
        "data/regulator_data.xml",
    ],
    "demo": [
        "demo/planning_phase_demo.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "qaco_planning_phase/static/src/scss/planning.scss",
            "qaco_planning_phase/static/src/css/planning_phase.css",
        ],
    },
    "installable": True,
    "application": True,
    "auto_install": True,
    "price": 0,
    "currency": "PKR",
    "description": """
Audit Planning Phase - Pakistan
================================

- Complete ISA 315 entity understanding and environment capture
- Analytical procedures library for ISA 520 expectations
- Materiality engine aligned to ISA 320 with automatic calculations
- Control assessment workspace with reliance guidance
- Risk register and audit strategy orchestration (ISA 315/330)
- Documentation, attachments, and checklist flow targeting zero deficiencies

Pakistan-specific compliance coverage (ICAP, SECP, AOB, SBP) paired with sign-offs and quality review workflows.
""",
}
