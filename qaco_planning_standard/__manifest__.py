{
    "name": "QACO Planning Standard",
    "summary": "ISA-aligned audit planning: strategy, materiality, risk assessment, checklist, PBC, milestones",
    "version": "17.0.1.0",
    "author": "QACO",
    "license": "LGPL-3",
    "depends": ["base", "mail", "qaco_audit"],
    "data": [
        "security/ir.model.access.csv",
        "views/planning_views.xml",
        "data/sequence_data.xml",
    ],
    "application": False,
    "installable": True,
    "category": "Accounting/Auditing",
}
