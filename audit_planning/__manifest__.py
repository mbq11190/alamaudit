# -*- coding: utf-8 -*-
{
    "name": "Audit Planning - Statutory Audit Pakistan",
    "version": "17.0.2.0.0",
    "category": "Accounting/Audit",
    "summary": "ISA-Compliant Statutory Audit Planning with 13 Mandatory Tabs",
    "description": """
Statutory Audit Planning Module for Pakistan - Odoo 17

FULLY COMPLIANT with:
- International Standards on Auditing (ISAs) as adopted in Pakistan
- Companies Act, 2017
- ISQM-1
- IESBA Code of Ethics
- ICAP QCR / AOB inspection requirements

Features:
- 13 Mandatory Planning Tabs (P-1 through P-13)
- Sequential Navigation with Save & Next
- Risk-Based Auto Audit Program Generation
- Audit Planning Memorandum (APM) Auto-Generation
- Partner-Level Control and Sign-offs
- Complete Audit Trail (ISA 230)
- ICAP QCR-Ready Documentation

Tab Structure:
P-1: Engagement Setup & Team Assignment (ISA 210, ISA 220, ISQM-1)
P-2: Understanding the Entity & Environment (ISA 315)
P-3: Internal Control Understanding (ISA 315)
P-4: Preliminary Analytical Procedures (ISA 520)
P-5: Materiality & Performance Materiality (ISA 320)
P-6: Risk Assessment (RMM) (ISA 315)
P-7: Fraud Risk Assessment (ISA 240)
P-8: Going Concern (Preliminary) (ISA 570)
P-9: Laws & Regulations (ISA 250)
P-10: Related Parties Planning (ISA 550)
P-11: Group Audit Planning (ISA 600)
P-12: Audit Strategy & Audit Plan (ISA 300)
P-13: Planning Review & Approval (ISA 220, ISQM-1)
    """,
    "author": "QACO Audit",
    "license": "LGPL-3",
    "depends": [
        "base",
        "mail",
        "web",
        "qaco_audit",
        "qaco_client_onboarding",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/assertion_tags.xml",
        "data/materiality_defaults.xml",
        "data/checklist_data.xml",
        "views/planning_main_views.xml",
        "views/planning_tabs_p1_p6_views.xml",
        "views/planning_tabs_p7_p13_views.xml",
        "views/planning_program_views.xml",
        "views/audit_planning_menu.xml",
        "views/audit_planning_tree.xml",
        "views/audit_planning_form.xml",
        "views/audit_planning_kanban.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "audit_planning/static/src/js/planning_dashboard.js",
            "audit_planning/static/src/js/button_box_limit_patch.js",
            "audit_planning/static/src/css/planning_dashboard.css",
            "audit_planning/static/src/xml/planning_dashboard.xml",
        ],
    },
    "application": True,
    "installable": True,
    "auto_install": False,
}
