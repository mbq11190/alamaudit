# -*- coding: utf-8 -*-
"""Pre-migration script to add res.partner extension fields."""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Add res.partner extension fields if they don't exist."""
    _logger.info("Running pre-migration for qaco_planning_phase 17.0.1.11")
    
    # Check if columns exist before adding them
    partner_columns = [
        ("is_qaco_client", "BOOLEAN"),
        ("legal_name", "VARCHAR"),
        ("trade_name", "VARCHAR"),
        ("incorporation_no", "VARCHAR"),
        ("incorporation_date", "DATE"),
        ("legal_form", "VARCHAR"),
        ("business_description", "TEXT"),
        ("regulatory_body", "VARCHAR"),
        ("regulatory_license_no", "VARCHAR"),
        ("regulatory_license_expiry", "DATE"),
    ]
    
    for column_name, column_type in partner_columns:
        cr.execute(
            """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='res_partner' AND column_name=%s
            """,
            (column_name,)
        )
        if not cr.fetchone():
            _logger.info(f"Adding column {column_name} to res_partner")
            if column_type == "BOOLEAN":
                cr.execute(
                    f"ALTER TABLE res_partner ADD COLUMN {column_name} BOOLEAN DEFAULT FALSE"
                )
            elif column_type == "DATE":
                cr.execute(
                    f"ALTER TABLE res_partner ADD COLUMN {column_name} DATE"
                )
            elif column_type == "TEXT":
                cr.execute(
                    f"ALTER TABLE res_partner ADD COLUMN {column_name} TEXT"
                )
            else:  # VARCHAR
                cr.execute(
                    f"ALTER TABLE res_partner ADD COLUMN {column_name} VARCHAR"
                )
        else:
            _logger.info(f"Column {column_name} already exists in res_partner")
    
    # Add qaco_risk_assessment columns for stored computed/related fields
    # Check if table exists first
    cr.execute(
        """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name='qaco_risk_assessment'
        """
    )
    if cr.fetchone():
        risk_assessment_columns = [
            ("audit_id", "INTEGER"),  # stored related field
            ("overall_assessment", "VARCHAR"),
            ("risk_score", "INTEGER"),
        ]
        
        for column_name, column_type in risk_assessment_columns:
            cr.execute(
                """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='qaco_risk_assessment' AND column_name=%s
                """,
                (column_name,)
            )
            if not cr.fetchone():
                _logger.info(f"Adding column {column_name} to qaco_risk_assessment")
                if column_type == "INTEGER":
                    cr.execute(
                        f"ALTER TABLE qaco_risk_assessment ADD COLUMN {column_name} INTEGER"
                    )
                else:  # VARCHAR
                    cr.execute(
                        f"ALTER TABLE qaco_risk_assessment ADD COLUMN {column_name} VARCHAR"
                    )
            else:
                _logger.info(f"Column {column_name} already exists in qaco_risk_assessment")
    else:
        _logger.info("Table qaco_risk_assessment does not exist yet, will be created by ORM")
    
    _logger.info("Pre-migration for qaco_planning_phase 17.0.1.11 completed")
