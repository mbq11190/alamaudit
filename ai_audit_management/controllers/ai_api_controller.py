from odoo import http
from odoo.http import request


class AIAuditController(http.Controller):
    @http.route("/ai_audit/health", type="json", auth="user")
    def health(self):
        return {"status": "ok"}

    @http.route("/ai_audit/chatbot", type="json", auth="user")
    def chatbot(self, prompt=None):
        if not prompt:
            return {"error": "Prompt required"}
        # Use a sudoed transient helper to reuse _call_openai logic safely
        helper = request.env["audit.ai.helper.mixin"].sudo()
        try:
            reply = helper._call_openai(
                prompt,
                model=request.env["audit.ai.settings"]
                .sudo()
                .get_active_settings()
                .model_version,
            )
        except Exception as exc:  # broad to surface user-friendly message
            return {"error": str(exc)}
        return {"reply": reply}

    @http.route("/ai_audit/vision_ocr", type="json", auth="user")
    def vision_ocr(self, document_id=None):
        if not document_id:
            return {"error": "document_id required"}
        doc = request.env["audit.ocr.document"].sudo().browse(int(document_id))
        if not doc.exists():
            return {"error": "Document not found"}
        doc.action_run_ocr()
        return {
            "status": "processed",
            "text": doc.extracted_text,
            "summary": doc.ai_summary,
        }
