from odoo import models, fields

class ResGroups(models.Model):
    _inherit = 'res.groups'
    
    category_id = fields.Many2one('ir.module.category', string='Application', index=True)