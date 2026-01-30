# -*- coding: utf-8 -*-

from odoo import models, fields

class PeeplDefaultField(models.TransientModel):
    _name = 'peepl.default.field'
    _description = 'Default Fields Display'

    name = fields.Char(string='Field Name', readonly=True)
    field_type = fields.Char(string='Field Type', readonly=True)
    description = fields.Char(string='Description', readonly=True)

    def get_default_fields(self):
        return [
            {'name': 'PIC', 'field_type': 'Many2one', 'description': 'Person in Charge'},
            {'name': 'Client', 'field_type': 'Many2one', 'description': 'Client/Partner'},
            {'name': 'Project/Task', 'field_type': 'Char', 'description': 'Project or Task name'},
            {'name': 'Status', 'field_type': 'Selection', 'description': 'Task status'},
            {'name': 'Progress', 'field_type': 'Integer', 'description': 'Progress percentage'},
            {'name': 'Notes', 'field_type': 'Html', 'description': 'Additional notes'},
        ]