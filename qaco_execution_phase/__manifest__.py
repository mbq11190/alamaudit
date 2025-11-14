{
    'name': 'QACO Execution Phase',
    'version': '17.0.1.0.0',
    'category': 'Services/Audit',
    'summary': 'Audit Execution Phase - Fieldwork, Testing, Evidence & Findings',
    'description': """
        Comprehensive Audit Execution Phase Management
        ==============================================
        
        This module manages the execution phase of audit engagements including:
        * Fieldwork planning and tracking
        * Audit testing procedures
        * Evidence collection and documentation
        * Findings and observations management
        * Working papers organization
        * Time and resource tracking
        * Team member assignments
        * Testing checklists and completion tracking
    """,
    'author': 'QACO',
    'website': 'https://www.qaco.com',
    'depends': ['qaco_audit', 'qaco_planning_phase', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/testing_category_data.xml',
        'views/execution_phase_views.xml',
        'views/qaco_audit_form_extend.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
