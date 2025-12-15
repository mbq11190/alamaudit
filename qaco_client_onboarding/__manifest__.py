# -*- coding: utf-8 -*-
{
    'name': 'QACO Client Onboarding',
    'version': '17.0.1.0.0',
    'category': 'Audit',
    'summary': 'Client Onboarding Phase',
    'description': """
Client Onboarding Module
========================
Client onboarding phase with smart button access from audit.
    """,
    'author': 'QACO',
    'website': 'https://www.qaco.com',
    'depends': ['qaco_audit'],
    'data': [
        'security/ir.model.access.csv',
        'data/audit_standard_library_data.xml',
        'data/audit_onboarding_checklist_data.xml',
        'data/onboarding_seed.xml',
        'views/client_onboarding_form.xml',
        'views/audit_smart_button.xml',
        'reports/client_onboarding_report.xml',
        'reports/client_onboarding_report_template.xml',
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
