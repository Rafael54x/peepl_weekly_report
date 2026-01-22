# -*- coding: utf-8 -*-

from odoo import models, fields

class PeeplDepartment(models.Model):
    _name = 'peepl.department'
    _description = 'Peepl Department'

    name = fields.Char(string='Department Name', required=True)
    code = fields.Char(string='Code')
    manager_id = fields.Many2one('res.users', string='Manager')
    active = fields.Boolean(string='Active', default=True)
