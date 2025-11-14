# -*- coding: utf-8 -*-


{
    'name': "QACO Employees",

    'summary': "QACO Employees Database Management System",

    'description': """
QACO Employees Database Management System
    """,

    'author': "QACO",
    'website': "https://www.qaco.com.pk",

    'category': 'Uncategorized',

    'version': '17.0.0.0.10',


    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'hr', 'project', 'web',
                'hr_attendance', 'hr_holidays', 'hr_expense'],


    # always loaded
    'data': [
        'views/qaco_employees_form_view.xml',
        'security/security_groups.xml',
        'security/security_rules.xml',
        'security/ir.model.access.csv',
        'views/transfer_view.xml',
        'views/transfer_cc_recipient_views.xml',
        'views/search_view.xml',
        'wizard/leave_adjustment_reject_wizard_view.xml',
        'views/leave_summary_views.xml',
        'views/qaco_employees_tree_view.xml',
        'wizard/leave_adjustment_reject_wizard_view.xml',
        'views/leave_adjustment_email_template.xml',
        'views/leave_adjustment_templates.xml',
        'views/leave_condonation_email_template.xml',
        'views/leave_condonation_templates.xml',
        'views/leave_condonation_views.xml',
        # Restrict leave cancellation to QACO employees administrators
        'views/hr_leave_views.xml',
        # Hide employee create button and make user form employee/partner editable
        'views/hr_employee_no_create.xml',
        'views/email_transfer_request.xml',
        'views/email_transfer_expired.xml',
        'views/unallocated_employee_recipient_views.xml',
        'data/designation_data.xml',
        'data/region_data.xml',
        'data/sequence.xml',
        'data/cron_weekly_employee_report.xml',
        'data/leave_condonation_sequence.xml',
        'data/cron_unallocated_daily_notify.xml',
        'data/cron_pending_transfers.xml',
        'data/cron_geofence_reconcile.xml',
        'data/cron_daily_attendance_report.xml',
        'data/cron_unallocated_expiry_employees.xml',
        'data/cron_email_leave_summary_to_employees.xml',
        'security/menu_restrictions.xml',
        'views/timeoff_menu_inherit.xml',
        'data/menu_sequence.xml',
    ],
    'images': [
            'static/description/icon.svg',],

    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'OPL-1',
}



