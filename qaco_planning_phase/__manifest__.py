{
    "name": "QACO Planning Phase (ISA)",
    "summary": "Planning Phase",
    "version": "17.0.1.12",
    "author": "QACO",
    "license": "LGPL-3",
    "category": "Accounting/Auditing",
    "depends": ["qaco_audit", "qaco_client_onboarding"],
    "data": [
        "security/ir.model.access.csv",
        "views/planning_phase_form.xml",
        "views/planning_phase_views.xml",
        "views/audit_smart_button.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": True,
}
