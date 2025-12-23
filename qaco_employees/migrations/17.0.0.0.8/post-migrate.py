def migrate(cr, version):
    cr.execute(
        """SELECT 1 FROM pg_constraint WHERE conname='leave_adjustment_approval_unique_adjustment_validator'"""
    )
    if cr.fetchone():
        cr.execute(
            """ALTER TABLE leave_adjustment_approval
               DROP CONSTRAINT leave_adjustment_approval_unique_adjustment_validator"""
        )
