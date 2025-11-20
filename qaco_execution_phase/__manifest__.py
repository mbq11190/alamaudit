{
    "name": "QACO Execution Phase",
    "summary": "Execution Phase",
    "version": "17.0.1.0",
    "author": "QACO",
    "license": "LGPL-3",
    "category": "Accounting/Auditing",
    "depends": ["qaco_audit", "qaco_planning_phase"],
    "data": [
        "security/ir.model.access.csv",
        "views/execution_phase_actions.xml",
        "views/execution_phase_form.xml",
        "views/audit_smart_button.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": True,
}
