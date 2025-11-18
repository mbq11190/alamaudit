from odoo import http
from odoo.http import request


class QacoServiceWorker(http.Controller):
    @http.route("/web/service-worker.js", type="http", auth="none", csrf=False, db=False)
    def service_worker(self, **_kwargs):
        script = """
self.addEventListener('install', (event) => self.skipWaiting());
self.addEventListener('activate', (event) => event.waitUntil(self.clients.claim()));
self.addEventListener('fetch', (event) => {
    if (event.request.method !== 'GET') {
        return;
    }
    event.respondWith(fetch(event.request));
});
""".strip()
        headers = [
            ("Content-Type", "application/javascript"),
            ("Cache-Control", "public, max-age=0, s-maxage=0"),
        ]
        return request.make_response(script, headers=headers)
