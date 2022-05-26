from unicodedata import digit
from odoo import models,  fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta


class LibraryBook (models.Model):
    _name = 'library.book'
    _inherit = ['base.archive']
    _description = 'Library Book'
    _order = 'date_release desc, name'
    _rec_name = 'short_name' 

    short_name = fields.Char('Short Title', translate=True, index=True)
    name = fields.Char('Title', required= True)
    author_ids = fields.Many2Many(
        'res.partner',
        string='Authors'
    )
    notes = fields.Text('Internal Notes')
    state = fields.Seletion(
        [('draft', 'Not Vailable'),
        ('available', 'Available'),
        ('lost', 'Lost')],
        'State')
    description = fields.Html('Description',sanitize=True, strip_style=False )
    cover = fields.Binary('Book Cover')
    out_of_print = fields.Boolean('Out of Print?')
    date_release = fields.Date('Release Date')
    date_updated = fields.Datetime('Last Updated')
    pages = fields.Integer('Number of Pages',
            groups='base.group_user',states={'lost': [('readonly', True)]},
            help='Total book page count', company_dependent=False)
    reader_rating = fields.Float(
        'Reading Average Rating',
        digits = (14,4),
    )
    cost_price = fields.Float('Book Cost', digit='Book Price')
    currency_id = fields.Many2one('res.currency', string='Currency')
    retail_price = fields.Monetary('Retail Price',  # optional: currency_field='currency_id',
    )
    publisher_id = fields.Many2one( 
        'res.partner', string='Publisher', 
        # optional: 
        ondelete='set null', 
        context={}, 
        domain=[], 
    )
    publisher_city = fields.Char( 
        'Publisher City', 
        related='publisher_id.city',
        readonly=True)

    category_id = fields.Many2one('library.book.category')

    _sql_constraints = [ 
            ('name_uniq', 'UNIQUE (name)', 
            'Book title must be unique.'),
            ('positive_page', 'CHECK(pages>0)', 
            'No of pages must be positive') 
    ]

    age_days = fields.Float( 
        string='Days Since Release', 
        compute='_compute_age', 
        inverse='_inverse_age', 
        search='_search_age', 
        store=False, # optional
        compute_sudo=True # optional 
    )
    ref_doc_id = fields.Reference( 
        selection='_referencable_models', 
        string='Reference Document')


    @api.constrains('date_release') 
    def _check_release_date(self):
        for record in self:
            if record.date_release and record.date_release > fields.Date.today():
                raise models.ValidationError('Release date must be in the past') 

    @api.depends('date_release')
    def _compute_age(self):
        today = fields.Date.today()
        for book in self:
            if book.date_release:
                delta = today - book.date_release
                book.age_days = delta.days
            else:
                book.age_days = 0

    @api.depends('date_release')
    def _inverse_age(self):
        today = fields.Date.today()
        for book in self.filtered('date_release'):
            d = today - timedelta(days=book.age_days)
            book.date_release = d

    def _search_age(self, operator, value):
        today = fields.Date.today()
        value_days = timedelta(days=value)
        value_date = today - value_days
        # convert the operator:
        # book with age > value have a date < value_date
        operator_map = {
            '>': '<', '>=': '<=',
            '<': '>', '<=': '>=',
         }
        new_op = operator_map.get(operator, operator)
        return [('date_release', new_op, value_date)]     

    @api.model 
    def _referencable_models(self):
        models = self.env['ir.model'].search([('field_id.name', '=', 'message_ids')])
        return [(x.model, x.name) for x in models]





class ResPartner(models.Model): 
    _inherit = 'res.partner' 
    published_book_ids = fields.One2many( 'library.book', 'publisher_id', string='Published Books')
    authored_book_ids = fields.Many2many('library.book', string='Authored Books',   # relation='library_book_res_partner_rel' # optional
    )
    count_books = fields.Integer( 'Number of Authored Books', compute='_compute_count_books') 

    @api.depends('authored_book_ids') 
    def _compute_count_books(self): 
        for r in self: 
            r.count_books = len(r.authored_book_ids) 



class LibraryMember(models.Model): 
    _name = 'library.member' 
    _inherits = {'res.partner': 'partner_id'} 
    partner_id = fields.Many2one( 'res.partner',  ondelete='cascade', delegate=True)
    date_start = fields.Date('Member Since') 
    date_end = fields.Date('Termination Date') 
    member_number = fields.Char() 
    date_of_birth = fields.Date('Date of birth')


class BaseArchive(models.AbstractModel): 
    _name = 'base.archive' 
    active = fields.Boolean(default=True)

    def do_archive(self): 
        for record in self: 
            record.active = not record.active
