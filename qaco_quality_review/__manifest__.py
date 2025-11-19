{
    "name": "QACO Quality Review",
    "summary": "Quality Review",
    "version": "17.0.1.0",
    "author": "QACO",
    "license": "LGPL-3",
    "category": "Accounting/Auditing",
    "depends": ["qaco_audit", "qaco_deliverables"],
    "data": [
        "security/ir.model.access.csv",
        "views/quality_review_form.xml",
        "views/audit_smart_button.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "qaco_quality_review/static/src/css/quality_review.css",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": True,
}
