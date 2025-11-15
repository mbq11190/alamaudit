{
    "name": "Audit Planning Compliance",
    "version": "17.0.1.0",
    "summary": "ISA 300/315/320 aligned planning workflow with ICAP/SECP localization",
    "category": "Accounting/Audit",
    "depends": [
        "base",
        "mail",
        "document",
        "hr",
        "account"
    ],
    "data": [
        "security/audit_security.xml",
        "security/ir.model.access.csv",
        "data/audit_config_data.xml",
        "data/pbc_templates.xml",
        "data/mail_templates.xml",
        "data/cron_jobs.xml",
        "views/audit_menus.xml",
        "views/audit_engagement_views.xml",
        "views/audit_materiality_views.xml",
        "views/audit_risk_views.xml",
        "views/audit_pbc_views.xml",
        "views/audit_staff_views.xml",
        "views/audit_timeline_views.xml",
        "views/audit_settings_views.xml",
        "reports/planning_memorandum_templates.xml",
        "reports/planning_memorandum_report.xml",
        "data/demo_data.xml"
    ],
    "demo": [],
    "application": True,
    "installable": True,
    "license": "LGPL-3"
}
