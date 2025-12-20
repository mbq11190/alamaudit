{
    "name": "Audit Planning Phase - Pakistan Statutory Audit",
    "summary": "Zero-deficiency ISA-compliant planning workflow (P-1 to P-13) for statutory audits in Pakistan",
    "version": "17.0.2.0.0",
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
        # Security
        "security/planning_phase_security.xml",
        "security/ir.model.access.csv",
        # P-1 to P-13 Views
        "views/planning_p1_views.xml",
        "views/planning_p2_views.xml",
        "views/planning_p3_views.xml",
        "views/planning_p4_views.xml",
        "views/planning_p5_views.xml",
        "models/planning_p6_risk.py",
        "views/planning_p6_views.xml",
        "views/planning_p7_views.xml",
        "views/planning_p8_views.xml",
        "views/planning_p9_views.xml",
        "views/planning_p6_views.xml",
        "views/planning_p7_views.xml",
        "views/planning_p8_views.xml",
        "views/planning_p9_views.xml",
        "views/planning_p10_views.xml",
        "views/planning_p11_views.xml",
        "views/planning_p10_related_parties_views.xml",
        "views/planning_p12_views.xml",
        "views/planning_p13_views.xml",
        # Legacy Views (for backward compatibility)
        "views/planning_phase_views.xml",
        "views/supporting_views.xml",
        "views/planning_phase_actions.xml",
        "views/audit_smart_button.xml",
        # Dashboard
        "views/planning_dashboard_views.xml",
        # Menu Structure
        "views/planning_menu.xml",
        # Data
        "data/industry_data.xml",
        "data/regulator_data.xml",
        "data/assertion_tags.xml",
        "data/materiality_defaults.xml",
        "data/checklist_data.xml",
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
    "application": False,  # Not a standalone app - accessed via Audit Work smart button
    "auto_install": True,
    "price": 0,
    "currency": "PKR",
    "description": """
Audit Planning Phase - Pakistan (P-1 to P-13)
==============================================

ISA-Compliant Planning Tabs:
- P-1: Engagement Setup & Team Assignment (ISA 210/220/ISQM-1)
- P-2: Entity & Environment Understanding (ISA 315)
- P-3: Internal Control Understanding (ISA 315)
- P-4: Preliminary Analytical Review (ISA 520)
- P-5: Materiality Determination (ISA 320)
- P-6: Risk of Material Misstatement (ISA 315)
- P-7: Fraud Risk Considerations (ISA 240)
- P-8: Going Concern Assessment (ISA 570)
- P-9: Laws & Regulations Compliance (ISA 250)
- P-10: Related Party Transactions (ISA 550)
- P-11: Group Audit Considerations (ISA 600)
- P-12: Audit Strategy & Plan (ISA 300)
- P-13: Approval & Planning Lock (ISA 220/ISQM-1)

Features:
- Status-driven workflow (Not Started → In Progress → Completed → Reviewed → Approved)
- Maker-checker control (Senior → Manager → Partner)
- Automatic APM (Audit Planning Memorandum) generation
- Pakistan-specific compliance (ICAP, SECP, AOB, FBR, SBP, PRA)
- Quality review integration with EQCR support
- Complete audit trail via mail.thread
""",
}
