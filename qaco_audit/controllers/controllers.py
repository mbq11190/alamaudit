# -*- coding: utf-8 -*-
# from odoo import http


# class Corporate(http.Controller):
#     @http.route('/tax/tax', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tax/tax/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('tax.listing', {
#             'root': '/tax/tax',
#             'objects': http.request.env['qaco.corporate'].search([]),
#         })

#     @http.route('/tax/tax/objects/<model("qaco.corporate"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tax.object', {
#             'object': obj
#         })
