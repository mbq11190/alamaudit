{
    'name': 'QACO Planning Phase',
    'version': '17.0.1.0.0',
    'category': 'Audit',
    'summary': 'Planning Phase for Audit Process',
    'description': """
        Planning Phase Module
        ======================
        This module manages the planning phase of the audit process including:
        - Client Industry & Sector information
        - Planning notebook/checklist
    """,
    'author': 'QACO',
    'website': '',
    'depends': ['base', 'qaco_audit'],
    'data': [
        'security/ir.model.access.csv',
        'data/industry_sector_data.xml',
        'views/industry_sector_views.xml',
        'views/planning_phase_views.xml',
        'views/menu_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
