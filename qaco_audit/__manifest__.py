{
    'name': "QACO Audit",

    'summary': "Audit Work Management",

    'description': """
    Audit Workflow Management of QACO
    """,

    'author': "QACO",
    'website': "https://www.qaco.com.pk",

    'category': 'Uncategorized',
    'version': '17.0.0.0.3',

    'depends': ['base', 'mail', 'hr', 'project', 'web', 'qaco_employees'],

    'data': [
        'security/ir.model.access.csv',
        'security/security_groups.xml',
        'views/tree_view.xml',
        'views/auto_follower_views.xml',
        'views/menu_view.xml',
        'views/form_view.xml',
        'views/kanban_view.xml',
        'views/quarterly_audit_views.xml',
        'views/audit_attachment_views.xml',
        'data/audit_stages_data.xml',
        'data/audit_quarter_stage_data.xml',
        'data/annual_audit_stages_data.xml',
        'views/search_view.xml',
        'data/audit_year_data.xml',
        'data/annual_audit_year_data.xml',
        'data/sequence.xml',
        'data/quarterly_audit_sequence.xml',
        'data/annual_audit_sequence.xml',
        'data/auto_create_delete_quarters.xml',
        'data/audit_quarter_2025_data.xml',
        'data/monthly_audit_month_data.xml',
        'data/monthly_audit_stages_data.xml',
        'data/monthly_internal_audit_sequence.xml',
        'data/auto_create_delete_months.xml',
        'views/monthly_internal_audit_views.xml',
        'views/monthly_internal_audit_menu.xml',
        'wizard/audit_done_view.xml',
        'views/annual_audit_views.xml',
    ],
    'images': [
        'static/description/icon.svg',],

    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'OPL-1',

    # 'assets': {
    #     'web._assets_primary_variables': [
    #         ('prepend', 'corporate/static/src/scss/primary_variables.scss'),
    #     ],
    # },

}
