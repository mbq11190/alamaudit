{
    "name": "QACO Deliverables",
    "summary": "Audit Deliverables",
    "version": "17.0.1.0",
    "author": "QACO",
    "license": "LGPL-3",
    "category": "Accounting/Auditing",
    "depends": ["qaco_audit", "qaco_finalisation_phase"],
    "data": [
        "security/ir.model.access.csv",
        "views/deliverables_actions.xml",
        "views/deliverables_form.xml",
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
