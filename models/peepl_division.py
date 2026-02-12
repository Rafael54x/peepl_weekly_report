# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PeeplDivision(models.Model):
    _name = 'peepl.division'
    _description = 'Division'
    _order = 'sequence, name'

    name = fields.Char(string='Division Name', required=True)
    department_id = fields.Many2one('hr.department', string='Department', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
    allowed_department_ids = fields.Many2many('hr.department', compute='_compute_allowed_departments')

    @api.depends_context('uid')
    def _compute_allowed_departments(self):
        for record in self:
            current_user = self.env.user
            if current_user.has_group('peepl_weekly_report.group_peepl_bod'):
                record.allowed_department_ids = self.env['hr.department'].sudo().search([])
            elif current_user.has_group('peepl_weekly_report.group_peepl_supervisor') or current_user.has_group('peepl_weekly_report.group_peepl_manager'):
                user_assignment = self.env['peepl.user.assignment'].search([
                    ('user_id', '=', current_user.id), ('active', '=', True)
                ], limit=1)
                record.allowed_department_ids = user_assignment.department_id if user_assignment else self.env['hr.department']
            else:
                record.allowed_department_ids = self.env['hr.department']
