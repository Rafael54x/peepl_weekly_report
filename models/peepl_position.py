# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PeeplPosition(models.Model):
    _name = 'peepl.position'
    _description = 'Position Master Data'

    name = fields.Char(string='Position Name', required=True)
    code = fields.Char(string='Position Code', required=True)
    level = fields.Selection([
        ('bod', 'BOD'),
        ('manager', 'Manager'),
        ('staff', 'Staff')
    ], string='Level', required=True, default='staff')
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Position code must be unique!')
    ]

    @api.model
    def create(self, vals_list):
        # Handle both single dict and list of dicts
        if not isinstance(vals_list, list):
            vals_list = [vals_list]
        
        for vals in vals_list:
            # Auto set level to staff if not BOD or Manager
            if vals.get('code') not in ['bod', 'manager', 'staff']:
                vals['level'] = 'staff'
        
        return super(PeeplPosition, self).create(vals_list)
