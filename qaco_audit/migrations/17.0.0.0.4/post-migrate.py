# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Post-migration script to convert firm_name data from old Selection values to Many2one references
    This runs automatically after module update - no manual intervention needed!
    """
    _logger.info("=" * 70)
    _logger.info("Starting post-migration for qaco_audit 17.0.0.0.4")
    _logger.info("=" * 70)

    try:
        # Check if the old firm_name_old column exists
        cr.execute(
            """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='qaco_audit' AND column_name='firm_name_old'
        """
        )

        if not cr.fetchone():
            _logger.info(
                "No firm_name_old column found - migration not needed or already completed"
            )
            return

        _logger.info("Found firm_name_old column - migrating data...")

        # Mapping of old selection values to firm name XML IDs
        firm_mapping = {
            "Alam Aulakh": "firm_name_alam_aulakh",
            "QACO": "firm_name_qaco",
            "Baker Tilly": "firm_name_baker_tilly",
            "3rd party Firm": "firm_name_3rd_party",
        }

        total_migrated = 0

        # Update each record based on old value
        for old_value, xml_id in firm_mapping.items():
            _logger.info("Migrating records with firm_name_old='%s'...", old_value)

            # Get the ID of the firm name record
            cr.execute(
                """
                SELECT res_id 
                FROM ir_model_data 
                WHERE module='qaco_audit' AND name=%s
                LIMIT 1
            """,
                (xml_id,),
            )

            firm_id_result = cr.fetchone()

            if not firm_id_result:
                _logger.warning(
                    "Could not find firm record for '%s' (xml_id: %s) - skipping",
                    old_value,
                    xml_id,
                )
                continue

            firm_id = firm_id_result[0]

            # Update records
            cr.execute(
                """
                UPDATE qaco_audit
                SET firm_name = %s
                WHERE firm_name_old = %s AND (firm_name IS NULL OR firm_name != %s)
            """,
                (firm_id, old_value, firm_id),
            )

            updated = cr.rowcount
            total_migrated += updated
            _logger.info("✓ Updated %s record(s)", updated)

        # Check for any unmigrated records
        cr.execute(
            """
            SELECT firm_name_old, COUNT(*) 
            FROM qaco_audit 
            WHERE firm_name_old IS NOT NULL AND firm_name IS NULL
            GROUP BY firm_name_old
        """
        )
        unmigrated = cr.fetchall()

        if unmigrated:
            _logger.warning("Found unmigrated records (unknown firm names):")
            for firm, count in unmigrated:
                _logger.warning("  - '%s': %s records (set to NULL)", firm, count)

        # Drop the old column
        _logger.info("Cleaning up: dropping firm_name_old column...")
        cr.execute("ALTER TABLE qaco_audit DROP COLUMN IF EXISTS firm_name_old")
        _logger.info("✓ Old column dropped")

        _logger.info("=" * 70)
        _logger.info("✓ Post-migration completed successfully!")
        _logger.info("  Total records migrated: %s", total_migrated)
        _logger.info("=" * 70)

    except Exception as e:
        _logger.error("Error during post-migration: %s", str(e))
        _logger.error("You may need to check firm_name data manually")
        # Don't raise - let the migration continue
