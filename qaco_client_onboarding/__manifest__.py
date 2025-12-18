# -*- coding: utf-8 -*-
{
    'name': 'QACO Client Onboarding',
    'version': '17.0.1.1.0',
    'category': 'Audit',
    'summary': 'Client Onboarding Phase with Auto-Generated Reports',
    'description': """
Client Onboarding Module
========================
Client onboarding phase with smart button access from audit.

Features:
- Comprehensive client acceptance workflow
- ISA-referenced mandatory documentation
- Auto-generated reports upon Partner Approval:
  • Client Acceptance & Continuance Report (ISA 220, ISQM-1)
  • Ethics & Independence Compliance Report (IESBA Code, ISA 220)
  • Fraud & Business Risk Summary (ISA 240, ISA 315)
  • Engagement Authorization Memorandum (ISA 210, ISQM-1)
- ICAP QCR Ready documentation
- Time-stamped, Partner-signed reports
    """,
    'author': 'QACO',
    'website': 'https://www.qaco.com',
    'depends': ['qaco_audit'],
    'data': [
        'security/ir.model.access.csv',
        'data/pakistan_location_data.xml',
        'data/onboarding_template_data.xml',
        'data/audit_standard_library_data.xml',
        'data/audit_onboarding_checklist_data.xml',
        'data/onboarding_seed.xml',
        'views/client_onboarding_form.xml',
        'views/audit_smart_button.xml',
        'reports/client_onboarding_report.xml',
        'reports/client_onboarding_report_template.xml',
        'reports/report_acceptance_continuance.xml',
        'reports/report_ethics_independence.xml',
        'reports/report_fraud_business_risk.xml',
        'reports/report_engagement_authorization.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'qaco_client_onboarding/static/src/scss/onboarding.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': True,
    'license': 'LGPL-3',
}
