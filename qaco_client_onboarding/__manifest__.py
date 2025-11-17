# -*- coding: utf-8 -*-
{
    'name': 'QACO Client Onboarding',
    'version': '17.0.1.0.0',
    'category': 'Audit',
    'summary': 'Client acceptance, KYC, due diligence, and engagement process',
    'description': """
Client Onboarding Module
========================
Comprehensive client acceptance and onboarding workflow including:
- Client acceptance evaluation
- KYC (Know Your Client) documentation
- Due diligence and background checks
- Conflict of interest checks
- Independence assessment
- Engagement letter generation and acceptance
- Terms and conditions agreement
- Fee proposal and approval
    """,
    'author': 'QACO',
    'website': 'https://www.qaco.com',
    'depends': ['qaco_audit'],
    'data': [
        'security/ir.model.access.csv',
        'data/onboarding_sequence.xml',
        'data/onboarding_status_data.xml',
        'views/client_onboarding_views.xml',
        'views/audit_extension_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
