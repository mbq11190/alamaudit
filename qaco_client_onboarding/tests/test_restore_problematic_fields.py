# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from qaco_client_onboarding.migrations import _import_helper


class TestRestoreProblematicFields(TransactionCase):
    def setUp(self):
        super().setUp()
        self.cr = self.env.cr

    def test_restore_deleted_field(self):
        # Create a new temp ir_model_fields row and copy to backup and delete original
        model_rec = self.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
        self.assertTrue(model_rec)
        # Insert a new problematic field directly
        self.cr.execute("INSERT INTO ir_model_fields (model, name, field_description, ttype, relation) VALUES (%s,%s,%s,%s,%s) RETURNING id",
                        (model_rec.model, 'tmp_restore_test', 'Tmp', 'many2one', 'non.existent.model'))
        fid = self.cr.fetchone()[0]
        # Copy into backup table
        self.cr.execute("INSERT INTO backup_problematic_ir_model_fields SELECT * FROM ir_model_fields WHERE id=%s", (fid,))
        # Delete the original
        self.cr.execute("DELETE FROM ir_model_fields WHERE id=%s", (fid,))

        # Call restore helper
        from scripts.restore_problematic_fields import restore_fields
        res = restore_fields(self.cr, [fid], dry_run=False, force=False)
        self.assertIn(fid, res['restored'])

        # confirm row exists again in ir_model_fields
        self.cr.execute("SELECT id, model, name, relation FROM ir_model_fields WHERE id=%s", (fid,))
        row = self.cr.fetchone()
        self.assertTrue(row)
        self.assertEqual(row[0], fid)
        self.assertEqual(row[2], 'tmp_restore_test')

        # confirm a migration log entry exists
        self.cr.execute("SELECT action FROM qaco_problematic_fields_migration_log WHERE field_id=%s ORDER BY created_at DESC LIMIT 1", (fid,))
        log = self.cr.fetchone()
        self.assertTrue(log and log[0] == 'restored')

        # cleanup
        self.cr.execute("DELETE FROM ir_model_fields WHERE id=%s", (fid,))
        self.cr.execute("DELETE FROM backup_problematic_ir_model_fields WHERE id=%s", (fid,))
        self.cr.execute("DELETE FROM qaco_problematic_fields_migration_log WHERE field_id=%s", (fid,))
