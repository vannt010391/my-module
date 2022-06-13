# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.main import Website


class Main(http.Controller):

    @http.route('/my_library/books', type='http', auth='none')
    def books(self):
        books = request.env['library.book'].sudo().search([])
        html_result = '<html><body><ul>'
        for book in books:
            html_result += "<li> %s </li>" % book.name
        html_result += '</ul></body></html>'
        return html_result

    @http.route('/my_library/books/json', type='json', auth='none')
    def books_json(self):
        records = request.env['library.book'].sudo().search([])
        return records.read(['name'])

    @http.route('/colette_library/all-books', type='http', auth='none')
    def all_books(self):
        books = request.env['library.book'].sudo().search([])
        html_result = '<html><body><ul>'
        for book in books:
            html_result += "<li> %s </li>" % book.name
        html_result += '</ul></body></html>'
        return html_result

    # @http.route('/colette_library/all-books/mark-mine', type='http', auth='public')
    # def all_books_mark_mine(self):
    #     books = request.env['library.book'].sudo().search([])
    #     html_result = '<html><body><ul>'
    #     for book in books:
    #         if request.env.user.partner_id.id in book.author_ids.ids:
    #             html_result += "<li> <b>%s</b> </li>" % book.name
    #         else:
    #             html_result += "<li> %s </li>" % book.name
    #     html_result += '</ul></body></html>'
    #     return html_result

    # @http.route('/colette_library/all-books/mine', type='http', auth='user')
    # def all_books_mine(self):
    #     books = request.env['library.book'].search([
    #         ('author_ids', 'in', request.env.user.partner_id.ids),
    #     ])
    #     html_result = '<html><body><ul>'
    #     for book in books:
    #         html_result += "<li> %s </li>" % book.name
    #     html_result += '</ul></body></html>'
    #     return html_result

    @http.route('/colette_library/book_details', type='http', auth='none')
    def book_details(self, book_id):
        record = request.env['library.book'].sudo().browse(int(book_id))
        return u'<html><body><h1>%s</h1>Authors: %s' % (
            record.name,
            u', '.join(record.author_ids.mapped('name')) or 'none',
        )

    @http.route("/colette_library/book_details/<model('library.book'):book>", type='http', auth='none')
    def book_details_in_path(self, book):
        return self.book_details(book.id)


    @http.route('/demo_page', type='http', auth='none')
    def books(self):
        image_url = '/colette_library/static/description/icon.png'
        html_result = """<html>
            <body>
                <img src="%s"/>
            </body>
        </html>""" % image_url
        return html_result



class WebsiteInfo(Website):
    @http.route()
    def website_info(self):
        result = super(WebsiteInfo, self).website_info()
        result.qcontext['apps'] = result.qcontext['apps'].filtered(
            lambda x: x.name != 'website'
        )
        return result