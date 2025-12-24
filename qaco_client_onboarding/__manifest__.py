# -*- coding: utf-8 -*-
{
    "name": "QACO Client Onboarding",
    "version": "17.0.1.0.1",
    "category": "Audit",
    "summary": "Client Onboarding Phase with Auto-Save & Auto-Generated Reports",
    "description": """
Client Onboarding Module
========================
Client onboarding phase with smart button access from audit.

Features:
- Comprehensive client acceptance workflow
- ISA-referenced mandatory documentation
- AUTO-SAVE functionality (Sections 1.0-1.10):
  - Auto-save every 10 seconds
  - Auto-save on field change (debounced)
  - Respects Partner Approval lock
  - Full audit trail maintained (ISA 230 / ISQM-1)
  - Visual "Saved at HH:MM" indicator
- Auto-generated reports upon Partner Approval:
  - Client Acceptance & Continuance Report (ISA 220, ISQM-1)
  - Ethics & Independence Compliance Report (IESBA Code, ISA 220)
  - Fraud & Business Risk Summary (ISA 240, ISA 315)
  - Engagement Authorization Memorandum (ISA 210, ISQM-1)
- ICAP QCR Ready documentation
- Time-stamped, Partner-signed reports
- Downloadable Fit & Proper Assessment Template (Word/PDF)
- Notebooks with Save & Next functionality:
  - Auto-save every 30 seconds
  - Draft recovery and session persistence
  - Sequential note navigation
    """,
    "author": "QACO",
    "website": "https://www.qaco.com",
    "depends": ["qaco_audit"],
    "data": [
        "security/ir.model.access.csv",
        "data/pakistan_location_data.xml",
        "data/onboarding_template_data.xml",
        "views/onboarding_template_views.xml",
        "data/audit_standard_library_data.xml",
        "data/audit_onboarding_checklist_data.xml",
        "data/onboarding_seed.xml",
        "data/independence_seed.xml",
        "data/fix_attach_button_override.xml",
        "data/document_vault_security.xml",
        "data/document_vault_taxonomy.xml",
        "data/decision_drivers.xml",
        "views/final_authorization_views.xml",
        "views/onboarding_decision_views.xml",
        "views/document_vault_views.xml",
        "views/audit_export_views.xml",
        "views/client_onboarding_form.xml",
        "views/res_config_settings_views.xml",
        "data/onboarding_menu.xml",
        "data/settings_menu.xml",
        "data/decision_menu.xml",
        "data/document_vault_menu.xml",
        "views/onboarding_attach_wizard_views.xml",
        # "views/client_onboarding_template_section.xml",  # Temporarily disabled - requires full form structure
        "views/audit_smart_button.xml",
        "views/notebook_views.xml",
        "reports/client_onboarding_report.xml",
        "reports/client_onboarding_report_template.xml",
        "reports/report_acceptance_continuance.xml",
        "reports/report_ethics_independence.xml",
        "reports/report_fraud_business_risk.xml",
        "reports/report_engagement_authorization.xml",
        "reports/report_engagement_decision.xml",
        "reports/report_predecessor_clearance_memo.xml",
        "reports/report_predecessor_clearance_pack.xml",
        "reports/report_audit_snapshot.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "qaco_client_onboarding/static/src/scss/onboarding.scss",
            "qaco_client_onboarding/static/src/scss/templates_section.scss",
            "qaco_client_onboarding/static/src/js/onboarding_autosave.esm.js",
            "qaco_client_onboarding/static/src/js/save_next_widget.esm.js",
            "qaco_client_onboarding/static/src/js/attach_selected.js",
            "qaco_client_onboarding/static/src/js/templates_ui.js",
            "qaco_client_onboarding/static/src/xml/save_next_templates.xml",
        ],
    },
    "web.qunit_suite_tests": [
        "qaco_client_onboarding/static/tests/templates_ui_tests.esm.js",
    ],
    "external_dependencies": {
        "python": ["pypdf", "PyPDF2"],
    },
    # Note: python-docx and weasyprint are optional for Word/PDF generation
    # If not installed, the system falls back to HTML-based downloads
    "installable": True,
    "application": False,
    "auto_install": True,
    "pre_init_hook": "pre_init_hook",
    "license": "LGPL-3",
}
