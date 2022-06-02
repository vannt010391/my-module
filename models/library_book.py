# -*- coding: utf-8 -*-
import logging
from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.translate import _

logger = logging.getLogger(__name__)

class BaseArchive(models.AbstractModel):
    _name = 'base.archive'
    _description = 'Abstract Archive'

    active = fields.Boolean(default=True)

    def do_archive(self):
        for record in self:
            record.active = not record.active


class LibraryBook(models.Model):
    _name = 'library.book'
   
    _inherit = ['base.archive']
    _description = 'Library Book'
    _order = 'date_release desc, name'

    name = fields.Char('Title', required=True, index=True)
    short_name = fields.Char('Short Title',translate=True, index=True)
    notes = fields.Text('Internal Notes')
    state = fields.Selection(
        [('draft', ' Unavailable'),
         ('available', 'Available'),
         ('borrowed', 'Borrowed'),
         ('lost', 'Lost')],
        'State', default="draft")
    description = fields.Html('Description', sanitize=True, strip_style=False)
    cover = fields.Binary('Book Cover')
    out_of_print = fields.Boolean('Out of Print?')
    date_release = fields.Date('Release Date')
    date_updated = fields.Datetime('Last Updated', copy=False)
    # date return
    date_return = fields.Date('Date to return')
    
    pages = fields.Integer('Number of Pages',
        groups='base.group_user',
        states={'lost': [('readonly', True)]},
        help='Total book page count', company_dependent=False)
    reader_rating = fields.Float(
        'Reader Average Rating',
        digits=(14, 4),  # Optional precision (total, decimals),
    )
    isbn = fields.Char('ISBN')
    author_ids = fields.Many2many('res.partner', string='Authors')

    cost_price = fields.Float('Book Cost', digits='Book Price')
    currency_id = fields.Many2one('res.currency', string='Currency')
    retail_price = fields.Monetary('Retail Price') # optional attribute: currency_field='currency_id' incase currency field have another name then 'currency_id'

    publisher_id = fields.Many2one('res.partner', string='Publisher',
        # optional:
        ondelete='set null',
        context={},
        domain=[],
    )
    
    publisher_city = fields.Char('Publisher City', related='publisher_id.city', readonly=True)

    category_id = fields.Many2one('library.book.category')
    age_days = fields.Float(
        string='Days Since Release',
        compute='_compute_age', inverse='_inverse_age', search='_search_age',
        store=False,
        compute_sudo=True,
    )

    ref_doc_id = fields.Reference(selection='_referencable_models', string='Reference Document')

    old_edition = fields.Many2one('library.book', string='Old Edition')

    @api.model
    def _referencable_models(self):
        models = self.env['ir.model'].search([('field_id.name', '=', 'message_ids')])
        return [(x.model, x.name) for x in models]

    @api.depends('date_release')
    def _compute_age(self):
        today = fields.Date.today()
        for book in self:
            if book.date_release:
                delta = today - book.date_release
                book.age_days = delta.days
            else:
                book.age_days = 0

    # This reverse method of _compute_age. Used to make age_days field editable
    # It is optional if you don't want to make compute field editable then you can remove this
    def _inverse_age(self):
        today = fields.Date.today()
        for book in self.filtered('date_release'):
            d = today - timedelta(days=book.age_days)
            book.date_release = d

    # This used to enable search on copute fields
    # It is optional if you don't want to make enable search then you can remove this
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

    def name_get(self):
        """ This method used to customize display name of the record """
        result = []
        # for record in self:
        #     rec_name = "%s (%s)" % (record.name, record.date_release)
        #     result.append((record.id, rec_name))
        # return result
        for book in self:
            authors = book.author_ids.mapped('name')
            name = '%s (%s)' % (book.name, ','.join(authors))
            result.append((book.id, name))
        return result

    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name)', 'Book title must be unique.'),
        ('positive_page', 'CHECK(pages>0)', 'No of pages must be positive')
    ]

    @api.constrains('date_release')
    def _check_release_date(self):
        for record in self:
            if record.date_release and record.date_release > fields.Date.today():
                raise models.ValidationError('Release date must be in the past')

    @api.model
    def is_allowed_transition(self, old_state, new_state):
        allowed = [
            ('draft', 'available'),
            ('available', 'borrowed'),
            ('borrowed', 'available'),
            ('available', 'lost'),
            ('borrowed', 'lost'),
            ('lost', 'available') 
        ]
        return (old_state, new_state) in allowed

    def change_state(self, new_state):
        for book in self:
            if book.is_allowed_transition(book.state, new_state):
                book.state = new_state
            else:
                msg = _("Moving from %s to %s is not allowed") % (book.state, new_state)
                raise UserError(msg)
    
    def make_available(self):
        # self.change_state('available')
        # self.date_return = False
        # return super(LibraryBook, self).make_available()
        self.ensure_one()
        self.change_state('available')

    def make_borrowed(self):
        # self.change_state('borrowed')
        # day_to_borrow = self.category_id.max_borrow_days or 10
        # self.date_return = fields.Date.today() + timedelta(days=day_to_borrow)
        # return super(LibraryBook, self).make_borrowed()
        self.ensure_one()
        self.change_state('borrowed')
    
    def make_lost(self):
        self.ensure_one()
        self.change_state('lost')
        if not self.env.context.get('avoid_deactivate'):
            self.active = False


    def log_all_library_members(self):
        # this is an empty recordset of model library.member
        library_member_model = self.env['library.member']
        all_members = library_member_model.search([])
        print("ALL MEMBERS:", all_members)
        return True

    # Updating values of recordset records
    def change_release_date(self):
        self.ensure_one()
        self.date_release = field.Date.today()
    
    # Find the books
    def find_book(self):
        domain = [
            '|', 
            '&', ('name', 'ilike', 'Book Name'), ('category_id.name', 'ilike', 'Category Name'),
            '&', ('name', 'ilike', 'Book Name 2'), ('category_id.name', 'ilike', 'Category Name 2')
        ]
        books = self.search(domain)

    def find_partner(self):
        PartnerObj = self.env['res.partner']
        domain = [
            '&', ('name', 'ilike', 'Parth Gajjar'),('company_id.name', '=', 'Odoo')
        ]
        partner = PartnerObj.search(domain)

    
    @api.model
    def books_with_multiple_authors(self, all_books):
        return all_books.filter(predicate)
        # return all_books.filter(lambda b: len(b.author_ids) > 1) # lambda function
        
    def predicate(book):
        if len(book.author_ids) > 1:
            return True
        return False

    @api.model
    def get_author_names(self, books):
        return books.mapped('author_ids.name') #mapped() return a recordset; otherwise, a Python list is returned
        
    @api.model
    def sort_books_by_date(self, books):
        return books.sorted(key='release_date', reverse=True)
    
       
    
    @api.model
    def _get_average_cost(self):
        grouped_result = self.read_group([('cost_price', "!=", False)], ['category_id', 'cost_price:avg'],['category_id'])
        return grouped_result   


    def book_rent(self):
        self.ensure_one()
        if self .state != 'available':
            raise UserError(_('Book is not available for renting'))
        rent_as_superuser = self.env['library.book.rent'].sudo()
        rent_as_superuser.create({ 'book_id': self.id,  'borrower_id': self.env.user.partner_id.id, 'return_date': fields.Date.today() })
    
    def average_book_occupation(self):
        self.flush()
        sql_query = """
            SELECT
                lb.name,
                avg((EXTRACT(epoch from age(return_date, rent_date)) / 86400))::int
            FROM
                library_book_rent AS lbr
            JOIN
                library_book as lb ON lb.id = lbr.book_id
            WHERE lbr.state = 'returned'
            GROUP BY lb.name;"""
        self.env.cr.execute(sql_query)
        result = self.env.cr.fetchall()
        logger.info("Average book occupation: %s", result)

    def return_all_books(self):
        self.ensure_one()
        wizard = self.env['library.return.wizard']
        # with Form(wizard) as return_form:
        #     return_form.borrower_id = self.env.user.partner_id
        #     record = return_form.save()
        #     record.books_returns()
        wizard.create({'borrower_id': self.env.user.partner_id.id}).books_returns()

class ResPartner(models.Model):
    _inherit = 'res.partner'

    published_book_ids = fields.One2many('library.book', 'publisher_id', string='Published Books')
    authored_book_ids = fields.Many2many(
        'library.book',
        string='Authored Books',
        # relation='library_book_res_partner_rel'  # optional
    )

    count_books = fields.Integer('Number of Authored Books', compute='_compute_count_books')

    @api.depends('authored_book_ids')
    def _compute_count_books(self):
        for r in self:
            r.count_books = len(r.authored_book_ids)


class LibraryMember(models.Model):
    _name = 'library.member'
    _inherits = {'res.partner': 'partner_id'}

    _description = 'Library Member'

    partner_id = fields.Many2one('res.partner', ondelete='cascade')
    date_start = fields.Date('Member Since')
    date_end = fields.Date('Termination Date')
    member_number = fields.Char()
    date_of_birth = fields.Date('Date of birth')