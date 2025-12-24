{
    "name": "Audit Planning Phase - Pakistan Statutory Audit",
    "summary": "Zero-deficiency ISA-compliant planning workflow (P-1 to P-13) for statutory audits in Pakistan",
    "version": "17.0.1.0.0",
    "author": "QACO",
    "website": "https://alamaudit.thinkoptimise.com",
    "license": "LGPL-3",
    "category": "Audit",
    "depends": [
        "base",
        "mail",
        "web",
        "qaco_audit",
    ],
    "data": [
        # Security
        "security/planning_phase_security.xml",
        "security/ir.model.access.csv",
        # P-1 to P-13 Views
        "views/planning_p1_views.xml",
        "views/planning_p2_views.xml",
        "views/planning_p3_views.xml",
        "views/planning_p4_views.xml",
        "views/planning_p5_views.xml",
        "views/planning_p10_views.xml",
        "views/planning_p11_views.xml",
        "views/planning_p10_related_parties_views.xml",
        "views/planning_p12_views.xml",
        "views/planning_p13_views.xml",
        # Legacy Views (for backward compatibility)
        "views/planning_phase_views.xml",
        "views/supporting_views.xml",
        "views/planning_phase_actions.xml",
        "views/audit_smart_button.xml",
        # Dashboard
        "views/planning_dashboard_views.xml",
        # Templates (Session 7B)
        "views/planning_template_views.xml",
        # Menu Structure
        "views/planning_menu.xml",
        # Data
        "data/industry_data.xml",
        "data/mail_templates.xml",  # Session 7A: Email notifications
        # "data/planning_templates.xml",  # Session 7B: Industry templates - DISABLED: XML schema issues
        "data/regulator_data.xml",
        "data/assertion_tags.xml",
        "data/materiality_defaults.xml",
        "data/checklist_data.xml",
    ],
    "demo": [
        "demo/planning_phase_demo.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "qaco_planning_phase/static/src/scss/planning.scss",
            "qaco_planning_phase/static/src/css/planning_phase.css",
        ],
    },
    "installable": True,
    "application": False,  # Not a standalone app - accessed via Audit Work smart button
    "auto_install": True,
    "price": 0,
    "currency": "PKR",
    "description": "Audit Planning Phase module covering planning tabs P-1 to P-13 (ISA-aligned).",
}
