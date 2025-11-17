# -*- coding: utf-8 -*-
{
    'name': 'QACO Quality Review',
    'version': '17.0.1.0.0',
    'category': 'Audit',
    'summary': 'Engagement Quality Control Review (EQCR) and quality assurance',
    'description': """
Quality Review Module
=====================
Comprehensive quality control and review process including:
- Engagement Quality Control Review (EQCR)
- Hot review (concurrent review)
- Cold review (post-completion review)
- Peer review
- Compliance checklist
- Quality findings and remediation
- File completeness review
- Professional standards compliance
- Technical review and sign-off
    """,
    'author': 'QACO',
    'website': 'https://www.qaco.com',
    'depends': ['qaco_audit', 'qaco_deliverables'],
    'data': [
        'security/ir.model.access.csv',
        'data/quality_review_sequence.xml',
        'data/review_checklist_data.xml',
        'views/quality_review_views.xml',
        'views/audit_extension_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
