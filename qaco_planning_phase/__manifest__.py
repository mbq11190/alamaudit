{
    'name': 'QACO Planning Phase (ISA)',
    'version': '17.0.1.1',
    'category': 'Accounting/Auditing',
    'summary': 'ISA-aligned audit planning: strategy, materiality, risk assessment, checklist, PBC, timeline',
    'description': """
        Planning Phase Module
        ======================
        This module manages the planning phase of the audit process including:
        - Client Industry & Sector information
        - Planning notebook/checklist
    """,
    'author': 'QACO',
    'website': '',
    'depends': ['base', 'mail', 'qaco_audit'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/industry_sector_data.xml',
        'views/planning_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
