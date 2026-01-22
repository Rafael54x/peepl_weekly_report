# -*- coding: utf-8 -*-

from odoo import models, fields

class PeeplClient(models.Model):
    _name = 'peepl.client'
    _description = 'Peepl Client'

    name = fields.Char(string='Client Name', required=True)
    code = fields.Char(string='Code')
    active = fields.Boolean(string='Active', default=True)
