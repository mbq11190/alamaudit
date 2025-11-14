{
    'name': 'QACO Finalisation Phase',
    'version': '17.0.1.0.0',
    'category': 'Services/Audit',
    'summary': 'Audit Finalisation Phase - Reporting, Review, Quality Control & Sign-off',
    'description': """
        Comprehensive Audit Finalisation Phase Management
        ==============================================
        
        This module manages the finalisation phase of audit engagements including:
        * Audit report drafting and review
        * Quality control and review process
        * Client discussions and meetings
        * Adjustments and corrections
        * Management representation letters
        * Report sign-off and approval
        * Deliverables tracking
        * Post-audit file completion
        * Archiving and documentation
    """,
    'author': 'QACO',
    'website': 'https://www.qaco.com',
    'depends': ['qaco_audit', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/report_type_data.xml',
        'views/finalisation_phase_views.xml',
        'views/qaco_audit_form_extend.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
