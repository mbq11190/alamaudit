# -*- coding: utf-8 -*-
import base64
from odoo.tests.common import TransactionCase


class TestP3AttachmentCounts(TransactionCase):
    def test_attachment_counts_store_and_update(self):
        Partner = self.env["res.partner"]
        Audit = self.env["qaco.audit"]
        P3 = self.env["qaco.planning.p3.controls"]
        Attachment = self.env["ir.attachment"]

        partner = Partner.create({"name": "AttachmentCountClient"})
        audit = Audit.create({"client_id": partner.id})

        p3 = P3.create({"audit_id": audit.id})

        # Initially counts should be zero
        self.assertEqual(p3.flowchart_count, 0)
        self.assertEqual(p3.walkthrough_doc_count, 0)

        # Create an attachment and link to flowcharts
        data = base64.b64encode(b"testpdf").decode()
        attach = Attachment.create({"name": "flow1.pdf", "datas": data, "mimetype": "application/pdf"})
        p3.process_flowchart_ids = [(4, attach.id)]

        # After linking, stored counts should update to 1
        p3.refresh()
        self.assertEqual(p3.flowchart_count, 1)

        # Add a walkthrough doc
        attach2 = Attachment.create({"name": "walk1.pdf", "datas": data, "mimetype": "application/pdf"})
        p3.walkthrough_doc_ids = [(4, attach2.id)]
        p3.refresh()
        self.assertEqual(p3.walkthrough_doc_count, 1)
