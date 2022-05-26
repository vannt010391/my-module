from odoo import models,  fields

class LibraryBook (models.Model):
    _name = 'library.book'
    name = fields.Char('Title', required= True)
    date_release = fields.Date('Release Date')
    author_ids = fields.Many2Many(
        'res.partner',
        string='Authors'
    )
    