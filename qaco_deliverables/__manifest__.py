# -*- coding: utf-8 -*-
{
    'name': 'QACO Audit Deliverables',
    'version': '17.0.1.0.0',
    'category': 'Audit',
    'summary': 'Audit deliverables management and distribution tracking',
    'description': """
Audit Deliverables Module
==========================
Comprehensive deliverables management including:
- Audit reports (standard, modified, adverse, disclaimer)
- Financial statements
- Management letters and representations
- Tax returns and compliance certificates
- Regulatory filings
- Deliverable distribution tracking
- Client acknowledgment and sign-off
- Document versioning and revisions
    """,
    'author': 'QACO',
    'website': 'https://www.qaco.com',
    'depends': ['qaco_audit', 'qaco_finalisation_phase'],
    'data': [
        'security/ir.model.access.csv',
        'data/deliverable_sequence.xml',
        'data/deliverable_type_data.xml',
        'views/deliverables_views.xml',
        'views/audit_extension_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
