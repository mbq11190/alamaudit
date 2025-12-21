{
    "name": "QACO Finalisation Phase",
    "summary": "Finalisation Phase",
    "version": "17.0.1.0",
    "author": "QACO",
    "license": "LGPL-3",
    "category": "Accounting/Auditing",
    "depends": ["qaco_audit", "qaco_execution_phase"],
    "data": [
        "security/ir.model.access.csv",
        "views/finalisation_phase_actions.xml",
        "views/finalisation_phase_form.xml",
        "views/audit_smart_button.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": True,
    "assets": {
        "web.assets_backend": [
            "qaco_planning_phase/static/src/scss/planning.scss",
            "qaco_planning_phase/static/src/css/planning_phase.css",
        ],
    },
}
