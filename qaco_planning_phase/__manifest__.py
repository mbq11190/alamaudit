{
    "name": "QACO Planning Phase (ISA)",
    "summary": "ISA-aligned audit planning: strategy, materiality, risk assessment, checklist, PBC, timeline",
    "version": "17.0.1.1",
    "author": "QACO",
    "license": "LGPL-3",
    "depends": ["base", "mail", "qaco_audit"],
    "data": [
        "security/ir.model.access.csv",
        "data/sequence_data.xml",
        "data/industry_sector_data.xml",
        "views/planning_views.xml",
    ],
    "application": False,
    "installable": True,
    "category": "Accounting/Auditing",
}
