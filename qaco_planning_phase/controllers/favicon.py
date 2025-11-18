from odoo import http
from odoo.http import request


class QacoFavicon(http.Controller):
    @http.route("/favicon.ico", type="http", auth="none", csrf=False, db=False)
    def favicon(self, **_params):
        headers = [
            ("Cache-Control", "public, max-age=86400"),
        ]
        return request.make_response("", headers=headers, status=204)