{
    'name': "QACO Audit",

    'summary': "Audit Work Management",

    'description': """
    Audit Workflow Management of QACO
    """,

    'author': "QACO",
    'website': "https://www.qaco.com.pk",

    'category': 'Uncategorized',
    'version': '17.0.0.0.5',

    'depends': ['base', 'mail', 'hr', 'project', 'web', 'qaco_employees'],

    'pre_init_hook': 'pre_init_hook',
    'uninstall_hook': 'uninstall_hook',

    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'security/audit_security_rules.xml',
        'views/auto_follower_views.xml',
        'views/menu_view.xml',
        'data/firm_name_data.xml',
        'views/tree_view.xml',
        'views/firm_name_views.xml',
        'views/form_view.xml',
        'views/kanban_view.xml',
        'data/qaco_engagement_sequence.xml',
        'data/audit_document_sequences.xml',
        'views/audit_attachment_views.xml',
        'views/audit_changelog_views.xml',
        'data/audit_stages_data.xml',
        'views/search_view.xml',
        'data/audit_year_data.xml',
        'data/sequence.xml',
        'wizard/audit_done_view.xml',
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
