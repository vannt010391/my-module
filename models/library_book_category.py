from odoo import models, fields, api 
from odoo.exceptions import ValidationError

class BookCategory(models.Model): 
    _name = 'library.book.category'
    _parent_store = True
    _parent_name = "parent_id" # optional if field is'parent_id'
    parent_path = fields.Char(index=True)
    name = fields.Char('Category') 
    parent_id = fields.Many2one('library.book.category', string='Parent Category', ondelete='restrict', index=True) 
    child_ids = fields.One2many( 'library.book.category', 'parent_id', string='Child Categories')
    description = fields.Text('Description')
    
    # max_borrow_days = fields.Integer('Maximum borrow days', help="For how many days book can be borrowed", default=10)


    #functions
    @api.constrains('parent_id') 
    def _check_hierarchy(self): 
        if not self._check_recursion(): 
            raise models.ValidationError('Error! You cannot create recursive categories.') 

    