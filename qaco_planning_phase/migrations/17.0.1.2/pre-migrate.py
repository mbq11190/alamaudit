def migrate(cr, version):
    """
    Remove duplicate industry sector records to avoid unique constraint violations.
    This handles cases where records were created without proper XML IDs.
    """
    if not version:
        return

    # Delete existing industry sector records that might cause duplicates
    # Only delete if they don't have any references from planning records
    cr.execute("""
        DELETE FROM planning_industry_sector
        WHERE id NOT IN (
            SELECT DISTINCT industry_sector_id 
            FROM qaco_planning_phase 
            WHERE industry_sector_id IS NOT NULL
        )
    """)
