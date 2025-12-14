# -*- coding: utf-8 -*-
{
    "name": "Audit Planning",
    "version": "17.0.1.0",
    "category": "Accounting/Audit",
    "summary": "Audit planning aligned with ISA standards",
    "description": """Manage audit planning with ISA 300/315/320/330/520/550/240 compliance, progress dashboards, and approvals.""",
    "author": "Your Company",
    "license": "LGPL-3",
    "depends": [
        "base",
        "mail",
        "web",
        "documents",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/checklist_data.xml",
        "views/audit_planning_menu.xml",
        "views/audit_planning_tree.xml",
        "views/audit_planning_form.xml",
        "views/audit_planning_kanban.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "audit_planning/static/src/js/planning_dashboard.js",
            "audit_planning/static/src/css/planning_dashboard.css",
            "audit_planning/static/src/xml/planning_dashboard.xml",
        ],
    },
    "application": True,
    "installable": True,
}
