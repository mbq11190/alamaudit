# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

from odoo import api


class TestMigrationProblematicFields(TransactionCase):
    def setUp(self):
        super(TestMigrationProblematicFields, self).setUp()
        self.env = self.env
        self.cr = self.env.cr

    def test_migration_backups_and_clears_relations(self):
        # Create a fake ir_model_fields row referencing a non-existent model
        Model = self.env['ir.model']
        # use an existing model for 'model' to avoid integrity issues
        partner_model = self.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
        self.assertTrue(partner_model, 'res.partner model must exist for test')

        # insert a problematic field record directly using SQL to bypass ORM checks
        self.cr.execute(
            "INSERT INTO ir_model_fields (model, name, field_description, ttype, relation) VALUES (%s,%s,%s,%s,%s) RETURNING id",
            (partner_model.model, 'tmp_missing_rel', 'Temp missing rel', 'many2one', 'non.existent.model'),
        )
        fid = self.cr.fetchone()[0]

        # Run migration
        from qaco_client_onboarding.migrations._import_helper import import_module
        # import and call migration function
        mod = import_module('qaco_client_onboarding.migrations.17.0.1.8.post_migration')
        mod.migrate(self.cr, '17.0.1.8')

        # Assert backup row created
        self.cr.execute("SELECT id FROM backup_problematic_ir_model_fields WHERE id=%s", (fid,))
        self.assertTrue(self.cr.fetchone(), 'Backup row must exist')

        # Assert the original field's relation was cleared
        self.cr.execute("SELECT relation FROM ir_model_fields WHERE id=%s", (fid,))
        rel = self.cr.fetchone()
        self.assertTrue(rel and rel[0] is None, 'Relation should be cleared by migration')

        # Assert migration log entry exists
        self.cr.execute("SELECT field_id, action FROM qaco_problematic_fields_migration_log WHERE field_id=%s", (fid,))
        log = self.cr.fetchone()
        self.assertTrue(log and log[0] == fid and log[1] == 'cleared_relation')

        # cleanup: remove created ir_model_fields record and backup/log rows
        self.cr.execute("DELETE FROM ir_model_fields WHERE id=%s", (fid,))
        self.cr.execute("DELETE FROM backup_problematic_ir_model_fields WHERE id=%s", (fid,))
        self.cr.execute("DELETE FROM qaco_problematic_fields_migration_log WHERE field_id=%s", (fid,))
