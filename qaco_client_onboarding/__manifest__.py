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
        'views/client_onboarding_form.xml',
        'views/audit_smart_button.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
    'license': 'LGPL-3',
}
