Clearance Pack attachment bundling

Feature: Auto-merge small PDF attachments into the Clearance Correspondence Pack bundle.

Behaviour:
- Only attachments with mimetype `application/pdf` and size <= `qaco_client_onboarding.pack_attachment_max_kb` (default 512 KB) are merged into the bundle.
- Other attachments are skipped and listed in the attachment's description for manual inclusion or review.
- The merged bundle is saved as an `ir.attachment` on the `qaco.onboarding.predecessor.request` record, named `clearance_pack_bundle_<id>.pdf`.

Configuration:
- The threshold is configurable via Settings → Audit → Onboarding, field "Pack attachments max size (KB)".
- Default provided via `data/independence_seed.xml` as 512 KB.

Implementation notes:
- Merging uses `pypdf` (preferred) or falls back to `PyPDF2` if present. Add one of these to the Python env if desired.
- If no PDF merger library is available on the server, the system will still generate the base pack PDF but will not merge attachments.
